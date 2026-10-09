# -*- coding: utf-8 -*-
"""S5 v2 辅助数据：石青放大底、全器法线估计、口沿唇线、底边积釉色差。输出到 work/。"""
import os, sys, numpy as np, cv2
HERE = os.path.dirname(os.path.abspath(__file__))
S = os.path.dirname(os.path.dirname(HERE))
RU = os.path.join(S, 'assets/ru')
W = os.path.join(HERE, 'work')
SP = sys.argv[1] if len(sys.argv) > 1 else W


def ss(e0, e1, x):
    x = np.clip((x - e0) / (e1 - e0), 0, 1); return x * x * (3 - 2 * x)


def qing():
    a = np.load(os.path.join(S, 'segs/qianli/data/q_full.npy'), mmap_mode='r')   # 原点 (84000,0) unit 1
    x0, y0, x1, y1 = 700, 2560, 1300, 3040
    c = np.ascontiguousarray(a[y0:y1, x0:x1]).astype(np.float32)
    up = cv2.resize(c, ((x1 - x0) * 4, (y1 - y0) * 4), interpolation=cv2.INTER_LANCZOS4)
    out = np.clip(up + 0.5, 0, 255).astype(np.uint8)
    np.save(os.path.join(W, 'qing_up.npy'), out)
    cv2.imwrite(os.path.join(SP, 'qing_prev.jpg'), cv2.cvtColor(cv2.resize(out, (1280, 853)), cv2.COLOR_RGB2BGR))
    print('qing', out.shape, 'origin', x0, y0, 'unit 0.25', 'mean', c.reshape(-1, 3).mean(0))


