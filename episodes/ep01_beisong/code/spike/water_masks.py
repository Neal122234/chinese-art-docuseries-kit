import numpy as np, cv2
P = np.load('P2.npy', mmap_mode='r')
def tophat_mask(x0, y0, x1, y1, klen, thr0, thr1, name):
    c = np.ascontiguousarray(P[y0:y1, x0:x1])
    L = cv2.cvtColor(c, cv2.COLOR_RGB2GRAY).astype(np.float32)
    L = cv2.GaussianBlur(L, (0, 0), 1.0)
    op = cv2.morphologyEx(L, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_RECT, (klen, 1)))
    th = L - op
    m = np.clip((th - thr0) / (thr1 - thr0), 0, 1)
    # keep elongated vertical components only
    b = (m > 0.3).astype(np.uint8)
    n, lab, st, _ = cv2.connectedComponentsWithStats(b, 8)
    keep = np.zeros(n, bool)
    for i in range(1, n):
        w, h = st[i, cv2.CC_STAT_WIDTH], st[i, cv2.CC_STAT_HEIGHT]
        keep[i] = h >= 40 and h >= 2.5 * w
    kb = cv2.dilate(keep[lab].astype(np.uint8), np.ones((5, 5), np.uint8))
    m = m * kb
    np.save(f'layers/{name}_mask.npy', m.astype(np.float32))
    vis = c.copy(); vis[..., 0] = np.clip(vis[..., 0] + m * 160, 0, 255)
    print(name, m.shape, 'mask px', int((m > 0.3).sum()))
    return vis
v = tophat_mask(3950, 3200, 4450, 6200, 25, 6, 18, 'wf')
cols = [cv2.resize(v[i * 1000:(i + 1) * 1000], (250, 500), interpolation=cv2.INTER_AREA) for i in range(3)]
cv2.imwrite('wf_mask_vis.jpg', cv2.cvtColor(np.hstack(cols), cv2.COLOR_RGB2BGR))
v2 = tophat_mask(1950, 7750, 2450, 8330, 21, 5, 16, 'cas')
cv2.imwrite('cas_mask_vis.jpg', cv2.cvtColor(v2, cv2.COLOR_RGB2BGR))
