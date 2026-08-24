"""四方数据导入工具 - 应用入口"""

import sys
import traceback

from PySide6.QtWidgets import QApplication, QMessageBox

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


def _try_auto_connect() -> tuple | None:
    """尝试自动连接上次使用的数据库。

    返回 (conn, schema, connection_name, db_info) 元组，失败返回 None。
    """
    last_cfg = local_db.get_last_connection()
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


def main():
    sys.excepthook = _global_excepthook

    app = QApplication(sys.argv)
    app.setApplicationName("四方数据导入工具")
    apply_theme(app)

    skip_auto_connect = False

    while True:
        conn = None
        schema = "dbo"
        conn_name = ""
        db_info = ""

        # 第一次启动尝试自动连接；切换连接时直接弹对话框
        if not skip_auto_connect:
            auto_result = _try_auto_connect()
            if auto_result:
                conn, schema, conn_name, db_info = auto_result

        if conn is None:
            # 弹出连接管理对话框
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

        # 重置标志，下次循环默认自动连接（正常重启时）
        # 如果是切换连接触发的循环，下面会设置skip_auto_connect为False吗？
        # 不——切换连接时，我们已经走完对话框了，下一轮如果再切还是会弹框，所以正常走完后重置
        skip_auto_connect = False

        # 创建主窗口
        window = MainWindow(conn, db_info, schema, connection_name=conn_name)

        # 监听切换连接请求
        switch_requested = {"flag": False}

        def _on_switch():
            switch_requested["flag"] = True

        window.connection_switch_requested.connect(_on_switch)
        window.show()

        app.exec()

        # 检查是否需要切换连接
        if switch_requested["flag"]:
            skip_auto_connect = True
            try:
                if conn:
                    conn.close()
            except Exception:
                pass
            continue
        else:
            # 用户正常关闭窗口，退出
            break


if __name__ == "__main__":
    main()
