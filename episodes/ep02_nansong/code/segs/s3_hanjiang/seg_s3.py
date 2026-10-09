# -*- coding: utf-8 -*-
"""s3 传马远《寒江独钓图》· 全局 108–174（帧 0 = 108 s），66 s，1280×720 30 fps。
  0–9    全貌静止（总装在这里做"留白"收墨转场）
  9.6–20.2 展签（墙面右侧，竖排）
  13–18  船开始轻轻起伏（刚体，≤0.6°，另有 ±3 px 升沉；钓丝以入水点为定点随竿梢做相似变换，不变形）
  20.2–56.5 镜头从全画极缓推向钓丝入水点（对数匀速，峰值约 4.7%/s）
  22.4 起 每约 7 s 入水点扩出一组同心涟漪（线质取自原作船下水纹：淡墨细线、前实后虚、侧锋略粗）
  52.6–66 涟漪一圈圈加密、不再消散，铺满全屏（总装 166–174 做"涟漪变水图"，遮罩另出）
用法（重活走锁，成片后台）：
  lockf -k $S/.heavy.lock python3 seg_s3.py OUT.mp4 [--mask MASK.mp4] [--frames a:b] [--stills 0,300] [--check]
"""
import os, sys, time, math, json, argparse, subprocess
import numpy as np, cv2
HERE = os.path.dirname(os.path.abspath(__file__))
S = '~/claude-projects/china-art/series'
sys.path.insert(0, os.path.join(S, 'lib'))
import engine as E

WK = os.path.join(HERE, 'work')
META = json.load(open(os.path.join(WK, 'meta.json')))
PW, PH = META['W'], META['H']
G0, DUR = 108.0, 66.0

# ---------------------------------------------------------------- 构图
SF = 930.0 / PW                                   # 全貌：画宽 930 px（左留 44 px），右侧墙面放展签
FULL = {'cx': PW / 2 + (640 - 44 - 465) / SF, 'cy': PH / 2, 'vh': 720 / SF}
CLOSE = {'cx': 840, 'cy': 2230, 'vh': 900}        # 推到入水点：渔翁已出画，竿梢从右上伸入
PUSH = (20.2, 56.5, 3.5)                          # 起、止、每端缓入缓出
LABEL = {'text': ['寒江獨釣圖', '南宋　傳馬遠', '絹本墨畫淡彩', '二六·七×五〇·六厘米', '東京國立博物館藏'],
         'x': 1236 / 1280, 'y': (360 - PH / 2 * SF) / 720, 't0': 9.6, 't1': 20.2, 'fade': 1.0, 'color': '#2b251d'}

ENTRY = np.float64(META['entry'])                 # 钓丝入水点 = 涟漪圆心
TIP = np.float64(META['tip'])                     # 竿梢
PIVOT = np.float64([2700, 2110])                  # 船底中点
BOB = dict(deg=0.6, heave=3.0, period=5.6, on=(13.0, 18.0))

# ---------------------------------------------------------------- 涟漪
ASP = 0.40                                        # 水面透视：椭圆纵横比（按原作船下弧线）
INK = np.float32([52, 36, 19])                    # 比原作水纹（77,53,27）略浓，保证全貌时也看得见
REG = [22.4, 29.3, 36.2, 43.1, 49.9]              # 常规：每约 7 s 一组
FIN = [52.6, 54.0, 55.3, 56.6, 57.9, 59.2, 60.5, 61.8, 63.1, 64.4, 65.7]   # 收尾：加密、不消散


def ring_list():
    rng = np.random.default_rng(11)
    R = []
    for i, tb in enumerate(REG):
        final = tb >= 49
        for j, (dl, st) in enumerate(zip([0, 0.42, 0.9], [1.0, 0.72, 0.48])):
            R.append(dict(tb=tb + dl, v=125.0 - 8 * j, st=st, life=None if final else 9.0, back=0.16, ph=rng.uniform(0, 2 * np.pi, 8)))
    for i, tb in enumerate(FIN):
        for j, (dl, st) in enumerate(zip([0, 0.45], [0.95, 0.5])):
            R.append(dict(tb=tb + dl, v=165.0 - 6 * j, st=st, life=None, back=0.5, ph=rng.uniform(0, 2 * np.pi, 8)))
    return R


