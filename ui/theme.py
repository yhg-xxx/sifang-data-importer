"""全局主题 - 亮色现代扁平风 QSS（白底 + 蓝色主色 + 圆角卡片）

用法：main.py 中创建 QApplication 后调用 apply_theme(app)。
辅助约定：
- QPushButton 设置 setProperty("class", "primary") → 蓝色实心主按钮
- QLabel 设置 setProperty("secondary", True) → 灰色次要文字
- QFrame 设置 setObjectName("card") → 白色圆角卡片容器
- QTableWidget 设置 setObjectName("innerTable") → 卡片内无边框表格
"""

from PySide6.QtGui import QPalette, QColor, QFont

# ── 色板 ──
PRIMARY = "#2563EB"        # 主色（蓝）
PRIMARY_HOVER = "#1D4ED8"
PRIMARY_PRESSED = "#1E40AF"
PRIMARY_DISABLED = "#A8BEF5"

WINDOW_BG = "#F3F5F9"      # 窗口底色
CARD_BG = "#FFFFFF"        # 卡片底色
BORDER = "#E4E8EF"         # 常规边框
BORDER_INPUT = "#D4DAE3"   # 输入框边框
TEXT = "#1F2733"           # 主文字
TEXT_SECONDARY = "#6B7480" # 次要文字
SUCCESS = "#16A34A"        # 成功
WARNING = "#D97706"         # 警告
DANGER = "#DC2626"          # 失败

FONT_FAMILY = "Microsoft YaHei UI"
FONT_SIZE = 10  # pt

