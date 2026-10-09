# 渲染：畸变校正 + 单应 + 平滑位移网格（stitch_mesh），逐条带 remap，羽化混合 + 每块每通道增益
import cv2, numpy as np, json, os
D = os.path.dirname(os.path.abspath(__file__)) + '/../wanhe/'
sol = json.load(open(D + 'work/stitch_solution_h.json')); mesh = json.load(open(D + 'work/stitch_mesh.json'))
E = np.load(D + 'work/stitch_mesh_E.npy'); G = mesh['G']; grids = mesh['grids']
T = list(sol['H'].keys()); Hs = [np.array(sol['H'][t]) for t in T]; Hi = [np.linalg.inv(h) for h in Hs]
k1, k2 = sol['k1'], sol['k2']; C = np.array(sol['C']); F = sol['F']
IM = [cv2.imread(D + 'full/K2A000896N000000000%s.jpg' % t, cv2.IMREAD_COLOR) for t in T]
Wt, Ht = 3048, 2297
def Egrid(n):
    g = grids[n]; return E[g['off']:g['off'] + g['nx'] * g['ny']].reshape(g['ny'], g['nx'], 2).astype(np.float32)
EG = [Egrid(n) for n in range(len(T))]
def E_at(n, X, Y):
    g = grids[n]; u = ((X - g['x0']) / G).astype(np.float32); v = ((Y - g['y0']) / G).astype(np.float32)
    ex = cv2.remap(EG[n][..., 0], u, v, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
    ey = cv2.remap(EG[n][..., 1], u, v, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE); return ex, ey
def undist(p):
    d = (p - C) / F; r2 = (d ** 2).sum(-1, keepdims=True); return C + d * (1 + k1 * r2 + k2 * r2 * r2) * F
def fwd(n, p):
    q = undist(p) @ Hs[n][:, :2].T + Hs[n][:, 2]; m = q[:, :2] / q[:, 2:3]
    ex, ey = E_at(n, m[:, 0:1].astype(np.float32), m[:, 1:2].astype(np.float32)); return m + np.hstack([ex, ey])
def inv(n, X, Y):
    ex, ey = E_at(n, X, Y); ex, ey = E_at(n, X - ex, Y - ey); mx, my = X - ex, Y - ey
    h = Hi[n]; w = h[2, 0] * mx + h[2, 1] * my + h[2, 2]
    ux = (h[0, 0] * mx + h[0, 1] * my + h[0, 2]) / w; uy = (h[1, 0] * mx + h[1, 1] * my + h[1, 2]) / w
    px, py = ux.copy(), uy.copy()
    for _ in range(6):
        dx = (px - C[0]) / F; dy = (py - C[1]) / F; r2 = dx * dx + dy * dy; s = 1 + k1 * r2 + k2 * r2 * r2
        px = C[0] + (ux - C[0]) / s; py = C[1] + (uy - C[1]) / s
    return px.astype(np.float32), py.astype(np.float32)
cor = [fwd(n, np.array([[0, 0], [Wt, 0], [Wt, Ht], [0, Ht]], float)) for n in range(len(T))]
allc = np.vstack(cor); X0, Y0 = np.floor(allc.min(0)).astype(int); X1, Y1 = np.ceil(allc.max(0)).astype(int)
W, H = int(X1 - X0), int(Y1 - Y0); print('mosaic', W, H, 'origin', X0, Y0, flush=True)
R = 300.0
def weight(px, py):
    rx = np.clip(np.minimum(px, Wt - 1 - px) / R, 0, 1); ry = np.clip(np.minimum(py, Ht - 1 - py) / R, 0, 1)
    rx = rx * rx * (3 - 2 * rx); ry = ry * ry * (3 - 2 * ry); w = rx * ry
    w[(px < 0) | (py < 0) | (px > Wt - 1) | (py > Ht - 1)] = 0; return w
# 增益（1/8）
s = 8; ys, xs = np.mgrid[0:H:s, 0:W:s].astype(np.float32); X = xs + X0; Y = ys + Y0
low = []; val = []
for n in range(len(T)):
    px, py = inv(n, X, Y); sm = cv2.resize(IM[n], None, fx=1 / s, fy=1 / s, interpolation=cv2.INTER_AREA).astype(np.float32)
    low.append(cv2.remap(sm, px / s, py / s, cv2.INTER_LINEAR)); val.append(weight(px, py) > 0.5)
rows, rhs = [], []
for a in range(len(T)):
    for b in range(a + 1, len(T)):
        m = val[a] & val[b]
        if m.sum() < 500: continue
        r = np.zeros(len(T)); r[a] = 1; r[b] = -1; rows.append(r); rhs.append(np.log(low[b][m].mean(0)) - np.log(low[a][m].mean(0)))
rows.append(np.ones(len(T)) * 3); rhs.append(np.zeros(3))
g, *_ = np.linalg.lstsq(np.array(rows), np.array(rhs), rcond=None); gain = np.exp(g)
for t, gg in zip(T, gain): print('gain', t, np.round(gg[::-1], 4), flush=True)
del low
out_path = D + 'wanhe_mosaic_%dx%d.rgb' % (W, H)
out = np.memmap(out_path, np.uint8, 'w+', shape=(H, W, 3)); seam = []
for y0 in range(0, H, 384):
    hh = min(384, H - y0); acc = np.zeros((hh, W, 3), np.float32); ws = np.zeros((hh, W), np.float32); per = []
    for n in range(len(T)):
        c = cor[n] - [X0, Y0]
        if c[:, 1].max() < y0 - 50 or c[:, 1].min() > y0 + hh + 50: continue
        xa = max(0, int(c[:, 0].min()) - 50); xb = min(W, int(c[:, 0].max()) + 50)
        yy, xx = np.mgrid[y0:y0 + hh, xa:xb].astype(np.float32)
        px, py = inv(n, xx + X0, yy + Y0)
        img = cv2.remap(IM[n], px, py, cv2.INTER_LANCZOS4, borderMode=cv2.BORDER_CONSTANT).astype(np.float32) * gain[n][None, None, :]
        wt = weight(px, py).astype(np.float32)
        acc[:, xa:xb] += img * wt[..., None]; ws[:, xa:xb] += wt; per.append((xa, xb, img, wt))
    for i in range(len(per)):
        for j in range(i + 1, len(per)):
            a0, a1 = max(per[i][0], per[j][0]), min(per[i][1], per[j][1])
            if a1 - a0 < 50: continue
            A = per[i][2][:, a0 - per[i][0]:a1 - per[i][0]].mean(2); B = per[j][2][:, a0 - per[j][0]:a1 - per[j][0]].mean(2)
            m = (per[i][3][:, a0 - per[i][0]:a1 - per[i][0]] > 0.05) & (per[j][3][:, a0 - per[j][0]:a1 - per[j][0]] > 0.05)
            if m.sum() < 5000: continue
            ha = A - cv2.GaussianBlur(A, (0, 0), 3); hb = B - cv2.GaussianBlur(B, (0, 0), 3)
            seam.append(float(np.sqrt(((ha - hb)[m] ** 2).mean()) / (np.sqrt((0.5 * (ha + hb))[m] ** 2).mean() + 1e-6)))
    out[y0:y0 + hh] = np.clip(acc / np.maximum(ws, 1e-6)[..., None], 0, 255).astype(np.uint8)[..., ::-1]
    print('rows', y0, y0 + hh, flush=True)
out.flush()
print('seam HF diff / HF level: median %.3f  max %.3f  (n=%d)' % (np.median(seam), max(seam), len(seam)))
json.dump(dict(W=W, H=H, origin=[int(X0), int(Y0)], scale_vs_PGZ=sol['scale_vs_PGZ'], gains={t: gain[n].tolist() for n, t in enumerate(T)},
               note='文件像素 (x,y) ≈ PGZ 像素 × 2 − origin（网格位移 ≤ 约 30 px，精确对应以本文件为准）'), open(D + 'wanhe_mosaic_meta.json', 'w'), indent=1)
a = np.memmap(out_path, np.uint8, 'r', shape=(H, W, 3))
pv = cv2.resize(np.asarray(a[::2, ::2]), (W // 8, H // 8), interpolation=cv2.INTER_AREA)
cv2.imwrite(D + 'wanhe_mosaic_preview_ds8.jpg', pv[..., ::-1], [cv2.IMWRITE_JPEG_QUALITY, 90]); print('done')
