# -*- coding: utf-8 -*-
"""汝窑全器正侧面照（PAE）→ 展台画布：器物像素原样保留；影棚灰背景按"比值法"换成柔和纸/绢色
（保留原照的接触阴影与局部明暗），并向四周延展；背景叠极淡的真实绢纹（溪山裱绫）。
输出 work/pae_stage.npy（RGB uint8），世界坐标 = PAE 原图像素，画布原点 ORIGIN。"""
import os, sys, numpy as np, cv2
HERE = os.path.dirname(os.path.abspath(__file__))
S = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(S, 'lib'))
import engine as E

SRC = os.path.join(S, 'assets/ru/ru_full_front_PAE.jpg')
ORIGIN = (-1400, -500)            # 画布左上角的世界坐标
SIZE = (5900, 3700)               # 画布宽高（世界像素 = PAE 像素）
PAPER = np.float32([212, 206, 193])   # 纸/绢色（暖浅灰，和天青釉协调）
OUT = os.path.join(HERE, 'work', 'pae_stage.npy')


def matte(img):
    H, W = img.shape[:2]
    k = 3
    sm = cv2.resize(img, (W // k, H // k), interpolation=cv2.INTER_AREA)
    rgb = sm.astype(np.float32)
    chroma = (rgb[..., 1] + rgb[..., 2]) / 2 - rgb[..., 0]      # 釉：G,B 高于 R；背景中性
    m = np.full(sm.shape[:2], cv2.GC_BGD, np.uint8)
    rect = (380 // k, 700 // k, 2320 // k, 1250 // k)
    x, y, w, h = rect
    m[y:y + h, x:x + w] = cv2.GC_PR_BGD
    m[(chroma > 12) & (m == cv2.GC_PR_BGD)] = cv2.GC_PR_FGD
    m[(chroma > 20) & (m == cv2.GC_PR_FGD)] = cv2.GC_FGD
    bgd = np.zeros((1, 65), np.float64); fgd = np.zeros((1, 65), np.float64)
    cv2.grabCut(cv2.cvtColor(sm, cv2.COLOR_RGB2BGR), m, None, bgd, fgd, 6, cv2.GC_INIT_WITH_MASK)
    fg = ((m == cv2.GC_FGD) | (m == cv2.GC_PR_FGD)).astype(np.uint8)
    # 最大连通域 + 填洞
    n, lab, st, _ = cv2.connectedComponentsWithStats(fg)
    big = 1 + int(np.argmax(st[1:, cv2.CC_STAT_AREA]))
    fg = (lab == big).astype(np.uint8)
    ff = fg.copy(); cv2.floodFill(ff, None, (0, 0), 1); fg = fg | (1 - ff)
    fg = cv2.morphologyEx(fg, cv2.MORPH_CLOSE, np.ones((7, 7), np.uint8))
    a = cv2.resize(fg.astype(np.float32), (W, H), interpolation=cv2.INTER_LINEAR)
    a = cv2.GaussianBlur(a, (0, 0), 2.5)
    return np.clip((a - 0.5) * 1.6 + 0.5, 0, 1)


def main():
    img = cv2.cvtColor(cv2.imread(SRC), cv2.COLOR_BGR2RGB)
    H, W = img.shape[:2]
    a = matte(img)
    np.save(os.path.join(HERE, 'work', 'pae_matte.npy'), (a * 255).astype(np.uint8))
    f = img.astype(np.float32)
    lum = f.mean(2)
    # 背景平滑模型（归一化卷积，排除器物及其外扩一圈）
    k = 8
    bgm = (cv2.dilate((a > 0.02).astype(np.uint8), np.ones((61, 61), np.uint8)) == 0).astype(np.float32)
    ls = cv2.resize(lum * bgm, (W // k, H // k), interpolation=cv2.INTER_AREA)
    ms = cv2.resize(bgm, (W // k, H // k), interpolation=cv2.INTER_AREA)
    sig = 22
    model = cv2.GaussianBlur(ls, (0, 0), sig) / np.maximum(cv2.GaussianBlur(ms, (0, 0), sig), 1e-4)
    model = cv2.resize(model, (W, H), interpolation=cv2.INTER_CUBIC)
    ratio = lum / np.maximum(model, 1)
    ratio = 1 + cv2.GaussianBlur(ratio - 1, (0, 0), 1.2)
    ratio = np.clip(ratio, 0.45, 1.0)
    # 只在器物下方（接触阴影所在）保留原照明暗，其余处用干净纸色
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    dl = ((xx - 1560) / 1450) ** 2 + ((yy - 1760) / 380) ** 2
    ratio = 1 + (ratio - 1) * (1 - E.sstep(0.55, 1.0, dl))
    # 画布
    CW, CH = SIZE
    ox, oy = ORIGIN
    ys = np.arange(CH, dtype=np.float32)[:, None] + oy
    xs = np.arange(CW, dtype=np.float32)[None, :] + ox
    # 目标纸色：器物后方略亮，四周自然衰减（柔和灯光），下方地面略暗一点
    cx, cy = 1560, 1250
    d2 = ((xs - cx) / 3000) ** 2 + ((ys - cy) / 2300) ** 2
    shade = 1.0 - 0.13 * np.clip(d2, 0, 1.5)
    shade = shade - 0.035 * np.clip((ys - 1900) / 900, 0, 1)
    T = PAPER[None, None, :] * shade[..., None]
    # 真实绢纹（溪山裱绫，高通、极淡）
    xs_src = '~/claude-projects/china-art/trailer/assets_v3/xishan/work_full.npy'
    A = np.load(xs_src, mmap_mode='r'); SH, SW = A.shape[:2]
    bw = int(SW * 0.04)
    samples = [(xs_src, [int(SW * 0.004), int(SH * 0.2), bw, int(SH * 0.88)]),
               (xs_src, [SW - bw, int(SH * 0.2), SW - int(SW * 0.004), int(SH * 0.88)])]
    wp = E.silk_wall('ru_paper', samples, (CW, CH), unit=4, tex_scale=1.3, tone=(1, 1, 1), light=None)
    wall = np.load(wp).astype(np.float32)
    wall = cv2.resize(wall, (CW, CH), interpolation=cv2.INTER_CUBIC)
    wl = wall.mean(2)
    tex = wl / np.maximum(cv2.GaussianBlur(wl, (0, 0), 5), 1)   # 只留细纤维，去掉暗花（祥云纹）
    tex = 1 + 0.35 * (tex - 1)
    bg = T * tex[..., None]
    # 照片区域：背景 = 目标色 × 原照相对明暗（保留接触阴影），器物原样
    y0, x0 = -oy, -ox
    reg = bg[y0:y0 + H, x0:x0 + W]
    # 照片边缘处 ratio 渐回 1，避免照片边框痕迹
    ey = np.minimum(np.arange(H), H - 1 - np.arange(H)).astype(np.float32)
    ex = np.minimum(np.arange(W), W - 1 - np.arange(W)).astype(np.float32)
    edge = np.minimum(ey[:, None], ex[None, :])
    wedge = E.sstep(0, 160, edge)
    r = 1 + (ratio - 1) * wedge
    newbg = reg * r[..., None]
    reg[:] = f * a[..., None] + newbg * (1 - a[..., None])
    out = np.clip(bg + 0.5, 0, 255).astype(np.uint8)
    np.save(OUT + '.tmp.npy', out); os.replace(OUT + '.tmp.npy', OUT)
    prev = cv2.resize(out, (CW // 5, CH // 5), interpolation=cv2.INTER_AREA)
    cv2.imwrite(os.path.join(HERE, 'work', 'pae_stage_prev.jpg'), cv2.cvtColor(prev, cv2.COLOR_RGB2BGR), [cv2.IMWRITE_JPEG_QUALITY, 90])
    mv = cv2.resize((a * 255).astype(np.uint8), (W // 3, H // 3))
    cv2.imwrite(os.path.join(HERE, 'work', 'pae_matte_prev.png'), mv)
    print('ok', out.shape)


if __name__ == '__main__':
    main()
