"""导入编排器 - 协调 Excel 流式读取与数据库批量写入"""

from datetime import date, datetime
from typing import Any

from python_calamine import CalamineWorkbook

from app import database, date_utils, error_list, excel_reader, logger, local_db
from app.utils import merge_row_ranges

# 46 张目标表名
TABLE_NAMES = [f"enterprise_info_{i:03d}" for i in range(1, 47)]

BATCH_SIZE = 5000

# 数据库中 NOT NULL 的字段：空值（None / 空串 / 纯空白）必须在导入前拦截，
# 否则会被 _row_to_dict 转成空串 ''，而 SQL Server 的 NOT NULL 只拒绝 NULL、不拒绝 ''。
NOT_NULL_COLUMNS = ("company_name", "industry")

# 缓存 column_mapping，避免每行数据都打开/关闭 SQLite 连接
_COLUMN_MAPPING_CACHE = None
_COLUMN_DISPLAY_CACHE = None


def _get_column_mapping():
    """延迟加载并缓存 Excel 列 → 数据库字段映射。"""
    global _COLUMN_MAPPING_CACHE
    if _COLUMN_MAPPING_CACHE is None:
        _COLUMN_MAPPING_CACHE = local_db.get_column_mapping()
    return _COLUMN_MAPPING_CACHE


def _get_column_display_map() -> dict[str, str]:
    """延迟加载并缓存 db 字段名 → 「D列 企业名称」样式的显示名（错误名单用）。"""
    global _COLUMN_DISPLAY_CACHE
    if _COLUMN_DISPLAY_CACHE is None:
        _COLUMN_DISPLAY_CACHE = {
            m["db_column"]: f"{m['excel_col']}列 {m['description'] or m['db_column']}"
            for m in local_db.get_column_mapping_with_desc()
        }
    return _COLUMN_DISPLAY_CACHE


_LENGTH_CONSTRAINTS = None


def _get_length_constraints() -> list[tuple[str, int]]:
    """延迟加载并缓存字段长度约束 [(db_col, max_length), ...]。

    约束定义在 validator.FIELD_CONSTRAINTS（与 DDL 一致的单一来源）；
    validator 反向依赖本模块的 _row_to_dict，须运行时导入避免循环。
    """
    global _LENGTH_CONSTRAINTS
    if _LENGTH_CONSTRAINTS is None:
        from app.validator import FIELD_CONSTRAINTS
        _LENGTH_CONSTRAINTS = [
            (db_col, max_length)
            for db_col, _is_not_null, max_length, _need_date in FIELD_CONSTRAINTS
            if max_length is not None
        ]
    return _LENGTH_CONSTRAINTS


def _display_value(value) -> str:
    """错误名单中的当前值展示：空值显示「（空）」，超长值截断。"""
    if value is None:
        return "（空）"
    text = str(value)
    if not text.strip():
        return "（空）"
    if len(text) > 60:
        return text[:60] + "…"
    return text


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
) -> list[tuple[int, dict, str]] | None:
    """逐行诊断一个批次，返回 [(Excel 行号, 行数据, 数据库报错), ...]。

    每次诊断使用独立的 cursor，避免批量插入失败导致 cursor 状态损坏
    从而所有的单行诊断全部报错。

    诊断 cursor 必须关闭 fast_executemany：批量特有的绑定失败（None/
    超长/混合类型的类型推断）在 fast 模式下单行插入同样会失败，会把
    正常行误诊为数据错误。诊断成功即提交的行仍留在事务内——调用方
    保证整表最终 rollback（诊断性重复插入不会落库）。
    """
    errors = []
    for idx, row_dict in enumerate(rows_as_dicts):
        excel_row = row_nums[idx]
        diag_cursor = conn.cursor()
        diag_cursor.fast_executemany = False
        try:
            database.insert_batch(diag_cursor, table_name, [row_dict], schema)
        except Exception as e:
            errors.append((excel_row, row_dict, str(e)))
        finally:
            diag_cursor.close()
    return errors


def _format_row_ranges(row_nums: list[int]) -> str:
    """将升序行号列表合并为连续区间文本，如 '第 106450-106480 行'。

    单行显示为 '第 5 行'；多段区间用逗号连接，
    如 '第 5-8 行, 第 20-25 行, 第 30 行'。
    """
    return ", ".join(f"第 {p} 行" for p in merge_row_ranges(row_nums))


