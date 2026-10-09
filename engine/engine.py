# -*- coding: utf-8 -*-
# 【工具包说明】2.5D 画中游渲染引擎：段文件（layers/camera/fx/labels）→ 逐帧合成 → ffmpeg 出 mp4；自带运镜速度检查。
# 输入：段 .py/.json（世界坐标 = 主图原图像素）、大图 .npy/.png；输出：mp4 或抽帧 png。详见同目录 ENGINE.md。
# 环境变量：FONT_DIR（思源宋体目录，缺省本机 china-art/trailer/fonts）、ENGINE_CACHE（mip 缓存，缺省 engine/cache/）、CHINA_ART_ROOT。
# 跑法：python3 engine/engine.py seg.py out.mp4 [--res 720|1080] [--frames a:b] [--stills 0,45] [--check]（重活走全局锁）。
"""中国艺术分集 · 2.5D 画中游渲染引擎（五个分段共用）。说明见同目录 ENGINE.md。

CLI:
  python3 lib/engine.py SEG.py OUT.mp4 [--res 720|1080] [--frames a:b] [--stills 0,45,120] [--check]
重活必须走全局锁：lockf -k series/.heavy.lock python3 lib/engine.py ...
"""
import os, sys, json, math, time, hashlib, argparse, subprocess, importlib.util
import numpy as np, cv2

LIB = os.path.dirname(os.path.abspath(__file__))
SERIES = os.path.dirname(LIB)
CACHE = os.environ.get('ENGINE_CACHE', os.path.join(LIB, 'cache'))      # mip 缓存（大，勿入库）
FONT_DIR = os.environ.get('FONT_DIR', os.path.join(os.environ.get('CHINA_ART_ROOT', '~/claude-projects/china-art'),
                                                   'trailer', 'fonts'))   # 思源宋体 SourceHanSerifSC-*.otf
T0 = time.time()
LIMIT_PAN_720 = 6.0      # px/frame @720p，硬上限
LIMIT_ZOOM = 6.0         # %/s
MIN_EASE = 1.0           # s，每端缓入缓出
MAX_TILT_DEG = 1.0


class EngineError(Exception):
    pass


def log(*a):
    print(f'[{time.time() - T0:6.1f}s]', *a, flush=True)


def sstep(e0, e1, x):
    t = np.clip((np.asarray(x, np.float32) - e0) / (e1 - e0 + 1e-9), 0, 1)
    return t * t * (3 - 2 * t)


# ======================================================================
# mip 缓存：大图按行分块做金字塔，磁盘 npy + mmap，渲染时只读可见区域
# ======================================================================
def _key(*parts):
    h = hashlib.md5()
    for p in parts:
        if isinstance(p, str) and os.path.exists(p):
            st = os.stat(p); h.update(f'{os.path.abspath(p)}|{st.st_size}|{st.st_mtime}'.encode())
        else:
            h.update(repr(p).encode())
    return h.hexdigest()[:10]


def _open(src):
    if isinstance(src, np.ndarray):
        return src
    if src.endswith('.npy'):
        return np.load(src, mmap_mode='r')
    im = cv2.imread(src, cv2.IMREAD_UNCHANGED)
    if im is None:
        raise EngineError(f'读不到图: {src}')
    if im.ndim == 2:
        im = cv2.cvtColor(im, cv2.COLOR_GRAY2RGB)
    elif im.shape[2] == 4:
        im = cv2.cvtColor(im, cv2.COLOR_BGRA2RGBA)
    else:
        im = cv2.cvtColor(im, cv2.COLOR_BGR2RGB)
    return im


