"""去重设置对话框 - 模式与判重列配置（兼作去重前的确认）"""

import os

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QComboBox,
    QPushButton,
    QRadioButton,
)

from app import local_db
from app.dedup import (
    MODE_GLOBAL,
    MODE_SHEET,
    duplicates_csv_path_for,
    output_path_for,
)
from app.utils import col_letter

# column_mapping 之外的固定补充列（仅部分 Sheet 存在第 12 列）
_EXTRA_COLUMNS = [{"excel_index": 11, "description": "匹配类型"}]


class DedupSettingsDialog(QDialog):
    """配置去重模式与判重列；点击「开始去重」时保存设置并接受。

    对话框内的摘要信息兼作去重前确认（sheet→表映射与去重无关，
    故不走 ConfirmDialog）。
    """

    def __init__(self, excel_path: str, selected_count: int, parent=None):
        super().__init__(parent)
        self.setWindowTitle("去重设置")
        self.setMinimumWidth(480)

        self._excel_path = excel_path
        self._options = None
        settings = local_db.get_dedup_settings()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        # ── 去重模式 ──
        mode_label = QLabel("去重模式:")
        mode_label.setStyleSheet("font-weight: 600;")
        layout.addWidget(mode_label)

        self._sheet_radio = QRadioButton("按 Sheet 内去重（跨 Sheet 同名企业保留）")
        self._sheet_radio.setChecked(settings["mode"] != MODE_GLOBAL)
        layout.addWidget(self._sheet_radio)

        self._global_radio = QRadioButton("全局去重（选中 Sheet 共用判重，跨 Sheet 同名只保留首个，每周例行默认）")
        # 必须显式置位：QRadioButton 默认不选中，漏掉会导致已保存「全局」时两个都不选
        self._global_radio.setChecked(settings["mode"] == MODE_GLOBAL)
        layout.addWidget(self._global_radio)

        layout.addSpacing(6)

        # ── 判重列 ──
        col_label = QLabel("判重列:")
        col_label.setStyleSheet("font-weight: 600;")
        layout.addWidget(col_label)

        self._col_combo = QComboBox()
        for item in self._load_columns():
            self._col_combo.addItem(item["label"], item["index"])
        default_index = self._col_combo.findData(settings["audit_col_index"])
        if default_index >= 0:
            self._col_combo.setCurrentIndex(default_index)
        layout.addWidget(self._col_combo)

        layout.addSpacing(6)

        # ── 摘要（兼作确认信息） ──
        summary = QLabel(
            f"将对勾选的 {selected_count} 个 Sheet 去重（其余 Sheet 原样复制），"
            f"保留录入时间(第一列)最早的行，平手保留首次出现。\n"
            f"判重键 = 判重列值去首尾空白并全角转半角；判重列为空的行不参与判重、原样保留。"
            f"录入时间为空或无法解析的行同样不参与去重、原样保留；"
            f"仅当企业名称与录入时间均可解析时，按录入时间最早保留。\n"
            f"输出: 源文件同目录「{os.path.basename(output_path_for(excel_path))}」"
            f"（如已存在自动加时间戳，不覆盖任何已有文件）；\n"
            f"如有删除将同时生成「{os.path.basename(duplicates_csv_path_for(excel_path))}」"
            f"（保留/删除对照清单）。"
        )
        summary.setProperty("secondary", True)
        summary.setWordWrap(True)
        layout.addWidget(summary)

        layout.addStretch()

        # ── 按钮行 ──
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        start_btn = QPushButton("开始去重")
        start_btn.setProperty("class", "primary")
        start_btn.setMinimumWidth(120)
        start_btn.clicked.connect(self._on_accepted)
        btn_layout.addWidget(start_btn)

        layout.addLayout(btn_layout)

    @staticmethod
    def _load_columns() -> list[dict]:
        """下拉项 = 本地列映射（11 列）+ 固定补充列，index 为 1-based 列号。"""
        mappings = local_db.get_column_mapping_with_desc() + _EXTRA_COLUMNS
        return [
            {
                "label": f"{col_letter(m['excel_index'] + 1)} {m['description']}",
                "index": m["excel_index"] + 1,
            }
            for m in mappings
        ]

    def _on_accepted(self):
        mode = MODE_GLOBAL if self._global_radio.isChecked() else MODE_SHEET
        audit_col_index = self._col_combo.currentData()
        local_db.save_dedup_settings(mode, audit_col_index)
        self._options = {"mode": mode, "audit_col_index": audit_col_index}
        self.accept()

    def options(self) -> dict | None:
        """对话框接受后返回 {"mode": str, "audit_col_index": int}；取消返回 None。"""
        return self._options
