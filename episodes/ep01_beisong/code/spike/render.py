# 2.5D multiplane renderer for Xishan spike.
# usage: python3 render.py OUT.mp4 [--frames a:b] [--review 0,30,...] [--scale 1.0]
import numpy as np, cv2, json, time, subprocess, sys, os, argparse
import numexpr as ne
ap = argparse.ArgumentParser()
ap.add_argument('out'); ap.add_argument('--frames', default='0:300'); ap.add_argument('--review', default='')
ap.add_argument('--noanim', action='store_true'); ap.add_argument('--flat', action='store_true')
ap.add_argument('--cam', default='main'); ap.add_argument('--stills', default='')
args = ap.parse_args()
t_start = time.time()
def log(*a): print(f'[{time.time()-t_start:6.1f}s]', *a, flush=True)

WO, HO, SS, FPS = 1920, 1080, 2, 30
WS, HS = WO * SS, HO * SS
meta = json.load(open('layers/meta.json'))
H2, W2 = meta['P2']

# ---------------- camera ----------------
s0 = 1010.0 / H2                      # screen px per P2 px at full view
c0 = np.array([W2 / 2.0, H2 / 2.0])
ZEND = 4.0
c1 = np.array([2500.0, 7800.0])
PFIX = (c1 * ZEND - c0) / (ZEND - 1)  # fixed point of the zoom
PS = np.array([WO / 2.0, HO / 2.0]) + (PFIX - c0) * s0
T0, T1, RAMP = 1.2, 10.0, 2.2
DELTA_MAX, TRUCK_MAX = 0.25, 300.0
def sstep(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1); return t * t * (3 - 2 * t)
def u_of_t(t):
    T = T1 - T0; r = RAMP; vmax = 1.0 / (T - r); tau = np.clip(t - T0, 0, T)
    if tau < r: return vmax * tau * tau / (2 * r)
    if tau < T - r: return vmax * (r / 2 + (tau - r))
    t2 = T - tau; return 1 - vmax * t2 * t2 / (2 * r)
def cam(t):
    u = u_of_t(t); p = sstep(0.1, 1.0, u)
    if args.flat: p = 0.0
    Z = np.exp(u * np.log(ZEND)); d = DELTA_MAX * p; tx = TRUCK_MAX * p
    return Z, d, tx
def layer_xf(t, depth):
    """returns (S, off): screen = PS + S*(u-PFIX) + off   (final-res px, u in P2)"""
    Z, dl, tx = cam(t)
    Zf = Z * (1 - dl); f = s0 * Zf
    S = f * depth / (depth - dl)
    off = np.array([f * tx * (1 / (1 - dl) - 1 / (depth - dl)), 0.0])
    return S, off

