"""事件仓库：多目标日期倒计时事件的增删改查与排序（data/events.json）。"""
import json
import os
import tempfile
import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from .paths import data_root

# 8 种预设颜色（Radix 色板，深浅主题下均可读）
COLOR_PRESETS = [
    ("red", "#E5484D"), ("orange", "#F76B15"), ("yellow", "#FFB224"),
    ("green", "#30A46C"), ("cyan", "#00A2C7"), ("blue", "#0091FF"),
    ("purple", "#8E4EC6"), ("pink", "#D6409F"),
]
COLOR_HEX = dict(COLOR_PRESETS)


@dataclass
class CountdownEvent:
    id: str
    name: str
    target: datetime
    color: str
    created_at: datetime

    def remaining(self, now: datetime):
        return self.target - now

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "target": self.target.isoformat(),
            "color": self.color,
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, d: dict) -> "CountdownEvent":
        return cls(
            id=d["id"],
            name=d["name"],
            target=datetime.fromisoformat(d["target"]),
            color=d.get("color", "blue"),
            created_at=datetime.fromisoformat(d.get("created_at", d["target"])),
        )


class EventRepository:
    def __init__(self, path: Path | None = None):
        self.path = path or (data_root() / "events.json")
        self._events: list[CountdownEvent] = []
        self._load()

    def _load(self):
        try:
            with open(self.path, encoding="utf-8") as f:
                self._events = [CountdownEvent.from_dict(d) for d in json.load(f).get("events", [])]
        except Exception:
            self._events = []

    def _save(self):
        with tempfile.NamedTemporaryFile(
            "w", encoding="utf-8", dir=str(self.path.parent),
            delete=False, suffix=".tmp",
        ) as f:
            json.dump({"events": [e.to_dict() for e in self._events]},
                      f, ensure_ascii=False, indent=2)
            tmp = f.name
        os.replace(tmp, self.path)

    def all(self, now: datetime) -> list[CountdownEvent]:
        """未到期按剩余时间升序在前；已到期排最后（刚过期的在前）。"""
        future = sorted(
            (e for e in self._events if e.remaining(now).total_seconds() > 0),
            key=lambda e: e.remaining(now),
        )
        past = sorted(
            (e for e in self._events if e.remaining(now).total_seconds() <= 0),
            key=lambda e: e.remaining(now), reverse=True,
        )
        return future + past

    def add(self, name: str, target: datetime, color: str) -> CountdownEvent:
        ev = CountdownEvent(
            id=uuid.uuid4().hex[:12],
            name=name.strip()[:30],
            target=target,
            color=color if color in COLOR_HEX else "blue",
            created_at=datetime.now(),
        )
        self._events.append(ev)
        self._save()
        return ev

    def update(self, ev_id: str, name: str, target: datetime, color: str):
        for e in self._events:
            if e.id == ev_id:
                e.name = name.strip()[:30]
                e.target = target
                e.color = color if color in COLOR_HEX else e.color
                self._save()
                return e
        return None

    def remove(self, ev_id: str) -> bool:
        before = len(self._events)
        self._events = [e for e in self._events if e.id != ev_id]
        changed = len(self._events) < before
        if changed:
            self._save()
        return changed

    def get(self, ev_id: str):
        return next((e for e in self._events if e.id == ev_id), None)
