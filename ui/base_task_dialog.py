"""任务进度对话框基类 - 导入/验证共用：进度条、状态文字、已用时、日志区、关闭按钮"""

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QProgressBar,
    QTextEdit,
    QPushButton,
    QLabel,
)
from PySide6.QtCore import QElapsedTimer, QTimer


class BaseTaskDialog(QDialog):
    """展示后台任务过程与结果的模态对话框基类。

    子类需：
    - __init__ 中先调用 super().__init__(parent)，再设置窗口标题/尺寸，
      最后调用 self._start_task()
    - 实现 _run_worker()：创建 worker、连接信号并 start
    - 实现 _on_finished(result)：任务结束后更新界面
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setModal(True)
        self._worker = None
        self._indeterminate = False
        self._elapsed = QElapsedTimer()
        self._tick_timer = QTimer(self)
        self._tick_timer.timeout.connect(self._update_elapsed)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # ── 进度条 ──
        self._progress_bar = QProgressBar()
        self._progress_bar.setRange(0, 100)
        self._progress_bar.setValue(0)
        layout.addWidget(self._progress_bar)

        # ── 状态文字 ──
        self._status_label = QLabel("准备中...")
        self._status_label.setObjectName("statusText")
        layout.addWidget(self._status_label)

        # ── 已用时间 ──
        self._elapsed_label = QLabel("已用时: 00:00")
        self._elapsed_label.setProperty("secondary", True)
        layout.addWidget(self._elapsed_label)

        # ── 日志区 ──
        self._log_text = QTextEdit()
        self._log_text.setObjectName("logArea")
        self._log_text.setReadOnly(True)
        layout.addWidget(self._log_text, 1)

        # ── 关闭按钮 ──
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        self._close_btn = QPushButton("关闭")
        self._close_btn.setEnabled(False)
        self._close_btn.clicked.connect(self.close)
        btn_layout.addWidget(self._close_btn)
        layout.addLayout(btn_layout)

    def _start_task(self):
        """开始任务：启动计时并创建后台 worker。"""
        self._elapsed.start()
        self._tick_timer.start(1000)  # 每秒刷新
        self._run_worker()

    def _run_worker(self):
        """由子类实现：创建 worker、连接信号并 start。"""
        raise NotImplementedError

    def _update_elapsed(self):
        secs = self._elapsed.elapsed() // 1000
        minutes, seconds = divmod(secs, 60)
        self._elapsed_label.setText(f"已用时: {minutes:02d}:{seconds:02d}")

    def _on_progress(self, current: int, total: int, message: str):
        """进度回调：更新进度条与状态文字。"""
        if not self._indeterminate and total > 0:
            self._progress_bar.setValue(int(current / total * 100))
        self._status_label.setText(message)

    def set_indeterminate(self, on: bool):
        """切换为「不确定（忙碌）」进度模式，适用于无法预估总量的长任务。"""
        self._indeterminate = on
        if on:
            self._progress_bar.setRange(0, 0)
        else:
            self._progress_bar.setRange(0, 100)
            self._progress_bar.setValue(0)

    def _on_log(self, line: str):
        self._log_text.append(line)

    def _finish(self):
        """任务结束收尾：停止计时、进度条拉满、启用关闭按钮。"""
        self._tick_timer.stop()
        self._update_elapsed()
        self._close_btn.setEnabled(True)
        if self._indeterminate:
            self._progress_bar.setRange(0, 100)
        self._progress_bar.setValue(100)