# ---------------- layers ----------------
def premult(rgba):
    out = rgba.copy()
    for r0 in range(0, rgba.shape[0], 1024):
        a = rgba[r0:r0 + 1024, :, 3:4].astype(np.uint16)
        out[r0:r0 + 1024, :, :3] = ((rgba[r0:r0 + 1024, :, :3].astype(np.uint16) * a + 127) // 255).astype(np.uint8)
    return out
def mips(img, n):
    lv = [img]
    for _ in range(n - 1):
        im = lv[-1]
        if min(im.shape[:2]) < 16: break
        lv.append(cv2.resize(im, (im.shape[1] // 2, im.shape[0] // 2), interpolation=cv2.INTER_AREA))
    return lv
class Layer:
    def __init__(s, name, img, origin, depth, unit=1, nmip=5):
        s.name, s.origin, s.depth, s.unit = name, np.array(origin, float), depth, unit
        s.lv = mips(img, nmip)
LAY = {}
def load(name, depth):
    a = premult(np.load(f'layers/{name}.npy'))
    LAY[name] = Layer(name, a, meta[name]['origin'], depth); log('loaded', name, a.shape)
ext = np.load('layers/ext8.npy')
ext = np.concatenate([ext, np.full(ext.shape[:2] + (1,), 255, np.uint8)], 2)
DEPTH = {'far': 1.30, 'cliff': 1.18, 'mist_a': 1.10, 'mist_b': 1.06, 'mid': 1.0, 'near': 0.86}
LAY['ext'] = Layer('ext', ext, meta['ext_origin_p2'], DEPTH['far'], unit=4, nmip=4)
for n_ in ['far', 'cliff', 'mid', 'near']: load(n_, DEPTH[n_])
car = premult(np.load('layers/caravan.npy'))
LAY['caravan'] = Layer('caravan', car, meta['caravan']['origin'], DEPTH['mid'], nmip=5)

def warp_layer(img, unit, origin, S, off, level_scale, roi=None):
    """forward-affine a level image into SS frame; returns (roi(x0,y0,x1,y1), warped) or None."""
    A = SS * S * unit * level_scale
    ctr = origin + (unit * level_scale - 1) / 2.0
    b = SS * (PS + off + S * (ctr - PFIX)) + (SS - 1) / 2.0
    h, w = img.shape[:2]
    if roi is None:
        x0 = int(np.floor(b[0] - A)); x1 = int(np.ceil(b[0] + A * w)) + 1
        y0 = int(np.floor(b[1] - A)); y1 = int(np.ceil(b[1] + A * h)) + 1
        x0, y0 = max(0, x0), max(0, y0); x1, y1 = min(WS, x1), min(HS, y1)
    else:
        x0, y0, x1, y1 = roi
    if x1 <= x0 or y1 <= y0: return None
    M = np.float32([[A, 0, b[0] - x0], [0, A, b[1] - y0]])
    out = cv2.warpAffine(img, M, (x1 - x0, y1 - y0), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
    return (x0, y0, x1, y1), out

def render_layer(L, S, off, extra_off=(0, 0)):
    """choose mip level (trilinear blend near transitions)"""
    A0 = SS * S * L.unit
    lvl = 0 if A0 >= 1 else int(np.floor(np.log2(1.0 / A0)))
    lvl = min(lvl, len(L.lv) - 1)
    A = A0 * 2 ** lvl
    org = L.origin + np.array(extra_off)
    r = warp_layer(L.lv[lvl], L.unit, org, S, off, 2 ** lvl)
    if r is None: return None
    if A < 0.62 and lvl + 1 < len(L.lv):
        w = (0.62 - A) / 0.12
        r2 = warp_layer(L.lv[lvl + 1], L.unit, org, S, off, 2 ** (lvl + 1), roi=r[0])
        if r2 is not None:
            out = cv2.addWeighted(r[1], 1 - w, r2[1], w, 0)
            return r[0], out
    return r

def over(acc, r):
    if r is None: return
    (x0, y0, x1, y1), img = r
    roi = acc[y0:y1, x0:x1]
    c = img[..., :3]; a = img[..., 3:4]
    ne.evaluate('roi * (1 - a / 255.0) + c', out=roi, casting='unsafe')

# ---------------- animated elements ----------------
rng = np.random.default_rng(3)
def periodic_noise(h, w, sy, sx, seed):
    r = np.random.default_rng(seed).standard_normal((h, w)).astype(np.float32)
    n = cv2.GaussianBlur(np.tile(r, (3, 3)), (0, 0), sigmaX=sx, sigmaY=sy)[h:2 * h, w:2 * w]
    return (n - n.mean()) / (n.std() + 1e-6)
FLOW = periodic_noise(2048, 64, 9, 1.6, 11)       # streaky, vertical
def flow_delta(mask, t, v, amp, seed_off):
    h, w = mask.shape
    iy = (np.arange(h)[:, None] - int(v * t) + seed_off) % FLOW.shape[0]
    ix = (np.arange(w)[None, :] + seed_off) % FLOW.shape[1]
    n = FLOW[iy, ix]
    # sub-pixel smoothness: blend with next row
    fr = (v * t) % 1.0
    n2 = FLOW[(iy - 1) % FLOW.shape[0], ix]
    n = n * (1 - fr) + n2 * fr
    d = mask * amp * np.clip(0.55 * n + 0.15, -0.9, 1.6)
    return d
WF_MASK = np.load('layers/wf_mask.npy'); WF_ORG = np.array([3950.0, 3200.0])
CAS_MASK = np.load('layers/cas_mask.npy'); CAS_ORG = np.array([1950.0, 7750.0])
def add_delta(acc, delta, origin, S, off):
    """additive RGB delta (float, P2 res) warped with layer transform"""
    A0 = SS * S
    lvl = 0 if A0 >= 1 else int(np.floor(np.log2(1.0 / A0)))
    d = delta
    for _ in range(lvl): d = cv2.resize(d, (d.shape[1] // 2, d.shape[0] // 2), interpolation=cv2.INTER_AREA)
    r = warp_layer(d, 1, origin, S, off, 2 ** lvl)
    if r is None: return
    (x0, y0, x1, y1), img = r
    acc[y0:y1, x0:x1] += img[..., None] * np.float32([1.0, 0.98, 0.9])

# mist: periodic fbm alpha textures at unit 4 (P8 px), band baked in
MIST_H, MIST_W = 640, 2048
MIST_ORG = np.array([-2000.0, 6080.0 - MIST_H * 2])     # P2 origin (centre row at P2 6080)
def fbm(h, w, seed):
    out = np.zeros((h, w), np.float32)
    for i, (s, g) in enumerate([(36, 1.0), (18, 0.5), (9, 0.25)]):
        out += g * periodic_noise(h, w, s * 0.55, s * 1.6, seed + i)
    return out / out.std()
yb = (np.arange(MIST_H, dtype=np.float32) - MIST_H / 2) * 4   # P2 offset from band centre
band = np.exp(-0.5 * (yb / 330.0) ** 2)[:, None]
MA = np.clip(0.42 + 0.34 * fbm(MIST_H, MIST_W, 21), 0, 1) ** 1.5 * band * 0.42
MB = np.clip(0.35 + 0.30 * fbm(MIST_H, MIST_W, 41), 0, 1) ** 1.6 * band * 0.30
paper8 = np.load('layers/paper8.npy')
_rows = np.where(band[:, 0] > 0.004)[0]; MIST_ROW0, MIST_ROW1 = int(_rows[0]), int(_rows[-1]) + 1
MIST_COL = np.median(paper8[1450:1560, 150:1100].reshape(-1, 3), 0) * 1.10
log('mist colour', MIST_COL)
def mist_over(acc, tex, t, v, depth):
    S, off = layer_xf(t, depth)
    A = SS * S * 4
    org = MIST_ORG + np.array([v * t, 0.0])
    ctr = org + 1.5
    b = SS * (PS + off + S * (ctr - PFIX)) + (SS - 1) / 2.0
    y0 = int(max(0, np.floor(b[1] + A * MIST_ROW0))); y1 = int(min(HS, np.ceil(b[1] + A * MIST_ROW1)))
    if y1 <= y0: return
    M = np.float32([[A, 0, b[0]], [0, A, b[1] - y0]])
    a = cv2.warpAffine(tex, M, (WS, y1 - y0), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_WRAP)[..., None]
    roi = acc[y0:y1]; mc = MIST_COL.astype(np.float32)
    ne.evaluate('roi * (1 - a) + a * mc', out=roi, casting='unsafe')

# paper-only frame for ink-emergence (start view, static)
def paper_frame():
    acc = np.zeros((HS, WS, 3), np.float32)
    S, off = layer_xf(0.0, DEPTH['far'])
    over(acc, render_layer(LAY['ext'], S, off))
    p8 = np.concatenate([np.clip(paper8, 0, 255).astype(np.uint8), np.full(paper8.shape[:2] + (1,), 255, np.uint8)], 2)
    pl = Layer('paper', p8, (0.0, 0.0), DEPTH['far'], unit=4, nmip=4)
    over(acc, render_layer(pl, S, off))
    return acc
T_INK = 1.25
GRADE = np.clip(255 * (np.arange(256) / 255.0) ** 0.86 * 1.02, 0, 255).astype(np.uint8)

def far_covers(S, off):
    L = LAY['far']; o = L.origin + 130; e = L.origin + np.array(L.lv[0].shape[1::-1]) - 130
    p0 = PS + off + S * (o - PFIX); p1 = PS + off + S * (e - PFIX)
    return p0[0] <= 0 and p0[1] <= 0 and p1[0] >= WO and p1[1] >= HO
def render(t, paper_acc=None):
    acc = np.zeros((HS, WS, 3), np.float32)
    S, off = layer_xf(t, DEPTH['far'])
    if not far_covers(S, off): over(acc, render_layer(LAY['ext'], S, off))
    over(acc, render_layer(LAY['far'], S, off))
    if not args.noanim:
        add_delta(acc, flow_delta(WF_MASK, t, 230.0, 26.0, 0), WF_ORG, S, off)
    S, off = layer_xf(t, DEPTH['cliff']); over(acc, render_layer(LAY['cliff'], S, off))
    if not args.noanim:
        mist_over(acc, MA, t, 16.0, DEPTH['mist_a'])
        mist_over(acc, MB, t, 30.0, DEPTH['mist_b'])
    S, off = layer_xf(t, DEPTH['mid']); over(acc, render_layer(LAY['mid'], S, off))
    if not args.noanim:
        add_delta(acc, flow_delta(CAS_MASK, t, 110.0, 22.0, 500), CAS_ORG, S, off)
        over(acc, render_layer(LAY['caravan'], S, off, extra_off=(-4.2 * t, 0.0)))
    else:
        over(acc, render_layer(LAY['caravan'], S, off))
    S, off = layer_xf(t, DEPTH['near']); over(acc, render_layer(LAY['near'], S, off))
    if paper_acc is not None and t < T_INK:
        lum = lambda x: x[..., 0] * 0.299 + x[..., 1] * 0.587 + x[..., 2] * 0.114
        ink = np.clip((lum(paper_acc) - lum(acc)) / np.maximum(lum(paper_acc) - 38, 20), 0, 1)
        ink = cv2.GaussianBlur(ink, (0, 0), 1.0)
        q = sstep(0.0, T_INK, t)
        th = 1.0 - 1.4 * q
        rev = sstep(th, th + 0.4, ink)[..., None]
        acc = paper_acc + (acc - paper_acc) * rev
    fr = cv2.resize(acc, (WO, HO), interpolation=cv2.INTER_AREA)
    fr = np.clip(fr + 0.5, 0, 255).astype(np.uint8)
    return cv2.LUT(fr, GRADE)

if __name__ == '__main__':
    a, b = map(int, args.frames.split(':'))
    review = set(int(x) for x in args.review.split(',') if x)
    os.makedirs('review', exist_ok=True)
    pacc = paper_frame()
    if args.stills:
        for i in [int(x) for x in args.stills.split(',')]:
            tr = time.time(); fr = render(i / FPS, pacc)
            cv2.imwrite(f'review/{args.out}_f{i:03d}.png', cv2.cvtColor(fr, cv2.COLOR_RGB2BGR)); log('still', i, f'{time.time()-tr:.2f}s')
        sys.exit(0)
    ff = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{WO}x{HO}', '-r', str(FPS), '-i', '-',
                           '-c:v', 'libx264', '-preset', 'slow', '-crf', '15', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', args.out], stdin=subprocess.PIPE)
    tr = time.time()
    for i in range(a, b):
        t = i / FPS
        fr = render(t, pacc)
        ff.stdin.write(fr.tobytes())
        if i in review:
            cv2.imwrite(f'review/{os.path.splitext(os.path.basename(args.out))[0]}_f{i:03d}.png', cv2.cvtColor(fr, cv2.COLOR_RGB2BGR))
        if i % 15 == 0: log(f'frame {i}  {(time.time()-tr)/(i-a+1):.2f}s/frame')
    ff.stdin.close(); ff.wait()
    log('done', (time.time() - tr) / (b - a), 's/frame')