def normals():
    img = cv2.cvtColor(cv2.imread(os.path.join(RU, 'ru_full_front_PAE.jpg')), cv2.COLOR_BGR2RGB).astype(np.float32)
    m8 = np.load(os.path.join(W, 'pae_matte.npy'))
    H, Wd = m8.shape
    m = m8 > 127
    L = img.mean(2); sat = img.max(2) - img.min(2)
    score = (L - cv2.GaussianBlur(L, (0, 0), 5)) - 0.5 * sat
    xs = np.arange(470, 2590, 4); yf = []
    for x in xs:
        top = np.nonzero(m[:, x])[0].min(); yc = 1147 - 40 * (x - 450) / 2152
        lo = int(max(yc + (40 if abs(x - 1526) > 700 else 150), top + 20)); hi = int(yc + 380)
        yf.append(lo + int(np.argmax(score[lo:hi, x - 1:x + 2].mean(1))))
    yf = np.array(yf, float)
    c = np.polyfit(xs, yf, 6); ok = np.abs(yf - np.polyval(c, xs)) < 12
    c = np.polyfit(xs[ok], yf[ok], 6)
    yy, xx = np.mgrid[0:H, 0:Wd].astype(np.float32)
    yfront = np.polyval(c, np.clip(xx[0], 450, 2602)).astype(np.float32)[None, :]
    colany = m.any(0)
    ytop = np.where(colany, m.argmax(0), H).astype(np.float32)[None, :]
    rowany = m.any(1)
    left = np.where(rowany, m.argmax(1), 0).astype(np.float32)
    right = np.where(rowany, Wd - 1 - m[:, ::-1].argmax(1), 1).astype(np.float32)
    # 外壁：按行轮廓当作椭圆柱
    cxr = ((left + right) / 2)[:, None]; ar = np.maximum((right - left) / 2, 1)[:, None]
    u = np.clip((xx - cxr) / ar, -0.995, 0.995)
    ext = np.stack([u, 0.15 * np.sqrt(1 - u * u), np.sqrt(1 - u * u)], -1)
    # 内壁/内底：凹面
    ui = np.clip((xx - 1526) / 1076, -0.995, 0.995)
    v = (yy - ytop) / np.maximum(yfront - ytop, 1)
    vfl = 0.58 + 0.42 * ui * ui
    wfl = ss(vfl - 0.1, vfl + 0.1, v)
    wall_i = np.stack([-0.85 * ui, 0.05 + 0 * ui, np.sqrt(np.clip(1 - 0.72 * ui * ui, 0.05, 1))], -1)
    floor = np.stack([-0.25 * ui, -0.88 + 0 * ui, 0.45 + 0 * ui], -1)
    inn = wall_i * (1 - wfl[..., None]) + floor * wfl[..., None]
    wint = 1 - ss(-6, 6, yy - yfront)            # 唇线之上 = 内
    n = inn * wint[..., None] + ext * (1 - wint[..., None])
    n /= np.linalg.norm(n, axis=-1, keepdims=True)
    n = cv2.GaussianBlur(n, (0, 0), 3)
    n /= np.linalg.norm(n, axis=-1, keepdims=True)
    mf = m8.astype(np.float32) / 255
    aux = np.concatenate([n, mf[..., None], wint[..., None]], -1)
    aux = np.dstack([cv2.resize(np.ascontiguousarray(aux[..., k]), (Wd // 2, H // 2), interpolation=cv2.INTER_AREA) for k in range(aux.shape[2])]).astype(np.float16)
    np.save(os.path.join(W, 'pae_aux.npy'), aux)
    vis = ((aux[..., :3].astype(np.float32) * 0.5 + 0.5) * 255 * aux[..., 3:4].astype(np.float32)).astype(np.uint8)
    cv2.imwrite(os.path.join(SP, 'pae_normals.jpg'), cv2.resize(vis, (Wd // 4, H // 4))[..., ::-1])
    print('aux', aux.shape)


def lip():
    img = cv2.cvtColor(cv2.imread(os.path.join(RU, 'ru_rim_PBD.jpg')), cv2.COLOR_BGR2RGB).astype(np.float32)
    L = img.mean(2); sat = img.max(2) - img.min(2)
    score = (L - cv2.GaussianBlur(L, (0, 0), 6)) - 0.3 * sat
    xs = np.arange(100, 2700, 6); ys = []
    for x in xs:
        g = 1380 - 120 * ((x - 100) / 2600) ** 3 if x < 2300 else 1330 - 400 * ((x - 2300) / 600) ** 1.5
        lo, hi = int(g - 160), int(g + 120)
        ys.append(lo + int(np.argmax(score[lo:hi, x - 2:x + 3].mean(1))))
    ys = np.array(ys, float)
    c = np.polyfit(xs, ys, 5); ok = np.abs(ys - np.polyval(c, xs)) < 10
    c = np.polyfit(xs[ok], ys[ok], 5)
    np.save(os.path.join(W, 'pbd_lip.npy'), c)
    vis = cv2.imread(os.path.join(RU, 'ru_rim_PBD.jpg'))
    for x in range(100, 2700, 20):
        cv2.circle(vis, (x, int(np.polyval(c, x))), 4, (0, 0, 255), -1)
    cv2.imwrite(os.path.join(SP, 'pbd_lip.jpg'), cv2.resize(vis[900:1700, :], (1527, 400)))
    print('lip inliers', ok.mean())


def pool():
    img = cv2.cvtColor(cv2.imread(os.path.join(RU, 'ru_baseedge_PBE.jpg')), cv2.COLOR_BGR2RGB).astype(np.float32)
    H, Wd = img.shape[:2]
    up = img[1150:1400, 200:2400].reshape(-1, 3)
    cu = np.median(up, 0)
    bl = cv2.GaussianBlur(img, (0, 0), 30)
    delta = (cu[None, None, :] - bl)
    yy = np.arange(H, dtype=np.float32)[:, None]
    # 区域：器壁下半到托座底边（y≈1800 以下是足与阴影，不动）
    reg = ss(1250, 1400, yy) * (1 - ss(1770, 1800, yy)) * np.ones((1, Wd), np.float32)
    reg *= 1 - ss(2550, 2700, np.arange(Wd, dtype=np.float32))[None, :]
    aux = np.concatenate([delta, reg[..., None]], -1)
    aux = cv2.resize(aux, (Wd // 2, H // 2), interpolation=cv2.INTER_AREA).astype(np.float16)
    np.save(os.path.join(W, 'pbe_pool.npy'), aux)
    thin = np.clip(img + delta * reg[..., None], 0, 255).astype(np.uint8)
    cv2.imwrite(os.path.join(SP, 'pbe_thin.jpg'), cv2.resize(thin, (Wd // 3, H // 3))[..., ::-1])
    print('pool upper color', cu)


if __name__ == '__main__':
    what = sys.argv[2:] or ['qing', 'normals', 'lip', 'pool']
    for w in what:
        globals()[w]()
