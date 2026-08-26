"""四方数据导入工具 - 应用入口"""

import sys
import traceback

from PySide6.QtWidgets import QApplication, QMessageBox, QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import QThread, Signal, QEventLoop

from ui.connection_dialog import ConnectionDialog
from ui.main_window import MainWindow
from ui.theme import apply_theme

# ── 初始化本地 SQLite 数据库 ──
from app import local_db
local_db.init_db()

from app import database as db_module
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


def _try_auto_connect_sync(last_cfg: dict | None) -> tuple | None:
    """用给定配置尝试自动连接上次使用的数据库（在后台线程中调用）。

    返回 (conn, schema, connection_name, db_info) 元组，失败返回 None。
    """
    if not last_cfg:
        return None
    try:
        conn = db_module.connect(
            last_cfg["server"],
            last_cfg["database"],
            last_cfg["username"],
            last_cfg["password"],
        )
        db_info = f"{last_cfg['server']}/{last_cfg['database']} (schema: {last_cfg['schema']})"
        return (conn, last_cfg["schema"], last_cfg["name"], db_info)
    except Exception:
        return None


class AutoConnectThread(QThread):
    """后台线程：尝试自动连接，避免启动阶段阻塞 GUI 线程。"""
    result_ready = Signal(object)

    def __init__(self, last_cfg, parent=None):
        super().__init__(parent)
        self._last_cfg = last_cfg

    def run(self):
        self.result_ready.emit(_try_auto_connect_sync(self._last_cfg))


def _try_auto_connect_async(app: QApplication) -> tuple | None:
    """在独立线程中尝试自动连接，期间显示「正在连接…」遮罩，避免无窗口冻结。"""
    last_cfg = local_db.get_last_connection()
    if not last_cfg:
        return None

    overlay = QWidget()
    overlay.setWindowTitle("四方数据导入工具")
    overlay_layout = QVBoxLayout(overlay)
    overlay_layout.addWidget(QLabel("正在自动连接上次使用的数据库…"))
    overlay.setFixedSize(340, 90)
    overlay.show()
    app.processEvents()

    worker = AutoConnectThread(last_cfg)
    loop = QEventLoop()
    result_box = {}

    def _on_result(r):
        result_box["result"] = r
        loop.quit()

    worker.result_ready.connect(_on_result)
    worker.start()
    loop.exec()        # 运行真实事件循环，遮罩可正常重绘
    worker.wait()

    overlay.close()
    return result_box.get("result")


def main():
    sys.excepthook = _global_excepthook

    app = QApplication(sys.argv)
    app.setApplicationName("四方数据导入工具")
    apply_theme(app)

    switch_requested = {"flag": False}    # 本轮主窗口是否因“连接管理”而关闭
    skip_auto_connect = {"flag": False}   # 下一轮是否跳过自动连接（刚切换完，让用户重选）

    def run_main_window(conn, db_info, schema, conn_name):
        window = MainWindow(conn, db_info, schema, connection_name=conn_name)

        def _on_switch():
            switch_requested["flag"] = True

        window.connection_switch_requested.connect(_on_switch)
        window.show()
        app.exec()
        window.close()

    while True:
        conn = None
        schema = "dbo"
        conn_name = ""
        db_info = ""

        # 刚切换过连接 -> 不自动连，直接进入连接管理让用户重选
        if not skip_auto_connect["flag"]:
            auto_result = _try_auto_connect_async(app)
            if auto_result:
                conn, schema, conn_name, db_info = auto_result

        if conn is None:
            dialog = ConnectionDialog()
            if dialog.exec() != ConnectionDialog.DialogCode.Accepted:
                return  # 用户取消，退出应用

            conn = dialog.connection
            schema = dialog.schema
            conn_name = dialog.connection_name
            if conn is None:
                return
            db_info = ""
            cfg = local_db.get_last_connection()
            if cfg:
                db_info = f"{cfg['server']}/{cfg['database']} (schema: {schema})"

        run_main_window(conn, db_info, schema, conn_name)

        if switch_requested["flag"]:
            switch_requested["flag"] = False   # 复位：下一轮主窗口视为正常关闭
            skip_auto_connect["flag"] = True   # 下一轮不自动连，让用户选库
            try:
                if conn:
                    conn.close()
            except Exception:
                pass
            continue
        else:
            # 用户正常关闭窗口（含点 ✕），退出
            skip_auto_connect["flag"] = False
            break


if __name__ == "__main__":
    main()
