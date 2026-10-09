# -*- coding: utf-8 -*-
"""S5 梁楷《泼墨仙人》· 全局 214–253（帧 0 = 214 s），39 s，1280×720 30 fps。
世界坐标 = 台北故宫 PAB 原图像素（画页 [524,674,1158,2037]）。多镜头（各自相机、各自速度检查），镜头间柔和溶解（同北宋集汝窑段做法）。
  214–221  A 衣袍泼墨近景铺满屏（供"浪涌成泼墨"转场），219 起极缓拉开
  222–224  A→B 焦点穿过的溶解；B 继续拉开到全貌（228.4 停），展签 227.6–233.4
  232.3–234  全貌上人物的墨"退回纸里"（最淡的先退，题诗印款不动）
  234–235  B→C（空纸对空纸），C = 脸部近景
  235.3–238.3  高光一：脸部细笔一根根显出（揭原作之墨，沿每根线走）
  236.4–245  C 缓缓拉开到半身；239–243.6 高光二：衣袍湿墨从九个落墨中心沿纸纤维洇开铺满（湿前沿略深，干后回到原墨）
  244.4–245.8  C→E 焦点穿过的溶解；E = 下摆泼墨近景铺满屏，极缓推近到 253（供"墨干成开片"转场）
用法：python3 render.py OUT.mp4 [--frames a:b] [--stills 0,300] [--check]（重活走 lockf 锁）"""
import os, sys, math, time, argparse, subprocess, json
import numpy as np, cv2
HERE = os.path.dirname(os.path.abspath(__file__))
EP = os.path.dirname(os.path.dirname(HERE))
S = os.path.dirname(EP)
sys.path.insert(0, os.path.join(S, 'lib'))
import engine as E

WK = os.path.join(HERE, 'work')
PAB = os.path.join(EP, 'assets/pomo/npm_pomo_PAB.jpg')
LX, LY, LW, LH = 524, 674, 1158, 2037
G0, DUR, FPS = 214.0, 39.0, 30
W, H, SS = 1280, 720, 2
WS, HS = W * SS, H * SS

FULL = dict(cx=1352, cy=1692, vh=2240)
LABEL = {'text': ['潑墨仙人', '南宋　梁楷', '紙本水墨', '四八·七×二七·七厘米', '臺北故宮博物院藏'],
         'x': 0.80, 'y': 0.16, 'color': '#2b251d', 'title_size': 26, 'size': 22,
         't0': 227.6 - G0, 't1': 233.4 - G0, 'fade': 0.9}


def K(t, cx, cy, vh, ease=None):
    k = dict(t=t, cx=cx, cy=cy, vh=vh)
    if ease is not None:
        k['ease'] = ease
    return k


# 镜头：名字、权重窗口 [入起, 入止, 出起, 出止]（本段秒）、相机、溶解时是否虚焦
SHOTS = [
    ('A_robe', [None, None, 8.2, 9.8], [K(0, 1103, 1700, 600), K(5.0, 1103, 1700, 600), K(10.2, 1103, 1700, 740, ease=1.3)], 4.0),
    ('B_full', [8.2, 9.8, 19.9, 21.0], [K(0, 1180, 1760, 1720), K(8.0, 1180, 1760, 1720),
                                       K(14.4, FULL['cx'], FULL['cy'], FULL['vh'], ease=1.4)], 4.0),
    ('C_face', [19.9, 21.0, 30.4, 31.8], [K(0, 1190, 1215, 680), K(22.4, 1190, 1215, 680), K(31.0, 1110, 1820, 1000, ease=1.5)], 0.0),
    ('E_robe', [30.4, 31.8, None, None], [K(0, 1103, 2200, 640), K(30.2, 1103, 2200, 640), K(39.0, 1103, 2200, 580, ease=2.0)], 4.0),
]


def weight(win, t):
    a0, a1, b0, b1 = win
    w = 1.0
    if a0 is not None:
        w *= float(E.sstep(a0, a1, t))
    if b0 is not None:
        w *= 1.0 - float(E.sstep(b0, b1, t))
    return w


def sst(a, b, x):
    x = np.clip((x - a) / (b - a), 0, 1)
    return x * x * (3 - 2 * x)


