# -*- coding: utf-8 -*-
"""s3 寒江独钓 · 素材准备（只读原图，产物在 work/）
  paint.npy   原图（Commons 5906×3159，未改色）
  plate.npy   干净底板：船+渔翁+竿、钓丝原位置用"周围低频 + 上方空绢高频"补成绢
  boat.npy    RGBA 精灵：船、渔翁、竿（直通 alpha），世界坐标 origin 见 meta.json
  line.npy    RGBA 精灵：钓丝（竿梢 → 入水点）
  wall        E.silk_wall（本画空白绢的纹理，色调按北宋集墙面 180,167,132）
用法：lockf -k $S/.heavy.lock python3 prep.py
"""
import os, sys, json
import numpy as np, cv2
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__))
S = '~/claude-projects/china-art/series'
sys.path.insert(0, os.path.join(S, 'lib'))
import engine as E

SRC = os.path.join(S, 'ep02_nansong/assets/hanjiang/src_hanjiang_commons_5906x3159.jpg')
WK = os.path.join(HERE, 'work'); os.makedirs(WK, exist_ok=True)

# 船+渔翁+竿的外轮廓（世界坐标，按 look/grid_boat.jpg 描），会再外扩并与墨/色检测求交
BOAT_POLY = [(1426, 1884), (1560, 1856), (1700, 1778), (1720, 1700), (1748, 1656), (1832, 1648), (1858, 1698),
             (1916, 1720), (2002, 1788), (2044, 1868), (2062, 1936), (2226, 1926), (2236, 1898), (2268, 1900),
             (2276, 1946), (2336, 1950), (2344, 1826), (2440, 1800), (2560, 1780), (2664, 1786), (2764, 1836),
             (2900, 1876), (3000, 1910), (3230, 1846), (3500, 1736), (3756, 1584), (3806, 1586), (3834, 1660),
             (3764, 1762), (3232, 2082), (2982, 2114), (2622, 2160), (2200, 2168), (1880, 2148), (1678, 2066),
             (1674, 1950), (1560, 1902), (1440, 1914)]
BOAT_BOX = (1380, 1540, 3880, 2220)       # x0,y0,x1,y1
LINE_BOX = (840, 1860, 1460, 2200)
TIP = (1438, 1897)                        # 竿梢
ENTRY = (872, 2160)                       # 钓丝入水点（涟漪圆心）
DONOR_DY = -560                           # 补洞纹理取自正上方空绢


