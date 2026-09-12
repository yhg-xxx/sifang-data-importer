"""Excel 文件读取 - 使用 python-calamine 和 zipfile"""

import zipfile
import xml.etree.ElementTree as ET

from python_calamine import CalamineWorkbook


_R_NS = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"


def read_sheet_entries(filepath: str) -> list[tuple[str, str | None]]:
    """解析 xl/workbook.xml，返回 [(sheet名, rId)]（ElementTree 正确处理属性
    引号与实体转义）。

    供 read_sheets 的 sheet 名列表与 xlsx_surgery 的 XML 条目定位共用同一份
    解析，避免两套解析器对同一文件各自漂移；rId 缺失（rels 异常的 sheet）
    时为 None，由调用方决定取舍。
    """
    ns = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
    result = []

    with zipfile.ZipFile(filepath, "r") as z:
        with z.open("xl/workbook.xml") as f:
            for sheet_elem in ET.parse(f).getroot().findall(f".//{ns}sheet"):
                name = sheet_elem.get("name")
                if name:
                    result.append((name, sheet_elem.get(f"{_R_NS}id")))

    return result


def read_sheets(filepath: str) -> list[dict]:
    """读取 sheet 名称（通过 zipfile 解析 xl/workbook.xml，秒级完成）。

    返回值:
        [
            {"sheet_name": str},
            ...
        ]
    """
    return [{"sheet_name": name} for name, _rid in read_sheet_entries(filepath)]


def iter_sheet_rows_from_workbook(
    wb: CalamineWorkbook, sheet_name: str, batch_size: int = 5000,
):
    """从已打开的 workbook 中流式读取单个 sheet（避免重复打开文件）。

    Yields:
        (start_row: int, list[tuple[int, list]]): start_row 为批次首行在 Excel 中的行号（1-based），
        每批为 (实际Excel行号, 行数据) 元组列表，最多 batch_size 个数据行。
    """
    ws = wb.get_sheet_by_name(sheet_name)
    yield from _iter_ws_rows(ws, batch_size)


def _iter_ws_rows(ws, batch_size: int):
    """内部函数：从已打开的 worksheet 流式读取。"""
    rows_iter = ws.iter_rows()

    # 跳过表头（第1行）
    try:
        next(rows_iter)
    except StopIteration:
        pass

    batch = []
    batch_start_row = 2   # 数据从第2行开始
    row_num = 2
    for row in rows_iter:
        truncated = list(row)[:11]
        if any(cell is not None and str(cell).strip() != "" for cell in truncated):
            batch.append((row_num, truncated))
        if len(batch) >= batch_size:
            yield batch_start_row, batch
            batch_start_row = row_num + 1
            batch = []
        row_num += 1
    if batch:
        yield batch_start_row, batch
