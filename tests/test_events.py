import json
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

from core.events import EventRepository, CountdownEvent, COLOR_HEX


def test_add_and_list():
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "events.json"
        repo = EventRepository(path)
        ev = repo.add("Test", datetime(2026, 12, 1, 9, 0), "red")
        assert ev.name == "Test"
        assert ev.color == "red"
        assert len(repo.all(datetime.now())) == 1


def test_sorting():
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "events.json"
        repo = EventRepository(path)
        now = datetime(2026, 1, 1, 0, 0)
        repo.add("A", now + timedelta(days=1), "red")
        repo.add("B", now + timedelta(days=3), "blue")
        repo.add("C", now + timedelta(days=2), "green")
        names = [e.name for e in repo.all(now)]
        assert names == ["A", "C", "B"]


def test_past_events_at_end():
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "events.json"
        repo = EventRepository(path)
        now = datetime(2026, 1, 1, 0, 0)
        repo.add("Future", now + timedelta(days=1), "red")
        repo.add("Past", now - timedelta(days=1), "blue")
        names = [e.name for e in repo.all(now)]
        assert names == ["Future", "Past"]


def test_update():
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "events.json"
        repo = EventRepository(path)
        ev = repo.add("Old", datetime(2026, 12, 1), "red")
        repo.update(ev.id, "New", datetime(2026, 12, 2), "blue")
        updated = repo.get(ev.id)
        assert updated.name == "New"
        assert updated.color == "blue"


def test_remove():
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "events.json"
        repo = EventRepository(path)
        ev = repo.add("X", datetime(2026, 12, 1), "red")
        assert repo.remove(ev.id)
        assert not repo.remove(ev.id)
        assert len(repo.all(datetime.now())) == 0


def test_color_presets():
    assert "red" in COLOR_HEX
    assert "blue" in COLOR_HEX
    assert len(COLOR_HEX) == 8
