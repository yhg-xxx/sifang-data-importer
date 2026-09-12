"""数据去重进度/结果对话框"""

from PySide6.QtCore import QThread, Signal, Qt
from PySide6.QtWidgets import (
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QAbstractItemView,
)

from app.dedup import run_dedup
from ui.base_task_dialog import BaseTaskDialog
from ui.theme import DANGER, SUCCESS, WARNING


class DedupWorker(QThread):
    """后台执行去重的工作线程（纯离线操作，无需数据库连接）。"""

    progress = Signal(int, int, str)   # current, total, message
    log = Signal(str)                   # 日志行
    result_ready = Signal(dict)         # 去重结果 dict（不遮蔽 QThread.finished）

    def __init__(self, excel_path, selected_sheet_names: list = None,
                 mode: str = "sheet", audit_col_index: int = 4, parent=None):
        super().__init__(parent)
        self._excel_path = excel_path
        self._selected_sheet_names = selected_sheet_names
        self._mode = mode
        self._audit_col_index = audit_col_index
        self._cancelled = False

    def cancel(self):
        """请求取消：工作线程在下一行检查点停止。"""
        self._cancelled = True

    def run(self):
        try:
            result = run_dedup(
                self._excel_path,
                self._selected_sheet_names,
                self._mode,
                self._audit_col_index,
                lambda current, total, message: self.progress.emit(current, total, message),
                cancel_check=lambda: self._cancelled,
            )
        except BaseException as e:
            # 兜底：任何意外异常（含 PanicException 等非 Exception 派生错误）也
            # 必须发结果信号，避免对话框永久卡在运行态
            result = {
                "success": False, "cancelled": False, "error": str(e),
                "sheets": [], "pending_sheets": [],
                "output_path": "", "duplicates_csv": "",
                "total_rows": 0, "total_deleted": 0,
            }
        self.result_ready.emit(result)


class DedupDialog(BaseTaskDialog):
    """展示去重过程与结果的模态对话框（支持取消）。"""

    def __init__(self, excel_path, selected_sheet_names: list = None,
                 mode: str = "sheet", audit_col_index: int = 4, parent=None):
        super().__init__(parent)
        self.setWindowTitle("数据去重")
        self.setMinimumSize(720, 520)

        self._excel_path = excel_path
        self._selected_sheet_names = selected_sheet_names
        self._mode = mode
        self._audit_col_index = audit_col_index
        self._result = None

        # 单 sheet 去重时改用不确定进度，避免进度条长期卡在 0%（沿用现有惯例）
        if selected_sheet_names and len(selected_sheet_names) == 1:
            self.set_indeterminate(True)

        self._build_result_view()
        self._start_task()

    def _add_extra_buttons(self, btn_layout):
        """基类构造时回调：在关闭按钮左侧注入「取消」按钮。"""
        self._cancel_btn = QPushButton("取消")
        self._cancel_btn.clicked.connect(self._on_cancel_clicked)
        btn_layout.addWidget(self._cancel_btn)

    def _on_cancel_clicked(self):
        if self._worker is not None:
            self._worker.cancel()
        self._cancel_btn.setEnabled(False)
        self._status_label.setText("正在取消...")

    def _build_result_view(self):
        """在基类布局中插入逐 Sheet 结果表（插入位置参照 ValidateDialog）。"""
        self._result_table = QTableWidget()
        self._result_table.setObjectName("innerTable")
        self._result_table.setColumnCount(6)
        self._result_table.setHorizontalHeaderLabels([
            "序号", "Sheet", "处理方式", "总行数", "删除", "保留",
        ])
        self._result_table.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self._result_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._result_table.setAlternatingRowColors(True)
        self._result_table.verticalHeader().setVisible(False)
        self._result_table.horizontalHeader().setStretchLastSection(True)
        self._result_table.verticalHeader().setDefaultSectionSize(34)
        self.layout().insertWidget(3, self._result_table, 2)

    def _run_worker(self):
        self._launch_worker(DedupWorker(
            self._excel_path,
            self._selected_sheet_names,
            self._mode,
            self._audit_col_index,
        ))

    def _on_progress(self, current: int, total: int, message: str):
        super()._on_progress(current, total, message)
        self._log_text.append(message)

    def _on_finished(self, result: dict):
        self._cancel_btn.setEnabled(False)
        self._result = result
        self._fill_result_table(result)

        if result.get("cancelled"):
            self._result_ok = False
            self._status_label.setText("已取消（未生成输出文件）")
            self._status_label.setStyleSheet(f"color: {WARNING}; font-weight: bold;")
            pending = result.get("pending_sheets") or []
            if pending:
                self._log_text.append("=" * 30)
                self._log_text.append("以下 Sheet 未处理: " + "、".join(pending))
        elif result.get("success"):
            self._result_ok = True
            deleted = result.get("total_deleted", 0)
            self._status_label.setText(f"去重完成！共删除 {deleted} 个重复行")
            self._status_label.setStyleSheet(f"color: {SUCCESS}; font-weight: bold;")
            self._log_text.append("=" * 30)
            self._log_text.append(f"输出文件: {result.get('output_path', '')}")
            if result.get("duplicates_csv"):
                self._log_text.append(f"重复清单: {result['duplicates_csv']}")
        else:
            self._result_ok = False
            self._status_label.setText("去重失败")
            self._status_label.setStyleSheet(f"color: {DANGER}; font-weight: bold;")
            self._log_text.append("=" * 30)
            self._log_text.append(f"错误: {result.get('error', '')}")

    def _fill_result_table(self, result: dict):
        sheets = result.get("sheets", [])
        self._result_table.setRowCount(len(sheets))
        for i, s in enumerate(sheets):
            if s.get("copied_only"):
                action = "原样复制" + ("（未完成）" if s.get("unfinished") else "")
            else:
                action = "去重" + ("（未完成）" if s.get("unfinished") else "")
            self._set_cell(i, 0, str(i + 1), Qt.AlignmentFlag.AlignCenter)
            self._set_cell(i, 1, s["sheet"])
            self._set_cell(i, 2, action, Qt.AlignmentFlag.AlignCenter)
            self._set_cell(i, 3, str(s["total"]), Qt.AlignmentFlag.AlignCenter)
            self._set_cell(i, 4, str(s["deleted"]), Qt.AlignmentFlag.AlignCenter)
            self._set_cell(i, 5, str(s["kept"]), Qt.AlignmentFlag.AlignCenter)
        self._result_table.resizeColumnsToContents()

    def _set_cell(self, row: int, col: int, text: str, align=None):
        item = QTableWidgetItem(text)
        if align is not None:
            item.setTextAlignment(align)
        self._result_table.setItem(row, col, item)

    @property
    def dedup_result(self) -> dict | None:
        """去重结果（任务结束后可读；主窗口据此判断是否自动切换文件）。"""
        return self._result
