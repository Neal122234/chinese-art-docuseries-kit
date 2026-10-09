# -*- coding: utf-8 -*-
"""v1 成片的雾带纹理纵向接缝修复：只重渲"画内雾带在屏幕上"的帧，其余帧从 v1 成片解码照搬，一次编码输出。
（修复本身在 seg_s2.py 的 seamless_tall/fix_fog_bands；雾带不在屏上的帧，新旧渲染逐像素相同。）
  nohup lockf -k $S/.heavy.lock python3 patch_fog_seam.py > patch.log 2>&1 &
"""
import sys, os, math, time, subprocess
import numpy as np, cv2
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import seg_s2 as S
E = S.E

OLD = os.path.join(HERE, 'seg_s2_v1_seam.mp4')          # v1 成片（备份）
OUT_TMP = os.path.join(HERE, 'seg_s2_v2_tmp.mp4')
OUT = os.path.join(S.S, 'segs', 'seg_s2.mp4')
REV = os.path.join(HERE, 'review')


def band_frames(M):
    redo = set()
    for i in range(M.nframes):
        t = i / M.fps
        for n, k in M.weights(t).items():
            R = M.R[n]
            for fx in R.fx:
                if not (isinstance(fx, E.Fog) and fx.mode == 'world' and fx.active(t)):
                    continue
                if E.curve(fx.spec.get('opacity', 0.5), t) <= 0:
                    continue
                rise = fx.rise[0] * math.sin(2 * math.pi * t / fx.rise[1]) if fx.rise[0] else 0.0
                s, c = R.layer_xf(t, fx.par, fx.zpar)
                x0, y0, x1, y1 = fx.band
                ya = R.H / 2 + s * (y0 + rise - c[1]); yb = R.H / 2 + s * (y1 + rise - c[1])
                xa = R.W / 2 + s * (x0 - c[0]); xb = R.W / 2 + s * (x1 - c[0])
                if yb > -4 and ya < R.H + 4 and xb > -4 and xa < R.W + 4:
                    redo.add(i)
    grown = set()
    for i in redo:
        grown.update(range(max(0, i - 3), min(M.nframes, i + 4)))
    return sorted(grown)


def ranges(idx):
    out = []
    for i in idx:
        if out and i == out[-1][1]:
            out[-1][1] = i + 1
        else:
            out.append([i, i + 1])
    return out


def main():
    M = S.Multi(S.build(), 720)
    M.check()
    redo = band_frames(M)
    E.log(f'重渲 {len(redo)} 帧，区间 {ranges(redo)}')
    # 先出复核静帧（接缝原先最明显的时刻 + 全貌）
    for i in (30, 1050, 1080, 1110, 2400):
        fr = M.render(i / M.fps)
        cv2.imwrite(os.path.join(REV, f'v2_f{i:04d}.png'), cv2.cvtColor(fr, cv2.COLOR_RGB2BGR))
        E.log(f'still {i}')
    W, H = M.W, M.H
    dec = subprocess.Popen(['ffmpeg', '-v', 'error', '-i', OLD, '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'],
                           stdout=subprocess.PIPE)
    enc = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}',
                            '-r', f'{M.fps:g}', '-i', '-', '-c:v', 'libx264', '-preset', 'medium', '-crf', '12',
                            '-pix_fmt', 'yuv420p', '-movflags', '+faststart', OUT_TMP], stdin=subprocess.PIPE)
    rs = set(redo); tr = time.time(); nb = W * H * 3
    for i in range(M.nframes):
        b = dec.stdout.read(nb)
        if len(b) < nb:
            raise SystemExit(f'旧片帧数不足：{i}')
        if i in rs:
            b = M.render(i / M.fps).tobytes()
        enc.stdin.write(b)
        if i % 60 == 0:
            E.log(f'frame {i}/{M.nframes}  {time.time() - tr:.0f}s')
    enc.stdin.close(); enc.wait(); dec.wait()
    os.replace(OUT_TMP, OUT)
    E.log(f'完成 {OUT}')


if __name__ == '__main__':
    main()
