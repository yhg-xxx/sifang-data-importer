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

from ui.toast import toast


class BaseTaskDialog(QDialog):
    """展示后台任务过程与结果的模态对话框基类。

    子类需：
    - __init__ 中先调用 super().__init__(parent)，再设置窗口标题/尺寸，
      最后调用 self._start_task()
    - 实现 _run_worker()：构造 worker 后调用 self._launch_worker(worker)
    - 实现 _on_finished(result)：任务结果到达时更新界面
      （不需要调用 _finish，关闭按钮由基类在线程真正退出后统一启用）

    线程生命周期约定：
    - worker 的自定义结果信号必须命名为 result_ready（不能叫 finished，
      否则会遮蔽 QThread.finished，导致无法做线程退出收尾）
    - worker.run() 必须自带兜底 try/except，任何路径都发射 result_ready
    - 任务运行期间（线程未退出）reject/closeEvent 被拦截：运行中的 QThread
      被析构会直接 qFatal 崩溃，且导入线程会在后台继续写库
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setModal(True)
        self._worker = None
        self._indeterminate = False
        self._result_ok = True   # 结果是否「完成」（成功/部分成功）；失败/取消时不把进度条拉满
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
        self._add_extra_buttons(btn_layout)
        self._close_btn = QPushButton("关闭")
        self._close_btn.setEnabled(False)
        self._close_btn.clicked.connect(self.close)
        btn_layout.addWidget(self._close_btn)
        layout.addLayout(btn_layout)

    def _add_extra_buttons(self, btn_layout):
        """子类可覆写：在关闭按钮左侧追加自有按钮（如「取消」）。

        注意：本方法在基类构造时（子类 __init__ 体执行前）被调用，
        覆写实现不应依赖子类 __init__ 中才创建的属性。
        """
        pass

    def _start_task(self):
        """开始任务：启动计时并创建后台 worker。"""
        self._elapsed.start()
        self._tick_timer.start(1000)  # 每秒刷新
        self._run_worker()

    def _run_worker(self):
        """由子类实现：构造 worker 并调用 self._launch_worker(worker)。"""
        raise NotImplementedError

    def _launch_worker(self, worker):
        """统一启动 worker：连接进度/日志/结果信号，并在线程退出后收尾。

        关闭按钮在真正的 QThread.finished 到达时才启用——result_ready 发射时
        线程可能尚未退出 run()，立即放行关闭会进入析构竞态。
        """
        self._worker = worker
        worker.progress.connect(self._on_progress)
        worker.log.connect(self._on_log)
        worker.result_ready.connect(self._on_finished)
        worker.finished.connect(self._on_thread_finished)
        worker.start()

    def _on_thread_finished(self):
        """线程真正退出：清理引用并收尾（此时启用关闭按钮是安全的）。"""
        worker = self._worker
        self._worker = None
        if worker is not None:
            worker.deleteLater()
        self._finish()

    def reject(self):
        """任务运行中拦截 Esc/取消，避免运行中的线程被析构导致进程崩溃。"""
        if self._worker is not None:
            toast.warning(self, "任务正在进行中，请等待完成（去重可点「取消」）")
            return
        super().reject()

    def closeEvent(self, event):
        """任务运行中拦截标题栏 ✕ 关闭。"""
        if self._worker is not None:
            toast.warning(self, "任务正在进行中，请等待完成（去重可点「取消」）")
            event.ignore()
            return
        super().closeEvent(event)

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
        """任务结束收尾：停止计时、启用关闭按钮。

        成功时进度条拉满；失败/取消保持当前值，避免「100% 完成」误导
        （结果是否完成由子类在 _on_finished 中写入 self._result_ok）。
        """
        self._tick_timer.stop()
        self._update_elapsed()
        self._close_btn.setEnabled(True)
        if self._indeterminate:
            self._progress_bar.setRange(0, 100)
        if self._result_ok:
            self._progress_bar.setValue(100)
