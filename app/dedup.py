"""数据去重 - 两遍处理（扫描定保留 + XML 手术写全保真输出）

判重键 = 判重列（默认 D 企业名称）经 normalize_dedup_key 规范化；
**去留依据** = 第一列录入时间(A 列 collected_at) 经 parse_date 解析为 date：
同一判重键的多行中，保留录入时间最早者；平手（同日期）保留文件中首次出现者。
空判重键或空/不可解析录入时间的行不参与去重、原样保留。

- 读：python-calamine 单遍流式扫描（不缓存行，内存恒定；文本日期解析结果
  记忆化——周更文件原始值仅数百种，重复值直接查表）
- 写：xlsx_surgery XML 手术 —— 输出 = 源 zip 逐条目复制，唯独勾选去重的
  worksheet XML 行级重写（删重复行 + 行号紧凑重排 + 合并单元格/数据验证/
  超链接/筛选范围修正），未勾选 Sheet 预扫描计数后纯字节泵搬运，
  样式 / 条件格式（重复值标红）/ 列宽 / 超链接 / 保护等全部原样保留
- 两遍：第一遍 calamine 扫描计算每个判重键的保留行（最小录入时间）；
  第二遍按 zip 条目顺序手术写出。手术前先预扫描校验「XML 有值行数 ==
  calamine 行数」并拒止含共享公式的 Sheet，不一致立即作废，绝不带错删行
- 进度三段单调（扫描 → 校验 → 写出），全程不回跳
- 输出永不覆盖任何已有文件：目标 xlsx 或重复清单 CSV 已存在时自动加时间戳
- 中途取消：作废整个输出文件（半去重的文件比没有文件更危险）
"""

import csv
import os
import re
from datetime import datetime

from python_calamine import CalamineWorkbook

from app import logger, xlsx_surgery
from app.date_utils import parse_date
from app.utils import normalize_dedup_key, timestamped_output_candidates

DEDUP_SUFFIX = "_已去重"
DUPLICATES_PREFIX = "重复清单__"

MODE_SHEET = "sheet"    # 按 Sheet 内去重（跨 Sheet 同名保留，与 46 表独立导入语义一致）
MODE_GLOBAL = "global"  # 全局去重（所有选中 Sheet 共用判重记录，跨 Sheet 保留录入时间最早者）

# 录入时间列固定为 A 列（schema: collected_at, excel_index=0, DB date 类型）
_TIME_COL_INDEX = 1

# 已带后缀（含旧时间戳）的源文件名归一：X / X_已去重 / X_已去重_20260905_153012[_2] → X_已去重
_STAMPED_SUFFIX_RE = re.compile(r"_已去重(_\d{8}_\d{6}(?:_\d+)?)?$")


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


def _csv_for_output(out_path: str) -> str:
    """与输出 xlsx 同目录配对的重复清单 CSV 路径「重复清单__原名….csv」。"""
    dir_name, base = os.path.split(out_path)
    return os.path.join(dir_name, DUPLICATES_PREFIX + os.path.splitext(base)[0] + ".csv")


def duplicates_csv_path_for(excel_path: str) -> str:
    """理想重复清单 CSV 路径：与理想输出 xlsx 同名配对「重复清单__原名_已去重.csv」。"""
    return _csv_for_output(output_path_for(excel_path))


def _resolve_output_paths(excel_path: str) -> tuple[str, str]:
    """解析实际输出 (xlsx, csv)：理想名未被占用则直接用；任一已存在或与源文件同名，
    则整体加时间戳（xlsx 与 CSV 配对同一时间戳，同秒冲突加 _2 计数），永不覆盖
    任何已有文件。对已去重文件再去重时，理想名即源文件自身 → 必然走时间戳分支
    生成新副本。
    """
    src = os.path.abspath(excel_path)

    def _free(out: str, csv_path: str) -> bool:
        return (os.path.abspath(out) != src
                and not os.path.exists(out) and not os.path.exists(csv_path))

    plain_out = output_path_for(excel_path)
    plain_csv = duplicates_csv_path_for(excel_path)
    if _free(plain_out, plain_csv):
        return plain_out, plain_csv

    stem = os.path.splitext(plain_out)[0]
    for out in timestamped_output_candidates(stem, ".xlsx"):
        csv_path = _csv_for_output(out)
        if _free(out, csv_path):
            return out, csv_path


