"""Sheet名-表映射对话框 — 展示、新增、编辑、删除、筛选 local_db 中 sheet→表名映射"""

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QLineEdit,
    QTableWidget,
    QTableWidgetItem,
    QAbstractItemView,
    QMenu,
    QMessageBox,
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QAction

from app import local_db

ROLE_ID = Qt.ItemDataRole.UserRole
FILTER_DEBOUNCE_MS = 200


class SheetDirectoryDialog(QDialog):
    """展示全部 Sheet 名称、对应数据库表名的模态对话框。

    支持：
    - 搜索框实时筛选（按 Sheet 名称模糊匹配）
    - 双击单元格进入编辑（列 0~2），回车后弹窗确认保存
    - 右键行 → 删除，弹窗确认
    - 右上角「新增」按钮，新增空行
    - 「最后导入时间」列（列 3）不可编辑
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Sheet名-表映射")
        self.setMinimumSize(700, 500)
        self._editing_row = -1
        self._editing_col = -1
        self._old_text = ""
        self._all_records: list[dict] = []
        self._filter_keyword = ""
        self._pending_filter = ""

        self._setup_ui()
        self._load_all_data()

    # ── UI 搭建 ──

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # ── 顶部：计数 + 搜索框 + 新增按钮 ──
        top_layout = QHBoxLayout()
        self._count_label = QLabel()
        top_layout.addWidget(self._count_label)
        top_layout.addSpacing(12)

        self._filter_input = QLineEdit()
        self._filter_input.setPlaceholderText("筛选Sheet名称...")
        self._filter_input.setClearButtonEnabled(True)
        self._filter_input.setMinimumWidth(180)
        self._filter_input.setMaximumWidth(260)
        self._filter_input.textChanged.connect(self._on_filter_text_changed)
        self._filter_input.returnPressed.connect(self._apply_filter_immediately)
        top_layout.addWidget(self._filter_input)

        reset_btn = QPushButton("重置")
        reset_btn.setMinimumWidth(60)
        reset_btn.clicked.connect(self._reset_filter)
        top_layout.addWidget(reset_btn)

        top_layout.addStretch()

        add_btn = QPushButton("新增")
        add_btn.setMinimumWidth(80)
        add_btn.setAutoDefault(False)
        add_btn.clicked.connect(self._add_row)
        top_layout.addWidget(add_btn)
        layout.addLayout(top_layout)

        # ── 表格 ──
        self._table = QTableWidget()
        self._table.setColumnCount(4)
        self._table.setHorizontalHeaderLabels(["序号", "Sheet名称", "数据库表名", "最后导入时间"])
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._table.setAlternatingRowColors(True)
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.verticalHeader().setVisible(False)

        self._table.setColumnWidth(0, 60)
        self._table.setColumnWidth(1, 200)
        self._table.setColumnWidth(2, 200)

        self._table.cellDoubleClicked.connect(self._on_cell_double_clicked)
        self._table.cellChanged.connect(self._on_cell_changed)
        self._table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._table.customContextMenuRequested.connect(self._on_context_menu)

        layout.addWidget(self._table, 1)

        # ── 筛选 debounce 定时器 ──
        self._filter_timer = QTimer(self)
        self._filter_timer.setSingleShot(True)
        self._filter_timer.timeout.connect(self._apply_filter)

        # ── 关闭按钮 ──
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        close_btn = QPushButton("关闭")
        close_btn.setMinimumWidth(100)
        close_btn.clicked.connect(self.close)
        btn_layout.addWidget(close_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

    # ── 数据加载 ──

    def _load_all_data(self):
        """从数据库加载全部记录到 _all_records，然后刷新表格。"""
        self._all_records = local_db.get_sheet_names()
        self._reload_table()

    def _reload_table(self):
        """根据当前筛选关键词重建表格。"""
        keyword = self._filter_keyword.lower() if self._filter_keyword else ""

        # 筛选
        if keyword:
            filtered = [r for r in self._all_records if keyword in r.get("sheet_name", "").lower()]
        else:
            filtered = list(self._all_records)

        self._table.setRowCount(len(filtered))

        for row, r in enumerate(filtered):
            self._fill_row(row, r)

        # 计数标签
        total = len(self._all_records)
        shown = len(filtered)
        if keyword:
            self._count_label.setText(f"共 {total} 条（筛选 {shown} 条）")
        else:
            self._count_label.setText(f"共 {total} 条记录")

    def _fill_row(self, row: int, r: dict):
        """将一条记录填充到指定行。"""
        table = self._table

        def _make_item(text: str, align=Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter):
            item = QTableWidgetItem(text)
            item.setTextAlignment(align)
            return item

        order_item = _make_item(str(r.get("sheet_order", "")), Qt.AlignmentFlag.AlignCenter)
        order_item.setData(ROLE_ID, r.get("id"))
        table.setItem(row, 0, order_item)

        name_item = _make_item(r.get("sheet_name", ""))
        name_item.setData(ROLE_ID, r.get("id"))
        table.setItem(row, 1, name_item)

        tbl_item = _make_item(r.get("table_name", ""))
        tbl_item.setData(ROLE_ID, r.get("id"))
        table.setItem(row, 2, tbl_item)

        last_time = r.get("last_import_time", "") or "—"
        time_item = QTableWidgetItem(last_time)
        time_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        time_item.setFlags(time_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        time_item.setData(ROLE_ID, r.get("id"))
        table.setItem(row, 3, time_item)

    # ── 筛选 ──

    def _on_filter_text_changed(self, text: str):
        """输入框文本变化 → debounce 后执行筛选。"""
        self._pending_filter = text
        self._filter_timer.start(FILTER_DEBOUNCE_MS)

    def _apply_filter(self):
        """执行筛选（编辑进行中时延迟到编辑结束）。"""
        if self._editing_row != -1:
            # 正在编辑，等编辑结束后再筛
            return
        self._filter_keyword = self._pending_filter
        self._reload_table()

    def _apply_filter_immediately(self):
        """按回车立即筛选（跳过 debounce）。"""
        self._filter_timer.stop()
        self._filter_keyword = self._filter_input.text()
        self._pending_filter = self._filter_keyword
        if self._editing_row == -1:
            self._reload_table()

    def _reset_filter(self):
        """清空搜索框，重置筛选。"""
        self._filter_input.clear()
        self._filter_keyword = ""
        self._pending_filter = ""
        self._filter_timer.stop()
        self._reload_table()

    def _reapply_pending_filter(self):
        """编辑结束后重新应用待处理的筛选。"""
        if self._pending_filter != self._filter_keyword:
            self._filter_keyword = self._pending_filter
            self._reload_table()

    # ── 双击编辑 ──

    def _on_cell_double_clicked(self, row: int, col: int):
        """双击进入编辑模式（列 3 不可编辑）。"""
        if col == 3:
            return

        item = self._table.item(row, col)
        if item is None:
            return

        self._editing_row = row
        self._editing_col = col
        self._old_text = item.text()

        self._table.editItem(item)

    # ── 编辑完成（回车 / 失去焦点）──

    def _on_cell_changed(self, row: int, col: int):
        """单元格内容变更后触发：弹窗确认 → 保存或回退。"""
        if row != self._editing_row or col != self._editing_col:
            return

        item = self._table.item(row, col)
        if item is None:
            return

        new_text = item.text()

        if new_text == self._old_text:
            self._reset_edit_state()
            self._reapply_pending_filter()
            return

        if col == 0:
            try:
                int(new_text)
            except ValueError:
                QMessageBox.warning(self, "输入错误", "序号必须为整数。")
                self._revert_cell(row, col)
                self._reset_edit_state()
                self._reapply_pending_filter()
                return

        reply = QMessageBox.question(
            self, "确认修改",
            f"确定要将「{self._old_text}」修改为「{new_text}」吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            # 先结束编辑会话，防止 _save_current_row 重建表格触发 cellChanged 递归弹窗
            self._reset_edit_state()
            self._save_current_row(row)
        else:
            self._revert_cell(row, col)
            self._reset_edit_state()

        self._reapply_pending_filter()

    def _save_current_row(self, row: int):
        """收集当前行所有可编辑列的值，新增或更新 DB。"""
        order_text = self._table.item(row, 0).text() if self._table.item(row, 0) else ""
        name_text = self._table.item(row, 1).text() if self._table.item(row, 1) else ""
        tbl_text = self._table.item(row, 2).text() if self._table.item(row, 2) else ""

        record_id = self._get_row_id(row)

        if record_id is None:
            try:
                new_id = local_db.add_sheet_mapping(
                    int(order_text) if order_text else 0,
                    name_text,
                    tbl_text,
                )
                # 更新表格行 id
                for c in range(4):
                    it = self._table.item(row, c)
                    if it:
                        it.setData(ROLE_ID, new_id)
                time_item = self._table.item(row, 3)
                if time_item:
                    time_item.setFlags(time_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            except Exception as e:
                QMessageBox.critical(self, "保存失败", f"新增记录失败：{e}")
                return
        else:
            try:
                local_db.update_sheet_mapping(
                    record_id,
                    int(order_text) if order_text else 0,
                    name_text,
                    tbl_text,
                )
            except Exception as e:
                QMessageBox.critical(self, "保存失败", f"更新记录失败：{e}")
                return

        # 刷新 _all_records 并重建表格
        self._load_all_data()

    def _revert_cell(self, row: int, col: int):
        self._table.blockSignals(True)
        item = self._table.item(row, col)
        if item:
            item.setText(self._old_text)
        self._table.blockSignals(False)

    def _reset_edit_state(self):
        self._editing_row = -1
        self._editing_col = -1
        self._old_text = ""

    def _get_row_id(self, row: int):
        item = self._table.item(row, 0)
        if item is None:
            return None
        val = item.data(ROLE_ID)
        return val if val is not None else None

    # ── 新增行 ──

    def _add_row(self):
        """在表格末尾新增一个空行。"""
        row = self._table.rowCount()
        self._table.insertRow(row)

        r = {"id": None, "sheet_order": "", "sheet_name": "", "table_name": "", "last_import_time": ""}
        self._fill_row(row, r)

        total = len(self._all_records) + 1
        if self._filter_keyword:
            self._count_label.setText(f"共 {total} 条（筛选 {self._table.rowCount()} 条）")
        else:
            self._count_label.setText(f"共 {total} 条记录")

    # ── 右键菜单（删除）──

    def _on_context_menu(self, pos):
        row = self._table.rowAt(pos.y())
        if row < 0:
            return

        self._table.selectRow(row)

        menu = QMenu(self)
        delete_action = QAction("删除此行", self)
        delete_action.triggered.connect(lambda: self._delete_row(row))
        menu.addAction(delete_action)
        menu.exec(self._table.viewport().mapToGlobal(pos))

    def _delete_row(self, row: int):
        sheet_name = self._table.item(row, 1).text() if self._table.item(row, 1) else ""
        table_name = self._table.item(row, 2).text() if self._table.item(row, 2) else ""

        reply = QMessageBox.question(
            self, "确认删除",
            f"确定要删除以下映射吗？\n\nSheet: {sheet_name}\n表名: {table_name}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        record_id = self._get_row_id(row)
        if record_id is not None:
            try:
                local_db.delete_sheet_mapping(record_id)
            except Exception as e:
                QMessageBox.critical(self, "删除失败", f"删除记录失败：{e}")
                return

        # 从 _all_records 中移除，然后重建表格
        self._all_records = [r for r in self._all_records if r.get("id") != record_id]
        self._reload_table()
