# 万壑松风 2×4 网格瓦片（PGB–PGI，台北故宫 IIIF cid 33）联合配准：两两 SIFT 匹配 + 对整幅图 PGZ 的弱锚点，最小二乘解每块的仿射
import cv2, numpy as np, json, itertools, os
D = os.path.dirname(os.path.abspath(__file__)) + '/../wanhe/'
T = ['PGB', 'PGC', 'PGD', 'PGE', 'PGF', 'PGG', 'PGH', 'PGI']
S = 2.0                                     # 拼接坐标 = PGZ 坐标 × 2
reg = json.load(open(D + 'reg_to_PGZ.json'))
A0 = {t: S * np.array(reg[t]['M']) for t in T}   # 初值：tile → mosaic
def load(t, gray=True):
    return cv2.imread(D + 'full/K2A000896N000000000%s.jpg' % t, cv2.IMREAD_GRAYSCALE if gray else cv2.IMREAD_COLOR)
G = {t: load(t) for t in T}
sift = cv2.SIFT_create(nfeatures=40000, contrastThreshold=0.02)
def app(A, p): return p @ A[:, :2].T + A[:, 2]
def box(t):
    h, w = G[t].shape; c = app(A0[t], np.array([[0, 0], [w, 0], [w, h], [0, h]], float))
    return c.min(0), c.max(0)
pairs = []
for i, j in itertools.combinations(T, 2):
    (a0, a1), (b0, b1) = box(i), box(j)
    lo = np.maximum(a0, b0); hi = np.minimum(a1, b1)
    if (hi - lo).min() < 150: continue
    # 各自 tile 坐标里的重叠区（略放大）
    def crop(t):
        Ai = np.vstack([A0[t], [0, 0, 1]]); inv = np.linalg.inv(Ai)[:2]
        c = app(inv, np.array([[lo[0], lo[1]], [hi[0], lo[1]], [hi[0], hi[1]], [lo[0], hi[1]]]))
        h, w = G[t].shape
        x0, y0 = np.clip(c.min(0) - 60, 0, [w, h]).astype(int); x1, y1 = np.clip(c.max(0) + 60, 0, [w, h]).astype(int)
        return x0, y0, x1, y1
    ci, cj = crop(i), crop(j)
    ki, di = sift.detectAndCompute(G[i][ci[1]:ci[3], ci[0]:ci[2]], None)
    kj, dj = sift.detectAndCompute(G[j][cj[1]:cj[3], cj[0]:cj[2]], None)
    if di is None or dj is None: continue
    m = cv2.BFMatcher().knnMatch(di, dj, k=2)
    good = [a for a, b in m if a.distance < 0.8 * b.distance]
    p = np.float32([ki[a.queryIdx].pt for a in good]) + ci[:2]; q = np.float32([kj[a.trainIdx].pt for a in good]) + cj[:2]
    d = np.linalg.norm(app(A0[i], p) - app(A0[j], q), axis=1); keep = d < 40
    p, q = p[keep], q[keep]
    if len(p) < 20: print(i, j, 'few', len(p)); continue
    M, inl = cv2.estimateAffine2D(p, q, method=cv2.RANSAC, ransacReprojThreshold=2.0)
    inl = inl[:, 0].astype(bool); p, q = p[inl], q[inl]
    res = np.linalg.norm(app(M, p) - q, axis=1)
    print(i, j, 'matches', len(p), 'pair-affine rms %.2f' % np.sqrt((res ** 2).mean()))
    pairs.append((i, j, p, q))
# PGZ 锚点（弱）
ref = cv2.imread(D + 'full/K2A000896N000000000PGZ.jpg', cv2.IMREAD_GRAYSCALE)
kr, dr = sift.detectAndCompute(ref, None)
anchors = []
for t in T:
    sm = cv2.resize(G[t], None, fx=0.5, fy=0.5, interpolation=cv2.INTER_AREA)
    k, d = sift.detectAndCompute(sm, None)
    m = cv2.BFMatcher().knnMatch(d, dr, k=2); good = [a for a, b in m if a.distance < 0.75 * b.distance]
    p = np.float32([k[a.queryIdx].pt for a in good]) * 2; r = np.float32([kr[a.trainIdx].pt for a in good])
    M, inl = cv2.estimateAffine2D(p, r, method=cv2.RANSAC, ransacReprojThreshold=3.0)
    inl = inl[:, 0].astype(bool); anchors.append((t, p[inl], r[inl] * S)); print(t, 'anchors', inl.sum())
# 最小二乘：未知量每块 6 个
idx = {t: k for k, t in enumerate(T)}; n = 6 * len(T)
rows, rhs, wts = [], [], []
def eq(t, p, sign):
    r = np.zeros((2, n)); b = 6 * idx[t]
    r[0, b:b + 3] = sign * np.array([p[0], p[1], 1]); r[1, b + 3:b + 6] = sign * np.array([p[0], p[1], 1]); return r
Arows = []; B = []
for i, j, p, q in pairs:
    for a, b in zip(p, q):
        Arows.append(eq(i, a, 1) + eq(j, b, -1)); B.append([0, 0])
WA = 0.08
for t, p, r in anchors:
    for a, b in zip(p, r):
        Arows.append(WA * eq(t, a, 1)); B.append(WA * b)
Am = np.vstack(Arows); Bv = np.concatenate(B)
sol, *_ = np.linalg.lstsq(Am, Bv, rcond=None)
A = {t: sol[6 * idx[t]:6 * idx[t] + 6].reshape(2, 3) for t in T}
out = {}
for i, j, p, q in pairs:
    res = np.linalg.norm(app(A[i], p) - app(A[j], q), axis=1)
    print('resid', i, j, 'rms %.2f  p95 %.2f  max %.2f' % (np.sqrt((res ** 2).mean()), np.percentile(res, 95), res.max()))
    out['%s-%s' % (i, j)] = dict(n=len(p), rms=float(np.sqrt((res ** 2).mean())), p95=float(np.percentile(res, 95)))
for t, p, r in anchors:
    res = np.linalg.norm(app(A[t], p) - r, axis=1); print('anchor', t, 'rms %.2f (mosaic px; PGZ 本身只有 1/2 分辨率)' % np.sqrt((res ** 2).mean()))
json.dump(dict(scale_vs_PGZ=S, A={t: A[t].tolist() for t in T}, pair_resid=out), open(D + 'work/stitch_solution.json', 'w'), indent=1)
np.savez(D + 'work/stitch_matches.npz', **{'%s-%s_p' % (i, j): p for i, j, p, q in pairs}, **{'%s-%s_q' % (i, j): q for i, j, p, q in pairs})
