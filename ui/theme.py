"""主题管理：加载、切换、高 DPI 支持。"""
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication

# ── 颜色令牌（便于后续动态调整或 V2 自定义主题）─────────────────
DARK = {
    "bg": "#1A1A1E",
    "card": "#252529",
    "card_hover": "#2C2C30",
    "toolbar": "#252529",
    "text": "#F0F0F5",
    "text_secondary": "#8E8E93",
    "accent": "#0A84FF",
    "accent_hover": "#409CFF",
    "accent_pressed": "#0060DF",
    "danger": "#FF453A",
    "border": "#3A3A3E",
    "input_bg": "#252529",
    "scrollbar": "#5A5A5E",
    "scrollbar_hover": "#7A7A7E",
    "success": "#30D158",
    "tab_inactive": "#2C2C30",
    "tab_active": "#3A3A3E",
}

LIGHT = {
    "bg": "#F5F5F7",
    "card": "#FFFFFF",
    "card_hover": "#F0F0F5",
    "toolbar": "#FFFFFF",
    "text": "#1D1D1F",
    "text_secondary": "#6E6E73",
    "accent": "#0071E3",
    "accent_hover": "#0077ED",
    "accent_pressed": "#005BB5",
    "danger": "#FF3B30",
    "border": "#D2D2D7",
    "input_bg": "#FFFFFF",
    "scrollbar": "#C2C2C7",
    "scrollbar_hover": "#A2A2A7",
    "success": "#34C759",
    "tab_inactive": "#E5E5EA",
    "tab_active": "#FFFFFF",
}


