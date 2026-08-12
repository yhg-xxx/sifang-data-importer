"""日志记录 - 记录导入历史"""

import os
import sys

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
    """追加写入日志；Windows 下对文件头加锁，尽力避免多实例交错写入。"""
    try:
        import msvcrt
    except ImportError:
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


def log_import(result: dict) -> None:
    """追加一条导入日志。

    result 期望包含:
        - success: bool
        - file: str
        - start_time: str
        - end_time: str
        - tables: dict[str, int]  表名 -> 行数
        - error: str (optional)
    """
    lines = [SEPARATOR, f"开始时间: {result.get('start_time', '')}", f"结束时间: {result.get('end_time', '')}",
             f"状态: {'成功' if result.get('success') else '失败'}", f"文件: {result.get('file', '')}",
             f"表数: {len(result.get('tables', {}))}"]

    if not result.get("success") and result.get("error"):
        lines.append(f"错误: {result['error']}")

    lines.append("详情:")
    for table_name, row_count in result.get("tables", {}).items():
        lines.append(f"  {table_name}: {row_count} 行")

    lines.append("")

    log_path = _get_log_path()
    _rotate_if_needed(log_path)
    _append_text(log_path, "\n".join(lines))
