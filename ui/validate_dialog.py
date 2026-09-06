"""验证数据对话框"""

from PySide6.QtCore import QThread, Signal, Qt
from PySide6.QtWidgets import (
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QAbstractItemView,
)

from app.validator import validate_excel
from ui.base_task_dialog import BaseTaskDialog
from ui.theme import DANGER, SUCCESS


_REASON_LABELS = {
    "NOT NULL": "空值(必填)",
    "LENGTH": "超长",
    "DATE": "日期非法",
    "TYPE": "类型不符",
}


def _reason_label(reason: str) -> str:
    return _REASON_LABELS.get(reason, reason)


class ValidateWorker(QThread):
    """后台执行验证的工作线程。"""
    progress = Signal(int, int, str)   # current, total, sheet_name
    log = Signal(str)                   # 日志行
    result_ready = Signal(dict)         # 验证结果 dict（不遮蔽 QThread.finished）

    def __init__(self, excel_path, selected_sheets: list = None, parent=None):
        super().__init__(parent)
        self._excel_path = excel_path
        self._selected_sheets = selected_sheets

    def run(self):
        def _progress_callback(current, total, sheet_name):
            self.progress.emit(current, total, sheet_name)

        try:
            result = validate_excel(
                self._excel_path, self._selected_sheets,
                _progress_callback,
            )

            if result["valid"]:
                self.log.emit(
                    f"验证通过！共 {result['total_sheets']} 个 Sheet，"
                    f"{result['total_rows']} 行数据，未发现错误。"
                )
            elif result.get("error"):
                self.log.emit(f"\n错误: {result['error']}")
            else:
                self.log.emit(
                    f"验证完成，发现 {result['total_errors']} 个错误"
                    f"（分布在 {len(result['errors_by_sheet'])} 个 Sheet 中）:\n"
                )
                for sheet_name, sheet_data in result["errors_by_sheet"].items():
                    self.log.emit(sheet_data["formatted"])
                    self.log.emit("")
        except Exception as e:
            # 兜底：任何意外异常（文件被占用、损坏等）也必须发结果信号，
            # 避免对话框永久卡在运行态
            result = {
                "valid": False, "total_errors": 0, "total_rows": 0,
                "total_sheets": 0, "errors_by_sheet": {}, "error": str(e),
            }
            self.log.emit(f"验证失败: {e}")

        self.result_ready.emit(result)