def _format_sheet_errors(
    errors: list[dict],
    total_rows: int = 0,
) -> str:
    """将整个 sheet 的结构化错误按数据库报错信息分组，格式化为精简文本。

    errors 为 _import_sheet 收集的结构化错误 dict 列表。
    每组展示：错误类型 + 行数 + 出错行号区间；连续行号合并为区间
    （如 106450-106480）避免逐行刷屏。不带表/Sheet 头（消费方自带），
    也不展开列值样例——完整错误数据见错误名单 xlsx。
    total_rows 为整个 sheet 已扫描的总行数，用于确认已全量扫描。
    """
    groups = {}
    for err in errors:
        groups.setdefault(err["message"], []).append(err)

    scanned = f"，已扫描整个 Sheet 共 {total_rows} 行" if total_rows else ""
    parts = [
        f"共 {len(errors)} 行数据存在错误{scanned}:"
    ]
    for err_text, items in groups.items():
        parts.append(f"  · {err_text}：{len(items)} 行")
        parts.append(f"    出错行: {_format_row_ranges([e['row'] for e in items])}")
    return "\n".join(parts)


def _import_sheet(
    conn,
    wb,
    sheet_name: str,
    table_name: str,
    schema: str,
    progress_callback=None,
) -> tuple[int | Any, list[
    dict[str, str | list[tuple[str, str]] | dict | Any] | dict[str, str | list[tuple[str, str]] | dict | Any] | dict[
        str, int | str | list[Any] | dict]], list[str]] | None:
    """导入单个 sheet，返回 (扫描行数, 行级错误列表, 批量级错误信息列表)。

    数据错误不再抛异常（由调用方汇总为失败表后继续导入下一表）；
    只有基础设施级错误（如连接断开）才会向上抛出。

    行级错误为结构化 dict：
        {"row": Excel行号, "message": 完整错误文本, "kind": "null"/"date"/"db",
         "fields": [(列名显示, 当前值显示), ...], "values": 整行字段 dict}
    fields 供错误名单 xlsx 使用；kind 供名单归类问题类型。
    """
    sheet_rows = 0
    all_errors = []
    bulk_error_msgs = []
    batch_index = 0
    display_map = _get_column_display_map()

    for batch_start_row, batch in excel_reader.iter_sheet_rows_from_workbook(
        wb, sheet_name, BATCH_SIZE
    ):
        batch_index += 1
        row_nums = [rn for rn, _ in batch]
        rows_as_dicts = [_row_to_dict(row_data) for _, row_data in batch]
        sheet_rows += len(batch)

        # ── NOT NULL 前置检查 ──
        # 空 company_name / industry 若放行，会被 _row_to_dict 转成空串 '' 写入数据库，
        # 而 SQL Server 的 NOT NULL 不拦截空串，因此这里显式拦截并记录错误。
        clean_rows = []
        clean_row_nums = []
        for excel_row, row_dict in zip(row_nums, rows_as_dicts):
            null_cols = [
                col for col in NOT_NULL_COLUMNS
                if row_dict.get(col) is None
                or (
                    isinstance(row_dict.get(col), str)
                    and row_dict.get(col).strip() == ""
                )
            ]
            if null_cols:
                all_errors.append({
                    "row": excel_row,
                    "values": row_dict,
                    "kind": "null",
                    "message": f"字段 [{', '.join(null_cols)}] 不能为空 (NOT NULL 约束)",
                    "fields": [
                        (display_map.get(col, col), _display_value(row_dict.get(col)))
                        for col in null_cols
                    ],
                })
                continue

            # 日期字段(collected_at)预校验：给出清晰中文报错，
            # 避免把脏值交给数据库后报出晦涩的 22018。
            # _to_date 已把可解析的值统一转成 date；到这里仍不是 date 的，
            # 要么是解析失败的字符串，要么是数值格式（Excel「常规」单元格
            # 会把日期读成 int/float 序列号），统一拦截。
            v = row_dict.get("collected_at")
            if v is not None and not isinstance(v, date):
                hint = ("" if isinstance(v, str)
                        else "（日期列应为文本格式，请勿使用数值/常规格式）")
                all_errors.append({
                    "row": excel_row,
                    "values": row_dict,
                    "kind": "date",
                    "message": f"字段 [collected_at] 第 {excel_row} 行 "
                               f"值 '{_display_value(v)}' "
                               f"不是有效日期（应形如 2024-01-31）{hint}",
                    "fields": [
                        (display_map.get("collected_at", "collected_at"),
                         _display_value(v))
                    ],
                })
                continue

            # 长度预校验：超长值若放行到数据库，会触发「批量失败 → 整批
            # 逐行诊断」的慢路径；在预检阶段报出可以便宜一个数量级。
            overlength = [
                (db_col, max_length)
                for db_col, max_length in _get_length_constraints()
                if isinstance(row_dict.get(db_col), str)
                and len(row_dict[db_col]) > max_length
            ]
            if overlength:
                all_errors.append({
                    "row": excel_row,
                    "values": row_dict,
                    "kind": "length",
                    "message": "、".join(
                        f"字段 [{db_col}] 值长度 {len(row_dict[db_col])} "
                        f"超过限制 {max_length}"
                        for db_col, max_length in overlength
                    ),
                    "fields": [
                        (display_map.get(db_col, db_col),
                         _display_value(row_dict[db_col]))
                        for db_col, _max_length in overlength
                    ],
                })
                continue

            clean_rows.append(row_dict)
            clean_row_nums.append(excel_row)

        if not clean_rows:
            continue  # 本批没有可插入的有效行

        # 每批使用独立 cursor，避免批量失败后 cursor 状态损坏影响后续批次
        batch_cursor = conn.cursor()
        batch_cursor.fast_executemany = True
        try:
            database.insert_batch(batch_cursor, table_name, clean_rows, schema)
        except Exception as e:
            if progress_callback:
                progress_callback(
                    0, 0,
                    f"表 [{table_name}] 第 {batch_index} 批批量插入失败，"
                    "正在逐行定位错误行...",
                )
            batch_errors = _diagnose_batch(
                conn, table_name, clean_rows, clean_row_nums, schema,
            )
            if batch_errors:
                for excel_row, row_dict, err in batch_errors:
                    all_errors.append({
                        "row": excel_row,
                        "values": row_dict,
                        "kind": "db",
                        "message": err,
                        "fields": [],
                    })
            else:
                # fast_executemany 类型推断等批量特有原因：单行全部插入成功
                bulk_error_msgs.append(str(e))
        finally:
            try:
                batch_cursor.close()
            except Exception:
                pass

    return sheet_rows, all_errors, bulk_error_msgs


