# -*- coding: utf-8 -*-
"""S4《千里江山图》2:47–4:02（75 s）第二版。帧 0 = 2:47。
 A 0–10s    水面网纹铺满屏（淡墨→青绿渗入），水纹明显在流，小舟明显在走
 B 8–18.5s  全卷全貌（lib/scrollview.py 长案透视；未就绪时退回横带）
 C 16–75s   平远展卷（远山/水/近岸三层纵深视差，水流、小舟）→ 群峰停（呼吸）→ 一直推进：
            3:40.8–3:49 主峰"一层层罩染"（褪成墨线 → 赭石自下漫上 → 石绿自山脊漫下 → 石青自峰顶晕开）
            → 3:54 过 1:1 → 石青自峰顶向四周漫开铺满整屏 → 4:02 约 1.6× 原图像素，颗粒清楚
用法: python3 render.py OUT.mp4 [--stills 0,300] [--frames a:b] [--mask MASK.mp4] [--res 720]"""
import sys, os, math, argparse, subprocess, time
import numpy as np, cv2
S = '~/claude-projects/china-art/series/'
sys.path.insert(0, S + 'lib'); sys.path.insert(0, S + 'segs/qianli')
import engine as E
import render_v1 as V1
D = S + 'segs/qianli/data/'
W0, H0 = 153767, 6110
FPS = 30
DUR = 75.0
sstep = V1.sstep

# ---------------------------------------------------------------- A 水面
FLOW_A = dict(V1.FLOW_FULL, speed=30, period=150, streak=4)

def boatsA():
    # 10 s 内约 1.3 个身长（小舟身长约 384 世界像素）
    return [
        {'type': 'drift', 'layer': 'full', 'sprite': D + 'boatM.npy', 'origin': [85122, 5571], 'unit': 1,
         'path': [[0, 0, 0], [11, -520, 10]], 'tilt': {'deg': 0.5, 'period': 3.2}, 'body': 1200, 'cache_name': 'qianli_boatM'},
        {'type': 'drift', 'layer': 'full', 'sprite': D + 'boatR.npy', 'origin': [85472, 5378], 'unit': 1,
         'path': [[0, 0, 0], [11, -560, -8]], 'tilt': {'deg': 0.45, 'period': 3.7}, 'body': 1200, 'cache_name': 'qianli_boatR'},
    ]

def seg_A():
    s = V1.seg_A(); s['fx'] = [FLOW_A] + boatsA(); s['ss'] = 1; return s

# ---------------------------------------------------------------- C 相机
S0 = dict(cx=97600, cy=3055, vh=8730)
S1 = dict(cx=85300, cy=3950, vh=3400)
TGT = np.array([85160.0, 2560.0])        # 峰顶石青
T_PAN0, T_PAN1, T_PUSH = 18.0, 36.0, 39.0
RATE = 0.0585                            # ln/s（< 6 %/s）
RAMP = 2.0

class CamC:
    def __init__(self, scale=1.0):
        self.scale = scale
        self.rest_c = np.array([S1['cx'], S1['cy']], float); self.rest_vh = S1['vh'] * scale
        k0 = dict(t=T_PAN0, **S0); k1 = dict(t=T_PAN1, ease=2.0, **S1)
        self.pan = E.Camera({'keys': [k0, k1]}, FPS)

    def lnz(self, t):                    # 推进累计 ln 缩放
        u = t - T_PUSH
        if u <= 0:
            return 0.0
        if u < RAMP:
            return RATE * u * u / (2 * RAMP)
        return RATE * (RAMP / 2 + u - RAMP)

    def state(self, t):
        if t <= T_PAN1:
            c, vh = self.pan.state(t)
        else:
            vh = S1['vh'] * math.exp(-self.lnz(t))
            k = (vh / S1['vh']) ** 2
            c = TGT + (np.array([S1['cx'], S1['cy']]) - TGT) * k
        return np.array(c, float), vh * self.scale

