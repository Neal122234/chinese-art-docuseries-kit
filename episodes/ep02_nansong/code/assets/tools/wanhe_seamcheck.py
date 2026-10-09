# 自检：在每对瓦片的重叠区取 256×256 小块，把两块各自按最终映射渲出来，DoG 后做相位相关，统计残余错位
import cv2, numpy as np, json, os, re, itertools
src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'wanhe_stitch_render2.py')).read()
src = src.split('# 增益（1/8）')[0]            # 只取映射函数部分
ns = {'__file__': os.path.join(os.path.dirname(os.path.abspath(__file__)), 'wanhe_stitch_render2.py')}; exec(src, ns)
T, inv, weight, X0, Y0, IM, cor = ns['T'], ns['inv'], ns['weight'], ns['X0'], ns['Y0'], ns['IM'], ns['cor']
def patch(n, x, y, s=256):
    yy, xx = np.mgrid[y:y + s, x:x + s].astype(np.float32); px, py = inv(n, xx + X0, yy + Y0)
    img = cv2.remap(cv2.cvtColor(IM[n], cv2.COLOR_BGR2GRAY), px, py, cv2.INTER_CUBIC).astype(np.float32)
    return img, weight(px, py)
def dog(a): return cv2.GaussianBlur(a, (0, 0), 1.5) - cv2.GaussianBlur(a, (0, 0), 6)
res = []
for i, j in itertools.combinations(range(len(T)), 2):
    ci, cj = cor[i] - [X0, Y0], cor[j] - [X0, Y0]
    lo = np.maximum(ci.min(0), cj.min(0)) + 320; hi = np.minimum(ci.max(0), cj.max(0)) - 320 - 256
    if (hi - lo).min() < 0: continue
    for x in np.linspace(lo[0], hi[0], 4).astype(int):
        for y in np.linspace(lo[1], hi[1], 4).astype(int):
            a, wa = patch(i, x, y); b, wb = patch(j, x, y)
            if wa.min() < 0.01 or wb.min() < 0.01: continue
            da, db = dog(a), dog(b)
            if da.std() < 2: continue
            win = cv2.createHanningWindow((256, 256), cv2.CV_32F)
            (dx, dy), r = cv2.phaseCorrelate(da, db, win)
            res.append((T[i], T[j], x, y, dx, dy, r))
m = np.array([np.hypot(r[4], r[5]) for r in res]); rr = np.array([r[6] for r in res])
good = rr > 0.2
print('patches', len(res), 'confident', good.sum())
print('shift |d| px (confident): median %.2f  p90 %.2f  max %.2f' % (np.median(m[good]), np.percentile(m[good], 90), m[good].max()))
for r in sorted(res, key=lambda r: -np.hypot(r[4], r[5]))[:6]: print('worst', r[0], r[1], 'at', r[2], r[3], 'd=(%.2f,%.2f) resp %.2f' % (r[4], r[5], r[6]))
