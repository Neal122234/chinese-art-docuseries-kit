# -*- coding: utf-8 -*-
"""S5 汝窑《青瓷无纹水仙盆》v2 · 全局 3:50–4:52（帧 0 = 3:50），62 s。
多镜头合成：每个镜头是一个独立的 engine.Renderer（各自相机、各自速度检查），镜头之间整屏柔和溶解。
v2 的"动"（都用原照像素，只加光和揭示）：
  0–7.5   满屏石青（千里江山主峰石青，原作像素 8× 放大，看得见绢丝与矿物颗粒），缓推
  7.5–11.8 颗粒"熔成釉"：石青颗粒逐渐融化、颜色滑向天青，一道釉面反光掠过，接天青釉面微距
  11–19.5 拉开到全器
  17.4–24.6 冲击点：一道柔光从左向右扫过器身。外壁的高光顺着弧面走、内壁的高光反向走（法线估计）；
          亮处釉色微暖，背光处偏蓝；四周略暗，背景上一团光跟着走
  25–31   口沿：焦点从虚到实 + 一粒光沿唇线滑过，经过处粉色显出
  31–37   底边：釉从上往下流、积到底边处成碧（按原照颜色揭示）
  37–45   支钉：四周暗下，一束光依次落到六个支钉上
  45–     回全器（4:40 起交给 S6 淡出）
用法（重活走锁；成片后台跑）：
  lockf -k $S/.heavy.lock python3 seg_s5.py OUT.mp4 [--res 720|1080] [--stills 0,300] [--frames a:b] [--check]
"""
import os, sys, time, argparse, subprocess, json, math
import numpy as np, cv2
HERE = os.path.dirname(os.path.abspath(__file__))
S = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(S, 'lib'))
import engine as E

RU = os.path.join(S, 'assets/ru')
WK = os.path.join(HERE, 'work')
STAGE = os.path.join(WK, 'pae_stage.npy')
STAGE_ORIGIN = [-1400, -500]
G0 = 230.0                      # 本段 t=0 对应全局 3:50
DUR = 62.0

FULL = {'cx': 1809, 'cy': 1280, 'vh': 2180}       # 全器全貌（器物居左偏中，右侧留白放展签）
LABEL = {'text': ['汝窯青瓷無紋水仙盆', '北宋', '高六·九厘米', '臺北故宮博物院藏'],
         'x': 0.905, 'y': 0.2, 'color': '#2b251d', 'title_size': 26, 'size': 22}

# 时间表（本段秒）
MELT = (7.5, 11.8)              # 石青 → 天青
SWEEP = dict(on=(17.2, 18.4), off=(23.6, 24.8), move=(17.6, 24.2), phi=(-68.0, 64.0))
RIM_FOCUS = (24.6, 26.6)
RIM_GLINT = (25.4, 30.6)
POOL = (31.4, 35.6)
SPUR_DIM = (37.4, 38.2, 43.2, 44.4)
SPURS = [(1075, 690), (1870, 700), (2530, 1270), (1815, 1815), (1060, 1780), (445, 1165)]   # 顺时针
SPUR_T0, SPUR_DT = 38.0, 0.62


def sst(e0, e1, x):
    return float(E.sstep(e0, e1, x))


def photo_layer(fn, name):
    return {'name': name, 'src': os.path.join(RU, fn), 'origin': [0, 0], 'unit': 1, 'cache_name': 'ru_' + name}


def stage_layer():
    return {'name': 'stage', 'src': STAGE, 'origin': STAGE_ORIGIN, 'unit': 1, 'cache_name': 'ru_stage'}


def K(t, cx, cy, vh, ease=None):
    k = {'t': t, 'cx': cx, 'cy': cy, 'vh': vh}
    if ease is not None:
        k['ease'] = ease
    return k


# ---------------------------------------------------------------- 工具：把世界坐标里的辅助图贴到 acc（SS 分辨率）
def warp_aux(R, t, arr, origin, unit, interp=cv2.INTER_LINEAR):
    s, c = R.layer_xf(t)
    SS = R.SS
    A = SS * s * unit
    bx = SS * (R.W / 2 + s * (origin[0] - c[0]))
    by = SS * (R.H / 2 + s * (origin[1] - c[1]))
    M = np.float32([[A, 0, bx], [0, A, by]])
    return cv2.warpAffine(arr, M, (R.WS, R.HS), flags=interp, borderMode=cv2.BORDER_CONSTANT, borderValue=0)


