"""路径管理：区分开发环境与 PyInstaller 打包环境。

- app_root()      程序根目录（打包后为 exe 所在目录，数据存这里 → 便携语义）
- resource_root() 资源目录（打包后解压在 _MEIPASS，开发时为项目 resources/）
- data_root()     用户数据目录 app_root()/data/
"""
import sys
from pathlib import Path


def _is_frozen() -> bool:
    return getattr(sys, "frozen", False)


def app_root() -> Path:
    if _is_frozen():
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


def resource_root() -> Path:
    if _is_frozen():
        return Path(getattr(sys, "_MEIPASS", ""))
    return Path(__file__).resolve().parent.parent / "resources"


def data_root() -> Path:
    d = app_root() / "data"
    d.mkdir(parents=True, exist_ok=True)
    (d / "ringtones").mkdir(exist_ok=True)
    return d
