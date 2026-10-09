# 预处理：主图转 npy（mmap 直读）、水面遮罩（flow 用 + 导出遮罩用）
import numpy as np, cv2, os
HOLE = 900   # v2: 只填 < 900 世界像素² 的小孔（水纹涡）；人和小物件不再算水（流速加大后会拖影）
RAW = '~/claude-projects/china-art/series/assets/qingming/qingming_cc_38414x1800.rgb'
W, H = 38414, 1800
D = os.path.dirname(os.path.abspath(__file__)) + '/work/'
A = np.memmap(RAW, dtype=np.uint8, mode='r', shape=(H, W, 3))
p = D + 'qm.npy'
if not os.path.exists(p):
    out = np.lib.format.open_memmap(p + '.tmp.npy', 'w+', np.uint8, (H, W, 3))
    for r in range(0, H, 200):
        out[r:r + 200] = A[r:r + 200]
    out.flush(); del out; os.replace(p + '.tmp.npy', p)

def water_mask(name, x0, y0, x1, y1, unit, thr, erode, polys_out=(), polys_in=None, feather=4):
    b = np.ascontiguousarray(A[y0:y1, x0:x1]).astype(np.float32)
    if unit > 1:
        b = cv2.resize(b, ((x1 - x0) // unit, (y1 - y0) // unit), interpolation=cv2.INTER_AREA)
    lum = b.mean(2)
    base = cv2.GaussianBlur(np.percentile(lum, 75) * np.ones_like(lum) * 0 + lum, (0, 0), 60 / unit)
    base = np.maximum(base, np.percentile(lum, 60))
    d = np.clip((base - lum) / base, 0, 1)
    Dd = cv2.GaussianBlur(d, (0, 0), 7 / unit)
    m = (Dd < thr).astype(np.uint8)
    # 小岛去掉：开运算
    k = max(3, int(9 / unit) | 1)
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((k, k), np.uint8))
    if polys_in is not None:
        pm = np.zeros_like(m)
        for poly in polys_in:
            cv2.fillPoly(pm, [((np.array(poly) - [x0, y0]) / unit).astype(np.int32)], 1)
        m &= pm
    for poly in polys_out:
        cv2.fillPoly(m, [((np.array(poly) - [x0, y0]) / unit).astype(np.int32)], 0)
    # 填掉水里的小孔（涡纹被误判为物体），免得水流中出现不动的斑点
    inv = (1 - m).astype(np.uint8)
    n, lab, st, _ = cv2.connectedComponentsWithStats(inv, 8)
    small = np.zeros(n, bool); small[1:] = st[1:, cv2.CC_STAT_AREA] < HOLE / unit / unit
    m[small[lab] & (inv > 0)] = 1
    if polys_in is not None:
        m &= pm
    np.save(D + f'raw_{name}.npy', m.astype(np.uint8))
    e = max(1, int(erode / unit))
    m = cv2.erode(m, np.ones((2 * e + 1, 2 * e + 1), np.uint8))
    mf = cv2.GaussianBlur(m.astype(np.float32), (0, 0), feather / unit)
    np.save(D + f'mask_{name}.npy', mf.astype(np.float32))
    if unit > 1:
        np.save(D + f'src_{name}.npy', np.clip(b + 0.5, 0, 255).astype(np.uint8))
    vis = b.copy(); vis[..., 0] = vis[..., 0] * (1 - 0.6 * mf) + 255 * 0.6 * mf
    f = min(1.0, 1800 / vis.shape[1])
    cv2.imwrite(D + f'vis_{name}.jpg', cv2.cvtColor(cv2.resize(np.clip(vis, 0, 255).astype(np.uint8), None, fx=f, fy=f, interpolation=cv2.INTER_AREA), cv2.COLOR_RGB2BGR))
    print(name, mf.shape, float(mf.mean()))

import sys
which = sys.argv[1:] or ['B', 'C', 'E']
if 'B' in which:   # 汴河漕船段：船下方开阔水面
    water_mask('B', 21800, 940, 29000, 1780, 2, 0.085, 14,
               polys_in=[[[21800, 1060], [23400, 1100], [25200, 1100], [26900, 1090], [27250, 1000], [29000, 1000], [29000, 1780], [21800, 1780]]])
if 'C' in which:   # 虹桥：桥下与船周围水面
    water_mask('C', 18950, 430, 21000, 1060, 1, 0.075, 10,
               polys_in=[[[18990, 740], [19150, 560], [19450, 505], [20600, 520], [21000, 520], [21000, 1060], [18950, 1060]]])
if 'E' in which:   # 结尾整屏水面
    water_mask('E', 23700, 1180, 24600, 1700, 1, 0.12, 6,
               polys_in=[[[23700, 1180], [24600, 1180], [24600, 1700], [23700, 1700]]])

if 'P' in which:   # 结尾水面的绢缝修补（x≈24178–24187 一道竖向绢缝/折痕）：用左侧 20 px 的同一行绢纹横向搬过来，边缘羽化
    x0, y0, x1, y1 = 23700, 1180, 24600, 1700
    p = np.ascontiguousarray(A[y0:y1, x0:x1]).astype(np.float32)
    xs = np.arange(x0, x1, dtype=np.float32)
    w = np.clip(np.minimum(xs - 24172, 24193 - xs) / 4.0, 0, 1)[None, :, None]
    sh = np.roll(p, 20, axis=1)          # sh[:, x] = p[:, x-20]
    p = p * (1 - w) + sh * w
    np.save(D + 'patchE.npy', np.clip(p + 0.5, 0, 255).astype(np.uint8))
    v = cv2.resize(np.clip(p[60:340, 400:600], 0, 255).astype(np.uint8), None, fx=3, fy=3, interpolation=cv2.INTER_NEAREST)
    cv2.imwrite(D + 'vis_patchE.jpg', cv2.cvtColor(v, cv2.COLOR_RGB2BGR))
    print('patchE', p.shape)

if 'W' in which:   # 虹桥大船船头分水：贴船舷急流 + 船头下侧 V 形尾迹（∩ 水面 raw_C）
    x0, y0 = 18950, 430
    raw = np.load(D + 'raw_C.npy').astype(np.float32)
    polys = {'hull': [[19480, 800], [19700, 797], [19850, 822], [20075, 762], [20262, 688], [20420, 612],
                      [20470, 690], [20290, 770], [20090, 850], [19850, 900], [19700, 880], [19470, 875]],
             'vlo': [[19470, 790], [19560, 805], [19900, 950], [19880, 995], [19800, 1000], [19440, 870], [19330, 840]]}
    for k, poly in polys.items():
        m = np.zeros_like(raw)
        cv2.fillPoly(m, [(np.array(poly) - [x0, y0]).astype(np.int32)], 1.0)
        rawe = cv2.erode(raw, np.ones((9, 9), np.uint8))
        m = cv2.GaussianBlur(m, (0, 0), 22) * cv2.GaussianBlur(rawe, (0, 0), 3)
        m = np.clip(m * 1.6, 0, 1) * 0.9
        ys, xs = np.where(m > 0.004)
        a0, a1, b0, b1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
        np.save(D + f'mask_W{k}.npy', m[a0:a1, b0:b1].astype(np.float32))
        open(D + f'mask_W{k}.origin', 'w').write(f'{x0 + b0} {y0 + a0}')
        print('wake', k, (x0 + b0, y0 + a0), m[a0:a1, b0:b1].shape)

def fill_water(tex, water, step=24):
    """把非水面像素（人、船、岸）用左侧同一行的水纹一格格搬过来填满，供 flow 当源纹理：
    水流平移取样时不会把人、船身拖进水里（v1 的拖影/重影）。"""
    out = tex.copy(); valid = water.astype(bool).copy()
    for sgn in (1, -1):
        for _ in range(400):
            if valid.all():
                break
            sh = np.roll(out, sgn * step, axis=1); sv = np.roll(valid, sgn * step, axis=1)
            if sgn > 0:
                sv[:, :step] = False
            else:
                sv[:, -step:] = False
            take = ~valid & sv
            if not take.any():
                break
            out[take] = sh[take]; valid |= take
    return out

if 'F' in which:   # 填好的流动源纹理：C（含船头分水两块）、B
    raw = np.load(D + 'raw_C.npy').astype(np.uint8)
    wat = cv2.erode(raw, np.ones((5, 5), np.uint8))
    tex = np.ascontiguousarray(A[430:1060, 18950:21000])
    f = fill_water(tex, wat)
    np.save(D + 'srcf_C.npy', f)
    for k in ('hull', 'vlo'):
        m = np.load(D + f'mask_W{k}.npy'); ox, oy = [int(v) for v in open(D + f'mask_W{k}.origin').read().split()]
        np.save(D + f'srcf_W{k}.npy', np.ascontiguousarray(f[oy - 430:oy - 430 + m.shape[0], ox - 18950:ox - 18950 + m.shape[1]]))
    rawB = np.load(D + 'raw_B.npy').astype(np.uint8)
    watB = cv2.erode(rawB, np.ones((3, 3), np.uint8))
    texB = np.load(D + 'src_B.npy')
    np.save(D + 'srcf_B.npy', fill_water(texB, watB, step=12))
    v = np.concatenate([tex[250:630, 700:1500], f[250:630, 700:1500]], 0)
    cv2.imwrite(D + 'vis_fillC.jpg', cv2.cvtColor(v, cv2.COLOR_RGB2BGR))
    print('fill ok', f.shape, texB.shape)
