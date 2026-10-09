# -*- coding: utf-8 -*-
"""第二集 s2 马远《踏歌图》 全局 49–117（帧 0 = 49.0 s，2040 帧）。
动：
  · 题诗自己写出来：宁宗的二十个字先淡成残影，再按"自上而下、自左而右、沿笔画连通路径"的次序逐字逐笔显出
    （揭原作之墨，笔锋过处墨先湿重再收），四行分别与旁白读诗同步；随后「賜王都提舉」小字写出、两方印按下。
  · 踏歌：田埂上三组老农（甲 / 乙丙 / 丁）整身刚体起伏顿足，落脚点踩在配乐起音上（强拍大踏、弱拍小踏），
    父层用修补后的底板，不做肢体变形。
  · 下降：题诗 → 中景宫阙 → 田埂，换景别都是干净叠化（1.5 s）；拉开见左下斧劈巨石，再上移到拖枝柳，
    最后叠化拉回全貌静止。
  v2（2026-09-29）：按用户意见"本集不用雾"，去掉雾纱叠化（veil_z / veil_d）、宫阙松间雾（mist_m）、
    田埂上方的雾带（F 镜头 fog fx）；X_AP、X_WZ 叠化收到 1.5 s。v1 带雾代码：work/seg_s2_v1_fog.py.bak。
  速度检查：   lockf -k $S/.heavy.lock python3 seg_s2.py --check
  抽帧：       lockf -k $S/.heavy.lock python3 seg_s2.py --stills 100,400 --out review/s.png
  成片：       nohup lockf -k $S/.heavy.lock python3 seg_s2.py --out ../seg_s2.mp4 > render.log 2>&1 &
"""
import sys, os, math, time, json, argparse, subprocess
from types import SimpleNamespace
import numpy as np, cv2

S = '~/claude-projects/china-art/series'
sys.path.insert(0, S + '/lib')
import engine as E

HERE = os.path.dirname(os.path.abspath(__file__))
EP = S + '/ep02_nansong'
SRC = HERE + '/work/tage_full.npy'          # 13391×7831（高×宽），与名画记 PNG 逐像素相同
T_GLOBAL0 = 49.0
DUR = 68.0
FOG_RECT = [3400, 4550, 2200, 800]          # 远峰与松林之间的空白雾（原图像素 x,y,w,h）
G = lambda g: g - T_GLOBAL0                 # 全局秒 → 段内秒

# ---------------- 时间表（段内秒） ----------------
T_FULL_END = 12.0            # 61.0 全貌静止结束
X_AP = (13.4, 14.9)          # 全貌 → 题诗 干净叠化
T_GHOST = (G(64.8), G(66.1)) # 题诗淡成残影
GHOST = 0.16
LINES_T = [(G(66.35), G(67.95)), (G(68.05), G(69.65)), (G(70.45), G(72.05)), (G(72.15), G(73.75))]
T_INSCR = (G(73.95), G(74.65))
T_SEAL = (G(74.80), G(75.05))   # 小印 / 御書之寶
X_PM = (28.0, 29.5)
X_MF = (32.0, 33.5)
X_WZ = (50.55, 52.05)
# 顿足（全局秒，强=1 / 弱=0）：配乐起音 82.74–84.84、88.51–94.64；84.84–88.51 配乐停顿处按旁白节奏约 0.7 s 一踏
BEATS = [(82.74, 0), (83.44, 1), (84.09, 0), (84.84, 1), (85.55, 0), (86.25, 1), (86.95, 0), (87.70, 1),
         (88.51, 1), (89.20, 1), (89.89, 0), (90.59, 1), (91.24, 0), (91.97, 1), (92.59, 0), (93.28, 1),
         (93.99, 0), (94.64, 1)]


def zoom_about(state, p, k):
    cx, cy, vh = state
    return (p[0] - (p[0] - cx) / k, p[1] - (p[1] - cy) / k, vh / k)


def cam(*keys, rest=None):
    ks = [dict(t=k[0], cx=k[1][0], cy=k[1][1], vh=k[1][2], **({'ease': k[2]} if len(k) > 2 else {})) for k in keys]
    r = rest if rest is not None else ks[-1]
    return {'rest': {'cx': r['cx'], 'cy': r['cy'], 'vh': r['vh']} if 'cx' in r else r, 'keys': ks}


POEM_C = (3420, 1290)
WILLOW = (5550, 9500)