def world_grid(R, t):
    s, c = R.layer_xf(t)
    SS = R.SS
    X = c[0] + ((np.arange(R.WS, dtype=np.float32) + 0.5) / SS - R.W / 2) / s
    Y = c[1] + ((np.arange(R.HS, dtype=np.float32) + 0.5) / SS - R.H / 2) / s
    return X, Y, s


class FxRelight:
    """一道柔光扫过全器：法线估计（外壁椭圆柱 + 内壁凹面 + 内底），漫反射改明暗与冷暖，两瓣柔和高光，背景跟光。"""
    def __init__(self, R, after='stage'):
        self.R, self.after = R, after
        aux = np.load(os.path.join(WK, 'pae_aux.npy')).astype(np.float32)   # PAE 坐标，unit 2
        self.nrm = np.ascontiguousarray(aux[..., :3])
        self.msk = np.ascontiguousarray(aux[..., 3:5])

    def env(self, t):
        a0, a1 = SWEEP['on']; b0, b1 = SWEEP['off']
        return sst(a0, a1, t) * (1 - sst(b0, b1, t))

    def draw(self, acc, t):
        e = self.env(t)
        if e <= 1e-3:
            return
        R = self.R
        m0, m1 = SWEEP['move']
        u = sst(m0, m1, t)
        phi = math.radians(SWEEP['phi'][0] + (SWEEP['phi'][1] - SWEEP['phi'][0]) * u)
        el = math.radians(9)
        L = np.float32([math.sin(phi) * math.cos(el), -math.sin(el), math.cos(phi) * math.cos(el)])
        Hh = L + np.float32([0, 0, 1]); Hh /= np.linalg.norm(Hh)
        n = warp_aux(R, t, self.nrm, (0, 0), 2)
        mk = warp_aux(R, t, self.msk, (0, 0), 2)
        m = np.clip(mk[..., 0], 0, 1)
        ndl = np.clip(n @ L, 0, 1)
        ndh = np.clip(n @ Hh, 0, 1)
        # 器物：漫反射改明暗（0.80–1.22），冷暖随受光
        f = 0.74 + 0.50 * ndl
        k = np.clip((ndl - 0.25) / 0.65, 0, 1)[..., None]
        warm = np.float32([1.045, 1.0, 0.94]); cool = np.float32([0.92, 0.985, 1.07])
        tint = cool + (warm - cool) * k
        vf = f[..., None] * tint
        # 背景：一团光跟着光源走，四周略暗
        X, Y, s = world_grid(R, t)
        xp = 1526 + 1900 * math.sin(phi)
        gx = np.exp(-((X - xp) / 1250.0) ** 2)
        gy = np.exp(-((Y - 1150) / 1500.0) ** 2)
        g = gy[:, None] * gx[None, :]
        bf = (0.80 + 0.30 * g)[..., None] * (1 + 0.035 * g[..., None] * np.float32([1, 0, -1]))
        fac = vf * m[..., None] + bf * (1 - m[..., None])
        fac = 1 + e * (fac - 1)
        acc *= fac
        # 高光：两瓣，调制于釉面本身的细纹理（不是平涂的光）
        lum = acc.mean(2)
        hp = lum - cv2.GaussianBlur(lum, (0, 0), 2.0 * R.H / 720)       # 釉面细纹尺度按 720p 等比
        tex = np.clip(1 + hp / 30.0, 0.6, 1.4)
        wi = np.clip(mk[..., 1], 0, 1)                      # 内壁/内底权重：凹面高光收一半，免得发白
        spec = np.minimum(0.42 * ndh ** 36 + 0.22 * ndh ** 7, 0.5) * m * tex * e * (1 - 0.55 * wi)
        col = np.float32([252, 249, 238])
        acc += spec[..., None] * (col - acc)


class FxFocus:
    """焦点从虚到实（整屏景深，不是拖影）。"""
    def __init__(self, R, span, sig0, after='__top__'):
        self.R, self.span, self.sig0, self.after = R, span, sig0, after

    def draw(self, acc, t):
        a, b = self.span
        sig = self.sig0 * (1 - sst(a, b, t)) * self.R.SS * self.R.H / 720     # sig0 = 720p 输出像素
        if sig < 0.3:
            return
        acc[:] = cv2.GaussianBlur(acc, (0, 0), sig)