def seg_C(pm, dur=DUR):
    fl_ds3 = {'type': 'flow', 'layer': 'ds3', 'after': 'full', 'mask': np.load(pm), 'origin': [78000, 3900], 'unit': 3,
              'dir': [-1, 0.12], 'speed': 75, 'period': 300, 'streak': 5, 'strength': 1.0, 't1': 58}
    fl_full = dict(V1.FLOW_FULL, speed=75, period=300, streak=5, t1=58)
    boats = [
        {'type': 'drift', 'layer': 'full', 'sprite': D + 'boatM.npy', 'origin': [85122, 5571], 'unit': 1,
         'path': [[24, 0, 0], [50, -900, 16]], 'tilt': {'deg': 0.4, 'period': 3.4}, 'body': 1200, 'cache_name': 'qianli_boatM', 't1': 58},
        {'type': 'drift', 'layer': 'full', 'sprite': D + 'boatR.npy', 'origin': [85472, 5378], 'unit': 1,
         'path': [[24, 0, 0], [50, -950, -12]], 'tilt': {'deg': 0.35, 'period': 3.9}, 'body': 1200, 'cache_name': 'qianli_boatR', 't1': 58},
    ]
    layers = [V1.wall_local(),
              {'name': 'ds3', 'src': D + 'q_ds3p.npy', 'origin': [78000, 0], 'unit': 3, 'crop': [78000, 0, 108000, H0], 'feather': 0,
               'cache_name': 'qianli_ds3p'},
              {'name': 'full', 'src': D + 'q_full.npy', 'origin': [84000, 0], 'unit': 1, 'crop': [84000, 0, 86400, H0], 'feather': 140,
               'cache_name': 'qianli_full'}]
    return {'fps': FPS, 'duration': dur, 'layers': layers, 'ss': 1,
            'camera': {'rest': S1, 'keys': [dict(t=0, **S0), dict(t=1, **S0)]},
            'fx': [fl_ds3, fl_full] + boats}

# ---------------------------------------------------------------- 纵深视差（平远展卷）
DEP = np.load(D + 'depth12.npy'); DEP_O = (66000.0, -6000.0); DEP_U = 12.0
PAR_FAR, PAR_NEAR = 1.0, 1.045          # 远山=画面基准（与全貌落点、罩染同一坐标），水面向近岸越近越快
PAR_REF = np.array([S0['cx'], S0['cy']])  # 视差零点 = 全貌落地状态 S0（叠化无重影）

def parallax(canvas, t, cam, W, H):
    """canvas: 视差=1 渲出的、四周各多出 (mx,my) 像素的画面；按纵深图把每个像素换成它所在深度层的位置。"""
    c, vh = cam.state(t)
    Hc, Wc = canvas.shape[:2]
    s = Hc / vh
    delta = c - PAR_REF
    mx, my = (Wc - W) // 2, (Hc - H) // 2
    # 纵深图 → 输出屏幕（与画布同一比例）
    M = np.float32([[s * DEP_U, 0, Wc / 2 + s * (DEP_O[0] + 0.5 * DEP_U - c[0]) - 0.5 - mx],
                    [0, s * DEP_U, Hc / 2 + s * (DEP_O[1] + 0.5 * DEP_U - c[1]) - 0.5 - my]])
    d = cv2.warpAffine(DEP, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
    par = PAR_FAR + (PAR_NEAR - PAR_FAR) * d
    qx, qy = np.meshgrid(np.arange(W, dtype=np.float32) + mx, np.arange(H, dtype=np.float32) + my)
    mapx = qx + s * (par - 1) * delta[0]; mapy = qy + s * (par - 1) * delta[1]
    return cv2.remap(canvas, mapx.astype(np.float32), mapy.astype(np.float32), cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT)

# ---------------------------------------------------------------- 一层层罩染
ZR = np.load(D + 'zr_maps.npy'); ZRX, ZRY, ZRU = np.load(D + 'zr_meta.npy'); SKY = np.load(D + 'zr_sky.npy')
Z0, Z_INK, Z_OCH, Z_GRN, Z_BLU, Z1 = 53.8, 55.0, 55.6, 57.3, 59.3, 62.2

def warp_world(img, ox, oy, u, c, vh, W, H):
    s = H / vh
    M = np.float32([[s * u, 0, W / 2 + s * (ox + 0.5 * u - c[0]) - 0.5], [0, s * u, H / 2 + s * (oy + 0.5 * u - c[1]) - 0.5]])
    return cv2.warpAffine(img, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)

def front(T, p, w=0.10):
    x = p - T
    a = sstep(0.0, w, x)
    e = np.exp(-((x - 0.35 * w) / (0.45 * w)) ** 2)      # 湿边：水洗前沿颜料堆积
    return a, e

def prog(t, t0, t1, lo=-0.25, hi=1.45):
    u = float(np.clip((t - t0) / (t1 - t0), 0, 1)); u = u * u * (3 - 2 * u)
    return lo + (hi - lo) * u

_sl = float(SKY @ np.float32([0.3, 0.55, 0.15]))
BARE = ((_sl + (SKY - _sl) * 0.55) * 1.10).astype(np.float32)      # 未上色的素绢：比画里的"天"略浅略灰

def stages(O):
    L = O @ np.float32([0.3, 0.55, 0.15])
    ch = O.max(2) - O.min(2)
    ink = sstep(100, 46, L) * sstep(90, 38, ch)
    hp = L - cv2.GaussianBlur(L, (0, 0), 1.3 * O.shape[0] / 720)     # 墨线细节尺度按 720p 等比
    P0 = BARE[None, None, :] * (1 - 0.80 * ink[..., None]) + np.float32([20, 16, 12]) * 0.80 * ink[..., None] + 0.7 * hp[..., None]
    och = L[..., None] * np.float32([1.20, 0.95, 0.50]) + np.float32([6, 3, 0])
    hsv = cv2.cvtColor(np.clip(O, 0, 255).astype(np.uint8), cv2.COLOR_RGB2HSV).astype(np.float32)
    B_ = O[..., 2] - O[..., 0]
    b = sstep(8, 40, B_) * sstep(-25, 5, O[..., 2] - O[..., 1])
    hsv[..., 0] = np.clip(hsv[..., 0] - 30 * b, 0, 179)
    hsv[..., 2] = np.clip(hsv[..., 2] * (1 + 0.10 * b), 0, 255)
    grn = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2RGB).astype(np.float32)
    return P0, och, grn

