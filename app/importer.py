"""导入编排器 - 协调 Excel 流式读取与数据库批量写入"""

from datetime import datetime
import openpyxl
from openpyxl.utils import get_column_letter

from app import database, date_utils, excel_reader, logger, local_db

# 46 张目标表名
TABLE_NAMES = [f"enterprise_info_{i:03d}" for i in range(1, 47)]

BATCH_SIZE = 5000

# 缓存 column_mapping，避免每行数据都打开/关闭 SQLite 连接
_COLUMN_MAPPING_CACHE = None


def _get_column_mapping():
    """延迟加载并缓存 Excel 列 → 数据库字段映射。"""
    global _COLUMN_MAPPING_CACHE
    if _COLUMN_MAPPING_CACHE is None:
        _COLUMN_MAPPING_CACHE = local_db.get_column_mapping()
    return _COLUMN_MAPPING_CACHE


def _to_date(value):
    """将 collected_at 值统一转为 datetime.date；无法解析时返回原值（交由数据库报错）。"""
    if value is None:
        return None
    if isinstance(value, str) and not value.strip():
        return None
    parsed = date_utils.parse_date(value)
    return parsed if parsed is not None else value


def _row_to_dict(row: list) -> dict:
    """将 Excel 一行数据转换为 {字段名: 值} dict。"""
    result = {}
    for db_col, excel_idx in _get_column_mapping():
        value = row[excel_idx] if excel_idx < len(row) else None
        if db_col == "collected_at":
            value = _to_date(value)
        # 避免 pyodbc fast_executemany 因 None 推断出过小的参数类型
        elif value is None:
            value = ""
        result[db_col] = value
    return result


def _diagnose_batch(
    conn,
    table_name: str,
    rows_as_dicts: list[dict],
    row_nums: list[int],
    schema: str,
) -> list[tuple[int, dict, str]]:
    """逐行诊断一个批次，返回 [(Excel 行号, 行数据, 数据库报错), ...]。

    每次诊断使用独立的 cursor，避免批量插入失败导致 cursor 状态损坏
    从而所有的单行诊断全部报错。
    """
    errors = []
    for idx, row_dict in enumerate(rows_as_dicts):
        excel_row = row_nums[idx]
        diag_cursor = conn.cursor()
        diag_cursor.fast_executemany = True
        try:
            database.insert_batch(diag_cursor, table_name, [row_dict], schema)
        except Exception as e:
            errors.append((excel_row, row_dict, str(e)))
        finally:
            diag_cursor.close()
    return errors


def _format_sheet_errors(
    sheet_name: str,
    table_name: str,
    errors: list[tuple[int, dict, str]],
) -> str:
    """将整个 sheet 的错误行按数据库报错信息分组，格式化输出。

    每组展示：错误类型 + 全部出错行号 + 前 3 条样例的列值明细，
    保证所有错误一次看全且同类错误不重复刷屏。
    """
    groups = {}
    for excel_row, row_dict, err in errors:
        groups.setdefault(err, []).append((excel_row, row_dict))

    parts = [
        f"导入失败，表 [{table_name}] / Sheet [{sheet_name}] "
        f"共 {len(errors)} 行数据存在错误:"
    ]
    for err, items in groups.items():
        parts.append(f"\n■ 错误类型（{len(items)} 行）: {err}")
        row_lines = []
        for i in range(0, len(items), 15):
            chunk = items[i:i + 15]
            row_lines.append("  第 " + ", ".join(str(rn) for rn, _ in chunk) + " 行")
        parts.append("\n".join(row_lines))

        sample_count = min(3, len(items))
        parts.append(f"  样例（前 {sample_count} 条）:")
        for excel_row, row_dict in items[:sample_count]:
            col_details = [
                f"    {get_column_letter(idx + 1)}列 ({db_col}) = {repr(row_dict.get(db_col))}"
                for db_col, idx in _get_column_mapping()
            ]
            parts.append(f"  Excel 第 {excel_row} 行:")
            parts.extend(col_details)
    return "\n".join(parts)