def run_dedup(excel_path: str, selected_sheet_names: list = None,
              mode: str = MODE_SHEET, audit_col_index: int = 4,
              progress_callback=None, cancel_check=None) -> dict:
    """执行去重，输出全格式保真的新 Excel（勾选的 Sheet 去重、其余原样搬运）。

    参数:
        excel_path: 源 .xlsx 路径
        selected_sheet_names: 需要去重的 Sheet 名列表（未列出的整表复制）
        mode: MODE_SHEET / MODE_GLOBAL
        audit_col_index: 判重列（1-based，如 4 = D 列企业名称）
        progress_callback: (current, total, message) 进度回调；三段单调
            （扫描 → 校验 → 写出），current/total 全程递增不回跳
        cancel_check: 无参回调，返回 True 时停止并作废整个输出文件

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
        （如「原名_已去重_20260905_153012.xlsx」，同秒冲突加 _2 计数），xlsx 与
        CSV 配对同一时间戳。
        中途取消作废整个输出文件（不产出半去重文件），cancelled=True。
        异常不向外抛，统一放入 error 字段（与 importer.run_import 契约一致；
        PanicException 等非 Exception 派生错误同样收敛，避免工作线程无信号终止）。
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
    # 作用域键 -> 保留行信息 {"time": date, "sheet": str, "row_num": int,
    #                        "raw_key": str, "raw_time": str}
    # 仅当严格更早 (t < existing.time) 时替换；相等不替换 → 平手保留首次出现
    keepers = {}
    # 作用域键 -> 全部落败行 [(Sheet, 行号, 原始键值, 录入时间原始值), ...]
    # （含被更早时间顶替的原保留行；扫描结束即成完整对照，供重复清单 CSV 使用）
    deleted_records = {}
    # Sheet 名 -> calamine 有值行数（含表头）；数据行数 = max(0, 有值行数 - 1)
    sheet_valued = {}
    wb = None
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

    def _register_deleted(scope_key, sheet_name, row_num, raw_key_str, raw_time_str):
        deleted_records.setdefault(scope_key, []).append(
            (sheet_name, row_num, raw_key_str, raw_time_str))

    def _sheet_row(name, total, deleted_cnt, unfinished):
        """结果表统一行结构（取消/成功两条统计路径共用同一构造点）。"""
        return {"sheet": name, "total": total, "kept": total - deleted_cnt,
                "deleted": deleted_cnt, "copied_only": name not in selected,
                "unfinished": unfinished}

    try:
        # sheet 名 → XML 条目映射提前解析：进度分母与缺失检查都依赖
        entries = xlsx_surgery.sheet_xml_entries(excel_path)

        # ── Pass 1: calamine 流式扫描，计算每个判重键的保留行（不缓存行数据）──
        wb = CalamineWorkbook.from_path(excel_path)
        all_names = list(wb.sheet_names)
        selected_names = [n for n in all_names if n in selected]

        missing = [n for n in selected_names if n not in entries]
        if missing:
            raise xlsx_surgery.SurgeryError(
                f"无法在源文件中定位 Sheet 的 XML：{('、'.join(missing))[:200]}")

        count_names = [n for n in all_names if n not in selected and n in entries]
        # 进度三段单调：扫描 0..n_sel → 校验+写出 n_sel..n_sel+2*n_pre
        n_sel = len(selected_names)
        n_pre = n_sel + len(count_names)
        grand_total = n_sel + 2 * n_pre

        # 文本日期解析结果记忆化：周更文件原始值仅数百种，重复值直接查表
        time_memo = {}
        # 原始键值/时间值字符串驻留：同键重复行共享同一字符串对象，显著降内存
        str_memo = {}

        def _intern(val):
            s = str_memo.get(val)
            if s is None:
                s = "" if val is None else str(val)
                str_memo[val] = s
            return s

        for i, sheet_name in enumerate(selected_names):
            if cancel_check and cancel_check():
                cancelled = True
                break
            if progress_callback:
                progress_callback(
                    i, grand_total,
                    f"正在扫描 ({i + 1}/{n_sel}): {sheet_name}")
            try:
                rows_iter = wb.get_sheet_by_name(sheet_name).iter_rows()
                header = next(rows_iter, None)
            except BaseException:
                # 全空 Sheet 触发 calamine 的 Rust panic（PanicException 不继承
                # Exception，get_sheet_by_name/iter_rows/next 均可能触发）：按 0 行
                # 处理，正常走后续流程而非整单失败。若 panic 发生在行迭代中途，
                # 截断的行数会在手术预扫描的对齐校验中暴露并作废，fail-closed
                header = None
                rows_iter = iter(())
            data_rows = 0
            row_num = 2  # 数据从第 2 行开始
            for row in rows_iter:
                if cancel_check and cancel_check():
                    cancelled = True
                    break
                data_rows += 1
                # 判重键 + 录入时间
                raw_key = (row[audit_col_index - 1]
                           if len(row) >= audit_col_index else None)
                key = normalize_dedup_key(raw_key)
                raw_time_val = (row[_TIME_COL_INDEX - 1]
                                if len(row) >= _TIME_COL_INDEX else None)
                if key and isinstance(raw_time_val, str):
                    if raw_time_val in time_memo:
                        t = time_memo[raw_time_val]
                    else:
                        t = time_memo[raw_time_val] = parse_date(raw_time_val)
                else:
                    t = parse_date(raw_time_val) if key else None
                if key and t is not None:
                    scope_key = key if mode == MODE_GLOBAL else (sheet_name, key)
                    raw_key_str = _intern(raw_key)
                    raw_time_str = _intern(raw_time_val)
                    cur = keepers.get(scope_key)
                    if cur is not None and not t < cur["time"]:
                        # 新行不更早（含平手）：新行落败，原保留行不变
                        _register_deleted(scope_key, sheet_name, row_num,
                                          raw_key_str, raw_time_str)
                    else:
                        if cur is not None:
                            # 新行更早：原保留行落败，登记后顶替
                            _register_deleted(scope_key, cur["sheet"], cur["row_num"],
                                              cur["raw_key"], cur["raw_time"])
                        keepers[scope_key] = {
                            "time": t, "sheet": sheet_name, "row_num": row_num,
                            "raw_key": raw_key_str, "raw_time": raw_time_str,
                        }
                row_num += 1
            sheet_valued[sheet_name] = data_rows + (1 if header is not None else 0)
            if cancelled:
                break

        # 及时释放源文件句柄（后续手术阶段改用 zipfile 流式读取）
        try:
            wb.close()
        except Exception:
            pass
        wb = None

        if cancelled:
            # 扫描未完成：无法可靠写出，不产生输出文件
            result["pending_sheets"] = list(all_names)
            result["cancelled"] = True
            _finish_timing()
        else:
            # 落败行号按 Sheet 归并（扫描后一次性推导，避免双结构并行维护漂移）
            deleted_rows_by_sheet = {}
            for recs in deleted_records.values():
                for sh, rn, _, _ in recs:
                    deleted_rows_by_sheet.setdefault(sh, set()).add(rn)

            # ── Pass 2: XML 手术写出（全格式保真）──
            surgery_targets = {
                entries[n]: (deleted_rows_by_sheet.get(n, set()), sheet_valued[n])
                for n in selected_names
            }
            count_entries = [entries[n] for n in count_names]
            entry_names = {entry: n for n, entry in entries.items()}

            def _surgery_progress(current, _total, message):
                # 手术层报 0..2*n_pre，整体叠加扫描段偏移后全程单调
                progress_callback(n_sel + current, grand_total, message)

            try:
                stats = xlsx_surgery.rewrite_workbook(
                    excel_path, out_path, surgery_targets,
                    count_entries=count_entries, entry_names=entry_names,
                    progress_callback=_surgery_progress if progress_callback else None,
                    cancel_check=cancel_check)
            except xlsx_surgery.Cancelled as c:
                cancelled = True
                stats = c.stats

            if cancelled:
                # 作废整个输出文件：半去重的文件比没有文件更危险
                _remove_partial()
                result["cancelled"] = True
            else:
                result["output_path"] = out_path
                # 重复清单数据：按保留行首次出现顺序写出（deleted_records 键
                # 必为保留键，二者同源，无需再组装中间结构）
                if deleted_records:
                    _write_duplicates_csv(csv_path, keepers, deleted_records)
                    result["duplicates_csv"] = csv_path
                result["success"] = True

            # 逐 Sheet 结果统计（取消/成功共用一条路径；复制 Sheet 行数来自手术统计）
            stats_by_name = {entry_names.get(e): st for e, st in stats.items()}
            unfinished_marked = False
            for n in all_names:
                st = stats_by_name.get(n)
                if st is not None:
                    total = (max(0, sheet_valued.get(n, 0) - 1) if n in selected
                             else max(0, st.get("calamine_rows", 0) - 1))
                    deleted_cnt = st.get("deleted", 0) if n in selected else 0
                    result["sheets"].append(_sheet_row(n, total, deleted_cnt, False))
                    result["total_rows"] += total
                    result["total_deleted"] += deleted_cnt
                elif cancelled and not unfinished_marked:
                    # 首个未完成 Sheet 标注（其后的进待处理清单）
                    unfinished_marked = True
                    result["sheets"].append(_sheet_row(
                        n, max(0, sheet_valued.get(n, 0) - 1) if n in selected else 0,
                        0, True))
                elif cancelled:
                    result["pending_sheets"].append(n)
                else:
                    # 成功路径上不在手术统计中的 Sheet（如无 worksheet XML 的图表
                    # Sheet）：0 行原样，不计未完成
                    result["sheets"].append(_sheet_row(n, 0, 0, False))
            _finish_timing()

    except PermissionError as e:
        _finish_timing()
        locked = getattr(e, "filename", None)
        if locked and os.path.abspath(locked) == os.path.abspath(excel_path):
            result["error"] = ("源文件被占用（可能正在 Excel/WPS 中打开或被"
                               "同步盘/杀毒锁定），请关闭后重试")
        else:
            result["error"] = "输出文件被占用（可能正在 Excel 中打开），请关闭后重试"
        _remove_partial()
    except Exception as e:
        _finish_timing()
        result["error"] = str(e)
        _remove_partial()
    except BaseException as e:
        # PanicException（如全空 Sheet 触发 calamine 的 Rust panic）不继承
        # Exception，同样收敛为 error 结果，避免工作线程无信号终止
        _finish_timing()
        result["error"] = f"{type(e).__name__}: {e}".rstrip(": ")
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


def _write_duplicates_csv(csv_path: str, keepers: dict, deleted_records: dict) -> None:
    """写出保留/删除对照清单（UTF-8-SIG，Excel 直接打开中文不乱码）。

    长表结构：同一判重键的保留行与其全部删除行相邻成组，组间按保留行首次
    出现顺序排列；保留/删除各自显示自己的判重列原始值与录入时间原始值，
    全角/半角、空格差异一目了然（这正是它们被判为重复的原因）。仅收录有
    删除记录的键。
    """
    with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(["处理", "Sheet名称", "Excel行号", "判重列原始值", "录入时间"])
        for scope_key, v in keepers.items():
            recs = deleted_records.get(scope_key)
            if not recs:
                continue
            writer.writerow(["保留", v["sheet"], v["row_num"],
                             v["raw_key"], v["raw_time"]])
            for sheet, row, raw_key, raw_time in recs:
                writer.writerow(["删除", sheet, row, raw_key, raw_time])
