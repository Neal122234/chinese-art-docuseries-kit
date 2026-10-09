# -*- coding: utf-8 -*-
"""第二集 S6 南宋官窑青瓷瓶 · 段窗口 = 全局 246–284 s（帧 0 = 246 s），38 s，1140 帧。
素材：Met 52679（DP335586，CC0）。世界坐标 = 该照片原图像素。预处理见 prep.py（展台、抠图、开片遮罩、点亮顺序、法线）。
  0–6.5    釉面开片微距铺满屏（1.16× 原图像素，静止；246–253 供总装"墨干成开片"，另导出开片线遮罩）
  6.5–12   微距缓拉开（≤6%/s）；9.6–12.2 叠化到中景，中景继续拉开，16.5 到全器（背景 = s7 同一块绢，全貌时与 s7 首帧重合）
  16–22.5  展签
  17.4–27.6 高光：一道柔光从左向右扫过器身（回转体法线：漫射改明暗冷暖 + 竖向高光带随弧面走）；
           光到之处，照片里真实的开片纹一条条亮起（每条枝从光先到的一端沿线点亮），之后保持微亮，27.2–30.8 退回
  30.8–38  全器静止（278–284 交给 s7 淡为绢底）
用法（渲染走锁）：
  python3 seg_s6.py OUT.mp4 [--stills 0,300] [--frames a:b] [--check] [--mask MASK.mp4]"""
import os, sys, time, argparse, subprocess, json, math
import numpy as np, cv2
HERE = os.path.dirname(os.path.abspath(__file__))
EP = os.path.dirname(os.path.dirname(HERE))
S = os.path.dirname(EP)
sys.path.insert(0, os.path.join(S, 'lib'))
sys.path.insert(0, HERE)
import engine as E
import prep as P

WK = os.path.join(HERE, 'work')
G0 = 246.0
DUR = 38.0
FULL = dict(P.FULL)
LABEL = {'text': ['官窯青瓷瓶', '南宋　十二至十三世紀', '高二七·九厘米', '紐約大都會藝術博物館藏'],
         'x': 0.845, 'y': 0.2, 'color': '#EDE6D8', 'title_size': 26, 'size': 22}
MACRO = dict(cx=1455, cy=2605, vh=620)
SWEEP = dict(on=(17.4, 18.6), move=(17.8, 25.8), phi=(-125.0, 125.0), off=(26.0, 27.6))
GLOW_OUT = (27.2, 30.8)
DISS = (9.6, 12.2)


def sst(a, b, x):
    return float(E.sstep(a, b, x))


def K(t, cx, cy, vh, ease=None):
    k = {'t': t, 'cx': cx, 'cy': cy, 'vh': vh}
    if ease is not None:
        k['ease'] = ease
    return k


def stage_layer():
    return {'name': 'stage', 'src': os.path.join(WK, 'stage.npy'), 'origin': list(P.STAGE_ORIGIN), 'unit': 1,
            'cache_name': 'ep02_s6_guan_stage'}


def warp(R, t, arr, unit, W=None, H=None, SS=None, interp=cv2.INTER_LINEAR):
    """把照片坐标（origin 0,0，unit）的辅助图贴到屏幕网格（默认 SS 分辨率）。"""
    s, c = R.layer_xf(t)
    SS = R.SS if SS is None else SS
    W = R.W if W is None else W; H = R.H if H is None else H
    A = SS * s * unit
    bx = SS * (W / 2 - s * c[0]); by = SS * (H / 2 - s * c[1])
    M = np.float32([[A, 0, bx], [0, A, by]])
    return cv2.warpAffine(arr, M, (W * SS, H * SS), flags=interp, borderMode=cv2.BORDER_CONSTANT, borderValue=0)


def world_x(R, t):
    s, c = R.layer_xf(t)
    return c[0] + ((np.arange(R.WS, dtype=np.float32) + 0.5) / R.SS - R.W / 2) / s, \
        c[1] + ((np.arange(R.HS, dtype=np.float32) + 0.5) / R.SS - R.H / 2) / s


