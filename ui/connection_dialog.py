"""数据库连接管理对话框 - 多连接管理"""

from PySide6.QtCore import QThread, Signal, Qt
from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QLineEdit,
    QPushButton,
    QMessageBox,
    QListWidget,
    QListWidgetItem,
    QWidget,
    QSplitter,
    QFrame,
    QLabel,
)

from app import local_db
from app import database as db_module
from app.constants import ERROR_CONTACT
from ui.toast import toast


class ConnectWorker(QThread):
    """后台线程：测试连接或建立连接，避免阻塞 UI。"""

    ok = Signal(object)
    error = Signal(str)

    def __init__(self, server, database, username, password,
                 test_only: bool = False, parent=None):
        super().__init__(parent)
        self._server = server
        self._database = database
        self._username = username
        self._password = password
        self._test_only = test_only

    def run(self):
        try:
            if self._test_only:
                ok, msg = db_module.test_connection(
                    self._server, self._database, self._username, self._password,
                )
                if ok:
                    self.ok.emit(msg)
                else:
                    self.error.emit(msg)
            else:
                conn = db_module.connect(
                    self._server, self._database, self._username, self._password,
                )
                self.ok.emit(conn)
        except Exception as e:
            self.error.emit(str(e))


class ConnectionDialog(QDialog):
    """数据库连接管理对话框 - 支持多连接保存、切换、新增、删除。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("数据库连接管理")
        self.setMinimumWidth(720)
        self.setMinimumHeight(460)
        self.setModal(True)

        self._conn = None
        self._schema = "dbo"
        self._conn_id = None
        self._conn_name = ""
        self._worker = None
        self._pending_params = None
        self._loading_list = False
        self._connections = []
        self._setup_ui()
        self._reload_connection_list()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(12)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        # ── 左侧：连接列表 ──
        left_panel = QFrame()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(8)

        list_label = QLabel("已保存的连接")
        list_label.setProperty("secondary", True)
        left_layout.addWidget(list_label)

        self._conn_list = QListWidget()
        self._conn_list.setMinimumWidth(200)
        self._conn_list.currentRowChanged.connect(self._on_list_selection_changed)
        left_layout.addWidget(self._conn_list, 1)

        list_btn_layout = QHBoxLayout()
        self._add_btn = QPushButton("新增")
        self._add_btn.clicked.connect(self._add_new_connection)
        list_btn_layout.addWidget(self._add_btn)

        self._delete_btn = QPushButton("删除")
        self._delete_btn.clicked.connect(self._delete_connection)
        list_btn_layout.addWidget(self._delete_btn)
        left_layout.addLayout(list_btn_layout)

        splitter.addWidget(left_panel)

        # ── 右侧：连接表单 ──
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(8)

        form = QFormLayout()
        form.setVerticalSpacing(12)

        self._name_edit = QLineEdit()
        self._name_edit.setPlaceholderText("例如：第一组库（表1-50）")
        form.addRow("连接名称:", self._name_edit)

        self._server_edit = QLineEdit()
        self._server_edit.setPlaceholderText("例如：192.168.1.100")
        form.addRow("服务器地址:", self._server_edit)

        self._database_edit = QLineEdit()
        self._database_edit.setPlaceholderText("数据库名称")
        form.addRow("数据库名:", self._database_edit)

        self._schema_edit = QLineEdit()
        self._schema_edit.setPlaceholderText("默认 dbo")
        self._schema_edit.setText("dbo")
        form.addRow("模式(Schema):", self._schema_edit)

        self._username_edit = QLineEdit()
        self._username_edit.setPlaceholderText("用户名")
        form.addRow("用户名:", self._username_edit)

        self._password_edit = QLineEdit()
        self._password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self._password_edit.setPlaceholderText("密码")
        form.addRow("密码:", self._password_edit)
        right_layout.addLayout(form)

        right_layout.addStretch()

        # 按钮行
        btn_layout = QHBoxLayout()
        self._pwd_toggle_btn = QPushButton("显示密码")
        self._pwd_toggle_btn.setCheckable(True)
        self._pwd_toggle_btn.clicked.connect(self._toggle_password_visible)
        btn_layout.addWidget(self._pwd_toggle_btn)
        btn_layout.addSpacing(8)

        self._test_btn = QPushButton("测试连接")
        self._test_btn.clicked.connect(self._test_connection)
        btn_layout.addWidget(self._test_btn)

        btn_layout.addStretch()

        self._connect_btn = QPushButton("连接")
        self._connect_btn.setDefault(True)
        self._connect_btn.setProperty("class", "primary")
        self._connect_btn.clicked.connect(self._connect)
        btn_layout.addWidget(self._connect_btn)

        self._cancel_btn = QPushButton("取消")
        self._cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self._cancel_btn)

        right_layout.addLayout(btn_layout)
        splitter.addWidget(right_panel)

        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([220, 480])

        main_layout.addWidget(splitter, 1)

    def _reload_connection_list(self):
        """重新从数据库加载连接列表。"""
        self._loading_list = True
        self._connections = local_db.get_all_connections()
        self._conn_list.clear()

        last_used_row = 0
        for i, c in enumerate(self._connections):
            display_name = c["name"]
            item = QListWidgetItem(display_name)
            item.setData(Qt.ItemDataRole.UserRole, c["id"])
            self._conn_list.addItem(item)
            # 检查是否是 last_used（第一条就是，因为已按 is_last_used 排序）

        if self._connections:
            self._conn_list.setCurrentRow(0)
            self._fill_form(self._connections[0])
        else:
            self._clear_form()
            self._delete_btn.setEnabled(False)

        self._loading_list = False
        self._update_delete_btn_state()

    def _fill_form(self, conn_cfg: dict):
        """用连接配置填充表单。"""
        self._conn_id = conn_cfg.get("id")
        self._name_edit.setText(conn_cfg.get("name", ""))
        self._server_edit.setText(conn_cfg.get("server", ""))
        self._database_edit.setText(conn_cfg.get("database", ""))
        self._schema_edit.setText(conn_cfg.get("schema", "dbo"))
        self._username_edit.setText(conn_cfg.get("username", ""))
        self._password_edit.setText(conn_cfg.get("password", ""))

    def _clear_form(self):
        """清空表单（新增模式）。"""
        self._conn_id = None
        self._name_edit.clear()
        self._server_edit.clear()
        self._database_edit.clear()
        self._schema_edit.setText("dbo")
        self._username_edit.clear()
        self._password_edit.clear()

    def _toggle_password_visible(self):
        """切换密码显示/隐藏（勾选式按钮）。"""
        if self._pwd_toggle_btn.isChecked():
            self._password_edit.setEchoMode(QLineEdit.EchoMode.Normal)
            self._pwd_toggle_btn.setText("隐藏密码")
        else:
            self._password_edit.setEchoMode(QLineEdit.EchoMode.Password)
            self._pwd_toggle_btn.setText("显示密码")

    def _get_params(self) -> tuple:
        return (
            self._name_edit.text().strip(),
            self._server_edit.text().strip(),
            self._database_edit.text().strip(),
            self._schema_edit.text().strip() or "dbo",
            self._username_edit.text().strip(),
            self._password_edit.text(),
        )

    def _on_list_selection_changed(self, row: int):
        """列表选中项变化时，填充表单。"""
        if self._loading_list:
            return
        if 0 <= row < len(self._connections):
            self._fill_form(self._connections[row])
        else:
            self._clear_form()
        self._update_delete_btn_state()

    def _update_delete_btn_state(self):
        """更新删除按钮可用状态：至少有一个连接时才可用。"""
        self._delete_btn.setEnabled(self._conn_list.count() > 0)

    def _add_new_connection(self):
        """新增连接：清空表单，取消列表选中。"""
        self._loading_list = True
        self._conn_list.clearSelection()
        self._conn_list.setCurrentRow(-1)
        self._loading_list = False
        self._clear_form()
        self._name_edit.setFocus()

    def _delete_connection(self):
        """删除当前选中的连接。"""
        current_item = self._conn_list.currentItem()
        if current_item is None:
            return
        conn_id = current_item.data(Qt.ItemDataRole.UserRole)
        conn_name = current_item.text()

        reply = QMessageBox.question(
            self,
            "删除连接",
            f"确定要删除连接「{conn_name}」吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        local_db.delete_connection(conn_id)
        toast.success(self, f"已删除连接：{conn_name}")
        self._reload_connection_list()

    def _start_worker(self, test_only: bool):
        """启动后台连接线程。"""
        name, server, db_name, schema, username, password = self._get_params()
        if not name:
            name = f"{server}/{db_name}" if server and db_name else ""
        if not server or not db_name:
            toast.warning(self, "请填写服务器地址和数据库名")
            return False

        if test_only:
            self._test_btn.setEnabled(False)
            self._test_btn.setText("测试中...")
        else:
            self._connect_btn.setEnabled(False)
            self._connect_btn.setText("连接中...")
            self._test_btn.setEnabled(False)
        self._pending_params = (name, server, db_name, schema, username, password)

        self._worker = ConnectWorker(
            server, db_name, username, password, test_only=test_only,
        )
        self._worker.finished.connect(self._worker.deleteLater)
        self._worker.ok.connect(
            self._on_test_ok if test_only else self._on_connect_ok
        )
        self._worker.error.connect(
            self._on_test_error if test_only else self._on_connect_error
        )
        self._worker.start()
        return True

    def _test_connection(self):
        self._start_worker(test_only=True)

    def _on_test_ok(self, msg: str):
        self._test_btn.setText("测试连接")
        self._test_btn.setEnabled(True)
        self._connect_btn.setEnabled(True)
        toast.success(self, msg)

    def _on_test_error(self, msg: str):
        self._test_btn.setText("测试连接")
        self._test_btn.setEnabled(True)
        self._connect_btn.setEnabled(True)
        QMessageBox.warning(self, "连接失败", f"{msg}\n\n{ERROR_CONTACT}")

    def _connect(self):
        self._start_worker(test_only=False)

    def _on_connect_ok(self, conn):
        self._connect_btn.setText("连接")
        self._connect_btn.setEnabled(True)
        self._test_btn.setEnabled(True)

        name, server, db_name, schema, username, password = self._pending_params
        self._conn = conn
        self._schema = schema
        self._conn_name = name

        saved_id = local_db.save_connection({
            "id": self._conn_id,
            "name": name,
            "server": server,
            "database": db_name,
            "schema": schema,
            "username": username,
            "password": password,
        })
        self._conn_id = saved_id

        self.accept()

    def _on_connect_error(self, msg: str):
        self._connect_btn.setText("连接")
        self._connect_btn.setEnabled(True)
        self._test_btn.setEnabled(True)
        QMessageBox.critical(
            self,
            "连接失败",
            f"{msg}\n\n{ERROR_CONTACT}",
        )

    @property
    def connection(self):
        return self._conn

    @property
    def schema(self):
        return self._schema

    @property
    def connection_name(self):
        return self._conn_name
