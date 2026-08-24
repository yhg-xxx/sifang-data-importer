"""列映射对话框 — 展示 local_db 中 Excel 列 → 数据库字段的映射关系"""

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QAbstractItemView,
)
from PySide6.QtCore import Qt

from app import local_db


class ColumnMappingDialog(QDialog):
    """展示 Excel 列 → 数据库字段映射的模态对话框。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("列映射")
        self.setMinimumSize(660, 480)
        self.resize(720, 520)
        self._setup_ui()
        self._load_data()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # ── 标题 ──
        self._count_label = QLabel()
        self._count_label.setProperty("secondary", True)
        layout.addWidget(self._count_label)

        # ── 表格 ──
        self._table = QTableWidget()
        self._table.setColumnCount(6)
        self._table.setHorizontalHeaderLabels([
            "序号", "Excel列", "数据库字段", "Excel索引", "说明", "约束说明",
        ])
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._table.setAlternatingRowColors(True)
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.verticalHeader().setVisible(False)
        self._table.verticalHeader().setDefaultSectionSize(34)

        # 列宽
        self._table.setColumnWidth(0, 50)
        self._table.setColumnWidth(1, 70)
        self._table.setColumnWidth(2, 130)
        self._table.setColumnWidth(3, 70)
        self._table.setColumnWidth(4, 130)

        layout.addWidget(self._table, 1)

        # ── 关闭按钮 ──
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        close_btn = QPushButton("关闭")
        close_btn.setMinimumWidth(100)
        close_btn.clicked.connect(self.close)
        btn_layout.addWidget(close_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

    def _load_data(self):
        records = local_db.get_column_mapping_with_desc()
        self._count_label.setText(f"共 {len(records)} 条映射")
        self._table.setRowCount(len(records))

        for row, r in enumerate(records):
            items = [
                (str(r["col_order"]), Qt.AlignmentFlag.AlignCenter),
                (r["excel_col"], Qt.AlignmentFlag.AlignCenter),
                (r["db_column"], Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter),
                (str(r["excel_index"]), Qt.AlignmentFlag.AlignCenter),
                (r["description"], Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter),
                (r["constraint_desc"], Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter),
            ]
            for col, (text, alignment) in enumerate(items):
                item = QTableWidgetItem(text)
                item.setTextAlignment(alignment)
                self._table.setItem(row, col, item)
