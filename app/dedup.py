"""数据去重 - 流式读取 + 内存判重 + 只写保留行到全新 Excel

与旧去重工具（Go 引擎直接改写 xlsx 内部 XML、删行后上移）不同：
本模块单遍流式处理，重复行根本不写入输出文件，
「阶段2 残留删不净」类问题在结构上不存在。

- 读：python-calamine 一次载入、多 Sheet 复用（与导入流程同一套）
- 写：xlsxwriter constant_memory 模式，逐行落盘、内存恒定
- 判重键 = 判重列值经 normalize_dedup_key 规范化（strip + 全角转半角）；
  空键不参与判重（行保留，交给「验证数据」报 NOT NULL）
- 未勾选的 Sheet 原样复制进输出文件，保证交付文件完整
- 输出永不覆盖任何已有文件：目标 xlsx 或重复清单 CSV 已存在时自动加时间戳
"""

import csv
import os
import re
from datetime import date, datetime, time

import xlsxwriter
from python_calamine import CalamineWorkbook

from app import logger
from app.utils import normalize_dedup_key

DEDUP_SUFFIX = "_已去重"
DUPLICATES_SUFFIX = "__重复清单"

MODE_SHEET = "sheet"    # 按 Sheet 内去重（跨 Sheet 同名保留，与 46 表独立导入语义一致）
MODE_GLOBAL = "global"  # 全局去重（所有选中 Sheet 共用判重记录，按文件内 Sheet 顺序保留首个）

_DATETIME_FORMAT = "yyyy-mm-dd hh:mm:ss"
_TIME_FORMAT = "hh:mm:ss"

# 已带后缀（含旧时间戳）的源文件名归一：X / X_已去重 / X_已去重_20260905_153012[_2] → X_已去重
_STAMPED_SUFFIX_RE = re.compile(r"_已去重(_\d{8}_\d{6}(?:_\d+)?)?$")
_STAMP_FORMAT = "%Y%m%d_%H%M%S"


def output_path_for(excel_path: str) -> str:
    """理想输出路径：源文件同目录「原名_已去重.xlsx」（已带后缀/旧时间戳则归一，不叠加）。

    仅用于展示与推导；实际写入路径见 _resolve_output_paths（已存在时加时间戳）。
    """
    dir_name = os.path.dirname(excel_path)
    stem, _ = os.path.splitext(os.path.basename(excel_path))
    m = _STAMPED_SUFFIX_RE.search(stem)
    if not m:
        stem += DEDUP_SUFFIX
    else:
        stem = stem[: m.start()] + DEDUP_SUFFIX
    return os.path.join(dir_name, stem + ".xlsx")


def duplicates_csv_path_for(excel_path: str) -> str:
    """理想重复清单 CSV 路径：与理想输出 xlsx 同名配对「原名_已去重__重复清单.csv」。"""
    stem, _ = os.path.splitext(output_path_for(excel_path))
    return stem + DUPLICATES_SUFFIX + ".csv"


def _resolve_output_paths(excel_path: str) -> tuple[str, str]:
    """解析实际输出 (xlsx, csv)：理想名未被占用则直接用；任一已存在或与源文件同名，
    则整体加时间戳（xlsx 与 CSV 配对同一时间戳），永不覆盖任何已有文件。
    对已去重文件再去重时，理想名即源文件自身 → 必然走时间戳分支生成新副本。
    """
    src = os.path.abspath(excel_path)

    def _free(out: str, csv_path: str) -> bool:
        return (os.path.abspath(out) != src
                and not os.path.exists(out) and not os.path.exists(csv_path))

    plain_out = output_path_for(excel_path)
    plain_csv = duplicates_csv_path_for(excel_path)
    if _free(plain_out, plain_csv):
        return plain_out, plain_csv

    stem, _ = os.path.splitext(plain_out)
    stamp = datetime.now().strftime(_STAMP_FORMAT)
    n = 0
    while True:
        suffix = f"_{stamp}" if n == 0 else f"_{stamp}_{n}"
        out = f"{stem}{suffix}.xlsx"
        csv_path = f"{stem}{suffix}{DUPLICATES_SUFFIX}.csv"
        if _free(out, csv_path):
            return out, csv_path
        n += 1


