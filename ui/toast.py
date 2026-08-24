"""Toast 消息提示 — 仿 Element Plus Message

非阻塞轻提示：在父窗口顶部居中弹出，自动淡出消失，支持多条向下堆叠。
仅在 GUI 线程调用；父窗口销毁时随窗口一起清理。

用法：
    from ui.toast import toast

    toast.success(self, "导入完成")
    toast.error(self, "连接失败")
    toast.warning(self, "部分表导入失败")
    toast.info(self, "正在读取 Sheet…")
"""

from PySide6.QtCore import QEasingCurve, QPoint, QPropertyAnimation, Qt, QTimer
from PySide6.QtWidgets import QFrame, QGraphicsOpacityEffect, QHBoxLayout, QLabel, QWidget

from ui.theme import BORDER, CARD_BG, DANGER, PRIMARY, SUCCESS, TEXT, WARNING

_TOP = 24    # 距父窗口顶部
_GAP = 12    # 多条消息间距

_KINDS = {
    "success": (SUCCESS, "✓"),
    "error": (DANGER, "×"),
    "warning": (WARNING, "!"),
    "info": (PRIMARY, "i"),
}


class Toast(QFrame):
    """单条消息（通过模块级 toast.* 快捷方法使用，不直接实例化）"""

    _active: list = []  # 当前所有活跃 Toast

    def __init__(self, parent: QWidget, text: str, kind: str = "info", duration_ms: int = 3000):
        super().__init__(parent)
        color, icon = _KINDS[kind]

        self._closing = False
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)  # 不拦截鼠标点击
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        self.setObjectName("toast")
        self.setStyleSheet(
            f"QFrame#toast {{ background-color: {CARD_BG};"
            f" border: 1px solid {BORDER}; border-radius: 8px; }}"
        )

        icon_label = QLabel(icon, self)
        icon_label.setFixedSize(18, 18)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_label.setStyleSheet(
            f"background-color: {color}; color: #FFFFFF;"
            f" border-radius: 9px; font-size: 11px; font-weight: 700;"
        )

        text_label = QLabel(text, self)
        text_label.setStyleSheet(f"color: {TEXT}; font-size: 13px;")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 10, 16, 10)
        layout.setSpacing(10)
        layout.addWidget(icon_label)
        layout.addWidget(text_label)

        # 单行完整显示：不换行、不限宽，尺寸自适应文本
        self.adjustSize()

        # 顶部居中、向下堆叠
        y = _TOP + sum(t.height() + _GAP for t in self._siblings(parent))
        x = (parent.width() - self.width()) // 2
        self.move(x, y)

        Toast._active.append(self)
        self.show()
        self.raise_()

        # 淡入 + 下滑入场
        self._opacity = QGraphicsOpacityEffect(self)
        self._opacity.setOpacity(0.0)
        self.setGraphicsEffect(self._opacity)

        fade_in = QPropertyAnimation(self._opacity, b"opacity", self)
        fade_in.setDuration(160)
        fade_in.setEndValue(1.0)
        fade_in.start(QPropertyAnimation.DeletionPolicy.DeleteWhenStopped)

        slide = QPropertyAnimation(self, b"pos", self)
        slide.setDuration(220)
        slide.setStartValue(QPoint(x, y - 14))
        slide.setEndValue(QPoint(x, y))
        slide.setEasingCurve(QEasingCurve.Type.OutCubic)
        slide.start(QPropertyAnimation.DeletionPolicy.DeleteWhenStopped)

        QTimer.singleShot(duration_ms, self._fade_out)

    def _fade_out(self):
        if self._closing:
            return
        self._closing = True
        fade_out = QPropertyAnimation(self._opacity, b"opacity", self)
        fade_out.setDuration(220)
        fade_out.setEndValue(0.0)
        fade_out.finished.connect(self.close)
        fade_out.start(QPropertyAnimation.DeletionPolicy.DeleteWhenStopped)

    def closeEvent(self, event):
        if self in Toast._active:
            Toast._active.remove(self)
        self._relayout(self.parentWidget())
        super().closeEvent(event)

    # ── 堆叠管理 ──

    @classmethod
    def _cleanup(cls):
        """移除父窗口已销毁的残留项（父窗口关闭时子控件不经过 closeEvent）"""
        for t in list(cls._active):
            try:
                t.isVisible()
            except RuntimeError:
                cls._active.remove(t)

    @classmethod
    def _siblings(cls, parent):
        cls._cleanup()
        return [
            t for t in cls._active
            if t.parentWidget() is parent and t.isVisible() and not t._closing
        ]

    @classmethod
    def _relayout(cls, parent):
        """某条消失后，其余消息上移补位"""
        if parent is None:
            return
        y = _TOP
        for t in cls._siblings(parent):
            anim = QPropertyAnimation(t, b"pos", t)
            anim.setDuration(160)
            anim.setEndValue(QPoint((parent.width() - t.width()) // 2, y))
            anim.start(QPropertyAnimation.DeletionPolicy.DeleteWhenStopped)
            y += t.height() + _GAP


class toast:
    """快捷入口：toast.success / toast.error / toast.warning / toast.info

    parent 通常传主窗口或对话框（self），Toast 显示在其内部顶部。
    """

    @staticmethod
    def success(parent: QWidget, text: str, duration_ms: int = 3000) -> None:
        Toast(parent, text, "success", duration_ms)

    @staticmethod
    def error(parent: QWidget, text: str, duration_ms: int = 3000) -> None:
        Toast(parent, text, "error", duration_ms)

    @staticmethod
    def warning(parent: QWidget, text: str, duration_ms: int = 3000) -> None:
        Toast(parent, text, "warning", duration_ms)

    @staticmethod
    def info(parent: QWidget, text: str, duration_ms: int = 3000) -> None:
        Toast(parent, text, "info", duration_ms)
