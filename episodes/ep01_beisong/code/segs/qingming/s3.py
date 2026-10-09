# -*- coding: utf-8 -*-
"""S3 张择端《清明上河图》· 全局 1:37–2:56（帧 0 = 1:37）。
多镜头驱动：每个镜头是一个引擎段（相机时间 = 本段全局时间），镜头之间按时间窗交叉淡化（手卷"一段一段展开"）。
用法（重活走全局锁）：
  python3 s3.py --stills 0,300,...            抽帧到 stills/
  python3 s3.py --check                       各镜头速度检查
  nohup lockf -k series/.heavy.lock python3 s3.py --render > render.log 2>&1 &
  [--res 1080] [--frames a:b]
"""
import os, sys, math, time, json, argparse, subprocess
import numpy as np, cv2

SERIES = '~/claude-projects/china-art/series'
sys.path.insert(0, SERIES + '/lib')
import engine as E

HERE = os.path.dirname(os.path.abspath(__file__))
WK = HERE + '/work/'
QM = WK + 'qm.npy'                         # 38414×1800 已校色（assets/qingming/qingming_cc_38414x1800.rgb）
W, H = 38414, 1800
XS = '~/claude-projects/china-art/trailer/assets_v3/xishan/work_full.npy'
# 墙面：溪山立轴诗塘的素纸/绢（无暗花；裱边绫的云纹暗花放大后像祥云壁纸，不用）
SILK = [(XS, [2400, 700, 4700, 3450])]      # 诗塘素纸中段：避开印章、旧印痕与折痕
TONE = (0.84, 0.80, 0.71)
FPS, DUR = 30, 79.0
SSX = int(os.environ.get('S3_SS', '2'))      # 引擎镜头超采样（S3_SS=1 提速）
OUT = SERIES + '/segs/seg_s3.mp4'
OUT_MASK = SERIES + '/segs/seg_s3_water_mask.mp4'

# ---------------- 镜头时间窗（本段时间 t = 全局 − 97 s） ----------------
#            名        可见起  淡入完  淡出起  可见止
WIN = {'O': (0.0, 0.0, 8.5, 10.0),      # 1:37 卷首疏林薄雾（雾转场落点）
       'F': (8.5, 10.0, 17.9, 18.4),   # 1:45.5 全貌：长案透视（lib/scrollview.py），光走全卷 → 环移 → 俯冲降入卷首
       'A': (17.9, 18.4, 28.0, 29.5),  # 1:55 卷首（与 F 落点同一状态）→ 驴队
       'B': (28.0, 29.5, 39.0, 40.5),  # 2:05 汴河漕船
       'C': (39.0, 40.5, 61.5, 63.0),  # 2:16 虹桥 画中游
       'D': (61.5, 63.0, 69.0, 70.5),  # 2:38.5 格物：「脚店」招牌
       'E': (69.0, 70.5, DUR, DUR)}    # 2:46 汴河水面铺满（水接水）


def weight(name, t):
    a, b, c, d = WIN[name]
    if t < a or t > d:
        return 0.0
    w = 1.0
    if b > a:
        w = min(w, float(E.sstep(a, b, t)))
    if d > c and t > c:
        w = min(w, 1 - float(E.sstep(c, d, t)))
    return w


def cam(*ks):
    keys = [dict(t=k[0], cx=k[1], cy=k[2], vh=k[3], **({'ease': k[4]} if len(k) > 4 else {})) for k in ks]
    return {'rest': dict(cx=ks[0][1], cy=ks[0][2], vh=ks[0][3]), 'keys': keys}


SCROLL = {'name': 'scroll', 'src': QM, 'origin': [0, 0], 'unit': 1, 'cache_name': 'qingming_scroll'}


def close_wall():
    """近景用的绢墙（细单位），只在手卷上下/卷首外侧露出；画卷在墙上有柔影。"""
    ox, oy, sw, sh = 15000, -1600, 25000, 5000
    p = E.silk_wall('qm_close', SILK, (sw, sh), unit=3, tex_scale=1.6, tone=TONE, light=None,
                    shadow={'rect': [-ox, -oy, W - ox, H - oy], 'offset': [0, 22], 'blur': 36, 'strength': 0.30})
    return {'name': 'wall', 'src': p, 'origin': [ox, oy], 'unit': 3, 'cache_name': 'wall_qm_close'}


def flow(name, origin, unit, speed, period, d=(1, 0), streak=2.0, t0=None, t1=None):
    f = {'type': 'flow', 'layer': 'scroll', 'mask': WK + f'mask_{name}.npy', 'origin': origin, 'unit': unit,
         'dir': list(d), 'speed': speed, 'period': period, 'streak': streak, 'strength': 1.0, 'seed': ord(name[0])}
    if os.path.exists(WK + f'srcf_{name}.npy'):          # v2：非水面已用左侧水纹填满（不把人、船身拖进水里）
        f['src'] = WK + f'srcf_{name}.npy'
    elif unit > 1:
        f['src'] = WK + f'src_{name}.npy'
    if t0 is not None:
        f['t0'] = t0
    if t1 is not None:
        f['t1'] = t1
    return f


