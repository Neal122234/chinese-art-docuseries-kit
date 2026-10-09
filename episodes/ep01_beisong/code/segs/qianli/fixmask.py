# 重做水面遮罩：去掉逐像素"船色"判定造成的斑点，船只按连通块剔除；全分辨率块按区域 + 静止罾网船矩形
import numpy as np, cv2
D = '~/claude-projects/china-art/series/segs/qianli/data/'
ds3 = np.load(D + 'q_ds3.npy', mmap_mode='r')          # 世界 x 78000–108000, unit 3
H, W = ds3.shape[:2]
sm = cv2.resize(np.ascontiguousarray(ds3), (W // 4, H // 4), interpolation=cv2.INTER_AREA).astype(np.float32)
R, G, B = sm[..., 0], sm[..., 1], sm[..., 2]
w_ = ((G - R > 4) & (R < 100) & (B < G + 6) & (G < 125)).astype(np.float32)
w_ = cv2.blur(w_, (5, 5)); m = (w_ > 0.6).astype(np.uint8)
m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
n, lab, st, _ = cv2.connectedComponentsWithStats(m, 8)
keep = np.zeros(n, bool)
for i in range(1, n):
    if st[i, cv2.CC_STAT_AREA] > 3600 and st[i, cv2.CC_STAT_TOP] + st[i, cv2.CC_STAT_HEIGHT] > H // 4 * 0.8:
        keep[i] = True
m = keep[lab].astype(np.uint8)
# 填水中小洞（船、绢斑）：面积 < 400 的洞补上
inv = (1 - m).astype(np.uint8); n2, lab2, st2, _ = cv2.connectedComponentsWithStats(inv, 4)
small = np.zeros(n2, bool)
for i in range(1, n2):
    if st2[i, cv2.CC_STAT_AREA] < 400: small[i] = True
m[small[lab2]] = 1
m = cv2.erode(m, np.ones((3, 3), np.uint8))
m3 = cv2.resize(m.astype(np.float32), (W, H), interpolation=cv2.INTER_LINEAR)
m3 = cv2.GaussianBlur(m3, (0, 0), 5); m3 = np.clip((m3 - 0.25) / 0.5, 0, 1)
m3[:1300] = 0
# 静止的船（棕黄船身连通块，面积够大才算，绢斑不算）→ 挖掉
f3 = np.ascontiguousarray(ds3).astype(np.float32)
tan = ((f3[..., 0] > 100) & (f3[..., 0] > f3[..., 1] - 5)).astype(np.uint8)
tan = cv2.morphologyEx(tan, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
n3, lab3, st3, _ = cv2.connectedComponentsWithStats(tan, 8)
big = np.zeros(n3, bool)
for i in range(1, n3):
    if st3[i, cv2.CC_STAT_AREA] > 60: big[i] = True
boat = cv2.dilate(big[lab3].astype(np.uint8), np.ones((15, 15), np.uint8)).astype(np.float32)
m3 = m3 * (1 - cv2.GaussianBlur(boat, (0, 0), 3))
def zero(x0, y0, x1, y1):
    m3[y0 // 3:y1 // 3, (x0 - 78000) // 3:(x1 - 78000) // 3] = 0
zero(90000, 0, 108000, 4300); zero(93600, 0, 97200, 4500); zero(100000, 0, 102400, 5300)
m3 = cv2.GaussianBlur(m3, (0, 0), 2)
xf0, xf1 = 84000 // 3 - 26000, 86400 // 3 - 26000
ramp = np.ones(W, np.float32); ramp[xf0 + 30:xf1 - 30] = 0; ramp = cv2.GaussianBlur(ramp[None, :], (0, 0), 10)[0]
np.save(D + 'wmask_ds3_fix.npy', (m3 * ramp[None, :])[1300:].astype(np.float32))    # origin (78000,3900) unit 3
# 全分辨率块 x 84000–86400：ds3 水面（不挖动船）∪ y≥5000，减去静止罾网船
mf = cv2.resize(m3[:, xf0:xf1], (2400, H0 := 6110), interpolation=cv2.INTER_LINEAR)
mf[5000:] = 1.0
st_ = np.zeros_like(mf)
cv2.rectangle(st_, (84440 - 84000, 5405), (85135 - 84000, 5610), 1.0, -1)     # 罾网船 + 网
mf = mf * (1 - cv2.GaussianBlur(st_, (0, 0), 10))
mf[:4300] = 0
mf = cv2.GaussianBlur(mf, (0, 0), 3)
np.save(D + 'wmask_full.npy', mf[4300:].astype(np.float32))                        # origin (84000,4300) unit 1
v = cv2.resize(np.ascontiguousarray(ds3[1300:]), (2500, 184)).astype(np.float32); mv = cv2.resize(m3[1300:] * ramp[None, :], (2500, 184))[..., None]
cv2.imwrite(D + 'wmask_vis2.jpg', cv2.cvtColor((v * (1 - .5 * mv) + np.float32([255, 0, 0]) * .5 * mv).astype(np.uint8), cv2.COLOR_RGB2BGR))
full = np.load(D + 'q_full.npy', mmap_mode='r')
v = cv2.resize(np.ascontiguousarray(full[4300:, :]), (800, 603)).astype(np.float32); mv = cv2.resize(mf[4300:], (800, 603))[..., None]
cv2.imwrite(D + 'wmaskf_vis2.jpg', cv2.cvtColor((v * (1 - .5 * mv) + np.float32([255, 0, 0]) * .5 * mv).astype(np.uint8), cv2.COLOR_RGB2BGR))
print('ok')
