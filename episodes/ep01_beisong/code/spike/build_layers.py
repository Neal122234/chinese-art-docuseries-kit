# Build 2.5D layers for Xishan (溪山行旅图) from P2 (painting area, ds2 of full-res).
# Memory-aware (8GB machine): big arrays processed in row chunks.
import numpy as np, cv2, time, json, os
from polys import NEAR, MID, CLIFF
t0 = time.time()
os.makedirs('layers', exist_ok=True)
P = np.load('P2.npy')                       # (9956,4975,3) RGB uint8
H, W = P.shape[:2]
MARGIN = 640                                # extension around painting (P2 px) on FAR/edge layers
FEATHER = 110                               # painting border feather (P2 px)
CH = 1024                                   # row chunk

def log(*a): print(f'[{time.time()-t0:6.1f}s]', *a, flush=True)
def smooth(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1); return t * t * (3 - 2 * t)
ker = lambda r: cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * r + 1, 2 * r + 1))

def pushpull(img, w, levels=14):
    pyr = []
    a = img * w[..., None]; b = w.copy()
    for _ in range(levels):
        pyr.append((a, b))
        if min(b.shape) < 4: break
        a = cv2.pyrDown(a); b = cv2.pyrDown(b)
    a, b = pyr[-1]
    cur = a / np.maximum(b, 1e-6)[..., None]
    for a, b in reversed(pyr[:-1]):
        up = cv2.pyrUp(cur, dstsize=(b.shape[1], b.shape[0]))
        wn = np.clip(b * 4, 0, 1)[..., None]
        cur = (a / np.maximum(b, 1e-6)[..., None]) * wn + up * (1 - wn)
    return cur

