"""日期解析工具 - 验证与导入共用同一套日期格式与归一化逻辑"""

import unicodedata
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
    """归一化日期字符串：全角转半角后，按日期段/时间段分别归一分隔符。

    「.」在日期段（2024.01.31）与时间段（10.30）含义不同：日期段的
    . / 统一为 '-'，时间段的 . ： 统一为 ':'，不能用全局替换——否则
    点分日期会被改写成 '2024:01:31' 而无法解析。
    """
    text = unicodedata.normalize("NFKC", value.strip())  # 全角数字/冒号/斜杠等 → 半角
    parts = text.split()
    if not parts:
        return ""
    date_part = parts[0].replace("/", "-").replace(".", "-")
    time_part = "".join(parts[1:]).replace(".", ":").replace("：", ":")
    return f"{date_part} {time_part}" if time_part else date_part


def parse_date(value):
    """将值解析为纯 datetime.date；无法解析时返回 None。

    支持 datetime/date 对象与常见字符串格式（见 DATE_FORMATS）。
    None 或空字符串视为无值，返回 None。数值等其他类型返回 None。
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
