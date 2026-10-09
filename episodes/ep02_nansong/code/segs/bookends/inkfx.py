# -*- coding: utf-8 -*-
"""片头/片尾扩展（不改 lib/）。第二集副本：自北宋集 segs/bookends/inkfx.py 复制，只在 STROKES 里加了「南」「一」。
- ink   竖排墨字"渗进绢里"：墨从笔画中心先显，沿绢的经纬方向微微洇开；乘法混合，绢纹透过墨色。
- tone  整体明暗曲线（片头灯亮起、片尾灯暗下；不落到纯黑）。
用 run.py 启动（它把这两类 fx 注册进 engine，再调 engine.main）。"""
import os, math
import numpy as np, cv2
import engine as E

FONT_DIR = E.FONT_DIR


def _glyph_column(text, px, weight, lead=1.16):
    """竖排一列，返回覆盖率 (h, w) float32，px = 字号（精灵像素）。"""
    from PIL import Image, ImageDraw, ImageFont
    k = 2                                    # 2× 画再缩回，边缘更顺
    f = ImageFont.truetype(os.path.join(FONT_DIR, f'SourceHanSerifSC-{weight}.otf'), int(round(px * k)))
    pad = int(px * 0.6 * k)
    n = len(text)
    H = int(n * px * lead * k + 2 * pad); W = int(px * k + 2 * pad)
    img = Image.new('L', (W, H), 0); d = ImageDraw.Draw(img)
    y = pad
    for ch in text:
        if ch in ' 　':
            y += px * lead * k * 0.55; continue
        bb = d.textbbox((0, 0), ch, font=f)
        cw = bb[2] - bb[0]
        d.text((pad + (px * k - cw) / 2 - bb[0], y), ch, font=f, fill=255)
        y += px * lead * k
    H2 = int(math.ceil(y + pad))
    a = np.asarray(img, np.float32)[:H2] / 255.0
    a = cv2.resize(a, (a.shape[1] // k, a.shape[0] // k), interpolation=cv2.INTER_AREA)
    return a, pad / k


class Ink(E._FxBase):
    """spec: text, size（720p 字号）, weight, x/y（右上角，屏幕比例，按 rest 相机换成世界坐标，之后随画走）,
    t0（开始渗）, dur（渗完用时，默认 1.5）, out: [ta, tb] 淡出, ink: '#rrggbb', density（0..1）,
    silk: 取纤维纹理的层名（让洇开沿经纬走、墨色随纤维深浅）"""

    def __init__(self, spec, R):
        spec.setdefault('after', '__top__')
        super().__init__(spec, R)
        self.R = R
        SS = R.SS
        s_rest = R.H / R.cam.rest_vh
        self.unit = 1.0 / (SS * s_rest)                 # 精灵 1 px = rest 时 1 个超采样像素
        px = spec.get('size', 30) * SS * R.H / 720.0
        G, pad = _glyph_column(spec['text'], px, spec.get('weight', 'Regular'), spec.get('lead', 1.16))
        h, w = G.shape
        # 右上角锚点（屏幕比例）→ 世界坐标：精灵左上角
        c = R.cam.rest_c
        xr = c[0] + (spec['x'] * R.W - R.W / 2) / s_rest
        yt = c[1] + (spec['y'] * R.H - R.H / 2) / s_rest
        self.origin = np.array([xr - (w - pad) * self.unit, yt - pad * self.unit])
        # 绢纤维（高频）：从 silk 层 L0 取同一块
        F = np.zeros((h, w), np.float32)
        if spec.get('silk') and spec['silk'] in R.by_name:
            L = R.by_name[spec['silk']]
            j0 = (self.origin[0] - L.origin[0]) / L.unit; i0 = (self.origin[1] - L.origin[1]) / L.unit
            sc = self.unit / L.unit
            hh, ww = int(math.ceil(h * sc)) + 2, int(math.ceil(w * sc)) + 2
            ii, jj = int(max(0, i0)), int(max(0, j0))
            blk = np.ascontiguousarray(L.lv[0][ii:ii + hh, jj:jj + ww, :3]).astype(np.float32).mean(2)
            if blk.size:
                blk = cv2.resize(blk, (w, h), interpolation=cv2.INTER_LINEAR)
                hp = blk - cv2.GaussianBlur(blk, (0, 0), 3)
                F = hp / (hp.std() + 1e-6)
        rng = np.random.default_rng(int(spec.get('seed', 5)))
        # 洇：沿经（竖）、纬（横）两个方向的一维扩散，取大者；纤维亮处吸墨多
        sg = px * spec.get('bleed', 0.05)
        Hx = cv2.GaussianBlur(G, (0, 0), sigmaX=sg, sigmaY=0.6)
        Hy = cv2.GaussianBlur(G, (0, 0), sigmaX=0.6, sigmaY=sg)
        Hd = cv2.GaussianBlur(G, (0, 0), sg * 0.45)
        halo = np.maximum(np.maximum(Hx, Hy), Hd) * np.clip(1 + 0.45 * F, 0.2, 2.0)
        halo = np.clip(halo - G, 0, 1)
        # 显现时刻：笔画中心先显 → 边缘；沿列从上到下有先后；再叠一点低频起伏（不成颗粒）
        core = cv2.GaussianBlur(G, (0, 0), px * 0.06)
        core = np.clip(core / (core.max() + 1e-6) * 1.4, 0, 1)
        yy = np.linspace(0, 1, h, dtype=np.float32)[:, None] * np.ones((1, w), np.float32)
        lowv = cv2.GaussianBlur(rng.standard_normal((h, w)).astype(np.float32), (0, 0), px * 0.35)
        lowv /= (lowv.std() + 1e-6)
        order = float(spec.get('order', 0.35))
        tau = order * yy + 0.42 * (1 - core) + 0.06 * lowv
        tau -= tau[G > 0.5].min() if (G > 0.5).any() else tau.min()
        span = float(np.percentile(tau[G > 0.3], 99)) + 0.45 if (G > 0.3).any() else 1.0
        dur = float(spec.get('dur', 1.5))
        self.k = dur / (span + 0.25)                    # 把整体时长缩放到 dur
        self.tau = tau.astype(np.float32)
        # 周边像素继承附近笔画的时刻（归一化卷积），洇晕和先行的淡墨跟着笔画走
        sb = max(2.0, sg * 1.5)
        num = cv2.GaussianBlur(tau * G, (0, 0), sb); den = cv2.GaussianBlur(G, (0, 0), sb)
        self.tau_s = np.where(den > 1e-3, num / np.maximum(den, 1e-3), tau.max()).astype(np.float32)
        # 先行淡墨：比笔画宽、沿经纬散开的湿墨影，随后收成清楚的字
        wet = np.maximum(cv2.GaussianBlur(G, (0, 0), sigmaX=sg * 1.6, sigmaY=sg * 0.5),
                         cv2.GaussianBlur(G, (0, 0), sigmaX=sg * 0.5, sigmaY=sg * 1.6))
        self.wet = np.clip(wet * 1.5, 0, 1) * np.clip(1 + 0.35 * F, 0.4, 1.6)
        self.G, self.halo, self.F = G, halo, F
        self.dens = float(spec.get('density', 0.9)) * np.clip(1 + 0.08 * F, 0.8, 1.15)
        col = spec.get('ink', '#1b1511')
        rgb = np.float32([int(col[i:i + 2], 16) for i in (1, 3, 5)]) / 255.0
        self.mul = (1 - rgb)                            # 乘法混合：acc *= 1 - a*(1-ink)
        self.t0 = float(spec['t0']); self.out = spec.get('out')

    def alpha(self, t):
        u = (t - self.t0) / self.k                      # 规范时间
        if u <= 0:
            return None
        a_core = E.sstep(0.05, 0.5, u - self.tau)
        d = u - self.tau_s
        a_wet = E.sstep(-0.18, 0.2, d) * (1 - 0.75 * E.sstep(0.2, 0.75, d))
        a_halo = E.sstep(0.25, 0.9, d)
        A = np.maximum(self.G * a_core * self.dens, self.wet * a_wet * float(self.spec.get('wet', 0.32)))
        A = np.maximum(A, self.halo * a_halo * float(self.spec.get('halo', 0.22)))
        if self.out:
            A = A * (1 - float(E.sstep(self.out[0], self.out[1], t)))
        return A

    def draw(self, acc, t):
        if not self.active(t):
            return
        A = self.alpha(t)
        if A is None or A.max() < 1e-3:
            return
        R = self.R
        s, c = R.layer_xf(t, self.par, self.zpar)
        SS = R.SS
        a0 = SS * s * self.unit
        bx = SS * (R.W / 2 + s * (self.origin[0] - c[0]))
        by = SS * (R.H / 2 + s * (self.origin[1] - c[1]))
        h, w = A.shape
        X0 = max(0, int(math.floor(bx)) - 2); Y0 = max(0, int(math.floor(by)) - 2)
        X1 = min(R.WS, int(math.ceil(bx + a0 * w)) + 2); Y1 = min(R.HS, int(math.ceil(by + a0 * h)) + 2)
        if X1 <= X0 or Y1 <= Y0:
            return
        M = np.float32([[a0, 0, bx - X0], [0, a0, by - Y0]])
        a = cv2.warpAffine(A.astype(np.float32), M, (X1 - X0, Y1 - Y0), flags=cv2.INTER_LINEAR,
                           borderMode=cv2.BORDER_CONSTANT, borderValue=0)
        roi = acc[Y0:Y1, X0:X1]
        roi *= (1 - a[..., None] * self.mul[None, None, :])


# 楷/宋体「北宋」逐笔中线（1000 px 字号、PIL 画字原点坐标），按笔顺
STROKES = {
    '北': [[(378, 352), (378, 1215)],                                              # 竖
           [(72, 635), (345, 635)],                                                # 横
           [(55, 1070), (200, 1015), (345, 945)],                                  # 提
           [(905, 545), (800, 640), (635, 755)],                                   # 撇
           [(600, 352), (600, 1100), (640, 1160), (760, 1160), (900, 1150), (925, 1100), (925, 980)]],  # 竖弯钩
    '宋': [[(440, 318), (510, 380), (540, 440)],                                   # 点
           [(165, 420), (160, 510), (120, 580), (90, 615)],                        # 左点
           [(180, 485), (860, 485), (920, 495), (840, 560), (795, 615)],           # 横钩
           [(80, 735), (930, 735)],                                                # 横
           [(498, 540), (498, 1215)],                                              # 竖
           [(440, 750), (360, 900), (230, 1060), (45, 1185)],                      # 撇
           [(540, 750), (640, 920), (780, 1060), (945, 1145)]],                    # 捺
    # 第二集（南宋）新增：按思源宋体 Regular 1000 px 实测中线
    '南': [[(60, 465), (935, 465)],                                                # 横
           [(497, 315), (497, 605)],                                               # 竖
           [(175, 585), (175, 1225)],                                              # 竖（左）
           [(212, 612), (830, 612), (858, 648), (845, 700), (845, 1160), (822, 1208), (760, 1225), (700, 1188), (650, 1147)],  # 横折钩
           [(335, 665), (385, 730), (405, 800)],                                   # 点
           [(682, 680), (612, 760), (540, 822)],                                   # 撇
           [(275, 835), (735, 835)],                                               # 横
           [(250, 985), (755, 985)],                                               # 横
           [(497, 825), (497, 1205)]],                                             # 竖
    '一': [[(55, 737), (955, 737)]],                                               # 横
}


def _polyline_param(P, xs, ys):
    """点到折线的最近距离与弧长参数（0..1）"""
    P = np.asarray(P, np.float32)
    seg = np.diff(P, axis=0); L = np.hypot(seg[:, 0], seg[:, 1]); cum = np.concatenate([[0], np.cumsum(L)])
    best_d = np.full(xs.shape, 1e9, np.float32); best_s = np.zeros(xs.shape, np.float32)
    for k in range(len(seg)):
        ax, ay = P[k]; dx, dy = seg[k]
        u = np.clip(((xs - ax) * dx + (ys - ay) * dy) / (L[k] ** 2 + 1e-9), 0, 1)
        d = np.hypot(xs - (ax + u * dx), ys - (ay + u * dy))
        m = d < best_d
        best_d = np.where(m, d, best_d); best_s = np.where(m, (cum[k] + u * L[k]) / cum[-1], best_s)
    return best_d, best_s, float(cum[-1])


class Brush(Ink):
    """「落墨」：按笔顺一笔一笔写出来。笔锋过处墨先湿后定；每笔起笔处墨重、洇得开；
    第一笔落下的一瞬有一团淡墨沿绢的经纬洇开（落墨）；写完后墨沿纤维继续微微洇出（各向异性：沿经纬快、斜向慢，纤维亮处吸墨多）。
    spec 同 ink，另加 speed（字号 1000 单位/秒）、gap（笔间停顿 s）、bloom（落墨晕的半径，字号倍数）。"""

    def __init__(self, spec, R):
        super().__init__(spec, R)
        from PIL import ImageFont
        SS = R.SS
        px = spec.get('size', 30) * SS * R.H / 720.0
        k = 2; lead = spec.get('lead', 1.16)
        pad2 = int(px * 0.6 * k); fs = int(round(px * k))
        f = ImageFont.truetype(os.path.join(FONT_DIR, f"SourceHanSerifSC-{spec.get('weight', 'Regular')}.otf"), fs)
        G = self.G; h, w = G.shape
        yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
        tau = np.full((h, w), 1e3, np.float32)
        spd = float(spec.get('speed', 5000)); gap = float(spec.get('gap', 0.045)); base = 0.03
        t = 0.0; y = pad2; self.starts = []
        core_r = 0.045 * px
        for ch in spec['text']:
            if ch not in STROKES:
                y += px * lead * k; continue
            bb = ImageFont.FreeTypeFont.getbbox(f, ch)
            ox = pad2 + (px * k - (bb[2] - bb[0])) / 2 - bb[0]; oy = y
            near_d = np.full((h, w), 1e9, np.float32); near_t = np.full((h, w), 1e3, np.float32)
            for P in STROKES[ch]:
                Ps = [((ox + gx * fs / 1000.0) / k, (oy + gy * fs / 1000.0) / k) for gx, gy in P]
                d, s, Lp = _polyline_param(Ps, xx, yy)
                dur = base + Lp / (spd * fs / 1000.0 / k)
                tt = t + 0.02 + dur * (s ** 0.92)                     # 起笔略顿，行笔匀
                self.starts.append((t, Ps[0], Lp))
                m = d < near_d                                        # 最近中线归属
                near_d = np.where(m, d, near_d); near_t = np.where(m, tt, near_t)
                cellm = (yy >= (oy - 0.08 * px * k) / k) & (yy < (oy + px * lead * k) / k)
                tau = np.where(cellm & (d < core_r), np.minimum(tau, tt), tau)  # 交叉处：先写到的那笔先显
                t += dur + gap
            cell = (yy >= (oy - 0.08 * px * k) / k) & (yy < (oy + px * lead * k) / k)   # 只管本字的格
            tau = np.where(cell & (G > 0.02) & (tau > 900), near_t, tau)
            y += px * lead * k
            t += 0.06
        self.total = t
        tau = np.where(G > 0.02, tau, 1e3).astype(np.float32)
        self.btau = tau
        # 周边像素继承附近笔画的时刻（洇晕跟着笔走）
        gm = (G > 0.3).astype(np.uint8)
        dist, lab = cv2.distanceTransformWithLabels(1 - gm, cv2.DIST_L1, 3, labelType=cv2.DIST_LABEL_PIXEL)
        ys_, xs_ = np.nonzero(gm)
        lut = np.zeros(lab.max() + 1, np.float32)
        z = np.nonzero(gm.ravel())[0]
        lut_idx = lab.ravel()[z]
        lut[lut_idx] = tau.ravel()[z]
        self.tau_n = lut[lab].astype(np.float32)
        # 各向异性（L1）距离 + 纤维调制：沿经纬洇得远、纤维亮处洇得远
        self.dout = (dist.astype(np.float32) * np.clip(1 - 0.30 * self.F, 0.5, 1.6)).astype(np.float32)
        self.R_bleed = float(spec.get('bleed_px', 0.05)) * px
        # 落墨晕：第一笔起笔处
        t0s, p0, _ = self.starts[0]
        dd = np.hypot(xx - p0[0], (yy - p0[1]) * 0.85) * np.clip(1 - 0.30 * cv2.GaussianBlur(self.F, (0, 0), 1.2), 0.5, 1.6)
        self.bloom_d = dd.astype(np.float32); self.bloom_R = float(spec.get('bloom', 0.55)) * px
        self.bloom_t = t0s
        # 每笔起笔处的重墨晕
        st = np.zeros((h, w), np.float32)
        for (ts, p, Lp) in self.starts:
            st = np.maximum(st, np.exp(-((xx - p[0]) ** 2 + (yy - p[1]) ** 2) / (2 * (0.07 * px) ** 2)))
        self.press = st

    def alpha(self, t):
        tt = t - self.t0
        if tt <= 0:
            return None
        # 笔锋：过处 50 ms 内显出，刚写的墨先湿重（多 8%）再收
        a_core = E.sstep(-0.005, 0.05, tt - self.btau)
        fresh = 1 + 0.10 * (1 - E.sstep(0.05, 0.6, tt - self.btau))
        A = self.G * a_core * self.dens * fresh
        # 洇：写过之后墨沿纤维向外走，半径随时间 1-exp 增长
        s = np.maximum(tt - self.tau_n, 0)
        r = self.R_bleed * (1 + 0.8 * self.press) * (1 - np.exp(-s / 0.45))
        front = E.sstep(-1.5, 1.0, r - self.dout)
        fall = np.clip(1 - self.dout / (self.R_bleed * 1.8 + 1e-6), 0, 1) ** 1.3
        halo = front * fall * float(self.spec.get('halo', 0.16)) * np.clip(1 + 0.7 * self.F, 0.2, 2.0)
        halo *= (tt > self.tau_n)
        A = np.maximum(A, halo * (1 - self.G))
        # 落墨：第一笔落下时，一团淡墨在 0.3 s 内沿经纬洇开，留成淡淡的湿痕
        sb = tt - self.bloom_t
        if sb > 0:
            rb = self.bloom_R * (1 - np.exp(-sb / 0.16))
            fb = E.sstep(-2.0, 1.5, rb - self.bloom_d)
            ring = np.exp(-((self.bloom_d - rb) / (0.06 * self.bloom_R + 1e-6)) ** 2) * (1 - E.sstep(0.2, 0.9, sb))
            dry = 1 - 0.35 * E.sstep(0.3, 2.2, sb)                  # 湿痕慢慢干浅
            body = np.clip(1 - self.bloom_d / (self.bloom_R * 1.05), 0, 1) ** 0.6
            edge = np.exp(-((self.bloom_d - rb) / (0.07 * self.bloom_R + 1e-6)) ** 2)   # 水痕：湿前沿留下的深一线
            ab = fb * (0.24 * body * dry + 0.16 * edge * E.sstep(0.05, 0.25, sb)) * np.clip(1 + 0.7 * self.F, 0.25, 2.0)
            ab += 0.5 * np.exp(-(self.bloom_d / (0.10 * self.bloom_R)) ** 2) * E.sstep(0.0, 0.06, sb)  # 笔尖落点
            ab *= float(self.spec.get('bloom_gain', 1.0))            # 第二集新增：小字把落墨晕压淡（默认 1 = 原样）
            A = np.maximum(A, ab)
        if self.out:
            A = A * (1 - float(E.sstep(self.out[0], self.out[1], t)))
        return A.astype(np.float32)


class Tone(E._FxBase):
    """整体明暗：gain 曲线 [[t,g],...]（1 = 原样）。只做亮度，不改色相；不会到纯黑。"""

    def __init__(self, spec, R):
        spec.setdefault('after', '__top__')
        super().__init__(spec, R)

    def draw(self, acc, t):
        g = E.curve(self.spec['gain'], t)
        if abs(g - 1) > 1e-4:
            acc *= np.float32(g)


def register():
    orig = E.make_fx
    if getattr(orig, '_bookends', False):
        return

    def make_fx(spec, R):
        if spec['type'] == 'ink':
            return Ink(spec, R)
        if spec['type'] == 'brush':
            return Brush(spec, R)
        if spec['type'] == 'tone':
            return Tone(spec, R)
        return orig(spec, R)
    make_fx._bookends = True
    E.make_fx = make_fx
