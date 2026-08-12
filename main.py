"""四方数据导入工具 - 应用入口"""

import sys
import traceback

from PySide6.QtWidgets import QApplication, QMessageBox

from ui.connection_dialog import ConnectionDialog
from ui.main_window import MainWindow

# ── 初始化本地 SQLite 数据库 ──
from app import local_db
local_db.init_db()

from app.constants import ERROR_CONTACT


def _global_excepthook(exc_type, exc_value, exc_tb):
    """全局未捕获异常处理，弹出统一错误提示。"""
    detail = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
    QMessageBox.critical(
        None,
        "程序错误",
        f"{exc_value}\n\n{ERROR_CONTACT}",
    )
    print(detail, file=sys.stderr)


def main():
    sys.excepthook = _global_excepthook

   

    app = QApplication(sys.argv)
    app.setApplicationName("四方数据导入工具")

    # ── 连接对话框 ──
    conn_dialog = ConnectionDialog()
    if conn_dialog.exec() != ConnectionDialog.Accepted:
        return  # 用户取消则退出

    conn = conn_dialog.connection
    schema = conn_dialog.schema
    if conn is None:
        return

    from app import config
    cfg = config.load_config()
    db_info = f"{cfg.get('server', '')}/{cfg.get('database', '')} (schema: {schema})"

    window = MainWindow(conn, db_info, schema)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
