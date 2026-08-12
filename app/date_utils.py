"""日期解析工具 - 验证与导入共用同一套日期格式与归一化逻辑"""

from datetime import date, datetime

# 与 create_all_tables.sql 的 date 列对齐：仅支持以下格式
DATE_FORMATS = (
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%d",
    "%Y-%m-%d %H:%M",
    "%Y-%m-%d-%H:%M:%S",
    "%Y-%m-%d-%H:%M",
)


def normalize_date_str(value: str) -> str:
    """归一化日期字符串：统一斜杠、点号、全角冒号为 '-' 与 ':'。"""
    return value.strip().replace("/", "-").replace(".", ":").replace("：", ":")


def parse_date(value):
    """将值解析为纯 datetime.date；无法解析时返回 None。

    支持 datetime/date 对象与常见字符串格式（见 DATE_FORMATS）。
    None 或空字符串视为无值，返回 None。
    """
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        normalized = normalize_date_str(text)
        for fmt in DATE_FORMATS:
            try:
                return datetime.strptime(normalized, fmt).date()
            except ValueError:
                continue
    return None
