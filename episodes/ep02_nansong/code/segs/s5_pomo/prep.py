# -*- coding: utf-8 -*-
"""S5 泼墨仙人 · 预处理（世界坐标 = PAB 原图像素；画页 [524,674,1158,2037]）
产出 work/：leaf.npy（原画页 RGB）、plate.npy（去墨纸底）、D.npy（墨密度）、Tline/Tbloom/Trec 到达时间、face 线编号。"""
import os, sys, json, math
import numpy as np, cv2
HERE = os.path.dirname(os.path.abspath(__file__))
EP = os.path.dirname(os.path.dirname(HERE))
WK = os.path.join(HERE, 'work'); os.makedirs(WK, exist_ok=True)
PAB = os.path.join(EP, 'assets/pomo/npm_pomo_PAB.jpg')
LX, LY, LW, LH = 524, 674, 1158, 2037

im = cv2.cvtColor(cv2.imread(PAB), cv2.COLOR_BGR2RGB)
leaf = im[LY:LY + LH, LX:LX + LW].astype(np.float32)
np.save(os.path.join(WK, 'leaf.npy'), leaf.astype(np.uint8))
H, W = leaf.shape[:2]
L = leaf.mean(2)

# ---- 纸色低频：人物区外 + 低墨像素，大尺度加权模糊（泼墨面积大，小尺度会把墨当纸） ----
ds = 4
Ls = cv2.resize(leaf, (W // ds, H // ds), interpolation=cv2.INTER_AREA)
lum = Ls.mean(2)
def _P(x, y): return ((x - LX) // ds, (y - LY) // ds)
fg = np.zeros(lum.shape, np.uint8)
cv2.fillPoly(fg, [np.int32([_P(x, y) for x, y in [(530, 980), (760, 960), (1080, 990), (1150, 965), (1440, 975), (1450, 1150),
    (1520, 1330), (1560, 1600), (1500, 2200), (1440, 2720), (600, 2720), (590, 2380), (600, 2180), (560, 1600), (528, 1300)]])], 1)
paper = np.broadcast_to(np.median(Ls[fg == 0], 0), Ls.shape).astype(np.float32).copy()
for it in range(5):
    pl = paper.mean(2)
    wgt = ((lum > pl - 5) & ((fg == 0) | (lum > pl - 3))).astype(np.float32) + 1e-5
    sig = 60 if it < 2 else 35
    paper = cv2.GaussianBlur(Ls * wgt[..., None], (0, 0), sig) / cv2.GaussianBlur(wgt, (0, 0), sig)[..., None]
paper_full = cv2.resize(paper, (W, H), interpolation=cv2.INTER_CUBIC)
eps = 1.0
logo = np.log(leaf + eps); logp = np.log(paper_full + eps)
D = np.clip((logp - logo).mean(2), 0, None)          # 墨密度（亮度对数差）
Ds = cv2.GaussianBlur(D, (0, 0), 1.2)
np.save(os.path.join(WK, 'D.npy'), Ds.astype(np.float16))

# ---- 去墨纸底：低频换成纸色，高频纹理在墨区压低 ----
low = cv2.GaussianBlur(logo, (0, 0), 3.0)
hp = logo - low
m = np.clip((cv2.GaussianBlur(Ds, (0, 0), 3) - 0.04) / 0.18, 0, 1)
m = cv2.dilate(m, np.ones((9, 9), np.uint8))
k = (1 - 0.95 * m)[..., None]
# 纸底纹理：墨区的高频里墨的笔触也在，只留 20%，另加一张真实空白纸的纹理平铺补足
plate = np.exp(logp + k * hp) - eps
# 取空白纸的高频纹理（全页中墨最少处）做补底
Tm = (cv2.GaussianBlur(Ds, (0, 0), 6) < 0.035).astype(np.uint8)
ys, xs = np.nonzero(Tm[200:-200, 100:-100])
rng = np.random.default_rng(3)
tex = np.zeros_like(hp); tw = np.zeros((H, W, 1), np.float32)
ps = 112
blank_hp = logo - cv2.GaussianBlur(logo, (0, 0), 14.0)
cands = [(y + 200, x + 100) for y, x in zip(ys[::997], xs[::997])]
cands = [(y, x) for y, x in cands if y + ps < H and x + ps < W and Tm[y:y + ps, x:x + ps].mean() > 0.9]
win1 = np.sin(np.linspace(0, np.pi, ps, dtype=np.float32)) ** 2
win = (win1[:, None] * win1[None, :])[..., None]
for yy in range(-ps // 2, H, ps // 2):
    for xx in range(-ps // 2, W, ps // 2):
        y, x = cands[int(rng.integers(len(cands)))]
        y0, x0 = max(yy, 0), max(xx, 0); y1, x1 = min(yy + ps, H), min(xx + ps, W)
        if y1 <= y0 or x1 <= x0: continue
        tex[y0:y1, x0:x1] += blank_hp[y + (y0 - yy):y + (y1 - yy), x + (x0 - xx):x + (x1 - xx)] * win[(y0 - yy):(y1 - yy), (x0 - xx):(x1 - xx)]
        tw[y0:y1, x0:x1] += win[(y0 - yy):(y1 - yy), (x0 - xx):(x1 - xx)] ** 2
tex = tex / np.sqrt(np.maximum(tw, 1e-3))
plate = np.exp(logp + k * hp + (1 - k) * (tex - cv2.GaussianBlur(tex, (0, 0), 3.0)) * 0.9 + (1 - k) * cv2.GaussianBlur(tex, (0, 0), 3.0) * 0.8) - eps
# 墨很淡处直接用原纸（保留原纸的斑驳），只在有墨处换成去墨纸底
m2 = np.clip((cv2.GaussianBlur(Ds, (0, 0), 4) - 0.05) / 0.17, 0, 1)[..., None]
m2 = m2 * m2 * (3 - 2 * m2)
plate = leaf * (1 - m2) + plate * m2
np.save(os.path.join(WK, 'plate.npy'), np.clip(plate, 0, 255).astype(np.uint8))

# ---- 人物区（去掉题诗、印、款）----
def P(x, y):
    return (x - LX, y - LY)
fig = np.zeros((H, W), np.uint8)
poly = np.int32([P(x, y) for x, y in [(530, 980), (760, 960), (1080, 990), (1150, 965), (1440, 975), (1450, 1150),
                                          (1520, 1330), (1560, 1600), (1500, 2200), (1440, 2720), (600, 2720), (590, 2380),
                                          (600, 2180), (560, 1600), (528, 1300)]])
cv2.fillPoly(fig, [poly], 1)
figm = cv2.GaussianBlur(fig.astype(np.float32), (0, 0), 14)
np.save(os.path.join(WK, 'fig.npy'), figm.astype(np.float16))

# ---- 细线 vs 泼墨：top-hat ----
Du8 = np.clip(Ds * 400, 0, 255).astype(np.uint8)
wash = cv2.morphologyEx(Du8, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15))).astype(np.float32) / 400
thin = np.clip(Ds - wash, 0, None)
face = np.zeros((H, W), np.uint8)
fpoly = np.int32([P(x, y) for x, y in [(1070, 1000), (1400, 990), (1440, 1150), (1420, 1360), (1300, 1420), (1150, 1420),
                                           (1080, 1330), (1050, 1150)]])
cv2.fillPoly(face, [fpoly], 1)
washn = cv2.dilate(wash, np.ones((9, 9), np.uint8))
lines = ((thin > 0.07) & (face > 0) & (washn < 0.22)).astype(np.uint8)
lines = cv2.morphologyEx(lines, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))
grp = cv2.dilate(lines, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (13, 13)))
n, lab, st, cen = cv2.connectedComponentsWithStats(grp, 8)
lab = lab * lines
comps = [i for i in range(1, n) if (lab == i).sum() >= 60]
# 顺序：自上而下（头轮廓 → 眉眼 → 鼻口 → 胡须），同高的从左到右
comps.sort(key=lambda i: (round(st[i, cv2.CC_STAT_TOP] / 40), st[i, cv2.CC_STAT_LEFT]))
print('face line comps', len(comps), [int(st[i, cv2.CC_STAT_AREA]) for i in comps])
t0, t1 = 235.3, 238.3
Tline = np.full((H, W), np.inf, np.float32)
lens = np.array([max(st[i, cv2.CC_STAT_WIDTH], st[i, cv2.CC_STAT_HEIGHT]) for i in comps], float)
durs = 0.22 + 0.5 * np.sqrt(lens / lens.max())
# 起点错开，允许重叠
starts = np.linspace(t0, t1 - durs[-1], len(comps)) if comps else []
info = []
for k_, (i, s0, d) in enumerate(zip(comps, starts, durs)):
    yy, xx = np.nonzero(lab == i)
    pts = np.stack([xx, yy], 1).astype(np.float32)
    mu = pts.mean(0); cv_ = np.cov((pts - mu).T)
    ev, evec = np.linalg.eigh(cv_); ax = evec[:, 1]
    if ax[0] < 0: ax = -ax                        # 横线从左到右；竖线从上到下
    if abs(ax[1]) > abs(ax[0]) and ax[1] < 0: ax = -ax
    u = (pts - mu) @ ax; u = (u - u.min()) / (np.ptp(u) + 1e-6)
    Tline[yy, xx] = s0 + d * u
    info.append(dict(i=int(i), start=float(s0), dur=float(d), bbox=[int(st[i, 0] + LX), int(st[i, 1] + LY), int(st[i, 2]), int(st[i, 3])]))
# 线的柔边：邻近像素取最近线像素的时间
known = np.isfinite(Tline)
dist, idx = cv2.distanceTransformWithLabels((~known).astype(np.uint8), cv2.DIST_L2, 5, labelType=cv2.DIST_LABEL_PIXEL)
ky, kx = np.nonzero(known)
lut = np.zeros(idx.max() + 1, np.float32); lut[idx[ky, kx]] = Tline[ky, kx]
Tnear = lut[idx]
near = (face > 0) & (dist <= 3)
Tline2 = np.where(near, Tnear, np.inf).astype(np.float32)
np.save(os.path.join(WK, 'Tline.npy'), Tline2)
json.dump(info, open(os.path.join(WK, 'face_lines.json'), 'w'), ensure_ascii=False, indent=1)

# ---- 泼墨洇开：几何距离（墨浓处走得快）+ 纸纤维各向异性噪声 ----
from skimage.graph import MCP_Geometric
ds2 = 2
Dw = cv2.resize(cv2.GaussianBlur(Ds, (0, 0), 3), (W // ds2, H // ds2), interpolation=cv2.INTER_AREA)
rng = np.random.default_rng(11)
def fibers(h, w, seed, sx, sy):
    r = np.random.default_rng(seed).standard_normal((h, w)).astype(np.float32)
    a = cv2.GaussianBlur(r, (0, 0), sigmaX=sx, sigmaY=sy)
    return (a - a.mean()) / (a.std() + 1e-6)
hh, ww = Dw.shape
fib = 0.9 * fibers(hh, ww, 3, 9, 9)
dn = np.clip(Dw / 0.45, 0, 1)
cost = 1.0 / (0.08 + dn) * np.exp(0.35 * fib)
CENTERS = [(847, 1341, 0.00), (1235, 1994, 0.35), (1083, 1737, 0.7), (1361, 1529, 1.0), (1174, 2363, 1.25),
           (835, 2006, 1.5), (1009, 2353, 1.75), (890, 1881, 1.95), (700, 1120, 0.45)]
T = np.full((hh, ww), np.inf, np.float32)
acc = []
for (cx, cy, dt) in CENTERS:
    m_ = MCP_Geometric(cost)
    c, _ = m_.find_costs([((cy - LY) // ds2, (cx - LX) // ds2)])
    acc.append((c.astype(np.float32), dt))
ink = (Dw > 0.06) & (cv2.resize(figm, (ww, hh)) > 0.5)
# 归一：让 92% 的墨在 4.2 s 内到
best = None
cs = np.stack([c for c, _ in acc]); dts = np.float32([d for _, d in acc])
for kk in np.linspace(0.002, 0.2, 200):
    Tk = (cs * kk + dts[:, None, None]).min(0)
    q = np.percentile(Tk[ink], 92)
    if q >= 4.2:
        best = kk; break
Tb = (cs * best + dts[:, None, None]).min(0)
print('bloom k', best, 'pctl', [round(float(np.percentile(Tb[ink], p)), 2) for p in (10, 50, 92, 99)])
Tb = cv2.resize(Tb, (W, H), interpolation=cv2.INTER_LINEAR)
# 纸纤维：直接用这张纸自己的细纹理（去墨纸底的高频），湿前沿顺着真实纤维走
_pl = np.log(plate.mean(2) + 1.0)
_hpf = _pl - cv2.GaussianBlur(_pl, (0, 0), 2.5)
_hpf = cv2.GaussianBlur(_hpf, (0, 0), 0.8)
fibF = _hpf / (_hpf.std() + 1e-6)
_mid = _pl - cv2.GaussianBlur(_pl, (0, 0), 12)
fibF = 0.7 * fibF + 0.8 * _mid / (_mid.std() + 1e-6)
Tb = Tb + 0.09 * fibF
Tbloom = np.minimum(239.0 + Tb, 243.6).astype(np.float32)
np.save(os.path.join(WK, 'Tbloom.npy'), Tbloom)

# ---- 退墨（全貌时，最淡的先退）----
rk = np.clip(Ds / 0.6, 0, 1)
Trec = (232.3 + 1.3 * rk ** 0.7 + 0.05 * fibF).astype(np.float32)
np.save(os.path.join(WK, 'Trec.npy'), Trec)

# 预览
def sv(name, a):
    cv2.imwrite(os.path.join(WK, name), cv2.cvtColor(np.clip(a, 0, 255).astype(np.uint8), cv2.COLOR_RGB2BGR))
sm = lambda a: cv2.resize(a, (W // 2, H // 2), interpolation=cv2.INTER_AREA)
sv('plate_prev.jpg', sm(plate))
sv('leaf_prev.jpg', sm(leaf))
tv = np.clip((Tbloom - 239) / 4.5, 0, 1) * 255
sv('tbloom_prev.jpg', sm(np.dstack([tv] * 3) * (Ds[..., None] > 0.06) * (figm[..., None] > 0.5)))
fx0, fy0 = P(1000, 960)
fc = plate[fy0:fy0 + 520, fx0:fx0 + 520].copy()
lm = np.isfinite(Tline2[fy0:fy0 + 520, fx0:fx0 + 520])
fc2 = leaf[fy0:fy0 + 520, fx0:fx0 + 520].copy(); fc2[lm] = fc2[lm] * 0.5 + np.float32([255, 0, 0]) * 0.5
sv('face_plate.jpg', np.concatenate([fc, fc2], 1))