# ---------------------------------------------------------------- 辅助图（一次载入）
class Aux:
    def __init__(self):
        crack = np.load(os.path.join(WK, 'crack.npy')).astype(np.float32) / 255
        ign = np.load(os.path.join(WK, 'ignite.npy')).astype(np.float32)
        self.crack1 = crack
        h, w = crack.shape
        self.crack2 = cv2.resize(crack, (w // 2, h // 2), interpolation=cv2.INTER_AREA)
        self.crack4 = cv2.resize(crack, (w // 4, h // 4), interpolation=cv2.INTER_AREA)
        # 点亮时刻 T（本段秒），按 alpha 加权下采样到 unit 2
        T = self.t_sweep(ign[..., 0]) + ign[..., 1]
        T[crack <= 0] = 0
        num = cv2.resize(T * crack, (w // 2, h // 2), interpolation=cv2.INTER_AREA)
        self.T2 = num / np.maximum(self.crack2, 1e-4)
        self.T2[self.crack2 <= 1e-4] = 99.0
        n = np.load(os.path.join(WK, 'nrm.npy')).astype(np.float32)
        m = np.load(os.path.join(WK, 'matte.npy')).astype(np.float32) / 255
        self.m2 = cv2.resize(m, (n.shape[1], n.shape[0]), interpolation=cv2.INTER_AREA)
        self.nrm2 = np.ascontiguousarray(n)

    @staticmethod
    def t_sweep(nx):
        """高光带（半程向量方位 = 光方位/2）经过法线 nx 的时刻。"""
        phi = np.degrees(2 * np.arcsin(np.clip(nx, -0.999, 0.999)))
        p0, p1 = SWEEP['phi']; m0, m1 = SWEEP['move']
        u = np.clip((phi - p0) / (p1 - p0), 0, 1)
        tab = np.linspace(0, 1, 513); st = tab * tab * (3 - 2 * tab)
        return (m0 + (m1 - m0) * np.interp(u, st, tab)).astype(np.float32)


class FxSweep:
    """柔光扫过器身 + 开片沿线亮起。"""
    def __init__(self, R, aux, after='stage'):
        self.R, self.aux, self.after = R, aux, after

    def env(self, t):
        return sst(*SWEEP['on'], t) * (1 - sst(*SWEEP['off'], t))

    def statics(self, acc, t):
        """镜头静止时（全器 16.5 s 起）辅助图只贴一次。"""
        R, A = self.R, self.aux
        s, c = R.layer_xf(t)
        key = (round(float(s), 7), round(float(c[0]), 3), round(float(c[1]), 3))
        if getattr(self, 'key', None) == key:
            return self.cache
        mk = np.clip(warp(R, t, A.m2, 2), 0, 1)
        n = warp(R, t, A.nrm2, 2)
        al = warp(R, t, A.crack2, 2)
        T = warp(R, t, A.T2, 2, interp=cv2.INTER_NEAREST)
        lum = acc.mean(2)
        hp = lum - cv2.GaussianBlur(lum, (0, 0), 2.0 * R.SS * R.H / 720)
        tex = np.clip(1 + hp / 30.0, 0.6, 1.4)
        X, Y = world_x(R, t)
        gy = np.exp(-((Y - 2000) / 1600.0) ** 2)
        self.key, self.cache = key, (mk, n, al, T, tex, X, gy)
        return self.cache

    def draw(self, acc, t):
        R, A = self.R, self.aux
        e = self.env(t)
        g_out = 1 - sst(*GLOW_OUT, t)
        if e <= 1e-3 and (t < SWEEP['move'][0] or g_out <= 1e-3):
            return
        mk, n, al, T, tex, X, gy = self.statics(acc, t)
        if e > 1e-3:
            m0, m1 = SWEEP['move']
            u = sst(m0, m1, t)
            phi = math.radians(SWEEP['phi'][0] + (SWEEP['phi'][1] - SWEEP['phi'][0]) * u)
            el = math.radians(10)
            L = np.float32([math.sin(phi) * math.cos(el), -math.sin(el), math.cos(phi) * math.cos(el)])
            Hh = L + np.float32([0, 0, 1]); Hh /= np.linalg.norm(Hh)
            ndl = np.clip(n @ L, 0, 1); ndh = np.clip(n @ Hh, 1e-4, 1)
            f = 0.84 + 0.36 * ndl
            k = np.clip((ndl - 0.2) / 0.7, 0, 1)[..., None]
            warm = np.float32([1.05, 1.0, 0.93]); cool = np.float32([0.94, 0.99, 1.05])
            vf = f[..., None] * (cool + (warm - cool) * k)
            xp = 1450 + 1700 * math.sin(phi)
            gx = np.exp(-((X - xp) / 1300.0) ** 2)
            gg = gy[:, None] * gx[None, :]
            bf = (0.88 + 0.22 * gg)[..., None] * (1 + 0.04 * gg[..., None] * np.float32([1, 0.2, -0.8]))
            fac = vf * mk[..., None] + bf * (1 - mk[..., None])
            acc *= 1 + e * (fac - 1)
            lg = np.log(ndh)
            spec = np.minimum(0.42 * np.exp(26 * lg) + 0.30 * np.exp(6 * lg), 0.6) * mk * tex * e
            acc += spec[..., None] * (np.float32([250, 250, 242]) - acc)
        # 开片亮起（加色光：暖象牙色，核心 + 两层光晕，光晕在半分辨率上算）
        if t >= SWEEP['move'][0] and g_out > 1e-3:
            d = t - T
            on = np.clip(d / 0.22, 0, 1); on = on * on * (3 - 2 * on)
            I = np.clip(al * on * (0.55 + 0.45 * np.exp(-np.maximum(d, 0) / 1.1)) * g_out, 0, 1)
            k720 = R.SS * R.H / 720
            Ih = cv2.resize(I, (R.WS // 2, R.HS // 2), interpolation=cv2.INTER_AREA)
            h1 = cv2.resize(cv2.GaussianBlur(Ih, (0, 0), 1.3 * k720 / 2), (R.WS, R.HS), interpolation=cv2.INTER_LINEAR)
            h2 = cv2.resize(cv2.GaussianBlur(Ih, (0, 0), 5.0 * k720 / 2), (R.WS, R.HS), interpolation=cv2.INTER_LINEAR)
            core = np.float32([255, 236, 190]); halo = np.float32([255, 214, 150])
            w = np.clip(0.75 * I, 0, 0.9)
            acc += w[..., None] * (core - acc)
            acc += (np.clip(1.6 * h1, 0, 1) * 0.55 + np.clip(2.2 * h2, 0, 1) * 0.30)[..., None] * halo * 0.55
            np.minimum(acc, 255, out=acc)


def shots():
    D = DUR
    sh = []
    sh.append(('A_macro', [None, None, DISS[0], DISS[1]], {
        'duration': D, 'layers': [stage_layer()], 'sharpen': 0.2,
        'camera': {'rest': MACRO, 'keys': [K(0, **MACRO), K(6.5, **MACRO), K(12.2, 1455, 2605, 648, ease=1.5)]}}))
    b0 = dict(cx=1470, cy=2470, vh=2150)
    sh.append(('B_full', [DISS[0], DISS[1], None, None], {
        'duration': D, 'layers': [stage_layer()], 'sharpen': 0.25,
        'camera': {'rest': FULL, 'keys': [K(0, **b0), K(9.0, **b0), K(16.5, FULL['cx'], FULL['cy'], FULL['vh'], ease=1.3)]},
        'labels': [dict(LABEL, t0=16.0, t1=22.5, fade=1.0)]}))
    return sh


def weight(win, t):
    a0, a1, b0, b1 = win
    w = 1.0
    if a0 is not None:
        w *= sst(a0, a1, t)
    if b0 is not None:
        w *= 1.0 - sst(b0, b1, t)
    return w


class Multi:
    def __init__(self, res=720):
        self.aux = Aux()
        self.items = []
        for name, win, spec in shots():
            R = E.Renderer(spec, res)
            if name == 'B_full':
                R.fx.append(FxSweep(R, self.aux))
            self.items.append((name, win, R))
        R0 = self.items[0][2]
        self.W, self.H, self.fps = R0.W, R0.H, R0.fps
        self.nframes = int(round(DUR * self.fps))

    def check(self):
        for name, win, R in self.items:
            E.log(f'[{name}]'); R.check_speed()

    def render(self, t):
        acc = None; tot = 0.0
        for name, win, R in self.items:
            w = weight(win, t)
            if w <= 1e-4:
                continue
            fr = R.render(t).astype(np.float32)
            acc = fr * w if acc is None else acc + fr * w
            tot += w
        return np.clip(acc / tot + 0.5, 0, 255).astype(np.uint8)

    def mask(self, t):
        """开片线遮罩（屏幕上照片里真实裂纹的位置，白 = 裂纹），与成片逐帧对齐。"""
        acc = None; tot = 0.0
        for name, win, R in self.items:
            w = weight(win, t)
            if w <= 1e-4:
                continue
            s, c = R.layer_xf(t)
            unit = 1 if s > 0.7 else (2 if s > 0.35 else 4)
            src = {1: self.aux.crack1, 2: self.aux.crack2, 4: self.aux.crack4}[unit]
            m = warp(R, t, src, unit, SS=1)
            acc = m * w if acc is None else acc + m * w
            tot += w
        return np.clip(acc / tot * 255 + 0.5, 0, 255).astype(np.uint8)


BEATS = [
    ('开片微距铺满屏（静止，供"墨干成开片"转场）', 246.0),
    ('微距开始拉开', 252.5),
    ('叠化到中景', 255.6),
    ('到全器（背景 = s7 同一块绢）', 262.5),
    ('展签出', 262.0), ('展签收', 268.5),
    ('高光：柔光亮起、开始扫过器身（左→右）', 263.4),
    ('开片纹第一批亮起', 264.3),
    ('光扫到器身正中（最亮的一刻）', 267.8),
    ('光扫完，整片开片网亮着', 271.8),
    ('开片光退去', 273.2), ('全器静止（原照原色）', 276.8),
    ('段末（s7 淡为绢底 278–284）', 284.0)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('out'); ap.add_argument('--res', type=int, default=720)
    ap.add_argument('--frames', default=''); ap.add_argument('--stills', default='')
    ap.add_argument('--check', action='store_true'); ap.add_argument('--crf', type=int, default=12)
    ap.add_argument('--mask', default='')
    a = ap.parse_args()
    M = Multi(a.res)
    M.check()
    json.dump([{'what': s, 'global_s': g, 'local_s': round(g - G0, 2)} for s, g in BEATS],
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
    enc = ['-c:v', 'libx264', '-preset', 'medium', '-crf', str(a.crf), '-pix_fmt', 'yuv420p', '-movflags', '+faststart']
    ff = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{M.W}x{M.H}',
                           '-r', f'{M.fps:g}', '-i', '-'] + enc + [a.out + '.tmp.mp4'], stdin=subprocess.PIPE)
    fm = None
    if a.mask:
        fm = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'gray', '-s', f'{M.W}x{M.H}',
                               '-r', f'{M.fps:g}', '-i', '-'] + enc + [a.mask + '.tmp.mp4'], stdin=subprocess.PIPE)
    tr = time.time()
    for i in range(f0, f1):
        t = i / M.fps
        ff.stdin.write(M.render(t).tobytes())
        if fm is not None:
            fm.stdin.write(M.mask(t).tobytes())
        if (i - f0) % 30 == 0:
            E.log(f'frame {i}/{f1}  {(time.time() - tr) / (i - f0 + 1):.2f}s/帧')
    ff.stdin.close(); ff.wait()
    os.replace(a.out + '.tmp.mp4', a.out)
    if fm is not None:
        fm.stdin.close(); fm.wait(); os.replace(a.mask + '.tmp.mp4', a.mask)
    E.log(f'完成 {a.out}')


if __name__ == '__main__':
    try:
        main()
    except E.EngineError as e:
        print('ENGINE ERROR:', e, file=sys.stderr); sys.exit(2)
