"""主窗口：工具栏、页签、自适应、托盘、窗口记忆、置顶、透明度。"""
import time
from datetime import datetime, timedelta

from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont, QIcon, QAction
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QStackedWidget, QSystemTrayIcon, QMenu, QMessageBox,
    QSizePolicy, QDialog, QApplication,
)

from core.settings import Settings
from core.events import EventRepository
from core.stats import Stats
from core.ringtone import RingtoneManager
from .theme import ThemeManager
from .event_page import EventPage
from .timer_page import TimerPage
from .event_dialog import EventDialog
from .settings_dialog import SettingsDialog
from .reminder_popup import ReminderPopup


class MainWindow(QMainWindow):
    timer_finished = pyqtSignal(str)
    phase_finished = pyqtSignal(str)

    def __init__(self, app=None):
        super().__init__()
        self._settings = Settings()
        self._repo = EventRepository()
        self._stats = Stats()
        self._ringtone = RingtoneManager(self._settings)
        self._theme = ThemeManager(self._settings)
        if app:
            self._theme.apply(app)

        self._last_event_ring = 0.0   # 事件响铃去重（全局，秒级时间戳）
        self._rung_event_ids: set[str] = set()

        self.setWindowTitle("倒计时")
        self.setMinimumSize(320, 260)
        self._build_ui()
        self._build_tray()
        self._apply_settings()
        self._restore_geometry()

        # 全局 tick
        self._tick_timer = QTimer(self)
        self._tick_timer.timeout.connect(self._on_tick)
        self._tick_timer.start(1000)

        # 托盘 tooltip 刷新（每 10 秒）
        self._tray_tip_timer = QTimer(self)
        self._tray_tip_timer.timeout.connect(self._update_tray_tooltip)
        self._tray_tip_timer.start(10000)

    # ── UI 构建 ──
    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 工具栏
        self._toolbar = QWidget()
        self._toolbar.setObjectName("toolbar")
        tb = QHBoxLayout(self._toolbar)
        tb.setContentsMargins(8, 6, 8, 6)
        tb.setSpacing(6)

        self._btn_events = QPushButton("事件")
        self._btn_events.setCheckable(True)
        self._btn_events.setChecked(True)
        self._btn_events.setObjectName("tool")
        self._btn_events.clicked.connect(lambda: self._set_page(0))
        tb.addWidget(self._btn_events)

        self._btn_timer = QPushButton("计时")
        self._btn_timer.setCheckable(True)
        self._btn_timer.setObjectName("tool")
        self._btn_timer.clicked.connect(lambda: self._set_page(1))
        tb.addWidget(self._btn_timer)

        tb.addStretch()

        self._btn_new = QPushButton("＋")
        self._btn_new.setObjectName("tool")
        self._btn_new.setToolTip("新建事件")
        self._btn_new.clicked.connect(self._on_new_event)
        tb.addWidget(self._btn_new)

        self._btn_pin = QPushButton("📌")
        self._btn_pin.setCheckable(True)
        self._btn_pin.setObjectName("tool")
        self._btn_pin.setToolTip("置顶")
        self._btn_pin.clicked.connect(self._on_toggle_top)
        tb.addWidget(self._btn_pin)

        self._btn_theme = QPushButton("🌙")
        self._btn_theme.setObjectName("tool")
        self._btn_theme.setToolTip("切换主题")
        self._btn_theme.clicked.connect(self._on_toggle_theme)
        tb.addWidget(self._btn_theme)

        self._btn_more = QPushButton("⋯")
        self._btn_more.setObjectName("tool")
        self._btn_more.setToolTip("更多")
        self._btn_more.clicked.connect(self._on_more_menu)
        tb.addWidget(self._btn_more)

        layout.addWidget(self._toolbar)

        # 内容区
        self._stack = QStackedWidget()
        self._event_page = EventPage(self._repo)
        self._timer_page = TimerPage(self._settings, self._stats)
        self._stack.addWidget(self._event_page)
        self._stack.addWidget(self._timer_page)
        layout.addWidget(self._stack, 1)

        # 状态栏
        self._statusbar = QLabel("就绪")
        self._statusbar.setObjectName("secondary")
        self._statusbar.setContentsMargins(12, 6, 12, 6)
        layout.addWidget(self._statusbar)

        # 信号连接
        self.timer_finished.connect(self._on_timer_finished)
        self.phase_finished.connect(self._on_phase_finished)

    def _set_page(self, index: int):
        self._stack.setCurrentIndex(index)
        self._btn_events.setChecked(index == 0)
        self._btn_timer.setChecked(index == 1)

    # ── 系统托盘 ──
    def _build_tray(self):
        self._tray = QSystemTrayIcon(self)
        self._tray.setToolTip("倒计时")
        self._tray.activated.connect(self._on_tray_activated)

        menu = QMenu(self)
        self._act_show = QAction("显示主窗口", self)
        self._act_show.triggered.connect(self.showNormal)
        menu.addAction(self._act_show)

        self._act_pause = QAction("暂停计时", self)
        self._act_pause.triggered.connect(self._on_tray_pause)
        menu.addAction(self._act_pause)

        menu.addSeparator()
        act_quit = QAction("退出", self)
        act_quit.triggered.connect(self._quit_app)
        menu.addAction(act_quit)

        self._tray.setContextMenu(menu)
        self._tray.show()

    def _on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.showNormal()
            self.raise_()
            self.activateWindow()

    def _on_tray_pause(self):
        if self._timer_page.is_running():
            self._timer_page.pause()
            self._act_pause.setText("继续计时")
        else:
            self._timer_page.resume()
            self._act_pause.setText("暂停计时")

    def _update_tray_tooltip(self):
        status = self._timer_page.tooltip_status()
        self._tray.setToolTip(f"倒计时\n{status}")
        self._act_pause.setText(
            "暂停计时" if self._timer_page.is_running() else "继续计时"
        )

    # ── 应用设置 ──
    def _apply_settings(self):
        # 置顶
        on_top = self._settings.get("always_on_top", True)
        self._btn_pin.setChecked(on_top)
        self._set_topmost(on_top)
        # 主题
        theme = self._settings.get("theme", "dark")
        self._btn_theme.setText("🌙" if theme == "dark" else "☀️")
        # 开机自启
        self._apply_autostart()

    def _set_topmost(self, on_top: bool):
        flags = self.windowFlags()
        if on_top:
            flags |= Qt.WindowType.WindowStaysOnTopHint
        else:
            flags &= ~Qt.WindowType.WindowStaysOnTopHint
        self.setWindowFlags(flags)
        self.show()

    def _on_toggle_top(self):
        on_top = self._btn_pin.isChecked()
        self._settings.set("always_on_top", on_top)
        self._set_topmost(on_top)

    def _on_toggle_theme(self):
        self._theme.toggle()
        theme = self._settings.get("theme", "dark")
        self._btn_theme.setText("🌙" if theme == "dark" else "☀️")

    # ── 更多菜单 ──
    def _on_more_menu(self):
        menu = QMenu(self)
        act_settings = menu.addAction("设置")
        menu.addSeparator()
        act_quit = menu.addAction("退出")
        action = menu.exec(self._btn_more.mapToGlobal(self._btn_more.rect().bottomRight()))
        if action == act_settings:
            self._open_settings()
        elif action == act_quit:
            self._quit_app()

    def _open_settings(self):
        dlg = SettingsDialog(self._settings, self._stats, self._ringtone, self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self._apply_settings()
            self._theme.refresh()
            self._apply_autostart()
            self._apply_opacity()

    # ── 新建事件 ──
    def _on_new_event(self):
        dlg = EventDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            data = dlg.get_data()
            ev = self._repo.add(data["name"], data["target"], data["color"])
            self._event_page.add_event(ev)
            self._set_page(0)

    # ── 自适应 ──
    def resizeEvent(self, event):
        super().resizeEvent(event)
        w = self._stack.width()
        mode = "compact" if w < 400 else ("wide" if w >= 720 else "standard")
        self._event_page.set_layout_mode(mode)
        # timer_page 暂无三档差异，但保留接口

    # ── 全局 tick ──
    def _on_tick(self):
        now = datetime.now()
        self._event_page.refresh(now)
        self._timer_page.tick()
        self._update_statusbar()
        self._check_event_ring(now)

    def _update_statusbar(self):
        today = self._stats.today_summary()
        self._statusbar.setText(
            f"今日  番茄 {today['pomodoros']}  ·  专注 {today['minutes']} 分钟"
        )

    def _check_event_ring(self, now: datetime):
        """事件到期响铃（去重：2 秒内全局只响一次，单个事件 5 秒内不重响）。"""
        for ev in self._repo.all(now):
            sec = ev.remaining(now).total_seconds()
            if -2 <= sec <= 0:
                if ev.id not in self._rung_event_ids:
                    now_ts = time.time()
                    if now_ts - self._last_event_ring >= 2.0:
                        self._ringtone.ring(5)
                        self._last_event_ring = now_ts
                        QTimer.singleShot(5000, self._ringtone.stop)
                    self._rung_event_ids.add(ev.id)
            elif sec > 5:
                # 如果事件被编辑到未来，移除响铃记录
                self._rung_event_ids.discard(ev.id)

    # ── 计时完成处理 ──
    def _on_timer_finished(self, mode: str):
        dur = self._settings.get("ring_duration", "until_confirm")
        if dur == "15s":
            self._ringtone.ring(15)
        else:
            self._ringtone.ring()
        ReminderPopup.show(self, "时间到", "倒计时结束！", [("知道了", "dismiss")])
        self._ringtone.stop()

    def _on_phase_finished(self, phase: str):
        if phase == "focus":
            dur = self._settings.get("ring_duration", "until_confirm")
            if dur == "15s":
                self._ringtone.ring(15)
            else:
                self._ringtone.ring()
            result = ReminderPopup.show(
                self, "专注完成", "专注阶段结束，休息一下吧！",
                [("知道了", "dismiss"), ("开始休息", "next")],
            )
            self._ringtone.stop()
            if result == "next":
                # 延迟到 Pomodoro._enter() 之后执行，确保新阶段已就绪
                QTimer.singleShot(0, self._timer_page.resume)
        else:
            self._ringtone.ring(3)
            QTimer.singleShot(3000, self._ringtone.stop)

    # ── 窗口记忆 ──
    def _restore_geometry(self):
        x = self._settings.get("window.x")
        y = self._settings.get("window.y")
        w = self._settings.get("window.w", 460)
        h = self._settings.get("window.h", 660)
        if x is not None and y is not None:
            self.move(x, y)
        self.resize(w, h)
        if self._settings.get("window.maximized"):
            self.showMaximized()

    def _save_geometry(self):
        if not self.isMaximized():
            self._settings.set("window.x", self.x())
            self._settings.set("window.y", self.y())
            self._settings.set("window.w", self.width())
            self._settings.set("window.h", self.height())
        self._settings.set("window.maximized", self.isMaximized())

    # ── 透明度 / 悬停增强 ──
    def enterEvent(self, event):
        if self._settings.get("hover_boost", True):
            self.setWindowOpacity(1.0)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._apply_opacity()
        super().leaveEvent(event)

    def _apply_opacity(self):
        op = self._settings.get("opacity", 0.95)
        self.setWindowOpacity(op)

    # ── 开机自启 ──
    def _apply_autostart(self):
        try:
            from PyQt6.QtCore import QSettings
            reg = QSettings(
                "HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\Run",
                QSettings.Format.NativeFormat,
            )
            key = "CountdownWidget"
            enabled = self._settings.get("autostart", False)
            if enabled:
                import sys
                reg.setValue(key, sys.executable.replace("python.exe", "countdown.exe"))
            else:
                reg.remove(key)
        except Exception:
            pass

    # ── 关闭与退出 ──
    def closeEvent(self, event):
        if self._settings.get("close_to_tray", True):
            self.hide()
            event.ignore()
            self._tray.showMessage(
                "倒计时", "已最小化到系统托盘",
                QSystemTrayIcon.MessageIcon.Information, 2000,
            )
            return
        # 直接退出模式
        if self._timer_page.is_running():
            btn = QMessageBox.question(
                self, "确认退出", "计时进行中，确定要退出吗？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if btn != QMessageBox.StandardButton.Yes:
                event.ignore()
                return
        self._do_quit()
        event.accept()

    def _quit_app(self):
        self._do_quit()
        from PyQt6.QtWidgets import QApplication
        QApplication.quit()

    def _do_quit(self):
        self._save_geometry()
        self._ringtone.stop()
        self._tick_timer.stop()
        self._tray_tip_timer.stop()
