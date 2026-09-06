"""使用说明窗口 - 非模态富文本帮助，顶部目录胶囊点击跳转各段。"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTextBrowser,
)

from ui.help_content import build_help_html

# (胶囊文字, 正文锚点)
NAV_SECTIONS = [
    ("使用流程", "usage"),
    ("菜单功能", "menus"),
    ("注意事项", "notes"),
    ("联系信息", "contact"),
]


class HelpDialog(QDialog):
    """展示工具使用说明。

    非模态（show 打开，不阻塞主窗口），内容按「流程/菜单/注意/联系」四段组织，
    顶部目录胶囊点击后滚动到对应段落；重复打开时复用同一实例。
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("使用说明 - 四方信息源入库")
        self.resize(880, 620)
        self.setMinimumSize(700, 460)

        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        # ── 顶栏：目录胶囊 + 关闭 ──
        nav_layout = QHBoxLayout()
        nav_layout.setSpacing(8)

        for text, anchor in NAV_SECTIONS:
            chip = QPushButton(text)
            chip.setObjectName("navChip")
            chip.setCursor(Qt.CursorShape.PointingHandCursor)
            chip.setAutoDefault(False)
            chip.clicked.connect(lambda _=False, a=anchor: self._jump_to(a))
            nav_layout.addWidget(chip)

        nav_layout.addStretch()

        close_btn = QPushButton("关闭")
        close_btn.setAutoDefault(False)
        close_btn.clicked.connect(self.close)
        nav_layout.addWidget(close_btn)

        layout.addLayout(nav_layout)

        # ── 正文 ──
        self._browser = QTextBrowser()
        self._browser.setOpenExternalLinks(False)
        # 必须在 setHtml 之前设置默认样式表才会生效
        self._browser.document().setDefaultStyleSheet(
            "h1{font-size:17pt;color:#1F2733;margin:0px 0px 4px 0px;}"
            "h2{color:#2563EB;font-size:13pt;margin-top:14px;}"
            "a{color:#2563EB;text-decoration:none;}"
            "p{margin-top:4px;margin-bottom:8px;}"
            "li{margin-bottom:4px;}"
        )
        self._browser.setHtml(build_help_html())
        layout.addWidget(self._browser, 1)

        # ── 底栏提示 ──
        hint = QLabel("本说明随功能更新，实际以界面为准")
        hint.setProperty("secondary", True)
        layout.addWidget(hint)

    def _jump_to(self, anchor: str):
        """滚动正文到指定锚点。"""
        self._browser.scrollToAnchor(anchor)