def wake(name, d, speed, period):
    """虹桥大船船头分水：船头 V 形尾迹与贴船舷的急流（遮罩 = 手画多边形 ∩ 水面，prep 生成 mask_W<name>.npy）。"""
    org = [int(v) for v in open(WK + f'mask_W{name}.origin').read().split()]
    f = flow('W' + name, org, 1, speed, period, d=d, streak=4.5, t0=38.5, t1=63.5)
    f['mask'] = WK + f'mask_W{name}.npy'; f['seed'] = 101 + len(name); f['src'] = WK + f'srcf_W{name}.npy'
    return f


def shots():
    S = {}
    base = {'fps': FPS, 'duration': DUR, 'sharpen': 0.22, 'grade': {'gamma': 1.0, 'gain': 1.0}, 'ss': SSX}
    # O 卷首疏林薄雾：满屏画面（供雾转场），先静 6 s，再极缓推近
    S['O'] = dict(base, layers=[close_wall(), SCROLL],
                  camera=cam((0, 35780, 690, 1330), (6.0, 35780, 690, 1330), (10.0, 35670, 700, 1275, 1.5)))
    # A 降入卷首（右端），从右往左、缓推到驴队
    S['A'] = dict(base, layers=[close_wall(), SCROLL],
                  camera=cam((0, 37250, 897, 2190), (18.4, 37250, 897, 2190), (27.8, 36560, 800, 1450, 1.5)))
    # B 汴河漕船：从右往左匀速，河水向右（下游）慢流
    S['B'] = dict(base, layers=[close_wall(), SCROLL],
                  fx=[flow('B', [21800, 940], 2, 70, 150, streak=4.0, t0=27.5, t1=41)],
                  camera=cam((0, 27000, 900, 2300), (29.5, 27000, 900, 2300), (39.0, 24500, 900, 2300, 1.5)))
    # C 虹桥 画中游：缓推到桥与大船铺满；桥下河水流过船头
    S['C'] = dict(base, layers=[close_wall(), SCROLL],
                  fx=[flow('C', [18950, 430], 1, 48, 110, d=(1, 0.03), streak=3.5, t0=38.5, t1=63.5),
                      wake('hull', (1, -0.22), 78, 120), wake('vlo', (1, 0.5), 62, 110)],
                  camera=cam((0, 19850, 900, 2300), (41.5, 19850, 900, 2300), (57.5, 19590, 560, 1060, 2.0)))
    # D 格物：推近到虹桥西头酒楼门前「十千 脚店」灯箱招牌
    S['D'] = dict(base, layers=[close_wall(), SCROLL],
                  camera=cam((0, 17040, 1590, 590), (63.0, 17040, 1590, 590), (69.8, 17036, 1612, 430, 1.2)))
    # E 汴河水面铺满屏，淡墨水纹缓流（水接水）
    # patchE = 同一块原图，只把 x≈24180 的一道竖向绢缝用左侧 20 px 的同行绢纹补掉（prep.py P）；水流取 patchE 自身像素
    fE = flow('E', [23700, 1180], 1, 15, 40, streak=2.2, t0=68.5); fE['layer'] = 'patchE'
    S['E'] = dict(base, layers=[close_wall(), SCROLL,
                                {'name': 'patchE', 'src': WK + 'patchE.npy', 'origin': [23700, 1180], 'unit': 1,
                                 'cache_name': 'qm_patchE'}],
                  fx=[fE],
                  camera=cam((0, 24150, 1440, 400)))
    return S


def mask_seg():
    m = (np.load(WK + 'raw_E.npy') * 255).astype(np.uint8)
    p = WK + 'maskE_rgb.npy'
    np.save(p, np.repeat(m[..., None], 3, 2))
    return {'fps': FPS, 'duration': DUR, 'ss': 1, 'sharpen': 0, 'background': [0, 0, 0],
            'layers': [{'name': 'm', 'src': p, 'origin': [23700, 1180], 'unit': 1, 'cache_name': 'qm_maskE'}],
            'camera': cam((0, 24150, 1440, 400))}


LAND = {'cx': 37250, 'cy': 897, 'vh': 2190}     # F 俯冲落点 = A 镜头起始状态
F_LABEL = {'text': ['清明上河圖', '北宋　張擇端', '絹本淡設色', '二四·八×五二八厘米', '北京故宮博物院藏'],
           'x': 0.955, 'y': 0.08, 't0': 9.9, 't1': 14.4, 'fade': 0.9, 'color': '#EDE6D8', 'title_size': 26, 'size': 22}


