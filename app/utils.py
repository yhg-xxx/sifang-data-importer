"""通用工具函数 - Excel 列索引与列字母互转等共享功能"""


def col_letter(idx: int) -> str:
    """Excel 列索引(1-based) → 列字母：1→A, 27→AA。"""
    letters = ""
    while idx > 0:
        idx, rem = divmod(idx - 1, 26)
        letters = chr(65 + rem) + letters
    return letters
