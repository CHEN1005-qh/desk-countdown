"""倒计时桌面小工具 - 入口。"""
import faulthandler
import sys
import traceback
from datetime import datetime

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication

from ui.main_window import MainWindow
from ui.theme import ThemeManager
from core.settings import Settings
from core.paths import data_root

# 全局日志文件句柄，供异常钩子/faulthandler 使用（防止被 GC 关闭）
_LOG_FH = None


def _init_error_logging():
    """全局异常日志：Python 未捕获异常与 C++ 层崩溃栈都写入 data/error.log。

    打包为 console=False 后没有控制台输出，任何未捕获异常（含 Qt 槽内异常、
    段错误）都必须留痕，否则闪退无从排查。
    """
    global _LOG_FH
    try:
        _LOG_FH = open(data_root() / "error.log", "a", encoding="utf-8", buffering=1)
        _LOG_FH.write(f"\n[{datetime.now().isoformat()}] === 程序启动 ===\n")
        faulthandler.enable(file=_LOG_FH)   # 捕获 C++ 层崩溃（段错误/fail-fast）栈

        def hook(tp, val, tb):
            _LOG_FH.write(f"[{datetime.now().isoformat()}] 未捕获异常: {tp.__name__}: {val}\n")
            traceback.print_exception(tp, val, tb, file=_LOG_FH)
            _LOG_FH.flush()

        sys.excepthook = hook
    except Exception:
        pass   # 日志不可用时绝不影响主程序


def main():
    _init_error_logging()

    # 高 DPI
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)

    app = QApplication(sys.argv)
    app.setApplicationName("CountdownWidget")
    app.setOrganizationName("countdown-widget")

    settings = Settings()
    theme = ThemeManager(settings)
    theme.apply(app)

    win = MainWindow(app)
    win.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