class Leaf:
    """画页当前状态（原画 / 退墨 / 揭墨），画页像素坐标。"""
    def __init__(self):
        self.orig = np.load(os.path.join(WK, 'leaf.npy')).astype(np.float32)
        self.plate = np.load(os.path.join(WK, 'plate.npy')).astype(np.float32)
        self.diff = self.orig - self.plate
        D = np.load(os.path.join(WK, 'D.npy')).astype(np.float32)
        fig = np.load(os.path.join(WK, 'fig.npy')).astype(np.float32)
        self.wf = fig * sst(0.03, 0.10, cv2.GaussianBlur(D, (0, 0), 2))       # 参与退/揭的权重（人物区内有墨处）
        self.ink = np.clip(D / 0.35, 0, 1) * self.wf
        tl = np.load(os.path.join(WK, 'Tline.npy'))
        tb = np.load(os.path.join(WK, 'Tbloom.npy'))
        self.isline = np.isfinite(tl)
        self.T = np.where(self.isline, tl, tb).astype(np.float32)
        self.w = np.where(self.isline, 0.06, 0.42).astype(np.float32)
        self.Trec = np.load(os.path.join(WK, 'Trec.npy'))
        self.cache = {}

    def at(self, tg):
        """tg = 全局秒 → float32 RGB（画页像素）"""
        if tg < 232.1 or tg > 245.5:
            return self.orig
        if tg < 234.6:
            R = 1 - sst(self.Trec - 0.3, self.Trec + 0.3, tg)
            Re = 1 - self.wf * (1 - R)
            return self.plate + self.diff * Re[..., None]
        T, w = self.T, self.w
        R = sst(T - w, T + w, tg)
        Re = 1 - self.wf * (1 - R)
        out = self.plate + self.diff * Re[..., None]
        # 湿前沿：墨到之处边缘略深（积墨的水痕），刚落下的墨是湿的、略深，约 1.6 s 干回原色
        front = 4 * R * (1 - R) * self.ink
        wet = sst(T, T + 0.25, tg) * (1 - sst(T + 0.4, T + 2.0, tg)) * self.ink
        dark = np.where(self.isline, 0.12 * front + 0.12 * wet, 0.13 * front + 0.07 * wet)
        return out * (1 - dark)[..., None]


