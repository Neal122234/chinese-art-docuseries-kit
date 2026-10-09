# 千里江山 S4 素材准备：ds3 区段、全分辨率块补船洞、船精灵、水面遮罩、墙样本
import numpy as np, cv2, os
D = '~/claude-projects/china-art/series/segs/qianli/data/'
T = '~/claude-projects/china-art/trailer/'
X3 = (26000, 36000)                      # ds3 区段 = 世界 78000–108000
a = np.memmap(T + 'src/s5_northern_song/qianli_ds3_51255x2036.rgb', dtype=np.uint8, mode='r', shape=(2036, 51255, 3))
ds3 = np.ascontiguousarray(a[:, X3[0]:X3[1]])
np.save(D + 'q_ds3.npy', ds3)
full = np.array(np.load(T + 'assets_v3/qianli/work_full_x84000-86400.npy'))   # (6110,2400,3) 世界 x 84000–86400
FX = 84000

def polymask(shape, polys, rects, lines, ox, oy):
    m = np.zeros(shape, np.uint8)
    for p in polys:
        cv2.fillPoly(m, [np.int32([[x - ox, y - oy] for x, y in p])], 255)
    for x0, y0, x1, y1 in rects:
        cv2.rectangle(m, (x0 - ox, y0 - oy), (x1 - ox, y1 - oy), 255, -1)
    for x0, y0, x1, y1 in lines:
        cv2.line(m, (x0 - ox, y0 - oy), (x1 - ox, y1 - oy), 255, 5)
    return m

# 船（boats_full.jpg 坐标 + (84500, 5300) = 世界）
C = (84500, 5300)
def w(pts): return [(x + C[0], y + C[1]) for x, y in pts]
boats = {
 'boatM': dict(polys=[w([(722, 322), (992, 318), (988, 347), (960, 360), (760, 362), (728, 347)])],
               rects=[tuple(np.add([718, 286, 758, 334], [C[0], C[1], C[0], C[1]])), tuple(np.add([928, 285, 965, 337], [C[0], C[1], C[0], C[1]]))],
               lines=[tuple(np.add([636, 364, 727, 318], [C[0], C[1], C[0], C[1]])), tuple(np.add([888, 291, 992, 360], [C[0], C[1], C[0], C[1]]))],
               shift=430),
 'boatR': dict(polys=[w([(986, 132), (1328, 124), (1322, 152), (1292, 172), (1030, 178), (993, 157)])],
               rects=[tuple(np.add(r, [C[0], C[1], C[0], C[1]])) for r in [[1028, 98, 1060, 154], [1148, 116, 1180, 154], [1266, 93, 1300, 142]]],
               lines=[tuple(np.add(l, [C[0], C[1], C[0], C[1]])) for l in [[992, 92, 1042, 126], [1118, 116, 1162, 132], [1288, 116, 1400, 166]]],
               shift=-460),
}
meta = {}
for name, b in boats.items():
    ys = [p[1] for p in b['polys'][0]] + [r[1] for r in b['rects']] + [r[3] for r in b['rects']] + [l[1] for l in b['lines']] + [l[3] for l in b['lines']]
    xs = [p[0] for p in b['polys'][0]] + [r[0] for r in b['rects']] + [r[2] for r in b['rects']] + [l[0] for l in b['lines']] + [l[2] for l in b['lines']]
    x0, x1, y0, y1 = min(xs) - 14, max(xs) + 14, min(ys) - 14, max(ys) + 14
    m = polymask((y1 - y0, x1 - x0), b['polys'], b['rects'], b['lines'], x0, y0)
    m = cv2.dilate(m, np.ones((5, 5), np.uint8))
    al = cv2.GaussianBlur(m.astype(np.float32) / 255, (0, 0), 1.2)
    rgb = full[y0:y1, x0 - FX:x1 - FX].copy()
    spr = np.concatenate([rgb, (al * 255 + 0.5).astype(np.uint8)[..., None]], 2)
    np.save(D + f'{name}.npy', spr)
    # 补洞：同一行水面平移过来
    hole = cv2.GaussianBlur(cv2.dilate(m, np.ones((15, 15), np.uint8)).astype(np.float32) / 255, (0, 0), 4)[..., None]
    sx = b['shift']
    donor = full[y0:y1, x0 - FX + sx:x1 - FX + sx].astype(np.float32)
    full[y0:y1, x0 - FX:x1 - FX] = (rgb * (1 - hole) + donor * hole + 0.5).astype(np.uint8)
    meta[name] = [x0, y0, x1 - x0, y1 - y0]
np.save(D + 'q_full.npy', full)
print('boats', meta)

