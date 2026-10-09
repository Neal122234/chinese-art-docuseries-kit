# -*- coding: utf-8 -*-
"""S0 片头第二版（落墨）轻量合成：不跑整段引擎，只重做 0–6.6 s 的题字，S1 夜宴部分原样保留。
- 绢底：取第一版 seg_s01 在 6.55 s 的纯绢帧（题字已收、夜宴未起，灯已全亮；镜头 0–7.2 s 静止，所以 0–6.6 s 每帧的绢底都是它）。
- 题字：按 seg_s01.py 的 fx 规格（brush「北宋」逐笔落墨 + ink 小字），用 inkfx 的同一套 alpha，乘法混合进绢底；灯亮曲线同 seg_s01.py。
- 6.6 s 起接第一版原帧（夜宴从绢里浮现起）。拼接点两边都是同一块纯绢，无跳变。
第一版原片读 _v1/segs/seg_s01.mp4（硬链接备份）；输出先写 work/，再 mv 覆盖 segs/seg_s01.mp4（mv 不动硬链接备份）。
1080 终版：seg_s01.py 已改成同样的 fx 规格，run.py --res 1080 整段重渲即可（引擎路径）。
用法：python3 s0_compose.py [--preview out.mp4]   （约 30 s，单核，<0.5 GB）"""
import os, sys, types, argparse, subprocess
import numpy as np, cv2
HERE = os.path.dirname(os.path.abspath(__file__))
SER = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(SER, 'lib')); sys.path.insert(0, HERE)
import engine as E
import inkfx
cv2.setNumThreads(1)

V1 = os.path.join(SER, '_v1', 'segs', 'seg_s01.mp4')
W, H, FPS, SPLICE = 1280, 720, 30, 198                     # 帧 198 = 6.6 s 起用原帧


def grab(t):
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-ss', f'{t:.4f}', '-i', V1, '-frames:v', '1', '-f', 'rawvideo',
                          '-pix_fmt', 'rgb24', '-'], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(H, W, 3)


def build_fx(plate):
    L = types.SimpleNamespace(lv=[plate], origin=np.array([0., 0.]), unit=1.0)
    R = types.SimpleNamespace(SS=1, H=H, W=W, cam=types.SimpleNamespace(rest_vh=H, rest_c=np.array([W / 2, H / 2])),
                              by_name={'silk': L})
    ns = {'__file__': os.path.join(HERE, 'seg_s01.py')}
    src = open(os.path.join(HERE, 'seg_s01.py'), encoding='utf-8').read()
    exec(src.replace("yeyan = np.memmap(YEYAN, np.uint8, 'r', shape=(3981, 16000, 3))", "yeyan = None"), ns)
    seg = ns['build']()
    tone = next(f for f in seg['fx'] if f['type'] == 'tone')['gain']
    objs = []
    for f in seg['fx']:
        if f['type'] == 'brush': objs.append(inkfx.Brush(dict(f), R))
        elif f['type'] == 'ink': objs.append(inkfx.Ink(dict(f), R))
    return tone, objs


def frame(plate_f, tone, objs, t):
    acc = plate_f * np.float32(E.curve(tone, t))
    for o in objs:
        A = o.alpha(t)
        if A is None or A.max() < 1e-3: continue
        h, w = A.shape
        M = np.float32([[1, 0, o.origin[0]], [0, 1, o.origin[1]]])      # 亚像素放置
        a = cv2.warpAffine(A.astype(np.float32), M, (W, H), flags=cv2.INTER_LINEAR, borderValue=0)
        acc *= (1 - a[..., None] * o.mul[None, None, :])
    return np.clip(acc * 255 + 0.5, 0, 255).astype(np.uint8)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--preview'); ap.add_argument('--out')
    a = ap.parse_args()
    plate = grab(6.55)
    plate_f = plate.astype(np.float32) / 255.0
    tone, objs = build_fx(plate)
    print(f'北宋 落墨 {objs[0].t0:.2f}–{objs[0].t0 + objs[0].total:.2f} s', flush=True)
    enc = ['-c:v', 'libx264', '-preset', 'medium', '-crf', '12', '-pix_fmt', 'yuv420p', '-threads', '2', '-movflags', '+faststart']
    if a.preview:                                             # 片头预览：0–9 s（含夜宴浮现）
        n1 = 270
    else:
        n1 = int(subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-count_packets', '-show_entries',
                                 'stream=nb_read_packets', '-of', 'csv=p=0', V1], capture_output=True, text=True).stdout)
    out = a.preview or a.out or os.path.join(HERE, 'work', 'seg_s01_v2.mp4')
    p = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS),
                          '-i', '-', *enc, out], stdin=subprocess.PIPE)
    for n in range(SPLICE):
        p.stdin.write(frame(plate_f, tone, objs, n / FPS).tobytes())
    dec = subprocess.Popen(['ffmpeg', '-v', 'error', '-i', V1, '-vf', f'select=gte(n\\,{SPLICE})', '-vsync', '0',
                            '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], stdout=subprocess.PIPE)
    n = SPLICE
    while n < n1:
        b = dec.stdout.read(W * H * 3)
        if len(b) < W * H * 3: break
        p.stdin.write(b); n += 1
    dec.kill(); p.stdin.close(); p.wait()
    print(f'done {out}  {n} 帧', flush=True)


if __name__ == '__main__':
    main()
