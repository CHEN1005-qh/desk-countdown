"""生成 3 个内置铃声到 resources/ringtones/（44.1kHz 16bit 单声道 wav）。

可重复执行（覆盖旧文件）。运行：python tools/gen_ringtones.py
"""
import math
import struct
import wave
from pathlib import Path

SR = 44100
OUT_DIR = Path(__file__).resolve().parent.parent / "resources" / "ringtones"


def _render(segments, amp=0.45):
    """segments: [(freq_hz, dur_sec, attack_sec, release_sec, wave_type)]
    freq=0 表示静音；wave_type: sine | square
    """
    samples = []
    for freq, dur, atk, rel, wtype in segments:
        n = int(SR * dur)
        na, nr = int(SR * atk), int(SR * rel)
        for i in range(n):
            if freq <= 0:
                samples.append(0.0)
                continue
            t = i / SR
            v = math.sin(2 * math.pi * freq * t)
            if wtype == "square":
                v = 0.62 if v >= 0 else -0.62
            env = 1.0
            if na > 0 and i < na:
                env = i / na
            if nr > 0 and i > n - nr:
                env = min(env, (n - i) / nr)
            samples.append(v * amp * env)
    return samples


def _write(path: Path, samples):
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(SR)
        frames = b"".join(
            struct.pack("<h", int(max(-1.0, min(1.0, s)) * 32767))
            for s in samples
        )
        f.writeframes(frames)


def main():
    # 1) 清脆短促：E6 → G6 → C7 三连上行短音
    _write(OUT_DIR / "default_1.wav", _render([
        (1318.51, 0.09, 0.004, 0.02, "sine"),
        (0,       0.05, 0, 0, "sine"),
        (1567.98, 0.09, 0.004, 0.02, "sine"),
        (0,       0.05, 0, 0, "sine"),
        (2093.00, 0.20, 0.004, 0.06, "sine"),
    ], amp=0.5))

    # 2) 轻柔长音：C5 / G5 缓起缓落的钟声
    _write(OUT_DIR / "default_2.wav", _render([
        (523.25, 0.75, 0.08, 0.25, "sine"),
        (0,      0.12, 0, 0, "sine"),
        (783.99, 0.85, 0.08, 0.30, "sine"),
    ], amp=0.38))

    # 3) 复古电子：方波琶音 E5-G5-B5-E6 × 2
    arp = [(659.26, 0.10, 0.006, 0.01, "square"),
           (783.99, 0.10, 0.006, 0.01, "square"),
           (987.77, 0.10, 0.006, 0.01, "square"),
           (1318.51, 0.12, 0.006, 0.02, "square")]
    _write(OUT_DIR / "default_3.wav", _render(
        arp + [(0, 0.08, 0, 0, "sine")] + arp, amp=0.34))

    print(f"已生成 3 个铃声 → {OUT_DIR}")


if __name__ == "__main__":
    main()
