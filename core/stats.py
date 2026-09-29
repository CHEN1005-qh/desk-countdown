"""专注统计：data/stats.json，按会话记录，按日聚合。"""
import json
import os
import tempfile
from datetime import date, datetime, timedelta
from pathlib import Path

from .paths import data_root


class Stats:
    def __init__(self, path: Path | None = None):
        self.path = path or (data_root() / "stats.json")
        try:
            with open(self.path, encoding="utf-8") as f:
                self.sessions = json.load(f).get("sessions", [])
        except Exception:
            self.sessions = []

    def _save(self):
        with tempfile.NamedTemporaryFile(
            "w", encoding="utf-8", dir=str(self.path.parent),
            delete=False, suffix=".tmp",
        ) as f:
            json.dump({"sessions": self.sessions}, f, ensure_ascii=False)
            tmp = f.name
        os.replace(tmp, self.path)

    def record(self, minutes: int, mode: str):
        """mode: pomodoro（计入番茄数） | timer（仅计专注分钟）"""
        self.sessions.append({
            "date": date.today().isoformat(),
            "minutes": int(minutes),
            "mode": mode,
            "completed_at": datetime.now().isoformat(),
        })
        self._save()

    def today(self) -> dict:
        today_str = date.today().isoformat()
        todays = [s for s in self.sessions if s["date"] == today_str]
        return {
            "count": sum(1 for s in todays if s["mode"] == "pomodoro"),
            "minutes": sum(s["minutes"] for s in todays),
        }

    def totals(self) -> dict:
        return {
            "count": sum(1 for s in self.sessions if s["mode"] == "pomodoro"),
            "minutes": sum(s["minutes"] for s in self.sessions),
        }

    def last7(self) -> list[tuple[str, int]]:
        """近 7 天（含今天）每天的专注分钟数，旧→新。"""
        out = []
        for i in range(6, -1, -1):
            d = (date.today() - timedelta(days=i)).isoformat()
            out.append((d, sum(
                s["minutes"] for s in self.sessions if s["date"] == d
            )))
        return out

    def today_summary(self) -> dict:
        t = self.today()
        return {"pomodoros": t["count"], "minutes": t["minutes"]}

    def total_summary(self) -> dict:
        t = self.totals()
        return {"pomodoros": t["count"], "hours": t["minutes"] / 60.0}

    def clear(self):
        self.sessions = []
        self._save()
