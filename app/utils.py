"""通用工具函数 - Excel 列索引与列字母互转等共享功能"""


def col_letter(idx: int) -> str:
    """Excel 列索引(1-based) → 列字母：1→A, 27→AA。"""
    letters = ""
    while idx > 0:
        idx, rem = divmod(idx - 1, 26)
        letters = chr(65 + rem) + letters
    return letters


# 全角 ASCII（U+FF01~U+FF5E）→ 半角（减 0xFEE0），外加全角空格 U+3000 → 半角空格
_FULLWIDTH_MAP = {code: code - 0xFEE0 for code in range(0xFF01, 0xFF5F)}
_FULLWIDTH_MAP[0x3000] = 0x20


def normalize_dedup_key(value) -> str:
    """去重判重键规范化：全角转半角 → 去首尾空白。返回空串表示空值（不参与判重）。

    受限字符集转换，不使用 NFKC，避免误伤企业名称中的其他特殊字符。
    """
    if value is None:
        return ""
    return str(value).translate(_FULLWIDTH_MAP).strip()
