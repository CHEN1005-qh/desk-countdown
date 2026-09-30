"""番茄钟结束瞬间的崩溃回归复现脚本。

真实 Qt 事件循环 + 压缩时钟：在 phase_finished 信号触发的同一时刻执行
主窗口 _on_phase_finished 中的响铃+弹窗逻辑。历史 bug 为 ringtone._play
向 setLoopCount 传入 QSoundEffect.Loop.Infinite 枚举导致 TypeError，
槽内未捕获异常经 PyQt6 qFatal 直接闪退。本脚本用于回归验证。

运行：python tools/repro_pomodoro_crash.py   （期望退出码 0，无 traceback）
"""
import os
import sys
import time

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt6.QtCore import QObject, QTimer, pyqtSignal
from PyQt6.QtWidgets import QApplication, QWidget

from core.settings import Settings
from core.ringtone import RingtoneManager
from ui.reminder_popup import ReminderPopup


class Bridge(QObject):
    finished = pyqtSignal(str)


def main():
    app = QApplication(sys.argv)
    settings = Settings()
    ringtone = RingtoneManager(settings)

    win = QWidget()
    win.resize(400, 300)
    win.show()

    bridge = Bridge()

    def on_phase_finished(phase: str):
        # 复制主窗口 _on_phase_finished 的 focus 分支
        if settings.get("ring_duration", "until_confirm") == "15s":
            ringtone.ring(15)
        else:
            ringtone.ring()
        ReminderPopup.show(
            win, "专注完成", "专注阶段结束，休息一下吧！",
            [("知道了", "dismiss"), ("开始休息", "next")],
        )
        ringtone.stop()

    bridge.finished.connect(on_phase_finished)

    def drive():
        # 弹窗阻塞期间自动关闭，模拟用户点击"知道了"
        QTimer.singleShot(300, auto_close_popup)
        bridge.finished.emit("focus")

    def auto_close_popup():
        for w in QApplication.topLevelWidgets():
            if isinstance(w, ReminderPopup):
                w._on_click("dismiss")
                return

    QTimer.singleShot(200, drive)
    QTimer.singleShot(2000, app.quit)

    code = app.exec()
    print(f"退出码={code}（0 表示无崩溃）")
    return 0 if code == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