def build():
    samples = [(SRC, [4900, 200, 7600, 1300]), (SRC, [3300, 4550, 5700, 5250])]
    hs = E.hanging_scroll(SRC, 'tage', fill_h=0.94, samples=samples)
    F = (hs['full']['cx'], hs['full']['cy'], hs['full']['vh'])
    layers = hs['layers']
    A1 = zoom_about(F, POEM_C, 1.12)
    P0 = (POEM_C[0], POEM_C[1] - 30, 2500)
    P1 = (POEM_C[0], POEM_C[1], 2150)
    P2 = (POEM_C[0], POEM_C[1] + 620, 2150)
    M0 = (5300, 5450, 2700)
    M1 = (5300, 6500, 2700)
    F0 = (5450, 11650, 2300)
    F1 = (5450, 12080, 2300)
    FB = (4650, 11300, 3200)
    W1 = (5400, 9650, 2800)
    W2 = zoom_about(W1, WILLOW, 1 / 1.12)
    Zs = zoom_about(F, WILLOW, 1.2)
    shots = {
        'A': cam((0, F), (T_FULL_END, F), (15.5, A1, 1.0), rest=dict(cx=F[0], cy=F[1], vh=F[2])),
        'P': cam((0, P0), (13.3, P0), (18.0, P1, 1.5), (27.0, P1), (30.5, P2, 1.2), rest=dict(cx=P1[0], cy=P1[1], vh=P1[2])),
        'M': cam((0, M0), (27.5, M0), (33.5, M1, 1.5)),
        'F': cam((0, F0), (31.5, F0), (35.0, F1, 1.2), (36.0, F1), (43.5, FB, 1.5), (44.0, FB), (49.5, W1, 1.5),
                 (49.6, W1), (52.6, W2, 1.0), rest=dict(cx=F1[0], cy=F1[1], vh=F1[2])),
        'Z': cam((0, Zs), (50.0, Zs), (55.0, F, 1.5), rest=dict(cx=F[0], cy=F[1], vh=F[2])),
    }
    timeline = [('A', 0, 0), ('P', X_AP[0], X_AP[1]), ('M', X_PM[0], X_PM[1]), ('F', X_MF[0], X_MF[1]), ('Z', X_WZ[0], X_WZ[1])]
    fx_by = {
        'M': [],
        'F': [],                                     # v2：不用雾（v1 此处有田埂上方雾带）
    }
    seg_common = {'fps': 30, 'duration': DUR, 'layers': layers, 'fx': [],
                  'grade': {'gamma': 0.93, 'gain': 1.03}, 'sharpen': 0.25}
    label = {'text': ['踏歌圖', '南宋　馬遠', '絹本設色', '一九二·五×一一一厘米', '北京故宮博物院藏'],
             'x': 0.87, 'y': 0.14, 't0': G(55.8), 't1': G(61.2), 'fade': 0.9, 'color': '#2b251d',
             'title_size': 26, 'size': 23}
    return dict(seg=seg_common, shots=shots, timeline=timeline, labels=[label], fx_by=fx_by,
                states=dict(F=F, M0=M0, M1=M1))


# ======================================================================
def fbm(n, seed, beta=2.4, fmin=1.5):
    rng = np.random.default_rng(seed)
    w = rng.standard_normal((n, n))
    fy = np.fft.fftfreq(n)[:, None] * n; fx = np.fft.fftfreq(n)[None, :] * n
    f = np.sqrt(fx ** 2 + fy ** 2); f[0, 0] = 1
    amp = f ** (-beta / 2); amp[f < fmin] = 0
    r = np.real(np.fft.ifft2(np.fft.fft2(w) * amp))
    lo, hi = np.percentile(r, [1, 99])
    return np.clip((r - lo) / (hi - lo), 0, 1).astype(np.float32)


