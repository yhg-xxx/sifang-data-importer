"""验证数据对话框"""

from PySide6.QtCore import QThread, Signal

from app.validator import validate_excel
from app.constants import ERROR_CONTACT
from ui.base_task_dialog import BaseTaskDialog


class ValidateWorker(QThread):
    """后台执行验证的工作线程。"""
    progress = Signal(int, int, str)   # current, total, sheet_name
    log = Signal(str)                   # 日志行
    finished = Signal(dict)             # 验证结果 dict

    def __init__(self, excel_path, selected_sheets: list = None, parent=None):
        super().__init__(parent)
        self._excel_path = excel_path
        self._selected_sheets = selected_sheets

    def run(self):
        def _progress_callback(current, total, sheet_name):
            self.progress.emit(current, total, sheet_name)

        result = validate_excel(
            self._excel_path, self._selected_sheets,
            _progress_callback,
        )

        # 输出日志
        if result["valid"]:
            self.log.emit(
                f"验证通过！共 {result['total_sheets']} 个 Sheet，"
                f"{result['total_rows']} 行数据，未发现错误。"
            )
        else:
            self.log.emit(
                f"验证完成，发现 {result['total_errors']} 个错误"
                f"（分布在 {len(result['errors_by_sheet'])} 个 Sheet 中）:\n"
            )
            for sheet_name, errors in result["errors_by_sheet"].items():
                self.log.emit(f"\n{'='*50}")
                self.log.emit(f"Sheet: {sheet_name}（共 {len(errors)} 个错误）")
                self.log.emit(f"{'='*50}")
                for err in errors:
                    self.log.emit(err)

        if result.get("error"):
            self.log.emit(f"\n错误: {result['error']}")
            self.log.emit(ERROR_CONTACT)

        self.finished.emit(result)


class ValidateDialog(BaseTaskDialog):
    """展示验证过程与结果的模态对话框。"""

    def __init__(self, excel_path, selected_sheets: list = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("验证数据")
        self.setMinimumSize(600, 450)

        self._excel_path = excel_path
        self._selected_sheets = selected_sheets

        self._start_task()

    def _run_worker(self):
        self._worker = ValidateWorker(self._excel_path, self._selected_sheets)
        self._worker.progress.connect(self._on_progress)
        self._worker.log.connect(self._on_log)
        self._worker.finished.connect(self._on_finished)
        self._worker.start()

    def _on_progress(self, current: int, total: int, sheet_name: str):
        super()._on_progress(current, total, sheet_name)
        self._status_label.setText(
            f"正在验证 ({current + 1}/{total}): {sheet_name}"
        )

    def _on_finished(self, result: dict):
        self._finish()

        if result["valid"]:
            self._status_label.setText("验证通过！所有数据符合约束。")
            self._status_label.setStyleSheet("color: green; font-weight: bold;")
        else:
            self._status_label.setText(
                f"验证完成，发现 {result['total_errors']} 个错误"
            )
            self._status_label.setStyleSheet("color: red; font-weight: bold;")