def _safe_rollback(conn) -> None:
    """回滚当前事务；连接已断开时 rollback 自身可能抛错，忽略以保证流程继续。"""
    try:
        conn.rollback()
    except Exception:
        pass


def _connection_alive(conn) -> bool | None:
    """检测连接是否仍然可用（SELECT 1）；用于区分表级错误与连接级错误。"""
    try:
        cur = conn.cursor()
    except Exception:
        return False
    try:
        cur.execute("SELECT 1")
        return True
    except Exception:
        return False
    finally:
        try:
            cur.close()
        except Exception:
            pass


def _record_failed(
    failed_tables: dict,
    table_name: str,
    sheet_name: str,
    error_text: str,
    row_errors: list,
    progress_callback=None,
) -> None:
    """记录一张失败表（状态持久化失败不影响导入流程），并提示继续。"""
    failed_tables[table_name] = {
        "sheet_name": sheet_name,
        "error": error_text,
        "errors": row_errors,
    }
    try:
        local_db.update_import_result(table_name, False)
    except Exception:
        pass
    if progress_callback:
        progress_callback(0, 0, f"表 [{table_name}] 导入失败，已跳过，继续下一表...")


def _import_one_sheet(
    conn,
    wb,
    sheet_name: str,
    table_name: str,
    schema: str,
    table_row_counts: dict,
    failed_tables: dict,
    progress_callback=None,
) -> None:
    """导入单表：成功则提交并记入 table_row_counts；数据/表级错误则回滚该表、
    记入 failed_tables 后返回（流程继续后续表）；连接级错误向上抛出中止整个流程。"""
    cursor = conn.cursor()
    cursor.fast_executemany = True
    try:
        # 清空当前表（无 TRUNCATE 权限，使用 DELETE）
        database.delete_all_tables(cursor, [table_name], schema)

        # 流式写入当前表
        sheet_rows, row_errors, bulk_error_msgs = _import_sheet(
            conn, wb, sheet_name, table_name, schema, progress_callback,
        )

        if row_errors or bulk_error_msgs:
            _safe_rollback(conn)
            error_text = (
                _format_sheet_errors(row_errors, sheet_rows)
                if row_errors
                else "批量插入失败，但逐行诊断未发现异常数据，原始数据库报错：\n"
                     + "\n\n".join(bulk_error_msgs)
            )
            _record_failed(
                failed_tables, table_name, sheet_name, error_text, row_errors,
                progress_callback,
            )
            return

        table_row_counts[table_name] = sheet_rows

        # pyodbc autocommit=False 时需用 conn.commit() 提交 ODBC 层事务
        conn.commit()
    except Exception as e:
        _safe_rollback(conn)
        if not _connection_alive(conn):
            # 连接级错误：后续表必然全部失败，中止整个流程
            raise
        # 表级错误（权限、锁等）：记录后继续后续表
        _record_failed(
            failed_tables, table_name, sheet_name, str(e), [],
            progress_callback,
        )
    else:
        # 成功后才记录状态与最后导入时间（状态写入失败不影响已提交的数据）
        import_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            local_db.update_import_result(table_name, True, import_time)
        except Exception:
            pass
    finally:
        try:
            cursor.close()
        except Exception:
            pass


