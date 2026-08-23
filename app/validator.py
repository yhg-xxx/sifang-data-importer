"""数据验证模块 - 在导入前校验 Excel 数据是否符合数据库约束"""

from datetime import datetime, date

from python_calamine import CalamineWorkbook

from app.importer import _row_to_dict, _format_row_ranges, _get_column_mapping
from app import date_utils, excel_reader, local_db
from app.utils import col_letter

# 字段约束定义（与 create_all_tables.sql 保持一致）
# (db_col_name, is_not_null, max_length, need_date_check)
FIELD_CONSTRAINTS = [
    ("collected_at",  False, None,  True),   # date 类型
    ("team",          False, 50,    False),
    ("source",        False, 200,   False),
    ("company_name",  True,  500,   False),   # NOT NULL
    ("link",          False, 1000,  False),
    ("industry",      True,  100,   False),   # NOT NULL
    ("sub_category_2",False, 100,   False),
    ("sub_category_3",False, 100,   False),
    ("org_type",      False, 100,   False),
    ("status",        False, 200,   False),
    ("system_reply",  False, None,  False),   # nvarchar(MAX) 无限制
]

def _validate_row(row_dict: dict, excel_row: int):
    """校验单行数据，返回 [(excel_row, row_dict, err_msg), ...] 元组列表。"""
    errors = []

    for db_col, is_not_null, max_length, need_date_check in FIELD_CONSTRAINTS:
        value = row_dict.get(db_col)

        # 1. NOT NULL 检查
        if is_not_null:
            if value is None or (isinstance(value, str) and value.strip() == ""):
                errors.append((
                    excel_row, row_dict,
                    f"字段 [{db_col}] 不能为空 (NOT NULL 约束)",
                ))
                continue

        # 2. 如果值为 None，跳过长度和日期检查
        if value is None:
            continue

        # 3. 长度检查（仅对字符串类型）
        if max_length is not None and isinstance(value, str):
            if len(value) > max_length:
                errors.append((
                    excel_row, row_dict,
                    f"字段 [{db_col}] 值长度 {len(value)} 超过限制 {max_length}",
                ))

        # 4. 日期类型检查
        if need_date_check and value is not None:
            if not _is_valid_date(value):
                errors.append((
                    excel_row, row_dict,
                    f"字段 [{db_col}] 无法解析为日期",
                ))

    return errors


# 延迟初始化的字段名 → Excel 列字母映射缓存
_col_letter_map_cache = None


def _get_col_letter(db_col: str) -> str:
    """根据数据库字段名获取 Excel 列字母（延迟初始化 + 缓存）。"""
    global _col_letter_map_cache
    if _col_letter_map_cache is None:
        mapping = local_db.get_column_mapping()
        _col_letter_map_cache = {
            col_name: col_letter(excel_idx + 1)
            for col_name, excel_idx in mapping
        }
    return _col_letter_map_cache.get(db_col, "?")


def _is_valid_date(value) -> bool:
    """检查值是否可以转换为日期（与导入共用同一套格式，见 date_utils）。"""
    if value is None:
        return True
    if isinstance(value, (datetime, date)):
        return True
    if isinstance(value, str):
        if value.strip() == "":
            return True  # 空字符串视为 None，不报错
        return date_utils.parse_date(value) is not None
    return True  # 其他类型（如 int/float）不校验


def _format_validation_errors(
    sheet_name: str,
    errors: list[tuple[int, dict, str]],
    total_rows: int = 0,
) -> str:
    """将验证错误按类型分组，格式化输出（与导入报错格式一致）。"""
    groups = {}
    for excel_row, row_dict, err in errors:
        groups.setdefault(err, []).append((excel_row, row_dict))

    scanned = f"，已扫描整个 Sheet 共 {total_rows} 行" if total_rows else ""
    parts = [
        f"验证完成，Sheet [{sheet_name}] "
        f"共 {len(errors)} 行数据存在错误{scanned}:"
    ]
    for err, items in groups.items():
        parts.append(f"\n■ 错误类型（{len(items)} 行）: {err}")
        parts.append(f"  出错行: {_format_row_ranges([rn for rn, _ in items])}")

        sample_count = min(3, len(items))
        parts.append(f"  样例（前 {sample_count} 条）:")
        for excel_row, row_dict in items[:sample_count]:
            col_details = [
                f"    {col_letter(idx + 1)}列 ({db_col}) = {repr(row_dict.get(db_col))}"
                for db_col, idx in _get_column_mapping()
            ]
            parts.append(f"  Excel 第 {excel_row} 行:")
            parts.extend(col_details)
    return "\n".join(parts)


def validate_excel(filepath: str, selected_sheets: list[dict],
                   progress_callback=None) -> dict:
    """验证 Excel 文件中指定 sheet 的数据。

    参数:
        filepath: .xlsx 文件路径
        selected_sheets: [{"sheet_name": str, "table_name": str}, ...]
        progress_callback: (current: int, total: int, sheet_name: str) -> None

    返回:
        {
            "valid": bool,          # 是否所有数据通过验证
            "total_errors": int,    # 错误总数
            "total_rows": int,      # 总行数
            "total_sheets": int,    # 总 sheet 数
            "errors_by_sheet": {    # 按 sheet 分组的错误
                "sheet_name": {
                    "raw_errors": [(excel_row, row_dict, err_msg), ...],
                    "total_rows": int,
                    "formatted": str,
                },
            },
            "error": str,           # 错误信息
        }
    """
    if not selected_sheets:
        return {
            "valid": False,
            "total_errors": 1,
            "total_rows": 0,
            "total_sheets": 0,
            "errors_by_sheet": {},
            "error": "未选择任何 Sheet",
        }

    total_errors = 0
    total_rows = 0
    errors_by_sheet = {}

    wb = CalamineWorkbook.from_path(filepath)
    try:
        for i, item in enumerate(selected_sheets):
            sheet_name = item["sheet_name"]

            if progress_callback:
                progress_callback(i, len(selected_sheets), sheet_name)

            sheet_errors = []
            sheet_row_count = 0

            for batch_start_row, batch in excel_reader.iter_sheet_rows_from_workbook(
                wb, sheet_name, batch_size=5000
            ):
                for row_num, row in batch:
                    total_rows += 1
                    sheet_row_count += 1
                    row_dict = _row_to_dict(row)
                    row_errors = _validate_row(row_dict, row_num)
                    sheet_errors.extend(row_errors)
                    total_errors += len(row_errors)

            if sheet_errors:
                errors_by_sheet[sheet_name] = {
                    "raw_errors": sheet_errors,
                    "total_rows": sheet_row_count,
                    "formatted": _format_validation_errors(
                        sheet_name, sheet_errors, sheet_row_count,
                    ),
                }
    finally:
        wb.close()

    if progress_callback:
        progress_callback(len(selected_sheets), len(selected_sheets), "验证完成")

    return {
        "valid": total_errors == 0,
        "total_errors": total_errors,
        "total_rows": total_rows,
        "total_sheets": len(selected_sheets),
        "errors_by_sheet": errors_by_sheet,
        "error": "",
    }
