"""铃声管理：内置铃声（resources/ringtones）+ 用户导入（data/ringtones）。

wav 用 QSoundEffect 循环播放；mp3 用 QMediaPlayer（EndOfMedia 时重播实现循环）。
文件不存在时回退蜂鸣，绝不让程序因缺文件崩溃。
"""
import shutil
from dataclasses import dataclass
from pathlib import Path

from PyQt6.QtCore import QObject, QTimer, QUrl
from PyQt6.QtMultimedia import QAudioOutput, QMediaPlayer, QSoundEffect
from PyQt6.QtWidgets import QApplication

from .paths import data_root, resource_root

BUILTIN = ["default_1.wav", "default_2.wav", "default_3.wav"]
BUILTIN_LABEL = {
    "default_1.wav": "清脆短促（内置）",
    "default_2.wav": "轻柔长音（内置）",
    "default_3.wav": "复古电子（内置）",
}


@dataclass
class Ringtone:
    name: str      # 文件名（唯一标识）
    label: str     # 显示名
    path: Path
    builtin: bool


class RingtoneManager(QObject):
    def __init__(self, settings, parent=None):
        super().__init__(parent)
        self._settings = settings

        self._sfx = QSoundEffect(self)
        self._player = QMediaPlayer(self)
        self._output = QAudioOutput(self)
        self._player.setAudioOutput(self._output)
        self._player.mediaStatusChanged.connect(self._on_media_status)
        self._mp3_looping = False

        self._stop_timer = QTimer(self)          # 定时响铃（X 秒后自动停）
        self._stop_timer.setSingleShot(True)
        self._stop_timer.timeout.connect(self.stop)

    # ---- 列表与文件管理 ----
    def list(self) -> list[Ringtone]:
        out = []
        for name in BUILTIN:
            p = resource_root() / "ringtones" / name
            if p.exists():
                out.append(Ringtone(name, BUILTIN_LABEL[name], p, True))
        for p in sorted((data_root() / "ringtones").glob("*")):
            if p.suffix.lower() in (".wav", ".mp3"):
                out.append(Ringtone(p.name, f"{p.stem}（导入）", p, False))
        return out

    def _path_of(self, name: str) -> Path | None:
        p = data_root() / "ringtones" / name
        if p.exists():
            return p
        p = resource_root() / "ringtones" / name
        if p.exists():
            return p
        return None

    def import_file(self, src: str | Path) -> str | None:
        """复制音频到数据目录，返回新文件名；冲突自动改名。"""
        src = Path(src)
        if src.suffix.lower() not in (".wav", ".mp3"):
            return None
        dst_dir = data_root() / "ringtones"
        dst = dst_dir / src.name
        if dst.exists():
            dst = dst_dir / f"{src.stem}_{src.stat().st_mtime_ns % 100000}{src.suffix}"
        shutil.copy2(src, dst)
        return dst.name

    def remove(self, name: str) -> bool:
        """仅允许删除导入的铃声；若正被使用则回退默认。"""
        if name in BUILTIN:
            return False
        p = data_root() / "ringtones" / name
        if not p.exists():
            return False
        p.unlink()
        if self._settings.get("ringtone") == name:
            self._settings.set("ringtone", BUILTIN[0])
        return True

    # ---- 播放 ----
    def _volume(self) -> float:
        return max(0.0, min(1.0, self._settings.get("volume", 80) / 100.0))

    def _play(self, path: Path, loop: bool):
        self._stop_timer.stop()
        self._mp3_looping = False
        vol = self._volume()
        if path.suffix.lower() == ".wav":
            self._player.stop()
            # 同一源重播需要先清空再设置
            self._sfx.setSource(QUrl())
            self._sfx.setSource(QUrl.fromLocalFile(str(path)))
            self._sfx.setVolume(vol)
            self._sfx.setLoopCount(-1 if loop else 1)
            self._sfx.play()
        else:
            self._sfx.stop()
            self._player.setSource(QUrl.fromLocalFile(str(path)))
            self._output.setVolume(vol)
            self._mp3_looping = loop
            self._player.play()

    def _on_media_status(self, status):
        if (status == QMediaPlayer.MediaStatus.EndOfMedia
                and self._mp3_looping):
            self._player.setPosition(0)
            self._player.play()

    def ring(self, seconds: float | None = None):
        """提醒铃声。seconds=None 表示响到 stop()（用户确认）为止。"""
        name = self._settings.get("ringtone", BUILTIN[0])
        path = self._path_of(name) or self._path_of(BUILTIN[0])
        if path is None:
            QApplication.beep()   # 资源全丢时的最后兜底
            return
        self._play(path, loop=True)
        if seconds:
            self._stop_timer.start(int(seconds * 1000))

    def stop(self):
        self._stop_timer.stop()
        self._mp3_looping = False
        self._sfx.stop()
        self._player.stop()

    def preview(self, name: str):
        """设置页试听：单次播放。"""
        path = self._path_of(name)
        if path:
            self._play(path, loop=False)
