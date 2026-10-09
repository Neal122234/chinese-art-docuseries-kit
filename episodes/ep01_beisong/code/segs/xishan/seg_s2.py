# -*- coding: utf-8 -*-
"""S2 范宽《谿山行旅图》 v2 全局 0:19–1:46（帧 0 = 0:19）。v1 备份：seg_s2_v1.py / beats_v1.json。
v2 的"动"：
  · 驮队逐头走 2.5 个驴身（每头独立刚体起伏）；山脚溪涧、主峰右侧瀑布明显在流
  · 上升穿云：多层体积雾（分层视差、翻卷边缘、明暗体积）从镜头前掠过、吞没；雾面下沉，峰顶先出云，
    烟霞锁腰；主峰由雾中灰淡变浓黑并推近扑面，腰间雾层随推近向外掠过镜头
  · 雨点皴 1:1：按原作像素把墨分三批积出——淡墨如水自上而下漫开，次墨沿山势再漫，浓墨点如雨点逐个落下
  · 名款：四周压暗，一束柔光顺叶间斜落到「范宽」二字上
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
SRC = '~/claude-projects/china-art/trailer/assets_v3/xishan/work_full.npy'   # 24176×11105（高×宽），整轴含裱
SPK = S + '/spike/layers/'
P2O = (560, 3628)
FOG_RECT = [2800, 15200, 2400, 1100]      # 主峰脚下那带空白雾（原图像素 x,y,w,h）
T_GLOBAL0 = 19.0
DUR = 87.0
PR = (6175, 8480)                         # 雨点皴 1:1 的目标点（密点区）
SIG = (9870, 20605)                       # 「范宽」名款 [9830,20520,80,170]


def p2w(x, y):
    return [P2O[0] + 2 * x, P2O[1] + 2 * y]


PAINT = [560, 3628, 560 + 2 * 4975, 3628 + 2 * 9956]


def cam(*keys, rest=None):
    ks = [dict(t=k[0], cx=k[1][0], cy=k[1][1], vh=k[1][2], **({'ease': k[2]} if len(k) > 2 else {})) for k in keys]
    r = rest if rest is not None else ks[-1]
    return {'rest': {'cx': r['cx'], 'cy': r['cy'], 'vh': r['vh']} if 'cx' in r else r, 'keys': ks}


def zoom_about(state, p, k):
    cx, cy, vh = state
    return (p[0] - (p[0] - cx) / k, p[1] - (p[1] - cy) / k, vh / k)


def match_point(state_from, p, vh_new):
    cx, cy, vh = state_from
    return (p[0] - (p[0] - cx) * vh_new / vh, p[1] - (p[1] - cy) * vh_new / vh, vh_new)


# ---- 时间表（段内秒） ----
T_CAR = (15.0, 31.0)          # 驮队行走
T_RISE = (25.5, 37.8)         # 从驮队上升到瀑布/雾带
T_CUT = 38.05                 # 满雾下换到主峰镜头
T_PUSH = (40.3, 46.8)         # 主峰扑面推近
T_R = (45.4, 46.9)            # 叠入 1:1 皴法（裸绢）
T_ACC = 46.3                  # 淡墨开始漫开
T_SIG = (63.8, 66.3, 71.0, 73.2)   # 光落下 / 落定 / 保持到 / 收


def build():
    hs = E.hanging_scroll(SRC, 'xishan', fill_h=0.94)
    F = (hs['full']['cx'], hs['full']['cy'], hs['full']['vh'])
    layers = hs['layers'] + [
        {'name': 'far', 'src': SPK + 'far.npy', 'origin': p2w(-640, -640), 'unit': 2, 'crop': PAINT, 'feather': 80,
         'cache_name': 'xishan_far'},
        {'name': 'cliff', 'src': SPK + 'cliff.npy', 'origin': p2w(-640, 3930), 'unit': 2, 'par': 1.008, 'zpar': 0.01,
         'cache_name': 'xishan_cliff'},
        {'name': 'mid', 'src': SPK + 'mid.npy', 'origin': p2w(-640, 6074), 'unit': 2, 'par': 1.03, 'zpar': 0.03,
         'cache_name': 'xishan_mid'},
        {'name': 'near', 'src': SPK + 'near.npy', 'origin': p2w(-640, 8667), 'unit': 2, 'par': 1.05, 'zpar': 0.06,
         'cache_name': 'xishan_near'},
    ]
    A1 = (F[0], 14500, 22800)
    B0 = (7300, 20950, 3600)                  # 山脚：溪涧 + 路 + 驮队（右侧走出树林）
    B1 = (8350, 20980, 2300)                  # 驮队近景
    C1 = (6950, 13950, 3800)                  # 升到瀑布（右侧整条在画内）与主峰脚下雾带之上
    D0 = (5535, 6700, 5590)                   # 主峰（画宽 = 屏宽），峰顶上留一线天
    D1 = zoom_about(D0, PR, 1.32)             # 扑面推近（向山体腹地）
    R0 = match_point(D1, PR, 1150)
    R1 = (PR[0], PR[1], 760)                  # ≈1:1 @720p
    S0 = (9170, 20300, 1450)
    S1 = (9700, 20605, 900)
    S2 = (S1[0], S1[1], S1[2] * 1.13)
    E0 = zoom_about(F, SIG, 1.12)

    shots = {
        'A': cam((0, F), (12.3, F), (16.3, A1, 1.5), rest=dict(cx=F[0], cy=F[1], vh=F[2])),
        'B': cam((0, B0), (14.3, B0), (25.0, B1, 1.5), (T_RISE[0], B1), (T_RISE[1], C1, 1.8),
                 rest=dict(cx=B1[0], cy=B1[1], vh=B1[2])),
        'D': cam((0, D0), (T_PUSH[0], D0), (T_PUSH[1], D1, 1.3), rest=dict(cx=D0[0], cy=D0[1], vh=D0[2])),
        'R': cam((0, R0), (45.8, R0), (55.3, R1, 1.5)),
        'S': cam((0, S0), (55.3, S0), (65.8, S1, 1.5), (70.3, S1), (74.3, S2, 1.5), rest=dict(cx=S1[0], cy=S1[1], vh=S1[2])),
        'E': cam((0, E0), (72.3, E0), (77.3, F, 1.5), rest=dict(cx=F[0], cy=F[1], vh=F[2])),
    }
    timeline = [('A', 0, 0), ('B', 14.3, 16.3), ('D', T_CUT - 0.05, T_CUT + 0.05), ('R', T_R[0], T_R[1]),
                ('S', 55.3, 56.8), ('E', 72.3, 74.3)]

    fx = [
        # 主峰右侧瀑布：原画像素沿水线向下流（上升穿过时约 40 px/s @720p）
        {'type': 'flow', 'layer': 'far', 'mask': SPK + 'wf_mask.npy', 'origin': p2w(3950, 3200), 'unit': 2,
         'dir': [0, 1], 'speed': 230, 'period': 150, 'streak': 30},
        # 山脚溪涧
        {'type': 'flow', 'layer': 'mid', 'mask': SPK + 'cas_mask.npy', 'origin': p2w(1950, 7750), 'unit': 2,
         'dir': [0, 1], 'speed': 150, 'period': 90, 'streak': 22, 'strength': 0.95},
        # 主峰脚下的烟霞带（画内）
        {'type': 'fog', 'after': 'cliff', 'par': 1.015, 'zpar': 0.02,
         'tex': {'src': SRC, 'rect': FOG_RECT, 'ds': 4},
         'band': [560, 14700, 10510, 16900], 'feather': 500, 'drift': [16, 0], 'rise': [40, 9],
         'opacity': [[0, 0.30], [30, 0.30], [35.5, 0.62], [44, 0.62], [48, 0.30]]},
    ]
    seg_common = {'fps': 30, 'duration': DUR, 'layers': layers, 'fx': fx,
                  'grade': {'gamma': 0.9, 'gain': 1.03}, 'sharpen': 0.25}
    lite = {'R', 'S'}
    label = {'text': ['谿山行旅圖', '北宋　范寬', '絹本淺設色', '二〇六·三×一〇三·三厘米', '臺北故宮博物院藏'],
             'x': 0.87, 'y': 0.14, 't0': 3.5, 't1': 12.3, 'fade': 0.9, 'color': '#2b251d',
             'title_size': 26, 'size': 23}
    return dict(seg=seg_common, shots=shots, timeline=timeline, labels=[label], lite=lite, n_base=len(hs['layers']),
                states=dict(D0=D0, R0=R0, R1=R1))


# ======================================================================
def fbm(n, seed, beta=2.4, fmin=1.5):
    """周期 fBm 噪声（FFT 滤波白噪声），值域约 0..1。"""
    rng = np.random.default_rng(seed)
    w = rng.standard_normal((n, n))
    fy = np.fft.fftfreq(n)[:, None] * n; fx = np.fft.fftfreq(n)[None, :] * n
    f = np.sqrt(fx ** 2 + fy ** 2); f[0, 0] = 1
    amp = f ** (-beta / 2); amp[f < fmin] = 0
    r = np.real(np.fft.ifft2(np.fft.fft2(w) * amp))
    lo, hi = np.percentile(r, [1, 99])
    return np.clip((r - lo) / (hi - lo), 0, 1).astype(np.float32)


def real_fog_color(W, H, lut):
    """雾色 = 原图主峰脚下空白雾的真实像素（提亮、抹掉绢缝），缩到半分辨率屏幕大小。"""
    src = E._open(SRC)
    x, y, w, h = FOG_RECT
    blk = np.ascontiguousarray(src[y:y + h, x:x + w, :3])
    col = cv2.resize(blk, (w // 4, h // 4), interpolation=cv2.INTER_AREA).astype(np.float32)
    col = np.clip(col * 1.24, 0, 255)
    col = cv2.GaussianBlur(col, (0, 0), 12.0)
    col = cv2.LUT(np.clip(col + 0.5, 0, 255).astype(np.uint8), lut).astype(np.float32)
    return cv2.resize(col, (W // 2, H // 2), interpolation=cv2.INTER_AREA)


def cumint(fn, t0, t1, dt=0.01):
    ts = np.arange(t0, t1 + dt, dt)
    v = np.array([fn(t) for t in ts])
    return ts, np.concatenate([[0], np.cumsum((v[1:] + v[:-1]) * 0.5 * dt)])


class VolFog:
    """屏幕空间多层体积雾（半分辨率计算）：每层 = 周期 fBm（横向拉长）+ 域扭曲（边缘翻卷、形状演化）
    + 自上而下的光照明暗（上表面亮、底面暗），颜色取真实雾像素。雾块是一个"雾层板"：
    top/bot 为雾板上下边（输出像素，边缘由噪声翻卷），各层按 lead 先后到达（前景先到先走 → 视差）。
    vy: 层下移速度（px/s，镜头上升时雾向下掠过），P(t): 推近的对数倍率，层按 zr 放大（前景放大更快 → 穿过去）。"""

    LAYERS = [  # 由后到前
        dict(scale=1.7, vy=30, vx=-9, lead=-0.5, amax=1.00, db=0.30, zr=1.2, tint=0.95, seed=3),
        dict(scale=2.3, vy=45, vx=11, lead=-0.15, amax=0.80, db=0.05, zr=1.7, tint=0.98, seed=5),
        dict(scale=3.1, vy=60, vx=-13, lead=0.2, amax=0.72, db=-0.05, zr=2.3, tint=1.05, seed=7),
        dict(scale=4.3, vy=80, vx=16, lead=0.5, amax=0.62, db=-0.12, zr=3.0, tint=1.12, seed=9),
    ]

    def __init__(self, W, H, col, top, bot, bias, vfac, P, t_on, layers=None, L=260.0):
        self.W, self.H = W, H
        self.w2, self.h2 = W // 2, H // 2
        # 1080p：雾场在 720p 参考坐标里定义（top/bot/L/速度/噪声尺度都是 720p 像素），网格按实际分辨率采样
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
        # 速度因子积分（镜头停止上升后雾放慢）
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
class CaravanWalk(E._FxBase):
    """驮队：按连通域拆成每头驴/每个人，各自刚体平移 + 轻微起伏（步态），整体走 path。"""

    def __init__(self, spec, R):
        super().__init__(spec, R)
        s = np.load(spec['sprite'])
        al = s[..., 3]
        m = cv2.morphologyEx((al > 50).astype(np.uint8), cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5)))
        n, lab, st, _ = cv2.connectedComponentsWithStats(m, 8)
        big = [i for i in range(1, n) if st[i, cv2.CC_STAT_AREA] >= 120]
        ds = np.stack([cv2.distanceTransform((lab != i).astype(np.uint8), cv2.DIST_L2, 5) for i in big], 0)
        own = np.argmin(ds, 0)
        self.unit = float(spec.get('unit', 2)); self.origin = np.array(spec['origin'], float)
        self.parts = []
        rng = np.random.default_rng(4)
        for k, i in enumerate(big):
            a = al.astype(np.float32) * (own == k)
            ys, xs = np.nonzero(a > 0)
            if len(xs) == 0:
                continue
            x0, x1, y0, y1 = max(0, xs.min() - 2), min(s.shape[1], xs.max() + 3), max(0, ys.min() - 2), min(s.shape[0], ys.max() + 3)
            rgba = s[y0:y1, x0:x1].astype(np.float32).copy()
            aa = a[y0:y1, x0:x1] / 255.0
            rgba[..., :3] *= aa[..., None]; rgba[..., 3] = aa * 255
            lv = [np.clip(rgba + 0.5, 0, 255).astype(np.uint8)]
            while min(lv[-1].shape[:2]) >= 8:
                lv.append(cv2.resize(lv[-1], (lv[-1].shape[1] // 2, lv[-1].shape[0] // 2), interpolation=cv2.INTER_AREA))
            self.parts.append(dict(lv=lv, off=np.array([x0, y0], float) * self.unit,
                                   foot=np.array([(x0 + x1) / 2, y1], float) * self.unit,
                                   ph=rng.uniform(0, 2 * math.pi), per=rng.uniform(0.85, 1.05)))
        self.path = spec['path']; self.t0, self.t1 = self.path[0][0], self.path[-1][0]
        E.log(f'驮队拆为 {len(self.parts)} 块')

    def offset(self, t):
        (ta, xa, ya), (tb, xb, yb) = self.path[0], self.path[-1]
        k = float(E.sstep(ta, tb, t))
        return np.array([xa + k * (xb - xa), ya + k * (yb - ya)])

    def draw(self, acc, t):
        s, c = self.R.layer_xf(t, self.par, self.zpar)
        off = self.offset(t)
        # 步态幅度随行走速度（smoothstep 导数）
        tau = (t - self.t0) / (self.t1 - self.t0)
        gait = 0.0 if tau <= 0 or tau >= 1 else min(1.0, 6 * tau * (1 - tau) / 1.2)
        for p in self.parts:
            ph = 2 * math.pi * t / p['per'] + p['ph']
            bob = -7.0 * abs(math.sin(ph / 2)) * gait
            rot = 0.8 * math.sin(ph) * gait
            o = self.origin + p['off'] + off + np.array([0, bob])
            self.R.draw_image(acc, p['lv'], o, self.unit, s, c, rot_deg=rot, pivot=self.origin + p['foot'] + off)


# ======================================================================
class InkAccum(E._FxBase):
    """雨点皴一层层积出：原作像素的乘性墨模型 P = S·T（S=裸绢，T=墨透过率），墨深 D=1-T。
    三批：淡墨（D≤L1）如水自上而下漫开；次墨（L1–L2）沿山势再漫；浓墨（>L2）按连通的墨点逐个落下（雨点）。"""

    def __init__(self, spec, R):
        super().__init__(spec, R)
        x0, y0, x1, y1 = [int(v) for v in spec['rect']]
        self.origin = np.array([x0, y0], float)
        src = E._open(SRC)
        P = np.ascontiguousarray(src[y0:y1, x0:x1, :3]).astype(np.float32)
        h, w = P.shape[:2]
        fx, fy, fw, fh = FOG_RECT
        fog = np.ascontiguousarray(src[fy:fy + fh, fx:fx + fw, :3]).astype(np.float32)
        silk = np.median(fog.reshape(-1, 3), 0) * 1.02
        weave = fog - cv2.GaussianBlur(fog, (0, 0), 4)
        reps = (int(math.ceil(h / fh)) + 1, int(math.ceil(w / fw)) + 1)
        rows = [np.concatenate([weave if (j % 2 == 0) else weave[:, ::-1] for j in range(reps[1])], 1) for i in range(reps[0])]
        rows = [r if (i % 2 == 0) else r[::-1] for i, r in enumerate(rows)]
        wv = np.concatenate(rows, 0)[:h, :w]
        Sk = np.clip(silk[None, None, :] + 0.6 * wv, 1, 255).astype(np.float32)
        lum = lambda a: a @ np.float32([0.3, 0.55, 0.15])
        D = np.clip(1 - lum(P) / lum(Sk), 0, 1)
        L1, L2 = np.percentile(D, [45, 80])
        self.S = Sk; self.SmP = (Sk - P).astype(np.float32); self.D = np.maximum(D, 1e-3).astype(np.float32)
        self.segs = [np.clip(D, 0, L1), np.clip(D - L1, 0, L2 - L1), np.clip(D - L2, 0, 1)]
        yy = np.linspace(0, 1, h, dtype=np.float32)[:, None]; xx = np.linspace(0, 1, w, dtype=np.float32)[None, :]
        n1 = cv2.resize(fbm(256, 21, 2.6), (w, h)); n2 = cv2.resize(fbm(256, 22, 2.6), (w, h))
        T0 = float(spec['t0'])
        self.tmaps = [T0 + 1.5 * yy + 0.5 * (n1 - 0.5) + 0 * xx,
                      T0 + 1.3 + 1.3 * (0.65 * yy + 0.35 * (1 - xx)) + 0.5 * (n2 - 0.5)]
        self.durs = [0.8, 0.7, 0.28]
        # 浓墨点：连通域，每点随机落下时刻；大块墨内部用平滑噪声让墨沿块内渗开
        m = (D > L2).astype(np.uint8)
        n, lab, st, _ = cv2.connectedComponentsWithStats(m, 8)
        rng = np.random.default_rng(8)
        r = rng.uniform(0, 1, n).astype(np.float32)
        tdot = r[lab]
        bigc = st[:, cv2.CC_STAT_AREA] > 2500; bigc[0] = False
        nb = cv2.GaussianBlur(rng.uniform(0, 1, (h, w)).astype(np.float32), (0, 0), 22)
        nb = (nb - nb.min()) / (nb.max() - nb.min() + 1e-6)
        tdot = np.where(bigc[lab], nb, tdot)
        tdot = cv2.dilate(tdot, np.ones((3, 3), np.uint8))   # 点的软边与点同时落
        self.tmaps.append(T0 + 2.9 + 2.3 * tdot + 0.25 * yy)
        self.t_end = T0 + 2.9 + 2.3 + 0.25 + 0.3
        # 区域外沿柔边（在视野外）
        fe = 120
        ay = E.sstep(0, fe, np.minimum(np.arange(h), h - 1 - np.arange(h)).astype(np.float32))
        ax = E.sstep(0, fe, np.minimum(np.arange(w), w - 1 - np.arange(w)).astype(np.float32))
        self.alpha = (ay[:, None] * ax[None, :]).astype(np.float32)
        self._cache = None
        E.log(f'积墨区 {w}x{h}，L1={L1:.3f} L2={L2:.3f}，浓墨点 {n - 1} 个')

    def draw(self, acc, t):
        if t > self.t_end:
            return
        if t < self.tmaps[0].min():
            if self._cache is None:
                self._cache = self._rgba(self.S)
            rgba = self._cache
        else:
            Dsh = np.zeros_like(self.D)
            for seg, tm, du in zip(self.segs, self.tmaps, self.durs):
                k = np.clip((t - tm) / du, 0, 1)
                Dsh += (k * k * (3 - 2 * k)) * seg
            f = (Dsh / self.D)[..., None]
            rgba = self._rgba(self.S - self.SmP * f)
        s, c = self.R.layer_xf(t, 1.0, 0.0)
        lv = [rgba]
        while min(lv[-1].shape[:2]) > 64 and len(lv) < 3:
            lv.append(cv2.resize(lv[-1], (lv[-1].shape[1] // 2, lv[-1].shape[0] // 2), interpolation=cv2.INTER_AREA))
        self.R.draw_image(acc, lv, self.origin, 1.0, s, c)

    def _rgba(self, img):
        a = self.alpha[..., None]
        return np.clip(np.concatenate([img * a, a * 255], 2) + 0.5, 0, 255).astype(np.uint8)


# ======================================================================
class SigLight:
    """名款：四周压暗，一束柔光顺叶间斜落（光池从左上沿光束方向滑下、收拢）落到名字上。"""

    def __init__(self, W, H, R, p_world):
        self.W, self.H, self.R, self.p = W, H, R, np.array(p_world, float)
        self.k = H / 720.0                  # 1080p：光池/光束尺寸按 720p 像素写，网格换成 720p 参考坐标
        X, Y = np.meshgrid((np.arange(W, dtype=np.float32) + 0.5) / self.k, (np.arange(H, dtype=np.float32) + 0.5) / self.k)
        self.X, self.Y = X, Y
        ang = math.radians(28)
        self.dir = np.array([-math.sin(ang), -math.cos(ang)])       # 从名字指向光源（左上）
        dap = cv2.resize(fbm(256, 31, 2.2), (W, H))
        self.dapple = (0.55 + 0.9 * (dap - 0.5)).astype(np.float32)
        a, b, c_, d = T_SIG
        self.env = [[a, 0], [b, 1], [c_, 1], [d, 0]]
        self.beam = [[a, 0], [a + 1.2, 1], [b + 0.8, 0.9], [c_, 0.35], [d, 0]]
        self.fall = (a, b)

    def draw(self, fr, t):
        env = E.curve(self.env, t)
        if env <= 1e-3:
            return fr
        p = self.R.world_to_screen(t, self.p) / self.k
        fall = float(E.sstep(self.fall[0], self.fall[1], t))
        pc = p + self.dir * 330 * (1 - fall)
        sx, sy = 62 * (1 + 1.2 * (1 - fall)), 95 * (1 + 0.8 * (1 - fall))
        dx, dy = self.X - pc[0], self.Y - pc[1]
        pool = np.exp(-(dx * dx / (2 * sx * sx) + dy * dy / (2 * sy * sy)))
        # 光束：沿 dir 的软带，只在光池上方
        qx, qy = self.X - p[0], self.Y - p[1]
        along = qx * self.dir[0] + qy * self.dir[1]
        across = qx * self.dir[1] - qy * self.dir[0]
        beam = np.exp(-across * across / (2 * 48.0 ** 2)) * E.sstep(-20, 120, along) * self.dapple
        bm = E.curve(self.beam, t)
        mult = (1 - 0.36 * env * (1 - pool)) * (1 + 0.20 * env * pool)
        fr = fr * mult[..., None]
        warm = np.float32([1.0, 0.93, 0.78])
        fr = fr + (env * pool * 5 + bm * beam * 18)[..., None] * warm
        return fr


def seamless_tall(a):
    """雾带纹理纵向无缝：引擎的 world 雾带在 band 高于纹理时纵向环绕，纹理上下边不连续 → 一条横直线
    （v1 成片在 y≈15800 处可见）。做法同引擎横向：接缝处交叉淡化；再接一份横向错开半宽的同一块雾，
    周期 = 2h−2K（≈1760 世界像素），比雾带实浓区（2200−2×500 羽化）高，看不出重复。"""
    h = a.shape[0]; K = h // 5
    B = np.roll(a, a.shape[1] // 2, axis=1)
    w = np.linspace(0, 1, K, dtype=np.float32).reshape((K,) + (1,) * (a.ndim - 1))
    first = B[h - K:] * (1 - w) + a[:K] * w          # 环绕处：B 底 → A 顶
    mid = a[h - K:] * (1 - w) + B[:K] * w             # A 底 → B 顶
    return np.ascontiguousarray(np.concatenate([first, a[K:h - K], mid, B[K:h - K]], 0).astype(np.float32))


def fix_fog_bands(R):
    for fx in R.fx:
        if isinstance(fx, E.Fog) and fx.mode == 'world' and not getattr(fx, '_tall', False):
            fx.col = seamless_tall(fx.col); fx.dens = seamless_tall(fx.dens); fx._tall = True



# ======================================================================
class Multi:
    def __init__(self, spec, res=720):
        self.spec = spec
        self.R = {}
        for name, c in spec['shots'].items():
            seg = dict(spec['seg']); seg['camera'] = c
            if name in spec.get('lite', ()):
                seg['layers'] = seg['layers'][:spec['n_base']]; seg['fx'] = []
            R = E.Renderer(seg, res)
            fix_fog_bands(R)
            if name not in spec.get('lite', ()):
                R.fx.append(CaravanWalk({'layer': 'mid', 'sprite': SPK + 'caravan.npy', 'origin': p2w(3665, 8615), 'unit': 2,
                                         'path': [[T_CAR[0], 0, 0], [T_CAR[1], -700, 14]]}, R))
            self.R[name] = R
        r0 = next(iter(self.R.values()))
        self.W, self.H, self.fps, self.nframes = r0.W, r0.H, r0.fps, r0.nframes
        st = spec['states']
        R0, R1 = st['R0'], st['R1']
        m = 180
        hw0 = R0[2] * 16 / 9 / 2; hh0 = R0[2] / 2
        rect = [min(R0[0] - hw0, R1[0] - R1[2] * 8 / 9) - m, min(R0[1] - hh0, R1[1] - R1[2] / 2) - m,
                max(R0[0] + hw0, R1[0] + R1[2] * 8 / 9) + m, max(R0[1] + hh0, R1[1] + R1[2] / 2) + m]
        self.R['R'].fx.append(InkAccum({'after': '__top__', 'rect': rect, 't0': T_ACC}, self.R['R']))
        col = real_fog_color(self.W, self.H, r0.lut)
        self.fog_col_mean = col.reshape(-1, 3).mean(0)
        H = 720.0          # VolFog 的 top/bot 用 720p 参考坐标（1080p 由 VolFog 内部换算）
        RD = self.R['D']
        D0vh = st['D0'][2]

        def P(t):
            p = 0.18 * float(E.sstep(31.0, 39.4, t)) + 0.02 * float(E.sstep(39.4, T_PUSH[0], t))
            if t > T_PUSH[0]:
                p += math.log(D0vh / RD.cam.state(t)[1])
            return p

        C = E.curve
        self.fog = VolFog(self.W, self.H, col,
                          top=lambda t: C([[38.0, -200], [40.6, 0.62 * H], [T_PUSH[1], 1.0 * H]], t),
                          bot=lambda t: C([[33.8, -260], [37.6, H + 300], [37.7, 4000]], t),
                          bias=lambda t: C([[45.4, 0.0], [47.0, -1.4]], t),
                          vfac=lambda t: C([[30.5, 0.5], [32.5, 1.0], [39.4, 1.0], [42.0, 0.14]], t),
                          P=P, t_on=(30.5, 47.1))
        veil = [[13.3, 0], [15.3, 1], [17.2, 0], [71.3, 0], [73.3, 1], [75.4, 0]]
        vl = [dict(l, lead=0, vy=6 + 4 * i, vx=(-1) ** i * (8 + 4 * i)) for i, l in enumerate(VolFog.LAYERS[1:])]
        vl[0]['amax'] = 0.7; vl[1]['amax'] = 0.62; vl[2]['amax'] = 0.55
        self.veil = VolFog(self.W, self.H, col, top=lambda t: -4000, bot=lambda t: 4000,
                           bias=lambda t: -1.2 + 0.60 * C(veil, t), vfac=lambda t: 1.0, P=lambda t: 0.0,
                           t_on=(13.3, 75.4), layers=vl)
        self.sig = SigLight(self.W, self.H, self.R['S'], SIG)
        self.haze = [[T_CUT - 0.1, 0.5], [39.0, 0.5], [42.8, 0.1], [45.2, 0.0]]
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
            if n == 'D':   # 主峰从雾中灰淡 → 浓黑（空气透视退去 = 压过来）
                h = E.curve(self.haze, t)
                if h > 1e-3:
                    f = f * (1 - h) + self.fog_col_mean * h
            if n == 'R':   # 1:1 皴法原画很暗：固定支点轻提反差，让墨点层次读得出（不随帧变）
                f = (f - 72.0) * 1.22 + 76.0
            if n == 'S':
                f = self.sig.draw(f, t)
            fr = f * k if fr is None else fr + f * k
        fr = self.fog.draw(fr, t)
        fr = self.veil.draw(fr, t)
        for lb in self.labels:
            lb.draw(fr, t)
        return np.clip(fr + 0.5, 0, 255).astype(np.uint8)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', default=os.path.join(S, 'segs', 'seg_s2.mp4'))
    ap.add_argument('--res', type=int, default=720)
    ap.add_argument('--frames', default='')
    ap.add_argument('--stills', default='')
    ap.add_argument('--check', action='store_true')
    ap.add_argument('--crf', type=int, default=12)
    ap.add_argument('--ss', type=int, default=0)
    a = ap.parse_args()
    spec = build()
    if a.ss:
        spec['seg']['ss'] = a.ss
    M = Multi(spec, a.res)
    E.log(f'S2: {M.nframes} 帧 {M.W}x{M.H}@{M.fps:g}，镜头 {list(M.R)}')
    M.check()
    if a.check:
        return
    if a.stills:
        base = os.path.splitext(a.out)[0]
        for i in [int(x) for x in a.stills.split(',') if x]:
            tr = time.time()
            fr = M.render(i / M.fps)
            cv2.imwrite(f'{base}_f{i:04d}.jpg', cv2.cvtColor(fr, cv2.COLOR_RGB2BGR), [cv2.IMWRITE_JPEG_QUALITY, 88])
            E.log(f'still {i} (全局 {T_GLOBAL0 + i / M.fps:.1f}s) {time.time() - tr:.2f}s')
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