class ValidateDialog(BaseTaskDialog):
    """展示验证过程与结果的模态对话框。"""

    def __init__(self, excel_path, selected_sheets: list = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("验证数据")
        self.setMinimumSize(720, 520)

        self._excel_path = excel_path
        self._selected_sheets = selected_sheets
        self._all_groups = []   # 按 (sheet, 行号) 合并后的错误组

        # 单 sheet 验证时改用不确定进度，避免进度条长时间卡在 0%
        if selected_sheets and len(selected_sheets) == 1:
            self.set_indeterminate(True)

        self._build_error_view()
        self._start_task()

    def _build_error_view(self):
        """在基类布局中插入「筛选栏 + 错误表」，替代纯文本墙。"""
        lay = self.layout()

        # ── 筛选栏 ──
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("错误类型:"))
        self._type_combo = QComboBox()
        self._type_combo.addItem("全部", "ALL")
        self._type_combo.addItem("空值(必填)", "NOT NULL")
        self._type_combo.addItem("超长", "LENGTH")
        self._type_combo.addItem("日期非法", "DATE")
        self._type_combo.currentIndexChanged.connect(self._apply_filter)
        filter_layout.addWidget(self._type_combo)

        self._count_label = QLabel("")
        self._count_label.setProperty("secondary", True)
        filter_layout.addStretch()
        filter_layout.addWidget(self._count_label)
        lay.insertLayout(3, filter_layout)

        # ── 错误表 ──
        self._error_table = QTableWidget()
        self._error_table.setObjectName("innerTable")
        self._error_table.setColumnCount(6)
        self._error_table.setHorizontalHeaderLabels([
            "序号", "Sheet", "行号", "字段", "当前值", "原因",
        ])
        self._error_table.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self._error_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._error_table.setAlternatingRowColors(True)
        self._error_table.verticalHeader().setVisible(False)
        self._error_table.horizontalHeader().setStretchLastSection(True)
        self._error_table.verticalHeader().setDefaultSectionSize(34)
        # 先插筛选栏（索引 3），再在其后插错误表（索引 4），
        # 保证「筛选栏在错误表上方」
        lay.insertWidget(4, self._error_table, 2)

    def _run_worker(self):
        self._launch_worker(ValidateWorker(self._excel_path, self._selected_sheets))

    def _on_progress(self, current: int, total: int, sheet_name: str):
        super()._on_progress(current, total, sheet_name)
        self._status_label.setText(
            f"正在验证 ({current + 1}/{total}): {sheet_name}"
        )

    def _on_finished(self, result: dict):
        if result["valid"]:
            self._result_ok = True
            self._status_label.setText("验证通过！所有数据符合约束。")
            self._status_label.setStyleSheet(f"color: {SUCCESS}; font-weight: bold;")
            self._count_label.setText("未发现错误")
            return

        if result.get("error"):
            # 整体失败（文件被占用/损坏等），不是数据错误
            self._result_ok = False
            self._status_label.setText("验证失败")
            self._status_label.setStyleSheet(f"color: {DANGER}; font-weight: bold;")
            self._count_label.setText(result["error"])
            return

        self._result_ok = True

        # 汇总所有 sheet 的结构化错误，按「连续行号区间」折叠成一行
        # （相邻出错的 Excel 行合并为一行，行号列显示如 90164-90166；单行长度为 1 的区间只显示单号）
        for sheet_name, data in result["errors_by_sheet"].items():
            pairs = sorted(
                ((e["row"], e) for e in data["errors"]),
                key=lambda p: p[0],
            )
            runs = []          # [{"sheet","row_start","row_end","errors":[]}, ...]
            cur = None
            for row, e in pairs:
                if cur is None or row > cur["row_end"] + 1:
                    cur = {
                        "sheet": sheet_name,
                        "row_start": row,
                        "row_end": row,
                        "errors": [],
                    }
                    runs.append(cur)
                # row == row_end（同行业多错）或 row == row_end+1（相邻行）都并入当前区间
                cur["errors"].append(e)
                if row > cur["row_end"]:
                    cur["row_end"] = row
            self._all_groups.extend(runs)

        self._apply_filter()
        self._status_label.setText(
            f"验证完成，发现 {result['total_errors']} 个错误"
        )
        self._status_label.setStyleSheet(f"color: {DANGER}; font-weight: bold;")

    def _apply_filter(self):
        reason = self._type_combo.currentData()
        groups = [
            g for g in self._all_groups
            if reason == "ALL"
            or any(e["reason"] == reason for e in g["errors"])
        ]

        self._error_table.setRowCount(len(groups))
        fm = self._error_table.fontMetrics()
        line_h = fm.lineSpacing()
        max_lines = 12   # 单个单元格最多显示行数，超出截断并提示

        for i, g in enumerate(groups):
            errors = g["errors"]
            self._set_cell(i, 0, str(i + 1), align=Qt.AlignmentFlag.AlignCenter)
            self._set_cell(i, 1, g["sheet"])
            # 行号区间：单行显示单号，连续行显示 "起始-结束"
            if g["row_start"] == g["row_end"]:
                row_text = str(g["row_start"])
            else:
                row_text = f"{g['row_start']}-{g['row_end']}"
            self._set_cell(i, 2, row_text, align=Qt.AlignmentFlag.AlignCenter)

            # 同一区间内多个错误：字段 / 值 / 原因 各列内用换行合并
            field_str = self._cap_lines(
                "\n".join(e["field"] for e in errors), max_lines)
            value_str = self._cap_lines(
                "\n".join(e["value"] for e in errors), max_lines)
            reason_str = self._cap_lines(
                "\n".join(_reason_label(e["reason"]) for e in errors), max_lines)
            self._set_cell(i, 3, field_str)
            self._set_cell(i, 4, value_str)
            self._set_cell(i, 5, reason_str)

            # 行高随内容行数自动撑开，避免换行文本被裁掉（不低于默认 34）
            lines = max(
                field_str.count("\n") + 1,
                value_str.count("\n") + 1,
                reason_str.count("\n") + 1,
            )
            self._error_table.setRowHeight(i, max(lines * line_h + 6, 34))

        self._error_table.resizeColumnsToContents()

        total = len(self._all_groups)
        self._count_label.setText(f"显示 {len(groups)} / {total} 行错误")

    @staticmethod
    def _cap_lines(text: str, max_lines: int) -> str:
        """超过 max_lines 行时截断并在末尾提示剩余条数，避免单行过高。"""
        parts = text.split("\n")
        if len(parts) <= max_lines:
            return text
        kept = "\n".join(parts[:max_lines])
        return f"{kept}\n…(还有 {len(parts) - max_lines} 条未显示)"

    def _set_cell(self, row: int, col: int, text: str, align=None):
        item = QTableWidgetItem(text)
        flags = Qt.AlignmentFlag.AlignTop
        if align is not None:
            flags |= align
        item.setTextAlignment(flags)
        self._error_table.setItem(row, col, item)