def _import_sheet(
    conn,
    wb,
    sheet_name: str,
    table_name: str,
    schema: str,
    progress_callback=None,
) -> int:
    """导入单个 sheet，返回导入行数。

    某批次批量插入失败时，对该批次逐行诊断并继续处理后续批次，
    收集整个 sheet 的所有错误；全部批次处理完后再统一抛出。
    """
    sheet_rows = 0
    all_errors = []
    bulk_error_msgs = []
    batch_index = 0

    for batch_start_row, batch in excel_reader.iter_sheet_rows_from_workbook(
        wb, sheet_name, BATCH_SIZE
    ):
        batch_index += 1
        row_nums = [rn for rn, _ in batch]
        rows_as_dicts = [_row_to_dict(row_data) for _, row_data in batch]

        # 每批使用独立 cursor，避免批量失败后 cursor 状态损坏影响后续批次
        batch_cursor = conn.cursor()
        batch_cursor.fast_executemany = True
        try:
            database.insert_batch(batch_cursor, table_name, rows_as_dicts, schema)
        except Exception as e:
            if progress_callback:
                progress_callback(
                    0, 0,
                    f"表 [{table_name}] 第 {batch_index} 批批量插入失败，"
                    "正在逐行定位错误行...",
                )
            batch_errors = _diagnose_batch(
                conn, table_name, rows_as_dicts, row_nums, schema,
            )
            if batch_errors:
                all_errors.extend(batch_errors)
            else:
                # fast_executemany 类型推断等批量特有原因：单行全部插入成功
                bulk_error_msgs.append(str(e))
        finally:
            batch_cursor.close()
        sheet_rows += len(batch)

    if all_errors:
        raise ValueError(_format_sheet_errors(sheet_name, table_name, all_errors))
    if bulk_error_msgs:
        raise ValueError(
            "批量插入失败，但逐行诊断未发现异常数据，原始数据库报错：\n"
            + "\n\n".join(bulk_error_msgs)
        )
    return sheet_rows


def build_failure_result(
    file_name: str = "",
    start_time: str = "",
    tables: dict | None = None,
    error: str = "",
) -> dict:
    """构造失败的导入结果 dict（run_import 与工作线程共用，避免重复组装）。"""
    return {
        "success": False,
        "file": file_name,
        "start_time": start_time,
        "end_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "tables": tables or {},
        "error": error,
    }


def run_import(
    conn,
    excel_path: str,
    selected_sheets: list[dict],
    schema: str = "dbo",
    progress_callback=None,
) -> dict:
    """执行完整导入流程。

    参数:
        conn: pyodbc.Connection 对象
        excel_path: .xlsx 文件路径
        selected_sheets: [{"sheet_name": str, "table_name": str}, ...]
        schema: 数据库 schema 名称
        progress_callback: (current: int, total: int, message: str) -> None

    返回:
        {
            "success": bool,
            "file": str,
            "start_time": str,
            "end_time": str,
            "tables": {表名: 行数},
            "error": str (失败时有值),
        }
    """
    start_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    file_name = excel_path.rsplit("\\", 1)[-1].rsplit("/", 1)[-1]
    table_row_counts = {}

    if not selected_sheets:
        raise ValueError("未选择任何 Sheet 进行导入")

    target_tables = [item["table_name"] for item in selected_sheets]
    actual_count = len(selected_sheets)

    try:
        # ── 1. 检查数据库表是否存在 ──
        if progress_callback:
            progress_callback(0, actual_count, "正在检查数据库表结构...")

        all_exist, missing = database.check_tables_exist(conn, target_tables, schema)
        if not all_exist:
            missing_str = ", ".join(missing)
            raise ValueError(
                f"数据库缺少以下 {len(missing)} 张表：{missing_str}\n"
                "请先执行建表脚本 create_all_tables.sql"
            )

        # ── 2. 打开 Excel 一次，所有 sheet 共用 ──
        if progress_callback:
            progress_callback(0, actual_count, "正在读取 Excel 文件...")
        wb = openpyxl.load_workbook(excel_path, read_only=True, data_only=True)

        try:
            # ── 3. 逐表导入，每表一个事务 ──
            for i, item in enumerate(selected_sheets):
                sheet_name = item["sheet_name"]
                table_name = item["table_name"]

                if progress_callback:
                    progress_callback(
                        i, actual_count,
                        f"正在导入 ({i+1}/{actual_count}) {table_name}..."
                    )

                cursor = conn.cursor()
                cursor.fast_executemany = True
                try:
                    # 清空当前表（无 TRUNCATE 权限，使用 DELETE）
                    database.delete_all_tables(cursor, [table_name], schema)

                    # 流式写入当前表
                    sheet_rows = _import_sheet(
                        conn, wb, sheet_name, table_name, schema,
                        progress_callback,
                    )
                    table_row_counts[table_name] = sheet_rows

                    # pyodbc autocommit=False 时需用 conn.commit() 提交 ODBC 层事务
                    conn.commit()

                    # 记录最后导入时间
                    import_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    local_db.update_last_import_time(table_name, import_time)

                except Exception:
                    conn.rollback()
                    raise
                finally:
                    cursor.close()

        finally:
            wb.close()

        if progress_callback:
            progress_callback(actual_count, actual_count, "导入完成")

        end_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        result = {
            "success": True,
            "file": file_name,
            "start_time": start_time,
            "end_time": end_time,
            "tables": table_row_counts,
            "error": "",
        }

    except Exception as e:
        result = build_failure_result(file_name, start_time, table_row_counts, str(e))

    # ── 4. 记录日志 ──
    try:
        logger.log_import(result)
    except Exception:
        pass

    return result
