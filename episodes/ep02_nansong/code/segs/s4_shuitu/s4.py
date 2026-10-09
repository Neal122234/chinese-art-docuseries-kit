# -*- coding: utf-8 -*-
"""第二集 S4 马远《水图》卷 · 第二版（全局 166–222，56 s，帧 0 = 166.0）。第一版代码存 s4_v1.py。
 0–7     洞庭风细水纹铺满屏，线在流（最慢）；另出水纹线遮罩（供 s3 涟漪转场）
 7–13    从这段水纹里拉出（scrollview 反向俯冲）→ 长案上一整卷；暖光沿卷走；展签（在卷外暗处）
 13–13.4 全貌停（极慢环移）
 13.4–14 干净叠化进第一段
 14–38   十二段按卷序逐段：每段整段铺满画面高度（全段可见，左右邻段压暗），静止 1.6 s + 0.4 s 干净叠化；
         段左侧竖排小字标段名（第一段「殘段」，其余与杨皇后原题同字）。展示时不推拉、不平移、不加水流
 37.6–38 叠化回「黄河逆流」整段
 38–45   黄河逆流：线的浓淡顺流涌动渐起；缓推向题名一侧，柔光落在「黃河逆流」四字上（停留）
 45–50.5 从题名移到浪头最密处
 50.5–56 黄河逆流近景，浪越涌越急（镜头极慢推）
世界坐标 = 全卷原图像素（127821×3400）。
用法: python3 s4.py prep | python3 s4.py OUT.mp4 [--stills 0,300] [--frames a:b] [--mask M.mp4] [--speed]"""
import sys, os, math, json, time, argparse, subprocess
import numpy as np, cv2

S = '~/claude-projects/china-art/series/'
sys.path.insert(0, S + 'lib')
import engine as E
import scrollview as SV

EP = S + 'ep02_nansong/'
AS = EP + 'assets/shuitu/'
HERE = EP + 'segs/s4_shuitu/'
DATA = HERE + 'data/'
os.makedirs(DATA, exist_ok=True)
W0, H0 = 127821, 3400
FPS = 30
DUR = 56.0
FOV = 38.0
SECS = {s['order']: s for s in json.load(open(AS + 'sections_auto.json'))}

# ------------------------------------------------------------ v2 时间表（本段秒）
T_PULL0, T_PULL1 = 7.0, 13.0          # 拉出（反向俯冲）
T_XOV = 13.4                           # 全貌 → 第一段叠化开始
T_SEG0, SEG_T, SEG_X = 14.0, 2.0, 0.4  # 十二段：每段 2.0 s = 静 1.6 + 叠化 0.4
T_FOCUS = T_SEG0 + 12 * SEG_T          # 38.0 回到黄河逆流
SEG_NAME = {k: (SECS[k]['name'] if k > 1 else '殘段') for k in SECS}
DIM = 0.30                             # 逐段展示时左右邻段的亮度


def seg_frame(k):
    """第 k 段整段铺满画面高度（上下各收 10 px 磨损绢边），水平居中。"""
    s = SECS[k]
    return dict(cx=(s['x0'] + s['x1']) / 2.0, cy=(s['y0'] + s['y1']) / 2.0, vh=float(s['y1'] - s['y0'] - 20))


F6 = seg_frame(6)
T_TT = dict(cx=86560, cy=1430, vh=2150)            # 题名在左上、巨浪在右（不出本段）
T_WAVE = dict(cx=87580, cy=2330, vh=1650)          # 浪头最密的一带
T_END = dict(cx=87750, cy=2370, vh=1350)
FOCUS_KEYS = [dict(t=T_FOCUS, **F6), dict(t=T_FOCUS + 1.0, **F6), dict(t=45.0, ease=1.0, **T_TT),
              dict(t=50.5, ease=1.2, **T_WAVE), dict(t=56.0, ease=1.5, **T_END)]


def sstep(a, b, x):
    x = np.clip((np.asarray(x, np.float32) - a) / (b - a), 0, 1)
    return x * x * (3 - 2 * x)


def full():
    return np.memmap(AS + 'shuitu_full_127821x3400.rgb', np.uint8, 'r', shape=(H0, W0, 3))