def build_failure_result(
    file_name: str = "",
    start_time: str = "",
    tables: dict | None = None,
    error: str = "",
    failed_tables: dict | None = None,
) -> dict:
    """构造失败的导入结果 dict（run_import 与工作线程共用，避免重复组装）。"""
    return {
        "success": False,
        "partial": False,
        "file": file_name,
        "start_time": start_time,
        "end_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "tables": tables or {},
        "failed_tables": failed_tables or {},
        "error": error,
        "error_list_path": "",
    }


def run_import(
    conn,
    excel_path: str,
    selected_sheets: list[dict],
    schema: str = "dbo",
    progress_callback=None,
) -> None | dict[str, str | dict[Any, Any] | bool | Any] | dict:
    """执行完整导入流程。

    逐表独立事务：某表数据错误时仅回滚该表、记录失败并继续导入后续表，
    全部表处理完后汇总「部分成功」结果；仅连接断开等基础设施错误中止整个流程。
    有失败表时自动在源文件同目录生成错误名单 xlsx。

    参数:
        conn: pyodbc.Connection 对象
        excel_path: .xlsx 文件路径
        selected_sheets: [{"sheet_name": str, "table_name": str}, ...]
        schema: 数据库 schema 名称
        progress_callback: (current: int, total: int, message: str) -> None

    返回:
        {
            "success": bool,          # 是否全部成功
            "partial": bool,          # 是否部分成功（有失败表但流程完整走完）
            "file": str,
            "start_time": str,
            "end_time": str,
            "tables": {表名: 行数},   # 成功的表
            "failed_tables": {表名: {"sheet_name": str, "error": str, "errors": [dict]}},
            "error": str,             # 失败汇总 / 致命错误文本（成功时为空）
            "error_list_path": str,   # 自动生成的错误名单 xlsx 路径（如有）
        }
    """
    start_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    file_name = excel_path.rsplit("\\", 1)[-1].rsplit("/", 1)[-1]
    table_row_counts = {}
    failed_tables = {}

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
        wb = CalamineWorkbook.from_path(excel_path)

        try:
            # ── 3. 逐表导入，每表一个事务；失败记录后继续下一表 ──
            for i, item in enumerate(selected_sheets):
                if progress_callback:
                    progress_callback(
                        i, actual_count,
                        f"正在导入 ({i+1}/{actual_count}) {item['table_name']}..."
                    )
                _import_one_sheet(
                    conn, wb, item["sheet_name"], item["table_name"], schema,
                    table_row_counts, failed_tables, progress_callback,
                )
        finally:
            wb.close()

        if progress_callback:
            progress_callback(actual_count, actual_count, "导入完成")

        end_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # ── 4. 有失败表时自动生成错误名单 xlsx（生成失败不影响导入结果） ──
        error_list_path = ""
        list_note = ""
        if failed_tables:
            try:
                error_list_path = error_list.generate_error_list(
                    excel_path, failed_tables,
                )
            except Exception as e:
                list_note = f"（错误名单生成失败: {e}）"

        fail_count = len(failed_tables)
        result = {
            "success": fail_count == 0,
            "partial": fail_count > 0,
            "file": file_name,
            "start_time": start_time,
            "end_time": end_time,
            "tables": table_row_counts,
            "failed_tables": failed_tables,
            "error": (
                f"{fail_count} 张表导入失败：{'、'.join(failed_tables)}{list_note}"
                if fail_count else ""
            ),
            "error_list_path": error_list_path,
        }

    except Exception as e:
        result = build_failure_result(
            file_name, start_time, table_row_counts, str(e), failed_tables,
        )

    # ── 5. 记录日志 ──
    try:
        logger.log_import(result)
    except Exception:
        pass

    return result
