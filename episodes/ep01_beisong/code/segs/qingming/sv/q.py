# 低分辨率快速抽帧（不拿锁，轻量）：python3 sv/q.py RES SHOTS FRAMES
import sys, time, cv2
sys.argv, args = sys.argv[:1], sys.argv[1:]
sys.path.insert(0, '~/claude-projects/china-art/series/segs/qingming')
import s3
res = int(args[0]); only = args[1].split(','); fr = [int(x) for x in args[2].split(',')]
for k in list(s3.WIN):
    if k not in only: s3.WIN[k] = (-9, -9, -9, -9)
F = s3.Film(res, only=only)
for i in fr:
    t0 = time.time(); im = F.frame(i)
    cv2.imwrite(f'~/claude-projects/china-art/series/segs/qingming/sv/q_{i:04d}.jpg', cv2.cvtColor(im, cv2.COLOR_RGB2BGR), [cv2.IMWRITE_JPEG_QUALITY, 90])
    print(i, round(time.time() - t0, 2), flush=True)
