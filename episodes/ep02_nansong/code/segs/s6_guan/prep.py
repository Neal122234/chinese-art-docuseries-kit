# -*- coding: utf-8 -*-
"""S6 官窑瓶 · 预处理（世界坐标 = Met DP335586 原图像素）
1) 抠器物（grabCut + 羽化）；2) 展台：背景换成本集片尾同一块绢（seg_s7 的 silk.npy，映射使全貌时背景与 s7 首帧的绢完全重合，
   总装"全器淡为绢底"时只有器物在淡），保留原照器物下的接触阴影（比值法）；3) 开片裂纹遮罩（只取照片里真实的暗线：
   sato 脊线 + 滞后阈值 + 去小连通域，限釉面内）；4) 器身法线（回转体估计），供光扫用。
输出 work/：stage.npy（RGB，原点 STAGE_ORIGIN）、matte.npy（照片坐标 uint8）、crack.npy（照片坐标 uint8）、nrm.npy（照片坐标/2）。
用法：lockf -k $S/.heavy.lock python3 prep.py [stage|crack|all]"""
import os, sys, json, numpy as np, cv2
cv2.setNumThreads(1)
HERE = os.path.dirname(os.path.abspath(__file__))
EP = os.path.dirname(os.path.dirname(HERE))
S = os.path.dirname(EP)
sys.path.insert(0, os.path.join(S, 'lib'))
import engine as E

SRC = os.path.join(EP, 'assets/guanyao/met_DP335586.jpg')
SILK = os.path.join(EP, 'segs/bookends/work/silk.npy')       # 968×1720，s7 用 C0=(860,484,vh 880)
WK = os.path.join(HERE, 'work')
FULL = dict(cx=1757, cy=1990, vh=2800)
S7C = (860, 484, 880)
SILK_UNIT = FULL['vh'] / S7C[2]                             # 每绢像素 = 多少世界像素
SILK_ORIGIN = (FULL['cx'] - S7C[0] * SILK_UNIT, FULL['cy'] - S7C[1] * SILK_UNIT)
STAGE_ORIGIN = (-1000, 440)
STAGE_SIZE = (5500, 3100)
BOX = (640, 780, 2260, 3000)                                 # 开片计算范围（照片坐标）


def load():
    return cv2.cvtColor(cv2.imread(SRC), cv2.COLOR_BGR2RGB)


