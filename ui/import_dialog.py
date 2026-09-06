"""导入进度/结果对话框"""

import os
from datetime import datetime

from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import QMessageBox, QPushButton

from app.importer import build_failure_result, run_import
from app import database, config as app_config
from app.error_msgs import humanize_db_error
from ui.base_task_dialog import BaseTaskDialog
from ui.theme import DANGER, SUCCESS, WARNING


class ImportWorker(QThread):
    """后台执行导入的工作线程。"""

    progress = Signal(int, int, str)   # current, total, message
    log = Signal(str)                   # 逐表日志行
    result_ready = Signal(dict)         # 导入结果 dict（不遮蔽 QThread.finished）

    def __init__(self, excel_path, schema: str = "dbo",
                 selected_sheets: list = None,
                 db_params: dict | None = None, parent=None):
        super().__init__(parent)
        self._excel_path = excel_path
        self._schema = schema
        self._selected_sheets = selected_sheets
        self._db_params = db_params or {}

    def run(self):
        def _progress_callback(current, total, message):
            self.progress.emit(current, total, message)

        start_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        file_name = os.path.basename(self._excel_path)
        conn = None
        try:
            # 连接参数优先用主窗口传入的本次会话连接快照，避免依赖
            # local.db 的 is_last_used 记录（双开实例时可能被另一实例改写）
            cfg = self._db_params or app_config.load_config()
            # pyodbc 连接不是线程安全的，必须在工作线程内创建独立连接，
            # 避免跨线程共享主线程的连接导致 HY010 "函数序列错误"
            conn = database.connect(
                cfg.get("server", ""),
                cfg.get("database", ""),
                cfg.get("username", ""),
                cfg.get("password", ""),
            )
            try:
                result = run_import(
                    conn, self._excel_path,
                    self._selected_sheets, self._schema,
                    _progress_callback,
                )
            except Exception as e:
                self.result_ready.emit(build_failure_result(
                    file_name=file_name, start_time=start_time, error=str(e),
                ))
                return

            # 填充逐表日志（成功或部分成功时，对成功的表查询数据库实际行数）
            if result.get("success") or result.get("partial"):
                ok_tables = list(result.get("tables", {}).keys())
                if ok_tables:
                    self.log.emit("正在统计导入行数...")
                    try:
                        db_table_counts = database.count_tables_rows_batch(
                            conn, ok_tables, self._schema,
                        )
                    except Exception as e:
                        # 行数统计失败不影响导入结果本身，只在日志中提示
                        self.log.emit(f"行数统计失败：{e}")
                    else:
                        for table_name, count in db_table_counts.items():
                            self.log.emit(f"{table_name}: {count} 行")
                        self.log.emit(
                            f"合计：{len(db_table_counts)} 张表，"
                            f"共 {sum(db_table_counts.values())} 行"
                        )
                        result["tables"] = db_table_counts

            self.result_ready.emit(result)
        except Exception as e:
            # 连接失败等任何异常都必须发射结果信号，避免对话框永久卡在运行态
            self.result_ready.emit(build_failure_result(
                file_name=file_name, start_time=start_time, error=str(e),
            ))
        finally:
            if conn is not None:
                try:
                    conn.close()
                except Exception:
                    pass


class ImportDialog(BaseTaskDialog):
    """展示导入过程与结果的模态对话框。"""

    def __init__(self, excel_path, schema: str = "dbo",
                 selected_sheets: list = None,
                 db_params: dict | None = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("导入数据")
        self.setMinimumSize(520, 380)

        self._excel_path = excel_path
        self._schema = schema
        self._selected_sheets = selected_sheets
        self._db_params = db_params
        self._result = None

        # 单 sheet 导入（可能十几~二十万行）改用不确定进度，避免进度条长期卡在 0%
        if selected_sheets and len(selected_sheets) == 1:
            self.set_indeterminate(True)

        self._start_task()

    def _run_worker(self):
        self._launch_worker(ImportWorker(
            self._excel_path, self._schema, self._selected_sheets,
            self._db_params,
        ))

    def _add_extra_buttons(self, btn_layout):
        """「打开错误名单」按钮：部分成功且有名单文件时显示。"""
        self._open_list_btn = QPushButton("打开错误名单")
        self._open_list_btn.setVisible(False)
        self._open_list_btn.clicked.connect(self._open_error_list)
        btn_layout.addWidget(self._open_list_btn)

    def _open_error_list(self):
        """用系统默认程序打开错误名单 xlsx。"""
        path = (self._result or {}).get("error_list_path", "")
        if not path:
            return
        try:
            os.startfile(path)  # Windows 下用默认关联程序打开
        except Exception as e:
            QMessageBox.warning(self, "打开失败", f"无法打开错误名单文件：{e}")

    def _on_progress(self, current: int, total: int, message: str):
        super()._on_progress(current, total, message)
        self._log_text.append(message)

    def _on_finished(self, result: dict):
        self._result = result
        failed = result.get("failed_tables") or {}

        if result["success"]:
            self._result_ok = True
            total_rows = sum(result["tables"].values())
            self._status_label.setText(
                f"导入完成！共 {len(result['tables'])} 张表，{total_rows} 行数据"
            )
            self._status_label.setStyleSheet(f"color: {SUCCESS}; font-weight: bold;")
            self._log_text.append("=" * 30)
            self._log_text.append(f"导入成功（数据库实际行数: {total_rows}）")
        elif result.get("partial"):
            self._result_ok = True
            ok_count = len(result.get("tables", {}))
            total_rows = sum(result.get("tables", {}).values())
            self._status_label.setText(
                f"导入完成：成功 {ok_count} 张（共 {total_rows} 行），失败 {len(failed)} 张"
            )
            self._status_label.setStyleSheet(f"color: {WARNING}; font-weight: bold;")
            self._log_text.append("=" * 30)
            for table_name, info in failed.items():
                sheet_name = info.get("sheet_name", "")
                self._log_text.append(f"■ {table_name} [{sheet_name}] 导入失败：")
                self._log_text.append(humanize_db_error(info.get("error", "")))
            error_rows = sum(len(info.get("errors") or []) for info in failed.values())
            self._log_text.append(
                f"汇总：成功 {ok_count} 张（共 {total_rows} 行）；"
                f"失败 {len(failed)} 张，错误行共 {error_rows} 行"
            )
            list_path = result.get("error_list_path", "")
            if list_path:
                self._log_text.append(f"错误名单已生成：{list_path}")
                self._open_list_btn.setVisible(True)
                self._open_list_btn.setEnabled(True)
            self._log_text.append(
                "请将错误名单发业务人员修正；修正完成后重新选择定稿文件，"
                "程序会自动提示只勾选失败的 Sheet 进行补录。"
            )
        else:
            self._result_ok = False
            self._status_label.setText("导入失败")
            self._status_label.setStyleSheet(f"color: {DANGER}; font-weight: bold;")
            self._log_text.append("=" * 30)
            self._log_text.append(f"错误: {humanize_db_error(result.get('error', ''))}")
            if result.get("tables"):
                self._log_text.append(
                    f"（中止前已成功导入 {len(result['tables'])} 张表，数据已保留）"
                )