def _qss(t: dict) -> str:
    """根据颜色令牌生成完整 QSS。"""
    return f"""
/* ===== 基础 ===== */
QMainWindow, QDialog {{
    background-color: {t["bg"]};
    color: {t["text"]};
}}
QWidget {{
    color: {t["text"]};
}}
QLabel {{
    color: {t["text"]};
    background-color: transparent;
}}
QLabel#secondary {{
    color: {t["text_secondary"]};
}}
QLabel#danger {{
    color: {t["danger"]};
}}

/* ===== 事件卡片 ===== */
QFrame#EventCard {{
    background-color: {t["card"]};
    border-radius: 10px;
    border: 1px solid transparent;
}}
QFrame#EventCard[overdue="true"] {{
    border: 1px solid {t["danger"]};
}}

/* ===== 按钮 ===== */
QPushButton {{
    background-color: {t["accent"]};
    color: white;
    border: none;
    border-radius: 6px;
    padding: 6px 14px;
    font-weight: 500;
}}
QPushButton:hover {{
    background-color: {t["accent_hover"]};
}}
QPushButton:pressed {{
    background-color: {t["accent_pressed"]};
}}
QPushButton:disabled {{
    background-color: {t["border"]};
    color: {t["text_secondary"]};
}}
QPushButton#tool {{
    background-color: transparent;
    color: {t["text_secondary"]};
    border-radius: 4px;
    padding: 4px 8px;
}}
QPushButton#tool:hover {{
    background-color: {t["border"]};
    color: {t["text"]};
}}
QPushButton#tool:checked {{
    background-color: {t["accent"]};
    color: white;
}}
QPushButton#danger {{
    background-color: {t["danger"]};
}}
QPushButton#danger:hover {{
    background-color: #E03A30;
}}
QPushButton#flat {{
    background-color: transparent;
    color: {t["accent"]};
}}
QPushButton#flat:hover {{
    background-color: {t["card_hover"]};
}}

/* ===== 输入框 ===== */
QLineEdit, QTextEdit, QSpinBox, QComboBox, QDateTimeEdit, QTimeEdit {{
    background-color: {t["input_bg"]};
    border: 1px solid {t["border"]};
    border-radius: 6px;
    padding: 5px 8px;
    color: {t["text"]};
}}
QLineEdit:focus, QTextEdit:focus, QSpinBox:focus, QComboBox:focus, QDateTimeEdit:focus {{
    border: 1px solid {t["accent"]};
}}
QComboBox::drop-down {{
    border: none;
    width: 24px;
}}
QComboBox QAbstractItemView {{
    background-color: {t["card"]};
    color: {t["text"]};
    border: 1px solid {t["border"]};
    selection-background-color: {t["accent"]};
}}
QSpinBox::up-button, QSpinBox::down-button {{
    width: 18px;
    background: {t["border"]};
    border-radius: 2px;
}}

/* ===== 滚动条 ===== */
QScrollArea {{
    border: none;
    background-color: transparent;
}}
QScrollBar:vertical {{
    background-color: transparent;
    width: 8px;
    border-radius: 4px;
    margin: 0px;
}}
QScrollBar::handle:vertical {{
    background-color: {t["scrollbar"]};
    border-radius: 4px;
    min-height: 30px;
}}
QScrollBar::handle:vertical:hover {{
    background-color: {t["scrollbar_hover"]};
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}
QScrollBar:horizontal {{
    background-color: transparent;
    height: 8px;
    border-radius: 4px;
    margin: 0px;
}}
QScrollBar::handle:horizontal {{
    background-color: {t["scrollbar"]};
    border-radius: 4px;
    min-width: 30px;
}}
QScrollBar::handle:horizontal:hover {{
    background-color: {t["scrollbar_hover"]};
}}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    width: 0px;
}}

/* ===== 页签 ===== */
QTabWidget::pane {{
    border: none;
    background-color: transparent;
}}
QTabBar::tab {{
    background-color: {t["tab_inactive"]};
    color: {t["text_secondary"]};
    border: none;
    padding: 8px 18px;
    margin-right: 2px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
}}
QTabBar::tab:selected {{
    background-color: {t["tab_active"]};
    color: {t["text"]};
    font-weight: 600;
}}
QTabBar::tab:hover:!selected {{
    background-color: {t["card_hover"]};
}}

/* ===== 进度条 ===== */
QProgressBar {{
    background-color: {t["border"]};
    border: none;
    border-radius: 4px;
    height: 8px;
    text-align: center;
    color: transparent;
}}
QProgressBar::chunk {{
    background-color: {t["accent"]};
    border-radius: 4px;
}}
QProgressBar#danger::chunk {{
    background-color: {t["danger"]};
}}

/* ===== 对话框 ===== */
QDialog {{
    background-color: {t["bg"]};
}}
QGroupBox {{
    border: 1px solid {t["border"]};
    border-radius: 8px;
    margin-top: 10px;
    padding-top: 10px;
    font-weight: 600;
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 4px;
    color: {t["text_secondary"]};
}}
QSlider::groove:horizontal {{
    height: 4px;
    background: {t["border"]};
    border-radius: 2px;
}}
QSlider::handle:horizontal {{
    background: {t["accent"]};
    width: 16px;
    height: 16px;
    margin: -6px 0;
    border-radius: 8px;
}}
QSlider::sub-page:horizontal {{
    background: {t["accent"]};
    border-radius: 2px;
}}
QCheckBox {{
    spacing: 6px;
}}
QCheckBox::indicator {{
    width: 18px;
    height: 18px;
    border-radius: 4px;
    border: 1px solid {t["border"]};
    background: {t["input_bg"]};
}}
QCheckBox::indicator:checked {{
    background: {t["accent"]};
    border: 1px solid {t["accent"]};
}}
QListWidget {{
    background-color: transparent;
    border: none;
    outline: none;
}}
QListWidget::item {{
    background-color: {t["card"]};
    border-radius: 8px;
    margin: 4px 8px;
    padding: 10px;
    border: 1px solid transparent;
}}
QListWidget::item:selected {{
    background-color: {t["card_hover"]};
    border: 1px solid {t["accent"]};
}}
QListWidget::item:hover {{
    background-color: {t["card_hover"]};
}}
QMenu {{
    background-color: {t["card"]};
    border: 1px solid {t["border"]};
    border-radius: 6px;
    padding: 6px;
}}
QMenu::item {{
    padding: 6px 20px;
    border-radius: 4px;
}}
QMenu::item:selected {{
    background-color: {t["accent"]};
    color: white;
}}
QMenu::separator {{
    height: 1px;
    background-color: {t["border"]};
    margin: 4px 8px;
}}
"""


class ThemeManager:
    def __init__(self, settings):
        self._settings = settings
        self._app = None

    def apply(self, app: QApplication):
        self._app = app
        theme = self._settings.get("theme", "dark")
        app.setStyleSheet(_qss(DARK if theme == "dark" else LIGHT))
        # 高 DPI
        app.setHighDpiScaleFactorRoundingPolicy(
            Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
        # 字体
        font = app.font()
        font.setFamily("Microsoft YaHei UI, Segoe UI, PingFang SC, sans-serif")
        app.setFont(font)

    def toggle(self):
        theme = "light" if self._settings.get("theme") == "dark" else "dark"
        self._settings.set("theme", theme)
        if self._app:
            self._app.setStyleSheet(_qss(DARK if theme == "dark" else LIGHT))

    def refresh(self):
        """重新应用当前主题（用于动态刷新）。"""
        if self._app:
            theme = self._settings.get("theme", "dark")
            self._app.setStyleSheet(_qss(DARK if theme == "dark" else LIGHT))
