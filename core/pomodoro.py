"""番茄钟状态机：专注/短休息/长休息循环。

- 番茄计数规则（PRD 3.2.2）：专注阶段自然走完才 +1 并计入统计，手动跳过不计。
- 与倒计时引擎相同：基于时间戳计算剩余，休眠唤醒自动纠正。
"""
import time
from enum import Enum

from PyQt6.QtCore import QObject, pyqtSignal


class Phase(Enum):
    IDLE = "idle"
    FOCUS = "focus"
    SHORT_BREAK = "short_break"
    LONG_BREAK = "long_break"


PHASE_LABEL = {
    Phase.IDLE: "就绪",
    Phase.FOCUS: "专注",
    Phase.SHORT_BREAK: "短休息",
    Phase.LONG_BREAK: "长休息",
}


class Pomodoro(QObject):
    phase_changed = pyqtSignal(object)   # Phase：新阶段进入（含暂停/继续引起的运行态变化）
    phase_finished = pyqtSignal(object)  # Phase：某阶段自然结束（归零）
    run_state_changed = pyqtSignal(bool) # running 状态变化

    def __init__(self, settings, stats, now_fn=time.time, parent=None):
        super().__init__(parent)
        self._settings = settings
        self._stats = stats
        self._now = now_fn

        self.phase = Phase.IDLE
        self.running = False
        self._end_ts = None
        self._remain = 0.0
        self._duration = 0.0
        self.cycle_dots = 0   # 本轮（两次长休息之间）已完成的番茄数

    # ---- 参数 ----
    def _minutes(self, key: str) -> int:
        return int(self._settings.get(f"pomodoro.{key}", DEFAULT_POMODORO[key]))

    def phase_minutes(self, phase: Phase) -> int:
        key = {
            Phase.FOCUS: "focus",
            Phase.SHORT_BREAK: "short_break",
            Phase.LONG_BREAK: "long_break",
        }.get(phase)
        return self._minutes(key) if key else 0

    def long_break_every(self) -> int:
        return max(1, self._minutes("long_break_every"))

    def auto_start_next(self) -> bool:
        return bool(self._settings.get("pomodoro.auto_start_next", True))

    # ---- 状态查询 ----
    def is_active(self) -> bool:
        return self.phase is not Phase.IDLE

    def remaining(self) -> float:
        if self.running:
            return max(0.0, self._end_ts - self._now())
        return self._remain

    def progress(self) -> float:
        """已消耗比例 0~1"""
        if self._duration <= 0:
            return 0.0
        return 1.0 - self.remaining() / self._duration

    # ---- 控制 ----
    def start(self):
        """开始（空闲→专注）或继续（暂停/pending 态）"""
        if self.phase is Phase.IDLE:
            self._enter(Phase.FOCUS, running=True)
        elif not self.running and self._remain > 0:
            self._resume()
        elif not self.running:
            self._enter(self.phase, running=True)

    def pause(self):
        if self.running:
            self._remain = self.remaining()
            self.running = False
            self.run_state_changed.emit(False)

    def skip(self):
        """手动跳过当前阶段：不计统计，直接进入下一阶段；运行状态保持。"""
        if self.phase is Phase.IDLE:
            return
        if self.phase is Phase.LONG_BREAK:
            self.cycle_dots = 0
        nxt = self._next_after(self.phase)
        self._enter(nxt, running=self.running)

    def reset(self):
        self.phase = Phase.IDLE
        self.running = False
        self._remain = self._duration = 0.0
        self.cycle_dots = 0
        self.phase_changed.emit(Phase.IDLE)

    # ---- 内部流转 ----
    def _next_after(self, phase: Phase) -> Phase:
        if phase is Phase.FOCUS:
            if self.cycle_dots >= self.long_break_every():
                return Phase.LONG_BREAK
            return Phase.SHORT_BREAK
        return Phase.FOCUS  # 休息结束 → 专注

    def _enter(self, phase: Phase, running: bool):
        was_running = self.running
        self.phase = phase
        self._duration = self.phase_minutes(phase) * 60.0
        self.running = running
        if running:
            self._end_ts = self._now() + self._duration
            self._remain = self._duration
        else:
            self._remain = self._duration
        self.phase_changed.emit(phase)
        if was_running != running:
            self.run_state_changed.emit(running)

    def _resume(self):
        self._end_ts = self._now() + self._remain
        self.running = True
        self.run_state_changed.emit(True)

    # ---- 由外部统一 tick 驱动 ----
    def on_tick(self):
        if not (self.running and self.phase is not Phase.IDLE):
            return
        if self.remaining() > 0:
            return

        ended = self.phase
        if ended is Phase.FOCUS:
            # 自然完成 → 计入番茄与统计
            self.cycle_dots += 1
            self._stats.record(int(round(self._duration / 60)), "pomodoro")
        elif ended is Phase.LONG_BREAK:
            self.cycle_dots = 0

        # 先置为停止态，防止弹窗 exec() 阻塞期间被重复触发
        self.running = False
        self._remain = 0.0

        nxt = self._next_after(ended)
        self.phase_finished.emit(ended)
        self._enter(nxt, running=self.auto_start_next())


DEFAULT_POMODORO = {"focus": 25, "short_break": 5, "long_break": 15, "long_break_every": 4}