# 水面遮罩（ds3 与全分辨率块），按颜色 + 连通 + 平滑
def watermask(img, k):
    f = img.astype(np.float32)
    R, G, B = f[..., 0], f[..., 1], f[..., 2]
    s = cv2.blur
    w_ = ((G - R > 4) & (R < 100) & (B < G + 6) & (G < 125)).astype(np.float32)
    w_ = s(w_, (k, k))
    m = (w_ > 0.72).astype(np.uint8)
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((k, k), np.uint8))
    n, lab, st, _ = cv2.connectedComponentsWithStats(m, 8)
    keep = np.zeros(n, bool)
    for i in range(1, n):
        if st[i, cv2.CC_STAT_AREA] > (k * 12) ** 2 and st[i, cv2.CC_STAT_TOP] + st[i, cv2.CC_STAT_HEIGHT] > img.shape[0] * 0.8:
            keep[i] = True
    m = keep[lab].astype(np.uint8)
    m = cv2.erode(m, np.ones((k, k), np.uint8))
    return m

# ds3：先在 ds12 上算再放大
sm = cv2.resize(ds3, (ds3.shape[1] // 4, ds3.shape[0] // 4), interpolation=cv2.INTER_AREA)
m12 = watermask(sm, 5)
m3 = cv2.resize(m12.astype(np.float32), (ds3.shape[1], ds3.shape[0]), interpolation=cv2.INTER_LINEAR)
m3[:1300] = 0                                   # 水只在下部
m3 = cv2.GaussianBlur(m3, (0, 0), 3)
# 静止的船（帆船、罾网船等）挖掉：棕黄色船身
f3 = ds3.astype(np.float32)
boatish = ((f3[..., 0] > 105) & (f3[..., 0] > f3[..., 1] - 5)).astype(np.uint8)
boatish = cv2.dilate(boatish, np.ones((13, 13), np.uint8))
m3 = m3 * (1 - cv2.GaussianBlur(boatish.astype(np.float32), (0, 0), 3))
x_full0, x_full1 = 84000 // 3 - X3[0], 86400 // 3 - X3[0]
ramp = np.ones(ds3.shape[1], np.float32)
ramp[x_full0 + 30:x_full1 - 30] = 0
ramp = cv2.GaussianBlur(ramp[None, :], (0, 0), 10)[0]
m3c = (m3 * ramp[None, :]).astype(np.float32)
y0c = 1300
np.save(D + 'wmask_ds3.npy', m3c[y0c:])          # origin 世界 (78000, 3900) unit 3
np.save(D + 'wmask_ds3_full.npy', m3[y0c:])
# 全分辨率块：放大 ds3 遮罩（不挖中段）+ 本块船
mf = cv2.resize(m3[:, x_full0:x_full1], (2400, 6110), interpolation=cv2.INTER_LINEAR)
ff = full.astype(np.float32)
bo = ((ff[..., 0] > 105) & (ff[..., 0] > ff[..., 1] - 5)).astype(np.uint8)
bo = cv2.dilate(bo, np.ones((31, 31), np.uint8))
mf = mf * (1 - cv2.GaussianBlur(bo.astype(np.float32), (0, 0), 8))
mf[:4300] = 0
np.save(D + 'wmask_full.npy', mf[4300:].astype(np.float32))     # origin (84000, 4300) unit 1
vis = cv2.resize(ds3, (2500, 509), interpolation=cv2.INTER_AREA).astype(np.float32)
mv = cv2.resize(m3c, (2500, 509))[..., None]
cv2.imwrite(D + 'wmask_vis.jpg', cv2.cvtColor((vis * (1 - 0.5 * mv) + np.float32([255, 0, 0]) * 0.5 * mv).astype(np.uint8), cv2.COLOR_RGB2BGR))
vf = cv2.resize(full[4300:], (600, 452)).astype(np.float32); mv = cv2.resize(mf[4300:], (600, 452))[..., None]
cv2.imwrite(D + 'wmaskf_vis.jpg', cv2.cvtColor((vf * (1 - 0.5 * mv) + np.float32([255, 0, 0]) * 0.5 * mv).astype(np.uint8), cv2.COLOR_RGB2BGR))
cv2.imwrite(D + 'patched_boats.jpg', cv2.cvtColor(full[5300:5750, 500:1900], cv2.COLOR_RGB2BGR))
# 墙样本：卷首隔水的浅灰绿绢
mt = np.memmap(T + 'src/s5_northern_song/qmount_crop_151400_153700_2300x6110.rgb', dtype=np.uint8, mode='r', shape=(6110, 2300, 3))
np.save(D + 'mount_silk.npy', np.ascontiguousarray(mt[300:4600, 1480:2240]))
print('ok')
