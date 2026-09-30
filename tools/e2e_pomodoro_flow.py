"""端到端集成验证：MainWindow + TimerPage 番茄钟结束全链路（压缩时钟）。

将 25 分钟专注压缩为一次 tick 触发，走完整链路：
tick → Pomodoro.on_tick → phase_finished 信号 → 主窗口响铃+弹窗 → 进入短休息。

验证：
- 全程无未捕获异常（即无闪退）
- 结束后自动进入短休息并运行
- 专注统计已记录

运行：python tools/e2e_pomodoro_flow.py   （期望输出 [PASS]，退出码 0）
注意：会向真实 data/stats.json 写入一条专注记录。
"""
import os
import sys
import time

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QApplication

from core.pomodoro import Phase
from core.timer_engine import TimerState
from ui.main_window import MainWindow


def main():
    app = QApplication(sys.argv)

    win = MainWindow(app)
    win.show()

    page = win._timer_page
    page.set_mode("pomodoro")
    pomo = page._pomodoro

    # 压缩时钟：真实时间源换成可推进的
    fake_now = [time.time()]
    pomo._now = lambda: fake_now[0]

    state = {"finished": 0}

    def drive():
        assert pomo.phase is Phase.FOCUS and pomo.running
        fake_now[0] += 25 * 60 + 1
        win._timer_page.tick()   # 等价于主窗口 tick 定时器触发
        state["finished"] = 1

    pomo.start()
    QTimer.singleShot(200, drive)
    QTimer.singleShot(3000, app.quit)

    app.exec()

    # 断言整条链路无异常且状态正确
    assert state["finished"] == 1, "阶段结束信号未触发"
    assert pomo.phase is Phase.SHORT_BREAK, f"应进入短休息, 实际 {pomo.phase}"
    assert pomo.running is True, "auto_start_next 应自动开始短休息"
    assert pomo.cycle_dots == 1
    assert win._stats.today()["count"] >= 1, "专注统计未记录"

    print("[PASS] 番茄钟：专注结束 → 响铃 → 弹窗 → 短休息，全程无闪退")

    # ---- 第二段：倒计时模式结束链路（同样曾因 parent 信号崩溃）----
    page.set_mode("countdown")
    timer = page._timer
    timer._now = lambda: fake_now[0]
    timer.configure(25 * 60)
    timer.start()
    assert timer.state is TimerState.RUNNING

    state2 = {"finished": 0}

    def drive2():
        fake_now[0] += 25 * 60 + 1
        page.tick()
        state2["finished"] = 1

    QTimer.singleShot(200, drive2)
    QTimer.singleShot(3000, app.quit)

    app.exec()

    assert state2["finished"] == 1, "倒计时结束信号未触发"
    assert timer.state is TimerState.FINISHED, f"应 finished, 实际 {timer.state}"

    print("[PASS] 倒计时：归零 → 响铃 → 弹窗，全程无闪退")
    return 0


if __name__ == "__main__":
    sys.exit(main())