# ---------- ink density ----------
Lf = cv2.cvtColor(P, cv2.COLOR_RGB2GRAY).astype(np.float32)
L8 = cv2.resize(Lf, (W // 4, H // 4), interpolation=cv2.INTER_AREA)
paper8 = cv2.GaussianBlur(cv2.dilate(cv2.GaussianBlur(L8, (0, 0), 2), ker(15)), (0, 0), 14)
paper = cv2.resize(paper8, (W, H), interpolation=cv2.INTER_CUBIC)
INK = 38.0
Lb = cv2.GaussianBlur(Lf, (0, 0), 1.2); del Lf
k = np.clip((paper - Lb) / np.maximum(paper - INK, 20), 0, 1).astype(np.float32); del Lb, paper
log('ink density pct', np.percentile(k[::7, ::7], [10, 50, 90]))

def poly_sd(poly):
    m = np.zeros((H, W), np.uint8)
    cv2.fillPoly(m, [np.round(np.array(poly, np.float32) * 4).astype(np.int32)], 1)
    di = cv2.distanceTransform(m, cv2.DIST_L2, 5)
    di -= cv2.distanceTransform(1 - m, cv2.DIST_L2, 5)
    return di

ys1 = np.arange(H, dtype=np.float32)[:, None]; xs1 = np.arange(W, dtype=np.float32)[None, :]
dborder = np.minimum(np.minimum(xs1, W - 1 - xs1), np.minimum(ys1, H - 1 - ys1))
wb = smooth(0, FEATHER, dborder).astype(np.float32); del dborder

K0 = 0.30
def layer_alpha(poly, band_in, band_out):
    sd = poly_sd(poly)
    key = smooth(K0 - 0.07, K0 + 0.07, k)
    a = np.maximum(smooth(0, band_in, sd), key * (sd > -band_out)).astype(np.float32)
    return a
aN = layer_alpha(NEAR, 44, 14)
aM = layer_alpha(MID, 170, 14)
aM[4*1945:4*2085, 4*470:4*625] = np.maximum(aM[4*1945:4*2085, 4*470:4*625], 1.0)
aC = layer_alpha(CLIFF, 60, 12)
aC *= smooth(1725 * 4, 1590 * 4, ys1).astype(np.float32)
log('alphas')

# ---------- silk texture tile (float16) ----------
sky = P[600:2600, 300:820].astype(np.float32)
hp = sky - cv2.GaussianBlur(sky, (0, 0), 5); hp -= hp.mean((0, 1))
tile = np.concatenate([hp, hp[:, ::-1]], 1); tile = np.concatenate([tile, tile[::-1]], 0).astype(np.float16)
TH, TW = tile.shape[:2]
def silk_tex(y0, x0, h, w, seed):
    r = np.random.default_rng(seed); oy, ox = int(r.integers(0, TH)), int(r.integers(0, TW))
    iy = (np.arange(h) + y0 + oy) % TH; ix = (np.arange(w) + x0 + ox) % TW
    return tile[iy][:, ix].astype(np.float32)
log('texture std', float(hp.std()))

# ---------- paper colour field at P8 (normalized convolution, multi-scale) ----------
P8 = cv2.resize(P, (W // 4, H // 4), interpolation=cv2.INTER_AREA).astype(np.float32)
k8 = cv2.resize(k, (W // 4, H // 4), interpolation=cv2.INTER_AREA)
def nconv(img, w, sig):
    num = cv2.GaussianBlur(img * w[..., None], (0, 0), sig); den = cv2.GaussianBlur(w, (0, 0), sig)
    return num, den
w8 = (k8 < 0.12).astype(np.float32)
n1, d1 = nconv(P8, w8, 16); n2, d2 = nconv(P8, w8, 70)
c1 = n1 / np.maximum(d1, 1e-4)[..., None]; c2 = n2 / np.maximum(d2, 1e-4)[..., None]
bl = np.clip(d1 / 0.25, 0, 1)[..., None]
paperRGB8 = c1 * bl + c2 * (1 - bl)
np.save('layers/paper8.npy', paperRGB8.astype(np.float32))
log('paper field')

# ---------- EXT background at P8: calm silk, gentle tonal continuation ----------
EXTX, EXTY = 2400, 900
gsilk = np.median(paperRGB8.reshape(-1, 3), 0)
he, we = H // 4 + 2 * EXTY, W // 4 + 2 * EXTX
ext = np.zeros((he, we, 3), np.float32); wext = np.zeros((he, we), np.float32)
ext[EXTY:EXTY + H // 4, EXTX:EXTX + W // 4] = paperRGB8; wext[EXTY:EXTY + H // 4, EXTX:EXTX + W // 4] = 1
n3, d3 = nconv(ext, wext, 110); del ext
cont = n3 / np.maximum(d3, 1e-4)[..., None]
yy8 = np.arange(he, dtype=np.float32)[:, None]; xx8 = np.arange(we, dtype=np.float32)[None, :]
dx = np.maximum(0, np.maximum(EXTX - xx8, xx8 - (EXTX + W // 4)))
dy = np.maximum(0, np.maximum(EXTY - yy8, yy8 - (EXTY + H // 4)))
wg = np.exp(-np.sqrt(dx ** 2 + dy ** 2) / 260.0)[..., None]
extf = cont * wg + gsilk * (1 - wg)
inside = wext[..., None] > 0
extf = np.where(inside, np.broadcast_to(paperRGB8.mean((0, 1)), extf.shape) * 0 + extf, extf)
rng = np.random.default_rng(7)
mot = cv2.GaussianBlur(rng.standard_normal((he, we)).astype(np.float32), (0, 0), 90); mot /= mot.std() + 1e-6
extf *= (1 + 0.012 * mot)[..., None]
ext_u8 = np.clip(extf, 0, 255).astype(np.uint8); del extf, mot, wg, cont, n3, d3, wext
np.save('layers/ext8.npy', ext_u8)
EXT_ORIGIN = (-EXTX * 4, -EXTY * 4)
log('ext', ext_u8.shape)

def ext_crop_p2(x0, y0, w, h):
    ex = (x0 - EXT_ORIGIN[0]) / 4.0 - 0.375; ey = (y0 - EXT_ORIGIN[1]) / 4.0 - 0.375
    M = np.float32([[0.25, 0, ex], [0, 0.25, ey]])   # dst->src map
    return cv2.warpAffine(ext_u8, M, (w, h), flags=cv2.INTER_LINEAR | cv2.WARP_INVERSE_MAP, borderMode=cv2.BORDER_REPLICATE).astype(np.float32)

# ---------- caravan sprite (lives in MID) ----------
cx0, cy0, cx1, cy1 = 3665, 8615, 4475, 8795
kc = k[cy0:cy1, cx0:cx1]
ink = smooth(0.20, 0.34, kc)
cm = cv2.dilate((ink > 0.5).astype(np.uint8), ker(3))
n, lab, stats, _ = cv2.connectedComponentsWithStats(cm, 8)
keep = np.zeros(n, bool); keep[1:] = stats[1:, cv2.CC_STAT_AREA] > 60
cm = keep[lab].astype(np.uint8)
car_a = np.clip(cv2.GaussianBlur(ink * cm, (0, 0), 0.8) * cv2.dilate(cm, ker(1)), 0, 1)
car_mask = np.zeros((H, W), np.uint8); car_mask[cy0:cy1, cx0:cx1] = cm
log('caravan px', int(cm.sum()))

# ---------- fills (low-freq pushpull at P4 + silk texture) ----------
def lowfreq(src_ok):
    P4 = cv2.resize(P, (W // 2, H // 2), interpolation=cv2.INTER_AREA).astype(np.float32)
    w4 = (cv2.resize(src_ok.astype(np.float32), (W // 2, H // 2), interpolation=cv2.INTER_AREA) > 0.99).astype(np.float32)
    return pushpull(P4, w4)

occN = cv2.dilate((aN > 0.5).astype(np.uint8), ker(4))
reg_mid = (occN | cv2.dilate(car_mask, ker(6))).astype(bool)
f4_mid = lowfreq((~reg_mid) & (aM > 0.5) & (k < 0.45))
occM = cv2.dilate((aM > 0.5).astype(np.uint8), ker(4)).astype(bool)
occC = cv2.dilate((aC > 0.9).astype(np.uint8), ker(4)).astype(bool)
reg_far = occM | occC | occN.astype(bool)
del occM, occC, occN
f4_far = lowfreq((~reg_far) & (k < 0.22))
log('lowfreq fills')

def filled_rows(y0, y1, reg, f4, seed, gain=1.0):
    """return P rows y0:y1 with reg replaced by upsampled fill + texture (float32)."""
    base = P[y0:y1].astype(np.float32)
    # upsample only this band of f4
    fy0 = max(0, y0 // 2 - 2); fy1 = min(f4.shape[0], y1 // 2 + 3)
    band = cv2.resize(f4[fy0:fy1], (W, (fy1 - fy0) * 2), interpolation=cv2.INTER_LINEAR)
    band = band[y0 - fy0 * 2: y0 - fy0 * 2 + (y1 - y0)]
    band = band + silk_tex(y0, 0, y1 - y0, W, seed) * gain
    r = reg[y0:y1]
    base[r] = band[r]
    return base

# ---------- pack layers ----------
meta = {'P2': [H, W], 'MARGIN': MARGIN, 'ext_origin_p2': list(EXT_ORIGIN), 'ext_scale': 4}
def pack(name, y0, y1, x0, x1, colfn, alpha, far=False):
    m = MARGIN
    oy0 = y0 - (m if y0 == 0 else 0); oy1 = y1 + (m if y1 == H else 0)
    ox0 = x0 - (m if x0 == 0 else 0); ox1 = x1 + (m if x1 == W else 0)
    hh, ww = oy1 - oy0, ox1 - ox0
    out = np.zeros((hh, ww, 4), np.uint8)
    for r0 in range(oy0, oy1, CH):
        r1 = min(oy1, r0 + CH)
        a0, a1 = max(r0, y0), min(r1, y1)           # painting rows inside this chunk
        if far:
            c = ext_crop_p2(ox0, r0, ww, r1 - r0) + silk_tex(r0 + 5000, ox0 + 5000, r1 - r0, ww, 5)
            a = np.ones((r1 - r0, ww), np.float32)
        else:
            c = np.zeros((r1 - r0, ww, 3), np.float32); a = np.zeros((r1 - r0, ww), np.float32)
        if a1 > a0:
            pc = colfn(a0, a1)[:, x0:x1]
            w_ = wb[a0:a1, x0:x1]
            sl = (slice(a0 - r0, a1 - r0), slice(x0 - ox0, x1 - ox0))
            if far:
                c[sl] = pc * w_[..., None] + c[sl] * (1 - w_[..., None])
            else:
                c[sl] = pc; a[sl] = alpha[a0:a1, x0:x1] * w_
        if far:   # melt outermost 120px into EXT
            yy_ = np.arange(r0, r1, dtype=np.float32)[:, None] - oy0; xx_ = np.arange(ww, dtype=np.float32)[None, :]
            de = np.minimum(np.minimum(xx_, ww - 1 - xx_), np.minimum(yy_, hh - 1 - yy_))
            a = smooth(0, 120, de).astype(np.float32)
        out[r0 - oy0:r1 - oy0, :, :3] = np.clip(c, 0, 255).astype(np.uint8)
        out[r0 - oy0:r1 - oy0, :, 3] = np.clip(a * 255 + 0.5, 0, 255).astype(np.uint8)
    np.save(f'layers/{name}.npy', out)
    prev = cv2.resize(out, (ww // 8, hh // 8), interpolation=cv2.INTER_AREA)
    al = prev[..., 3:4].astype(np.float32) / 255
    bg = np.zeros_like(prev[..., :3]); bg[..., 0] = 255; bg[..., 2] = 255
    cv2.imwrite(f'layers/{name}_prev.jpg', cv2.cvtColor((prev[..., :3] * al + bg * (1 - al)).astype(np.uint8), cv2.COLOR_RGB2BGR))
    meta[name] = {'origin': [int(ox0), int(oy0)], 'shape': [int(hh), int(ww)]}
    log(name, out.shape, 'origin', (ox0, oy0))
    del out

pack('far', 0, H, 0, W, lambda a, b: filled_rows(a, b, reg_far, f4_far, 23), None, far=True)
ys = np.where(aC.max(1) > 0.01)[0]; xs = np.where(aC.max(0) > 0.01)[0]
pack('cliff', max(0, ys.min() - 8), ys.max() + 8, 0, min(W, xs.max() + 8), lambda a, b: P[a:b].astype(np.float32), aC)
ys = np.where(aM.max(1) > 0.01)[0]
pack('mid', max(0, ys.min() - 8), H, 0, W, lambda a, b: filled_rows(a, b, reg_mid, f4_mid, 11, 0.9), aM)
ys = np.where(aN.max(1) > 0.01)[0]
pack('near', max(0, ys.min() - 8), H, 0, W, lambda a, b: P[a:b].astype(np.float32), aN)

spr = np.zeros((cy1 - cy0, cx1 - cx0, 4), np.uint8)
spr[..., :3] = P[cy0:cy1, cx0:cx1]; spr[..., 3] = np.clip(car_a * 255, 0, 255).astype(np.uint8)
np.save('layers/caravan.npy', spr); meta['caravan'] = {'origin': [cx0, cy0], 'shape': list(spr.shape[:2])}
v = spr[..., :3].astype(np.float32); al = spr[..., 3:4] / 255.0
cv2.imwrite('layers/caravan_prev.png', cv2.cvtColor(cv2.resize((v * al + 255 * (1 - al)).astype(np.uint8), None, fx=2, fy=2, interpolation=cv2.INTER_NEAREST), cv2.COLOR_RGB2BGR))
np.save('layers/k_ink.npy', (k * 255).astype(np.uint8))
json.dump(meta, open('layers/meta.json', 'w'), indent=1)
log('done')
