"""倒计时桌面小工具 - 入口。"""
import sys

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication

from ui.main_window import MainWindow
from ui.theme import ThemeManager
from core.settings import Settings


def main():
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
