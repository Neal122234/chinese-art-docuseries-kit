# -*- coding: utf-8 -*-
"""第二集 S1 李唐《万壑松风图》 全局 7–56 s（帧 0 = 全局 7 s，49 s，1470 帧）。
世界坐标 = work/wanhe_scroll.npy（拼接大图逐行校正梯形后的矩形立轴，含上下隔水），由 rectify.py 生成。
结构：全貌挂墙（静 10 s，展签）→ 读画缓推主峰 → 干净叠化 1.4 s → 主峰崖壁近景（淡墨底）
      → 斧劈高光：浓墨按侧锋方向一斧一斧落下（揭原作之墨，湿前沿急起缓停、落点压一下再回）
      → 干净叠化 1.0 s → 中央瀑布近景（瀑布流）→ 干净叠化 1.0 s → 拉回全貌，全貌静止到段尾。
v2（2026-09-29）：按用户意见"本集不用雾"，去掉三次云雾掠过（VEIL1–3），换景别只剩下面 XF1–3 的叠化，画始终可见；
    瀑布近景上方的松间云带（半透明盖住画的上部）也去掉，瀑布照常流（带云带版代码 work/seg_s1_v2_cloud.py.bak）。
v1 带雾版本：work/seg_s1_v1_fog.py.bak。
速度检查：  lockf -k $S/.heavy.lock python3 seg_s1.py --check
抽帧：      lockf -k $S/.heavy.lock python3 seg_s1.py --stills 100,400 --out work/s.png
成片：      nohup lockf -k $S/.heavy.lock python3 seg_s1.py --out ../seg_s1.mp4 > render.log 2>&1 &
"""
import sys, os, math, time, argparse, subprocess
from types import SimpleNamespace
import numpy as np, cv2

S = '~/claude-projects/china-art/series'
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, S + '/lib'); sys.path.insert(0, HERE)
import engine as E
import xishan_lib as X          # 北宋溪山段代码的副本（只借 VolFog / fbm）

SRC = HERE + '/work/wanhe_scroll.npy'      # 6286×4290（高×宽）
PGA = S + '/ep02_nansong/assets/wanhe/full/K2A000896N000000000PGA.jpg'   # 连裱整轴照片：天头/地头的真实绫
T_GLOBAL0 = 7.0
ALPHA = 0.36                               # 斧劈前主峰的墨只剩原作的 36%（淡墨底）
DUR = 49.0
CLOUD_BAND = False                         # v2：不画松间云带（本集不用雾）
CLOUD_RECT = [2650, 2330, 450, 420]        # 主峰右下大白云（空绢）
SILK_RECT = [2560, 960, 520, 170]          # 画顶空白天空绢
CLIFF_C = (1850, 1480)
WF = (2690, 3180)                          # 中央瀑布中段

# ---- 时间表（段内秒）----
T_READ = (10.0, 18.8)
VEIL1 = (18.2, 20.0, 21.9); XF1 = (19.3, 20.7)
T_PUSHC = (21.0, 34.6)
T_AXE = (26.3, 33.7)                       # 全局 33.3–40.7
VEIL2 = (34.0, 35.4, 37.2); XF2 = (34.9, 35.9)
T_PUSHW = (36.0, 40.0)
VEIL3 = (38.7, 39.7, 41.4); XF3 = (39.2, 40.2)
T_BACK = (39.6, 42.0)                      # 全局 46.6–49 回到全貌，之后静止


def zoom_about(state, p, k):
    cx, cy, vh = state
    return (p[0] - (p[0] - cx) / k, p[1] - (p[1] - cy) / k, vh / k)


def cam(*keys, rest=None):
    ks = [dict(t=k[0], cx=k[1][0], cy=k[1][1], vh=k[1][2], **({'ease': k[2]} if len(k) > 2 else {})) for k in keys]
    r = rest if rest is not None else ks[-1]
    return {'rest': {'cx': r['cx'], 'cy': r['cy'], 'vh': r['vh']}, 'keys': ks}