THEME_QSS = f"""
/* ── 基础 ── */
QWidget {{ color: {TEXT}; font-family: "{FONT_FAMILY}","Segoe UI",sans-serif; }}
QDialog, QMainWindow {{ background-color: {WINDOW_BG}; }}
QMessageBox {{ background-color: {CARD_BG}; }}
QLabel {{ background: transparent; }}
QLabel#dialogTitle {{ font-size: 15px; font-weight: 600; }}
QLabel[secondary="true"] {{ color: {TEXT_SECONDARY}; }}
QLabel#statusText {{ font-weight: 600; }}

/* ── 卡片容器 ── */
QFrame#card {{
    background-color: {CARD_BG};
    border: 1px solid {BORDER};
    border-radius: 10px;
}}

/* ── 按钮：默认（次要） ── */
QPushButton {{
    background-color: {CARD_BG};
    color: #374151;
    border: 1px solid {BORDER_INPUT};
    border-radius: 6px;
    padding: 6px 18px;
    min-height: 20px;
}}
QPushButton:hover {{ background-color: #F5F8FE; border-color: #A9BCF0; color: {PRIMARY_HOVER}; }}
QPushButton:pressed {{ background-color: #E8EEFB; }}
QPushButton:focus {{ border-color: {PRIMARY}; }}
QPushButton:disabled {{ background-color: #F3F4F6; border-color: #E5E7EB; color: #9CA3AF; }}

/* ── 按钮：主按钮（class=primary） ── */
QPushButton[class="primary"] {{
    background-color: {PRIMARY};
    border: 1px solid {PRIMARY};
    color: #FFFFFF;
    font-weight: 600;
}}
QPushButton[class="primary"]:hover {{ background-color: {PRIMARY_HOVER}; border-color: {PRIMARY_HOVER}; color: #FFFFFF; }}
QPushButton[class="primary"]:pressed {{ background-color: {PRIMARY_PRESSED}; border-color: {PRIMARY_PRESSED}; }}
QPushButton[class="primary"]:focus {{ border-color: {PRIMARY_PRESSED}; }}
QPushButton[class="primary"]:disabled {{ background-color: {PRIMARY_DISABLED}; border-color: {PRIMARY_DISABLED}; color: #EFF4FE; }}

/* ── 输入框 ── */
QLineEdit {{
    background-color: {CARD_BG};
    border: 1px solid {BORDER_INPUT};
    border-radius: 6px;
    padding: 6px 10px;
    selection-background-color: {PRIMARY};
    selection-color: #FFFFFF;
}}
QLineEdit:focus {{ border-color: {PRIMARY}; }}
QLineEdit:disabled {{ background-color: #F3F4F6; color: #9CA3AF; }}

/* ── 文本域（日志区） ── */
QTextEdit, QPlainTextEdit {{
    background-color: #FBFCFE;
    border: 1px solid {BORDER};
    border-radius: 8px;
    padding: 8px;
    selection-background-color: #C9D8FA;
    selection-color: {TEXT};
}}
QTextEdit#logArea {{ font-family: "Consolas","{FONT_FAMILY}",monospace; }}

/* ── 表格 ── */
QTableWidget, QTableView {{
    background-color: {CARD_BG};
    alternate-background-color: #F7F9FC;
    border: 1px solid {BORDER};
    border-radius: 8px;
    gridline-color: #EEF1F6;
    selection-background-color: #DCE7FC;
    selection-color: {TEXT};
}}
QTableWidget::item, QTableView::item {{ padding: 4px 8px; border: none; }}
QTableWidget::item:hover, QTableView::item:hover {{ background-color: #EEF3FE; }}
QTableWidget::item:selected, QTableView::item:selected {{ background-color: #DCE7FC; color: {TEXT}; }}

/* 卡片内表格（无外框，与卡片融为一体） */
QTableWidget#innerTable {{ border: none; background: transparent; alternate-background-color: #F7F9FC; }}

/* ── 表头 ── */
QHeaderView {{ background: #F2F5FA; border: none; }}
QHeaderView::section {{
    background: #F2F5FA;
    color: #5B6472;
    font-weight: 600;
    border: none;
    border-right: 1px solid #E9EDF3;
    border-bottom: 1px solid {BORDER};
    padding: 8px 10px;
}}
QTableCornerButton::section {{ background: #F2F5FA; border: none; border-bottom: 1px solid {BORDER}; }}

/* ── 进度条 ── */
QProgressBar {{
    background-color: #E9EDF4;
    border: none;
    border-radius: 5px;
    min-height: 14px;
    text-align: center;
    color: #374151;
    font-weight: 600;
}}
QProgressBar::chunk {{ background-color: {PRIMARY}; border-radius: 5px; }}

/* ── 滚动条（细长现代风） ── */
QScrollBar:vertical {{ background: transparent; width: 10px; margin: 2px; }}
QScrollBar::handle:vertical {{ background: #C9D2E0; border-radius: 4px; min-height: 30px; }}
QScrollBar::handle:vertical:hover {{ background: #AEBBCE; }}
QScrollBar:horizontal {{ background: transparent; height: 10px; margin: 2px; }}
QScrollBar::handle:horizontal {{ background: #C9D2E0; border-radius: 4px; min-width: 30px; }}
QScrollBar::handle:horizontal:hover {{ background: #AEBBCE; }}
QScrollBar::add-line, QScrollBar::sub-line {{ width: 0; height: 0; }}
QScrollBar::add-page, QScrollBar::sub-page {{ background: transparent; }}

/* ── 菜单栏 / 右键菜单 ── */
QMenuBar {{ background: transparent; border: none; }}
QMenuBar::item {{ background: transparent; padding: 6px 12px; border-radius: 6px; color: #374151; }}
QMenuBar::item:selected {{ background: #E9EEF9; color: {PRIMARY_HOVER}; }}
QMenu {{ background-color: {CARD_BG}; border: 1px solid {BORDER}; border-radius: 8px; padding: 6px; }}
QMenu::item {{ padding: 7px 26px 7px 14px; border-radius: 6px; color: #374151; }}
QMenu::item:selected {{ background: #EEF3FE; color: {PRIMARY_HOVER}; }}
QMenu::separator {{ height: 1px; background: #EEF1F6; margin: 4px 8px; }}

/* ── 状态栏 / 提示 ── */
QStatusBar {{ background: transparent; color: {TEXT_SECONDARY}; border-top: 1px solid {BORDER}; }}
QStatusBar::item {{ border: none; }}
QToolTip {{ background-color: {TEXT}; color: #FFFFFF; border: none; padding: 5px 8px; }}
"""


def apply_theme(app) -> None:
    """对 QApplication 应用全局主题：Fusion 风格 + 微软雅黑 + 蓝色高亮 + QSS。

    Fusion 风格对 QSS 支持最完整，且未在 QSS 中定义的部分（如复选框对勾）
    会用 Fusion + 高亮色板绘制，整体观感统一。
    """
    app.setStyle("Fusion")
    app.setFont(QFont(FONT_FAMILY, FONT_SIZE))

    palette = app.palette()
    palette.setColor(QPalette.ColorRole.Highlight, QColor(PRIMARY))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#FFFFFF"))
    app.setPalette(palette)

    app.setStyleSheet(THEME_QSS)
