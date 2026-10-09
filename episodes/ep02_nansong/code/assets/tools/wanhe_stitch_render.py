# 按 stitch_solution.json 把 8 块瓦片渲成一张无缝大图（逐条带渲染，羽化混合 + 每块每通道增益补偿）
import cv2, numpy as np, json, os
D = os.path.dirname(os.path.abspath(__file__)) + '/../wanhe/'
sol = json.load(open(D + 'work/stitch_solution.json'))
T = list(sol['A'].keys()); A = {t: np.array(sol['A'][t]) for t in T}
IM = {t: cv2.imread(D + 'full/K2A000896N000000000%s.jpg' % t, cv2.IMREAD_COLOR) for t in T}   # BGR
def corners(t):
    h, w = IM[t].shape[:2]; c = np.array([[0, 0], [w, 0], [w, h], [0, h]], float); return c @ A[t][:, :2].T + A[t][:, 2]
allc = np.vstack([corners(t) for t in T]); X0, Y0 = np.floor(allc.min(0)).astype(int); X1, Y1 = np.ceil(allc.max(0)).astype(int)
W, H = int(X1 - X0), int(Y1 - Y0); print('mosaic', W, H, 'origin (mosaic coords)', X0, Y0)
R = 300.0
def wmap(t):
    h, w = IM[t].shape[:2]
    x = np.arange(w, dtype=np.float32); y = np.arange(h, dtype=np.float32)
    rx = np.clip(np.minimum(x, w - 1 - x) / R, 0, 1); ry = np.clip(np.minimum(y, h - 1 - y) / R, 0, 1)
    rx = rx * rx * (3 - 2 * rx); ry = ry * ry * (3 - 2 * ry)
    return (ry[:, None] * rx[None, :]).astype(np.float32)
WM = {t: wmap(t) for t in T}
def shifted(t, ox, oy, s=1.0):
    M = A[t].copy(); M[:, 2] -= [ox, oy]; return M * s
# ---- 增益：1/8 分辨率下两两重叠区均值比
s = 0.125; w8, h8 = int(W * s) + 1, int(H * s) + 1
low = {}; lw = {}
for t in T:
    M = shifted(t, X0, Y0, s)
    low[t] = cv2.warpAffine(IM[t].astype(np.float32), M, (w8, h8), flags=cv2.INTER_AREA, borderMode=cv2.BORDER_CONSTANT)
    lw[t] = cv2.warpAffine(np.ones(IM[t].shape[:2], np.float32), M, (w8, h8), flags=cv2.INTER_LINEAR)
    lw[t] = cv2.erode((lw[t] > 0.999).astype(np.uint8), np.ones((9, 9), np.uint8)).astype(bool)
rows, rhs = [], []
for a in range(len(T)):
    for b in range(a + 1, len(T)):
        m = lw[T[a]] & lw[T[b]]
        if m.sum() < 2000: continue
        la = np.log(low[T[a]][m].mean(0)); lb = np.log(low[T[b]][m].mean(0))
        r = np.zeros(len(T)); r[a] = 1; r[b] = -1; rows.append(r); rhs.append(lb - la)
rows.append(np.ones(len(T)) * 3); rhs.append(np.zeros(3))
g, *_ = np.linalg.lstsq(np.array(rows), np.array(rhs), rcond=None); gain = np.exp(g)
for t, gg in zip(T, gain): print('gain', t, np.round(gg[::-1], 4), '(RGB)')
# ---- 渲染
out_path = D + 'wanhe_mosaic_%dx%d.rgb' % (W, H)
out = np.memmap(out_path, np.uint8, 'w+', shape=(H, W, 3))
seam = []
for y0 in range(0, H, 512):
    hh = min(512, H - y0); acc = np.zeros((hh, W, 3), np.float32); wsum = np.zeros((hh, W), np.float32)
    per = []
    for k, t in enumerate(T):
        c = corners(t) - [X0, Y0]
        if c[:, 1].max() < y0 or c[:, 1].min() > y0 + hh: continue
        M = shifted(t, X0, Y0 + y0)
        img = cv2.warpAffine(IM[t], M, (W, hh), flags=cv2.INTER_LANCZOS4, borderMode=cv2.BORDER_CONSTANT).astype(np.float32) * gain[k][None, None, :]
        wt = cv2.warpAffine(WM[t], M, (W, hh), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
        acc += img * wt[..., None]; wsum += wt; per.append((img, wt))
    # 接缝检查：两块都有效处的高频差
    for i in range(len(per)):
        for j in range(i + 1, len(per)):
            m = (per[i][1] > 0.05) & (per[j][1] > 0.05)
            if m.sum() > 5000:
                a = per[i][0].mean(2); b = per[j][0].mean(2)
                ha = a - cv2.GaussianBlur(a, (0, 0), 3); hb = b - cv2.GaussianBlur(b, (0, 0), 3)
                seam.append(float(np.sqrt(((ha - hb)[m] ** 2).mean()) / (np.sqrt((ha[m] ** 2).mean()) + 1e-6)))
    res = acc / np.maximum(wsum, 1e-6)[..., None]
    out[y0:y0 + hh] = np.clip(res, 0, 255).astype(np.uint8)[..., ::-1]
    print('rows', y0, y0 + hh, flush=True)
out.flush()
print('seam relative HF diff (0 = 完全一致, 1 = 不相关): median %.3f max %.3f' % (np.median(seam), max(seam)))
json.dump(dict(W=W, H=H, origin_mosaic=[int(X0), int(Y0)], scale_vs_PGZ=sol['scale_vs_PGZ'], gains={t: gain[k].tolist() for k, t in enumerate(T)},
               note='文件像素 (x,y) = PGZ 像素 × 2 − origin；PGZ = K2A000896N000000000PGZ.jpg（2252×3109 整幅）'), open(D + 'wanhe_mosaic_meta.json', 'w'), indent=1)
# 预览
a = np.memmap(out_path, np.uint8, 'r', shape=(H, W, 3))
pv = cv2.resize(np.asarray(a[::4, ::4]), (W // 8, H // 8), interpolation=cv2.INTER_AREA)
cv2.imwrite(D + 'wanhe_mosaic_preview_ds8.jpg', pv[..., ::-1], [cv2.IMWRITE_JPEG_QUALITY, 90])