class FxLipGlint:
    """一粒光沿口沿唇线滑过；经过处唇线的粉色显出来。"""
    def __init__(self, R, after='pbd'):
        self.R, self.after = R, after
        self.c = np.load(os.path.join(WK, 'pbd_lip.npy'))

    def draw(self, acc, t):
        a, b = RIM_GLINT
        e = sst(a - 0.6, a + 0.4, t) * (1 - sst(b - 0.5, b + 0.4, t))
        if e <= 1e-3:
            return
        R = self.R
        X, Y, s = world_grid(R, t)
        u = sst(a, b, t)
        xg = 1050 + (2560 - 1050) * u
        ylip = np.polyval(self.c, np.clip(X, 100, 2700)).astype(np.float32)
        d = Y[:, None] - ylip[None, :]                      # 离唇线的竖直距离（世界像素）
        along = np.exp(-((X - xg) / 130.0) ** 2)[None, :]
        wide = np.exp(-((X - xg) / 420.0) ** 2)[None, :]
        core = np.exp(-(d / 8.0) ** 2) * along
        halo = np.exp(-(d / 40.0) ** 2) * wide
        pink = np.exp(-((d - 2) / 16.0) ** 2) * wide
        # 粉：唇线处 R 上 G 下（光经过时显出）
        acc *= 1 + (e * pink)[..., None] * np.float32([0.14, -0.06, -0.03])
        acc += (e * (0.85 * core + 0.22 * halo))[..., None] * (np.float32([255, 244, 238]) - acc)


class FxPool:
    """底边积釉：先是和上半器壁一样的薄釉色，釉从上往下流下去，流过处显出原照的颜色，最后在底边积成碧。"""
    def __init__(self, R, after='pbe'):
        self.R, self.after = R, after
        aux = np.load(os.path.join(WK, 'pbe_pool.npy')).astype(np.float32)   # PBE 坐标，unit 2
        self.delta = np.ascontiguousarray(aux[..., :3]); self.reg = np.ascontiguousarray(aux[..., 3])

    def draw(self, acc, t):
        a, b = POOL
        R = self.R
        p = sst(a, b, t)
        if p >= 0.999:
            return
        X, Y, s = world_grid(R, t)
        yf = 1180 + (1900 - 1180) * p + 10 * np.sin(X / 260.0 + 1.3)   # 流动前沿（柔、略有起伏）
        # 前沿以上 = 原色；以下 = 薄釉色（更浅、更灰）
        cov = np.clip((Y[:, None] - yf[None, :]) / 160.0 + 0.5, 0, 1)
        cov = cov * cov * (3 - 2 * cov)
        dl = warp_aux(R, t, self.delta, (0, 0), 2)
        rg = warp_aux(R, t, self.reg, (0, 0), 2)
        w = (cov * rg)[..., None]
        acc += dl * w
        lum = acc.mean(2, keepdims=True)
        acc += w * ((lum - acc) * 0.28 + (np.float32([236, 240, 236]) - acc) * 0.07)


class FxSpurs:
    """四周暗下，一束柔光依次落到六个支钉上。"""
    def __init__(self, R, after='pbg'):
        self.R, self.after = R, after

    def draw(self, acc, t):
        a0, a1, b0, b1 = SPUR_DIM
        e = sst(a0, a1, t) * (1 - sst(b0, b1, t))
        if e <= 1e-3:
            return
        R = self.R
        X, Y, s = world_grid(R, t)
        lit = np.zeros((R.HS, R.WS), np.float32)
        for i, (sx, sy) in enumerate(SPURS):
            ti = SPUR_T0 + SPUR_DT * i
            w = sst(ti, ti + 0.55, t)
            if w <= 0:
                continue
            gx = np.exp(-((X - sx) / 200.0) ** 2); gy = np.exp(-((Y - sy) / 200.0) ** 2)
            lit = np.maximum(lit, w * gy[:, None] * gx[None, :])
        f = (0.58 + 0.46 * lit)[..., None] * (1 + 0.03 * lit[..., None] * np.float32([1, 0.3, -0.6]))
        acc *= 1 + e * (f - 1)


