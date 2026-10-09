# 【工具包说明】成片/段运镜速度自检：逐帧相位相关求全局位移，报告超过"7 秒走完一屏"（1/7 画宽/秒）的时段。
# 输入：任意 mp4；输出：终端报告（超限时段、峰值 W/s）。依赖 ffmpeg、numpy、opencv。
# 跑法：python3 engine/tools/pan_speed_check.py 片子.mp4 [--limit 0.142857] [--fps 30]
"""成片运镜速度自检：逐帧相位相关求全局位移，报告超过 7 秒规则（1/7 画宽/秒）的段落。
用法（>1 分钟请 nohup 后台跑）：python3 pan_speed_check.py 片子.mp4 [--limit 0.142857] [--fps 30]
依据：series/research/visual_refs.md §3。转场/硬切会让个别帧虚高，报警段需人眼复核。"""
import argparse, subprocess, numpy as np, cv2

ap = argparse.ArgumentParser()
ap.add_argument('src'); ap.add_argument('--limit', type=float, default=1/7)
ap.add_argument('--fps', type=float, default=30.0); ap.add_argument('--min_run', type=float, default=0.2)
a = ap.parse_args()
W, H = 480, 270
p = subprocess.Popen(['ffmpeg', '-v', 'error', '-i', a.src, '-vf', f'scale={W}:{H},format=gray',
                      '-f', 'rawvideo', '-'], stdout=subprocess.PIPE)
win = cv2.createHanningWindow((W, H), cv2.CV_32F)
prev, v, ok, i = None, [], [], 0
while True:
    b = p.stdout.read(W * H)
    if len(b) < W * H: break
    f = np.frombuffer(b, np.uint8).reshape(H, W).astype(np.float32)
    if prev is not None:
        (dx, dy), r = cv2.phaseCorrelate(prev, f, win)
        v.append(np.hypot(dx, dy) * a.fps / W); ok.append(r > 0.1)
    prev = f; i += 1
v, ok = np.array(v), np.array(ok)
bad = ok & (v > a.limit)
print(f'frames {i}  duration {i / a.fps:.1f}s  over-limit {bad.sum() / a.fps:.1f}s ({100 * bad.mean():.0f}%)  '
      f'peak {v[ok].max():.2f} W/s  limit {a.limit:.3f} W/s ({a.limit * 1920 / a.fps:.1f} px/frame @1080p)')
st = None
for k in range(len(v) + 1):
    f = k < len(v) and bad[k]
    if f and st is None: st = k
    if not f and st is not None:
        if (k - st) / a.fps >= a.min_run:
            print(f'  WARN {st / a.fps:7.2f}-{k / a.fps:7.2f}s  peak {v[st:k].max():.2f} W/s')
        st = None
