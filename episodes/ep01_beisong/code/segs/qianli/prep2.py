# -*- coding: utf-8 -*-
# 千里江山 S4 第二版素材：
#  1 q_ds3p.npy   ds3 区段，x 84000–86400 用补过船洞的全分辨率块缩小替换（小舟可以真的走）
#  2 depth12.npy  平远展卷的纵深图（世界 unit 12）：远岸线以上（远山、天）=0，水面向近处 0→1，卷下缘以下 =1
#  3 zr_*.npy     "一层层罩染"世界图（unit 2）：山体遮罩、矿色遮罩、自上而下/自下而上的晕染到达时间
#  4 fl_*.npy     结尾石青漫开：到石青的距离（unit 2）
import numpy as np, cv2
D = '~/claude-projects/china-art/series/segs/qianli/data/'
W0, H0 = 153767, 6110
rng = np.random.default_rng(7)

def sstep(a, b, x):
    u = np.clip((x - a) / (b - a), 0, 1); return u * u * (3 - 2 * u)

def fbm(h, w, sig):
    n = np.zeros((h, w), np.float32)
    for s, a in sig:
        r = cv2.GaussianBlur(rng.standard_normal((h, w)).astype(np.float32), (0, 0), s)
        n += a * r / (r.std() + 1e-6)
    return n

# ---- 1 ds3 补船洞 ----
ds3 = np.load(D + 'q_ds3.npy')
full = np.load(D + 'q_full.npy', mmap_mode='r')
j0 = (84000 - 78000) // 3
sm = cv2.resize(np.ascontiguousarray(full), (800, 2036), interpolation=cv2.INTER_AREA)
ds3[:, j0:j0 + 800] = sm
np.save(D + 'q_ds3p.npy', ds3)