# ---------------------------------------------------------------- 镜头表
def shots():
    D = DUR
    sh = []
    # Q 满屏石青（千里江山主峰石青，8× 原作像素）：缓推
    q0 = K(0, 990, 2826, 160)
    sh.append(('Q_qing', [None, None, 9.4, 11.6], {
        'duration': D, 'ss': 2, 'sharpen': 0.0,
        'layers': [{'name': 'qing', 'src': os.path.join(WK, 'qing_up.npy'), 'origin': [700, 2560], 'unit': 0.25,
                    'cache_name': 'ru_qing_up4'}],
        'camera': {'rest': q0, 'keys': [q0, K(0.6, 990, 2826, 160), K(11.6, 985, 2826, 122, ease=2.0)]}}, 'qing'))
    # A 天青釉面微距（基边照的器壁），熔釉时静，之后缓拉开
    a0 = K(0, 1650, 1222, 640)
    sh.append(('A_macro', [None, None, 11.6, 14.4], {
        'duration': D, 'layers': [photo_layer('ru_baseedge_PBE.jpg', 'pbe')],
        'camera': {'rest': a0, 'keys': [a0, K(9.8, 1650, 1222, 640), K(15.8, 1300, 1215, 760, ease=2.2)]}}, None))
    # B 从近到全貌 + 光扫
    b0 = K(0, 1560, 1330, 1480)
    sh.append(('B_full', [11.6, 14.4, 23.8, 25.2], {
        'duration': D, 'layers': [stage_layer()],
        'camera': {'rest': FULL, 'keys': [b0, K(10.4, 1560, 1330, 1480), K(19.5, FULL['cx'], FULL['cy'], FULL['vh'], ease=1.8)]},
        'labels': [dict(LABEL, t0=15.6, t1=23.9, fade=1.0)]}, 'relight'))
    # C 口沿：虚→实，一粒光沿唇线走
    c0 = K(0, 1700, 1335, 820)
    sh.append(('C_rim', [23.8, 25.2, 30.2, 31.6], {
        'duration': D, 'layers': [photo_layer('ru_rim_PBD.jpg', 'pbd')],
        'camera': {'rest': c0, 'keys': [c0, K(23.8, 1700, 1335, 820), K(31.6, 1880, 1290, 640, ease=1.8)]}}, 'rim'))
    # D 底边积釉
    d0 = K(0, 980, 1540, 780)
    sh.append(('D_base', [30.2, 31.6, 36.2, 37.6], {
        'duration': D, 'layers': [photo_layer('ru_baseedge_PBE.jpg', 'pbe')],
        'camera': {'rest': d0, 'keys': [d0, K(30.2, 980, 1540, 780), K(37.6, 900, 1600, 640, ease=1.8)]}}, 'pool'))
    # E 支钉
    e0 = K(0, 1496, 1253, 1700)
    sh.append(('E_spurs', [36.2, 37.6, 43.6, 45.0], {
        'duration': D, 'layers': [photo_layer('ru_spurs_PBG.jpg', 'pbg')],
        'camera': {'rest': e0, 'keys': [e0, K(36.2, 1496, 1253, 1700), K(45.0, 1496, 1253, 1440, ease=1.8)]}}, 'spurs'))
    # F 回全器，4:40 起静止供淡出
    f0 = K(0, 1700, 1300, 1880)
    sh.append(('F_full', [43.6, 45.0, None, None], {
        'duration': D, 'layers': [stage_layer()],
        'camera': {'rest': FULL, 'keys': [f0, K(43.6, 1700, 1300, 1880), K(50.0, FULL['cx'], FULL['cy'], FULL['vh'], ease=1.8)]}}, None))
    return sh


def weight(win, t):
    a0, a1, b0, b1 = win
    w = 1.0
    if a0 is not None:
        w *= float(E.sstep(a0, a1, t))
    if b0 is not None:
        w *= 1.0 - float(E.sstep(b0, b1, t))
    return w


BEATS = [  # 字幕锚点（全局秒）——画面按这些时间排
    ('这种青 也被宋人烧进了瓷里', 235), ('汝窑青瓷水仙盆', 244), ('通身没有一笔花纹 美全在釉色本身', 248),
    ('釉薄的口沿 透出淡淡的粉', 255), ('釉厚的地方 积成一抹淡碧', 261),
    ('底下六个芝麻大的支钉痕 是烧制时托住它的地方', 267), ('汝窑存世不足百件 这一件连一道开片都没有', 275)]


