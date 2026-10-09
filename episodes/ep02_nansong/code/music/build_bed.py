#!/usr/bin/env python3
"""第二集配乐底 bed_ep02.wav：吴兆基《平沙落雁》整曲（雨果《吴门琴韵》上集第 2 首，1987 年录音）。

整曲从头到尾一刀不剪、不拼、不循环；只做：
  1. 30 Hz 二阶高通（去次声/桌面低频，琴最低弦约 65 Hz，影响 < 0.3 dB）
  2. 15603 Hz 窄陷波（录音里有一条恒定的行频啸叫，约 -93 dBFS，Q=100，带宽约 156 Hz）
  3. 44.1 -> 48 kHz 多相重采样（scipy resample_poly 160/147）
  4. 0-2.0 s 升余弦淡入；FADE_A-FADE_B 升余弦淡出（覆盖最后一音的余音尾巴，源文件到此结束）
  5. 补数字静音到 296.000 s（片长 4:56）
电平不动（整体约 -27.7 LUFS），交给总装按字幕区/呼吸段做增益。
用法（重计算，走全局锁）：lockf -k ../../.heavy.lock python3 build_bed.py
"""
import os, json, subprocess
import numpy as np
from scipy.signal import butter, sosfilt, iirnotch, tf2sos, resample_poly

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, 'src', 'WuZhaoji_Pingsha_Hugo1987_HRP712.flac')
OUT = os.path.join(HERE, 'bed_ep02.wav')
SR_IN, SR = 44100, 48000
DUR = 296.0
FADE_IN = 2.0
FADE_A, FADE_B = 290.8, None          # None = 源文件末尾（294.30 s）
NOTCH_F, NOTCH_Q = 15603.0, 100.0


def main():
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', SRC, '-f', 'f32le', '-acodec', 'pcm_f32le', '-'],
                         stdin=subprocess.DEVNULL, capture_output=True, check=True).stdout
    x = np.frombuffer(raw, np.float32).reshape(-1, 2).astype(np.float64)
    src_dur = len(x) / SR_IN
    x = sosfilt(butter(2, 30, 'hp', fs=SR_IN, output='sos'), x, axis=0)
    b, a = iirnotch(NOTCH_F, NOTCH_Q, fs=SR_IN)
    x = sosfilt(tf2sos(b, a), x, axis=0)
    y = resample_poly(x, 160, 147, axis=0)
    del x
    n_src = int(round(src_dur * SR)); y = y[:n_src]
    t = np.arange(len(y)) / SR
    g = np.ones(len(y))
    fi = t < FADE_IN
    g[fi] = 0.5 * (1 - np.cos(np.pi * t[fi] / FADE_IN))
    fb = FADE_B if FADE_B is not None else len(y) / SR
    fo = t >= FADE_A
    g[fo] = 0.5 * (1 + np.cos(np.pi * np.clip((t[fo] - FADE_A) / (fb - FADE_A), 0, 1)))
    y *= g[:, None]
    out = np.zeros((int(round(DUR * SR)), 2))
    out[:len(y)] = y
    peak = float(np.abs(out).max())
    assert peak < 0.999, peak
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'f32le', '-ar', str(SR), '-ac', '2', '-i', '-',
                    '-c:a', 'pcm_s24le', OUT], input=out.astype(np.float32).tobytes(), check=True)
    info = dict(src=SRC, src_dur=round(src_dur, 3), out=OUT, dur=DUR, sr=SR, fade_in=[0, FADE_IN],
                fade_out=[FADE_A, round(fb, 3)], pad_silence=[round(fb, 3), DUR], peak_dbfs=round(20 * np.log10(peak), 2),
                filters=['highpass 30 Hz 2nd-order', f'notch {NOTCH_F} Hz Q{NOTCH_Q}', 'resample_poly 160/147'])
    json.dump(info, open(os.path.join(HERE, 'work', 'bed_ep02_build.json'), 'w'), ensure_ascii=False, indent=1)
    print(json.dumps(info, ensure_ascii=False))


if __name__ == '__main__':
    main()
