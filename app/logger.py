"""日志记录 - 记录导入历史"""

import os
import sys

try:
    import msvcrt
    _HAS_MSVCRT = True
except ImportError:  # 非 Windows 平台无文件锁
    _HAS_MSVCRT = False

LOG_FILE_NAME = "import_log.txt"
MAX_LOG_SIZE = 1 * 1024 * 1024  # 超过 1MB 轮转归档

SEPARATOR = "=" * 40


def _get_log_dir() -> str:
    """日志文件与 config.ini 同目录。"""
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.getcwd()


def _get_log_path() -> str:
    return os.path.join(_get_log_dir(), LOG_FILE_NAME)


def _rotate_if_needed(log_path: str) -> None:
    """日志超过 MAX_LOG_SIZE 时归档为 import_log.txt.bak（覆盖旧备份）。"""
    try:
        if os.path.exists(log_path) and os.path.getsize(log_path) > MAX_LOG_SIZE:
            backup_path = log_path + ".bak"
            if os.path.exists(backup_path):
                os.remove(backup_path)
            os.rename(log_path, backup_path)
    except OSError:
        pass  # 归档失败不阻断写入


def _append_text(log_path: str, text: str) -> None:
    """追加写入日志；Windows 下对文件头加锁，尽力避免多实例交错写入。

    日志写入永远不向上抛异常：文件被占用、目录只读、磁盘满等失败
    一律静默跳过——日志问题不能破坏导入/去重的结果上报。
    """
    try:
        if not _HAS_MSVCRT:
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(text)
            return

        with open(log_path, "a", encoding="utf-8") as f:
            locked = False
            try:
                f.seek(0)
                msvcrt.locking(f.fileno(), msvcrt.LK_LOCK, 1)
                locked = True
            except OSError:
                pass  # 文件为空或锁失败：尽力而为
            try:
                f.write(text)
                f.flush()
            finally:
                if locked:
                    try:
                        f.seek(0)
                        msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, 1)
                    except OSError:
                        pass
    except OSError:
        pass


def log_import(result: dict) -> None:
    """追加一条导入日志。

    result 期望包含:
        - success: bool（全部成功）
        - partial: bool（部分成功：有失败表但流程完整走完）
        - file: str
        - start_time: str
        - end_time: str
        - tables: dict[str, int]  成功表 -> 行数
        - failed_tables: dict[str, dict]  失败表 -> {"sheet_name": str, "error": str}
        - error: str (optional)
        - error_list_path: str (optional)
    """
    tables = result.get("tables", {})
    failed = result.get("failed_tables") or {}

    if result.get("partial"):
        status = f"部分成功（成功 {len(tables)} / 失败 {len(failed)}）"
    else:
        status = "成功" if result.get("success") else "失败"

    lines = [SEPARATOR, f"开始时间: {result.get('start_time', '')}", f"结束时间: {result.get('end_time', '')}",
             f"状态: {status}", f"文件: {result.get('file', '')}",
             f"表数: {len(tables) + len(failed)}"]

    if not result.get("success") and result.get("error"):
        lines.append(f"错误: {result['error']}")

    if result.get("error_list_path"):
        lines.append(f"错误名单: {result['error_list_path']}")

    lines.append("详情:")
    for table_name, row_count in tables.items():
        lines.append(f"  {table_name}: {row_count} 行")
    if tables:
        lines.append(f"  合计: {len(tables)} 张表，共 {sum(tables.values())} 行")
    for table_name, info in failed.items():
        sheet_name = info.get("sheet_name", "")
        lines.append(f"  {table_name} [{sheet_name}]: 导入失败")
        for ln in (info.get("error") or "").splitlines():
            lines.append(f"    {ln}")
    error_rows = sum(len(info.get("errors") or []) for info in failed.values())
    if error_rows:
        lines.append(f"  错误行合计: {error_rows} 行（{len(failed)} 张失败表）")

    lines.append("")

    log_path = _get_log_path()
    _rotate_if_needed(log_path)
    _append_text(log_path, "\n".join(lines))


def log_dedup(result: dict) -> None:
    """追加一条去重日志（与 log_import 共用文件与轮转/加锁机制）。

    result 期望包含:
        - success: bool
        - cancelled: bool (optional)
        - start_time / end_time: str
        - file / mode / audit_col_index
        - output_path / duplicates_csv: str
        - total_rows / total_deleted: int
        - sheets: [{"sheet", "total", "kept", "deleted", "copied_only", "unfinished"}]
        - pending_sheets: [str] (取消时)
        - error: str (optional)
    """
    if result.get("cancelled"):
        status = "已取消"
    elif result.get("success"):
        status = "成功"
    else:
        status = "失败"

    mode_text = "全局去重" if result.get("mode") == "global" else "按Sheet内去重"
    lines = [SEPARATOR,
             f"[去重] 开始时间: {result.get('start_time', '')}",
             f"[去重] 结束时间: {result.get('end_time', '')}",
             f"[去重] 状态: {status}",
             f"[去重] 源文件: {result.get('file', '')}",
             f"[去重] 模式: {mode_text}（判重列第 {result.get('audit_col_index', '')} 列）"]

    if result.get("output_path"):
        lines.append(f"[去重] 输出文件: {result['output_path']}")
    if result.get("duplicates_csv"):
        lines.append(f"[去重] 重复清单: {result['duplicates_csv']}")

    lines.append(f"[去重] 总行数: {result.get('total_rows', 0)}，删除重复: {result.get('total_deleted', 0)}")

    if not result.get("success") and result.get("error"):
        lines.append(f"[去重] 错误: {result['error']}")
    if result.get("pending_sheets"):
        lines.append(f"[去重] 未处理 Sheet: {'、'.join(result['pending_sheets'])}")

    lines.append("去重详情:")
    for s in result.get("sheets", []):
        if s.get("copied_only"):
            lines.append(f"  {s['sheet']}: 原样复制 {s['total']} 行")
        else:
            mark = "（未完成）" if s.get("unfinished") else ""
            lines.append(f"  {s['sheet']}: 共 {s['total']} 行，删除 {s['deleted']} 行，保留 {s['kept']} 行{mark}")

    lines.append("")

    log_path = _get_log_path()
    _rotate_if_needed(log_path)
    _append_text(log_path, "\n".join(lines))


def log_uncaught(detail: str) -> None:
    """记录未捕获异常文本（供全局 excepthook 兜底：无控制台的 windowed
    exe 与工作线程场景下，异常至少在日志中留痕）。"""
    log_path = _get_log_path()
    _rotate_if_needed(log_path)
    _append_text(log_path, f"[未捕获异常]\n{detail}\n\n")