def zr_apply(fr, t, c, vh):
    if t < Z0 or t > Z1:
        return fr
    H, W = fr.shape[:2]
    O = fr.astype(np.float32)
    m = warp_world(ZR, ZRX, ZRY, ZRU, c, vh, W, H)
    Mg, Ttop, Tbot = m[..., 1], m[..., 3], m[..., 4]
    P0, och, grn = stages(O)
    wet = np.zeros((H, W), np.float32)
    if t < Z_INK + 0.05:                                       # 褪成墨线：自上而下洗掉
        a0, e0 = front(Ttop, prog(t, Z0, Z_INK), 0.16)
        C = O + (P0 - O) * a0[..., None]
        wet += 0.5 * e0
    else:
        C = P0
        a1, e1 = front(Tbot, prog(t, Z_OCH, Z_OCH + 2.0), 0.14)
        C = C + (och - C) * a1[..., None]; wet += e1 * 0.8
        a2, e2 = front(Ttop, prog(t, Z_GRN, Z_GRN + 2.3), 0.10)
        a2 = a2 * Mg
        C = C + (grn - C) * a2[..., None]; wet += e2 * Mg
        a3, e3 = front(Ttop, prog(t, Z_BLU, Z_BLU + 2.7), 0.10)
        C = C + (O - C) * a3[..., None]; wet += 1.2 * e3 * np.clip(Mg + 0.2, 0, 1)
    wet = np.clip(wet, 0, 1.2)[..., None]
    lum = C @ np.float32([0.3, 0.55, 0.15])
    C = lum[..., None] + (C - lum[..., None]) * (1 + 0.35 * wet)        # 湿处更艳
    C = C * (1 - 0.20 * wet)                                              # 湿边略深
    return np.clip(C + 0.5, 0, 255).astype(np.uint8)

# ---------------------------------------------------------------- 石青漫开 + 颗粒
FLD = np.load(D + 'fl_dist.npy'); FLX, FLY, FLU = np.load(D + 'fl_meta.npy')
F0, F1 = 65.5, 71.5
_q = np.load(D + 'q_full.npy', mmap_mode='r')
_cap = np.ascontiguousarray(_q[2440:2700, 1000:1340]).astype(np.float32)
_bb = _cap[..., 2] - _cap[..., 0]
AZ = np.median(_cap[_bb > np.percentile(_bb, 70)], 0).astype(np.float32)
del _q
AZT = E.silk_wall('qianli_azurite', [(D + 'q_full.npy', [1010, 2480, 1330, 2670])], (1500, 1000), unit=1, tex_scale=1.0,
                  tone=(1.0, 1.0, 1.0), light=None, shadow=None, patch=150, seed=3)
AZT = np.load(AZT).astype(np.float32); AZX, AZY = 84400.0, 2050.0