RINGS = ring_list()


def sst(a, b, x):
    return float(E.sstep(a, b, x))


def K(t, st, ease=None):
    k = {'t': t, 'cx': st['cx'], 'cy': st['cy'], 'vh': st['vh']}
    if ease is not None:
        k['ease'] = ease
    return k


def build():
    samples = [(p, r) for p, r in META['samples']]
    ox, oy = -1000, -1400
    size = (9800, 6000)
    sh = {'rect': [-ox, -oy, -ox + PW, -oy + PH], 'offset': [40, 30], 'blur': 32, 'strength': 0.26}
    light = {'center': [-ox + PW * 0.62, -oy + PH * 0.42], 'radius': FULL['vh'] * 16 / 9 * 0.62, 'falloff': 0.16}
    wp = E.silk_wall('hanjiang', samples, size, unit=8, tex_scale=1.6, tone=tuple(META['tone']), light=light, shadow=sh)
    p0, p1, pe = PUSH
    return {
        'duration': DUR, 'fps': 30, 'ss': 2, 'sharpen': 0.25,
        'layers': [{'name': 'wall', 'src': wp, 'origin': [ox, oy], 'unit': 8, 'cache_name': 'hj_wall'},
                   {'name': 'paint', 'src': os.path.join(WK, 'plate.npy'), 'origin': [0, 0], 'unit': 1, 'cache_name': 'hj_plate'}],
        'camera': {'rest': FULL, 'keys': [K(0, FULL), K(p0, FULL), K(p1, CLOSE, ease=pe)]},
        'labels': [LABEL],
    }


# ---------------------------------------------------------------- 船与钓丝
def bob(t):
    a = sst(*BOB['on'], t)
    w = 2 * math.pi * t / BOB['period']
    return a * BOB['deg'] * math.sin(w), a * BOB['heave'] * math.sin(w - 1.2)


def rot(th_deg, v):
    th = math.radians(th_deg)
    return np.float64([math.cos(th) * v[0] - math.sin(th) * v[1], math.sin(th) * v[0] + math.cos(th) * v[1]])


class FxBoat:
    after = 'paint'

    def __init__(self, R):
        self.R = R
        self.lv = E.build_mips(os.path.join(WK, 'boat.npy'), name='hj_boat')
        self.org = np.float64(META['boat_origin'])

    def draw(self, acc, t):
        th, hv = bob(t)
        off = np.float64([0, hv])
        s, c = self.R.layer_xf(t)
        self.R.draw_image(acc, self.lv, self.org + off, 1.0, s, c, rot_deg=th, pivot=PIVOT + off)


class FxLine:
    """钓丝：入水点不动，竿梢跟船走 → 以入水点为定点的相似变换（旋转+极小缩放），线形不变。"""
    after = 'paint'

    def __init__(self, R):
        self.R = R
        self.lv = E.build_mips(os.path.join(WK, 'line.npy'), name='hj_line')
        self.org = np.float64(META['line_origin'])

    def draw(self, acc, t):
        th, hv = bob(t)
        tip2 = PIVOT + np.float64([0, hv]) + rot(th, TIP - PIVOT)
        v, v2 = TIP - ENTRY, tip2 - ENTRY
        k = float(np.hypot(*v2) / np.hypot(*v))
        g = math.degrees(math.atan2(v2[1], v2[0]) - math.atan2(v[1], v[0]))
        s, c = self.R.layer_xf(t)
        org = ENTRY + k * (self.org - ENTRY)
        self.R.draw_image(acc, self.lv, org, k, s, c, rot_deg=g, pivot=ENTRY)


# ---------------------------------------------------------------- 涟漪（极坐标缓冲：每圈只写一条窄带，再一次 remap 到屏幕）
NPHI, RSTEP, RMAX = 1024, 0.5, 3000.0
NR = int(RMAX / RSTEP)
PHI = (np.arange(NPHI, dtype=np.float64) + 0.0) * 2 * np.pi / NPHI


