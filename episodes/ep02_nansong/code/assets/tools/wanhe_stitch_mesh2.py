# 第四轮（SIFT + 稠密相位相关补点，网格 128）。第三轮：在"共享畸变 + 单应"之上，每块再加一张拼接坐标里的平滑位移网格（双线性，间距 G），
# 让所有两两匹配点落到同一位置；稀疏线性最小二乘 + 平滑正则 + IRLS 去外点。
import numpy as np, json, os
import scipy.sparse as sp
from scipy.sparse.linalg import lsqr
D = os.path.dirname(os.path.abspath(__file__)) + '/../wanhe/'
sol = json.load(open(D + 'work/stitch_solution_h.json'))
T = list(sol['H'].keys()); Hs = [np.array(sol['H'][t]) for t in T]
k1, k2 = sol['k1'], sol['k2']; C = np.array(sol['C']); F = sol['F']
def undist(p):
    d = (p - C) / F; r2 = (d ** 2).sum(1, keepdims=True); return C + d * (1 + k1 * r2 + k2 * r2 * r2) * F
def fwd(n, p):
    q = undist(p) @ Hs[n][:, :2].T + Hs[n][:, 2]; return q[:, :2] / q[:, 2:3]
G = 128.0
Wt, Ht = 3048, 2297
grids = []; off = 0
for n in range(len(T)):
    c = fwd(n, np.array([[0, 0], [Wt, 0], [Wt, Ht], [0, Ht]], float))
    x0, y0 = np.floor(c.min(0) / G) * G - G; x1, y1 = np.ceil(c.max(0) / G) * G + G
    nx, ny = int((x1 - x0) / G) + 1, int((y1 - y0) / G) + 1
    grids.append(dict(x0=x0, y0=y0, nx=nx, ny=ny, off=off)); off += nx * ny
N = off
def interp(n, m):
    g = grids[n]; u = (m[:, 0] - g['x0']) / G; v = (m[:, 1] - g['y0']) / G
    iu = np.clip(np.floor(u).astype(int), 0, g['nx'] - 2); iv = np.clip(np.floor(v).astype(int), 0, g['ny'] - 2)
    fu = u - iu; fv = v - iv
    idx = [g['off'] + iv * g['nx'] + iu, g['off'] + iv * g['nx'] + iu + 1, g['off'] + (iv + 1) * g['nx'] + iu, g['off'] + (iv + 1) * g['nx'] + iu + 1]
    w = [(1 - fu) * (1 - fv), fu * (1 - fv), (1 - fu) * fv, fu * fv]
    return idx, w
Z = np.load(D + 'work/stitch_matches.npz'); ZD = np.load(D + 'work/stitch_matches_dense.npz')
P = []
for k in list(Z.files) + ['D:' + f for f in ZD.files]:
    if k.endswith('_p'):
        src = ZD if k.startswith('D:') else Z; kk = k[2:] if k.startswith('D:') else k
        i, j = kk[:-2].split('-'); i, j = T.index(i), T.index(j)
        p = src[kk].astype(np.float64); q = src[kk[:-2] + '_q'].astype(np.float64)
        if k.startswith('D:'): p = np.repeat(p, 6, 0); q = np.repeat(q, 6, 0)   # 稠密块点代表 192² 区域，加权
        P.append((k[:-2], i, j, fwd(i, p), fwd(j, q)))
def build(wts):
    rows, cols, vals, rhs = [], [], [], []; r = 0
    for (name, i, j, mi, mj), wv in zip(P, wts):
        ii, wi = interp(i, mi); jj, wj = interp(j, mj); n = len(mi)
        for dim in range(2):
            rr = r + np.arange(n)
            for a in range(4):
                rows += [rr, rr]; cols += [2 * ii[a] + dim, 2 * jj[a] + dim]; vals += [wi[a] * wv, -wj[a] * wv]
            rhs.append((mj[:, dim] - mi[:, dim]) * wv); r += n
    # 平滑：相邻节点二阶差分
    LS, LM = 3.0, 0.02
    for n, g in enumerate(grids):
        nx, ny, o = g['nx'], g['ny'], g['off']
        for dim in range(2):
            for yy in range(ny):
                for xx in range(1, nx - 1):
                    rows += [np.array([r])] * 3; cols += [np.array([2 * (o + yy * nx + xx + d) + dim]) for d in (-1, 0, 1)]; vals += [np.array([LS]), np.array([-2 * LS]), np.array([LS])]; rhs.append(np.zeros(1)); r += 1
            for yy in range(1, ny - 1):
                for xx in range(nx):
                    rows += [np.array([r])] * 3; cols += [np.array([2 * (o + (yy + d) * nx + xx) + dim]) for d in (-1, 0, 1)]; vals += [np.array([LS]), np.array([-2 * LS]), np.array([LS])]; rhs.append(np.zeros(1)); r += 1
        idx = np.arange(o, o + nx * ny)
        for dim in range(2):
            rr = r + np.arange(len(idx)); rows.append(rr); cols.append(2 * idx + dim); vals.append(np.full(len(idx), LM)); rhs.append(np.zeros(len(idx))); r += len(idx)
    A = sp.csr_matrix((np.concatenate(vals), (np.concatenate(rows), np.concatenate(cols))), shape=(r, 2 * N))
    return A, np.concatenate(rhs)
wts = [np.ones(len(x[3])) for x in P]
for it in range(3):
    A, b = build(wts); x = lsqr(A, b, atol=1e-10, btol=1e-10, iter_lim=20000)[0]
    E = x.reshape(-1, 2); wts = []; rep = {}
    for name, i, j, mi, mj in P:
        ii, wi = interp(i, mi); jj, wj = interp(j, mj)
        ei = sum(E[ii[a]] * wi[a][:, None] for a in range(4)); ej = sum(E[jj[a]] * wj[a][:, None] for a in range(4))
        e = np.linalg.norm((mi + ei) - (mj + ej), axis=1)
        wts.append(np.where(e < 1.5, 1.0, 1.5 / np.maximum(e, 1e-6)))       # Huber
        rep[name] = [float(np.sqrt((e ** 2).mean())), float(np.percentile(e, 95)), float(np.median(e))]
    print('iter', it, ' '.join('%s rms %.2f p95 %.2f' % (k, v[0], v[1]) for k, v in rep.items()), flush=True)
print('max |E| %.1f px' % np.abs(E).max())
np.save(D + 'work/stitch_mesh_E.npy', E)
json.dump(dict(G=G, grids=grids, pair_resid=rep, base='stitch_solution_h.json'), open(D + 'work/stitch_mesh.json', 'w'), indent=1)