def flood_grain(fr, t, c, vh):
    if t < F0 - 2.5:
        return fr
    H, W = fr.shape[:2]
    kr = H / 720.0                                               # 模糊半径按 720p 像素写，1080p 等比放大
    O = fr.astype(np.float32)
    L = O @ np.float32([0.3, 0.55, 0.15])
    C = O
    if t >= F0:
        dist = warp_world(FLD, FLX, FLY, FLU, c, vh, W, H)
        u = float(np.clip((t - F0) / (F1 - F0), 0, 1)); u = u * u * (3 - 2 * u)
        p = -40 + 900 * u                                        # 前沿（世界像素）
        x = p - dist
        a = sstep(0, 70, x); e = np.exp(-((x - 25) / 30) ** 2)
        B_ = O[..., 2] - O[..., 0]
        isb = sstep(20, 55, B_)
        hp = L - cv2.GaussianBlur(L, (0, 0), 1.6 * kr)
        lo = cv2.GaussianBlur(L, (0, 0), 18 * kr); lo = (lo - lo.mean()) * 0.25
        s_ = H / vh
        Mz = np.float32([[s_, 0, W / 2 + s_ * (AZX + 0.5 - c[0]) - 0.5], [0, s_, H / 2 + s_ * (AZY + 0.5 - c[1]) - 0.5]])
        tex = cv2.warpAffine(AZT, Mz, (W, H), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT)
        lo = cv2.GaussianBlur(L, (0, 0), 14 * kr); lo = (lo - lo.mean()) / max(1.0, float(lo.mean()))
        F = tex * (1 + 0.45 * lo[..., None])
        k = (a * (1 - 0.6 * isb))[..., None]
        C = O + (F - O) * k
        C = C * (1 - 0.12 * e[..., None])
    g = 0.9 * float(sstep(F0 - 2.5, F1 + 1.0, t))                    # 颗粒：越推越清楚
    bl = cv2.GaussianBlur(C, (0, 0), 1.1 * kr)
    C = C + g * (C - bl)
    return np.clip(C + 0.5, 0, 255).astype(np.uint8)

# ---------------------------------------------------------------- B 全貌（lib/scrollview.py 长案透视，与清明同一语法）
# 世界坐标 = ds3 像素（原图 /3）；落点 = C 段起点 S0 的正俯视
B_LAND = dict(cx=S0['cx'] / 3, cy=S0['cy'] / 3, vh=S0['vh'] / 3)
B_T = (8.0, 12.6, 18.0)                  # 可见起 / 环移止 / 落地
B_LABEL = {'text': ['千里江山圖', '北宋　王希孟', '絹本青綠設色', '五一·五×一一九一·五厘米', '北京故宮博物院藏'],
           'x': 0.955, 'y': 0.08, 't0': 9.4, 't1': 14.6, 'fade': 0.9, 'color': '#EDE6D8', 'title_size': 26, 'size': 22}

class ShotB:
    def __init__(self, res=720):
        import scrollview as SV
        self.SV = SV
        silk = [(D + 'mount_silk.npy', [0, 0, 760, 4300])]
        sv = SV.ScrollView(D + 'q_ds3_whole.npy', 'qianli', silk, tone=(0.84, 0.80, 0.71), res=res, ss=1, tex_scale=0.55)
        self.F = SV.overview_shot(sv, B_T[0], B_T[1], B_T[2], B_LAND, light_sweep=(9.0, 12.6, 7000, 0.42))
        self.FL = E.Renderer({'fps': FPS, 'duration': DUR, 'ss': 1, 'layers': [],
                              'camera': {'keys': [dict(t=0, cx=0, cy=0, vh=1000)]}, 'labels': [B_LABEL]}, res)
        E.log('全貌: 环移峰 %.2f px/帧 @%.1fs，俯冲峰 %.2f px/帧 @%.1fs' % (
            SV.speed_report(self.F, B_T[0], B_T[1]) + SV.speed_report(self.F, B_T[1], B_T[2])))

    def render(self, t):
        fr = self.F.frame(min(t, B_T[2])).astype(np.float32)
        for lb in self.FL.labels:
            lb.draw(fr, t)
        return np.clip(fr + 0.5, 0, 255).astype(np.uint8)