# ---- 2 纵深图 ----
m = np.load(D + 'wmask_ds3_full.npy').astype(np.float32)      # origin (78000,3900) unit 3
def zero(x0, y0, x1, y1):
    m[max(0, (y0 - 3900) // 3):max(0, (y1 - 3900) // 3), (x0 - 78000) // 3:(x1 - 78000) // 3] = 0
zero(90000, 3900, 108000, 4300); zero(93600, 3900, 97200, 4500); zero(100000, 3900, 102400, 5300)
mb = cv2.GaussianBlur(m, (0, 0), 2) > 0.5
rows = np.where(mb.any(0), mb.argmax(0), mb.shape[0])          # 每列第一行水
ys = 3900 + 3 * rows.astype(np.float32)
from scipy.ndimage import median_filter
ys = median_filter(ys, 41, mode='nearest')
ys = cv2.GaussianBlur(ys[None, :], (0, 0), 6)[0]
ys = np.minimum(ys, H0 - 200)
# 世界 unit 12 网格：x 66000–120000, y -6000–12000
U = 12; X0, X1, Y0, Y1 = 66000, 120000, -6000, 12000
xs = X0 + (np.arange((X1 - X0) // U) + 0.5) * U; yy = Y0 + (np.arange((Y1 - Y0) // U) + 0.5) * U
ysx = np.interp(xs, 78000 + (np.arange(ys.size) + 0.5) * 3, ys)
Dm = np.clip((yy[:, None] - ysx[None, :]) / (H0 - ysx[None, :]), 0, 1) ** 0.85
Dm = cv2.GaussianBlur(Dm.astype(np.float32), (0, 0), 3)
np.save(D + 'depth12.npy', Dm)
print('depth', Dm.shape, 'shore y range', ys.min(), ys.max())

# ---- 3 罩染 unit 2：世界 x 83600–86400, y 1800–4400 ----
RX0, RY0, RU = 83600, 1800, 2
RW, RH = (86400 - RX0) // RU, (4400 - RY0) // RU
comp = np.zeros((RH, RW, 3), np.uint8)
a3 = ds3[(RY0) // 3:(4400) // 3 + 1, (RX0 - 78000) // 3:(86400 - 78000) // 3 + 1]
comp[:] = cv2.resize(a3, (RW, RH), interpolation=cv2.INTER_LINEAR)
fr = cv2.resize(np.ascontiguousarray(full[RY0:4400]), (2400 // 2, (4400 - RY0) // 2), interpolation=cv2.INTER_AREA)
comp[:, (84000 - RX0) // 2:] = fr
f = cv2.GaussianBlur(comp.astype(np.float32), (0, 0), 1.5)
R, G, B = f[..., 0], f[..., 1], f[..., 2]
sky = np.median(f[:120].reshape(-1, 3), 0)
dist = np.sqrt(((f - sky) ** 2).sum(-1))
M = sstep(16, 34, cv2.GaussianBlur(dist, (0, 0), 3))
M = cv2.GaussianBlur(M, (0, 0), 3)
blue = sstep(8, 40, B - R) * sstep(-25, 5, B - G)
green = sstep(4, 28, G - R) * (1 - blue)
Mg = cv2.GaussianBlur(np.clip(blue + green, 0, 1), (0, 0), 2.5)
Mb = cv2.GaussianBlur(blue, (0, 0), 2.5)
mm = Mg > 0.45
mm[:60] = False
ridge = np.where(mm.any(0), mm.argmax(0), RH).astype(np.float32)
ridge = median_filter(ridge, 15, mode='nearest'); ridge = cv2.GaussianBlur(ridge[None], (0, 0), 6)[0]
Y = np.arange(RH, dtype=np.float32)[:, None]
below = np.clip((Y - ridge[None, :]) / 420.0, 0, 1.6)                       # 顺山形：离本列山脊线越远越晚
summit = (ridge[None, :] - ridge.min()) / max(1.0, float(np.percentile(ridge, 60) - ridge.min()))
Ttop = 0.70 * below + 0.30 * np.clip(summit, 0, 1.5) + 0.07 * fbm(RH, RW, [(18, 1.0), (5, 0.4)])
Ttop = cv2.GaussianBlur(Ttop.astype(np.float32), (0, 0), 2)
Tbot = 1.0 - Y / RH + 0.035 * fbm(RH, RW, [(70, 1.0), (20, 0.3)])
Tbot = cv2.GaussianBlur(Tbot.astype(np.float32), (0, 0), 2)
zr = np.stack([M, Mg, Mb, Ttop, Tbot], -1).astype(np.float32)
np.save(D + 'zr_maps.npy', zr)
np.save(D + 'zr_meta.npy', np.array([RX0, RY0, RU], np.float64))
np.save(D + 'zr_sky.npy', sky.astype(np.float32))
vis = np.concatenate([comp, (np.stack([Mg] * 3, -1) * 255).astype(np.uint8), (np.stack([np.clip(Ttop, 0, 1)] * 3, -1) * 255).astype(np.uint8)], 1)
cv2.imwrite(D + 'zr_vis.jpg', cv2.cvtColor(cv2.resize(vis, (vis.shape[1] // 3, vis.shape[0] // 3)), cv2.COLOR_RGB2BGR))
print('zr', zr.shape, 'sky', sky)

# ---- 4 石青漫开：unit 2，世界 x 84200–86000, y 1900–3400（全分辨率 → unit 2）----
FX0, FY0, FU = 84200, 1900, 2
ff = cv2.resize(np.ascontiguousarray(full[FY0:3400, FX0 - 84000:86000 - 84000]), (900, 750), interpolation=cv2.INTER_AREA).astype(np.float32)
fb = cv2.GaussianBlur(ff, (0, 0), 3)
bl = (sstep(10, 40, fb[..., 2] - fb[..., 0]) > 0.5).astype(np.uint8)
bl = cv2.morphologyEx(bl, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
dt = cv2.distanceTransform(1 - bl, cv2.DIST_L2, 5).astype(np.float32) * FU    # 世界像素
dt = dt + 45 * fbm(750, 900, [(14, 1.0), (4, 0.35)])
bb = ff[..., 2] - ff[..., 0]
az = np.median(ff[bb > np.percentile(bb, 99)], 0)
np.save(D + 'fl_dist.npy', cv2.GaussianBlur(dt, (0, 0), 1.5).astype(np.float32))
np.save(D + 'fl_meta.npy', np.array([FX0, FY0, FU], np.float64))
np.save(D + 'fl_az.npy', az.astype(np.float32))
print('flood az', az, 'blue frac', bl.mean())