def main():
    a = np.asarray(Image.open(SRC).convert('RGB'))
    H, W = a.shape[:2]
    np.save(os.path.join(WK, 'paint.npy'), a)
    af = a.astype(np.float32)
    bg = cv2.medianBlur(a, 41).astype(np.float32)
    dist = np.sqrt(((af - bg) ** 2).sum(2))

    # ---- 船精灵 mask ----
    x0, y0, x1, y1 = BOAT_BOX
    poly = np.zeros((H, W), np.uint8)
    cv2.fillPoly(poly, [np.int32(BOAT_POLY)], 1)
    polyd = cv2.dilate(poly, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (25, 25)))
    ink = (dist > 15).astype(np.uint8) & polyd
    ink = cv2.morphologyEx(ink, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15)))
    # 填内部小洞（船身、衣袍内部少量与绢同色的点）
    inv = (1 - ink).astype(np.uint8)
    n, lab, st, _ = cv2.connectedComponentsWithStats(inv[y0:y1, x0:x1], 4)
    for i in range(1, n):
        if st[i, cv2.CC_STAT_AREA] < 4000:
            ink[y0:y1, x0:x1][lab == i] = 1
    n, lab, st, _ = cv2.connectedComponentsWithStats(ink[y0:y1, x0:x1], 8)
    big = np.zeros_like(ink[y0:y1, x0:x1])
    for i in range(1, n):
        if st[i, cv2.CC_STAT_AREA] >= 3000:
            big[lab == i] = 1
    m = np.zeros_like(ink); m[y0:y1, x0:x1] = big
    m = cv2.dilate(m, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7)))
    mb = cv2.GaussianBlur(m.astype(np.float32), (0, 0), 2.0)
    boat_a = np.clip(mb * 1.6 - 0.3, 0, 1)

    # ---- 钓丝 mask（竿梢以左）----
    lx0, ly0, lx1, ly1 = LINE_BOX
    lm = np.zeros((H, W), np.uint8)
    sub = dist[ly0:ly1, lx0:lx1]
    # 钓丝走向：竿梢→入水点的下垂弧，取检测结果在一条宽带内
    band = np.zeros_like(lm)
    pts = []
    for u in np.linspace(0, 1, 60):
        x = ENTRY[0] + (TIP[0] - ENTRY[0]) * u
        # 下垂：直线 + 向下的抛物线偏移（按 look 目测）
        y = ENTRY[1] + (TIP[1] - ENTRY[1]) * u + 60 * 4 * u * (1 - u) * 0.0
        pts.append((x, y))
    # 用实际检测：在宽带（±70 px 于直线）里找细线
    xx, yy = np.meshgrid(np.arange(lx0, lx1), np.arange(ly0, ly1))
    vx, vy = TIP[0] - ENTRY[0], TIP[1] - ENTRY[1]
    L = np.hypot(vx, vy)
    dperp = ((xx - ENTRY[0]) * vy - (yy - ENTRY[1]) * vx) / L
    upar = ((xx - ENTRY[0]) * vx + (yy - ENTRY[1]) * vy) / L / L
    near = (np.abs(dperp) < 90) & (upar > -0.03) & (upar < 1.0) & (xx < TIP[0] - 4)
    det = ((sub > 13) & near).astype(np.uint8)
    n, lab, st, _ = cv2.connectedComponentsWithStats(det, 8)
    k = 1 + int(np.argmax(st[1:, cv2.CC_STAT_AREA]))
    ys, xs = np.nonzero(lab == k)
    cf = np.polyfit(xs + lx0, ys + ly0, 3)
    curve = np.polyval(cf, xx)
    keep = (det > 0) & (np.abs(yy - curve) < 7) & (xx >= ENTRY[0] - 6)
    lm[ly0:ly1, lx0:lx1] = keep.astype(np.uint8)
    json.dump({'poly': cf.tolist()}, open(os.path.join(WK, 'line_fit.json'), 'w'))
    lm = cv2.dilate(lm, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7)))
    line_a = np.clip(cv2.GaussianBlur(lm.astype(np.float32), (0, 0), 1.6) * 1.5 - 0.2, 0, 1)
    line_a[:, :lx0] = 0; line_a[:, lx1:] = 0
    print('line px', int(lm.sum()), 'boat px', int(m.sum()))

    # ---- 干净底板 ----
    RX0, RY0, RX1, RY1 = 600, 1000, 4100, 2500      # 只在船区算底板（省内存）
    hole = np.maximum(m, lm).astype(np.float32)      # 只补精灵核心区（精灵 alpha 比它宽，底板补的绢只在船动时露一条）
    hole = hole[RY0:RY1, RX0:RX1]
    ar = af[RY0:RY1, RX0:RX1]
    sig = 45
    # 低频：1/8 尺度 inpaint 后放大（大洞中心也有正确的绢色）
    sh, sw = ar.shape[0] // 8, ar.shape[1] // 8
    small = cv2.resize(ar, (sw, sh), interpolation=cv2.INTER_AREA)
    smask = (cv2.resize(cv2.dilate(hole, np.ones((9, 9), np.uint8)), (sw, sh), interpolation=cv2.INTER_AREA) > 0.01).astype(np.uint8)
    small = cv2.inpaint(np.clip(small, 0, 255).astype(np.uint8), smask, 12, cv2.INPAINT_TELEA).astype(np.float32)
    small = cv2.GaussianBlur(small, (0, 0), 3)
    low = cv2.resize(small, (ar.shape[1], ar.shape[0]), interpolation=cv2.INTER_CUBIC)
    donor = af[RY0 + DONOR_DY:RY1 + DONOR_DY, RX0:RX1]
    dlow = cv2.GaussianBlur(donor, (0, 0), sig)
    fill = low + (donor - dlow)
    hw = np.clip(cv2.GaussianBlur(hole, (0, 0), 2) * 1.5, 0, 1)[..., None]
    pr = ar * (1 - hw) + fill * hw
    plate = a.copy()
    plate[RY0:RY1, RX0:RX1] = np.clip(pr + 0.5, 0, 255).astype(np.uint8)
    np.save(os.path.join(WK, 'plate.npy'), plate)

    # ---- 精灵 ----
    def sprite(alpha, box, name):
        x0, y0, x1, y1 = box
        rgba = np.concatenate([a[y0:y1, x0:x1], np.clip(alpha[y0:y1, x0:x1] * 255 + 0.5, 0, 255).astype(np.uint8)[..., None]], 2)
        np.save(os.path.join(WK, name + '.npy'), np.ascontiguousarray(rgba))
        Image.fromarray(rgba).save(os.path.join(HERE, 'look', name + '_sprite.png'))
    sprite(boat_a, BOAT_BOX, 'boat')
    sprite(line_a, LINE_BOX, 'line')
    # 核对图：底板（船区）
    Image.fromarray(plate[1450:2300, 700:3950]).resize((1625, 425)).save(os.path.join(HERE, 'look', 'plate_boat.jpg'), quality=90)

    # ---- 墙：本画空白绢的纹理，色调对齐北宋集墙面 ----
    samples = [(os.path.join(WK, 'paint.npy'), [300, 250, 1500, 1350]), (os.path.join(WK, 'paint.npy'), [4100, 1150, 5500, 2350]),
               (os.path.join(WK, 'paint.npy'), [2200, 2450, 3900, 3050])]
    med = np.median(np.concatenate([af[r[1]:r[3]:7, r[0]:r[2]:7].reshape(-1, 3) for _, r in samples]), 0)
    tone = tuple(float(x) for x in (np.float32([180, 167, 132]) / med))
    json.dump(dict(W=W, H=H, boat_origin=[BOAT_BOX[0], BOAT_BOX[1]], line_origin=[LINE_BOX[0], LINE_BOX[1]], tip=TIP,
                   entry=ENTRY, tone=tone, samples=[[p, r] for p, r in samples]), open(os.path.join(WK, 'meta.json'), 'w'), indent=1)
    print('tone', tone)


if __name__ == '__main__':
    main()