def arch_mask_world():
    """虹桥桥身与桥上人群（焦点转移用）：拱背折线附近 + 桥面以上。"""
    return np.array([(18860, 1060), (18960, 800), (19100, 560), (19280, 400), (19500, 320), (19740, 300), (20200, 290)], float)


class Film:
    def __init__(self, res=720, only=None):
        self.S = shots()
        self.R = {}
        for k, seg in self.S.items():
            if only and k not in only:
                continue
            self.R[k] = E.Renderer(seg, res)
        self.H = int(res); self.W = int(round(self.H * 16 / 9 / 2) * 2)
        self.n = int(round(DUR * FPS))
        self.F = None
        if not only or 'F' in only:
            import scrollview as SV
            self.SV = SV
            sv = SV.ScrollView(QM, 'qingming', SILK, tone=TONE, res=res, ss=1)
            self.F = SV.overview_shot(sv, 8.5, 12.4, 18.2, LAND, light_sweep=(9.3, 13.3, 4200, 0.30))
            self.FL = E.Renderer({'fps': FPS, 'duration': DUR, 'ss': 1, 'layers': [], 'camera': cam((0, 0, 0, 1000)),
                                  'labels': [F_LABEL]}, res)

    def check(self):
        for k, R in self.R.items():
            E.log(f'镜头 {k}:'); R.check_speed()
        if self.F is not None:
            E.log('镜头 F（长案透视）: 环移峰 %.2f px/帧 @%.1fs，俯冲峰 %.2f px/帧 @%.1fs' % (
                self.SV.speed_report(self.F, 8.5, self.F.t_glide) + self.SV.speed_report(self.F, self.F.t_glide, self.F.t_land)))

    def render_F(self, t):
        fr = self.F.frame(t).astype(np.float32)
        for lb in self.FL.labels:
            lb.draw(fr, t)
        return fr

    def dof_C(self, fr, t):
        """虹桥焦点转移：先实在大船（桥身虚），2:27 起焦点移到桥上围观人群（船虚），末段全清。"""
        on = float(E.sstep(40.0, 42.5, t)) * (1 - float(E.sstep(56.8, 59.2, t)))
        if on <= 0.003:
            return fr
        k = float(E.sstep(48.6, 51.0, t))           # 0 = 焦点在船，1 = 焦点在桥
        R = self.R['C']; sc, c = R.layer_xf(t)
        h, w = fr.shape[:2]; q = max(1, int(round(4 * h / 720)))     # 焦点图网格按 720p 的 4 px 等比（1080p = 6 px）
        ys, xs = np.mgrid[0:h // q, 0:w // q].astype(np.float32) * q + q / 2
        X = c[0] + (xs - w / 2) / sc; Y = c[1] + (ys - h / 2) / sc
        boat = ((X - 19960) / 1150) ** 2 + ((Y - 660) / 560) ** 2
        mb = 1 - E.sstep(0.8, 2.6, boat)
        P = arch_mask_world()
        d = np.full(X.shape, 1e9, np.float32)
        for (ax, ay), (bx, by) in zip(P[:-1], P[1:]):
            vx, vy = bx - ax, by - ay
            u = np.clip(((X - ax) * vx + (Y - ay) * vy) / (vx * vx + vy * vy), 0, 1)
            d = np.minimum(d, np.hypot(X - ax - u * vx, Y - ay - u * vy))
        above = (Y < 300 + 0 * X)
        side = ((X - P[0][0]) < 0) & (Y > 500)       # 左岸桥头
        mr = np.maximum(1 - E.sstep(160, 420, d), np.maximum(above.astype(np.float32), side.astype(np.float32) * 0.0))
        # 桥上人：拱背外侧（左上）一带也算桥
        outer = (Y < np.interp(X, P[:, 0], P[:, 1])) & (X < 19800)
        mr = np.maximum(mr, outer.astype(np.float32))
        sharp = mb * (1 - k) + mr * k
        blur_amt = (1 - np.clip(sharp, 0, 1)) * on
        blur_amt = cv2.resize(cv2.GaussianBlur(blur_amt, (0, 0), 1.5), (w, h), interpolation=cv2.INTER_LINEAR)[..., None]
        half = cv2.resize(fr, (w // 2, h // 2), interpolation=cv2.INTER_AREA)
        b1 = cv2.GaussianBlur(fr, (0, 0), 0.9 * h / 720)
        b2 = cv2.resize(cv2.GaussianBlur(half, (0, 0), 0.9 * h / 720), (w, h), interpolation=cv2.INTER_LINEAR)
        a1 = np.clip(blur_amt * 2, 0, 1); a2 = np.clip(blur_amt * 2 - 1, 0, 1)
        out = fr * (1 - a1) + b1 * a1
        out = out * (1 - a2) + b2 * a2
        # 焦点外略暗一点点（景深感），焦点处不动
        return out * (1 - 0.04 * blur_amt)

    def frame(self, i):
        t = i / FPS
        acc = None; ws = 0.0
        for k in list(self.R.keys()) + (['F'] if self.F is not None else []):
            w = weight(k, t)
            if w <= 0:
                continue
            if k == 'F':
                f = self.render_F(t)
            else:
                f = self.R[k].render(t).astype(np.float32)
                if k == 'C':
                    f = self.dof_C(f, t)
            f = f * w
            acc = f if acc is None else acc + f
            ws += w
        return np.clip(acc / max(ws, 1e-6) + 0.5, 0, 255).astype(np.uint8)


def ffmpeg(out, W, H, crf=12):
    return subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}',
                             '-r', str(FPS), '-i', '-', '-c:v', 'libx264', '-preset', 'medium', '-crf', str(crf),
                             '-pix_fmt', 'yuv420p', '-movflags', '+faststart', out], stdin=subprocess.PIPE)