class Multi:
    def __init__(self, res):
        self.items = []
        for name, win, spec, fx in shots():
            R = E.Renderer(spec, res)
            if fx == 'relight':
                R.fx.append(FxRelight(R))
            elif fx == 'rim':
                R.fx.append(FxLipGlint(R)); R.fx.append(FxFocus(R, RIM_FOCUS, 7.0, after='pbd'))
            elif fx == 'pool':
                R.fx.append(FxPool(R))
            elif fx == 'spurs':
                R.fx.append(FxSpurs(R))
            self.items.append((name, win, R, fx))
        R0 = self.items[0][2]
        self.W, self.H, self.fps = R0.W, R0.H, R0.fps
        self.nframes = int(round(DUR * self.fps))
        self.macro_mean = None

    def check(self):
        for name, win, R, fx in self.items:
            E.log(f'[{name}]'); R.check_speed()

    def melt(self, q, g, t):
        """石青颗粒熔成天青釉：先融（模糊加深）、颜色按统计量滑向釉面，最后细纹理换成釉面，一道反光掠过。"""
        a, b = MELT
        p = sst(a, b, t)
        qf = q.astype(np.float32); gf = g.astype(np.float32)
        H, W = self.H, self.W
        sig = 14.0 * sst(0.0, 0.6, p) * H / 720
        qb = cv2.GaussianBlur(qf, (0, 0), sig) if sig > 0.3 else qf
        # 颜色：整体滑向釉色，起伏（颗粒）同时收平——各通道同比收，不偏色
        mq = qb.reshape(-1, 3).mean(0); mg = gf.reshape(-1, 3).mean(0)
        k = sst(0.05, 0.8, p)
        qc = (qb - mq) * (1 - 0.75 * k) + (mq + (mg - mq) * k)
        w = sst(0.5, 1.0, p)
        out = qc * (1 - w) + gf * w
        # 釉面反光：宽而柔的斜向亮带，从左上掠到右下
        u = sst(0.35, 1.0, p)
        env = math.sin(math.pi * min(max((p - 0.3) / 0.7, 0), 1))
        if env > 1e-3:
            yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
            d = (xx * 0.8 + yy * 0.6) / W
            c = -0.3 + 1.6 * u
            band = np.exp(-((d - c) / 0.20) ** 2) * env
            out = out + (0.22 * band)[..., None] * (np.float32([250, 251, 245]) - out)
        return np.clip(out + 0.5, 0, 255).astype(np.uint8)

    def render(self, t):
        a, b = MELT
        frames = {}
        acc = None; tot = 0.0
        for name, win, R, fx in self.items:
            w = weight(win, t)
            if name == 'A_macro' and t < a:
                w = 0.0
            if name == 'Q_qing':
                w = 1.0 if t < b else 0.0
            if w <= 1e-4:
                continue
            fr = R.render(t)
            frames[name] = fr
        if 'Q_qing' in frames:
            if t < a:
                base = frames['Q_qing']
            else:
                g = frames.get('A_macro')
                base = self.melt(frames['Q_qing'], g, t)
            return base
        for name, win, R, fx in self.items:
            if name not in frames:
                continue
            w = weight(win, t)
            fr = frames[name].astype(np.float32)
            acc = fr * w if acc is None else acc + fr * w
            tot += w
        return np.clip(acc / tot + 0.5, 0, 255).astype(np.uint8)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('out'); ap.add_argument('--res', type=int, default=720)
    ap.add_argument('--frames', default=''); ap.add_argument('--stills', default='')
    ap.add_argument('--check', action='store_true'); ap.add_argument('--crf', type=int, default=12)
    a = ap.parse_args()
    M = Multi(a.res)
    M.check()
    json.dump([{'text': s, 'global_s': g, 'local_s': g - G0} for s, g in BEATS],
              open(os.path.join(HERE, 'beats.json'), 'w'), ensure_ascii=False, indent=1)
    if a.check:
        return
    if a.stills:
        base = os.path.splitext(a.out)[0]
        for i in [int(x) for x in a.stills.split(',') if x]:
            fr = M.render(i / M.fps)
            cv2.imwrite(f'{base}_f{i:04d}.png', cv2.cvtColor(fr, cv2.COLOR_RGB2BGR)); E.log(f'still {i}')
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
    E.log(f'完成 {a.out}')


if __name__ == '__main__':
    try:
        main()
    except E.EngineError as e:
        print('ENGINE ERROR:', e, file=sys.stderr); sys.exit(2)
