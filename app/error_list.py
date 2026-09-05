"""导入错误名单生成 - 将失败表的结构化错误导出为业务可读的 xlsx

导入结束后若有失败表，自动在源文件同目录生成
「源文件名__导入错误名单_时间戳.xlsx」（目标已存在时加计数后缀，永不覆盖）：
- 「汇总」sheet：按负责人聚合（可直接整段复制进群消息催办）
- 「明细」sheet：行级错误（Sheet、Excel行号、列名、当前值、问题描述、负责人）
"""

import os
from datetime import datetime

import xlsxwriter

from app.error_msgs import humanize_db_error


def _resolve_output_path(source_dir: str, source_stem: str) -> str:
    """生成不与任何已有文件冲突的名单路径；同秒冲突加 _2 计数后缀。"""
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    base = os.path.join(source_dir, f"{source_stem}__导入错误名单_{ts}")
    path = base + ".xlsx"
    counter = 2
    while os.path.exists(path):
        path = f"{base}_{counter}.xlsx"
        counter += 1
    return path


def _clean_text(value) -> str:
    """文本清洗：None/纯空白 → 空串。"""
    if value is None:
        return ""
    return str(value).strip()


def _problem_text(err: dict) -> str:
    """按错误 kind 归类出简短的问题描述（名单「问题描述」列与汇总用）。"""
    kind = err.get("kind", "")
    message = err.get("message", "")
    if kind == "null":
        return "必填字段为空，请补填"
    if kind == "date":
        return "日期格式无法识别（应形如 2024-01-31）"
    text = humanize_db_error(message) if message.strip() else ""
    first = next((ln for ln in text.splitlines() if ln.strip()), "未知错误")
    return first.strip()[:60]


def _collect(failed_tables: dict) -> tuple[dict, list]:
    """汇总失败表数据。

    返回 (summary, detail_rows)：
    - summary: {(负责人, Sheet名称): {"count": 错误行数, "problems": [问题描述]}}
    - detail_rows: [Sheet名称, Excel行号, 列名, 当前值, 问题描述, 负责人]
    """
    summary: dict = {}
    detail_rows: list = []

    for table_name, info in failed_tables.items():
        sheet_name = info.get("sheet_name", "")
        errors = list(info.get("errors") or [])
        if not errors:
            # 整表失败但无行级错误（如批量插入异常）：合成一条明细，保证名单可见
            first_line = next(
                (ln for ln in (info.get("error") or "").splitlines() if ln.strip()),
                "未知错误",
            )
            errors = [{
                "row": "", "values": {}, "kind": "db",
                "message": first_line, "fields": [],
            }]

        for err in errors:
            values = err.get("values") or {}
            team = _clean_text(values.get("team")) or "（未填负责人）"
            entry = summary.setdefault((team, sheet_name), {"count": 0, "problems": []})
            entry["count"] += 1

            problem = _problem_text(err)
            if problem not in entry["problems"]:
                entry["problems"].append(problem)

            fields = err.get("fields") or []
            if fields:
                for col_display, value_text in fields:
                    detail_rows.append(
                        [sheet_name, err.get("row", ""), col_display, value_text, problem, team]
                    )
            else:
                # 无具体列信息（数据库诊断错误）：用企业名称帮助定位行
                company = _clean_text(values.get("company_name")) or "—"
                detail_rows.append(
                    [sheet_name, err.get("row", ""), "—", company, problem, team]
                )

    return summary, detail_rows


def generate_error_list(excel_path: str, failed_tables: dict) -> str:
    """生成错误名单 xlsx，返回文件路径。

    failed_tables: {table_name: {"sheet_name": str, "error": str,
                                 "errors": [结构化错误 dict]}}
    错误 dict 结构见 importer._import_sheet（row/message/kind/fields/values）。
    """
    source_dir = os.path.dirname(os.path.abspath(excel_path))
    source_stem = os.path.splitext(os.path.basename(excel_path))[0]
    out_path = _resolve_output_path(source_dir, source_stem)
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    summary, detail_rows = _collect(failed_tables)

    workbook = xlsxwriter.Workbook(out_path)
    title_fmt = workbook.add_format({"bold": True, "font_size": 13})
    sub_fmt = workbook.add_format({"font_color": "#6B7480", "font_size": 10})
    header_fmt = workbook.add_format({
        "bold": True, "font_color": "#FFFFFF", "bg_color": "#2563EB",
        "border": 1, "align": "center", "valign": "vcenter",
    })
    cell_fmt = workbook.add_format({"border": 1, "valign": "vcenter"})
    cell_center = workbook.add_format({"border": 1, "align": "center", "valign": "vcenter"})
    cell_wrap = workbook.add_format({"border": 1, "valign": "top", "text_wrap": True})
    total_fmt = workbook.add_format({"bold": True, "border": 1, "align": "center"})
    total_left_fmt = workbook.add_format({"bold": True, "border": 1})

    # ── 汇总 sheet：按负责人聚合，可直接整段复制进群消息催办 ──
    ws_sum = workbook.add_worksheet("汇总")
    ws_sum.merge_range(0, 0, 0, 3, "导入错误名单", title_fmt)
    ws_sum.write(1, 0, f"生成时间：{generated_at}    源文件：{os.path.basename(excel_path)}", sub_fmt)
    ws_sum.write_row(3, 0, ["负责人", "Sheet名称", "错误行数", "主要问题"], header_fmt)

    row = 4
    for (team, sheet_name), entry in summary.items():
        ws_sum.write(row, 0, team, cell_fmt)
        ws_sum.write(row, 1, sheet_name, cell_fmt)
        ws_sum.write(row, 2, entry["count"], cell_center)
        ws_sum.write(row, 3, "；".join(entry["problems"]), cell_wrap)
        row += 1

    ws_sum.write(row, 0, "合计", total_left_fmt)
    ws_sum.write(row, 1, f"{len({s for _, s in summary})} 个 Sheet", total_fmt)
    ws_sum.write(row, 2, sum(e["count"] for e in summary.values()), total_fmt)
    ws_sum.write(row, 3, "修正后请通知数据组补录", total_left_fmt)

    ws_sum.set_column(0, 0, 14)
    ws_sum.set_column(1, 1, 24)
    ws_sum.set_column(2, 2, 10)
    ws_sum.set_column(3, 3, 42)

    # ── 明细 sheet：行级错误，支持筛选 ──
    ws_det = workbook.add_worksheet("明细")
    ws_det.write_row(0, 0, ["Sheet名称", "Excel行号", "列名", "当前值", "问题描述", "负责人"], header_fmt)

    for i, detail in enumerate(detail_rows, start=1):
        ws_det.write(i, 0, detail[0], cell_fmt)
        ws_det.write(i, 1, detail[1], cell_center)
        ws_det.write(i, 2, detail[2], cell_fmt)
        ws_det.write(i, 3, detail[3], cell_wrap)
        ws_det.write(i, 4, detail[4], cell_wrap)
        ws_det.write(i, 5, detail[5], cell_fmt)

    ws_det.freeze_panes(1, 0)
    ws_det.autofilter(0, 0, len(detail_rows), 5)
    ws_det.set_column(0, 0, 22)
    ws_det.set_column(1, 1, 10)
    ws_det.set_column(2, 2, 16)
    ws_det.set_column(3, 3, 34)
    ws_det.set_column(4, 4, 32)
    ws_det.set_column(5, 5, 12)

    workbook.close()
    return out_path
