"""新建 / 编辑事件对话框。"""
from datetime import datetime, timedelta

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QDateTimeEdit, QPushButton, QWidget, QGridLayout,
)

from core.events import COLOR_PRESETS, COLOR_HEX


class ColorButton(QPushButton):
    def __init__(self, color_key: str, hex_color: str, parent=None):
        super().__init__(parent)
        self.color_key = color_key
        self.setFixedSize(28, 28)
        self.setStyleSheet(
            f"background-color: {hex_color}; border-radius: 14px; border: 2px solid transparent;"
        )
        self.setCheckable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def set_checked(self, checked: bool):
        self.setChecked(checked)
        border = "white" if checked else "transparent"
        self.setStyleSheet(
            self.styleSheet().replace(
                f"border: 2px solid {('white' if not checked else 'transparent')};",
                f"border: 2px solid {border};"
            )
        )


class EventDialog(QDialog):
    def __init__(self, parent=None, event=None):
        super().__init__(parent)
        self._event = event
        self._selected_color = event.color if event else "blue"
        self.setWindowTitle("编辑事件" if event else "新建事件")
        self.setMinimumWidth(360)
        self._build_ui()
        if event:
            self._load_event()
        else:
            self._set_default_time()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)

        # 名称
        layout.addWidget(QLabel("事件名称"))
        self.name_edit = QLineEdit()
        self.name_edit.setMaxLength(30)
        self.name_edit.setPlaceholderText("例如：考研、春节、纪念日…")
        layout.addWidget(self.name_edit)

        # 目标时间
        layout.addWidget(QLabel("目标时间"))
        self.time_edit = QDateTimeEdit()
        self.time_edit.setCalendarPopup(True)
        self.time_edit.setDisplayFormat("yyyy-MM-dd HH:mm")
        self.time_edit.setDateTime(datetime.now())
        layout.addWidget(self.time_edit)

        # 颜色标签
        layout.addWidget(QLabel("颜色标签"))
        color_grid = QGridLayout()
        color_grid.setSpacing(8)
        self._color_buttons = []
        for i, (key, hex_c) in enumerate(COLOR_PRESETS):
            btn = ColorButton(key, hex_c)
            btn.clicked.connect(lambda _checked, k=key: self._on_color_pick(k))
            self._color_buttons.append(btn)
            color_grid.addWidget(btn, i // 4, i % 4)
        layout.addLayout(color_grid)

        # 按钮
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.setObjectName("flat")
        self.cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(self.cancel_btn)

        self.save_btn = QPushButton("保存")
        self.save_btn.clicked.connect(self._on_save)
        btn_row.addWidget(self.save_btn)
        layout.addLayout(btn_row)

    def _set_default_time(self):
        tomorrow = datetime.now() + timedelta(days=1)
        tomorrow = tomorrow.replace(hour=9, minute=0, second=0, microsecond=0)
        self.time_edit.setDateTime(tomorrow)

    def _load_event(self):
        self.name_edit.setText(self._event.name)
        self.time_edit.setDateTime(self._event.target)
        self._on_color_pick(self._event.color)

    def _on_color_pick(self, key: str):
        self._selected_color = key
        for btn in self._color_buttons:
            btn.setChecked(btn.color_key == key)
            # 重绘边框
            hex_c = COLOR_HEX[btn.color_key]
            border = "white" if btn.isChecked() else "transparent"
            btn.setStyleSheet(
                f"background-color: {hex_c}; border-radius: 14px; border: 2px solid {border};"
            )

    def _on_save(self):
        name = self.name_edit.text().strip()
        if not name:
            self.name_edit.setPlaceholderText("请填写事件名称")
            return
        self.accept()

    def get_data(self):
        return {
            "name": self.name_edit.text().strip(),
            "target": self.time_edit.dateTime().toPyDateTime(),
            "color": self._selected_color,
        }
