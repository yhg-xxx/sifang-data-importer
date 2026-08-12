"""导入进度/结果对话框"""

from PySide6.QtCore import QThread, Signal

from app.importer import build_failure_result, run_import
from app import database, config as app_config
from app.constants import ERROR_CONTACT
from ui.base_task_dialog import BaseTaskDialog


class ImportWorker(QThread):
    """后台执行导入的工作线程。"""

    progress = Signal(int, int, str)   # current, total, message
    log = Signal(str)                   # 逐表日志行
    finished = Signal(dict)             # 导入结果 dict

    def __init__(self, excel_path, schema: str = "dbo",
                 selected_sheets: list = None, parent=None):
        super().__init__(parent)
        self._excel_path = excel_path
        self._schema = schema
        self._selected_sheets = selected_sheets

    def run(self):
        def _progress_callback(current, total, message):
            self.progress.emit(current, total, message)

        # pyodbc 连接不是线程安全的，必须在工作线程内创建独立连接，
        # 避免跨线程共享主线程的连接导致 HY010 "函数序列错误"
        cfg = app_config.load_config()
        conn = database.connect(
            cfg.get("server", ""),
            cfg.get("database", ""),
            cfg.get("username", ""),
            cfg.get("password", ""),
        )
        try:
            try:
                result = run_import(
                    conn, self._excel_path,
                    self._selected_sheets, self._schema,
                    _progress_callback,
                )
            except Exception as e:
                self.finished.emit(build_failure_result(error=str(e)))
                return

            # 填充逐表日志
            if result["success"]:
                self.log.emit("正在统计导入行数...")
                table_names = [item["table_name"] for item in self._selected_sheets]
                db_table_counts = database.count_tables_rows_batch(
                    conn, table_names, self._schema,
                )
                for table_name, count in db_table_counts.items():
                    self.log.emit(f"{table_name}: {count} 行")
                result["tables"] = db_table_counts

            self.finished.emit(result)
        finally:
            try:
                conn.close()
            except Exception:
                pass


class ImportDialog(BaseTaskDialog):
    """展示导入过程与结果的模态对话框。"""

    def __init__(self, excel_path, schema: str = "dbo",
                 selected_sheets: list = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("导入数据")
        self.setMinimumSize(520, 380)

        self._excel_path = excel_path
        self._schema = schema
        self._selected_sheets = selected_sheets

        self._start_task()

    def _run_worker(self):
        self._worker = ImportWorker(self._excel_path,
                                     self._schema, self._selected_sheets)
        self._worker.progress.connect(self._on_progress)
        self._worker.log.connect(self._on_log)
        self._worker.finished.connect(self._on_finished)
        self._worker.start()

    def _on_progress(self, current: int, total: int, message: str):
        super()._on_progress(current, total, message)
        self._log_text.append(message)

    def _on_finished(self, result: dict):
        self._finish()

        if result["success"]:
            total_rows = sum(result["tables"].values())
            self._status_label.setText(
                f"导入完成！共 {len(result['tables'])} 张表，{total_rows} 行数据"
            )
            self._status_label.setStyleSheet("color: green; font-weight: bold;")
            self._log_text.append("=" * 30)
            self._log_text.append(f"导入成功（数据库实际行数: {total_rows}）")
        else:
            self._status_label.setText("导入失败")
            self._status_label.setStyleSheet("color: red; font-weight: bold;")
            self._log_text.append("=" * 30)
            self._log_text.append(f"错误: {result.get('error', '')}")
            self._log_text.append(ERROR_CONTACT)
