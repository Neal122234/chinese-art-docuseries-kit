import numpy as np, cv2
P = np.load('P2.npy', mmap_mode='r')
# waterfall: tophat, keep long vertical components
x0, y0, x1, y1 = 3950, 3200, 4450, 6200
c = np.ascontiguousarray(P[y0:y1, x0:x1]); L = cv2.GaussianBlur(cv2.cvtColor(c, cv2.COLOR_RGB2GRAY).astype(np.float32), (0, 0), 1.0)
th = L - cv2.morphologyEx(L, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_RECT, (25, 1)))
m = np.clip((th - 6) / 12, 0, 1)
cor = np.zeros(m.shape, np.uint8)
A = [(4150,3700),(4150,4200),(4135,4400),(4110,4800),(4095,5100),(4085,5300),(4080,6100)]
B = [(4095,5250),(4140,5320),(4150,5600),(4152,6100)]
for pl in (A, B):
    cv2.polylines(cor, [np.array([(x - x0, y - y0) for x, y in pl], np.int32)], False, 1, 56)
b = ((m > 0.3) & (cor > 0)).astype(np.uint8)
n, lab, st, _ = cv2.connectedComponentsWithStats(b, 8)
keep = np.zeros(n, bool); keep[1:] = st[1:, cv2.CC_STAT_HEIGHT] >= 60
m = m * cv2.dilate(keep[lab].astype(np.uint8), np.ones((5, 5), np.uint8)) * cor
m = cv2.GaussianBlur(m, (0, 0), 0.8)
np.save('layers/wf_mask.npy', m.astype(np.float32)); print('wf px', int((m > 0.3).sum()))
vis = c.copy(); vis[..., 0] = np.clip(vis[..., 0] + m * 160, 0, 255)
cols = [cv2.resize(vis[i * 1000:(i + 1) * 1000], (250, 500), interpolation=cv2.INTER_AREA) for i in range(3)]
cv2.imwrite('wf_mask_vis.jpg', cv2.cvtColor(np.hstack(cols), cv2.COLOR_RGB2BGR))
# cascade: hand regions x brightness weight
x0, y0, x1, y1 = 1950, 7750, 2450, 8330
c = np.ascontiguousarray(P[y0:y1, x0:x1]); L = cv2.GaussianBlur(cv2.cvtColor(c, cv2.COLOR_RGB2GRAY).astype(np.float32), (0, 0), 1.2)
reg = np.zeros(L.shape, np.uint8)
cv2.fillPoly(reg, [np.array([(228, 92), (300, 80), (445, 92), (448, 250), (225, 255)], np.int32)], 1)
cv2.fillPoly(reg, [np.array([(95, 372), (300, 362), (390, 372), (395, 548), (95, 548)], np.int32)], 1)
regf = cv2.GaussianBlur(reg.astype(np.float32), (0, 0), 8)
loc = cv2.GaussianBlur(L, (0, 0), 25)
wgt = np.clip((L - loc + 4) / 18, 0, 1)
m2 = regf * wgt
np.save('layers/cas_mask.npy', m2.astype(np.float32)); print('cas px', int((m2 > 0.3).sum()))
vis = c.copy(); vis[..., 0] = np.clip(vis[..., 0] + m2 * 160, 0, 255)
cv2.imwrite('cas_mask_vis.jpg', cv2.cvtColor(vis, cv2.COLOR_RGB2BGR))
