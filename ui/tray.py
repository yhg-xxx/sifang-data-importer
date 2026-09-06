"""系统托盘图标：程序运行期间驻留右下角通知区域。

图标加载项目 assets/icon.png（用户的「四方」logo，运行时做圆角遮罩）。
托盘可用时，主窗口关闭不退出程序而是最小化到托盘；
双击图标恢复窗口，右键菜单可重新打开或彻底退出。
托盘不可用时由 main.py 退化为原有行为（关窗即退出）。
"""

import sys
from pathlib import Path

from PySide6.QtCore import QObject, QRectF, Qt, Signal
from PySide6.QtGui import QIcon, QPainter, QPainterPath, QPixmap
from PySide6.QtWidgets import QMenu, QSystemTrayIcon

_ICON_SIZES = (16, 24, 32, 48, 64, 128, 256)
_CORNER_RATIO = 0.22   # 圆角半径占比（现代应用图标观感）


def _icon_source_path() -> Path:
    """图标源文件路径：PyInstaller 打包后从解包目录读，开发态从项目根 assets/ 读。"""
    base = getattr(sys, "_MEIPASS", None)
    root = Path(base) if base else Path(__file__).resolve().parent.parent
    return root / "assets" / "icon.png"


def _rounded(pm: QPixmap) -> QPixmap:
    """给 pixmap 加圆角遮罩（四角透明），避免托盘里生硬的直角方块。"""
    out = QPixmap(pm.size())
    out.fill(Qt.GlobalColor.transparent)
    r = pm.width() * _CORNER_RATIO
    path = QPainterPath()
    path.addRoundedRect(QRectF(0, 0, pm.width(), pm.height()), r, r)
    p = QPainter(out)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setClipPath(path)
    p.drawPixmap(0, 0, pm)
    p.end()
    return out


def _icon_from_file(path: Path) -> QIcon:
    """从 logo 文件生成多尺寸图标；文件缺失/损坏时返回空 QIcon（Qt 默认图标）。"""
    src = QPixmap(str(path))
    if src.isNull():
        return QIcon()
    # 居中裁正方形（logo 略非正方形时避免比例失真）
    side = min(src.width(), src.height())
    src = src.copy((src.width() - side) // 2, (src.height() - side) // 2, side, side)
    icon = QIcon()
    for size in _ICON_SIZES:
        scaled = src.scaled(
            size, size,
            Qt.AspectRatioMode.IgnoreAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        icon.addPixmap(_rounded(scaled))
    return icon


def create_tray_icon() -> QIcon:
    """托盘/窗口图标：assets/icon.png（圆角遮罩，16~256 多尺寸）。"""
    return _icon_from_file(_icon_source_path())


class TrayController(QObject):
    """封装 QSystemTrayIcon：菜单项与气泡提示集中在此。"""

    show_requested = Signal()    # 用户想看到主窗口（菜单 / 单击 / 双击）
    quit_requested = Signal()    # 用户想彻底退出程序

    def __init__(self, parent=None):
        super().__init__(parent)
        self.icon = create_tray_icon()
        self._notified_hidden = False   # 「已最小化到托盘」气泡只提示一次

        self._tray = QSystemTrayIcon(self.icon, self)
        self._tray.setToolTip("四方信息源入库")

        self._menu = QMenu()   # setContextMenu 不接管所有权，需持有引用
        act_show = self._menu.addAction("显示主窗口")
        act_show.triggered.connect(self.show_requested.emit)
        self._menu.addSeparator()
        act_quit = self._menu.addAction("退出")
        act_quit.triggered.connect(self.quit_requested.emit)
        self._tray.setContextMenu(self._menu)

        self._tray.activated.connect(self._on_activated)

    @staticmethod
    def is_available() -> bool:
        return QSystemTrayIcon.isSystemTrayAvailable()

    def show(self):
        self._tray.show()

    def hide(self):
        self._tray.hide()

    def notify_hidden_to_tray(self):
        """窗口最小化到托盘时气泡告知去向（每次运行只提示一次）。"""
        if not self._notified_hidden and QSystemTrayIcon.supportsMessages():
            self._tray.showMessage(
                "四方信息源入库",
                "程序已最小化到系统托盘：双击图标可重新打开窗口，右键图标可选择退出。",
                QSystemTrayIcon.MessageIcon.Information,
            )
            self._notified_hidden = True

    def notify_busy(self):
        """有任务进行中、拒绝退出时气泡说明原因。"""
        if QSystemTrayIcon.supportsMessages():
            self._tray.showMessage(
                "四方信息源入库",
                "有任务正在进行，请等待完成后再退出。",
                QSystemTrayIcon.MessageIcon.Warning,
            )

    def _on_activated(self, reason):
        if reason in (
            QSystemTrayIcon.ActivationReason.Trigger,
            QSystemTrayIcon.ActivationReason.DoubleClick,
        ):
            self.show_requested.emit()