def run_dedup(excel_path: str, selected_sheet_names: list = None,
              mode: str = MODE_SHEET, audit_col_index: int = 4,
              progress_callback=None, cancel_check=None) -> dict:
    """执行去重，输出全新 Excel（勾选的 Sheet 去重、其余原样复制）。

    参数:
        excel_path: 源 .xlsx 路径
        selected_sheet_names: 需要去重的 Sheet 名列表（未列出的整表复制）
        mode: MODE_SHEET / MODE_GLOBAL
        audit_col_index: 判重列（1-based，如 4 = D 列企业名称）
        progress_callback: (current, total, message) 进度回调
        cancel_check: 无参回调，返回 True 时在当前行停止（输出文件保留已处理部分）

    返回:
        {
            "success": bool, "cancelled": bool,
            "file": str, "mode": str, "audit_col_index": int,
            "output_path": str, "duplicates_csv": str,
            "total_rows": int, "total_deleted": int,
            "sheets": [{"sheet", "total", "kept", "deleted", "copied_only", "unfinished"}],
            "pending_sheets": [str],   # 取消时未处理的 Sheet 名
            "start_time": str, "end_time": str, "elapsed": float,
            "error": str,
        }
        输出永不覆盖任何已有文件：目标 xlsx 或重复清单 CSV 已存在时整体加时间戳
        （如「原名_已去重_20260905_153012.xlsx」），xlsx 与 CSV 配对同一时间戳。
        异常不向外抛，统一放入 error 字段（与 importer.run_import 契约一致）。
    """
    start_dt = datetime.now()
    selected = set(selected_sheet_names or [])
    # 输出永不覆盖：目标已存在（含对已去重文件再去重，理想名即源文件自身）时自动
    # 加时间戳生成新副本；实际写入路径必然不同于源文件，无原位替换场景
    out_path, csv_path = _resolve_output_paths(excel_path)

    result = {
        "success": False, "cancelled": False,
        "file": excel_path, "mode": mode, "audit_col_index": audit_col_index,
        "output_path": "", "duplicates_csv": "",
        "total_rows": 0, "total_deleted": 0,
        "sheets": [], "pending_sheets": [],
        "start_time": start_dt.strftime("%Y-%m-%d %H:%M:%S"),
        "end_time": "", "elapsed": 0.0, "error": "",
    }
    # 判重作用域键 -> {"kept": (Sheet, 行号, 原始值), "deleted": [(Sheet, 行号, 原始值), ...]}；
    # 全局模式键为判重键本身，按 Sheet 模式键为 (Sheet名, 判重键)，两口径互不混组。
    # dict 保持插入序：对照组按保留行首次出现顺序排列
    groups = {}
    wb = None
    book = None
    cancelled = False

    def _finish_timing():
        end_dt = datetime.now()
        result["end_time"] = end_dt.strftime("%Y-%m-%d %H:%M:%S")
        result["elapsed"] = round((end_dt - start_dt).total_seconds(), 1)

    def _remove_partial():
        """清理半成品输出（resolver 保证输出路径不等于源文件，删除安全）。"""
        try:
            if os.path.exists(out_path) and os.path.abspath(out_path) != os.path.abspath(excel_path):
                os.remove(out_path)
        except OSError:
            pass

    try:
        wb = CalamineWorkbook.from_path(excel_path)
        book = xlsxwriter.Workbook(out_path, {"constant_memory": True})
        # constant_memory 模式惯例：格式在写任何数据前创建
        date_fmt = book.add_format({"num_format": _DATETIME_FORMAT})
        time_fmt = book.add_format({"num_format": _TIME_FORMAT})

        all_names = list(wb.sheet_names)
        total = len(all_names)

        for i, sheet_name in enumerate(all_names):
            if cancel_check and cancel_check():
                cancelled = True
                break
            is_selected = sheet_name in selected
            action = "去重" if is_selected else "复制"
            if progress_callback:
                progress_callback(i, total, f"正在{action} ({i + 1}/{total}): {sheet_name}")

            ws_out = book.add_worksheet(sheet_name)
            rows_iter = wb.get_sheet_by_name(sheet_name).iter_rows()

            # 表头原样写出
            header = next(rows_iter, None)
            if header is not None:
                _write_row(ws_out, 0, list(header), date_fmt, time_fmt)

            out_row = 1
            row_num = 2  # 实际 Excel 行号（数据从第 2 行开始，含被跳过的重复行）
            sheet_total = 0
            sheet_deleted = 0
            for row in rows_iter:
                if cancel_check and cancel_check():
                    cancelled = True
                    break
                values = list(row)
                sheet_total += 1
                if is_selected:
                    raw_key = values[audit_col_index - 1] if len(values) >= audit_col_index else None
                    key = normalize_dedup_key(raw_key)
                    if key:
                        raw_val = "" if raw_key is None else str(raw_key)
                        scope_key = key if mode == MODE_GLOBAL else (sheet_name, key)
                        grp = groups.get(scope_key)
                        if grp is not None:
                            sheet_deleted += 1
                            grp["deleted"].append((sheet_name, row_num, raw_val))
                            row_num += 1
                            continue
                        groups[scope_key] = {
                            "kept": (sheet_name, row_num, raw_val),
                            "deleted": [],
                        }
                _write_row(ws_out, out_row, values, date_fmt, time_fmt)
                out_row += 1
                row_num += 1

            result["sheets"].append({
                "sheet": sheet_name, "total": sheet_total,
                "kept": sheet_total - sheet_deleted, "deleted": sheet_deleted,
                "copied_only": not is_selected, "unfinished": cancelled,
            })
            result["total_rows"] += sheet_total
            result["total_deleted"] += sheet_deleted
            if progress_callback:
                if is_selected:
                    summary = (f"{sheet_name}: 共 {sheet_total} 行，"
                               f"删除 {sheet_deleted} 行，保留 {sheet_total - sheet_deleted} 行")
                else:
                    summary = f"{sheet_name}: 原样复制 {sheet_total} 行"
                progress_callback(i, total, summary)

            if cancelled:
                break

        result["pending_sheets"] = all_names[len(result["sheets"]):]

        # constant_memory 模式在 close 时才真正打包输出文件。
        # 取消时可能一个 Sheet 都没写（close 有可能失败），吞掉不影响「已取消」语义
        close_ok = True
        try:
            book.close()
        except Exception:
            close_ok = False
            if not cancelled:
                raise
        if wb is not None:
            try:
                wb.close()  # 及时释放源文件句柄
            except Exception:
                pass
            wb = None

        if close_ok and os.path.exists(out_path):
            result["output_path"] = out_path
            if any(g["deleted"] for g in groups.values()):
                _write_duplicates_csv(csv_path, groups)
                result["duplicates_csv"] = csv_path

        result["success"] = not cancelled
        result["cancelled"] = cancelled
        _finish_timing()
    except PermissionError:
        _finish_timing()
        result["error"] = "输出文件被占用（可能正在 Excel 中打开），请关闭后重试"
        _remove_partial()
    except Exception as e:
        _finish_timing()
        result["error"] = str(e)
        _remove_partial()
    finally:
        if wb is not None:
            try:
                wb.close()
            except Exception:
                pass

    # 日志失败不能把已完成（或已诊断出错误的）去重结果误报为失败
    # （与 run_import 对 log_import 的兜底写法一致）
    try:
        logger.log_dedup(result)
    except Exception:
        pass
    return result


