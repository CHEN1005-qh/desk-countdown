"""设置管理：data/settings.json，深度合并默认值，写入原子化防损坏。"""
import copy
import json
import tempfile

from .paths import data_root

DEFAULTS = {
    "theme": "dark",                 # dark | light
    "always_on_top": True,
    "opacity": 0.95,                 # 0.40 ~ 1.00
    "window": {"x": None, "y": None, "w": 460, "h": 660, "maximized": False},
    "close_to_tray": True,
    "autostart": False,
    "ringtone": "default_1.wav",
    "volume": 80,                    # 0 ~ 100
    "ring_duration": "until_confirm",  # until_confirm | 15s
    "hover_boost": True,
    "timer": {"quick_minutes": [5, 10, 15, 25, 30, 45, 60], "default_minutes": 25},
    "pomodoro": {
        "focus": 25, "short_break": 5, "long_break": 15,
        "long_break_every": 4, "auto_start_next": True,
    },
}


def _merge(base: dict, override: dict) -> dict:
    out = copy.deepcopy(base)
    for k, v in (override or {}).items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _merge(out[k], v)
        else:
            out[k] = v
    return out


class Settings:
    """点路径读写：get("pomodoro.focus") / set("theme", "light")"""

    def __init__(self, path=None):
        self.path = path or (data_root() / "settings.json")
        try:
            with open(self.path, encoding="utf-8") as f:
                stored = json.load(f)
        except Exception:
            stored = {}
        self.data = _merge(DEFAULTS, stored)

    def get(self, dotted: str, default=None):
        cur = self.data
        for part in dotted.split("."):
            if not isinstance(cur, dict) or part not in cur:
                return default
            cur = cur[part]
        return cur

    def set(self, dotted: str, value, save: bool = True):
        parts = dotted.split(".")
        cur = self.data
        for p in parts[:-1]:
            cur = cur.setdefault(p, {})
        cur[parts[-1]] = value
        if save:
            self.save()

    def save(self):
        # 原子写：先写临时文件再替换，崩溃/强杀不会留下半截 JSON
        with tempfile.NamedTemporaryFile(
            "w", encoding="utf-8", dir=str(self.path.parent),
            delete=False, suffix=".tmp",
        ) as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)
            tmp = f.name
        import os
        os.replace(tmp, self.path)
