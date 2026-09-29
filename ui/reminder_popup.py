"""提醒弹层：计时/番茄钟归零时弹出，响铃 + 闪烁任务栏。"""
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QWidget,
)


class ReminderPopup(QDialog):
    def __init__(self, parent, title: str, message: str, buttons: list[tuple[str, str]]):
        """
        buttons: [(text, role), ...] 例如 [("知道了", "dismiss"), ("开始休息", "next")]
        """
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.Dialog |
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setMinimumWidth(320)
        self._result_role = None
        self._build_ui(title, message, buttons)
        self._setup_flash()

    def _build_ui(self, title: str, message: str, buttons: list[tuple[str, str]]):
        container = QWidget(self)
        container.setObjectName("popupContainer")
        container.setStyleSheet("""
            QWidget#popupContainer {
                background-color: #2C2C30;
                border-radius: 12px;
                border: 1px solid #3A3A3E;
            }
        """)
        layout = QVBoxLayout(container)
        layout.setSpacing(12)
        layout.setContentsMargins(24, 20, 24, 20)

        title_lbl = QLabel(title)
        title_lbl.setFont(QFont("", 16, QFont.Weight.Bold))
        title_lbl.setStyleSheet("color: #F0F0F5; background: transparent;")
        layout.addWidget(title_lbl)

        msg_lbl = QLabel(message)
        msg_lbl.setWordWrap(True)
        msg_lbl.setStyleSheet("color: #8E8E93; background: transparent;")
        layout.addWidget(msg_lbl)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        for text, role in buttons:
            btn = QPushButton(text)
            if role == "dismiss":
                btn.setObjectName("flat")
            btn.clicked.connect(lambda _checked, r=role: self._on_click(r))
            btn_row.addWidget(btn)
        layout.addLayout(btn_row)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(container)

    def _setup_flash(self):
        # Windows 任务栏闪烁
        try:
            import ctypes
            self._flash_timer = QTimer(self)
            self._flash_timer.timeout.connect(self._flash_window)
            self._flash_timer.start(800)
            self._flash_state = False
        except Exception:
            pass

    def _flash_window(self):
        try:
            import ctypes
            hwnd = self.winId().__int__()
            # FLASHW_ALL = 3, FLASHW_TIMERNOFG = 12
            class FLASHWINFO(ctypes.Structure):
                _fields_ = [
                    ("cbSize", ctypes.c_uint),
                    ("hwnd", ctypes.c_void_p),
                    ("dwFlags", ctypes.c_uint),
                    ("uCount", ctypes.c_uint),
                    ("dwTimeout", ctypes.c_uint),
                ]
            flash = FLASHWINFO()
            flash.cbSize = ctypes.sizeof(FLASHWINFO)
            flash.hwnd = hwnd
            flash.dwFlags = 3 | 12  # FLASHW_ALL | FLASHW_TIMERNOFG
            flash.uCount = 1
            ctypes.windll.user32.FlashWindowEx(ctypes.byref(flash))
        except Exception:
            pass

    def _on_click(self, role: str):
        self._result_role = role
        if hasattr(self, "_flash_timer"):
            self._flash_timer.stop()
        self.accept()

    def role(self) -> str | None:
        return self._result_role

    @classmethod
    def show(cls, parent, title: str, message: str, buttons=None):
        if buttons is None:
            buttons = [("知道了", "dismiss")]
        dlg = cls(parent, title, message, buttons)
        dlg.exec()
        return dlg.role()