# ---------------------------------------------------------------- 总装
def main():
    ap = argparse.ArgumentParser(); ap.add_argument('out'); ap.add_argument('--res', type=int, default=720)
    ap.add_argument('--stills', default=''); ap.add_argument('--frames', default=''); ap.add_argument('--mask', default='')
    ap.add_argument('--crf', type=int, default=12)
    a = ap.parse_args()
    RES = int(a.res)                     # 720 草稿 / 1080 终版：几何全在世界坐标，视差画布按比例放大（720→900，1080→1350）
    assert RES in (720, 1080)
    p16, pm = V1.prep_files()
    n = int(round(DUR * FPS))
    f0, f1 = (map(int, a.frames.split(':')) if a.frames else (0, n))
    if a.stills:
        st = [int(x) for x in a.stills.split(',') if x]; f0, f1 = min(st), max(st) + 1
    need = lambda t0, t1: f0 < t1 * FPS and f1 > t0 * FPS
    RA = E.Renderer(seg_A(), RES) if need(0, 10) else None
    RB = ShotB(RES) if need(8, 18.3) else None
    RC = RW = None
    if need(17.7, 75):
        RC = E.Renderer(seg_C(pm), RES); RC.cam = CamC(1.0)
        RW = E.Renderer(seg_C(pm), RES * 5 // 4); RW.cam = CamC(1.25)
        E.log('C 速度'); RC.check_speed(); RW.check_speed()
    RM = E.Renderer(dict(V1.seg_A_mask(), ss=1), RES) if (a.mask and RA) else None
    H = RES; W = int(round(H * 16 / 9 / 2) * 2)

    def renderC(t):
        if t < 52.0:
            fr = parallax(RW.render(t), t, RW.cam, W, H)
        else:
            fr = RC.render(t)
        c, vh = RC.cam.state(t)
        fr = zr_apply(fr, t, c, vh)
        fr = flood_grain(fr, t, c, vh)
        return fr

    def frame(i):
        t = i / FPS
        if t < 8.0:
            return V1.bleed(RA.render(t), t, H), 1.0
        if t < 10.0:
            w = float(sstep(8.0, 10.0, t))
            fa = V1.bleed(RA.render(t), t, H).astype(np.float32); fb = RB.render(t).astype(np.float32)
            return np.clip(fa * (1 - w) + fb * w + 0.5, 0, 255).astype(np.uint8), 1 - w
        if t < 17.7:
            return RB.render(t), 0.0
        if t < 18.3:
            w = float(sstep(17.7, 18.3, t))
            fb = RB.render(t).astype(np.float32); fc = renderC(t).astype(np.float32)
            return np.clip(fb * (1 - w) + fc * w + 0.5, 0, 255).astype(np.uint8), 0.0
        return renderC(t), 0.0

    if a.stills:
        base = os.path.splitext(a.out)[0]
        for i in [int(x) for x in a.stills.split(',') if x]:
            tr = time.time(); fr, _ = frame(i)
            cv2.imwrite(f'{base}_f{i:04d}.png', cv2.cvtColor(fr, cv2.COLOR_RGB2BGR)); E.log(f'still {i} {time.time() - tr:.2f}s')
        return
    def pipe(path):
        return subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}',
                                 '-r', str(FPS), '-i', '-', '-c:v', 'libx264', '-preset', 'medium', '-crf', str(a.crf),
                                 '-pix_fmt', 'yuv420p', '-movflags', '+faststart', path], stdin=subprocess.PIPE)
    ff = pipe(a.out); fm = pipe(a.mask) if a.mask else None
    black = np.zeros((H, W, 3), np.uint8)
    tr = time.time()
    for i in range(f0, f1):
        fr, wa = frame(i)
        ff.stdin.write(fr.tobytes())
        if fm is not None:
            if wa > 0:
                m = RM.render(i / FPS).astype(np.float32) * wa
                fm.stdin.write(np.clip(m + 0.5, 0, 255).astype(np.uint8).tobytes())
            else:
                fm.stdin.write(black.tobytes())
        if (i - f0) % 30 == 0:
            E.log(f'frame {i}/{f1}  {(time.time() - tr) / (i - f0 + 1):.2f}s/帧')
    ff.stdin.close(); ff.wait()
    if fm is not None:
        fm.stdin.close(); fm.wait()
    E.log(f'完成 {a.out}')

if __name__ == '__main__':
    try:
        main()
    except E.EngineError as e:
        print('ENGINE ERROR:', e, file=sys.stderr); sys.exit(2)
