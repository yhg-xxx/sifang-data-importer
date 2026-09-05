"""主窗口"""

import time

from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QFrame,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QApplication,
    QCheckBox,
    QTableWidget,
    QTableWidgetItem,
    QAbstractItemView,
    QHeaderView,
    QFileDialog,
    QMessageBox,
)
from PySide6.QtCore import Qt, QThread, QTimer, Signal
from PySide6.QtGui import QAction, QBrush, QColor, QKeySequence

from app import excel_reader, local_db
from app.constants import ERROR_CONTACT
from ui.import_dialog import ImportDialog
from ui.validate_dialog import ValidateDialog
from ui.dedup_settings_dialog import DedupSettingsDialog
from ui.dedup_dialog import DedupDialog
from ui.sheet_directory_dialog import SheetDirectoryDialog
from ui.column_mapping_dialog import ColumnMappingDialog
from ui.toast import toast
from ui.confirm_dialog import ConfirmDialog
from ui.theme import DANGER, TEXT


class SheetReaderWorker(QThread):
    """后台线程：读取 Excel 全部 sheet 名称。"""
    finished = Signal(list)
    error = Signal(str)

    def __init__(self, filepath: str, parent=None):
        super().__init__(parent)
        self._filepath = filepath

    def run(self):
        try:
            sheets = excel_reader.read_sheets(self._filepath)
            self.finished.emit(sheets)
        except Exception as e:
            self.error.emit(str(e))