def build_mips(src, name=None, premult=True, min_side=48, chunk=2048):
    """src: npy 路径 / 图片路径 / ndarray (H,W,3|4 uint8)。RGBA 视为直通 alpha，缓存为预乘。
    返回 [L0, L1, ...]（memmap）。L0 若为 RGB npy 直接 mmap 源文件，不复制。"""
    arr = _open(src)
    tag = name or (os.path.splitext(os.path.basename(src))[0] if isinstance(src, str) else 'arr')
    d = os.path.join(CACHE, 'mips', f'{tag}_{_key(src if isinstance(src, str) else arr.shape, premult)}')
    os.makedirs(d, exist_ok=True)
    levels = []
    C = arr.shape[2]
    # L0
    if C == 3 and isinstance(src, str) and src.endswith('.npy'):
        L0 = arr
    else:
        p0 = os.path.join(d, 'L0.npy')
        if not os.path.exists(p0):
            out = np.lib.format.open_memmap(p0 + '.tmp.npy', 'w+', np.uint8, arr.shape)
            for r in range(0, arr.shape[0], chunk):
                b = np.ascontiguousarray(arr[r:r + chunk])
                if C == 4 and premult:
                    a = b[..., 3:4].astype(np.uint16)
                    b = b.copy(); b[..., :3] = ((b[..., :3].astype(np.uint16) * a + 127) // 255).astype(np.uint8)
                out[r:r + chunk] = b
            out.flush(); del out; os.replace(p0 + '.tmp.npy', p0)
        L0 = np.load(p0, mmap_mode='r')
    levels.append(L0)
    lv = 1
    while min(levels[-1].shape[:2]) // 2 >= min_side:
        p = os.path.join(d, f'L{lv}.npy')
        prev = levels[-1]
        h2, w2 = prev.shape[0] // 2, prev.shape[1] // 2
        if not os.path.exists(p):
            out = np.lib.format.open_memmap(p + '.tmp.npy', 'w+', np.uint8, (h2, w2, C))
            for r in range(0, h2 * 2, chunk):
                b = np.ascontiguousarray(prev[r:min(r + chunk, h2 * 2), :w2 * 2])
                out[r // 2:r // 2 + b.shape[0] // 2] = cv2.resize(b, (w2, b.shape[0] // 2), interpolation=cv2.INTER_AREA).reshape(-1, w2, C)
            out.flush(); del out; os.replace(p + '.tmp.npy', p)
        levels.append(np.load(p, mmap_mode='r'))
        lv += 1
    return levels


# ======================================================================
# 相机：画面（世界）坐标；状态 (cx, cy, vh)，vh = 屏幕高度对应的世界像素
# 两关键帧之间按相似变换的对数插值（缩放对数匀速、围绕不动点），梯形速度曲线缓入缓出
# ======================================================================
class Camera:
    def __init__(self, spec, fps):
        self.fps = fps
        ks = spec['keys']
        self.keys = []
        for k in ks:
            self.keys.append(dict(t=float(k['t']), c=np.array([k['cx'], k['cy']], float), vh=float(k['vh']),
                                  ease=k.get('ease')))
        for a, b in zip(self.keys, self.keys[1:]):
            if b['t'] <= a['t']:
                raise EngineError(f'相机关键帧时间必须递增: {a["t"]} → {b["t"]}')
        r = spec.get('rest', ks[0])
        self.rest_c = np.array([r['cx'], r['cy']], float); self.rest_vh = float(r['vh'])
        self.moves = []
        for a, b in zip(self.keys, self.keys[1:]):
            same = np.allclose(a['c'], b['c']) and abs(a['vh'] - b['vh']) < 1e-6
            T = b['t'] - a['t']
            e = b['ease'] if b['ease'] is not None else min(1.5, T / 2.0)
            if not same and e < MIN_EASE - 1e-6:
                raise EngineError(f'{a["t"]:.2f}–{b["t"]:.2f}s 缓入缓出 {e:.2f}s < {MIN_EASE}s（段太短或 ease 太小）')
            e = min(e, T / 2.0)
            self.moves.append((a, b, same, e))

    @staticmethod
    def _u(tau, T, r):
        """梯形速度曲线（每端 r 秒线性加/减速），返回 0..1"""
        if r <= 1e-9:
            return tau / T
        v = 1.0 / (T - r)
        if tau < r:
            return v * tau * tau / (2 * r)
        if tau < T - r:
            return v * (r / 2 + (tau - r))
        t2 = T - tau
        return 1 - v * t2 * t2 / (2 * r)

    def state(self, t):
        ks = self.keys
        if t <= ks[0]['t']:
            return ks[0]['c'].copy(), ks[0]['vh']
        for a, b, same, e in self.moves:
            if t <= b['t']:
                if same:
                    return a['c'].copy(), a['vh']
                u = self._u(t - a['t'], b['t'] - a['t'], e)
                return interp_sim(a['c'], a['vh'], b['c'], b['vh'], u)
        return ks[-1]['c'].copy(), ks[-1]['vh']


def interp_sim(c0, vh0, c1, vh1, u):
    """相似变换插值：vh 对数插值；若有缩放，则围绕不动点缩放（屏幕上无额外漂移）。"""
    k = vh1 / vh0
    if abs(math.log(k)) < 1e-9:
        return c0 + (c1 - c0) * u, vh0
    # 屏幕 q = s (p - c)，s = 1/vh（相对）。不动点 p*: (p*-c0)/vh0 = (p*-c1)/vh1
    ps = (vh0 * c1 - vh1 * c0) / (vh0 - vh1)
    vh = vh0 * k ** u
    c = ps + (c0 - ps) * (vh / vh0)
    return c, vh


# ======================================================================
# 层
# ======================================================================
class Layer:
    """spec: name, src, origin[x,y]（世界坐标，层像素(0,0)左上角）, unit（世界像素/层像素）,
    par（视差系数，1=随画面；>1 近景移动更快）, zpar（推拉视差，默认 0）, crop[x0,y0,x1,y1]+feather（世界坐标）,
    opacity（常数或 [[t,a],...]）, t0/t1 可见时段"""

    def __init__(self, spec):
        self.spec = spec
        self.name = spec['name']
        self.lv = build_mips(spec['src'], name=spec.get('cache_name', self.name))
        self.origin = np.array(spec.get('origin', [0, 0]), float)
        self.unit = float(spec.get('unit', 1.0))
        self.par = float(spec.get('par', 1.0))
        self.zpar = float(spec.get('zpar', 0.0))
        self.crop = spec.get('crop'); self.feather = float(spec.get('feather', 0))
        self.C = self.lv[0].shape[2]

    def opacity(self, t):
        return curve(self.spec.get('opacity', 1.0), t)


def curve(v, t):
    """常数，或 [[t,val],...] 分段 smoothstep 插值"""
    if not isinstance(v, (list, tuple)):
        return float(v)
    if t <= v[0][0]:
        return float(v[0][1])
    for (ta, a), (tb, b) in zip(v, v[1:]):
        if t <= tb:
            return float(a + (b - a) * sstep(ta, tb, t))
    return float(v[-1][1])


class Renderer:
    def __init__(self, seg, res=720):
        self.seg = seg
        self.H = int(res); self.W = int(round(self.H * 16 / 9 / 2) * 2)
        self.SS = int(seg.get('ss', 2))
        self.WS, self.HS = self.W * self.SS, self.H * self.SS
        self.fps = float(seg.get('fps', 30))
        self.dur = float(seg['duration'])
        self.nframes = int(round(self.dur * self.fps))
        self.cam = Camera(seg['camera'], self.fps)
        self.layers = [Layer(s) for s in seg['layers']]
        self.by_name = {L.name: L for L in self.layers}
        self.fx = [make_fx(f, self) for f in seg.get('fx', [])]
        self.labels = [Label(l, self) for l in seg.get('labels', [])]
        g = seg.get('grade', {})
        gam, gain, lift = g.get('gamma', 1.0), g.get('gain', 1.0), g.get('lift', 0.0)
        x = np.arange(256) / 255.0
        self.lut = np.clip(255 * (lift + (1 - lift) * gain * x ** gam), 0, 255).astype(np.uint8)
        self.sharpen = float(seg.get('sharpen', 0.25))

    # ---- 变换 ----
    def layer_xf(self, t, par=1.0, zpar=0.0):
        """返回 (s, c)：屏幕(输出像素) q = (W/2,H/2) + s*(p - c)"""
        c, vh = self.cam.state(t)
        s = self.H / vh
        s_ref = self.H / self.cam.rest_vh
        sL = s * (s / s_ref) ** zpar
        cL = self.cam.rest_c + par * (s / sL) * (c - self.cam.rest_c)
        return sL, cL

    def world_to_screen(self, t, p, par=1.0, zpar=0.0):
        s, c = self.layer_xf(t, par, zpar)
        return np.array([self.W / 2, self.H / 2]) + s * (np.asarray(p, float) - c)

    # ---- 速度检查 ----
    def check_speed(self, verbose=True):
        n = self.nframes
        pars = sorted(set([(L.par, L.zpar) for L in self.layers] + [(1.0, 0.0)]))
        k720 = 720.0 / self.H
        bad = []
        pan_max, zoom_max = 0.0, 0.0
        prev = None
        for i in range(n + 1):
            t = i / self.fps
            st = [self.layer_xf(t, p, z) for p, z in pars]
            if prev is not None:
                for (s0, c0), (s1, c1) in zip(prev, st):
                    # 屏幕中心处画面点的位移
                    p = c0
                    q1 = s1 * (p - c1)
                    pan = float(np.hypot(*q1)) * k720
                    zoom = abs(math.log(s1 / s0)) * self.fps * 100
                    pan_max = max(pan_max, pan); zoom_max = max(zoom_max, zoom)
                    if pan > LIMIT_PAN_720 + 1e-6 or zoom > LIMIT_ZOOM + 1e-6:
                        bad.append((t, pan, zoom))
            prev = st
        if verbose:
            log(f'速度检查: 平移峰值 {pan_max:.2f} px/帧@720p（限 {LIMIT_PAN_720}），推拉峰值 {zoom_max:.2f} %/s（限 {LIMIT_ZOOM}）')
        if bad:
            runs, cur = [], [bad[0]]
            for b in bad[1:]:
                if b[0] - cur[-1][0] <= 1.5 / self.fps:
                    cur.append(b)
                else:
                    runs.append(cur); cur = [b]
            runs.append(cur)
            msg = '; '.join(f'{r[0][0]:.2f}–{r[-1][0]:.2f}s 平移峰 {max(x[1] for x in r):.2f}px/帧 推拉峰 {max(x[2] for x in r):.2f}%/s' for r in runs)
            raise EngineError('超速: ' + msg)
        return pan_max, zoom_max

    # ---- 单层绘制 ----
    def draw_image(self, acc, lv, origin, unit, s, c, crop=None, feather=0.0, opacity=1.0, rot_deg=0.0, pivot=None):
        """把金字塔 lv 画进 acc（SS 分辨率，float32 预乘）。"""
        SS = self.SS
        A0 = SS * s * unit
        f = math.log2(1.0 / A0) if A0 < 1 else 0.0
        l = min(int(math.floor(f)), len(lv) - 1)
        frac = f - l
        r = self._warp_level(lv, l, origin, unit, s, c, crop, feather, rot_deg, pivot)
        if r is None:
            return
        if frac > 0.6 and l + 1 < len(lv):
            w = (frac - 0.6) / 0.4
            r2 = self._warp_level(lv, l + 1, origin, unit, s, c, crop, feather, rot_deg, pivot, roi=r[0])
            if r2 is not None:
                r = (r[0], cv2.addWeighted(r[1], 1 - w, r2[1], w, 0))
        (x0, y0, x1, y1), img = r
        roi = acc[y0:y1, x0:x1]
        a = img[..., 3:4] * (opacity / 255.0)
        roi *= (1.0 - a)
        roi += img[..., :3] * opacity

    def _warp_level(self, lv, l, origin, unit, s, c, crop, feather, rot_deg, pivot, roi=None):
        SS, W, H = self.SS, self.W, self.H
        img = lv[l]; u = unit * 2 ** l
        h, w = img.shape[:2]
        A = SS * s * u
        bx = SS * (W / 2 + s * (origin[0] + 0.5 * u - c[0])) - 0.5
        by = SS * (H / 2 + s * (origin[1] + 0.5 * u - c[1])) - 0.5
        # 可见区域 → 层像素范围
        if roi is None:
            x0, y0, x1, y1 = 0, 0, self.WS, self.HS
        else:
            x0, y0, x1, y1 = roi
        pad = 3 + (abs(rot_deg) > 0) * 0.03 * max(x1 - x0, y1 - y0) / max(A, 1e-6)
        j0 = max(0, int(math.floor((x0 - bx) / A - pad))); j1 = min(w, int(math.ceil((x1 - bx) / A + pad)) + 1)
        i0 = max(0, int(math.floor((y0 - by) / A - pad))); i1 = min(h, int(math.ceil((y1 - by) / A + pad)) + 1)
        if j1 <= j0 or i1 <= i0:
            return None
        sub = np.ascontiguousarray(img[i0:i1, j0:j1])
        if sub.shape[2] == 3:
            sub = np.concatenate([sub, np.full(sub.shape[:2] + (1,), 255, np.uint8)], 2)
        if crop is not None:
            m = self._crop_mask(crop, feather, origin, u, i0, i1, j0, j1)
            sub = (sub.astype(np.float32) * m[..., None]).astype(np.uint8)
        # 目标 ROI
        ox, oy = bx + A * j0, by + A * i0
        if roi is None:
            X0 = max(0, int(math.floor(ox - A))); X1 = min(self.WS, int(math.ceil(ox + A * (j1 - j0))) + 1)
            Y0 = max(0, int(math.floor(oy - A))); Y1 = min(self.HS, int(math.ceil(oy + A * (i1 - i0))) + 1)
            if abs(rot_deg) > 0:
                X0, Y0, X1, Y1 = max(0, X0 - 8), max(0, Y0 - 8), min(self.WS, X1 + 8), min(self.HS, Y1 + 8)
        else:
            X0, Y0, X1, Y1 = roi
        if X1 <= X0 or Y1 <= Y0:
            return None
        M = np.float64([[A, 0, ox - X0], [0, A, oy - Y0]])
        if abs(rot_deg) > 0:
            px, py = pivot  # 世界坐标
            qx = SS * (W / 2 + s * (px - c[0])) - X0; qy = SS * (H / 2 + s * (py - c[1])) - Y0
            R = cv2.getRotationMatrix2D((qx, qy), -rot_deg, 1.0)
            M = np.vstack([R, [0, 0, 1]]) @ np.vstack([M, [0, 0, 1]])
            M = M[:2]
        out = cv2.warpAffine(sub, M.astype(np.float32), (X1 - X0, Y1 - Y0), flags=cv2.INTER_LINEAR,
                             borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0, 0))
        return (X0, Y0, X1, Y1), out.astype(np.float32)

    @staticmethod
    def _crop_mask(crop, feather, origin, u, i0, i1, j0, j1):
        xs = origin[0] + (np.arange(j0, j1) + 0.5) * u
        ys = origin[1] + (np.arange(i0, i1) + 0.5) * u
        fe = max(feather, 1e-3)
        mx = sstep(0, fe, np.minimum(xs - crop[0], crop[2] - xs))
        my = sstep(0, fe, np.minimum(ys - crop[1], crop[3] - ys))
        return (my[:, None] * mx[None, :]).astype(np.float32)

    def draw_layer(self, acc, L, t):
        sp = L.spec
        if 't0' in sp and t < sp['t0'] or 't1' in sp and t > sp['t1']:
            return
        op = L.opacity(t)
        if op <= 0.002:
            return
        s, c = self.layer_xf(t, L.par, L.zpar)
        self.draw_image(acc, L.lv, L.origin, L.unit, s, c, L.crop, L.feather, op)

    # ---- 一帧 ----
    def render(self, t):
        acc = np.zeros((self.HS, self.WS, 3), np.float32)
        bg = self.seg.get('background', [200, 190, 165])   # 只在所有层都未覆盖处出现；呈现模式应保证被墙纸覆盖
        acc[:] = np.float32(bg)
        after = {}
        for fx in self.fx:
            after.setdefault(fx.after, []).append(fx)
        for fx in after.get('__bottom__', []):
            fx.draw(acc, t)
        for L in self.layers:
            self.draw_layer(acc, L, t)
            for fx in after.get(L.name, []):
                fx.draw(acc, t)
        for fx in after.get('__top__', []):
            fx.draw(acc, t)
        for lb in self.labels:
            lb.draw(acc, t)
        fr = cv2.resize(acc, (self.W, self.H), interpolation=cv2.INTER_AREA)
        if self.sharpen > 0:
            bl = cv2.GaussianBlur(fr, (0, 0), 0.9)
            fr = fr + self.sharpen * (fr - bl)
        fr = np.clip(fr + 0.5, 0, 255).astype(np.uint8)
        return cv2.LUT(fr, self.lut)


# ======================================================================
# 局部活化
# ======================================================================
def periodic_noise(h, w, sy, sx, seed):
    r = np.random.default_rng(seed).standard_normal((h, w)).astype(np.float32)
    n = cv2.GaussianBlur(np.tile(r, (3, 3)), (0, 0), sigmaX=sx, sigmaY=sy)[h:2 * h, w:2 * w]
    return (n - n.mean()) / (n.std() + 1e-6)


def make_fx(spec, R):
    k = spec['type']
    if k == 'flow':
        return Flow(spec, R)
    if k == 'drift':
        return Drift(spec, R)
    if k == 'fog':
        return Fog(spec, R)
    raise EngineError(f'未知 fx 类型 {k}')


class _FxBase:
    def __init__(self, spec, R):
        self.spec, self.R = spec, R
        self.after = spec.get('after', spec.get('layer', '__top__'))
        par = spec.get('par'); zpar = spec.get('zpar')
        if 'layer' in spec and spec['layer'] in R.by_name:
            L = R.by_name[spec['layer']]
            par = L.par if par is None else par; zpar = L.zpar if zpar is None else zpar
        self.par = 1.0 if par is None else float(par); self.zpar = 0.0 if zpar is None else float(zpar)

    def active(self, t):
        sp = self.spec
        return not ('t0' in sp and t < sp['t0'] or 't1' in sp and t > sp['t1'])


class Flow(_FxBase):
    """遮罩内沿方向的纹理流动。用原画自己的像素做双相位平移（周期 period 世界像素，交叉淡化无跳变），
    外加沿方向滚动的细长亮纹（streak）。spec:
      mask: npy(float 0..1) 路径, origin: 世界坐标, unit: 世界像素/遮罩像素,
      src: 与遮罩同尺寸的 RGB npy（可省：从 layer 的 L0 裁；要求 layer.unit==unit）,
      dir: [dx,dy], speed: 世界像素/秒, period: 世界像素, streak: 亮度幅度(0..40), strength: 0..1"""

    def __init__(self, spec, R):
        super().__init__(spec, R)
        m = np.load(spec['mask']).astype(np.float32) if isinstance(spec['mask'], str) else spec['mask'].astype(np.float32)
        self.origin = np.array(spec['origin'], float); self.unit = float(spec.get('unit', 1))
        if spec.get('src') is not None:
            src = _open(spec['src'])
            if 'src_rect' in spec:
                x, y, w, h = spec['src_rect']; src = src[y:y + h, x:x + w]
            tex = np.ascontiguousarray(src[..., :3]).astype(np.float32)
        else:
            L = R.by_name[spec['layer']]
            if abs(L.unit - self.unit) > 1e-6:
                raise EngineError('flow: 省略 src 时遮罩 unit 必须等于层 unit')
            j = int(round((self.origin[0] - L.origin[0]) / L.unit)); i = int(round((self.origin[1] - L.origin[1]) / L.unit))
            tex = np.ascontiguousarray(L.lv[0][i:i + m.shape[0], j:j + m.shape[1], :3]).astype(np.float32)
            if L.C == 4:   # 预乘 → 反预乘
                a = np.ascontiguousarray(L.lv[0][i:i + m.shape[0], j:j + m.shape[1], 3:4]).astype(np.float32) / 255
                tex = tex / np.maximum(a, 1e-3)
        d = np.array(spec.get('dir', [0, 1]), float); self.dir = d / np.linalg.norm(d)
        self.speed = float(spec.get('speed', 60)); self.period = float(spec.get('period', 48))
        self.streak = float(spec.get('streak', 18)); self.strength = float(spec.get('strength', 1.0))
        self.noise = periodic_noise(1024, 64, 9, 1.6, int(spec.get('seed', 11)))
        self.pyr = [(tex, m)]
        while min(self.pyr[-1][1].shape) >= 16:
            t_, m_ = self.pyr[-1]
            sz = (m_.shape[1] // 2, m_.shape[0] // 2)
            self.pyr.append((cv2.resize(t_, sz, interpolation=cv2.INTER_AREA), cv2.resize(m_, sz, interpolation=cv2.INTER_AREA)))

    def draw(self, acc, t):
        if not self.active(t):
            return
        R = self.R
        s, c = R.layer_xf(t, self.par, self.zpar)
        A0 = R.SS * s * self.unit
        l = 0 if A0 >= 1 else min(int(math.floor(math.log2(1 / A0))), len(self.pyr) - 1)
        tex, m = self.pyr[l]; u = self.unit * 2 ** l
        h, w = m.shape
        ph = self.speed * t / u; P = self.period / u
        out = np.zeros_like(tex)
        for off in (0.0, 0.5):
            f = (ph / P + off) % 1.0
            wgt = 1 - abs(2 * f - 1)
            dx, dy = self.dir * f * P
            M = np.float32([[1, 0, dx], [0, 1, dy]])
            out += wgt * cv2.warpAffine(tex, M, (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
        # 沿方向滚动的细亮纹
        yy, xx = np.mgrid[0:h, 0:w].astype(np.float32) * u
        along = (xx * self.dir[0] + yy * self.dir[1] - self.speed * t) / 2.0
        across = (-xx * self.dir[1] + yy * self.dir[0]) / 2.0
        n = cv2.remap(self.noise, (across % 64).astype(np.float32), (along % 1024).astype(np.float32),
                      cv2.INTER_LINEAR, borderMode=cv2.BORDER_WRAP)
        out += (self.streak * np.clip(0.55 * n + 0.15, -0.9, 1.6))[..., None] * np.float32([1.0, 0.98, 0.92])
        a = np.clip(m * self.strength, 0, 1)
        rgba = np.concatenate([np.clip(out, 0, 255) * a[..., None], a[..., None] * 255], 2)
        rgba = np.clip(rgba, 0, 255).astype(np.uint8)
        R.draw_image(acc, [rgba], self.origin, u, s, c)


class Drift(_FxBase):
    """刚体小位移（驴队、船）。sprite: RGBA（直通 alpha）npy/png；origin/unit；
    path: [[t,dx,dy],...] 世界像素偏移（分段 smoothstep）；tilt: {'deg':≤1,'period':s}；
    body: 身长（世界像素），位移超过一个身长报错。父层需已是"干净底板"（精灵原位置已用绢纹补好）。"""

    def __init__(self, spec, R):
        super().__init__(spec, R)
        self.lv = build_mips(spec['sprite'], name=spec.get('cache_name', 'sprite_' + os.path.basename(str(spec['sprite']))))
        self.origin = np.array(spec['origin'], float); self.unit = float(spec.get('unit', 1))
        self.path = spec.get('path', [[0, 0, 0]])
        tl = spec.get('tilt', {}); self.tdeg = float(tl.get('deg', 0)); self.tper = float(tl.get('period', 5))
        if abs(self.tdeg) > MAX_TILT_DEG:
            raise EngineError(f'drift 起伏角 {self.tdeg}° > {MAX_TILT_DEG}°')
        h, w = self.lv[0].shape[:2]
        body = float(spec.get('body', w * self.unit))
        mx = max(math.hypot(p[1], p[2]) for p in self.path)
        if mx > body + 1e-6:
            raise EngineError(f'drift 位移 {mx:.0f} > 一个身长 {body:.0f}（世界像素）')
        self.pivot = self.origin + np.array([w, h]) * self.unit / 2

    def offset(self, t):
        p = self.path
        if t <= p[0][0]:
            return np.array(p[0][1:], float)
        for a, b in zip(p, p[1:]):
            if t <= b[0]:
                k = float(sstep(a[0], b[0], t))
                return np.array(a[1:], float) + k * (np.array(b[1:], float) - np.array(a[1:], float))
        return np.array(p[-1][1:], float)

    def draw(self, acc, t):
        if not self.active(t):
            return
        s, c = self.R.layer_xf(t, self.par, self.zpar)
        off = self.offset(t)
        rot = self.tdeg * math.sin(2 * math.pi * t / self.tper) if self.tdeg else 0.0
        self.R.draw_image(acc, self.lv, self.origin + off, self.unit, s, c, rot_deg=rot, pivot=self.pivot + off)


class Fog(_FxBase):
    """真实绢/雾像素做的云雾层。tex: {'src': npy, 'rect':[x,y,w,h] 源像素, 'ds': 缩小倍数}
    模式 'world'：雾带在世界坐标 band=[x0,y0,x1,y1] 内（上下 feather 柔边，左右无缝环绕），随 par 视差；
    模式 'screen'：满屏（转场用），scale = 纹理像素→屏幕高度比例。
    drift: [vx,vy] 世界(或屏幕高度比例)/秒；rise: [幅度, 周期s]；opacity: 常数或曲线；
    cover: 曲线 0..1——0=按真实雾的浓淡局部出现，1=整屏被雾吞没（显示真实雾/绢像素）。"""

    def __init__(self, spec, R):
        super().__init__(spec, R)
        tx = spec['tex']
        src = _open(tx['src'])
        x, y, w, h = tx['rect']; ds = int(tx.get('ds', 4))
        blk = np.ascontiguousarray(src[y:y + h, x:x + w, :3])
        col = cv2.resize(blk, (w // ds, h // ds), interpolation=cv2.INTER_AREA).astype(np.float32)
        lum = col.mean(2)
        dens = cv2.GaussianBlur(lum, (0, 0), max(2.0, col.shape[1] / 60))
        lo, hi = np.percentile(dens, [8, 92])
        dens = np.clip((dens - lo) / (hi - lo + 1e-6), 0, 1)
        # 左右无缝：尾部与头部交叉淡化
        K = col.shape[1] // 6
        wv = np.linspace(0, 1, K, dtype=np.float32)
        col[:, :K] = col[:, :K] * wv[None, :, None] + col[:, -K:] * (1 - wv[None, :, None]); col = col[:, :-K]
        dens[:, :K] = dens[:, :K] * wv[None, :] + dens[:, -K:] * (1 - wv[None, :]); dens = dens[:, :-K]
        # 雾色 = 真实雾/绢像素，按 lighten 提亮（雾比底下的山更亮）
        lift = float(spec.get('lighten', 1.18))
        self.col = np.clip(col * lift, 0, 255)
        self.col = cv2.GaussianBlur(self.col, (0, 0), float(spec.get('soften', 1.2)))
        self.dens = dens
        self.ds = ds
        self.mode = spec.get('mode', 'world')
        self.band = spec.get('band'); self.feather = float(spec.get('feather', 600))
        self.drift = np.array(spec.get('drift', [12, 0]), float)
        self.rise = spec.get('rise', [0, 10])
        self.scale = float(spec.get('scale', 1.0))

    def _alpha(self, dens, t):
        op = curve(self.spec.get('opacity', 0.5), t)
        cov = curve(self.spec.get('cover', 0.0), t)
        base = np.clip(0.25 + 0.95 * dens, 0, 1) * op
        if cov <= 0:
            return base
        th = 1.0 - 1.25 * cov          # 阈值下扫：浓处先被吞没，最后全满
        full = sstep(th - 0.18, th + 0.18, dens + 0.0)
        a = base + (1 - base) * full * min(1.0, cov * 1.6)
        return np.where(cov >= 0.999, 1.0, a).astype(np.float32)

    def draw(self, acc, t):
        if not self.active(t):
            return
        R = self.R
        rise = self.rise[0] * math.sin(2 * math.pi * t / self.rise[1]) if self.rise[0] else 0.0
        if self.mode == 'screen':
            # 纹理按屏幕高度铺满，水平环绕
            th = R.HS * self.scale
            k = th / self.col.shape[0]
            ox = (self.drift[0] * t * R.HS) % (self.col.shape[1] * k)
            oy = (self.drift[1] * t + rise) * R.HS
            M = np.float32([[k, 0, -ox], [0, k, oy]])
            col = cv2.warpAffine(self.col, M, (R.WS, R.HS), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_WRAP)
            den = cv2.warpAffine(self.dens, M, (R.WS, R.HS), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_WRAP)
            a = self._alpha(den, t)[..., None]
            acc *= (1 - a); acc += col * a
            return
        s, c = R.layer_xf(t, self.par, self.zpar)
        x0, y0, x1, y1 = self.band
        u = self.ds * self.scale
        # 纹理世界坐标：水平环绕平铺；band 内上下柔边
        SS = R.SS
        A = SS * s * u
        Y0 = int(max(0, math.floor(SS * (R.H / 2 + s * (y0 + rise - c[1])))))
        Y1 = int(min(R.HS, math.ceil(SS * (R.H / 2 + s * (y1 + rise - c[1])))))
        X0 = int(max(0, math.floor(SS * (R.W / 2 + s * (x0 - c[0])))))
        X1 = int(min(R.WS, math.ceil(SS * (R.W / 2 + s * (x1 - c[0])))))
        if Y1 <= Y0 or X1 <= X0:
            return
        bx = SS * (R.W / 2 + s * (x0 + self.drift[0] * t - c[0])) - X0
        by = SS * (R.H / 2 + s * (y0 + rise + self.drift[1] * t - c[1])) - Y0
        sz = (X1 - X0, Y1 - Y0)
        # 纹理缩小时先用 INTER_AREA 降采样，避免走样
        col, den, AA = self.col, self.dens, A
        while AA < 0.5 and min(col.shape[:2]) > 8:
            col = cv2.resize(col, (col.shape[1] // 2, col.shape[0] // 2), interpolation=cv2.INTER_AREA)
            den = cv2.resize(den, (den.shape[1] // 2, den.shape[0] // 2), interpolation=cv2.INTER_AREA)
            AA *= 2
        M = np.float32([[AA, 0, bx], [0, AA, by]])
        colw = cv2.warpAffine(col, M, sz, flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_WRAP)
        denw = cv2.warpAffine(den, M, sz, flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_WRAP)
        ys = c[1] + ((np.arange(Y0, Y1) + 0.5) / SS - R.H / 2) / s - rise
        xs = c[0] + ((np.arange(X0, X1) + 0.5) / SS - R.W / 2) / s
        fe = self.feather
        wy = sstep(0, fe, np.minimum(ys - y0, y1 - ys))
        wx = sstep(0, fe * 0.5, np.minimum(xs - x0, x1 - xs))
        a = self._alpha(denw, t) * wy[:, None] * wx[None, :]
        a = a[..., None].astype(np.float32)
        roi = acc[Y0:Y1, X0:X1]
        roi *= (1 - a); roi += colw * a


# ======================================================================
# 竖排展签
# ======================================================================
class Label:
    """spec: cols: [(文字, 字号720p, 字重)] 或 text: [str,...]（第一列为标题）；
    x,y: 屏幕比例（右上角锚点，列从右往左排）或 world:[x,y]（世界坐标锚点）；
    t0,t1,fade；color: '#rrggbb'；gap: 列距（字号倍数）；lead: 字距（字号倍数）"""

    def __init__(self, spec, R):
        from PIL import Image, ImageDraw, ImageFont
        self.spec, self.R = spec, R
        k = R.SS * R.H / 720.0
        cols = spec.get('cols')
        if cols is None:
            tx = spec['text']
            cols = [(tx[0], spec.get('title_size', 26), spec.get('title_weight', 'Regular'))] + \
                   [(x, spec.get('size', 22), spec.get('weight', 'Light')) for x in tx[1:]]
        col = spec.get('color', '#2a241c')
        rgb = tuple(int(col[i:i + 2], 16) for i in (1, 3, 5))
        lead = float(spec.get('lead', 1.18)); gap = float(spec.get('gap', 0.95))
        # 先算尺寸
        fonts = []
        W, Hh = 0, 0
        for txt, sz, wt in cols:
            f = ImageFont.truetype(os.path.join(FONT_DIR, f'SourceHanSerifSC-{wt}.otf'), int(round(sz * k)))
            fonts.append((txt, f, sz * k))
            W += sz * k * (1 + gap)
            Hh = max(Hh, len(txt) * sz * k * lead)
        W = int(W + 4); Hh = int(Hh + 4)
        img = Image.new('L', (W, Hh), 0)
        d = ImageDraw.Draw(img)
        x = W
        for i, (txt, f, px) in enumerate(fonts):
            x -= px * (1 + (gap if i > 0 else 0.05))
            y = 0.0
            for ch in txt:
                if ch in ' 　':
                    y += px * lead * 0.6; continue
                bb = d.textbbox((0, 0), ch, font=f)
                cw = bb[2] - bb[0]
                d.text((x + (px - cw) / 2 - bb[0], y), ch, font=f, fill=255)
                y += px * lead
        a = np.asarray(img, np.float32) / 255.0
        self.alpha = a; self.rgb = np.float32(rgb)
        self.t0, self.t1 = float(spec.get('t0', 0)), float(spec.get('t1', 1e9)); self.fade = float(spec.get('fade', 0.8))

    def draw(self, acc, t):
        if t < self.t0 or t > self.t1:
            return
        R = self.R
        op = min(sstep(self.t0, self.t0 + self.fade, t), 1 - sstep(self.t1 - self.fade, self.t1, t))
        if op <= 0:
            return
        h, w = self.alpha.shape
        if 'world' in self.spec:
            q = R.world_to_screen(t, self.spec['world']) * R.SS
            X1, Y0 = int(round(q[0])), int(round(q[1]))
        else:
            X1, Y0 = int(round(self.spec['x'] * R.WS)), int(round(self.spec['y'] * R.HS))
        X0 = X1 - w
        x0, y0, x1, y1 = max(0, X0), max(0, Y0), min(R.WS, X0 + w), min(R.HS, Y0 + h)
        if x1 <= x0 or y1 <= y0:
            return
        a = self.alpha[y0 - Y0:y1 - Y0, x0 - X0:x1 - X0][..., None] * op
        roi = acc[y0:y1, x0:x1]
        roi *= (1 - a); roi += self.rgb * a


# ======================================================================
# 呈现：墙面绢/绫合成（真实像素），立轴 / 手卷 / 器物
# ======================================================================
def silk_wall(name, samples, size, unit=8, tex_scale=2.5, tone=(0.80, 0.78, 0.74), light=None,
              shadow=None, patch=160, seed=7):
    """用真实绢/绫像素合成一面墙（缓存 npy，RGB，世界坐标由调用者用 origin/unit 放置）。
    samples: [(src_npy, [x0,y0,x1,y1]), ...] 源图里的空白绢/绫区域（原图像素）
    size: (宽,高) 世界像素；unit: 世界像素/墙像素；tex_scale: 纹理相对真实尺度的放大（>1 让织纹在全貌时可见）
    tone: RGB 乘子（相对样本中位色）；light: {'center':[x,y],'radius':r,'falloff':0.15} 世界坐标，自然明暗
    shadow: {'rect':[x0,y0,x1,y1],'offset':[dx,dy],'blur':b,'strength':0.25} 物件投在墙上的柔影"""
    key = _key(name, samples, size, unit, tex_scale, tone, light, shadow, patch, seed, 'v3')
    p = os.path.join(CACHE, f'wall_{name}_{key}.npy')
    if os.path.exists(p):
        return p
    rng = np.random.default_rng(seed)
    f = unit / tex_scale            # 样本缩小倍数
    pool = []
    for src, (x0, y0, x1, y1) in samples:
        a = _open(src)
        # 分块读、INTER_AREA 缩小（不跨步取样，避免织纹摩尔纹）
        rows = []
        step = int(max(256, round(f * 64)))
        for r in range(y0, y1, step):
            b = np.ascontiguousarray(a[r:min(r + step, y1), x0:x1, :3])
            rows.append(cv2.resize(b, (max(1, int(round(b.shape[1] / f))), max(1, int(round(b.shape[0] / f)))), interpolation=cv2.INTER_AREA))
        pool.append(np.concatenate(rows, 0).astype(np.float32))
    med = np.median(np.concatenate([q.reshape(-1, 3)[::17] for q in pool]), 0)
    # 剔除样本里的印章、墨迹、污点：亮度/色度离群像素 → 膨胀 → 积分图，含离群的补丁不取
    bads = []
    for q in pool:
        lum = q.mean(2); ch = q[..., 0] - q[..., 2]
        dl = lum - cv2.GaussianBlur(lum, (0, 0), 12); dc = ch - np.median(ch)
        sl = 1.4826 * np.median(np.abs(dl)) + 1e-3; sc = 1.4826 * np.median(np.abs(dc)) + 1e-3
        b = ((np.abs(dl) > 4.5 * sl) | (np.abs(dc) > 5 * sc)).astype(np.uint8)
        b = cv2.dilate(b, np.ones((5, 5), np.uint8))
        bads.append(cv2.integral(b))
    Ww, Hw = int(math.ceil(size[0] / unit)), int(math.ceil(size[1] / unit))
    ps = min(patch, min(min(q.shape[:2]) for q in pool) - 2)
    stepp = int(ps * 0.62)
    win1 = np.sin(np.linspace(0, np.pi, ps, dtype=np.float32)) ** 2
    win = win1[:, None] * win1[None, :]
    acc = np.zeros((Hw + ps, Ww + ps, 3), np.float32); wsum = np.zeros((Hw + ps, Ww + ps), np.float32)
    w2 = np.zeros_like(wsum)
    sig = max(6.0, ps / 5)
    for yy in range(-ps // 2, Hw, stepp):
        for xx in range(-ps // 2, Ww, stepp):
            for _try in range(40):
                qi = int(rng.integers(len(pool))); q = pool[qi]; ib = bads[qi]
                i = int(rng.integers(0, q.shape[0] - ps)); j = int(rng.integers(0, q.shape[1] - ps))
                if ib[i + ps, j + ps] - ib[i, j + ps] - ib[i + ps, j] + ib[i, j] == 0:
                    break
            pt = q[i:i + ps, j:j + ps]
            hp = pt - cv2.GaussianBlur(pt, (0, 0), sig)          # 纤维 + 暗花（去掉样本自身的大尺度明暗）
            jy, jx = yy + int(rng.integers(-stepp // 5, stepp // 5 + 1)), xx + int(rng.integers(-stepp // 5, stepp // 5 + 1))
            Y, X = jy + ps // 2, jx + ps // 2
            if Y < 0 or X < 0 or Y + ps > acc.shape[0] or X + ps > acc.shape[1]:
                continue
            acc[Y:Y + ps, X:X + ps] += hp * win[..., None]
            wsum[Y:Y + ps, X:X + ps] += win
            w2[Y:Y + ps, X:X + ps] += win * win
    o = ps // 2
    detail = acc[o:o + Hw, o:o + Ww] / np.sqrt(np.maximum(w2[o:o + Hw, o:o + Ww], 1e-4))[..., None]
    detail *= 0.8
    # 自然明暗：样本自身的低频起伏（大尺度）+ 灯光
    base = med * np.float32(tone)
    mot = cv2.GaussianBlur(rng.standard_normal((Hw, Ww)).astype(np.float32), (0, 0), max(Hw, Ww) / 30)
    mot = mot / (mot.std() + 1e-6)
    shade = 1 + 0.018 * mot
    ys = (np.arange(Hw, dtype=np.float32) + 0.5) * unit; xs = (np.arange(Ww, dtype=np.float32) + 0.5) * unit
    if light:
        cx, cy = light['center']; r = light['radius']; fo = light.get('falloff', 0.15)
        d2 = ((xs[None, :] - cx) ** 2 + ((ys[:, None] - cy) * 1.3) ** 2) / (r * r)
        shade *= (1 - fo * np.clip(d2, 0, 1.6) / 1.6)
    img = base[None, None, :] * shade[..., None] + detail
    if shadow:
        x0, y0, x1, y1 = shadow['rect']; dx, dy = shadow.get('offset', [0, 0])
        m = np.zeros((Hw, Ww), np.float32)
        cv2.rectangle(m, (int((x0 + dx) / unit), int((y0 + dy) / unit)), (int((x1 + dx) / unit), int((y1 + dy) / unit)), 1.0, -1)
        m = cv2.GaussianBlur(m, (0, 0), shadow.get('blur', 400) / unit)
        img *= (1 - shadow.get('strength', 0.25) * m)[..., None]
    np.save(p + '.tmp.npy', np.clip(img + 0.5, 0, 255).astype(np.uint8)); os.replace(p + '.tmp.npy', p)
    return p


def hanging_scroll(src, name, fill_h=0.94, samples=None, wall_unit=8, tex_scale=1.6, tone=(0.83, 0.79, 0.70),
                   res_aspect=16 / 9, shadow_strength=0.22):
    """立轴全貌：整轴（含装裱）按高度放入，两侧是用原图空白绫/绢合成的墙面。
    返回 dict(layers=[wall, scroll], full=相机全貌状态, size=(w,h))"""
    a = _open(src); H, W = a.shape[:2]
    vh = H / fill_h
    vw = vh * res_aspect
    mx = max(vw - W, 0) / 2 * 1.2 + W * 0.05   # 墙面每侧外延（全貌两侧 + 余量）
    my = vh * 0.08
    size = (W + 2 * mx, H + 2 * my)
    origin = (-mx, -my)
    if samples is None:   # 默认取左右裱边的绫（立轴原图通常带裱边）
        bw = int(W * 0.04)
        samples = [(src, [int(W * 0.004), int(H * 0.2), bw, int(H * 0.88)]),
                   (src, [W - bw, int(H * 0.2), W - int(W * 0.004), int(H * 0.88)])]
    # silk_wall 坐标以墙左上角为 0
    sh = {'rect': [mx, my, W + mx, H + my], 'offset': [W * 0.010, H * 0.006], 'blur': H * 0.005, 'strength': shadow_strength}
    light = {'center': [W / 2 + mx, H * 0.35 + my], 'radius': vw * 0.62, 'falloff': 0.16}
    wp = silk_wall(name, samples, size, unit=wall_unit, tex_scale=tex_scale, tone=tone, light=light, shadow=sh)
    return dict(layers=[{'name': 'wall', 'src': wp, 'origin': list(origin), 'unit': wall_unit, 'cache_name': f'wall_{name}'},
                        {'name': 'scroll', 'src': src, 'origin': [0, 0], 'unit': 1, 'cache_name': f'{name}_scroll'}],
                full={'cx': W / 2, 'cy': H / 2, 'vh': vh}, size=(W, H))


def handscroll_band(src, name, band_h=0.18, samples=None, wall_unit=8, tex_scale=2.5, tone=(0.80, 0.78, 0.74)):
    """手卷全貌：整卷作一条横带（宽度占屏 ~94%）躺在绢上。返回同 hanging_scroll。
    samples 必须给（手卷原图一般没有裱边可取）：例如画中空白绢区域。"""
    a = _open(src); H, W = a.shape[:2]
    vw = W / 0.94; vh = vw * 9 / 16
    size = (vw * 1.4, max(vh * 1.4, H * 3))
    origin = (W / 2 - size[0] / 2, H / 2 - size[1] / 2)
    ox, oy = -origin[0], -origin[1]
    sh = {'rect': [ox, oy, ox + W, oy + H], 'offset': [H * 0.02, H * 0.05], 'blur': H * 0.05, 'strength': 0.2}
    light = {'center': [ox + W / 2, oy + H / 2], 'radius': vw * 0.6, 'falloff': 0.14}
    wp = silk_wall(name, samples, size, unit=wall_unit, tex_scale=tex_scale, tone=tone, light=light, shadow=sh)
    return dict(layers=[{'name': 'wall', 'src': wp, 'origin': list(origin), 'unit': wall_unit, 'cache_name': f'wall_{name}'},
                        {'name': 'scroll', 'src': src, 'origin': [0, 0], 'unit': 1, 'cache_name': f'{name}_scroll'}],
                full={'cx': W / 2, 'cy': H / 2, 'vh': vh}, size=(W, H))


def object_photo(photo, name, fill=0.86, bg=None, feather=0.08, samples=None, wall_unit=2):
    """器物：照片主体占画面（高 fill），背景是与照片底色协调的柔和绢/纸色（真实绢纹 samples 可选），
    照片边缘按 feather（比例）羽化进底色，不漂浮、不纯黑。返回同上。"""
    a = _open(photo); H, W = a.shape[:2]
    b = np.concatenate([a[:H // 20].reshape(-1, a.shape[2]), a[-H // 20:].reshape(-1, a.shape[2])])[:, :3]
    col = np.median(b, 0) if bg is None else np.float32(bg)
    vh = H / fill; vw = vh * 16 / 9
    size = (vw * 1.3, vh * 1.3); origin = (W / 2 - size[0] / 2, H / 2 - size[1] / 2)
    if samples:
        wp = silk_wall(name, samples, size, unit=wall_unit * 4, tex_scale=1.5, tone=(1, 1, 1), light=None)
        wall = _open(wp).astype(np.float32)
        wall = wall / np.median(wall.reshape(-1, 3), 0) * col
        wp2 = os.path.join(CACHE, f'objbg_{name}_{_key(wp, tuple(col))}.npy'); np.save(wp2, np.clip(wall, 0, 255).astype(np.uint8))
        layers = [{'name': 'wall', 'src': wp2, 'origin': list(origin), 'unit': wall_unit * 4}]
    else:
        wp2 = os.path.join(CACHE, f'objbg_{name}_{_key(photo, tuple(col))}.npy')
        np.save(wp2, np.broadcast_to(np.clip(col, 0, 255).astype(np.uint8), (64, 114, 3)).copy())
        layers = [{'name': 'wall', 'src': wp2, 'origin': list(origin), 'unit': size[0] / 114}]
    fe = feather * min(W, H)
    layers.append({'name': 'photo', 'src': photo, 'origin': [0, 0], 'unit': 1, 'crop': [0, 0, W, H], 'feather': fe,
                   'cache_name': f'{name}_photo'})
    return dict(layers=layers, full={'cx': W / 2, 'cy': H / 2, 'vh': vh}, size=(W, H))


# ======================================================================
# 段加载 + CLI
# ======================================================================
def load_segment(path):
    if path.endswith('.json'):
        return json.load(open(path))
    spec = importlib.util.spec_from_file_location('seg', path)
    m = importlib.util.module_from_spec(spec)
    sys.path.insert(0, LIB)
    spec.loader.exec_module(m)
    return m.build() if hasattr(m, 'build') else m.SEG


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('seg'); ap.add_argument('out')
    ap.add_argument('--res', type=int, default=720)
    ap.add_argument('--frames', default='')
    ap.add_argument('--stills', default='')
    ap.add_argument('--check', action='store_true', help='只做速度检查')
    ap.add_argument('--crf', type=int, default=12)
    a = ap.parse_args(argv)
    seg = load_segment(a.seg)
    R = Renderer(seg, a.res)
    log(f'段 {a.seg}: {R.nframes} 帧 {R.W}x{R.H}@{R.fps:g}，层 {[L.name for L in R.layers]}，fx {[f.spec["type"] for f in R.fx]}')
    R.check_speed()
    if a.check:
        return
    if a.stills:
        base = os.path.splitext(a.out)[0]
        for i in [int(x) for x in a.stills.split(',') if x]:
            tr = time.time()
            fr = R.render(i / R.fps)
            cv2.imwrite(f'{base}_f{i:04d}.png', cv2.cvtColor(fr, cv2.COLOR_RGB2BGR))
            log(f'still {i} {time.time() - tr:.2f}s')
        return
    f0, f1 = (map(int, a.frames.split(':')) if a.frames else (0, R.nframes))
    ff = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{R.W}x{R.H}',
                           '-r', f'{R.fps:g}', '-i', '-', '-c:v', 'libx264', '-preset', 'medium', '-crf', str(a.crf),
                           '-pix_fmt', 'yuv420p', '-movflags', '+faststart', a.out], stdin=subprocess.PIPE)
    tr = time.time()
    for i in range(f0, f1):
        ff.stdin.write(R.render(i / R.fps).tobytes())
        if (i - f0) % 15 == 0:
            log(f'frame {i}/{f1}  {(time.time() - tr) / (i - f0 + 1):.2f}s/帧')
    ff.stdin.close(); ff.wait()
    log(f'完成 {a.out}  {(time.time() - tr) / max(1, f1 - f0):.2f}s/帧')


if __name__ == '__main__':
    try:
        main()
    except EngineError as e:
        print('ENGINE ERROR:', e, file=sys.stderr); sys.exit(2)
