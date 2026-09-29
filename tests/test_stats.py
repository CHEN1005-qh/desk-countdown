import tempfile
from pathlib import Path

from core.stats import Stats


def test_record_and_today():
    with tempfile.TemporaryDirectory() as tmp:
        stats = Stats(Path(tmp) / "stats.json")
        stats.record(25, "pomodoro")
        stats.record(10, "timer")
        today = stats.today()
        assert today["count"] == 1
        assert today["minutes"] == 35


def test_totals():
    with tempfile.TemporaryDirectory() as tmp:
        stats = Stats(Path(tmp) / "stats.json")
        stats.record(25, "pomodoro")
        total = stats.totals()
        assert total["count"] == 1
        assert total["minutes"] == 25


def test_clear():
    with tempfile.TemporaryDirectory() as tmp:
        stats = Stats(Path(tmp) / "stats.json")
        stats.record(25, "pomodoro")
        stats.clear()
        assert stats.today()["minutes"] == 0


def test_summary_methods():
    with tempfile.TemporaryDirectory() as tmp:
        stats = Stats(Path(tmp) / "stats.json")
        stats.record(25, "pomodoro")
        stats.record(25, "pomodoro")
        today = stats.today_summary()
        assert today["pomodoros"] == 2
        total = stats.total_summary()
        assert total["pomodoros"] == 2
        assert total["hours"] == 50 / 60.0