class Stage:
    def __init__(self):
        mx, my = 1100, 100
        size = (4800, 3400)
        self.origin = (-mx, -my); self.unit = 4
        sh = {'rect': [LX + mx, LY + my, LX + LW + mx, LY + LH + my], 'offset': [10, 8], 'blur': 14, 'strength': 0.20}
        light = {'center': [LX + LW / 2 + mx, LY + LH * 0.42 + my], 'radius': 2600, 'falloff': 0.14}
        p = E.silk_wall('pomo_mount', [(PAB, [420, 110, 2000, 640])], size, unit=self.unit, tex_scale=1.4,
                        tone=(0.93, 0.915, 0.89), light=light, shadow=sh)
        self.wall = np.load(p).astype(np.float32)
        yy, xx = np.mgrid[0:LH, 0:LW].astype(np.float32)
        d = np.minimum(np.minimum(xx + 0.5, LW - 0.5 - xx), np.minimum(yy + 0.5, LH - 0.5 - yy))
        self.alpha = np.clip(d / 1.5, 0, 1)[..., None]

    def draw(self, cam_state, leafimg):
        c, vh = cam_state
        s = H / vh
        A = SS * s
        acc = np.empty((HS, WS, 3), np.float32)
        # 墙
        u = self.unit
        M = np.float32([[A * u, 0, SS * W / 2 + A * (self.origin[0] + 0.5 * u - c[0]) - 0.5],
                        [0, A * u, SS * H / 2 + A * (self.origin[1] + 0.5 * u - c[1]) - 0.5]])
        cv2.warpAffine(self.wall, M, (WS, HS), dst=acc, flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
        # 画页（缩小时先降采样，避免锯齿）
        img = np.concatenate([leafimg * self.alpha, self.alpha], 2)
        lu = 1.0
        while A * lu < 0.7:
            img = cv2.resize(img, (max(1, img.shape[1] // 2), max(1, img.shape[0] // 2)), interpolation=cv2.INTER_AREA)
            lu *= 2
        sx = LW / img.shape[1]; sy = LH / img.shape[0]
        M = np.float32([[A * sx, 0, SS * W / 2 + A * (LX + 0.5 * sx - c[0]) - 0.5],
                        [0, A * sy, SS * H / 2 + A * (LY + 0.5 * sy - c[1]) - 0.5]])
        # 只 warp 可见范围
        x0 = max(0, int(SS * W / 2 + A * (LX - c[0])) - 2); x1 = min(WS, int(SS * W / 2 + A * (LX + LW - c[0])) + 3)
        y0 = max(0, int(SS * H / 2 + A * (LY - c[1])) - 2); y1 = min(HS, int(SS * H / 2 + A * (LY + LH - c[1])) + 3)
        if x1 > x0 and y1 > y0:
            M2 = M.copy(); M2[0, 2] -= x0; M2[1, 2] -= y0
            li = cv2.warpAffine(img, M2, (x1 - x0, y1 - y0), flags=cv2.INTER_LINEAR if A * lu < 1.05 else cv2.INTER_CUBIC,
                                borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0, 0))
            roi = acc[y0:y1, x0:x1]
            roi *= (1 - li[..., 3:4]); roi += li[..., :3]
        return acc


class Seg:
    def __init__(self):
        self.leaf = Leaf(); self.stage = Stage()
        self.cams = [E.Camera({'rest': ks[0], 'keys': ks}, FPS) for _, _, ks, _ in SHOTS]
        self.label = E.Label(LABEL, self)   # Label 只用到 SS/H/W/WS/HS/world_to_screen
        self.nframes = int(round(DUR * FPS))

    # Label 需要的属性
    SS, H, W, WS, HS = SS, H, W, WS, HS

    def check(self):
        pan_max = zoom_max = 0.0
        bad = []
        for (name, win, ks, _), cam in zip(SHOTS, self.cams):
            prev = None
            for i in range(self.nframes + 1):
                t = i / FPS
                c, vh = cam.state(t); s = H / vh
                if prev is not None and weight(win, t) > 0.001:
                    c0, s0 = prev
                    pan = float(np.hypot(*(s * (c0 - c)))) * 720.0 / H
                    zoom = abs(math.log(s / s0)) * FPS * 100
                    pan_max = max(pan_max, pan); zoom_max = max(zoom_max, zoom)
                    if pan > E.LIMIT_PAN_720 + 1e-6 or zoom > E.LIMIT_ZOOM + 1e-6:
                        bad.append((name, round(t, 2), round(pan, 2), round(zoom, 2)))
                prev = (c, s)
        E.log(f'速度检查: 平移峰值 {pan_max:.2f} px/帧（限 {E.LIMIT_PAN_720}），推拉峰值 {zoom_max:.2f} %/s（限 {E.LIMIT_ZOOM}）')
        if bad:
            raise E.EngineError(f'超速 {bad[:5]} …共 {len(bad)} 帧')

    def render(self, t):
        tg = G0 + t
        leafimg = self.leaf.at(tg)
        out = np.zeros((H, W, 3), np.float32); tot = 0.0
        for (name, win, ks, blur), cam in zip(SHOTS, self.cams):
            w = weight(win, t)
            if w <= 1e-3:
                continue
            acc = self.stage.draw(cam.state(t), leafimg)
            if name == 'B_full':
                self._cam = cam
                self.label.draw(acc, t)
            fr = cv2.resize(acc, (W, H), interpolation=cv2.INTER_AREA)
            if blur > 0 and w < 0.999:
                sg = blur * (1 - w)
                if sg > 0.3:
                    fr = cv2.GaussianBlur(fr, (0, 0), sg)
            out += w * fr; tot += w
        out /= max(tot, 1e-6)
        bl = cv2.GaussianBlur(out, (0, 0), 0.9)
        out = out + 0.25 * (out - bl)
        return np.clip(out + 0.5, 0, 255).astype(np.uint8)

    def world_to_screen(self, t, p, par=1.0, zpar=0.0):
        c, vh = self._cam.state(t)
        return np.array([W / 2, H / 2]) + H / vh * (np.asarray(p, float) - c)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('out'); ap.add_argument('--frames', default=''); ap.add_argument('--stills', default='')
    ap.add_argument('--check', action='store_true'); ap.add_argument('--crf', type=int, default=12)
    a = ap.parse_args()
    sg = Seg(); sg.check()
    if a.check:
        return
    if a.stills:
        base = os.path.splitext(a.out)[0]
        for i in [int(x) for x in a.stills.split(',') if x]:
            fr = sg.render(i / FPS)
            cv2.imwrite(f'{base}_f{i:04d}.png', cv2.cvtColor(fr, cv2.COLOR_RGB2BGR))
        return
    f0, f1 = (map(int, a.frames.split(':')) if a.frames else (0, sg.nframes))
    ff = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}',
                           '-r', str(FPS), '-i', '-', '-c:v', 'libx264', '-preset', 'medium', '-crf', str(a.crf),
                           '-pix_fmt', 'yuv420p', '-movflags', '+faststart', a.out], stdin=subprocess.PIPE)
    tr = time.time()
    for i in range(f0, f1):
        ff.stdin.write(sg.render(i / FPS).tobytes())
        if (i - f0) % 30 == 0:
            E.log(f'frame {i}/{f1}  {(time.time() - tr) / (i - f0 + 1):.2f}s/帧')
    ff.stdin.close(); ff.wait()
    E.log(f'完成 {a.out}')


if __name__ == '__main__':
    try:
        main()
    except E.EngineError as e:
        print('ENGINE ERROR:', e, file=sys.stderr); sys.exit(2)
