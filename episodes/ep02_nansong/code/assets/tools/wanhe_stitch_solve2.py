# 第二轮：同一台相机的 8 块瓦片 → 共享径向畸变 (k1,k2) + 每块单应，稀疏 SIFT 匹配做非线性最小二乘；对 PGZ 只留极弱锚点（定尺度/方向）
import cv2, numpy as np, json, os, sys
from scipy.optimize import least_squares
D = os.path.dirname(os.path.abspath(__file__)) + '/../wanhe/'
T = ['PGB', 'PGC', 'PGD', 'PGE', 'PGF', 'PGG', 'PGH', 'PGI']
sol1 = json.load(open(D + 'work/stitch_solution.json')); S = sol1['scale_vs_PGZ']
Z = np.load(D + 'work/stitch_matches.npz')
rng = np.random.default_rng(0)
pairs = []
for k in Z.files:
    if k.endswith('_p'):
        i, j = k[:-2].split('-'); p = Z[k]; q = Z[k[:-2] + '_q']
        if len(p) > 1500: sel = rng.choice(len(p), 1500, replace=False); p, q = p[sel], q[sel]
        pairs.append((T.index(i), T.index(j), p.astype(np.float64), q.astype(np.float64)))
# 锚点（缓存）
anc_f = D + 'work/stitch_anchors.npz'
if not os.path.exists(anc_f):
    sift = cv2.SIFT_create(nfeatures=40000, contrastThreshold=0.02)
    ref = cv2.imread(D + 'full/K2A000896N000000000PGZ.jpg', cv2.IMREAD_GRAYSCALE); kr, dr = sift.detectAndCompute(ref, None)
    out = {}
    for t in T:
        g = cv2.imread(D + 'full/K2A000896N000000000%s.jpg' % t, cv2.IMREAD_GRAYSCALE)
        sm = cv2.resize(g, None, fx=0.5, fy=0.5, interpolation=cv2.INTER_AREA); k, d = sift.detectAndCompute(sm, None)
        m = cv2.BFMatcher().knnMatch(d, dr, k=2); good = [a for a, b in m if a.distance < 0.75 * b.distance]
        p = np.float32([k[a.queryIdx].pt for a in good]) * 2; r = np.float32([kr[a.trainIdx].pt for a in good])
        M, inl = cv2.estimateAffine2D(p, r, method=cv2.RANSAC, ransacReprojThreshold=3.0); inl = inl[:, 0].astype(bool)
        out[t + '_p'] = p[inl]; out[t + '_r'] = r[inl] * S
    np.savez(anc_f, **out)
AZ = np.load(anc_f); anchors = []
for n, t in enumerate(T):
    p = AZ[t + '_p'].astype(np.float64); r = AZ[t + '_r'].astype(np.float64)
    if len(p) > 400: sel = rng.choice(len(p), 400, replace=False); p, r = p[sel], r[sel]
    anchors.append((n, p, r))
Wt, Ht = 3048.0, 2297.0; C = np.array([Wt / 2, Ht / 2]); F = np.hypot(Wt, Ht) / 2
def undist(p, k1, k2):
    d = (p - C) / F; r2 = (d ** 2).sum(1, keepdims=True); return C + d * (1 + k1 * r2 + k2 * r2 * r2) * F
def Hof(v): return np.append(v, 1.0).reshape(3, 3)
def app(H, p):
    q = p @ H[:, :2].T + H[:, 2]; return q[:, :2] / q[:, 2:3]
H0 = []
for t in T:
    A = np.array(sol1['A'][t]); H = np.vstack([A, [0, 0, 1]]); H0.append(H.flatten()[:8])
WA = float(sys.argv[1]) if len(sys.argv) > 1 else 0.02
use_dist = (sys.argv[2] != 'nodist') if len(sys.argv) > 2 else True
def resid(x):
    k1, k2 = (x[0], x[1]) if use_dist else (0.0, 0.0); Hs = [Hof(x[2 + 8 * n: 10 + 8 * n]) for n in range(len(T))]
    r = []
    for i, j, p, q in pairs: r.append((app(Hs[i], undist(p, k1, k2)) - app(Hs[j], undist(q, k1, k2))).ravel())
    for n, p, a in anchors: r.append(WA * (app(Hs[n], undist(p, k1, k2)) - a).ravel())
    return np.concatenate(r)
x0 = np.concatenate([[0.0, 0.0]] + H0)
xs = np.abs(x0) * 1e-3 + 1e-6; xs[:2] = 1e-3
res = least_squares(resid, x0, x_scale='jac', method='trf', loss='soft_l1', f_scale=2.0, max_nfev=200)
x = res.x; k1, k2 = (x[0], x[1]) if use_dist else (0.0, 0.0); Hs = [Hof(x[2 + 8 * n: 10 + 8 * n]) for n in range(len(T))]
print('WA', WA, 'dist', use_dist, 'k1 %.5f k2 %.5f' % (k1, k2), 'cost', res.cost)
full = np.load(D + 'work/stitch_matches.npz'); rep = {}
for k in full.files:
    if k.endswith('_p'):
        i, j = k[:-2].split('-'); p = full[k].astype(np.float64); q = full[k[:-2] + '_q'].astype(np.float64)
        e = np.linalg.norm(app(Hs[T.index(i)], undist(p, k1, k2)) - app(Hs[T.index(j)], undist(q, k1, k2)), axis=1)
        print('resid %s-%s rms %.2f p95 %.2f max %.2f' % (i, j, np.sqrt((e ** 2).mean()), np.percentile(e, 95), e.max())); rep[k[:-2]] = [float(np.sqrt((e ** 2).mean())), float(np.percentile(e, 95))]
tag = sys.argv[3] if len(sys.argv) > 3 else 'h'
json.dump(dict(scale_vs_PGZ=S, model='undistort(k1,k2 about tile centre, F=half diagonal) then homography', k1=k1, k2=k2, C=C.tolist(), F=F,
               H={t: Hs[n].tolist() for n, t in enumerate(T)}, pair_resid=rep), open(D + 'work/stitch_solution_%s.json' % tag, 'w'), indent=1)