# ------------------------------------------------------------ 各段水性（世界像素/秒）
# dir: 该段整体流向；P: 双相位周期；lam/A: 沿流向走的"墨涌"带（墨色浓淡随之起伏）
SEC = {
    1: dict(dir=(-1, 0), v=50, P=90, lam=600, A=0.40),
    2: dict(dir=(-1, 0), v=26, P=70, lam=520, A=0.48),      # 洞庭风细：最慢
    3: dict(dir=(1, 0), v=95, P=120, lam=700, A=0.52),      # 层波叠浪：由左向右推涌
    4: dict(dir=(-1, 0), v=55, P=110, lam=800, A=0.42),     # 寒塘清浅
    5: dict(dir=(-1, 0), v=140, P=140, lam=900, A=0.50),    # 长江万顷
    6: dict(dir=(0.94, -0.34), v=150, P=130, lam=800, A=0.55),  # 黄河逆流：最急
    7: dict(dir=(0.98, -0.17), v=70, P=90, lam=600, A=0.35),
}
FX0, FU = 79000, 8                      # 流场网格：世界 x 起点、每格世界像素
FX1 = 113400


FOCUS_CAM = E.Camera({'keys': FOCUS_KEYS}, FPS)


def sec_speed(k, t):
    v = SEC[k]['v']
    if k == 2:                          # 近景慢，拉远后世界速度加大（屏上仍是最慢）
        return v + (62 - v) * float(sstep(7.5, 12.5, t))
    if k == 6:
        if t < T_FOCUS:                 # 全貌远看
            return 240.0
        # 聚焦：屏上速度 38 px/s，段尾越涌越急 38→75 px/s（世界速度 = 屏速 × vh/720）
        vh = FOCUS_CAM.state(t)[1]
        return (38.0 + 37.0 * float(sstep(50.0, 55.5, t))) * vh / 720.0
    return v


def band_amp(k, t):
    a = SEC[k]['A']
    if k == 6 and t > 48:
        a = a + 0.25 * float(sstep(50.0, 55.5, t))
    return a


# 相位积分（逐帧累加，速度变化不会跳）
_TT = np.arange(0, DUR + 1.0, 1.0 / (FPS * 4))
PHASE = {}
for _k in SEC:
    _v = np.array([sec_speed(_k, t) for t in _TT])
    PHASE[_k] = np.concatenate([[0], np.cumsum((_v[1:] + _v[:-1]) / 2 * np.diff(_TT))])


def travel(k, t):
    return float(np.interp(t, _TT, PHASE[k]))


# ------------------------------------------------------------ 准备：mip、绢样、流场
def prep():
    t0 = time.time()
    arr = full()
    silk = DATA + 'silk.npy'
    if not os.path.exists(silk):
        np.save(silk, np.ascontiguousarray(arr[850:1750, 108400:109500]))
    lv = E.build_mips(arr, 'shuitu_scroll')
    E.log('mips', len(lv), [l.shape for l in lv[:4]], '%.0fs' % (time.time() - t0))
    fpath = DATA + 'field.npz'
    if os.path.exists(fpath):
        return
    L3 = lv[3]                                   # 1/8
    j0, j1 = FX0 // FU, FX1 // FU
    img = np.ascontiguousarray(L3[:, j0:j1]).astype(np.float32)
    h, w = img.shape[:2]
    lum = img @ np.float32([0.3, 0.55, 0.15])
    red = ((img[..., 0] - img[..., 1]) > 38) & ((img[..., 0] - img[..., 2]) > 45)
    red = cv2.dilate(red.astype(np.uint8), np.ones((13, 13), np.uint8)) > 0
    # 结构张量 → 线的切向
    gx = cv2.Sobel(cv2.GaussianBlur(lum, (0, 0), 0.8), cv2.CV_32F, 1, 0, ksize=3)
    gy = cv2.Sobel(cv2.GaussianBlur(lum, (0, 0), 0.8), cv2.CV_32F, 0, 1, ksize=3)
    Jxx = cv2.GaussianBlur(gx * gx, (0, 0), 6); Jyy = cv2.GaussianBlur(gy * gy, (0, 0), 6); Jxy = cv2.GaussianBlur(gx * gy, (0, 0), 6)
    # 主梯度方向角 θ（双角平均），切向 = θ + 90°
    th = 0.5 * np.arctan2(2 * Jxy, Jxx - Jyy)
    tx, ty = -np.sin(th), np.cos(th)
    coh = np.sqrt((Jxx - Jyy) ** 2 + 4 * Jxy ** 2) / (Jxx + Jyy + 1e-3)
    # 纹理能量 → 水面遮罩
    hp = lum - cv2.GaussianBlur(lum, (0, 0), 3)
    en = np.sqrt(cv2.GaussianBlur(hp * hp, (0, 0), 10))
    dx = np.zeros((h, w), np.float32); dy = np.zeros((h, w), np.float32)
    mask = np.zeros((h, w), np.float32); sid = np.zeros((h, w), np.uint8)
    X = (np.arange(w) + j0 + 0.5) * FU; Y = (np.arange(h) + 0.5) * FU
    for k, sp in SEC.items():
        s = SECS[k]
        cols = (X > s['x0'] + 190) & (X < s['x1'] - 150)
        rows = (Y > (720 if k == 6 else 880)) & (Y < s['y1'] - 70)
        box = np.outer(rows, cols)
        sid[np.outer(np.ones(h, bool), (X > s['x0'] - 300) & (X < s['x1'] + 300))] = k
        g = np.array(sp['dir'], np.float32); g /= np.linalg.norm(g)
        sg = np.sign(tx * g[0] + ty * g[1]); sg[sg == 0] = 1
        c = np.clip(coh, 0, 1)
        vx = tx * sg * c + g[0] * (1 - c) * 0.6; vy = ty * sg * c + g[1] * (1 - c) * 0.6
        vx = cv2.GaussianBlur(vx, (0, 0), 4) + 0.25 * g[0]; vy = cv2.GaussianBlur(vy, (0, 0), 4) + 0.25 * g[1]
        n = np.sqrt(vx * vx + vy * vy) + 1e-6
        dx[box] = (vx / n)[box]; dy[box] = (vy / n)[box]
        e = en[box]
        thr = np.percentile(e, 50) * 0.5 + np.percentile(e, 15) * 0.5
        m = (en > thr) & box & ~red
        # 题名、小字、左侧印（段左上）
        tb = s.get('title_box')
        if tb:
            x0, y0, bw, bh = tb
            m &= ~np.outer((Y > y0 - 250) & (Y < y0 + bh + 450), (X > x0 - 600) & (X < x0 + bw + 250))
        mm = cv2.morphologyEx(m.astype(np.uint8), cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))
        mm = cv2.morphologyEx(mm, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8)).astype(np.float32)
        mm = cv2.GaussianBlur(mm, (0, 0), 5) * box
        mask = np.maximum(mask, np.clip(mm * 1.6 - 0.3, 0, 1))
    np.savez(fpath, dx=dx, dy=dy, mask=mask, sid=sid)
    vis = np.ascontiguousarray(img).astype(np.uint8).copy()
    vis[..., 0] = np.clip(vis[..., 0] * (1 - 0.5 * mask) + 255 * 0.5 * mask, 0, 255)
    step = 12
    for i in range(6, h, step):
        for j in range(6, w, step):
            if mask[i, j] > 0.5:
                cv2.line(vis, (j, i), (int(j + 5 * dx[i, j]), int(i + 5 * dy[i, j])), (0, 255, 255), 1)
    cv2.imwrite(HERE + 'look/field.jpg', cv2.cvtColor(vis, cv2.COLOR_RGB2BGR), [cv2.IMWRITE_JPEG_QUALITY, 85])
    E.log('field done %.0fs' % (time.time() - t0))


