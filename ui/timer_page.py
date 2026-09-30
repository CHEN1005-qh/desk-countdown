"""计时页：自定义倒计时 + 番茄钟，含环形进度条与大数字。"""
from PyQt6.QtCore import Qt, QTimer, QRect
from PyQt6.QtGui import QFont, QPainter, QColor, QPen, QBrush
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGridLayout, QProgressBar, QSizePolicy,
)

from core.timer_engine import CountdownTimer, TimerState, format_seconds
from core.pomodoro import Pomodoro, Phase, PHASE_LABEL


class CircularProgress(QWidget):
    """环形进度条，0~1。"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self._progress = 0.0
        self.setMinimumSize(160, 160)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def set_progress(self, value: float):
        self._progress = max(0.0, min(1.0, value))
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self.rect().adjusted(10, 10, -10, -10)
        size = min(rect.width(), rect.height())
        rect = QRect(rect.center().x() - size // 2, rect.center().y() - size // 2, size, size)
        
        pen_width = max(8, size // 20)
        # 背景环
        pen = QPen(QColor("#3A3A3E"))
        pen.setWidth(pen_width)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        painter.drawArc(rect, 0, 360 * 16)
        
        # 进度环
        progress_pen = QPen(QColor("#0A84FF"))
        progress_pen.setWidth(pen_width)
        progress_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(progress_pen)
        span = int(-self._progress * 360 * 16)
        painter.drawArc(rect, 90 * 16, span)
        painter.end()


class TimerPage(QWidget):
    def __init__(self, settings, stats, parent=None):
        super().__init__(parent)
        self._settings = settings
        self._stats = stats
        self._mode = "countdown"  # countdown | pomodoro
        self._timer = CountdownTimer(parent=self)
        self._pomodoro = Pomodoro(settings, stats, parent=self)
        self._build_ui()
        self._bind_signals()
        self._apply_mode()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(12)

        # 模式切换
        mode_row = QHBoxLayout()
        mode_row.setSpacing(4)
        self._btn_countdown = QPushButton("倒计时")
        self._btn_countdown.setCheckable(True)
        self._btn_countdown.setObjectName("tool")
        self._btn_countdown.setChecked(True)
        self._btn_countdown.clicked.connect(lambda: self.set_mode("countdown"))
        mode_row.addWidget(self._btn_countdown)

        self._btn_pomodoro = QPushButton("番茄钟")
        self._btn_pomodoro.setCheckable(True)
        self._btn_pomodoro.setObjectName("tool")
        self._btn_pomodoro.clicked.connect(lambda: self.set_mode("pomodoro"))
        mode_row.addWidget(self._btn_pomodoro)
        mode_row.addStretch()
        layout.addLayout(mode_row)

        # 阶段名（番茄钟用）
        self._phase_lbl = QLabel("就绪")
        self._phase_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._phase_lbl.setFont(QFont("", 14, QFont.Weight.Bold))
        layout.addWidget(self._phase_lbl)

        # 大数字 + 进度环
        self._digit_lbl = QLabel("00:00")
        self._digit_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._digit_lbl.setFont(QFont("", 48, QFont.Weight.Bold))
        layout.addWidget(self._digit_lbl)

        self._ring = CircularProgress()
        layout.addWidget(self._ring, 1)

        # 水平进度条（倒计时模式备用，默认隐藏）
        self._bar = QProgressBar()
        self._bar.setTextVisible(False)
        self._bar.setMaximumHeight(6)
        self._bar.hide()
        layout.addWidget(self._bar)

        # 番茄进度点
        self._dots_lbl = QLabel("")
        self._dots_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._dots_lbl.setObjectName("secondary")
        layout.addWidget(self._dots_lbl)

        # 控制按钮
        ctrl_row = QHBoxLayout()
        ctrl_row.setSpacing(8)
        self._btn_start = QPushButton("开始")
        self._btn_start.clicked.connect(self._on_start)
        ctrl_row.addWidget(self._btn_start)

        self._btn_pause = QPushButton("暂停")
        self._btn_pause.clicked.connect(self._on_pause)
        self._btn_pause.hide()
        ctrl_row.addWidget(self._btn_pause)

        self._btn_skip = QPushButton("跳过")
        self._btn_skip.setObjectName("flat")
        self._btn_skip.clicked.connect(self._on_skip)
        ctrl_row.addWidget(self._btn_skip)

        self._btn_reset = QPushButton("重置")
        self._btn_reset.setObjectName("flat")
        self._btn_reset.clicked.connect(self._on_reset)
        ctrl_row.addWidget(self._btn_reset)
        layout.addLayout(ctrl_row)

        # 快捷按钮（倒计时模式）
        self._quick_wrap = QWidget()
        quick_grid = QGridLayout(self._quick_wrap)
        quick_grid.setContentsMargins(0, 0, 0, 0)
        quick_grid.setSpacing(6)
        self._quick_btns = []
        minutes = self._settings.get("timer.quick_minutes", [5, 10, 15, 25, 30, 45, 60])
        for i, m in enumerate(minutes):
            btn = QPushButton(f"{m}分")
            btn.setObjectName("tool")
            btn.clicked.connect(lambda _checked, mm=m: self._quick_set(mm))
            self._quick_btns.append(btn)
            quick_grid.addWidget(btn, i // 4, i % 4)
        layout.addWidget(self._quick_wrap)

        # 微调按钮（倒计时模式）
        self._adjust_wrap = QWidget()
        adjust_row = QHBoxLayout(self._adjust_wrap)
        adjust_row.setContentsMargins(0, 0, 0, 0)
        for delta, label in [(-300, "-5分"), (-60, "-1分"), (+60, "+1分"), (+300, "+5分")]:
            btn = QPushButton(label)
            btn.setObjectName("tool")
            btn.clicked.connect(lambda _checked, d=delta: self._adjust(d))
            adjust_row.addWidget(btn)
        adjust_row.addStretch()
        layout.addWidget(self._adjust_wrap)

        self._adjust_widgets = [self._quick_wrap, self._adjust_wrap]

    def _bind_signals(self):
        self._timer.state_changed.connect(self._on_timer_state)
        self._timer.finished.connect(self._on_timer_finished)
        self._pomodoro.phase_changed.connect(self._on_phase_changed)
        self._pomodoro.phase_finished.connect(self._on_phase_finished)
        self._pomodoro.run_state_changed.connect(self._on_run_state_changed)

    def set_mode(self, mode: str):
        if self._mode == mode:
            return
        self._mode = mode
        self._apply_mode()

    def _apply_mode(self):
        self._btn_countdown.setChecked(self._mode == "countdown")
        self._btn_pomodoro.setChecked(self._mode == "pomodoro")
        # 重置计时器
        self._timer.reset()
        self._pomodoro.reset()
        self._update_display()
        # 显示/隐藏番茄钟专属控件
        is_pomo = self._mode == "pomodoro"
        self._phase_lbl.setVisible(is_pomo)
        self._dots_lbl.setVisible(is_pomo)
        self._ring.setVisible(is_pomo)
        self._bar.setVisible(not is_pomo)
        for w in self._adjust_widgets:
            w.setVisible(not is_pomo)
        self._btn_skip.setVisible(is_pomo)

    # ---- 控制 ----
    def _on_start(self):
        if self._mode == "countdown":
            if self._timer.state == TimerState.IDLE:
                self._timer.configure(self._settings.get("timer.default_minutes", 25) * 60)
            self._timer.start()
        else:
            self._pomodoro.start()
        self._update_controls()

    def _on_pause(self):
        if self._mode == "countdown":
            self._timer.pause()
        else:
            self._pomodoro.pause()
        self._update_controls()

    def _on_skip(self):
        if self._mode == "pomodoro":
            self._pomodoro.skip()
            self._update_display()
            self._update_controls()

    def _on_reset(self):
        if self._mode == "countdown":
            self._timer.reset()
        else:
            self._pomodoro.reset()
        self._update_display()
        self._update_controls()

    def _quick_set(self, minutes: int):
        self.set_mode("countdown")
        self._timer.configure(minutes * 60)
        self._timer.start()
        self._update_display()
        self._update_controls()

    def _adjust(self, delta: int):
        self._timer.adjust(delta)
        self._update_display()

    # ---- 显示更新 ----
    def _update_display(self):
        if self._mode == "countdown":
            remain = self._timer.remaining()
            self._digit_lbl.setText(format_seconds(remain))
            prog = self._timer.progress()
            self._bar.setValue(int(prog * 100))
            self._ring.set_progress(prog)
        else:
            remain = self._pomodoro.remaining()
            self._digit_lbl.setText(format_seconds(remain))
            prog = self._pomodoro.progress()
            self._ring.set_progress(prog)
            self._phase_lbl.setText(PHASE_LABEL.get(self._pomodoro.phase, ""))
            # 进度点
            total = self._pomodoro.long_break_every()
            filled = min(self._pomodoro.cycle_dots, total)
            empty = max(0, total - self._pomodoro.cycle_dots)
            dots = "●" * filled + "○" * empty
            self._dots_lbl.setText(f"{dots}  本轮 {filled}/{total}")

    def _update_controls(self):
        if self._mode == "countdown":
            running = self._timer.state == TimerState.RUNNING
        else:
            running = self._pomodoro.running
        self._btn_start.setVisible(not running)
        self._btn_pause.setVisible(running)

    def _on_timer_state(self, state):
        self._update_controls()

    def _host(self):
        """返回持有 timer_finished / phase_finished 信号的主窗口（顶层窗口）。

        TimerPage 被 addWidget 到 QStackedWidget 后 parent 变成 QStackedWidget，
        它没有这两个信号；必须向上找到真正的顶层窗口。
        """
        win = self.window()
        return win if hasattr(win, "timer_finished") else None

    def _on_timer_finished(self):
        self._update_display()
        self._update_controls()
        # 通知主窗口响铃
        host = self._host()
        if host is not None:
            host.timer_finished.emit("countdown")

    def _on_phase_changed(self, phase):
        self._update_display()
        self._update_controls()

    def _on_phase_finished(self, phase):
        self._update_display()
        self._update_controls()
        host = self._host()
        if host is not None:
            host.phase_finished.emit(phase.value)

    def _on_run_state_changed(self, running):
        self._update_controls()

    # ---- 外部 tick ----
    def tick(self):
        if self._mode == "countdown":
            self._timer.on_tick()
        else:
            self._pomodoro.on_tick()
        self._update_display()

    # ---- 查询 ----
    def is_running(self) -> bool:
        if self._mode == "countdown":
            return self._timer.is_running()
        return self._pomodoro.running

    def tooltip_status(self) -> str:
        if self._mode == "countdown":
            if self._timer.state == TimerState.RUNNING:
                return f"倒计时 {format_seconds(self._timer.remaining())}"
            return "倒计时 已暂停"
        if self._pomodoro.phase != Phase.IDLE:
            label = PHASE_LABEL.get(self._pomodoro.phase, "")
            return f"{label} {format_seconds(self._pomodoro.remaining())}"
        return "番茄钟 就绪"

    def pause(self):
        self._on_pause()

    def resume(self):
        self._on_start()
