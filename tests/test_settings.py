import tempfile
from pathlib import Path

from core.settings import Settings, DEFAULTS


def test_defaults():
    with tempfile.TemporaryDirectory() as tmp:
        s = Settings(Path(tmp) / "settings.json")
        assert s.get("theme") == "dark"
        assert s.get("always_on_top") is True
        assert s.get("pomodoro.focus") == 25


def test_set_and_get():
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "settings.json"
        s = Settings(path)
        s.set("theme", "light")
        assert s.get("theme") == "light"
        # 持久化验证
        s2 = Settings(path)
        assert s2.get("theme") == "light"


def test_nested_default():
    with tempfile.TemporaryDirectory() as tmp:
        s = Settings(Path(tmp) / "settings.json")
        assert s.get("window.w") == 460


def test_missing_key_returns_default():
    with tempfile.TemporaryDirectory() as tmp:
        s = Settings(Path(tmp) / "settings.json")
        assert s.get("nonexistent", "fallback") == "fallback"