def build():
    H, W = E._open(SRC).shape[:2]
    samples = [(PGA, [520, 60, 1740, 540]), (PGA, [520, 2700, 1740, 2930])]
    hs = E.hanging_scroll(SRC, 'wanhe', fill_h=0.93, samples=samples, tex_scale=5.2)
    F = (hs['full']['cx'], hs['full']['cy'], hs['full']['vh'])
    A1 = zoom_about(F, (1900, 1650), 1.36)
    C0 = (CLIFF_C[0], CLIFF_C[1], 1150)
    C1 = (1880, 1500, 930)
    W0 = (2700, 3020, 1060)
    W1 = (2700, 3000, 1190)
    E0 = zoom_about(F, WF, 1.07)
    Fd = dict(cx=F[0], cy=F[1], vh=F[2])
    shots = {
        'A': cam((0, F), (T_READ[0], F), (T_READ[1], A1, 1.8), rest=Fd),
        'C': cam((0, C0), (T_PUSHC[0], C0), (T_PUSHC[1], C1, 2.0)),
        'W': cam((0, W0), (T_PUSHW[0], W0), (T_PUSHW[1], W1, 1.2)),
        'E': cam((0, E0), (T_BACK[0], E0), (T_BACK[1], F, 1.0), rest=Fd),
    }
    timeline = [('A', 0, 0), ('C', *XF1), ('W', *XF2), ('E', *XF3)]
    fx = [
        {'type': 'flow', 'layer': 'scroll', 'mask': HERE + '/work/wf_mask_up.npy', 'origin': [2540, 2990], 'unit': 1,
         'dir': [-0.55, 0.84], 'speed': 62, 'period': 60, 'streak': 20, 'strength': 1.0},
        {'type': 'flow', 'layer': 'scroll', 'mask': HERE + '/work/wf_mask_lo.npy', 'origin': [2540, 2990], 'unit': 1,
         'dir': [0.03, 1.0], 'speed': 70, 'period': 60, 'streak': 20, 'strength': 1.0, 'seed': 13},
    ]
    seg_common = {'fps': 30, 'duration': DUR, 'layers': hs['layers'], 'fx': fx,
                  'grade': {'gamma': 0.86, 'gain': 1.05}, 'sharpen': 0.25}
    label = {'text': ['萬壑松風圖', '北宋　李唐', '絹本設色', '一八八·七×一三九·八厘米', '臺北故宮博物院藏'],
             'x': 0.87, 'y': 0.14, 't0': 1.5, 't1': 9.8, 'fade': 0.9, 'color': '#2b251d',
             'title_size': 26, 'size': 23}
    return dict(seg=seg_common, shots=shots, timeline=timeline, labels=[label],
                states=dict(F=F, A1=A1, C0=C0, C1=C1, W0=W0, W1=W1, E0=E0))


# ======================================================================
def make_wf_masks():
    """中央瀑布遮罩：沿水路折线的走廊 × 比周围亮的水线（原作的淡色水纹），上下两折分开（方向不同）。"""
    pu = HERE + '/work/wf_mask_up.npy'; pl = HERE + '/work/wf_mask_lo.npy'
    if os.path.exists(pu) and os.path.exists(pl):
        return
    x0, y0, x1, y1 = 2540, 2990, 2800, 3600
    blk = np.ascontiguousarray(E._open(SRC)[y0:y1, x0:x1]).astype(np.float32)
    lum = blk @ np.float32([0.3, 0.55, 0.15])
    loc = lum - cv2.GaussianBlur(lum, (0, 0), 10)
    bright = E.sstep(1.5, 10.0, loc)
    h, w = lum.shape
    up = np.zeros((h, w), np.uint8); lo = np.zeros((h, w), np.uint8)
    P1 = np.int32([[2752, 3025], [2700, 3075], [2660, 3140], [2625, 3200], [2600, 3262], [2590, 3335]]) - [x0, y0]
    P2 = np.int32([[2600, 3430], [2605, 3500], [2610, 3585]]) - [x0, y0]
    cv2.polylines(up, [P1], False, 255, 56); cv2.polylines(lo, [P2], False, 255, 50)
    for m, p in ((up, pu), (lo, pl)):
        c = cv2.GaussianBlur(m.astype(np.float32) / 255, (0, 0), 7)
        a = np.clip(c * (0.25 + 0.9 * bright), 0, 1)
        a = cv2.GaussianBlur(a, (0, 0), 1.2).astype(np.float32)
        np.save(p, a)


