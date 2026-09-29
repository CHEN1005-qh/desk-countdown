from core.timer_engine import CountdownTimer, TimerState, format_seconds


def test_configure_and_remaining():
    timer = CountdownTimer(now_fn=lambda: 1000.0)
    timer.configure(60)
    assert timer.remaining() == 60.0
    assert timer.state == TimerState.IDLE


def test_start_and_progress():
    now = [1000.0]
    timer = CountdownTimer(now_fn=lambda: now[0])
    timer.configure(60)
    timer.start()
    assert timer.state == TimerState.RUNNING
    now[0] = 1030.0
    assert timer.remaining() == 30.0
    assert abs(timer.progress() - 0.5) < 0.01


def test_pause_and_resume():
    now = [1000.0]
    timer = CountdownTimer(now_fn=lambda: now[0])
    timer.configure(60)
    timer.start()
    now[0] = 1020.0
    timer.pause()
    assert timer.state == TimerState.PAUSED
    assert timer.remaining() == 40.0
    timer.start()
    now[0] = 1025.0
    assert timer.remaining() == 35.0


def test_finish():
    now = [1000.0]
    finished = [False]
    timer = CountdownTimer(now_fn=lambda: now[0])
    timer.finished.connect(lambda: finished.__setitem__(0, True))
    timer.configure(10)
    timer.start()
    now[0] = 1011.0
    timer.on_tick()
    assert timer.state == TimerState.FINISHED
    assert finished[0]


def test_format_seconds():
    assert format_seconds(65) == "01:05"
    assert format_seconds(3665) == "1:01:05"
    assert format_seconds(0) == "00:00"