def _write_row(ws, row_idx: int, values: list, date_fmt, time_fmt) -> None:
    """写一行。常规行（纯 str/int/float/None）走 write_row 快路径；
    含日期/时间时逐单元格分发并套格式，避免 Excel 中显示为序列数字。"""
    if not any(isinstance(v, (datetime, date, time)) for v in values):
        ws.write_row(row_idx, 0, values)
        return
    for col, value in enumerate(values):
        if value is None:
            continue  # 空单元格不写
        if isinstance(value, datetime):
            ws.write_datetime(row_idx, col, value, date_fmt)
        elif isinstance(value, date):
            ws.write_datetime(row_idx, col, value, date_fmt)
        elif isinstance(value, time):
            ws.write_time(row_idx, col, value, time_fmt)
        else:
            ws.write(row_idx, col, value)


def _write_duplicates_csv(csv_path: str, groups: dict) -> None:
    """写出保留/删除对照清单（UTF-8-SIG，Excel 直接打开中文不乱码）。

    长表结构：同一判重键的保留行与其全部删除行相邻成组，组间按保留行首次
    出现顺序排列；保留/删除各自显示自己的判重列原始值，全角/半角、空格
    差异一目了然（这正是它们被判为重复的原因）。仅收录有删除记录的键。
    """
    with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(["处理", "Sheet名称", "Excel行号", "判重列原始值"])
        for grp in groups.values():
            if not grp["deleted"]:
                continue
            sheet, row, raw = grp["kept"]
            writer.writerow(["保留", sheet, row, raw])
            for sheet, row, raw in grp["deleted"]:
                writer.writerow(["删除", sheet, row, raw])