def fix_tail(res, f0):
    """只重渲 [f0, 结尾) 并接回成片（整片按 crf 12 重编码一遍）。用于成片已在渲染中、之后才修的尾段。"""
    F = Film(res, only=['D', 'E'])
    tail = WK + 'tail.mp4'
    ff = ffmpeg(tail, F.W, F.H)
    for i in range(f0, F.n):
        ff.stdin.write(F.frame(i).tobytes())
    ff.stdin.close(); ff.wait()
    tmp = OUT + '.splice.mp4'
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', OUT, '-i', tail, '-filter_complex',
                    f'[0:v]trim=end_frame={f0},setpts=PTS-STARTPTS[a];[1:v]setpts=PTS-STARTPTS[b];[a][b]concat=n=2:v=1[o]',
                    '-map', '[o]', '-r', str(FPS), '-c:v', 'libx264', '-preset', 'medium', '-crf', '12', '-pix_fmt', 'yuv420p',
                    '-movflags', '+faststart', tmp], check=True)
    os.replace(tmp, OUT)
    E.log(f'尾段 {f0}– 已重渲并接回 {OUT}')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--res', type=int, default=720)
    ap.add_argument('--stills', default='')
    ap.add_argument('--check', action='store_true')
    ap.add_argument('--render', action='store_true')
    ap.add_argument('--mask', action='store_true')
    ap.add_argument('--frames', default='')
    ap.add_argument('--out', default=OUT)
    ap.add_argument('--mask_out', default=OUT_MASK)
    ap.add_argument('--stills_prefix', default=HERE + '/stills/s3')
    a = ap.parse_args()
    if a.mask:
        todo = WK + 'fix_tail.todo'
        if os.path.exists(todo) and os.path.exists(OUT):
            fix_tail(a.res, int(open(todo).read().strip()))
            os.remove(todo)
        R = E.Renderer(mask_seg(), a.res)
        ff = ffmpeg(a.mask_out, R.W, R.H, crf=16)
        n = int(round(DUR * FPS)); blk = np.zeros((R.H, R.W, 3), np.uint8).tobytes()
        for i in range(n):
            w = weight('E', i / FPS)
            if w <= 0:
                ff.stdin.write(blk); continue
            ff.stdin.write(np.clip(R.render(i / FPS).astype(np.float32) * w + 0.5, 0, 255).astype(np.uint8).tobytes())
        ff.stdin.close(); ff.wait(); E.log('mask 完成', a.mask_out); return
    F = Film(a.res)
    F.check()
    if a.check:
        return
    if a.stills:
        for i in [int(x) for x in a.stills.split(',') if x]:
            tr = time.time()
            fr = F.frame(i)
            cv2.imwrite(f'{a.stills_prefix}_f{i:04d}.png', cv2.cvtColor(fr, cv2.COLOR_RGB2BGR))
            E.log(f'still {i} (t={i / FPS:.2f}s, 全局 {97 + i / FPS:.1f}s) {time.time() - tr:.2f}s')
        return
    f0, f1 = (map(int, a.frames.split(':')) if a.frames else (0, F.n))
    ff = ffmpeg(a.out, F.W, F.H)
    tr = time.time()
    for i in range(f0, f1):
        ff.stdin.write(F.frame(i).tobytes())
        if (i - f0) % 30 == 0:
            E.log(f'frame {i}/{f1}  {(time.time() - tr) / (i - f0 + 1):.2f}s/帧')
    ff.stdin.close(); ff.wait()
    E.log(f'完成 {a.out}')


if __name__ == '__main__':
    try:
        main()
    except E.EngineError as e:
        print('ENGINE ERROR:', e, file=sys.stderr); sys.exit(2)
