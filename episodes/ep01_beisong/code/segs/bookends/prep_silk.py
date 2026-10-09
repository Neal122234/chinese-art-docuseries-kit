"""绢底：取《谿山行旅图》主峰左上空白绢（原图 x 2450–4170, y 3690–4658，1:1 真实像素），
去掉小污点（Telea 修补，只动离群点），整体按乘法增益调到夜宴图的绢色再压暗一点（暖暗），纹理不动。"""
import numpy as np, cv2
XS = '~/claude-projects/china-art/trailer/assets_v3/xishan/work_full.npy'
Y = '~/claude-projects/china-art/trailer/assets_v3/yeyan/work_listen_16000x3981.rgb'
a = np.load(XS, mmap_mode='r')
x0, y0, W, H = 2450, 3690, 1720, 968
s = np.ascontiguousarray(a[y0:y0 + H, x0:x0 + W]).astype(np.float32)
lum = cv2.GaussianBlur(s.mean(2), (0, 0), 2.5)          # 先抹掉经纬纹，只看成团的斑
dl = lum - cv2.GaussianBlur(lum, (0, 0), 30)
mad = 1.4826 * np.median(np.abs(dl)) + 1e-3
ch = cv2.GaussianBlur(s[..., 0] - s[..., 1], (0, 0), 3)
dc = ch - cv2.GaussianBlur(ch, (0, 0), 40); mc = 1.4826 * np.median(np.abs(dc)) + 1e-3
bad = ((np.abs(dl) > 3.2 * mad) | (dc > 3.5 * mc)).astype(np.uint8)
n, lab, st, _ = cv2.connectedComponentsWithStats(bad)
blob = np.zeros_like(bad)
for i in range(1, n):
    if st[i, 4] >= 25:
        blob[lab == i] = 1
blob = cv2.dilate(blob, np.ones((9, 9), np.uint8))
cv2.imwrite('review/silk_blob.png', blob * 255)
print('blob px', int(blob.sum()))
# 修补 = 低频用 Telea 补 + 高频经纬纹从旁边未污染处平移借来（补处仍有真实织纹，不会是一块糊）
low = cv2.GaussianBlur(s, (0, 0), 5)
hp = s - low
lowf = cv2.inpaint(np.clip(low, 0, 255).astype(np.uint8), blob, 9, cv2.INPAINT_TELEA).astype(np.float32)
hpf = hp.copy(); todo = blob.astype(bool).copy()
for dx, dy in [(64, 0), (-64, 0), (0, 64), (0, -64), (128, 32), (-128, -32), (96, 96), (-96, 96)]:
    sh = np.roll(hp, (dy, dx), (0, 1)); okm = ~np.roll(blob.astype(bool), (dy, dx), (0, 1))
    use = todo & okm
    hpf[use] = sh[use]; todo &= ~use
fm = cv2.GaussianBlur(blob.astype(np.float32), (0, 0), 2)[..., None]
s8 = s * (1 - fm) + (lowf + hpf) * fm
# 大尺度污渍减弱一半（保留绢的自然深浅）
low = cv2.GaussianBlur(s8, (0, 0), 60)
s8 = s8 - 0.5 * (low - low.reshape(-1, 3).mean(0))
y = np.memmap(Y, np.uint8, 'r', shape=(3981, 16000, 3))
ref = np.ascontiguousarray(y[400:2000, 5000:5450]).astype(np.float32)
tgt = np.median(ref.reshape(-1, 3), 0)
mu = s8.reshape(-1, 3).mean(0)
g = (0.72 * tgt + 0.28 * mu * tgt.mean() / mu.mean()) * 0.84 / mu
out = np.clip(s8 * g + 0.5, 0, 255).astype(np.uint8)
print('xishan mu', mu, 'yeyan silk', tgt, 'gain', g, 'out mean', out.reshape(-1, 3).mean(0))
np.save('work/silk.npy', out)
cv2.imwrite('review/silk_full.jpg', cv2.cvtColor(cv2.resize(out, (1280, 720), interpolation=cv2.INTER_AREA), cv2.COLOR_RGB2BGR), [cv2.IMWRITE_JPEG_QUALITY, 92])
cv2.imwrite('review/silk_ref_yeyan.jpg', cv2.cvtColor(np.ascontiguousarray(y[400:1100, 5000:5450]), cv2.COLOR_RGB2BGR))
