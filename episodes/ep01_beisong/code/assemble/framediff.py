"""逐帧平均绝对差（找跳变/闪）：python3 framediff.py clip.mp4 [t_offset]"""
import sys, subprocess, numpy as np
f = sys.argv[1]; off = float(sys.argv[2]) if len(sys.argv) > 2 else 0.0
W, H = 320, 180
p = subprocess.Popen(['ffmpeg', '-v', 'error', '-i', f, '-vf', f'scale={W}:{H},format=gray', '-f', 'rawvideo', '-'], stdout=subprocess.PIPE)
prev = None; d = []
while True:
    b = p.stdout.read(W * H)
    if len(b) < W * H: break
    x = np.frombuffer(b, np.uint8).astype(np.float32)
    if prev is not None: d.append(np.abs(x - prev).mean())
    prev = x
d = np.array(d); med = np.median(d)
print(f'frames {len(d)+1}  median diff {med:.2f}  max {d.max():.2f} @ {off + (d.argmax()+1)/30:.2f}s')
for i in np.argsort(-d)[:8]: print(f'  {off + (i+1)/30:7.2f}s  {d[i]:.2f}')
