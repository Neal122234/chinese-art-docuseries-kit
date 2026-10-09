# -*- coding: utf-8 -*-
"""S4《千里江山图》2:47–4:02（75 s）。三个引擎子段 + 本地合成：
 A 0–10s   水面网纹铺满屏（淡墨→青绿从上缘山脚渗入），缓拉起
 B 8–18.5s 整卷横带躺在绢上（展签），末段向选段缓推
 C 16–75s  降入选段：从右往左展卷+推近（水面慢流、小舟漂移）→ 停在群峰（呼吸段）→ 推近石青到满屏
用法: python3 render.py OUT.mp4 [--res 720|1080] [--stills 0,300,...] [--frames a:b] [--mask MASK.mp4]"""
import sys, os, math, argparse, subprocess, time
import numpy as np, cv2
S = '~/claude-projects/china-art/series/'
sys.path.insert(0, S + 'lib')
import engine as E
D = S + 'segs/qianli/data/'
T = '~/claude-projects/china-art/trailer/'
W0, H0 = 153767, 6110
FPS = 30
DUR = 75.0

def prep_files():
    p16 = D + 'q_ds16.npy'
    if not os.path.exists(p16):
        a = np.memmap(T + 'assets_v3/qianli/qianli_full_ds16_9610x381.rgb', dtype=np.uint8, mode='r', shape=(381, 9610, 3))
        np.save(p16, np.ascontiguousarray(a))
    pm = D + 'wmask_ds3_fix.npy'
    if not os.path.exists(pm):
        m = np.load(D + 'wmask_ds3.npy')           # origin (78000,3900) unit 3
        def zero(x0, y0, x1, y1):
            m[max(0, (y0 - 3900) // 3):max(0, (y1 - 3900) // 3), (x0 - 78000) // 3:(x1 - 78000) // 3] = 0
        zero(90000, 3900, 108000, 4300)            # 90k 以右 4300 以上都是山
        zero(93600, 3900, 97200, 4500)             # 瀑布下的青绿山坡
        zero(100000, 3900, 102400, 5300)           # 101k 石绿坡
        m = cv2.GaussianBlur(m, (0, 0), 4)
        np.save(pm, m)
    return p16, pm

SILK = [(D + 'mount_silk.npy', [0, 0, 760, 4300])]
TONE = (0.93, 0.92, 0.88)

def wall_band():
    vw = W0 / 0.94; vh = vw * 9 / 16
    size = (vw * 1.08, vh * 1.1)
    origin = (W0 / 2 - size[0] / 2, H0 / 2 - size[1] / 2)
    ox, oy = -origin[0], -origin[1]
    sh = {'rect': [ox, oy, ox + W0, oy + H0], 'offset': [H0 * 0.03, H0 * 0.08], 'blur': H0 * 0.12, 'strength': 0.22}
    light = {'center': [ox + W0 / 2, oy + H0 / 2], 'radius': vw * 0.6, 'falloff': 0.14}
    p = E.silk_wall('qianli_band', SILK, size, unit=64, tex_scale=2.5, tone=TONE, light=light, shadow=sh)
    return {'name': 'wall', 'src': p, 'origin': list(origin), 'unit': 64, 'cache_name': 'qianli_wall_band'}, vh

def wall_local():
    origin = (70000, -5000); size = (46000, 16000)
    ox, oy = -origin[0], -origin[1]
    sh = {'rect': [ox + 60000, oy, ox + 120000, oy + H0], 'offset': [H0 * 0.02, H0 * 0.05], 'blur': H0 * 0.05, 'strength': 0.22}
    p = E.silk_wall('qianli_local', SILK, size, unit=8, tex_scale=2.5, tone=TONE, light=None, shadow=sh)
    return {'name': 'wall', 'src': p, 'origin': list(origin), 'unit': 8, 'cache_name': 'qianli_wall_local'}

def boats(t_off):
    # 全局时间 0→44 s 缓缓漂移（刚体，< 半个船身），t_off = 子段起点的全局时间
    return [
        {'type': 'drift', 'layer': 'full', 'sprite': D + 'boatM.npy', 'origin': [85122, 5571], 'unit': 1,
         'path': [[0 - t_off, 0, 0], [44 - t_off, -150, 4]], 'tilt': {'deg': 0.3, 'period': 6.5}, 'body': 384, 'cache_name': 'qianli_boatM'},
        {'type': 'drift', 'layer': 'full', 'sprite': D + 'boatR.npy', 'origin': [85472, 5378], 'unit': 1,
         'path': [[0 - t_off, 0, 0], [44 - t_off, -170, -3]], 'tilt': {'deg': 0.25, 'period': 7.3}, 'body': 442, 'cache_name': 'qianli_boatR'},
    ]

FLOW_FULL = {'type': 'flow', 'layer': 'full', 'after': 'full', 'mask': D + 'wmask_full.npy', 'origin': [84000, 4300], 'unit': 1,
             'dir': [-1, 0.12], 'speed': 11, 'period': 96, 'streak': 3, 'strength': 1.0}

def img_layers():
    return [
        {'name': 'ds3', 'src': D + 'q_ds3.npy', 'origin': [78000, 0], 'unit': 3, 'crop': [78000, 0, 108000, H0], 'feather': 0,
         'cache_name': 'qianli_ds3'},
        {'name': 'full', 'src': D + 'q_full.npy', 'origin': [84000, 0], 'unit': 1, 'crop': [84000, 0, 86400, H0], 'feather': 140,
         'cache_name': 'qianli_full'},
    ]

def seg_A():
    k0 = dict(cx=85780, cy=5620, vh=640); k1 = dict(cx=85450, cy=5000, vh=860)
    return {'fps': FPS, 'duration': 10.0, 'layers': img_layers(),
            'camera': {'rest': k0, 'keys': [dict(t=0, **k0), dict(t=0.5, **k0), dict(t=10.0, ease=1.5, **k1)]},
            'fx': [FLOW_FULL] + boats(0.0)}

def seg_A_mask():
    k0 = dict(cx=85780, cy=5620, vh=640); k1 = dict(cx=85450, cy=5000, vh=860)
    m = np.load(D + 'wmask_full.npy')
    mm = np.repeat((np.clip(m, 0, 1) * 255 + 0.5).astype(np.uint8)[..., None], 3, 2)
    return {'fps': FPS, 'duration': 10.0, 'background': [0, 0, 0], 'sharpen': 0,
            'layers': [{'name': 'm', 'src': mm, 'origin': [84000, 4300], 'unit': 1, 'cache_name': 'qianli_wmask_full_v2'}],
            'camera': {'rest': k0, 'keys': [dict(t=0, **k0), dict(t=0.5, **k0), dict(t=10.0, ease=1.5, **k1)]}}

S0 = dict(cx=97600, cy=3055, vh=8730)

def seg_B(p16):
    wl, vh = wall_band()
    full = dict(cx=W0 / 2, cy=H0 / 2, vh=vh)
    s_b, s_c = 720 / vh, 720 / S0['vh']
    fx_ = (S0['cx'] * s_c - full['cx'] * s_b) / (s_c - s_b)
    tgt = np.array([fx_, H0 / 2]); r = 0.80
    c1 = tgt + (np.array([full['cx'], full['cy']]) - tgt) * r
    k1 = dict(cx=float(c1[0]), cy=float(c1[1]), vh=vh * r)
    return {'fps': FPS, 'duration': 10.5,
            'layers': [wl, {'name': 'band', 'src': p16, 'origin': [0, 0], 'unit': W0 / 9610, 'cache_name': 'qianli_band16'}],
            'camera': {'rest': full, 'keys': [dict(t=0, **full), dict(t=7.0, **full), dict(t=12.6, ease=1.6, **k1)]},
            'labels': [{'text': ['千里江山圖', '北宋　王希孟', '絹本青綠設色', '五一·五×一一九一·五厘米', '北京故宮博物院藏'],
                        'x': 0.915, 'y': 0.545, 't0': 1.4, 't1': 7.2, 'fade': 0.9, 'color': '#2b251d',
                        'title_size': 25, 'size': 20}]}

S0 = dict(cx=97600, cy=3055, vh=8730)
S1 = dict(cx=85300, cy=3950, vh=3400)
S2 = dict(cx=85070, cy=2890, vh=560)

def seg_C(pm):
    fl_ds3 = {'type': 'flow', 'layer': 'ds3', 'after': 'full', 'mask': np.load(pm), 'origin': [78000, 3900], 'unit': 3,
              'dir': [-1, 0.12], 'speed': 11, 'period': 96, 'streak': 3, 'strength': 1.0, 't1': 34.5}
    return {'fps': FPS, 'duration': 59.0,
            'layers': [wall_local()] + img_layers(),
            'camera': {'rest': S1, 'keys': [dict(t=0, **S0), dict(t=24.0, ease=2.5, **S1), dict(t=25.5, **S1),
                                            dict(t=59.0, ease=2.0, **S2)]},
            'fx': [fl_ds3, dict(FLOW_FULL, t1=34.5)] + boats(16.0)}

class FlowROI(E.Flow):
    """同 engine.Flow，但只在当前可见区域（+周期余量）内计算，避免整块水面每帧全算"""
    def draw(self, acc, t):
        if not self.active(t):
            return
        R = self.R
        s, c = R.layer_xf(t, self.par, self.zpar)
        A0 = R.SS * s * self.unit
        l = 0 if A0 >= 1 else min(int(math.floor(math.log2(1 / A0))), len(self.pyr) - 1)
        tex, m = self.pyr[l]; u = self.unit * 2 ** l
        hw, hh = R.W / 2 / s, R.H / 2 / s; pad = self.period + 8 * u
        j0 = max(0, int((c[0] - hw - pad - self.origin[0]) / u)); j1 = min(m.shape[1], int((c[0] + hw + pad - self.origin[0]) / u) + 1)
        i0 = max(0, int((c[1] - hh - pad - self.origin[1]) / u)); i1 = min(m.shape[0], int((c[1] + hh + pad - self.origin[1]) / u) + 1)
        if j1 - j0 < 4 or i1 - i0 < 4:
            return
        m = m[i0:i1, j0:j1]
        if m.max() < 0.01:
            return
        tex = np.ascontiguousarray(tex[i0:i1, j0:j1]); h, w = m.shape
        ph = self.speed * t / u; P = self.period / u
        out = np.zeros_like(tex)
        for off in (0.0, 0.5):
            f = (ph / P + off) % 1.0
            wgt = 1 - abs(2 * f - 1)
            dx, dy = self.dir * f * P
            M = np.float32([[1, 0, dx], [0, 1, dy]])
            out += wgt * cv2.warpAffine(tex, M, (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
        yy, xx = np.mgrid[i0:i1, j0:j1].astype(np.float32) * u
        along = (xx * self.dir[0] + yy * self.dir[1] - self.speed * t) / 2.0
        across = (-xx * self.dir[1] + yy * self.dir[0]) / 2.0
        n = cv2.remap(self.noise, (across % 64).astype(np.float32), (along % 1024).astype(np.float32),
                      cv2.INTER_LINEAR, borderMode=cv2.BORDER_WRAP)
        out += (self.streak * np.clip(0.55 * n + 0.15, -0.9, 1.6))[..., None] * np.float32([1.0, 0.98, 0.92])
        a = np.clip(m * self.strength, 0, 1)
        rgba = np.concatenate([np.clip(out, 0, 255) * a[..., None], a[..., None] * 255], 2)
        rgba = np.clip(rgba, 0, 255).astype(np.uint8)
        R.draw_image(acc, [rgba], self.origin + np.array([j0, i0]) * u, u, s, c)

_mk = E.make_fx
def _make_fx(spec, R):
    return FlowROI(spec, R) if spec['type'] == 'flow' else _mk(spec, R)
E.make_fx = _make_fx

def sstep(e0, e1, x):
    u = np.clip((x - e0) / (e1 - e0), 0, 1); return u * u * (3 - 2 * u)

def bleed(fr, t, H):
    """A 段：开头淡墨（暖灰），青绿从上缘（山脚一侧）渐渐渗进来"""
    p = float(sstep(0.8, 8.0, t))
    if p >= 0.999:
        return fr
    f = fr.astype(np.float32)
    lum = f @ np.float32([0.3, 0.55, 0.15])
    ink = (lum[..., None] * 1.15 + 42) * np.float32([1.0, 0.94, 0.79])
    y = (np.arange(fr.shape[0], dtype=np.float32) / fr.shape[0])[:, None, None]
    k = np.clip(1.75 * p - 0.75 * y, 0, 1); k = k * k * (3 - 2 * k)
    return np.clip(ink + (f - ink) * k + 0.5, 0, 255).astype(np.uint8)

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('out'); ap.add_argument('--res', type=int, default=720)
    ap.add_argument('--stills', default=''); ap.add_argument('--frames', default=''); ap.add_argument('--mask', default='')
    ap.add_argument('--crf', type=int, default=12)
    a = ap.parse_args()
    p16, pm = prep_files()
    RA = E.Renderer(seg_A(), a.res); RB = E.Renderer(seg_B(p16), a.res); RC = E.Renderer(seg_C(pm), a.res)
    for n, R in (('A', RA), ('B', RB), ('C', RC)):
        E.log(f'子段 {n}'); R.check_speed()
    RM = E.Renderer(seg_A_mask(), a.res) if a.mask else None
    W, H = RA.W, RA.H

    def frame(i):
        t = i / FPS
        if t < 8.0:
            return bleed(RA.render(t), t, H), 1.0
        if t < 10.0:
            w = float(sstep(8.0, 10.0, t))
            fa = bleed(RA.render(t), t, H).astype(np.float32); fb = RB.render(t - 8.0).astype(np.float32)
            return np.clip(fa * (1 - w) + fb * w + 0.5, 0, 255).astype(np.uint8), 1 - w
        if t < 16.0:
            return RB.render(t - 8.0), 0.0
        if t < 18.5:
            w = float(sstep(16.0, 18.5, t))
            fb = RB.render(t - 8.0).astype(np.float32); fc = RC.render(t - 16.0).astype(np.float32)
            return np.clip(fb * (1 - w) + fc * w + 0.5, 0, 255).astype(np.uint8), 0.0
        return RC.render(t - 16.0), 0.0

    if a.stills:
        base = os.path.splitext(a.out)[0]
        for i in [int(x) for x in a.stills.split(',') if x]:
            tr = time.time(); fr, _ = frame(i)
            cv2.imwrite(f'{base}_f{i:04d}.png', cv2.cvtColor(fr, cv2.COLOR_RGB2BGR)); E.log(f'still {i} {time.time() - tr:.2f}s')
        return
    n = int(round(DUR * FPS))
    f0, f1 = (map(int, a.frames.split(':')) if a.frames else (0, n))
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

if __name__ == "__main__" and False:
    try:
        main()
    except E.EngineError as e:
        print('ENGINE ERROR:', e, file=sys.stderr); sys.exit(2)