class MainWindow(QMainWindow):
    """用户成功连接数据库后显示的主窗口。"""

    connection_switch_requested = Signal()

    def __init__(self, conn, db_info: str, schema: str = "dbo", connection_name: str = "", parent=None):
        super().__init__(parent)
        self._conn = conn
        self._db_info = db_info
        self._schema = schema
        self._connection_name = connection_name
        self._excel_path = ""
        self._sheets = []
        self._reader_worker = None
        self._load_timer = None
        self._load_start_time = 0.0
        self._loading_file_name = ""
        self._updating_header = False  # 防止表头 checkbox 更新递归
        self._anchor_row = -1  # Shift 范围勾选的锚点行
        self._help_dlg = None  # 使用说明窗口（非模态，复用同一实例）

        self.setWindowTitle("四方数据导入工具")
        self.setMinimumSize(900, 620)

        self._setup_ui()
        self._setup_status_bar()

    def _setup_ui(self):
        # ── 菜单栏 ──
        menu_bar = self.menuBar()

        switch_conn_action = QAction("连接管理", self)
        switch_conn_action.setShortcut(QKeySequence("Ctrl+Shift+C"))
        switch_conn_action.triggered.connect(self._switch_connection)
        menu_bar.addAction(switch_conn_action)

        dir_action = QAction("Sheet名-表映射", self)
        dir_action.setShortcut(QKeySequence("Ctrl+N"))
        dir_action.triggered.connect(self._open_sheet_directory)
        menu_bar.addAction(dir_action)

        mapping_action = QAction("列映射", self)
        mapping_action.triggered.connect(self._open_column_mapping)
        menu_bar.addAction(mapping_action)

        about_action = QAction("使用说明", self)
        about_action.triggered.connect(self._show_about)
        menu_bar.addAction(about_action)

        # ── 读取计时器 ──
        self._load_timer = QTimer(self)
        self._load_timer.setInterval(1000)
        self._load_timer.timeout.connect(self._update_load_timer_label)

        # ── 中央控件 ──
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # ── 文件选择区 ──
        file_layout = QHBoxLayout()
        self._file_label = QLabel("未选择文件")
        self._file_label.setWordWrap(True)
        self._file_label.setProperty("secondary", True)
        file_layout.addWidget(self._file_label, 1)

        self._select_btn = QPushButton("选择文件")
        self._select_btn.clicked.connect(self._select_file)
        file_layout.addWidget(self._select_btn)

        self._clear_btn = QPushButton("清除文件")
        self._clear_btn.setVisible(False)
        self._clear_btn.clicked.connect(self._clear_file)
        file_layout.addWidget(self._clear_btn)
        layout.addLayout(file_layout)

        # ── Sheet 概览（白色卡片：表格 + 全选行） ──
        card = QFrame()
        card.setObjectName("card")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(12, 8, 12, 8)
        card_layout.setSpacing(6)

        self._sheet_table = QTableWidget()
        self._sheet_table.setObjectName("innerTable")
        self._sheet_table.setColumnCount(4)
        self._sheet_table.setHorizontalHeaderLabels([
            "", "序号", "Sheet名称", "最后导入时间",
        ])
        self._sheet_table.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self._sheet_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._sheet_table.setAlternatingRowColors(True)
        self._sheet_table.setShowGrid(False)
        self._sheet_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self._sheet_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self._sheet_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self._sheet_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self._sheet_table.verticalHeader().setVisible(False)
        self._sheet_table.verticalHeader().setDefaultSectionSize(38)

        # 列0固定宽度（给 checkbox 留足够空间）
        self._sheet_table.setColumnWidth(0, 50)

        card_layout.addWidget(self._sheet_table, 1)

        # 全选行（卡片底部：全选 checkbox + 已选计数）
        header_cb_layout = QHBoxLayout()
        self._header_cb = QCheckBox("全选")
        self._header_cb.setChecked(True)
        self._header_cb.stateChanged.connect(self._on_header_checkbox_clicked)
        header_cb_layout.addWidget(self._header_cb)

        self._count_label = QLabel("")
        self._count_label.setProperty("secondary", True)
        header_cb_layout.addWidget(self._count_label)
        header_cb_layout.addStretch()
        card_layout.addLayout(header_cb_layout)

        layout.addWidget(card, 1)

        # ── 按钮区 ──
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self._dedup_btn = QPushButton("开始去重")
        self._dedup_btn.setEnabled(False)
        self._dedup_btn.setMinimumWidth(120)
        self._dedup_btn.setMinimumHeight(36)
        self._dedup_btn.clicked.connect(self._start_dedup)
        btn_layout.addWidget(self._dedup_btn)

        btn_layout.addSpacing(16)

        self._validate_btn = QPushButton("验证数据")
        self._validate_btn.setEnabled(False)
        self._validate_btn.setMinimumWidth(120)
        self._validate_btn.setMinimumHeight(36)
        self._validate_btn.clicked.connect(self._start_validate)
        btn_layout.addWidget(self._validate_btn)

        btn_layout.addSpacing(16)

        self._import_btn = QPushButton("开始导入")
        self._import_btn.setProperty("class", "primary")
        self._import_btn.setEnabled(False)
        self._import_btn.setMinimumWidth(120)
        self._import_btn.setMinimumHeight(36)
        self._import_btn.clicked.connect(self._start_import)
        btn_layout.addWidget(self._import_btn)

        btn_layout.addStretch()
        layout.addLayout(btn_layout)

    def _setup_status_bar(self):
        if self._connection_name:
            self.statusBar().showMessage(f"当前连接: {self._connection_name}  |  {self._db_info}")
        else:
            self.statusBar().showMessage(f"已连接: {self._db_info}")

    def _switch_connection(self):
        """请求切换连接：关闭当前窗口，通知main.py重新走连接流程。"""
        try:
            if self._conn:
                self._conn.close()
        except Exception:
            pass
        self.connection_switch_requested.emit()
        self.close()

    def _select_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "选择数据文件",
            "",
            "Excel 文件 (*.xlsx)",
        )
        if not path:
            return

        self._load_file(path)

    def _load_file(self, path: str):
        """载入指定 Excel：设路径并后台读取 Sheet（选择文件与去重完成后自动切换共用）。"""
        self._excel_path = path
        file_name = path.rsplit("\\", 1)[-1].rsplit("/", 1)[-1]
        self._set_loading_state(file_name)

        # 后台线程读取 Excel，避免 UI 冻结
        self._reader_worker = SheetReaderWorker(path, self)
        self._reader_worker.finished.connect(self._on_sheets_loaded)
        self._reader_worker.error.connect(self._on_sheets_error)
        self._reader_worker.start()

    def _set_loading_state(self, file_name: str):
        """进入加载状态：禁用选择按钮、显示进度提示。"""
        self._select_btn.setEnabled(False)
        self._clear_btn.setVisible(False)
        self._import_btn.setEnabled(False)
        self._validate_btn.setEnabled(False)
        self._dedup_btn.setEnabled(False)
        self._file_label.setText(f"正在读取: {file_name} ...")
        self._sheet_table.setRowCount(0)

        self._loading_file_name = file_name
        self._load_start_time = time.time()
        self._load_timer.start()

    def _on_sheets_loaded(self, sheets: list):
        """后台读取完成，更新界面。"""
        elapsed = int(time.time() - self._load_start_time)
        self._load_timer.stop()
        self._sheets = sheets
        self._update_sheet_info()
        self._import_btn.setEnabled(True)
        self._validate_btn.setEnabled(True)
        self._dedup_btn.setEnabled(True)
        self._select_btn.setEnabled(True)
        self._clear_btn.setVisible(True)

        file_name = self._excel_path.rsplit("\\", 1)[-1].rsplit("/", 1)[-1]
        self._file_label.setText(f"已选择: {file_name}（读取用时 {elapsed}s）")
        toast.success(self, f"读取完成：共 {len(sheets)} 个 Sheet")

        # 检测上次导入失败的 Sheet，提示一键只勾选它们补录
        self._offer_failed_reimport()

    def _on_sheets_error(self, error_msg: str):
        """后台读取失败，恢复界面。"""
        self._load_timer.stop()
        QMessageBox.critical(self, "读取失败", f"无法读取文件：{error_msg}")
        self._sheets = []
        self._excel_path = ""
        self._import_btn.setEnabled(False)
        self._validate_btn.setEnabled(False)
        self._dedup_btn.setEnabled(False)
        self._select_btn.setEnabled(True)
        self._clear_btn.setVisible(False)
        self._file_label.setText("未选择文件")
        self._sheet_table.setRowCount(0)

    def _clear_file(self):
        """清除当前选择的 Excel 文件，恢复初始状态。"""
        if self._load_timer is not None:
            self._load_timer.stop()
        self._excel_path = ""
        self._sheets = []
        self._sheet_table.setRowCount(0)
        self._import_btn.setEnabled(False)
        self._validate_btn.setEnabled(False)
        self._dedup_btn.setEnabled(False)
        self._clear_btn.setVisible(False)
        self._file_label.setText("未选择文件")

    def _update_load_timer_label(self):
        """每秒更新加载中的已用时间。"""
        elapsed = int(time.time() - self._load_start_time)
        self._file_label.setText(f"正在读取: {self._loading_file_name} ... (已用时 {elapsed}s)")

    def _update_sheet_info(self):
        # 从 SQLite 获取 sheet→最后导入时间/导入状态 的映射
        mappings = local_db.get_sheet_names()
        time_map = {m["sheet_name"]: m["last_import_time"] for m in mappings}
        failed_set = {
            m["sheet_name"] for m in mappings if m.get("last_import_status") == "failed"
        }

        self._anchor_row = -1  # 表格重建后重置 Shift 锚点
        self._sheet_table.setRowCount(len(self._sheets))
        for i, sheet in enumerate(self._sheets):
            name = sheet["sheet_name"]

            # 勾选框（列0）— QCheckBox 包裹在居中容器中
            cb = QCheckBox()
            cb.setChecked(True)
            cb.setProperty("row", i)
            cb.stateChanged.connect(self._on_row_check_changed)
            cb.clicked.connect(self._on_row_check_clicked)
            wrapper = QWidget()
            wrapper_layout = QHBoxLayout(wrapper)
            wrapper_layout.setContentsMargins(0, 0, 0, 0)
            wrapper_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            wrapper_layout.addWidget(cb)
            self._sheet_table.setCellWidget(i, 0, wrapper)

            # 序号（列1）
            idx_item = QTableWidgetItem(str(i + 1))
            idx_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self._sheet_table.setItem(i, 1, idx_item)

            # Sheet名称（列2）— 上次导入失败的 Sheet 标红提示待补录
            name_item = QTableWidgetItem(name)
            if name in failed_set:
                name_item.setForeground(QBrush(QColor(DANGER)))
                name_item.setToolTip("上次导入失败：待业务修正后补录")
            self._sheet_table.setItem(i, 2, name_item)

            # 最后导入时间（列3）
            last_time = time_map.get(name, "")
            time_item = QTableWidgetItem(last_time if last_time else "—")
            time_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self._sheet_table.setItem(i, 3, time_item)

        # 初始化表头 checkbox 为全选状态
        self._update_header_check_state()

    def _get_checkbox(self, row: int) -> QCheckBox | None:
        """从指定行的列0 cellWidget 中提取 QCheckBox。"""
        w = self._sheet_table.cellWidget(row, 0)
        if isinstance(w, QCheckBox):
            return w
        # 包裹在居中容器中时，从 layout 中取第一个子 widget
        if isinstance(w, QWidget):
            layout = w.layout()
            if layout and layout.count() > 0:
                item = layout.itemAt(0)
                if item and isinstance(item.widget(), QCheckBox):
                    return item.widget()
        return None

    def _update_header_check_state(self):
        """根据所有行 checkbox 的状态更新表头 checkbox。"""
        if self._updating_header:
            return
        self._updating_header = True

        checked_count = 0
        total = self._sheet_table.rowCount()
        for row in range(total):
            cb = self._get_checkbox(row)
            if cb and cb.isChecked():
                checked_count += 1

        if total > 0 and checked_count == total:
            self._header_cb.setChecked(True)
        else:
            self._header_cb.setChecked(False)

        self._count_label.setText(f"已选 {checked_count}/{total}")

        self._updating_header = False

    def _on_row_check_changed(self):
        """任一行 checkbox 状态变化时，刷新表头 checkbox。"""
        self._update_header_check_state()

    def _on_row_check_clicked(self, checked: bool):
        """用户点击行首勾选框时触发。

        按住 Shift 点击时，将「上次点击的锚点行 → 当前行」整段设为同一勾选状态。
        """
        cb = self.sender()
        if cb is None:
            return
        row_prop = cb.property("row")
        if row_prop is None:
            return
        row = int(row_prop)
        if row < 0:
            return

        shift_held = QApplication.keyboardModifiers() & Qt.KeyboardModifier.ShiftModifier
        if shift_held and self._anchor_row != -1 and row != self._anchor_row:
            self._set_range_checked(self._anchor_row, row, checked)

        self._anchor_row = row

    def _set_range_checked(self, start: int, end: int, checked: bool):
        """将 start..end 行的勾选状态统一设为 checked（Shift 范围勾选）。"""
        lo, hi = min(start, end), max(start, end)
        self._updating_header = True
        for row in range(lo, hi + 1):
            cb = self._get_checkbox(row)
            if cb and cb.isChecked() != checked:
                cb.setChecked(checked)
        self._updating_header = False
        self._update_header_check_state()

    def _on_header_checkbox_clicked(self):
        """全选 checkbox 被点击时，同步所有行 checkbox。"""
        if self._updating_header:
            return

        self._anchor_row = -1  # 全选操作后重置 Shift 锚点
        all_checked = self._header_cb.isChecked()
        self._updating_header = True
        for row in range(self._sheet_table.rowCount()):
            cb = self._get_checkbox(row)
            if cb:
                cb.setChecked(all_checked)
        self._updating_header = False

    def _refresh_import_states(self):
        """导入完成后刷新最后导入时间列与失败红标。"""
        if not self._sheets:
            return
        mappings = local_db.get_sheet_names()
        time_map = {m["sheet_name"]: m["last_import_time"] for m in mappings}
        failed_set = {
            m["sheet_name"] for m in mappings if m.get("last_import_status") == "failed"
        }
        for i, sheet in enumerate(self._sheets):
            name = sheet["sheet_name"]
            last_time = time_map.get(name, "")
            time_item = QTableWidgetItem(last_time if last_time else "—")
            time_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self._sheet_table.setItem(i, 3, time_item)

            name_item = self._sheet_table.item(i, 2)
            if name_item:
                if name in failed_set:
                    name_item.setForeground(QBrush(QColor(DANGER)))
                    name_item.setToolTip("上次导入失败：待业务修正后补录")
                else:
                    name_item.setForeground(QBrush(QColor(TEXT)))
                    name_item.setToolTip("")

    def _open_sheet_directory(self):
        dialog = SheetDirectoryDialog(self)
        dialog.exec()

    def _open_column_mapping(self):
        dialog = ColumnMappingDialog(self)
        dialog.exec()

    def _show_about(self):
        """打开「使用说明」帮助窗口（非模态，可边看边操作）。"""
        if self._help_dlg is None:
            from ui.help_dialog import HelpDialog
            self._help_dlg = HelpDialog(self)
        self._help_dlg.show()
        self._help_dlg.raise_()
        self._help_dlg.activateWindow()

    def _get_selected_sheets(self) -> list[dict]:
        """收集勾选的 sheet，通过 SQLite 映射查找对应表名。

        返回:
            [{"sheet_name": str, "table_name": str}, ...]
        """
        # 获取 SQLite 映射
        mappings = local_db.get_sheet_names()
        sheet_to_table = {m["sheet_name"]: m["table_name"] for m in mappings}

        selected = []
        missing_mapping = []

        for row in range(self._sheet_table.rowCount()):
            cb = self._get_checkbox(row)
            if cb and cb.isChecked():
                name_item = self._sheet_table.item(row, 2)
                sheet_name = name_item.text() if name_item else ""

                table_name = sheet_to_table.get(sheet_name)
                if table_name:
                    selected.append({
                        "sheet_name": sheet_name,
                        "table_name": table_name,
                    })
                else:
                    missing_mapping.append(sheet_name)

        if missing_mapping:
            names = "、".join(missing_mapping)
            QMessageBox.warning(
                self, "映射缺失",
                f"以下 Sheet 在本地数据库中找不到对应的表映射，请检查：\n{names}\n\n{ERROR_CONTACT}"
            )
            return []

        return selected

    def _start_import(self):
        if not self._conn or not self._excel_path:
            return

        if not self._any_sheet_checked():
            toast.warning(self, "请先勾选至少一个 Sheet 后再导入")
            return

        selected = self._get_selected_sheets()
        if not selected:
            return

        # 确认对话框
        confirm = ConfirmDialog("导入", selected, self._excel_path, self)
        if confirm.exec() != ConfirmDialog.DialogCode.Accepted:
            return

        dialog = ImportDialog(self._excel_path, self._schema, selected, self)
        dialog.exec()
        self._refresh_import_states()

    def _start_validate(self):
        if not self._excel_path:
            return

        if not self._any_sheet_checked():
            toast.warning(self, "请先勾选至少一个 Sheet 后再验证")
            return

        selected = self._get_selected_sheets()
        if not selected:
            return

        # 确认对话框
        confirm = ConfirmDialog("验证", selected, self._excel_path, self)
        if confirm.exec() != ConfirmDialog.DialogCode.Accepted:
            return

        dialog = ValidateDialog(self._excel_path, selected, self)
        dialog.exec()

    def _get_selected_sheet_names(self) -> list[str]:
        """收集勾选的 sheet 名称（去重只按名称处理，不涉及表映射）。"""
        names = []
        for row in range(self._sheet_table.rowCount()):
            cb = self._get_checkbox(row)
            if cb and cb.isChecked():
                name_item = self._sheet_table.item(row, 2)
                if name_item:
                    names.append(name_item.text())
        return names

    def _start_dedup(self):
        if not self._excel_path:
            return

        if not self._any_sheet_checked():
            toast.warning(self, "请先勾选至少一个 Sheet 后再去重")
            return

        selected_names = self._get_selected_sheet_names()
        if not selected_names:
            return

        # 去重设置对话框（模式 + 判重列），摘要信息兼作去重前确认
        settings = DedupSettingsDialog(self._excel_path, len(selected_names), self)
        if settings.exec() != DedupSettingsDialog.DialogCode.Accepted:
            return
        options = settings.options() or {}

        dialog = DedupDialog(
            self._excel_path, selected_names,
            options.get("mode", "sheet"), options.get("audit_col_index", 4), self,
        )
        dialog.exec()

        # 去重成功且未取消：自动切换到去重后文件，可直接点「开始导入」
        result = dialog.dedup_result
        if (result and result.get("success") and not result.get("cancelled")
                and result.get("output_path")):
            toast.success(
                self, f"去重完成：删除 {result.get('total_deleted', 0)} 行，已切换到去重后文件"
            )
            self._load_file(result["output_path"])

    def _offer_failed_reimport(self):
        """文件加载后检测上次导入失败的 Sheet，提示一键只勾选它们补录。

        失败状态按表名持久化在本地 SQLite，跨文件有效：
        业务修正后的定稿文件（文件名每周变化）加载时同样能提示。
        """
        failed_names = set(local_db.get_failed_sheet_names())
        if not failed_names or self._sheet_table.rowCount() == 0:
            return

        hit_rows = []
        for row in range(self._sheet_table.rowCount()):
            name_item = self._sheet_table.item(row, 2)
            if name_item and name_item.text() in failed_names:
                hit_rows.append(row)
        if not hit_rows:
            return

        preview = "、".join(
            self._sheet_table.item(r, 2).text() for r in hit_rows[:8]
        )
        if len(hit_rows) > 8:
            preview += f" 等 {len(hit_rows)} 个"

        box = QMessageBox(self)
        box.setIcon(QMessageBox.Icon.Question)
        box.setWindowTitle("一键补录")
        box.setText(
            f"检测到 {len(hit_rows)} 个 Sheet 上次导入失败：\n{preview}\n\n"
            "是否只勾选这些 Sheet 进行补录？"
        )
        only_btn = box.addButton("只勾选失败 Sheet", QMessageBox.ButtonRole.YesRole)
        box.addButton("保持全选", QMessageBox.ButtonRole.NoRole)
        box.exec()
        if box.clickedButton() is not only_btn:
            return

        for row in range(self._sheet_table.rowCount()):
            cb = self._get_checkbox(row)
            if cb:
                cb.setChecked(row in hit_rows)
        toast.success(
            self, f"已只勾选 {len(hit_rows)} 个失败 Sheet，可直接「开始导入」补录"
        )

    def _any_sheet_checked(self) -> bool:
        """是否有任一 Sheet 被勾选。"""
        for row in range(self._sheet_table.rowCount()):
            cb = self._get_checkbox(row)
            if cb and cb.isChecked():
                return True
        return False
