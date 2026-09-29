import tempfile
from pathlib import Path

from core.pomodoro import Pomodoro, Phase
from core.settings import Settings
from core.stats import Stats


def test_focus_to_short_break():
    now = [1000.0]
    with tempfile.TemporaryDirectory() as tmp:
        settings = Settings(Path(tmp) / "settings.json")
        stats = Stats(Path(tmp) / "stats.json")
        pomo = Pomodoro(settings, stats, now_fn=lambda: now[0])
        pomo.start()
        assert pomo.phase == Phase.FOCUS
        assert pomo.running is True
        # 快进 25 分钟
        now[0] += 25 * 60 + 1
        pomo.on_tick()
        assert pomo.phase == Phase.SHORT_BREAK


def test_cycle_dots():
    now = [1000.0]
    with tempfile.TemporaryDirectory() as tmp:
        settings = Settings(Path(tmp) / "settings.json")
        stats = Stats(Path(tmp) / "stats.json")
        pomo = Pomodoro(settings, stats, now_fn=lambda: now[0])
        pomo.start()
        now[0] += 25 * 60 + 1
        pomo.on_tick()
        assert pomo.cycle_dots == 1


def test_skip_does_not_count():
    now = [1000.0]
    with tempfile.TemporaryDirectory() as tmp:
        settings = Settings(Path(tmp) / "settings.json")
        stats = Stats(Path(tmp) / "stats.json")
        pomo = Pomodoro(settings, stats, now_fn=lambda: now[0])
        pomo.start()
        pomo.skip()
        assert pomo.cycle_dots == 0
        assert pomo.phase == Phase.SHORT_BREAK


def test_long_break_every():
    now = [1000.0]
    with tempfile.TemporaryDirectory() as tmp:
        settings = Settings(Path(tmp) / "settings.json")
        # 设置每 2 个番茄长休息
        settings.set("pomodoro.long_break_every", 2, save=False)
        stats = Stats(Path(tmp) / "stats.json")
        pomo = Pomodoro(settings, stats, now_fn=lambda: now[0])
        # 第一个番茄
        pomo.start()
        now[0] += 25 * 60 + 1
        pomo.on_tick()
        assert pomo.phase == Phase.SHORT_BREAK
        # 休息结束 -> 第二个番茄
        now[0] += 5 * 60 + 1
        pomo.on_tick()
        assert pomo.phase == Phase.FOCUS
        # 第二个番茄完成 -> 长休息
        now[0] += 25 * 60 + 1
        pomo.on_tick()
        assert pomo.phase == Phase.LONG_BREAK
