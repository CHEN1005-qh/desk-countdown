"""事件页：事件列表，自适应三档布局，右键编辑/删除。"""
from datetime import datetime, timedelta

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QColor
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea,
    QGridLayout, QFrame, QMenu, QSizePolicy, QMessageBox, QDialog,
)

from core.events import CountdownEvent, EventRepository, COLOR_HEX
from .event_dialog import EventDialog


def _fmt_remain(td: timedelta) -> tuple[str, bool]:
    """返回 (显示文本, 是否已到期)。"""
    total = int(td.total_seconds())
    if total > 0:
        days, rem = divmod(total, 86400)
        hours, rem = divmod(rem, 3600)
        mins, secs = divmod(rem, 60)
        parts = []
        if days:
            parts.append(f"{days}天")
        if hours:
            parts.append(f"{hours}时")
        if mins:
            parts.append(f"{mins}分")
        parts.append(f"{secs}秒")
        return " ".join(parts), False
    else:
        days = abs(total) // 86400
        return f"已过去 {days} 天", True


class EventCard(QFrame):
    def __init__(self, event: CountdownEvent, repo: EventRepository, parent=None):
        super().__init__(parent)
        self.event = event
        self._repo = repo
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setStyleSheet("""
            EventCard {
                background-color: #252529;
                border-radius: 10px;
                border: 1px solid transparent;
            }
            EventCard[overdue="true"] {
                border: 1px solid #FF453A;
            }
        """)
        self.setObjectName("EventCard")
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_menu)
        self._build_ui()

    def _build_ui(self):
        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(12, 10, 12, 10)
        self._layout.setSpacing(10)

        # 色块
        self._color_dot = QLabel()
        self._color_dot.setFixedSize(12, 12)
        self._color_dot.setStyleSheet(
            f"background-color: {COLOR_HEX.get(self.event.color, '#0091FF')}; "
            "border-radius: 6px;"
        )
        self._layout.addWidget(self._color_dot)

        # 名称 + 时间 垂直
        v = QVBoxLayout()
        v.setSpacing(4)
        self._name_lbl = QLabel(self.event.name)
        self._name_lbl.setFont(QFont("", 11, QFont.Weight.Bold))
        v.addWidget(self._name_lbl)

        self._time_lbl = QLabel()
        self._time_lbl.setObjectName("secondary")
        v.addWidget(self._time_lbl)
        self._layout.addLayout(v, 1)

        # 目标日期（小字）
        self._target_lbl = QLabel(self.event.target.strftime("%m-%d %H:%M"))
        self._target_lbl.setObjectName("secondary")
        self._target_lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self._layout.addWidget(self._target_lbl)

    def update_display(self, now: datetime):
        text, overdue = _fmt_remain(self.event.remaining(now))
        self._time_lbl.setText(text)
        self.setProperty("overdue", "true" if overdue else "false")
        self.style().unpolish(self)
        self.style().polish(self)
        # 到期高亮名称
        if overdue:
            self._name_lbl.setStyleSheet("color: #FF453A; background: transparent;")
        else:
            self._name_lbl.setStyleSheet("")

    def _show_menu(self, pos):
        menu = QMenu(self)
        edit_act = menu.addAction("编辑")
        del_act = menu.addAction("删除")
        action = menu.exec(self.mapToGlobal(pos))
        if action == edit_act:
            self._edit()
        elif action == del_act:
            self._delete()

    def _edit(self):
        dlg = EventDialog(self, self.event)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            data = dlg.get_data()
            self._repo.update(
                self.event.id, data["name"], data["target"], data["color"]
            )

    def _delete(self):
        # 已到期事件不弹确认
        now = datetime.now()
        overdue = self.event.remaining(now).total_seconds() <= 0
        if not overdue:
            btn = QMessageBox.question(
                self, "删除确认", f"确定删除「{self.event.name}」吗？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if btn != QMessageBox.StandardButton.Yes:
                return
        self._repo.remove(self.event.id)
        self.deleteLater()

    def mouseDoubleClickEvent(self, event):
        self._edit()


class EventPage(QWidget):
    def __init__(self, repo: EventRepository, parent=None):
        super().__init__(parent)
        self.repo = repo
        self._cards: dict[str, EventCard] = {}
        self._mode = "standard"
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        layout.addWidget(self._scroll)

        self._container = QWidget()
        self._scroll.setWidget(self._container)

        self._grid = QGridLayout(self._container)
        self._grid.setContentsMargins(8, 8, 8, 8)
        self._grid.setSpacing(8)
        self._grid.setAlignment(Qt.AlignmentFlag.AlignTop)

    def set_layout_mode(self, mode: str):
        """compact / standard / wide"""
        if self._mode == mode:
            return
        self._mode = mode
        # 重排卡片
        self._reflow()

    def _reflow(self):
        # 清空布局但保留卡片引用
        while self._grid.count():
            item = self._grid.takeAt(0)
            if item.widget():
                item.widget().setParent(None)
        # 按模式重新放置
        cards = list(self._cards.values())
        if self._mode == "wide":
            cols = 2
            for i, card in enumerate(cards):
                self._grid.addWidget(card, i // cols, i % cols)
        else:
            for i, card in enumerate(cards):
                self._grid.addWidget(card, i, 0)

    def refresh(self, now: datetime):
        events = self.repo.all(now)
        # 移除已不存在的卡片
        ids = {e.id for e in events}
        for ev_id in list(self._cards.keys()):
            if ev_id not in ids:
                self._cards[ev_id].deleteLater()
                del self._cards[ev_id]
        # 添加新卡片或更新现有卡片
        for i, ev in enumerate(events):
            if ev.id not in self._cards:
                card = EventCard(ev, self.repo)
                self._cards[ev.id] = card
            else:
                card = self._cards[ev.id]
                card.event = ev
                card._repo = self.repo
            card.update_display(now)
        self._reflow()

    def add_event(self, event: CountdownEvent):
        self._cards[event.id] = EventCard(event, self.repo)
        self._reflow()
