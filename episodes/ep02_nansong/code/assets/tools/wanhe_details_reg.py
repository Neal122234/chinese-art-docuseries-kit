# 局部高清瓦片（PGJ–PGP、PGQ–PGW、PGX、PGA/PPA）配准到拼接大图坐标：tile 像素 → mosaic 像素 的相似变换
import cv2, numpy as np, json, os
D = os.path.dirname(os.path.abspath(__file__)) + '/../wanhe/'
W, H = 4876, 6332
mo = np.memmap(D + 'wanhe_mosaic_%dx%d.rgb' % (W, H), np.uint8, 'r', shape=(H, W, 3))
g2 = cv2.cvtColor(cv2.resize(np.asarray(mo[::2, ::2]), (W // 2, H // 2), interpolation=cv2.INTER_AREA), cv2.COLOR_RGB2GRAY)
sift = cv2.SIFT_create(nfeatures=30000, contrastThreshold=0.02)
k2, d2 = sift.detectAndCompute(g2, None)
labs = ['PGJ', 'PGK', 'PGL', 'PGM', 'PGN', 'PGO', 'PGP', 'PGQ', 'PGR', 'PGS', 'PGT', 'PGU', 'PGV', 'PGW', 'PGX']
out = {}
for L in labs:
    t = cv2.imread(D + 'full/K2A000896N000000000%s.jpg' % L, cv2.IMREAD_GRAYSCALE)
    s1 = 0.15; ts = cv2.resize(t, None, fx=s1, fy=s1, interpolation=cv2.INTER_AREA)
    k, d = sift.detectAndCompute(ts, None)
    m = cv2.BFMatcher().knnMatch(d, d2, k=2); good = [a for a, b in m if a.distance < 0.8 * b.distance]
    if len(good) < 8: print(L, 'stage1 few', len(good)); continue
    p = np.float32([k[a.queryIdx].pt for a in good]) / s1; q = np.float32([k2[a.trainIdx].pt for a in good]) * 2
    M, inl = cv2.estimateAffinePartial2D(p, q, method=cv2.RANSAC, ransacReprojThreshold=12)
    if M is None or inl.sum() < 8: print(L, 'stage1 fail'); continue
    # stage 2：全分辨率大图局部 vs 瓦片缩到大图尺度
    sc = np.hypot(M[0, 0], M[1, 0]); h, w = t.shape
    c = np.array([[0, 0], [w, 0], [w, h], [0, h]], float) @ M[:, :2].T + M[:, 2]
    x0, y0 = np.clip(c.min(0) - 80, 0, [W, H]).astype(int); x1, y1 = np.clip(c.max(0) + 80, 0, [W, H]).astype(int)
    crop = cv2.cvtColor(np.asarray(mo[y0:y1, x0:x1]), cv2.COLOR_RGB2GRAY)
    tt = cv2.resize(t, None, fx=sc, fy=sc, interpolation=cv2.INTER_AREA)
    ka, da = sift.detectAndCompute(tt, None); kb, db = sift.detectAndCompute(crop, None)
    m = cv2.BFMatcher().knnMatch(da, db, k=2); good = [a for a, b in m if a.distance < 0.8 * b.distance]
    p = np.float32([ka[a.queryIdx].pt for a in good]) / sc; q = np.float32([kb[a.trainIdx].pt for a in good]) + [x0, y0]
    M2, inl2 = cv2.estimateAffinePartial2D(p, q, method=cv2.RANSAC, ransacReprojThreshold=2.5)
    if M2 is None or inl2.sum() < 10: M2, inl2 = M, inl
    e = np.linalg.norm(p[inl2[:, 0] > 0] @ M2[:, :2].T + M2[:, 2] - q[inl2[:, 0] > 0], axis=1)
    sc2 = np.hypot(M2[0, 0], M2[1, 0]); c = np.array([[0, 0], [w, 0], [w, h], [0, h]], float) @ M2[:, :2].T + M2[:, 2]
    out[L] = dict(M_tile_to_mosaic=M2.tolist(), tile_px_per_mosaic_px=round(1 / sc2, 3), inliers=int(inl2.sum()), rms=round(float(np.sqrt((e ** 2).mean())), 2),
                  mosaic_box=[int(c[:, 0].min()), int(c[:, 1].min()), int(c[:, 0].max() - c[:, 0].min()), int(c[:, 1].max() - c[:, 1].min())], tile_size=[w, h])
    print(L, out[L]['mosaic_box'], 'x%.2f' % (1 / sc2), 'inl', int(inl2.sum()), 'rms', out[L]['rms'], flush=True)
json.dump(out, open(D + 'wanhe_detail_tiles.json', 'w'), indent=1)