# ------------------------------------------------------------ 带水流的长案全貌渲染器
class FlowScroll(SV.ScrollView):
    def _sample(self, lv, X, Y, lev, origin, unit, border):
        """同 scrollview._sample，但按屏幕分块取源图（长卷斜看时整块包围盒太大、会超出 remap 限制）。"""
        out = np.zeros(X.shape + (3,), np.float32); wsum = np.zeros(X.shape, np.float32)
        nL = len(lv)
        lev = np.clip(lev, 0, nL - 1)
        lo = int(np.floor(np.nanmin(lev))); hi = int(np.ceil(np.nanmax(lev)))
        Hs, Ws = X.shape
        TY, TX = 4, 8
        for L in range(lo, min(hi, nL - 1) + 1):
            w = np.clip(1 - np.abs(lev - L), 0, 1)
            sel = w > 0.002
            if not sel.any():
                continue
            img = lv[L]; sc = unit * 2 ** L
            ix = (X - origin[0]) / sc - 0.5; iy = (Y - origin[1]) / sc - 0.5
            acc = np.zeros(X.shape + (3,), np.float32)
            for bi in range(TY):
                r0, r1 = Hs * bi // TY, Hs * (bi + 1) // TY
                for bj in range(TX):
                    c0, c1 = Ws * bj // TX, Ws * (bj + 1) // TX
                    st = sel[r0:r1, c0:c1]
                    if not st.any():
                        continue
                    tix = ix[r0:r1, c0:c1]; tiy = iy[r0:r1, c0:c1]
                    xs, ys = tix[st], tiy[st]
                    x0 = int(max(0, math.floor(xs.min()) - 2)); x1 = int(min(img.shape[1], math.ceil(xs.max()) + 3))
                    y0 = int(max(0, math.floor(ys.min()) - 2)); y1 = int(min(img.shape[0], math.ceil(ys.max()) + 3))
                    if x1 <= x0 or y1 <= y0:
                        if border == cv2.BORDER_CONSTANT:
                            continue
                        x0 = int(np.clip(math.floor(xs.min()), 0, img.shape[1] - 64)); x1 = x0 + 64
                        y0 = int(np.clip(math.floor(ys.min()), 0, img.shape[0] - 64)); y1 = y0 + 64
                    x1 = min(x1, x0 + 32000); y1 = min(y1, y0 + 32000)
                    crop = np.ascontiguousarray(img[y0:y1, x0:x1])
                    mx_ = (tix - x0).astype(np.float32); my_ = (tiy - y0).astype(np.float32)
                    mx_[~st] = -10; my_[~st] = -10
                    acc[r0:r1, c0:c1] = cv2.remap(crop, mx_, my_, cv2.INTER_LINEAR, borderMode=border).astype(np.float32)
            out += acc * w[..., None]; wsum += w
        return out / np.maximum(wsum, 1e-6)[..., None]

    def setup_flow(self):
        z = np.load(DATA + 'field.npz')
        self.fdx, self.fdy, self.fm = z['dx'], z['dy'], z['mask']
        self.fsid = z['sid']
        self.t = 0.0
        self.flow_on = 1.0
        self.glow = None               # 暖光带中心（世界 x）

    def flow_band(self, X, Y, sel):
        """墨涌带：沿各段流向走的浓淡波（线形不动，墨色顺着流向涌过去）。"""
        t = self.t
        fx = ((X - FX0) / FU - 0.5).astype(np.float32); fy = (Y / FU - 0.5).astype(np.float32)
        m = cv2.remap(self.fm, fx, fy, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0) * self.flow_on
        sid = cv2.remap(self.fsid, fx, fy, cv2.INTER_NEAREST, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
        m = np.where(sel, m, 0).astype(np.float32)
        band = np.zeros(X.shape, np.float32)
        for k, sp in SEC.items():
            ss = (sid == k) & (m > 0.001)
            if not ss.any():
                continue
            g = np.array(sp['dir'], np.float32); g /= np.linalg.norm(g)
            al = X[ss] * g[0] + Y[ss] * g[1]
            ac = -X[ss] * g[1] + Y[ss] * g[0]
            lam = sp['lam']
            ph = 2 * np.pi * (al - 1.5 * travel(k, t)) / lam + 1.3 * np.sin(2 * np.pi * ac / (lam * 1.7)) \
                 + 0.7 * np.sin(2 * np.pi * (al * 0.37 + ac) / (lam * 2.3))
            band[ss] = band_amp(k, t) * np.sin(ph)
        return band * m

    def flow_maps(self, X, Y, sel):
        """返回两相位偏移后的坐标与权重、墨涌调制系数（只在 sel 内有效）。"""
        t = self.t
        fx = ((X - FX0) / FU - 0.5).astype(np.float32); fy = (Y / FU - 0.5).astype(np.float32)
        dx = cv2.remap(self.fdx, fx, fy, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
        dy = cv2.remap(self.fdy, fx, fy, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
        m = cv2.remap(self.fm, fx, fy, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0) * self.flow_on
        sid = cv2.remap(self.fsid, fx, fy, cv2.INTER_NEAREST, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
        m = np.where(sel, m, 0).astype(np.float32)
        tr = np.zeros(X.shape, np.float32); P = np.full(X.shape, 100, np.float32)
        band = np.zeros(X.shape, np.float32)
        for k, sp in SEC.items():
            ss = sid == k
            if not ss.any():
                continue
            tr[ss] = travel(k, t); P[ss] = sp['P']
            g = np.array(sp['dir'], np.float32); g /= np.linalg.norm(g)
            al = X[ss] * g[0] + Y[ss] * g[1]
            ac = -X[ss] * g[1] + Y[ss] * g[0]
            lam = sp['lam']
            ph = 2 * np.pi * (al - 1.5 * travel(k, t)) / lam + 1.3 * np.sin(2 * np.pi * ac / (lam * 1.7)) \
                 + 0.7 * np.sin(2 * np.pi * (al * 0.37 + ac) / (lam * 2.3))
            band[ss] = band_amp(k, t) * np.sin(ph)
        f1 = (tr / P) % 1.0; f2 = (f1 + 0.5) % 1.0
        w1 = 1 - np.abs(2 * f1 - 1)
        o1 = f1 * P * m; o2 = f2 * P * m
        return (X - dx * o1, Y - dy * o1), (X - dx * o2, Y - dy * o2), w1, band * m

    def render(self, cam, light=1.0):
        r, d, f, C, fpx = self.basis(cam)
        pcx, pcy = self.WS * (0.5 + cam.get('ox', 0.0)), self.HS * (0.5 + cam.get('oy', 0.0))
        a = (self.U - pcx) / fpx; b = (self.V - pcy) / fpx
        Dx = r[0] * a + d[0] * b + f[0]; Dy = r[1] * a + d[1] * b + f[1]; Dz = r[2] * a + d[2] * b + f[2]
        hit = Dz > 1e-4
        lam = np.where(hit, -C[2] / np.maximum(Dz, 1e-4), 0).astype(np.float32)
        X = (C[0] + lam * Dx).astype(np.float32); Y = (C[1] + lam * Dy).astype(np.float32)
        Xx = np.gradient(X, axis=1); Xy = np.gradient(X, axis=0); Yx = np.gradient(Y, axis=1); Yy = np.gradient(Y, axis=0)
        det = np.abs(Xx * Yy - Xy * Yx) + 1e-6
        l1 = np.hypot(Xx, Yx); l2 = np.hypot(Xy, Yy)
        smax = np.maximum(l1, l2); geo = np.sqrt(det)
        lev = np.log2(np.maximum(geo, 1e-3)) + 0.35 * np.log2(np.maximum(smax / geo, 1.0))
        lev = lev + self.lod_bias
        lev = np.maximum(lev, np.log2(np.maximum(smax, 1e-3)) - 1.5)   # 掠射处不取过细的级（源图包围盒过大）
        kf = float(sstep(7.0, 8.4, self.t)) if self.t < T_SEG0 else 0.0   # 全貌（斜看）阶段才用
        if kf > 0:                             # 拉远/斜看阶段：不读原图 L0（1.3 GB，读盘太慢）；渐入，不跳
            lev = np.maximum(lev + 0.25 * kf, kf)
        far = ~hit | (lam > 1e9)
        lev[far] = 30
        W, H = self.Wsrc, self.Hsrc
        inside = hit & (X >= 0) & (X < W) & (Y >= 0) & (Y < H)
        allin = bool(inside.all())
        if allin:
            img = None
        else:
            levT = lev - math.log2(self.t_unit)
            img = self._sample(self.tlv, X, Y, np.where(far, len(self.tlv) - 1, levT), self.t_origin, self.t_unit, cv2.BORDER_REFLECT)
        band = None
        if inside.any():
            Xi = np.where(inside, X, -9); Yi = np.where(inside, Y, -9); Li = np.where(inside, lev, 0)
            flowsel = inside & (X > FX0) & (X < FX1) & (Li < 4.2)
            sc = self._sample(self.lv, Xi, Yi, Li, (0, 0), 1, cv2.BORDER_REPLICATE)
            if self.flow_on > 0 and flowsel.any():
                band = self.flow_band(Xi, Yi, flowsel)
            if band is not None:
                # 墨涌：墨线相对本地绢色按带状起伏加深/减淡（只动原作的墨）
                base = cv2.GaussianBlur(sc, (0, 0), 9)
                ink = np.minimum(sc - base, 0)
                sc = sc + ink * band[..., None]
            if allin:
                img = sc
            else:
                px = np.maximum(smax, 1e-3)
                ed = np.minimum(np.minimum(X, W - X), np.minimum(Y, H - Y)) / px
                k = np.clip(ed + 0.5, 0, 1)[..., None]
                img = img * (1 - k) + sc * k
        ox = np.maximum(np.maximum(-X, X - W), 0); oy = np.maximum(np.maximum(-Y, Y - H), 0)
        dout = np.hypot(ox, oy * 1.15)
        pool = 1 - 0.70 * SV._sm((dout - self.pool[0]) / self.pool[1])
        lit = pool * light
        tx0, ty0, tx1, ty1 = self.table
        te = np.minimum(np.minimum(X - tx0, tx1 - X), np.minimum(Y - ty0, ty1 - Y)) / np.maximum(smax, 1e-3)
        lit = lit * np.where(far, 0, np.clip(te + 0.5, 0, 1))
        img = img * lit[..., None] + self.dark * (1 - lit[..., None]) * 0.55
        if self.glow is not None:             # 暖光沿卷走
            gx0, gsoft, gamp = self.glow
            g = gamp * np.exp(-((X - gx0) / gsoft) ** 2) * np.where(far, 0, 1) * np.clip(1 - dout / 4000, 0, 1)
            img = img * (1 + g[..., None] * np.float32([0.30, 0.22, 0.08]))
        depth = lam * np.sqrt(a * a + b * b + 1)
        hz = 1 - np.exp(-np.maximum(depth - self.haze0, 0) / self.hazeL)
        hz = np.where(far, 1.0, hz * self.hazeA)[..., None]
        img = img * (1 - hz) + self.dark * hz
        out = img if self.SS == 1 else cv2.resize(img, (self.W, self.H), interpolation=cv2.INTER_AREA)
        bl = cv2.GaussianBlur(out, (0, 0), 1.0)
        out = out + 0.22 * (out - bl)
        return np.clip(out + 0.5, 0, 255).astype(np.uint8)


def make_sv(res=720):
    sv = FlowScroll(full(), 'shuitu', [(DATA + 'silk.npy', [0, 0, 1100, 900])], tone=(0.84, 0.80, 0.71), res=res, ss=1,
                    table_unit=12, tex_scale=1.6, margin=(10000, 7000))
    sv.haze0, sv.hazeL, sv.hazeA = 80000.0, 150000.0, 0.62
    sv.pool = (1300.0, 4600.0)
    sv.setup_flow()
    return sv


# ------------------------------------------------------------ 相机
P_DONG = dict(cx=108250, cy=2745, vh=880)          # 洞庭风细最干净的一块
TITLE_HH = (85350, 896)                            # 题名框中心（黄河逆流）


def fit_range(sv, yaw, pitch, target, xr, fov=FOV, fill=0.94, bias=(0.0, 0.0)):
    x0, x1 = xr
    pts = [(x0, 0), (x1, 0), (x1, H0), (x0, H0)]
    c = dict(tx=float(target[0]), ty=float(target[1]), yaw=yaw, pitch=pitch, dist=(x1 - x0) * 0.8, fov=fov, ox=0.0, oy=0.0)
    for _ in range(80):
        q, z = sv.project(c, pts)
        if (z <= 0).any():
            c['dist'] *= 1.3; continue
        qx0, qy0 = q.min(0); qx1, qy1 = q.max(0)
        k = max((qx1 - qx0) / (sv.W * fill), (qy1 - qy0) / (sv.H * fill))
        c['dist'] *= k ** 0.7
        c['ox'] -= ((qx0 + qx1) / 2 / sv.W - 0.5 - bias[0]) * 0.7
        c['oy'] -= ((qy0 + qy1) / 2 / sv.H - 0.5 - bias[1]) * 0.7
    return c


class Cam:
    """整段相机：返回 scrollview 相机 dict。"""
    G = 6.0                                     # overview_shot 的滑行终点（反向用）

    def __init__(self, sv):
        self.sv = sv
        # 1) 拉出：反向俯冲。τ = TM − t：t=T_PULL0 时 τ=落点（洞庭），t=T_PULL1 时 τ=G（全貌），之后沿滑行段极慢环移
        self.TM = T_PULL0 + self.G + (T_PULL1 - T_PULL0)
        self.shot1 = SV.overview_shot(sv, 0.0, self.G, self.G + (T_PULL1 - T_PULL0), P_DONG, fov=FOV)
        self.plan = FOCUS_CAM

    def planar_state(self, c):
        return self.sv.state_for(c['cx'], c['cy'], c['vh'], fov=FOV)

    def __call__(self, t):
        if t <= T_PULL0:
            return self.planar_state(P_DONG)
        if t < T_SEG0:
            return self.shot1.cam(self.TM - t)
        if t < T_FOCUS - SEG_X:                 # 十二段逐段（相机只给出当前段；帧由 display() 合成）
            return self.planar_state(seg_frame(seg_at(t)))
        c, vh = self.plan.state(t)
        return self.sv.state_for(c[0], c[1], vh, fov=FOV)


def seg_at(t):
    """十二段展示期内 t 所在的段号（1..12）。"""
    return int(min(11, max(0, (t - T_SEG0) // SEG_T))) + 1


def speed_report(sv, cam, t0, t1):
    peak, tpk = 0.0, t0
    n = int(round((t1 - t0) * FPS))
    for i in range(n):
        ca, cb = cam(t0 + i / FPS), cam(t0 + (i + 1) / FPS)
        r, d, f, C, fpx = sv.basis(ca)
        pts = []
        for u in (-0.15, 0, 0.15):
            for v in (-0.15, 0, 0.15):
                a_, b_ = (u - ca.get('ox', 0)) * sv.WS / fpx, (v - ca.get('oy', 0)) * sv.HS / fpx
                D = r * a_ + d * b_ + f
                if D[2] <= 1e-4:
                    continue
                P = C + (-C[2] / D[2]) * D
                pts.append(P[:2])
        pts = np.array(pts)
        qa, _ = sv.project(ca, pts); qb, _ = sv.project(cb, pts)
        m = float(np.median(np.hypot(*(qb - qa).T))) * 720 / sv.H
        if m > peak:
            peak, tpk = m, t0 + i / FPS
    return peak, tpk


# ------------------------------------------------------------ 展签与题名光
LABEL = {'text': ['水圖卷', '南宋　馬遠', '絹本淡設色', '每段二六·八×四一·六厘米', '北京故宮博物院藏'],
         'x': 0.19, 'y': 0.49, 't0': 9.8, 't1': 14.0, 'fade': 0.6, 'color': '#EDE6D8', 'title_size': 26, 'size': 22}
GLOW = (9.0, 13.4)                                  # 暖光沿卷走（卷首 → 卷尾）
NAME_SIZE = 21                                      # 段名竖排小字（720p 字号）


def title_light(fr, t, sv, cam):
    """聚焦黄河逆流：四周略压暗，一束柔光落在「黃河逆流」四字上（峰值 40.8–45.2）。"""
    k = float(sstep(39.2, 40.8, t)) * (1 - float(sstep(45.2, 47.0, t)))
    if k <= 0:
        return fr
    q, _ = sv.project(cam, [TITLE_HH])
    x, y = q[0]
    H, W = fr.shape[:2]
    s = H / 720
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    rr = ((xx - x) / (150 * s)) ** 2 + ((yy - y) / (260 * s)) ** 2
    spot = np.exp(-rr)
    O = fr.astype(np.float32)
    O = O * (1 - 0.22 * k * (1 - spot[..., None])) * (1 + 0.14 * k * spot[..., None] * np.float32([1.0, 0.93, 0.78]))
    return np.clip(O + 0.5, 0, 255).astype(np.uint8)


def lines_mask(fr):
    L = fr.astype(np.float32) @ np.float32([0.3, 0.55, 0.15])
    base = cv2.GaussianBlur(L, (0, 0), 7)
    m = np.clip((base - L - 3) / 16, 0, 1)
    return m


# ------------------------------------------------------------ 主程序
def main():
    if len(sys.argv) > 1 and sys.argv[1] == 'prep':
        prep(); return
    ap = argparse.ArgumentParser(); ap.add_argument('out'); ap.add_argument('--res', type=int, default=720)
    ap.add_argument('--stills', default=''); ap.add_argument('--frames', default=''); ap.add_argument('--mask', default='')
    ap.add_argument('--crf', type=int, default=12); ap.add_argument('--speed', action='store_true')
    a = ap.parse_args()
    RES = a.res
    sv = make_sv(RES)
    cam = Cam(sv)
    if a.speed:
        for (t0, t1) in [(0, T_PULL0), (T_PULL0, T_PULL1), (T_PULL1, T_SEG0), (T_FOCUS, T_FOCUS + 1), (T_FOCUS + 1, 45.0),
                         (45.0, 50.5), (50.5, 56)]:
            print('speed %5.1f–%5.1f  峰 %.2f px/帧 @%.2f' % ((t0, t1) + speed_report(sv, cam, t0, t1)))
        for (t0, t1) in [(T_FOCUS + 1, 45.0), (45.0, 50.5), (50.5, 56)]:     # 推拉速度（对数，%/s）
            ts = np.arange(t0, t1, 1 / FPS)
            vh = np.array([FOCUS_CAM.state(x)[1] for x in ts])
            print('zoom  %5.1f–%5.1f  峰 %.1f %%/s' % (t0, t1, 100 * np.abs(np.diff(np.log(vh))).max() * FPS))
        return
    LR = E.Renderer({'fps': FPS, 'duration': DUR, 'ss': 1, 'layers': [],
                     'camera': {'keys': [dict(t=0, cx=0, cy=0, vh=1000)]}, 'labels': [LABEL]}, RES)
    H = RES; W = int(round(H * 16 / 9 / 2) * 2)
    n = int(round(DUR * FPS))

    def dim_sides(fr, c, k):
        """本段左右以外（邻段、段间裱纸）压暗到 DIM；平面相机下按屏幕列算，3 px 羽化。"""
        s = SECS[k]
        q, _ = sv.project(c, [(s['x0'], s['y0']), (s['x1'], s['y0'])])
        xs = np.arange(W, dtype=np.float32) + 0.5
        m = np.clip((xs - q[0][0]) / 3.0 + 0.5, 0, 1) * np.clip((q[1][0] - xs) / 3.0 + 0.5, 0, 1)
        g = DIM + (1 - DIM) * m
        return np.clip(fr.astype(np.float32) * g[None, :, None] + 0.5, 0, 255).astype(np.uint8), q[0][0]

    name_lb = {}

    def name_label(k, x_right):
        if k not in name_lb:
            y = 0.33 if k == 1 else 0.055       # 殘段无题；左侧段间裱纸顶上有骑缝大印，字放到印下方的空处
            name_lb[k] = E.Label({'cols': [(SEG_NAME[k], NAME_SIZE, 'Regular')], 'x': x_right / W, 'y': y,
                                  't0': -100, 't1': 1e9, 'fade': 0.01, 'color': '#EDE6D8', 'lead': 1.22}, LR)
        return name_lb[k]

    def draw_name(fr, k, x_left, op=1.0):
        """段名竖排小字：在本段左缘外侧，顶端与原题同高。"""
        lb = name_label(k, x_left - 22)
        f = fr.astype(np.float32)
        if op >= 0.999:
            lb.draw(f, 0.0)
        else:
            g = f.copy(); lb.draw(g, 0.0); f = f * (1 - op) + g * op
        return np.clip(f + 0.5, 0, 255).astype(np.uint8)

    seg_cache = {}

    def seg_still(k):
        """第 k 段的展示帧（静止：不推拉、不平移、不加水流）。"""
        if k not in seg_cache:
            sv.t = T_SEG0 + 0.5; sv.flow_on = 0.0; sv.glow = None
            c = cam.planar_state(seg_frame(k))
            fr, xl = dim_sides(sv.render(c), c, k)
            seg_cache[k] = draw_name(fr, k, xl)
        return seg_cache[k]

    def live(t):
        sv.t = t
        g = (t - GLOW[0]) / (GLOW[1] - GLOW[0])
        if 0 <= g <= 1:
            u = SV._sm5(g)
            sv.glow = (W0 + 6000 - (W0 + 12000) * u, 5200.0, 0.55 * math.sin(math.pi * min(1.0, g * 1.0)) ** 0.5)
        else:
            sv.glow = None
        sv.flow_on = 1.0 if t < T_SEG0 else float(sstep(T_FOCUS, T_FOCUS + 1.6, t))
        c = cam(t)
        fr = sv.render(c)
        if T_FOCUS - SEG_X <= t:                       # 聚焦段：邻段压暗、段名淡出、题名柔光
            fr, xl = dim_sides(fr, c, 6)
            op = 1 - float(sstep(T_FOCUS + 0.4, T_FOCUS + 1.2, t))
            if op > 0:
                fr = draw_name(fr, 6, xl, op)
            fr = title_light(fr, t, sv, c)
        if LABEL['t0'] < t < LABEL['t1']:
            f = fr.astype(np.float32)
            for lb in LR.labels:
                lb.draw(f, t)
            fr = np.clip(f + 0.5, 0, 255).astype(np.uint8)
        return fr

    def xfade(A, B, w):
        return np.clip(A.astype(np.float32) * (1 - w) + B.astype(np.float32) * w + 0.5, 0, 255).astype(np.uint8)

    def frame(i):
        t = i / FPS
        if t < T_XOV:
            return live(t)
        if t < T_SEG0:                                   # 全貌 → 第一段
            return xfade(live(t), seg_still(1), float(sstep(T_XOV, T_SEG0, t)))
        if t >= T_FOCUS:
            return live(t)
        k = seg_at(t)
        tk = T_SEG0 + (k - 1) * SEG_T + (SEG_T - SEG_X)   # 本段叠化开始
        if t < tk:
            return seg_still(k)
        w = float(sstep(tk, tk + SEG_X, t))
        return xfade(seg_still(k), seg_still(k + 1) if k < 12 else live(t), w)

    if a.stills:
        base = os.path.splitext(a.out)[0]
        for i in [int(x) for x in a.stills.split(',') if x]:
            tr = time.time(); fr = frame(i)
            cv2.imwrite(f'{base}_f{i:04d}.jpg', cv2.cvtColor(fr, cv2.COLOR_RGB2BGR), [cv2.IMWRITE_JPEG_QUALITY, 92])
            E.log(f'still {i} ({i / FPS:.2f}s) {time.time() - tr:.2f}s')
        return
    f0, f1 = (map(int, a.frames.split(':')) if a.frames else (0, n))

    def pipe(path):
        return subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}',
                                 '-r', str(FPS), '-i', '-', '-c:v', 'libx264', '-preset', 'medium', '-crf', str(a.crf),
                                 '-pix_fmt', 'yuv420p', '-movflags', '+faststart', path], stdin=subprocess.PIPE)
    ff = pipe(a.out); fm = pipe(a.mask) if a.mask else None
    black = np.zeros((H, W, 3), np.uint8)
    tr = time.time()
    for i in range(f0, f1):
        fr = frame(i)
        ff.stdin.write(fr.tobytes())
        if fm is not None:
            t = i / FPS
            k = 1 - float(sstep(7.0, 8.6, t))
            if k > 0:
                m = lines_mask(fr) * k
                fm.stdin.write(np.repeat(np.clip(m * 255 + 0.5, 0, 255).astype(np.uint8)[..., None], 3, 2).tobytes())
            else:
                fm.stdin.write(black.tobytes())
        if (i - f0) % 30 == 0:
            E.log(f'frame {i}/{f1}  {(time.time() - tr) / (i - f0 + 1):.2f}s/帧')
    ff.stdin.close(); ff.wait()
    if fm is not None:
        fm.stdin.close(); fm.wait()
    E.log(f'完成 {a.out}')


if __name__ == '__main__':
    main()
