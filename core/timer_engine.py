"""时长倒计时引擎。

关键约束（PRD 3.2.3）：剩余时间一律用「结束时间戳 - 当前时间」计算，
禁止 tick 累加 —— 系统休眠、界面卡顿后计时自动纠正，不漂移。
"""
import time
from enum import Enum

from PyQt6.QtCore import QObject, pyqtSignal


class TimerState(Enum):
    IDLE = "idle"          # 未装载/已重置
    RUNNING = "running"    # 计时中
    PAUSED = "paused"      # 暂停
    FINISHED = "finished"  # 已归零


class CountdownTimer(QObject):
    state_changed = pyqtSignal(object)   # TimerState
    finished = pyqtSignal()              # 自然归零（一次）

    def __init__(self, now_fn=time.time, parent=None):
        super().__init__(parent)
        self._now = now_fn
        self._duration = 0.0       # 最近一次装载的总时长（秒），供重置/进度条使用
        self._remain = 0.0         # 暂停/空闲时的剩余秒数
        self._end_ts = None        # 运行中的结束时间戳
        self._state = TimerState.IDLE

    # ---- 状态查询 ----
    @property
    def state(self) -> TimerState:
        return self._state

    @property
    def duration(self) -> float:
        return self._duration

    def remaining(self) -> float:
        if self._state is TimerState.RUNNING:
            return max(0.0, self._end_ts - self._now())
        return self._remain

    def is_running(self) -> bool:
        return self._state is TimerState.RUNNING

    def progress(self) -> float:
        """已消耗比例 0~1"""
        if self._duration <= 0:
            return 0.0
        return 1.0 - self.remaining() / self._duration

    # ---- 状态流转 ----
    def _set_state(self, s: TimerState):
        if s is not self._state:
            self._state = s
            self.state_changed.emit(s)

    def configure(self, seconds: float):
        """装载时长（仅空闲/已结束状态可用）"""
        if self._state in (TimerState.IDLE, TimerState.FINISHED):
            self._duration = max(1.0, float(seconds))
            self._remain = self._duration
            self._set_state(TimerState.IDLE)

    def adjust(self, delta_seconds: float):
        """±1/±5 分钟微调（空闲/暂停时可用），范围 1s ~ 24h"""
        if self._state in (TimerState.IDLE, TimerState.PAUSED):
            self._remain = min(24 * 3600.0, max(1.0, self._remain + delta_seconds))
            self._duration = max(self._duration, self._remain)

    def start(self):
        """开始 / 继续"""
        if self._state in (TimerState.IDLE, TimerState.PAUSED) and self._remain > 0:
            self._end_ts = self._now() + self._remain
            self._set_state(TimerState.RUNNING)

    def pause(self):
        if self._state is TimerState.RUNNING:
            self._remain = self.remaining()
            self._set_state(TimerState.PAUSED)

    def reset(self):
        self._remain = self._duration
        self._set_state(TimerState.IDLE)

    # ---- 由外部统一 tick 驱动 ----
    def on_tick(self):
        if self._state is TimerState.RUNNING and self.remaining() <= 0:
            self._remain = 0.0
            self._set_state(TimerState.FINISHED)
            self.finished.emit()


def format_seconds(sec: float) -> str:
    """MM:SS，≥1 小时显示 H:MM:SS"""
    sec = max(0, int(round(sec)))
    h, rem = divmod(sec, 3600)
    m, s = divmod(rem, 60)
    if h > 0:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"