def ring_radius(rg, t):
    age = t - rg['tb']
    if age <= 0:
        return None
    return 8.0 + rg['v'] * age * (1 - 0.018 * min(age, 14))


def ring_amp(rg, t, r):
    age = t - rg['tb']
    a = sst(0.0, 0.35, age) * rg['st']
    if rg['life'] is not None:
        L = rg['life']
        a *= 1 - sst(L - 3.4, L, age)
    a *= 1.0 / (1 + r / 2200.0)
    return a


class FxRipples:
    after = 'paint'

    def __init__(self, R):
        self.R = R
        self.alpha_ss = None        # 最近一帧的涟漪线 alpha（SS 分辨率），给遮罩输出

    def polar(self, t, sig_w):
        cosp, sinp = np.cos(PHI), np.sin(PHI)
        grad = np.sqrt(cosp ** 2 + (sinp / ASP) ** 2)                 # |∇ρ|：底边（前方）ρ 方向要更宽才得到同样的线宽
        sm = np.clip((sinp + 0.35) / 0.8, 0, 1)
        sm = sm * sm * (3 - 2 * sm)                                      # 前实后虚（原作水纹只画近处的弧）
        idx_all, val_all = [], []
        rmax = 0.0
        for rg in RINGS:
            r = ring_radius(rg, t)
            if r is None or r > RMAX - 100:
                continue
            a = ring_amp(rg, t, r)
            if a < 0.01:
                continue
            ph = rg['ph']
            # 手画的圈：不正圆、略偏心（偏心随半径长），不是同心靶环
            ex_, ey_ = 0.035 * r * math.sin(ph[6]), 0.02 * r * math.cos(ph[7])
            rr = r * (1 + 0.022 * np.sin(2 * PHI + ph[0]) + 0.013 * np.sin(3 * PHI + ph[1])) + ex_ * cosp + ey_ / ASP * sinp
            tex = (1 + 0.18 * np.sin(2 * PHI + ph[2]) + 0.12 * np.sin(9 * PHI + ph[3])) * (0.86 + 0.14 * np.sin(23 * PHI + ph[1]))
            # 后半（远处）断笔：两处缺口
            gap = 1 - 0.9 * np.exp(-((np.angle(np.exp(1j * (PHI - (1.25 * np.pi + 0.5 * math.sin(ph[4]))))) / 0.3) ** 2)) \
                    - 0.8 * np.exp(-((np.angle(np.exp(1j * (PHI - (1.75 * np.pi + 0.4 * math.sin(ph[5]))))) / 0.24) ** 2))
            front = rg['back'] + (1 - rg['back']) * sm
            amp = a * front * tex * np.clip(gap, 0, 1) * 0.95
            wmod = (0.62 + 0.6 * np.abs(cosp) ** 1.5) * (1 + 0.22 * np.sin(4 * PHI + ph[2]))   # 两侧侧锋略粗、底边细
            sr = sig_w * wmod * grad / RSTEP                               # ρ 方向 σ（格）
            c = rr / RSTEP
            Kh = int(math.ceil(3.2 * sr.max()))
            ks = np.arange(-Kh, Kh + 1)
            j = np.floor(c)[:, None] + ks[None, :]
            val = amp[:, None] * np.exp(-0.5 * ((j - c[:, None]) / sr[:, None]) ** 2)
            ok = (j >= 0) & (j < NR)
            ii = np.broadcast_to(np.arange(NPHI)[:, None], j.shape)
            idx_all.append((ii[ok] * NR + j[ok].astype(np.int64)))
            val_all.append(val[ok])
            rmax = max(rmax, r * 1.03 + 4 * sig_w * 2.5)
        if not idx_all:
            return None, 0
        buf = np.bincount(np.concatenate(idx_all), weights=np.concatenate(val_all), minlength=NPHI * NR)
        P = np.minimum(buf.reshape(NPHI, NR).astype(np.float32), 1.0)
        P = np.vstack([P, P[:1]])                                           # φ 环绕
        return P, rmax

    def draw(self, acc, t):
        R = self.R
        self.alpha_ss = None
        s, c = R.layer_xf(t)
        sig_w = max(1.8, 1.0 / s)                                           # 世界像素；全貌时保证屏上 ≥0.85 px
        P, rmax = self.polar(t, sig_w)
        if P is None:
            return
        SS = R.SS
        # 屏幕上涟漪外接框
        ex, ey = ENTRY
        bx0, bx1 = ex - rmax, ex + rmax
        by0, by1 = ey - rmax * ASP * 1.05, ey + rmax * ASP * 1.05
        X0 = max(0, int(math.floor(SS * (R.W / 2 + s * (bx0 - c[0]))))); X1 = min(R.WS, int(math.ceil(SS * (R.W / 2 + s * (bx1 - c[0])))) + 1)
        Y0 = max(0, int(math.floor(SS * (R.H / 2 + s * (by0 - c[1]))))); Y1 = min(R.HS, int(math.ceil(SS * (R.H / 2 + s * (by1 - c[1])))) + 1)
        if X1 <= X0 or Y1 <= Y0:
            return
        # 极坐标 → 屏幕：在 1× 分辨率上算（线宽 σ ≥ 1 屏幕像素，1× 采样足够），再放大到 SS
        x0h, x1h, y0h, y1h = X0 // SS, -(-X1 // SS), Y0 // SS, -(-Y1 // SS)
        Xh = c[0] + ((np.arange(x0h, x1h, dtype=np.float32) + 0.5) - R.W / 2) / s
        Yh = c[1] + ((np.arange(y0h, y1h, dtype=np.float32) + 0.5) - R.H / 2) / s
        dx = (Xh - ex)[None, :]
        dy = ((Yh - ey) / ASP)[:, None]
        rho = np.sqrt(dx * dx + dy * dy)
        phi = np.arctan2(np.broadcast_to(dy, rho.shape), np.broadcast_to(dx, rho.shape))
        mx = (rho / RSTEP).astype(np.float32)
        my = (np.mod(phi, 2 * np.pi) * (NPHI / (2 * np.pi))).astype(np.float32)
        ah = cv2.remap(P, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
        # 只在画心里（边缘 40 世界像素羽化）
        fe = 40.0
        cx_ = np.clip(np.minimum(Xh - 6, PW - 6 - Xh) / fe, 0, 1); cy_ = np.clip(np.minimum(Yh - 6, PH - 6 - Yh) / fe, 0, 1)
        ah *= (cy_[:, None] * cx_[None, :])
        X0, X1, Y0, Y1 = x0h * SS, min(R.WS, x1h * SS), y0h * SS, min(R.HS, y1h * SS)
        a = cv2.resize(ah, ((x1h - x0h) * SS, (y1h - y0h) * SS), interpolation=cv2.INTER_LINEAR)[:Y1 - Y0, :X1 - X0]
        roi = acc[Y0:Y1, X0:X1]
        lum = roi.mean(2)
        hp = lum - cv2.GaussianBlur(lum, (0, 0), 2.0)
        tex = np.clip(1 + hp / 22.0, 0.75, 1.25)                            # 墨吃进绢纹
        ae = np.clip(a * tex, 0, 1)[..., None]
        roi += ae * (INK - roi)
        full = np.zeros((R.HS, R.WS), np.float32)
        full[Y0:Y1, X0:X1] = a
        self.alpha_ss = full


# ---------------------------------------------------------------- 渲染
def make_renderer(res=720):
    R = E.Renderer(build(), res)
    rip = FxRipples(R)
    R.fx += [rip, FxLine(R), FxBoat(R)]
    return R, rip


def beats():
    ev = []
    ev.append(dict(t=108.0, what='全貌静止开始（留白收墨转场底画）'))
    ev.append(dict(t=117.0, what='全貌静止结束（转场完）；此后仍为全貌'))
    ev.append(dict(t=G0 + LABEL['t0'], what='展签淡入'))
    ev.append(dict(t=G0 + LABEL['t1'], what='展签收完'))
    ev.append(dict(t=G0 + BOB['on'][0], what='船开始起伏（≤0.6°，±3 px）'))
    ev.append(dict(t=G0 + PUSH[0], what='镜头开始从全画推向钓丝入水点'))
    for tb in REG:
        ev.append(dict(t=round(G0 + tb, 2), what='入水点扩出一组同心涟漪（3 圈）'))
    ev.append(dict(t=G0 + FIN[0], what='涟漪开始加密、不再消散'))
    ev.append(dict(t=G0 + PUSH[1], what='推镜到位（入水点近景，此后镜头静止）'))
    ev.append(dict(t=166.0, what='涟漪已铺开大半屏（涟漪变水图转场可开始）'))
    ev.append(dict(t=170.0, what='涟漪铺满全屏'))
    ev.append(dict(t=174.0, what='段尾'))
    return dict(segment='s3 传马远《寒江独钓图》', window=[108, 174], frame0_global=108.0, fps=30, frames=int(DUR * 30),
                events=ev, ripple_center_world=list(map(float, ENTRY)), close_camera=CLOSE, full_camera=FULL)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('out'); ap.add_argument('--mask', default='')
    ap.add_argument('--res', type=int, default=720)
    ap.add_argument('--frames', default=''); ap.add_argument('--stills', default='')
    ap.add_argument('--check', action='store_true'); ap.add_argument('--crf', type=int, default=12)
    a = ap.parse_args()
    R, rip = make_renderer(a.res)
    E.log(f'{R.nframes} 帧 {R.W}x{R.H}; FULL {FULL}; CLOSE {CLOSE}')
    R.check_speed()
    json.dump(beats(), open(os.path.join(HERE, 'beats.json'), 'w'), ensure_ascii=False, indent=1)
    if a.check:
        return
    if a.stills:
        base = os.path.splitext(a.out)[0]
        for i in [int(x) for x in a.stills.split(',') if x]:
            tr = time.time()
            fr = R.render(i / R.fps)
            cv2.imwrite(f'{base}_f{i:04d}.png', cv2.cvtColor(fr, cv2.COLOR_RGB2BGR))
            if rip.alpha_ss is not None:
                m = cv2.resize(rip.alpha_ss, (R.W, R.H), interpolation=cv2.INTER_AREA)
                cv2.imwrite(f'{base}_m{i:04d}.png', np.clip(m * 255 + .5, 0, 255).astype(np.uint8))
            E.log(f'still {i} {time.time() - tr:.2f}s')
        return
    f0, f1 = (map(int, a.frames.split(':')) if a.frames else (0, R.nframes))
    enc = ['-c:v', 'libx264', '-preset', 'medium', '-crf', str(a.crf), '-pix_fmt', 'yuv420p', '-movflags', '+faststart']
    ff = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{R.W}x{R.H}',
                           '-r', f'{R.fps:g}', '-i', '-'] + enc + [a.out], stdin=subprocess.PIPE)
    fm = None
    if a.mask:
        fm = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'gray', '-s', f'{R.W}x{R.H}',
                               '-r', f'{R.fps:g}', '-i', '-'] + enc + [a.mask], stdin=subprocess.PIPE)
    tr = time.time()
    zero = np.zeros((R.H, R.W), np.uint8)
    for i in range(f0, f1):
        ff.stdin.write(R.render(i / R.fps).tobytes())
        if fm is not None:
            if rip.alpha_ss is None:
                fm.stdin.write(zero.tobytes())
            else:
                m = cv2.resize(rip.alpha_ss, (R.W, R.H), interpolation=cv2.INTER_AREA)
                fm.stdin.write(np.clip(m * 255 + .5, 0, 255).astype(np.uint8).tobytes())
        if (i - f0) % 30 == 0:
            E.log(f'frame {i}/{f1}  {(time.time() - tr) / (i - f0 + 1):.2f}s/帧')
    ff.stdin.close(); ff.wait()
    if fm is not None:
        fm.stdin.close(); fm.wait()
    E.log(f'完成 {a.out}  {(time.time() - tr) / max(1, f1 - f0):.2f}s/帧')


if __name__ == '__main__':
    try:
        main()
    except E.EngineError as e:
        print('ENGINE ERROR:', e, file=sys.stderr); sys.exit(2)
