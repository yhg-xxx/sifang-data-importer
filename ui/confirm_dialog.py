"""确认对话框 - 显示选中的 sheet 映射"""

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QPushButton,
    QLabel,
    QAbstractItemView,
)
from PySide6.QtCore import Qt


class ConfirmDialog(QDialog):
    """确认导入/验证的模态对话框，展示 sheet→表名映射。"""

    def __init__(self, action_label: str, selected_sheets: list[dict],
                 filepath: str, parent=None):
        """
        参数:
            action_label: "导入" 或 "验证"（用于标题和文案）
            selected_sheets: [{"sheet_name": str, "table_name": str}, ...]
            filepath: Excel 文件路径
        """
        super().__init__(parent)
        self.setWindowTitle(f"确认{action_label}")
        self.setMinimumSize(480, 340)
        self.setModal(True)

        self._action_label = action_label
        self._selected_sheets = selected_sheets
        self._confirmed = False

        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # ── 顶部提示 ──
        self._header_label = QLabel(
            f"即将{self._action_label}以下 {len(self._selected_sheets)} 个 Sheet："
        )
        self._header_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        layout.addWidget(self._header_label)

        # ── 表格（3列） ──
        columns = ["序号", "Sheet名称", "数据库表名"]

        self._table = QTableWidget()
        self._table.setColumnCount(len(columns))
        self._table.setHorizontalHeaderLabels(columns)
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._table.setAlternatingRowColors(True)
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.verticalHeader().setVisible(False)

        self._table.setColumnWidth(0, 60)
        self._table.setColumnWidth(1, 160)
        self._table.setColumnWidth(2, 180)

        self._table.setRowCount(len(self._selected_sheets))
        for i, item in enumerate(self._selected_sheets):
            idx_item = QTableWidgetItem(str(i + 1))
            idx_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self._table.setItem(i, 0, idx_item)

            self._table.setItem(i, 1, QTableWidgetItem(item["sheet_name"]))
            self._table.setItem(i, 2, QTableWidgetItem(item["table_name"]))

        layout.addWidget(self._table, 1)

        # ── 按钮 ──
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self._cancel_btn = QPushButton("取消")
        self._cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self._cancel_btn)

        self._confirm_btn = QPushButton("确认")
        self._confirm_btn.setMinimumWidth(80)
        self._confirm_btn.clicked.connect(self._on_confirm)
        btn_layout.addWidget(self._confirm_btn)
        layout.addLayout(btn_layout)

    def _on_confirm(self):
        self._confirmed = True
        self.accept()

    def is_confirmed(self) -> bool:
        return self._confirmed