# ======================================================================
class AxeReveal(E._FxBase):
    """斧劈：原作像素的乘性墨模型 P = S·T（S=裸绢，D=1−lum(P)/lum(S) 为墨深）。
    淡墨（D≤L1）一开始就在：主峰只剩淡淡的山形。随后浓墨按"斧"落下：
    浓墨连通块按所在"块面"（抖动网格 ~300 px）归入一斧；每斧沿该处笔触的长轴方向（结构张量）由上向下扫，
    湿前沿急起缓停（0.24 s，ease-out），扫完落点再压深约 25% 后回到原作（顿挫）；次墨跟随附近的斧、软前沿。"""

    def __init__(self, spec, R, view_fn):
        super().__init__(spec, R)
        x0, y0, x1, y1 = [int(v) for v in spec['rect']]
        self.origin = np.array([x0, y0], float)
        src = E._open(SRC)
        P = np.ascontiguousarray(src[y0:y1, x0:x1, :3]).astype(np.float32)
        h, w = P.shape[:2]
        sx, sy, sw, sh = SILK_RECT
        sk = np.ascontiguousarray(src[sy:sy + sh, sx:sx + sw, :3]).astype(np.float32)
        silk = np.median(sk.reshape(-1, 3), 0) * 1.03
        weave = sk - cv2.GaussianBlur(sk, (0, 0), 4)
        reps = (int(math.ceil(h / sh)) + 1, int(math.ceil(w / sw)) + 1)
        rows = [np.concatenate([weave if (j % 2 == 0) else weave[:, ::-1] for j in range(reps[1])], 1) for i in range(reps[0])]
        rows = [r if (i % 2 == 0) else r[::-1] for i, r in enumerate(rows)]
        wv = np.concatenate(rows, 0)[:h, :w]
        Sk = np.clip(silk[None, None, :] + 0.6 * wv, 1, 255).astype(np.float32)
        lum = lambda a: a @ np.float32([0.3, 0.55, 0.15])
        D = np.clip(1 - lum(P) / lum(Sk), 0, 1).astype(np.float32)
        ink = D[D > 0.06]
        L1, L2 = np.percentile(ink, [24, 58])
        self.S = Sk; self.SmP = (Sk - P).astype(np.float32)
        self.invD = np.where(D > 0.02, 1.0 / np.maximum(D, 0.02), 0).astype(np.float32)
        self.always = (D <= 0.02).astype(np.float32)
        self.wash = np.clip(D, 0, L1).astype(np.float32)
        self.mid = np.clip(D - L1, 0, L2 - L1).astype(np.float32)
        self.dark = np.clip(D - L2, 0, 1).astype(np.float32)
        self.isdark = (self.dark > 0).astype(np.float32)
        # ---- 斧：抖动网格块面 ----
        rng = np.random.default_rng(24)
        SP = 300
        gy, gx = np.mgrid[SP // 2:h:SP, SP // 2:w:SP]
        seeds = np.stack([gx.ravel(), gy.ravel()], 1).astype(np.float32)
        seeds += rng.uniform(-0.32, 0.32, seeds.shape) * SP
        ds = 4
        yy, xx = np.mgrid[0:h:ds, 0:w:ds].astype(np.float32)
        # 块面边界不走直线：坐标先用平滑噪声扭一扭（边界随墨势弯折）
        hh, ww = xx.shape
        xx = xx + 95 * (cv2.resize(X.fbm(128, 71, 3.0), (ww, hh)) - 0.5) * 2
        yy = yy + 95 * (cv2.resize(X.fbm(128, 72, 3.0), (ww, hh)) - 0.5) * 2
        d2 = (xx[..., None] - seeds[:, 0]) ** 2 + ((yy[..., None] - seeds[:, 1]) * 1.15) ** 2
        cell_s = np.argmin(d2, -1).astype(np.int32)
        cellpix = cv2.resize(cell_s.astype(np.float32), (w, h), interpolation=cv2.INTER_NEAREST).astype(np.int32)
        m = (self.dark > 0).astype(np.uint8)
        n, lab, st, cen = cv2.connectedComponentsWithStats(m, 8)
        cx = np.clip(cen[:, 0].round().astype(int), 0, w - 1); cy = np.clip(cen[:, 1].round().astype(int), 0, h - 1)
        blobcell = cellpix[cy, cx]
        big = st[:, cv2.CC_STAT_AREA] > 0.35 * SP * SP
        cell = np.where(big[lab], cellpix, blobcell[lab]).astype(np.int32)
        cell[m == 0] = -1
        # 每斧方向：结构张量（梯度垂直于笔触长轴）
        Dg = cv2.GaussianBlur(D, (0, 0), 2.0)
        gxm = cv2.Sobel(Dg, cv2.CV_32F, 1, 0, ksize=3); gym = cv2.Sobel(Dg, cv2.CV_32F, 0, 1, ksize=3)
        K = len(seeds)
        idx = cellpix.ravel()
        Jxx = np.bincount(idx, (gxm * gxm).ravel(), K); Jyy = np.bincount(idx, (gym * gym).ravel(), K)
        Jxy = np.bincount(idx, (gxm * gym).ravel(), K)
        th = 0.5 * np.arctan2(2 * Jxy, Jxx - Jyy) + np.pi / 2      # 笔触长轴
        dirs = np.stack([np.cos(th), np.sin(th)], 1)
        flip = (dirs[:, 1] < 0) | ((np.abs(dirs[:, 1]) < 0.3) & (dirs[:, 0] < 0))
        dirs[flip] *= -1
        # 每斧的时间：可见的斧一拍一拍（~0.36 s），视野外的斧挤在一起
        Y, Xg = np.mgrid[0:h, 0:w]
        cnt = np.bincount(cell[cell >= 0], minlength=K)
        key = seeds[:, 1] + 0.45 * seeds[:, 0] + rng.normal(0, 110, K)
        order = [k for k in np.argsort(key) if cnt[k] > 0]
        vx0, vy0, vx1, vy1 = view_fn(sum(T_AXE) / 2)
        tcur, ts = 0.0, {}
        for k in order:
            wx, wy = seeds[k] + self.origin
            vis = vx0 + 80 < wx < vx1 - 80 and vy0 + 60 < wy < vy1 - 60 and cnt[k] > 400
            tcur += (0.36 + rng.uniform(-0.07, 0.07)) if vis else 0.03
            ts[k] = tcur
        scale = (T_AXE[1] - T_AXE[0] - 0.3) / max(tcur, 1e-6)
        tstart = np.full(K, 1e9, np.float32)
        for k, v in ts.items():
            tstart[k] = T_AXE[0] + (v - (ts[order[0]])) * scale
        self.nvis = sum(1 for k in order if ts[k] and True)
        # 沿方向坐标（每斧归一到 0..1）→ 前沿到达时刻（ease-out：前沿位置 f(τ)=1−(1−τ)²）
        DUR_AX = 0.24
        Tdark = np.full((h, w), 1e9, np.float32); Tend = np.full((h, w), 1e9, np.float32)
        for k in order:
            sel = cell == k
            ys_, xs_ = np.nonzero(sel)
            if len(xs_) == 0:
                continue
            a = (xs_ - seeds[k, 0]) * dirs[k, 0] + (ys_ - seeds[k, 1]) * dirs[k, 1]
            lo_, hi_ = np.percentile(a, [1, 99])
            an = np.clip((a - lo_) / max(hi_ - lo_, 1), 0, 1)
            tau = 1 - np.sqrt(1 - an)
            Tdark[ys_, xs_] = tstart[k] + DUR_AX * tau
            Tend[ys_, xs_] = tstart[k] + DUR_AX
        self.Tdark = Tdark; self.Tend = Tend
        # 次墨时间：附近浓墨时间的归一化卷积（平滑，无硬边）
        wgt = (Tdark < 1e8).astype(np.float32)
        tv = np.where(wgt > 0, Tdark, 0).astype(np.float32)
        num = cv2.GaussianBlur(tv, (0, 0), 32); den = cv2.GaussianBlur(wgt, (0, 0), 32)
        num2 = cv2.GaussianBlur(tv, (0, 0), 110); den2 = cv2.GaussianBlur(wgt, (0, 0), 110)
        tfb = np.where(den2 > 1e-3, num2 / np.maximum(den2, 1e-6), sum(T_AXE) / 2)
        a_ = np.clip(den / 0.25, 0, 1)
        self.Tmid = (a_ * (num / np.maximum(den, 1e-6)) + (1 - a_) * tfb).astype(np.float32)
        self.Tmid = np.where(den > 1e-4, self.Tmid, tfb).astype(np.float32) - 0.04
        self.t_first = float(min(self.Tdark.min(), self.Tmid.min()))
        self.t_end = float(max(self.Tend[self.Tend < 1e8].max(), self.Tmid.max())) + 0.9
        fe = 140
        ay = E.sstep(0, fe, np.minimum(np.arange(h), h - 1 - np.arange(h)).astype(np.float32))
        ax = E.sstep(0, fe, np.minimum(np.arange(w), w - 1 - np.arange(w)).astype(np.float32))
        self.alpha = (ay[:, None] * ax[None, :]).astype(np.float32)
        self._cache = None
        self.beats = sorted(set(round(float(tstart[k]) + DUR_AX, 2) for k in order
                                if vx0 < seeds[k, 0] + x0 < vx1 and vy0 < seeds[k, 1] + y0 < vy1))
        E.log(f'斧劈区 {w}x{h}，L1={L1:.3f} L2={L2:.3f}，块面 {len(order)}（视野内 {len(self.beats)}），'
              f'{self.t_first:.2f}–{self.t_end:.2f}s')

    def frac(self, t):
        """每像素显出比例：淡墨底 ALPHA（原作浓淡按比例变淡，结构都在）→ 1；浓墨尖前沿 + 落点压深，其余软前沿。"""
        km = np.clip((t - self.Tmid) / 0.24, 0, 1); km = km * km * (3 - 2 * km)
        kd = np.clip((t - self.Tdark) / 0.05, 0, 1)
        tau = np.maximum(t - self.Tend, 0)
        press = 1 + 0.30 * np.exp(-tau / 0.2) * (1 - np.exp(-tau / 0.03))
        k = km + self.isdark * (kd * press - km)
        return ALPHA + (1 - ALPHA) * k

    def draw(self, acc, t):
        if t > self.t_end:
            return
        if t < self.t_first:
            if self._cache is None:
                self._cache = self._rgba(self.S - self.SmP * ALPHA)
            rgba = self._cache
        else:
            rgba = self._rgba(self.S - self.SmP * self.frac(t)[..., None])
        s, c = self.R.layer_xf(t, 1.0, 0.0)
        lv = [rgba]
        while min(lv[-1].shape[:2]) > 64 and len(lv) < 3:
            lv.append(cv2.resize(lv[-1], (lv[-1].shape[1] // 2, lv[-1].shape[0] // 2), interpolation=cv2.INTER_AREA))
        self.R.draw_image(acc, lv, self.origin, 1.0, s, c)

    def _rgba(self, img):
        a = self.alpha[..., None]
        return np.clip(np.concatenate([np.clip(img, 0, 255) * a, a * 255], 2) + 0.5, 0, 255).astype(np.uint8)


def fog_color(W, H, lut):
    src = E._open(SRC)
    x, y, w, h = CLOUD_RECT
    blk = np.ascontiguousarray(src[y:y + h, x:x + w, :3])
    col = cv2.resize(blk, (w // 2, h // 2), interpolation=cv2.INTER_AREA).astype(np.float32)
    col = col * 1.5
    lm = col.mean(2, keepdims=True)
    col = np.clip(lm + 0.6 * (col - lm), 0, 255)
    col = cv2.GaussianBlur(col, (0, 0), 8.0)
    col = cv2.LUT(np.clip(col + 0.5, 0, 255).astype(np.uint8), lut).astype(np.float32)
    return cv2.resize(col, (W // 2, H // 2), interpolation=cv2.INTER_AREA)


# ======================================================================
class Multi:
    def __init__(self, spec, res=720):
        self.spec = spec
        self.R = {}
        for name, c in spec['shots'].items():
            seg = dict(spec['seg']); seg['camera'] = c
            if name in ('A',):
                seg['fx'] = []
            self.R[name] = E.Renderer(seg, res)
        r0 = self.R['A']
        self.W, self.H, self.fps, self.nframes = r0.W, r0.H, r0.fps, r0.nframes
        st = spec['states']
        RC = self.R['C']

        def view(t, m=1.0):
            (cx, cy), vh = RC.cam.state(t)
            return (cx - vh * 8 / 9 * m, cy - vh / 2 * m, cx + vh * 8 / 9 * m, cy + vh / 2 * m)
        C0 = st['C0']; mg = 170
        rect = [C0[0] - C0[2] * 8 / 9 - mg, C0[1] - C0[2] / 2 - mg, C0[0] + C0[2] * 8 / 9 + mg, C0[1] + C0[2] / 2 + mg]
        self.axe = AxeReveal({'after': '__top__', 'rect': rect}, RC, view)
        RC.fx.append(self.axe)
        col = fog_color(self.W, self.H, r0.lut)
        C = E.curve
        base = X.VolFog.LAYERS[1:]

        def veil(win, amax=(0.78, 0.7, 0.62), vy=(8, 12, 16), seed0=0):
            a, b, c_ = win
            vl = [dict(l, lead=0, vy=vy[i], vx=(-1) ** i * (9 + 5 * i), amax=amax[i], seed=l['seed'] + seed0)
                  for i, l in enumerate(base)]
            cv = [[a, 0], [b, 1], [c_, 0]]
            return X.VolFog(self.W, self.H, col, top=lambda t: -4000, bot=lambda t: 4000,
                            bias=lambda t: -1.2 + 0.72 * C(cv, t), vfac=lambda t: 1.0, P=lambda t: 0.0,
                            t_on=(a, c_), layers=vl)
        self.veils = []      # v2：不用雾，换景别只靠 XF1–3 干净叠化（v1 为 veil(VEIL1/2/3)）
        # 松间云气：瀑布近景上方的云带（屏幕上沿），横向漂移 ~20–30 px/s
        cl = [dict(l, lead=0, vy=0, vx=v, amax=am, seed=l['seed'] + 60)
              for l, v, am in zip(base, (18, 26, 34), (0.55, 0.45, 0.38))]
        self.cloud = X.VolFog(self.W, self.H, col, top=lambda t: -300, bot=lambda t: 290,
                              bias=lambda t: -0.62 + 0.0 * t, vfac=lambda t: 1.0, P=lambda t: 0.0,
                              t_on=(XF2[0], XF3[1]), layers=cl, L=170.0)
        self.cloud_env = [[XF2[0], 0], [XF2[1], 1], [XF3[0], 1], [XF3[1], 0]]
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
            if n == 'C':      # 近景原画很暗：固定支点轻提反差（不随帧变）
                f = (f - 70.0) * 1.22 + 74.0
            if n == 'W':
                f = (f - 70.0) * 1.10 + 72.0
                ce = E.curve(self.cloud_env, t) if CLOUD_BAND else 0.0
                if ce > 1e-3:
                    g = self.cloud.draw(f.copy(), t)
                    f = f * (1 - ce) + g * ce
            fr = f * k if fr is None else fr + f * k
        for v in self.veils:
            fr = v.draw(fr, t)
        for lb in self.labels:
            lb.draw(fr, t)
        return np.clip(fr + 0.5, 0, 255).astype(np.uint8)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', default=os.path.join(HERE, '..', 'seg_s1.mp4'))
    ap.add_argument('--res', type=int, default=720)
    ap.add_argument('--frames', default='')
    ap.add_argument('--stills', default='')
    ap.add_argument('--check', action='store_true')
    ap.add_argument('--crf', type=int, default=12)
    a = ap.parse_args()
    make_wf_masks()
    spec = build()
    M = Multi(spec, a.res)
    E.log(f'S1: {M.nframes} 帧 {M.W}x{M.H}@{M.fps:g}，镜头 {list(M.R)}，斧落点 {M.axe.beats}')
    M.check()
    if a.check:
        return
    if a.stills:
        base = os.path.splitext(a.out)[0]
        for i in [int(x) for x in a.stills.split(',') if x]:
            tr = time.time()
            fr = M.render(i / M.fps)
            cv2.imwrite(f'{base}_f{i:04d}.jpg', cv2.cvtColor(fr, cv2.COLOR_RGB2BGR), [cv2.IMWRITE_JPEG_QUALITY, 90])
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