def matte(img):
    H, W = img.shape[:2]
    k = 3
    sm = cv2.resize(img, (W // k, H // k), interpolation=cv2.INTER_AREA)
    rgb = sm.astype(np.float32)
    chroma = (rgb[..., 1] + rgb[..., 2]) / 2 - rgb[..., 0]
    m = np.full(sm.shape[:2], cv2.GC_BGD, np.uint8)
    x0, y0, x1, y1 = 600 // k, 680 // k, 2300 // k, 3260 // k
    m[y0:y1, x0:x1] = cv2.GC_PR_BGD
    m[(chroma > 8) & (m == cv2.GC_PR_BGD)] = cv2.GC_PR_FGD
    m[(chroma > 14) & (m == cv2.GC_PR_FGD)] = cv2.GC_FGD
    m[760 // k:800 // k, 1200 // k:1800 // k] = cv2.GC_PR_FGD          # 口沿（米白，色度低）
    m[1100 // k:2900 // k, 1350 // k:1550 // k] = cv2.GC_FGD           # 器身中轴
    bgd = np.zeros((1, 65), np.float64); fgd = np.zeros((1, 65), np.float64)
    cv2.grabCut(cv2.cvtColor(sm, cv2.COLOR_RGB2BGR), m, None, bgd, fgd, 6, cv2.GC_INIT_WITH_MASK)
    fg = ((m == cv2.GC_FGD) | (m == cv2.GC_PR_FGD)).astype(np.uint8)
    n, lab, st, _ = cv2.connectedComponentsWithStats(fg)
    big = 1 + int(np.argmax(st[1:, cv2.CC_STAT_AREA]))
    fg = (lab == big).astype(np.uint8)
    ff = fg.copy(); cv2.floodFill(ff, None, (0, 0), 1); fg = fg | (1 - ff)
    fg = cv2.morphologyEx(fg, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
    fg = cv2.morphologyEx(fg, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))
    a = cv2.resize(fg.astype(np.float32), (W, H), interpolation=cv2.INTER_LINEAR)
    # 圈足区（y>2955）：grabCut 会把足旁的影子并进来，按实测的足边与足底弧线限定
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    # 足底 = 每列 3060–3250 内最暗的接触线（下沿 +4 px），沿 x 平滑
    Lf = cv2.GaussianBlur(img.astype(np.float32).mean(2), (0, 0), 2.0)
    xsm = np.arange(860, 2010)
    yb = np.array([3060 + int(np.argmin(Lf[3060:3250, x])) for x in xsm], np.float32) + 4
    from scipy.ndimage import median_filter
    yb = median_filter(yb, 61, mode='nearest')
    yb = cv2.GaussianBlur(yb.reshape(1, -1), (0, 0), 12).ravel()
    ybot = np.interp(xx, xsm, yb).astype(np.float32)
    xl = 890 - (yy - 2955) * 0.04; xr = 1984 - (yy - 2955) * 0.04
    foot = (yy <= 2955) | ((xx >= xl) & (xx <= xr) & (yy <= ybot))
    a = a * foot
    a = cv2.GaussianBlur(a, (0, 0), 2.2)
    return np.clip((a - 0.5) * 1.8 + 0.5, 0, 1)


def build_stage():
    img = load(); H, W = img.shape[:2]
    a = matte(img)
    np.save(os.path.join(WK, 'matte.npy'), (a * 255 + 0.5).astype(np.uint8))
    f = img.astype(np.float32)
    lum = f.mean(2)
    # 背景平滑模型（排除器物外扩一圈），比值 = 接触阴影
    k = 8
    bgm = (cv2.dilate((a > 0.02).astype(np.uint8), np.ones((61, 61), np.uint8)) == 0).astype(np.float32)
    ls = cv2.resize(lum * bgm, (W // k, H // k), interpolation=cv2.INTER_AREA)
    ms = cv2.resize(bgm, (W // k, H // k), interpolation=cv2.INTER_AREA)
    model = cv2.GaussianBlur(ls, (0, 0), 20) / np.maximum(cv2.GaussianBlur(ms, (0, 0), 20), 1e-4)
    model = cv2.resize(model, (W, H), interpolation=cv2.INTER_CUBIC)
    ratio = lum / np.maximum(model, 1)
    ratio = 1 + cv2.GaussianBlur(ratio - 1, (0, 0), 2.0)
    ratio = np.clip(ratio, 0.42, 1.0)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    dl = ((xx - 1430) / 1050) ** 2 + ((yy - 3170) / 230) ** 2          # 只留圈足下方的接触阴影
    ratio = 1 + (ratio - 1) * (1 - E.sstep(0.45, 1.0, dl))
    ratio = 1 + (ratio - 1) * 0.85
    # 绢：s7 同一块，按 SILK_UNIT/ORIGIN 映射到世界坐标（镜像外扩）
    silk = np.load(SILK).astype(np.float32)
    ox, oy = STAGE_ORIGIN; CW, CH = STAGE_SIZE
    xs = (np.arange(CW, dtype=np.float32) + ox - SILK_ORIGIN[0]) / SILK_UNIT - 0.5
    ys = (np.arange(CH, dtype=np.float32) + oy - SILK_ORIGIN[1]) / SILK_UNIT - 0.5
    mx, my = np.meshgrid(xs, ys)
    bg = cv2.remap(silk, mx, my, cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT_101)
    # 照片区域：器物原样；背景 = 绢 × 接触阴影
    py0, py1 = max(0, oy), min(H, oy + CH); px0, px1 = max(0, ox), min(W, ox + CW)
    reg = bg[py0 - oy:py1 - oy, px0 - ox:px1 - ox]
    aa = a[py0:py1, px0:px1, None]
    reg[:] = f[py0:py1, px0:px1] * aa + reg * ratio[py0:py1, px0:px1, None] * (1 - aa)
    out = np.clip(bg + 0.5, 0, 255).astype(np.uint8)
    np.save(os.path.join(WK, 'stage.npy'), out)
    cv2.imwrite(os.path.join(WK, 'stage_prev.jpg'), cv2.cvtColor(cv2.resize(out, (CW // 5, CH // 5), interpolation=cv2.INTER_AREA), cv2.COLOR_RGB2BGR))
    json.dump({'STAGE_ORIGIN': STAGE_ORIGIN, 'SILK_UNIT': SILK_UNIT, 'SILK_ORIGIN': SILK_ORIGIN}, open(os.path.join(WK, 'stage_meta.json'), 'w'))
    # 法线（回转体）：每行左右边界 → 轴心、半径；半径随高度的斜率给上下倾
    fg = a > 0.5
    rows = np.arange(H)
    xl = np.full(H, np.nan, np.float32); xr = np.full(H, np.nan, np.float32)
    for y in range(H):
        idx = np.flatnonzero(fg[y])
        if idx.size > 20:
            xl[y], xr[y] = idx[0], idx[-1]
    ok = ~np.isnan(xl)
    x0 = np.interp(rows, rows[ok], ((xl + xr) / 2)[ok]); r = np.interp(rows, rows[ok], ((xr - xl) / 2)[ok])
    x0 = cv2.GaussianBlur(x0.reshape(-1, 1).astype(np.float32), (1, 0), 25).ravel()
    r = cv2.GaussianBlur(r.reshape(-1, 1).astype(np.float32), (1, 0), 12).ravel()
    dr = np.gradient(r)
    h2 = H // 2; w2 = W // 2
    X = (np.arange(w2, dtype=np.float32) + 0.5) * 2
    Y = ((np.arange(h2) + 0.5) * 2).astype(int).clip(0, H - 1)
    nx = np.clip((X[None, :] - x0[Y][:, None]) / np.maximum(r[Y][:, None], 1), -0.995, 0.995)
    nz = np.sqrt(1 - nx ** 2)
    ang = np.arctan(np.clip(dr[Y], -3, 3))[:, None] * np.ones_like(nx)   # r 往下变大 → 法线朝上（y 分量为负）
    n = np.stack([nx * np.cos(ang), -np.sin(ang), nz * np.cos(ang)], -1)
    n = n / np.linalg.norm(n, axis=-1, keepdims=True)
    np.save(os.path.join(WK, 'nrm.npy'), n.astype(np.float16))
    np.save(os.path.join(WK, 'axis.npy'), np.stack([x0, r]).astype(np.float32))
    print('stage ok', out.shape, 'silk unit', SILK_UNIT, SILK_ORIGIN)


def build_crack():
    """开片遮罩：只取照片里真实的暗线。黑帽（小暗结构）→ 16 向细长线滤波，取"最大向 − 各向中位"（线有方向、
    斑点各向同性，所以铁斑被压掉）→ 按 MAD 标准化 → 滞后阈值连通 + 去小块 → 软 alpha。
    再做点亮顺序：骨架 → 去交叉点拆成一条条枝 → 每枝从光先到的一端沿线点亮（速度 V，随机迟 0–JIT 秒）。"""
    from skimage.filters import apply_hysteresis_threshold
    from skimage.morphology import skeletonize
    from scipy import ndimage as ndi
    img = load(); H, W = img.shape[:2]
    a = np.load(os.path.join(WK, 'matte.npy')).astype(np.float32) / 255
    inner = cv2.erode((a > 0.5).astype(np.uint8), np.ones((35, 35), np.uint8)).astype(np.float32)
    yy = np.arange(H)[:, None]
    inner *= ((yy > 835) & (yy < 2935)).astype(np.float32)
    bx0, by0, bx1, by1 = BOX
    f = img[by0:by1, bx0:bx1].astype(np.float32)
    Y = 0.2 * f[..., 0] + 0.4 * f[..., 1] + 0.4 * f[..., 2]
    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (11, 11))
    bh = cv2.morphologyEx(Y, cv2.MORPH_BLACKHAT, k)
    bh = bh / np.maximum(cv2.GaussianBlur(Y, (0, 0), 40), 30) * 150
    bh = np.minimum(bh, np.percentile(bh, 99.5))
    mx = None; stack = []
    for i in range(16):
        th = np.pi * i / 16
        gy, gx = np.mgrid[-18:19, -18:19].astype(np.float32)
        u = gx * np.cos(th) + gy * np.sin(th); v = -gx * np.sin(th) + gy * np.cos(th)
        ker = np.exp(-u ** 2 / (2 * 7.0 ** 2)) * np.exp(-v ** 2 / (2 * 1.3 ** 2)); ker /= ker.sum()
        stack.append(cv2.filter2D(bh, -1, ker))
    stack = np.stack(stack)
    r = stack.max(0) - np.median(stack, 0); del stack
    m = inner[by0:by1, bx0:bx1]
    v = r[m > 0.5]
    med = np.median(v); mad = np.median(np.abs(v - med)) * 1.48
    z = (r - med) / mad * m
    hy = apply_hysteresis_threshold(z, 1.8, 3.4)
    n, lab, st, _ = cv2.connectedComponentsWithStats(hy.astype(np.uint8), connectivity=8)
    wh = np.maximum(st[:, cv2.CC_STAT_WIDTH], st[:, cv2.CC_STAT_HEIGHT])
    keep = (st[:, cv2.CC_STAT_AREA] >= 60) & (wh >= 40); keep[0] = False
    km = keep[lab]
    # 铁斑（粗、各向同性）：开运算后还在的粗块 → 去掉
    blob = cv2.morphologyEx((z > 3.0).astype(np.uint8), cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9)))
    blob = cv2.dilate(blob, np.ones((9, 9), np.uint8)).astype(bool)
    km = km & ~blob
    alpha = E.sstep(1.8, 5.0, z) * km
    alpha = cv2.GaussianBlur(alpha.astype(np.float32), (0, 0), 0.7) * m
    full = np.zeros((H, W), np.uint8)
    full[by0:by1, bx0:bx1] = (np.clip(alpha, 0, 1) * 255 + 0.5).astype(np.uint8)
    np.save(os.path.join(WK, 'crack.tmp.npy'), full); os.replace(os.path.join(WK, 'crack.tmp.npy'), os.path.join(WK, 'crack.npy'))
    # ---- 点亮顺序
    sk = skeletonize(km)
    nb = cv2.filter2D(sk.astype(np.float32), -1, np.ones((3, 3), np.float32)) - sk
    junc = sk & (nb >= 3)
    br = sk & ~cv2.dilate(junc.astype(np.uint8), np.ones((3, 3), np.uint8)).astype(bool)
    nlab, blab = cv2.connectedComponents(br.astype(np.uint8), connectivity=8)
    ax = np.load(os.path.join(WK, 'axis.npy'))
    ys, xs = np.nonzero(br)
    gyy = ys + by0; gxx = xs + bx0
    nx = np.clip((gxx - ax[0][gyy]) / np.maximum(ax[1][gyy], 1), -1, 1)
    L = blab[ys, xs]
    rng = np.random.default_rng(7)
    # 每枝起点 = nx 最小（光从左来，先到）的点
    order = np.lexsort((nx, L))
    Ls = L[order]
    first = np.r_[True, Ls[1:] != Ls[:-1]]
    p0 = order[first]; labs = Ls[first]
    NX0b = np.zeros(nlab, np.float32); X0b = np.zeros(nlab, np.float32); Y0b = np.zeros(nlab, np.float32)
    NX0b[labs] = nx[p0]; X0b[labs] = xs[p0]; Y0b[labs] = ys[p0]
    JIT = rng.uniform(0, 0.7, nlab).astype(np.float32)
    V = 380.0
    # 每个遮罩像素 → 最近的枝像素
    dist, (iy, ix) = ndi.distance_transform_edt(~br, return_indices=True)
    bl = blab[iy, ix]
    yy2, xx2 = np.mgrid[0:by1 - by0, 0:bx1 - bx0]
    off = JIT[bl] + np.hypot(xx2 - X0b[bl], yy2 - Y0b[bl]) / V
    nx0 = NX0b[bl]
    ign = np.zeros((H, W, 2), np.float16)
    ign[by0:by1, bx0:bx1, 0] = nx0; ign[by0:by1, bx0:bx1, 1] = off
    np.save(os.path.join(WK, 'ignite.tmp.npy'), ign); os.replace(os.path.join(WK, 'ignite.tmp.npy'), os.path.join(WK, 'ignite.npy'))
    # 核对图：开片最清楚处 1:1，原图 | 叠色
    cx0, cy0 = 900, 2240
    c = img[cy0:cy0 + 680, cx0:cx0 + 1200].astype(np.float32)
    al = full[cy0:cy0 + 680, cx0:cx0 + 1200, None].astype(np.float32) / 255
    ov = c * (1 - al) + al * np.float32([255, 40, 20])
    cv2.imwrite(os.path.join(WK, 'crack_check.jpg'), cv2.cvtColor(np.vstack([c, ov]).astype(np.uint8), cv2.COLOR_RGB2BGR))
    small = cv2.resize(full, (W // 3, H // 3), interpolation=cv2.INTER_AREA)
    cv2.imwrite(os.path.join(WK, 'crack_prev.png'), 255 - small)
    print('crack ok', 'coverage', float((full > 64).mean()), 'branches', nlab)


if __name__ == '__main__':
    what = sys.argv[1] if len(sys.argv) > 1 else 'all'
    if what in ('stage', 'all'):
        build_stage()
    if what in ('crack', 'all'):
        build_crack()