def real_fog_color(W, H, lut):
    src = E._open(SRC)
    x, y, w, h = FOG_RECT
    blk = np.ascontiguousarray(src[y:y + h, x:x + w, :3])
    col = cv2.resize(blk, (w // 4, h // 4), interpolation=cv2.INTER_AREA).astype(np.float32)
    col = np.clip(col * 1.30, 0, 255)
    col = cv2.GaussianBlur(col, (0, 0), 12.0)
    col = cv2.LUT(np.clip(col + 0.5, 0, 255).astype(np.uint8), lut).astype(np.float32)
    return cv2.resize(col, (W // 2, H // 2), interpolation=cv2.INTER_AREA)


def cumint(fn, t0, t1, dt=0.01):
    ts = np.arange(t0, t1 + dt, dt)
    v = np.array([fn(t) for t in ts])
    return ts, np.concatenate([[0], np.cumsum((v[1:] + v[:-1]) * 0.5 * dt)])


class VolFog:
    """屏幕空间多层体积雾（同北宋集 xishan/seg_s2.py，半分辨率计算）。"""
    LAYERS = [
        dict(scale=1.7, vy=30, vx=-9, lead=-0.5, amax=1.00, db=0.30, zr=1.2, tint=0.95, seed=3),
        dict(scale=2.3, vy=45, vx=11, lead=-0.15, amax=0.80, db=0.05, zr=1.7, tint=0.98, seed=5),
        dict(scale=3.1, vy=60, vx=-13, lead=0.2, amax=0.72, db=-0.05, zr=2.3, tint=1.05, seed=7),
        dict(scale=4.3, vy=80, vx=16, lead=0.5, amax=0.62, db=-0.12, zr=3.0, tint=1.12, seed=9),
    ]

    def __init__(self, W, H, col, top, bot, bias, vfac, P, t_on, layers=None, L=260.0):
        self.W, self.H = W, H
        self.w2, self.h2 = W // 2, H // 2
        self.k = H / 720.0
        self.Wr, self.Hr = W / self.k, H / self.k
        self.col = col
        self.top, self.bot, self.bias, self.P = top, bot, bias, P
        self.t_on = t_on
        self.L = L
        self.layers = [dict(l) for l in (layers or self.LAYERS)]
        for l in self.layers:
            l['N'] = fbm(512, l['seed'], 3.0)
            l['Wa'] = fbm(256, l['seed'] + 100, 3.4); l['Wb'] = fbm(256, l['seed'] + 200, 3.4)
        self.ts, self.I = cumint(vfac, t_on[0] - 1, t_on[1] + 1)
        X, Y = np.meshgrid((np.arange(self.w2) + 0.5) * 2 / self.k, (np.arange(self.h2) + 0.5) * 2 / self.k)
        self.Xo = X.astype(np.float32); self.Yo = Y.astype(np.float32)

    @staticmethod
    def _samp(tex, u, v):
        n = tex.shape[0]
        return cv2.remap(tex, (u % n).astype(np.float32), (v % n).astype(np.float32), cv2.INTER_LINEAR,
                         borderMode=cv2.BORDER_WRAP)

    def stack(self, t):
        if t < self.t_on[0] or t > self.t_on[1]:
            return None
        W, H = self.Wr, self.Hr
        Fp = np.zeros((self.h2, self.w2, 3), np.float32); Fa = np.zeros((self.h2, self.w2), np.float32)
        ivy = float(np.interp(t, self.ts, self.I))
        P = self.P(t); bias = self.bias(t)
        any_ = False
        for l in self.layers:
            tl = t + l['lead']
            top, bot = self.top(tl), self.bot(tl)
            E_ = np.minimum((self.Yo - top) / self.L, (bot - self.Yo) / self.L)
            if E_.max() + bias + l['db'] + 0.5 < -0.2:
                continue
            z = math.exp(P * l['zr']); sc = l['scale'] * z
            u = (self.Xo - W / 2) / (sc * 2.4) + l['vx'] * t / l['scale'] + 97 * l['seed']
            v = (self.Yo - H / 2) / sc - l['vy'] * ivy / l['scale'] + 53 * l['seed']
            wu = self._samp(l['Wa'], u * 0.25 + 0.6 * t, v * 0.25)
            wv = self._samp(l['Wb'], u * 0.25, v * 0.25 - 0.5 * t)
            u2 = u + 16 * (wu - 0.5); v2 = v + 12 * (wv - 0.5)
            n = self._samp(l['N'], u2, v2)
            nup = self._samp(l['N'], u2, v2 - 12)
            d = n - 0.5 + np.clip(E_, -1.5, 0.6) + bias + l['db']
            a = l['amax'] * E.sstep(-0.2, 0.2, d).astype(np.float32)
            if a.max() < 1e-3:
                continue
            any_ = True
            shade = np.clip(1 + 1.2 * (n - nup) + 0.30 * (n - 0.5), 0.86, 1.28) * l['tint']
            c = self.col * shade[..., None]
            a3 = a[..., None]
            Fp = Fp * (1 - a3) + c * a3
            Fa = Fa * (1 - a) + a
        if not any_:
            return None
        return Fp, Fa

    def draw(self, fr, t):
        st = self.stack(t)
        if st is None:
            return fr
        Fp, Fa = st
        Fp = cv2.resize(Fp, (self.W, self.H), interpolation=cv2.INTER_LINEAR)
        Fa = cv2.resize(Fa, (self.W, self.H), interpolation=cv2.INTER_LINEAR)[..., None]
        return fr * (1 - Fa) + Fp


# ======================================================================
def _pyr(rgba, n=4):
    lv = [rgba]
    while min(lv[-1].shape[:2]) > 48 and len(lv) < n:
        lv.append(cv2.resize(lv[-1], (lv[-1].shape[1] // 2, lv[-1].shape[0] // 2), interpolation=cv2.INTER_AREA))
    return lv


class PoemWrite(E._FxBase):
    """题诗逐笔写出（揭原作之墨）。显示 = S − (S − P)·f，S = 去墨后的绢（只在有墨处替换），f = 显墨比例。
    笔顺近似：每字的墨按连通笔画分组，组按"先上后下、先左后右"排序；组内沿笔画的测地距离从起笔点推进（笔锋走）。"""
    REG = [2080, 360, 4780, 2200]      # 题诗、小字、两印所在区域（世界坐标）

    def __init__(self, spec, R):
        spec.setdefault('after', 'scroll')
        super().__init__(spec, R)
        x0, y0, x1, y1 = self.REG
        self.origin = np.array([x0, y0], float)
        cache = HERE + '/work/poem_cache.npz'
        if os.path.exists(cache):
            z = np.load(cache)
            self.S, self.SmP, self.tau, self.ink = z['S'], z['SmP'], z['tau'], z['ink']
        else:
            self._prep()
            np.savez(cache, S=self.S, SmP=self.SmP, tau=self.tau, ink=self.ink)
        h, w = self.tau.shape
        fe = 40
        ay = E.sstep(0, fe, np.minimum(np.arange(h), h - 1 - np.arange(h)).astype(np.float32))
        ax = E.sstep(0, fe, np.minimum(np.arange(w), w - 1 - np.arange(w)).astype(np.float32))
        self.alpha = (ay[:, None] * ax[None, :]).astype(np.float32)[..., None]
        self.t_end = float(self.tau[self.ink > 0].max()) + 1.2
        E.log(f'题诗区 {w}x{h}，写完 {self.t_end + T_GLOBAL0:.2f}s（全局）')

    def _prep(self):
        from skimage.graph import MCP_Geometric
        from scipy import ndimage as ndi
        x0, y0, x1, y1 = self.REG
        src = E._open(SRC)
        P = np.ascontiguousarray(src[y0:y1, x0:x1, :3]).astype(np.float32)
        h, w = P.shape[:2]
        # 绢：先用灰度闭运算粗估，再对"非墨"像素做归一化卷积取局部绢色（均值，不偏亮）
        lum = lambda a: a @ np.float32([0.3, 0.55, 0.15])
        L = lum(P)
        # 局部绢色 = 1/4 缩小图上的大窗口中值（不受笔画与白色绢裂影响）
        Pd = cv2.resize(np.clip(P, 0, 255).astype(np.uint8), (w // 4, h // 4), interpolation=cv2.INTER_AREA)
        med = np.stack([cv2.medianBlur(np.ascontiguousarray(Pd[..., c]), 31) for c in range(3)], 2).astype(np.float32)
        silk = cv2.GaussianBlur(cv2.resize(med, (w, h), interpolation=cv2.INTER_LINEAR), (0, 0), 6)
        red0 = P[..., 0] - P[..., 2]
        D = np.clip(1 - L / np.maximum(lum(silk), 1), 0, 1)
        red = np.clip(red0 - (silk[..., 0] - silk[..., 2]) - 6, 0, 255) / 40.0
        D = np.maximum(D, np.clip(red, 0, 1) * 0.5)
        m = E.sstep(0.10, 0.24, cv2.GaussianBlur(D, (0, 0), 1.5)).astype(np.float32)
        m = cv2.dilate(m, np.ones((3, 3), np.uint8))
        # 去墨后的绢 = 平滑绢色 + 附近空白绢的织纹（只在有墨处）
        blank = np.ascontiguousarray(src[250:250 + h, 4900:4900 + w, :3]).astype(np.float32) if 4900 + w <= 7700 else None
        if blank is None or blank.shape[:2] != (h, w):
            bx = np.ascontiguousarray(src[200:1300, 4900:7600, :3]).astype(np.float32)
            reps = (h // bx.shape[0] + 1, w // bx.shape[1] + 1)
            blank = np.tile(bx, (reps[0], reps[1], 1))[:h, :w]
        weave = blank - cv2.GaussianBlur(blank, (0, 0), 5)
        Sfull = silk + 0.8 * weave
        mm = m[..., None]
        S = P * (1 - mm) + Sfull * mm
        self.S = S.astype(np.float32); self.SmP = (S - P).astype(np.float32)
        ink = (m > 0.02).astype(np.uint8)
        self.ink = ink
        tau = np.full((h, w), 1e9, np.float32)
        core = (cv2.GaussianBlur(D, (0, 0), 1.0) > 0.20).astype(np.uint8)
        core = cv2.morphologyEx(core, cv2.MORPH_OPEN, np.ones((2, 2), np.uint8))
        chars = json.load(open(EP + '/assets/tage/poem_chars.json'))
        jobs = []
        for li, line in enumerate(chars):
            ta, tb = LINES_T[li]
            n = len(line['chars']); dc = (tb - ta) / n
            for ci, c in enumerate(line['chars']):
                bx, by, bw, bh = c['box']
                jobs.append(([bx - 35, by - 35, bw + 70, bh + 70], ta + ci * dc, dc * 0.92))
        # 小字「賜王都提舉」一行、两方印
        jobs.append(([2300, 880, 105, 440], T_INSCR[0], T_INSCR[1] - T_INSCR[0]))
        seals = [([2290, 580, 90, 215], T_SEAL[0]), ([2116, 1267, 465, 445], T_SEAL[1])]
        for (bx, by, bw, bh), t0, dur in jobs:
            X0, Y0 = max(0, bx - x0), max(0, by - y0)
            X1, Y1 = min(w, bx + bw - x0), min(h, by + bh - y0)
            cm = core[Y0:Y1, X0:X1].copy()
            n, lab, st, _ = cv2.connectedComponentsWithStats(cm, 8)
            comps = [i for i in range(1, n) if st[i, cv2.CC_STAT_AREA] >= 25]
            if not comps:
                continue
            info = []
            for i in comps:
                ys, xs = np.nonzero(lab == i)
                key = ys.min() + 0.45 * xs.min()
                # 起笔点：左上
                j = np.argmin(ys + 0.6 * xs)
                cost = np.where(lab == i, 1.0, np.inf)
                mcp = MCP_Geometric(cost)
                dist, _ = mcp.find_costs([(ys[j], xs[j])])
                dd = np.where(lab == i, dist, np.nan)
                info.append((key, i, dd, np.nanmax(dd)))
            info.sort(key=lambda r: r[0])
            total = sum(r[3] for r in info) + 1e-6
            lift = 0.035
            v = (dur - lift * (len(info) - 1)) / total          # 秒 / 像素
            v = max(v, 0.2 / total)
            tt = t0
            sub = tau[Y0:Y1, X0:X1]
            for key, i, dd, L in info:
                sel = lab == i
                sub[sel] = np.minimum(sub[sel], tt + dd[sel] * v)
                tt += L * v + lift
        for (bx, by, bw, bh), t0 in seals:
            X0, Y0 = bx - x0, by - y0
            sub = tau[Y0:Y0 + bh, X0:X0 + bw]
            yy = np.linspace(0, 1, bh, dtype=np.float32)[:, None] * np.ones((1, bw), np.float32)
            sub[...] = np.minimum(sub, t0 + 0.06 * yy)
        # 笔画外的淡墨、飞白边：继承最近笔画的时刻（略晚一点 = 墨洇开）
        known = tau < 1e8
        dist, (iy, ix) = ndi.distance_transform_edt(~known, return_indices=True)
        tau = np.where(known, tau, tau[iy, ix] + np.minimum(dist, 30) * 0.004).astype(np.float32)
        self.tau = tau

    def f(self, t):
        if t < T_GHOST[0]:
            return None
        g = 1 - (1 - GHOST) * float(E.sstep(T_GHOST[0], T_GHOST[1], t))
        dt = t - self.tau
        wrote = E.sstep(0.0, 0.09, dt)
        wet = 0.14 * np.exp(-np.clip(dt, 0, None) / 0.35) * (dt > 0)
        return np.clip(g + (1 - g) * wrote + wet, 0, 1.14).astype(np.float32)

    def draw(self, acc, t):
        if t < T_GHOST[0] or t > self.t_end:
            return
        f = self.f(t)
        img = self.S - self.SmP * f[..., None]
        a = self.alpha
        rgba = np.clip(np.concatenate([img * a, a * 255], 2) + 0.5, 0, 255).astype(np.uint8)
        s, c = self.R.layer_xf(t, 1.0, 0.0)
        self.R.draw_image(acc, _pyr(rgba), self.origin, 1.0, s, c)


# ======================================================================
def _poly(pts, sx, sy, ox, oy):
    return np.array([[ox + x / sx, oy + y / sy] for x, y in pts], np.float32)


FIGS = {   # 世界坐标多边形（由 1:1 网格核对图目测，±10 px）
    'jia': dict(amp=60, tilt=1.0, dt=0.0, weak=True, polys=[
        _poly([(185, 110), (240, 75), (330, 60), (385, 95), (420, 175), (560, 175), (645, 215), (695, 260), (700, 420),
               (680, 560), (650, 640), (640, 760), (625, 870), (610, 930), (560, 965), (500, 960), (478, 905), (470, 1020),
               (470, 1110), (425, 1175), (330, 1165), (325, 1100), (300, 1000), (272, 880), (255, 780), (215, 730),
               (160, 700), (110, 640), (60, 600), (35, 545), (95, 480), (140, 430), (160, 330), (175, 220)],
              1.6667, 1.6667, 4060, 11840),
        _poly([(50, 540), (85, 535), (345, 1085), (310, 1100)], 1.6667, 1.6667, 4060, 11840)]),
    'yibing': dict(amp=44, tilt=0.6, dt=0.05, weak=True, polys=[
        _poly([(60, 120), (100, 70), (200, 62), (232, 98), (285, 105), (305, 150), (350, 225), (420, 285), (478, 298),
               (500, 245), (560, 232), (605, 258), (700, 298), (785, 318), (835, 380), (865, 460), (885, 545), (892, 650),
               (865, 700), (875, 772), (810, 792), (762, 762), (742, 722), (732, 792), (722, 852), (608, 852), (598, 800),
               (640, 742), (618, 700), (578, 660), (556, 598), (500, 560), (442, 545), (412, 600), (382, 652), (380, 702),
               (332, 722), (268, 722), (266, 680), (298, 630), (288, 560), (248, 520), (188, 480), (150, 420), (130, 350),
               (100, 302), (38, 300), (18, 232), (38, 180), (48, 132)], 1.0417, 1.0415, 5420, 11860)]),
    'ding': dict(amp=50, tilt=0.8, dt=-0.04, weak=False, polys=[
        _poly([(85, 262), (150, 240), (300, 238), (380, 288), (452, 358), (520, 428), (552, 498), (556, 592), (472, 612),
               (452, 700), (442, 800), (432, 872), (345, 885), (300, 905), (292, 985), (182, 978), (198, 900), (248, 858),
               (250, 790), (160, 742), (76, 702), (78, 600), (100, 522), (62, 452), (78, 362), (88, 300)],
              1.3103, 1.3103, 6480, 11760),
        _poly([(290, 250), (328, 108), (430, 88), (540, 18), (562, 40), (470, 140), (462, 300), (400, 312), (340, 292),
               (305, 282)], 1.3103, 1.3103, 6480, 11760),
        _poly([(0, 468), (100, 404), (112, 432), (0, 522)], 1.3103, 1.3103, 6480, 11760)]),
}
FARM_REG = [3980, 11720, 7120, 12760]


def stomp_h(tau):
    """一次顿足的抬起量（0..1），tau = t − 落脚时刻。抬起 0.30 s（缓出）→ 顶点 → 0.14 s 加速落下 → 落地微沉。"""
    if tau < -0.44 or tau > 0.12:
        return 0.0
    if tau < -0.14:
        u = (tau + 0.44) / 0.30
        return math.sin(u * math.pi / 2)
    if tau < 0:
        u = (tau + 0.14) / 0.14
        return 1 - u * u
    return -0.07 * math.sin(math.pi * tau / 0.12)


class FarmerDance(E._FxBase):
    """三组老农刚体顿足：先画修补底板（人物处用周边地面/绢修补 + 真实绢纹），再画人物精灵（平移 + ≤1° 前后俯仰，支点在脚底）。"""

    def __init__(self, spec, R):
        spec.setdefault('after', 'scroll')
        super().__init__(spec, R)
        x0, y0, x1, y1 = FARM_REG
        src = E._open(SRC)
        P = np.ascontiguousarray(src[y0:y1, x0:x1, :3])
        h, w = P.shape[:2]
        self.parts = []
        union = np.zeros((h, w), np.uint8)
        for name, fg in FIGS.items():
            m = np.zeros((h, w), np.uint8)
            for poly in fg['polys']:
                cv2.fillPoly(m, [np.round(poly - [x0, y0]).astype(np.int32)], 255)
            m = cv2.dilate(m, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (13, 13)))
            union = np.maximum(union, m)
            a = cv2.GaussianBlur(m.astype(np.float32) / 255.0, (0, 0), 3.0)
            ys, xs = np.nonzero(a > 0.004)
            bx0, bx1, by0, by1 = xs.min(), xs.max() + 1, ys.min(), ys.max() + 1
            aa = a[by0:by1, bx0:bx1]
            rgba = np.concatenate([P[by0:by1, bx0:bx1].astype(np.float32) * aa[..., None], aa[..., None] * 255], 2)
            ys2, xs2 = np.nonzero(m > 0)
            foot = np.array([xs2.mean() + x0, ys2.max() + y0], float)
            self.parts.append(dict(lv=_pyr(np.clip(rgba + 0.5, 0, 255).astype(np.uint8)), off=np.array([bx0 + x0, by0 + y0], float),
                                   foot=foot, **{k: fg[k] for k in ('amp', 'tilt', 'dt', 'weak')}))
        # 底板：修补区 = 人物外扩，Telea 修补后叠真实绢纹（取自附近空白绢）
        hole = cv2.dilate(union, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (25, 25)))
        inp = cv2.inpaint(P, hole, 9, cv2.INPAINT_TELEA).astype(np.float32)
        inp = cv2.GaussianBlur(inp, (0, 0), 2.0)
        bk = np.ascontiguousarray(src[200:200 + h, 4900:4900 + min(w, 2700), :3]).astype(np.float32)
        bk = np.tile(bk, (1, w // bk.shape[1] + 1, 1))[:, :w]
        weave = bk - cv2.GaussianBlur(bk, (0, 0), 5)
        inp = inp + 0.9 * weave
        ha = cv2.GaussianBlur(hole.astype(np.float32) / 255.0, (0, 0), 4.0)
        plate = inp * ha[..., None] + P.astype(np.float32) * (1 - ha[..., None])
        ra = np.clip(cv2.dilate(ha, np.ones((9, 9), np.uint8)) * 1.5, 0, 1)
        self.plate = _pyr(np.clip(np.concatenate([plate * ra[..., None], ra[..., None] * 255], 2) + 0.5, 0, 255).astype(np.uint8))
        self.origin = np.array([x0, y0], float)
        self.beats = [(G(b), s) for b, s in BEATS]
        self.t0 = 31.0; self.t1 = DUR + 1
        E.log(f'踏歌：{len(self.parts)} 组人物，{len(self.beats)} 踏')

    def pose(self, p, t):
        hsum, rot = 0.0, 0.0
        for k, (b, strong) in enumerate(self.beats):
            if not strong and not p['weak']:
                continue
            h = stomp_h(t - b - p['dt'])
            if h == 0.0:
                continue
            sc = 1.0 if strong else 0.5
            hsum += h * sc
            rot += h * sc * p['tilt'] * (1 if k % 2 == 0 else -1)
        return hsum * p['amp'], rot

    def draw(self, acc, t):
        if t < self.t0 or t > self.t1:
            return
        s, c = self.R.layer_xf(t, 1.0, 0.0)
        self.R.draw_image(acc, self.plate, self.origin, 1.0, s, c)
        for p in self.parts:
            dy, rot = self.pose(p, t)
            o = p['off'] + np.array([0.0, -dy])
            self.R.draw_image(acc, p['lv'], o, 1.0, s, c, rot_deg=rot, pivot=p['foot'] + np.array([0.0, -dy]))


# ======================================================================
class Multi:
    def __init__(self, spec, res=720):
        self.spec = spec
        self.R = {}
        for name, c in spec['shots'].items():
            seg = dict(spec['seg']); seg['camera'] = c
            seg['fx'] = spec['fx_by'].get(name, [])
            R = E.Renderer(seg, res)
            self.R[name] = R
        self.R['P'].fx.append(PoemWrite({}, self.R['P']))
        self.R['F'].fx.append(FarmerDance({}, self.R['F']))
        r0 = next(iter(self.R.values()))
        self.W, self.H, self.fps, self.nframes = r0.W, r0.H, r0.fps, r0.nframes
        col = real_fog_color(self.W, self.H, r0.lut)
        C = E.curve
        # 叠化雾纱：推拉叠化（横漂）与下降叠化（雾向上掠过）
        self.vz = vz = [[12.6, 0], [14.15, 1], [15.7, 0], [49.7, 0], [51.3, 1], [52.9, 0]]
        lz = [dict(l, lead=0, vy=6 + 4 * i, vx=(-1) ** i * (8 + 4 * i)) for i, l in enumerate(VolFog.LAYERS[1:])]
        lz[0]['amax'] = 0.72; lz[1]['amax'] = 0.64; lz[2]['amax'] = 0.56
        self.veil_z = VolFog(self.W, self.H, col, top=lambda t: -4000, bot=lambda t: 4000,
                             bias=lambda t: -1.2 + 0.52 * C(vz, t), vfac=lambda t: 1.0, P=lambda t: 0.0,
                             t_on=(12.6, 52.9), layers=lz)
        self.vd = vd = [[27.2, 0], [28.75, 1], [30.3, 0], [31.2, 0], [32.75, 1], [34.3, 0]]
        ld = [dict(l, lead=0, vy=-(40 + 14 * i), vx=(-1) ** i * (6 + 3 * i)) for i, l in enumerate(VolFog.LAYERS[1:])]
        ld[0]['amax'] = 0.74; ld[1]['amax'] = 0.66; ld[2]['amax'] = 0.58
        self.veil_d = VolFog(self.W, self.H, col, top=lambda t: -4000, bot=lambda t: 4000,
                             bias=lambda t: -1.2 + 0.56 * C(vd, t), vfac=lambda t: 1.0, P=lambda t: 0.0,
                             t_on=(27.2, 34.3), layers=ld)
        # 中景：宫阙四周的雾在松间漂，浓淡起伏（宫阙若隐若现）；雾带锚在世界坐标 y 5750–6950
        RM = self.R['M']
        H720 = 720.0
        sy = lambda t, wy: float(RM.world_to_screen(t, (5300, wy))[1]) * H720 / self.H
        lm = [dict(l, lead=0, vy=-(38 + 6 * i), vx=(-1) ** i * (10 + 4 * i)) for i, l in enumerate(VolFog.LAYERS[1:])]
        lm[0]['amax'] = 0.42; lm[1]['amax'] = 0.36; lm[2]['amax'] = 0.30
        self.mist_m = VolFog(self.W, self.H, col, top=lambda t: sy(t, 5720), bot=lambda t: sy(t, 6980),
                             bias=lambda t: -0.36 + 0.22 * math.sin(2 * math.pi * (t - 28.6) / 4.2),
                             vfac=lambda t: 1.0, P=lambda t: 0.0, t_on=(27.4, 33.9), layers=lm, L=220.0)
        fake = SimpleNamespace(SS=1, H=self.H, W=self.W, WS=self.W, HS=self.H)
        self.labels = [E.Label(l, fake) for l in spec['labels']]

    def weights(self, t):
        tl = self.spec['timeline']
        w = {tl[0][0]: 1.0}
        for name, a, b in tl[1:]:
            if t < a:
                break
            k = float(E.sstep(a, b, t)) if b > a else 1.0
            w = {n: v * (1 - k) for n, v in w.items() if v * (1 - k) > 1e-4}
            w[name] = k
        return w

    def check(self):
        for n, R in self.R.items():
            E.log(f'镜头 {n}:'); R.check_speed()

    def render(self, t):
        w = self.weights(t)
        fr = None
        for n, k in w.items():
            f = self.R[n].render(t).astype(np.float32)
            fr = f * k if fr is None else fr + f * k      # v2：不画雾（mist_m / veil_z / veil_d 都不用）
        for lb in self.labels:
            lb.draw(fr, t)
        return np.clip(fr + 0.5, 0, 255).astype(np.uint8)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', default=os.path.join(EP, 'segs', 'seg_s2.mp4'))
    ap.add_argument('--res', type=int, default=720)
    ap.add_argument('--frames', default='')
    ap.add_argument('--stills', default='')
    ap.add_argument('--check', action='store_true')
    ap.add_argument('--crf', type=int, default=12)
    a = ap.parse_args()
    spec = build()
    M = Multi(spec, a.res)
    E.log(f's2 踏歌: {M.nframes} 帧 {M.W}x{M.H}@{M.fps:g}，镜头 {list(M.R)}')
    M.check()
    if a.check:
        return
    if a.stills:
        base = os.path.splitext(a.out)[0]
        for i in [int(x) for x in a.stills.split(',') if x]:
            tr = time.time()
            fr = M.render(i / M.fps)
            cv2.imwrite(f'{base}_f{i:04d}.jpg', cv2.cvtColor(fr, cv2.COLOR_RGB2BGR), [cv2.IMWRITE_JPEG_QUALITY, 88])
            E.log(f'still {i} (全局 {T_GLOBAL0 + i / M.fps:.2f}s) {time.time() - tr:.2f}s')
        return
    f0, f1 = (map(int, a.frames.split(':')) if a.frames else (0, M.nframes))
    ff = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{M.W}x{M.H}',
                           '-r', f'{M.fps:g}', '-i', '-', '-c:v', 'libx264', '-preset', 'medium', '-crf', str(a.crf),
                           '-pix_fmt', 'yuv420p', '-movflags', '+faststart', a.out], stdin=subprocess.PIPE)
    tr = time.time()
    for i in range(f0, f1):
        ff.stdin.write(M.render(i / M.fps).tobytes())
        if (i - f0) % 30 == 0:
            E.log(f'frame {i}/{f1}  {(time.time() - tr) / (i - f0 + 1):.2f}s/帧')
    ff.stdin.close(); ff.wait()
    E.log(f'完成 {a.out}  {(time.time() - tr) / max(1, f1 - f0):.2f}s/帧')


if __name__ == '__main__':
    try:
        main()
    except E.EngineError as e:
        print('ENGINE ERROR:', e, file=sys.stderr); sys.exit(2)
