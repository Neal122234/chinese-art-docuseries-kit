# -*- coding: utf-8 -*-
# 【工具包说明】手卷全貌·长案透视镜头（清明、千里江山共用）：整卷平铺长案、暖光走卷、俯冲降入卷首，末帧交接 engine 平面相机。
# 输入：手卷原图 .npy、绢纹样本、色调；输出：逐帧 RGB（shot.frame(t)），由段文件调用。无硬编码路径（依赖同目录 engine.py）。
# 跑法：段文件里 import scrollview as SV（见下方 docstring 用法）。
"""手卷全貌 · 长案透视（清明、千里江山共用）。

整卷平铺在一张长长的绢面长案上，镜头从卷首一侧斜看过去：全卷全长可见，近大远小，向远处没入暖暗；
一道暖光沿卷从卷首走到卷尾（"五米多"被光走一遍）；镜头贴卷面缓缓滑行，然后俯冲、转正、降入卷首，
最后一帧与 engine 的平面相机状态 {cx, cy, vh} 完全等价（纯俯视 = 相似变换），直接交接给普通镜头。

用法（世界坐标 = 手卷原图像素，x 向右、y 向下；卷首在右端）：
    import scrollview as SV
    sv = SV.ScrollView(QM_NPY, name='qingming', silk=SILK_SAMPLES, tone=TONE, res=720)
    shot = SV.overview_shot(sv, t_in=8.5, t_glide=13.6, t_land=18.2, land={'cx':37250,'cy':897,'vh':2190})
    frame = shot.frame(t)                    # (H,W,3) uint8，t 为本段时间
    shot.land_state                          # 交接状态：t_land 之后用 engine 相机 cam((t_land, cx, cy, vh)) 接上
重活（首次建桌面绢纹、mip）走 lockf 全局锁。
"""
import os, sys, math
import numpy as np, cv2

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import engine as E


def _sm(x):
    x = np.clip(x, 0.0, 1.0)
    return x * x * (3 - 2 * x)


def _trap(x, r):
    """梯形速度曲线（两端各 r 比例线性加减速，中段匀速），0..1 → 0..1。峰速 = 1/(1-r) × 平均。"""
    x = min(max(x, 0.0), 1.0)
    if r <= 1e-6:
        return x
    v = 1.0 / (1 - r)
    if x < r:
        return v * x * x / (2 * r)
    if x < 1 - r:
        return v * (r / 2 + x - r)
    return 1 - v * (1 - x) ** 2 / (2 * r)


def _sm5(x):     # smootherstep：端点加速度为 0
    x = min(max(x, 0.0), 1.0)
    return x * x * x * (x * (6 * x - 15) + 10)


class ScrollView:
    """src: 手卷 RGB npy（可 memmap）；silk: [(npy, [x0,y0,x1,y1])] 空白绢样本（同 engine.silk_wall）。"""

    def __init__(self, src, name, silk, tone=(0.84, 0.80, 0.71), res=720, ss=2, table_unit=4, tex_scale=1.6,
                 margin=(6000, 4200), dark=(46, 38, 30), shadow=None, lod_bias=None):
        self.name = name
        self.lod_bias = (-0.45 if ss == 1 else 0.0) if lod_bias is None else lod_bias
        self.lv = E.build_mips(src, name + '_scroll')
        self.Hsrc, self.Wsrc = self.lv[0].shape[:2]
        self.H = int(res); self.W = int(round(self.H * 16 / 9 / 2) * 2)
        self.SS = ss; self.WS, self.HS = self.W * ss, self.H * ss
        W, H = self.Wsrc, self.Hsrc
        mx, my = margin
        sh = shadow or {'offset': [0, 22], 'blur': 36, 'strength': 0.30}
        sh = dict(sh, rect=[mx, my, mx + W, my + H])
        p = E.silk_wall(name + '_table', silk, (W + 2 * mx, H + 2 * my), unit=table_unit, tex_scale=tex_scale,
                        tone=tone, light=None, shadow=sh)
        self.tlv = E.build_mips(p, name + '_table')
        self.t_origin = (-mx, -my); self.t_unit = table_unit
        self.dark = np.array(dark, np.float32)
        self.table = (-mx * 0.55, -my * 0.62, W + mx * 0.55, H + my * 0.62)   # 长案桌面范围（世界）
        self.light_front = None          # 光沿卷走：光前沿的世界 x（None = 全亮）
        # 屏幕像素网格（SS 分辨率，像素中心）
        u = (np.arange(self.WS, dtype=np.float32) + 0.5); v = (np.arange(self.HS, dtype=np.float32) + 0.5)
        self.U, self.V = np.meshgrid(u, v)

    # ---------------- 相机 ----------------
    def basis(self, cam):
        """cam: tx,ty（注视点，桌面上）, yaw（度，0=正对卷面、>0 向卷尾/左转）, pitch（度，90=正俯视）, dist, fov（竖直视角，度）"""
        ps, ys = math.radians(cam['pitch']), math.radians(cam['yaw'])
        h = np.array([-math.sin(ys), -math.cos(ys), 0.0])
        f = math.cos(ps) * h + math.sin(ps) * np.array([0, 0, 1.0])     # +z 指向桌面
        r = np.array([math.cos(ys), -math.sin(ys), 0.0])
        d = np.cross(f, r)
        C = np.array([cam['tx'], cam['ty'], 0.0]) - cam['dist'] * f
        fpx = (self.HS / 2) / math.tan(math.radians(cam['fov']) / 2)
        return r, d, f, C, fpx

    def state_for(self, cx, cy, vh, fov=34.0):
        """engine 平面相机状态 → 等价的正俯视相机。"""
        fpx = (self.HS / 2) / math.tan(math.radians(fov) / 2)
        return dict(tx=cx, ty=cy, yaw=0.0, pitch=90.0, dist=vh * fpx / self.HS, fov=fov, ox=0.0, oy=0.0)

    def fit(self, yaw, pitch, target, fov=38.0, fill=0.90, margin_world=600, bias=(0.0, 0.0)):
        """注视点固定在 target（通常 = 卷首落点），求距离与画心偏移（ox, oy，屏幕比例），
        使整卷（四角外扩 margin）投影后居中并占屏 fill。镜头绕 target 转时，target 在屏幕上只随偏移平移。"""
        W, H = self.Wsrc, self.Hsrc
        m = margin_world
        pts = [(-m, -m), (W + m, -m), (W + m, H + m), (-m, H + m)]
        c = dict(tx=float(target[0]), ty=float(target[1]), yaw=yaw, pitch=pitch, dist=W * 0.8, fov=fov, ox=0.0, oy=0.0)
        for _ in range(80):
            q, z = self.project(c, pts)
            if (z <= 0).any():
                c['dist'] *= 1.3; continue
            x0, y0 = q.min(0); x1, y1 = q.max(0)
            k = max((x1 - x0) / (self.W * fill), (y1 - y0) / (self.H * fill))
            c['dist'] *= k ** 0.7
            c['ox'] -= ((x0 + x1) / 2 / self.W - 0.5 - bias[0]) * 0.7
            c['oy'] -= ((y0 + y1) / 2 / self.H - 0.5 - bias[1]) * 0.7
        return c

    def project(self, cam, pts):
        r, d, f, C, fpx = self.basis(cam)
        P = np.c_[np.asarray(pts, float), np.zeros(len(pts))] - C
        z = P @ f
        pcx, pcy = self.WS * (0.5 + cam.get('ox', 0.0)), self.HS * (0.5 + cam.get('oy', 0.0))
        return np.c_[pcx + fpx * (P @ r) / z, pcy + fpx * (P @ d) / z] / self.SS, z

    # ---------------- 渲染 ----------------
    def _sample(self, lv, X, Y, lev, origin, unit, border):
        """按每像素 mip 级（三线性）从金字塔取色。X,Y 世界坐标；返回 float32 (HS,WS,3)。"""
        out = np.zeros(X.shape + (3,), np.float32); wsum = np.zeros(X.shape, np.float32)
        nL = len(lv)
        lev = np.clip(lev, 0, nL - 1)
        lo = int(np.floor(np.nanmin(lev))); hi = int(np.ceil(np.nanmax(lev)))
        for L in range(lo, min(hi, nL - 1) + 1):
            w = np.clip(1 - np.abs(lev - L), 0, 1)
            sel = w > 0.002
            if not sel.any():
                continue
            img = lv[L]; sc = unit * 2 ** L
            ix = (X - origin[0]) / sc - 0.5; iy = (Y - origin[1]) / sc - 0.5
            xs, ys = ix[sel], iy[sel]
            x0 = int(max(0, math.floor(xs.min()) - 2)); x1 = int(min(img.shape[1], math.ceil(xs.max()) + 3))
            y0 = int(max(0, math.floor(ys.min()) - 2)); y1 = int(min(img.shape[0], math.ceil(ys.max()) + 3))
            if border == cv2.BORDER_CONSTANT and (x1 <= x0 or y1 <= y0):
                continue
            if x1 <= x0 or y1 <= y0:     # 全在外面：反射边界取最近的一块
                x0, x1 = 0, min(img.shape[1], 64); y0, y1 = 0, min(img.shape[0], 64)
            crop = np.ascontiguousarray(img[y0:y1, x0:x1])
            mx_ = (ix - x0).astype(np.float32); my_ = (iy - y0).astype(np.float32)
            mx_[~sel] = -10; my_[~sel] = -10
            s = cv2.remap(crop, mx_, my_, cv2.INTER_LINEAR, borderMode=border).astype(np.float32)
            out += s * w[..., None]; wsum += w
        return out / np.maximum(wsum, 1e-6)[..., None]

    def render(self, cam, light=1.0):
        r, d, f, C, fpx = self.basis(cam)
        # 每像素射线（世界）
        pcx, pcy = self.WS * (0.5 + cam.get('ox', 0.0)), self.HS * (0.5 + cam.get('oy', 0.0))
        a = (self.U - pcx) / fpx; b = (self.V - pcy) / fpx
        Dx = r[0] * a + d[0] * b + f[0]; Dy = r[1] * a + d[1] * b + f[1]; Dz = r[2] * a + d[2] * b + f[2]
        hit = Dz > 1e-4
        lam = np.where(hit, -C[2] / np.maximum(Dz, 1e-4), 0).astype(np.float32)
        X = (C[0] + lam * Dx).astype(np.float32); Y = (C[1] + lam * Dy).astype(np.float32)
        # 足迹（世界像素 / SS 像素）→ mip 级：几何平均 + 0.35×各向异性
        Xx = np.gradient(X, axis=1); Xy = np.gradient(X, axis=0); Yx = np.gradient(Y, axis=1); Yy = np.gradient(Y, axis=0)
        det = np.abs(Xx * Yy - Xy * Yx) + 1e-6
        l1 = np.hypot(Xx, Yx); l2 = np.hypot(Xy, Yy)
        smax = np.maximum(l1, l2); geo = np.sqrt(det)
        lev = np.log2(np.maximum(geo, 1e-3)) + 0.35 * np.log2(np.maximum(smax / geo, 1.0))
        lev = lev + self.lod_bias
        far = ~hit | (lam > 1e9)
        lev[far] = 30
        # 卷面范围
        W, H = self.Wsrc, self.Hsrc
        inside = hit & (X >= 0) & (X < W) & (Y >= 0) & (Y < H)
        # 桌面（绢）
        levT = lev - math.log2(self.t_unit)
        tab = self._sample(self.tlv, X, Y, np.where(far, len(self.tlv) - 1, levT), self.t_origin, self.t_unit, cv2.BORDER_REFLECT)
        img = tab
        if inside.any():
            sc = self._sample(self.lv, np.where(inside, X, -9), np.where(inside, Y, -9), np.where(inside, lev, 0),
                              (0, 0), 1, cv2.BORDER_REPLICATE)
            # 卷边抗锯齿：到卷边的距离（屏幕像素）
            px = np.maximum(smax, 1e-3)
            ed = np.minimum(np.minimum(X, W - X), np.minimum(Y, H - Y)) / px
            k = np.clip(ed + 0.5, 0, 1)[..., None]
            img = img * (1 - k) + sc * k
        # 灯光：以卷为中心的光池（卷外 1200 世界像素后渐暗）+ 沿卷走的暖光
        ox = np.maximum(np.maximum(-X, X - W), 0); oy = np.maximum(np.maximum(-Y, Y - H), 0)
        dout = np.hypot(ox, oy * 1.15)
        pool = 1 - 0.70 * _sm((dout - self.pool[0]) / self.pool[1])
        lit = pool * light
        if self.light_front is not None:
            fx0, soft, base = self.light_front
            lit = lit * (base + (1 - base) * _sm((X - fx0) / soft + 0.5))
        # 长案之外（桌边以外）没入暗处：桌面是有边的实物
        tx0, ty0, tx1, ty1 = self.table
        te = np.minimum(np.minimum(X - tx0, tx1 - X), np.minimum(Y - ty0, ty1 - Y)) / np.maximum(smax, 1e-3)
        lit = lit * np.where(far, 0, np.clip(te + 0.5, 0, 1))
        img = img * lit[..., None] + self.dark * (1 - lit[..., None]) * 0.55
        # 景深方向的暖暗空气（远处没入暗处，但卷尾仍可辨）
        depth = lam * np.sqrt(a * a + b * b + 1)
        hz = 1 - np.exp(-np.maximum(depth - self.haze0, 0) / self.hazeL)
        hz = np.where(far, 1.0, hz * self.hazeA)[..., None]
        img = img * (1 - hz) + self.dark * hz
        out = cv2.resize(img, (self.W, self.H), interpolation=cv2.INTER_AREA)
        bl = cv2.GaussianBlur(out, (0, 0), 1.0)
        out = out + 0.22 * (out - bl)
        return np.clip(out + 0.5, 0, 255).astype(np.uint8)

    haze0, hazeL, hazeA = 30000.0, 60000.0, 0.62
    pool = (800.0, 2800.0)       # 卷外全亮距离、渐暗距离（世界像素）


def lerp_cam(a, b, u):
    o = {}
    for k in a:
        if k == 'dist':
            o[k] = a[k] * (b[k] / a[k]) ** u
        else:
            o[k] = a[k] + (b[k] - a[k]) * u
    return o


class OverviewShot:
    """全貌镜头：t_in 起可见（外面叠化进来）→ 贴卷面缓滑到 t_glide → 俯冲降入卷首，t_land 正好等于 land 平面状态。"""

    def __init__(self, sv, t_in, t_glide, t_land, land, start, glide_end, light_sweep=None):
        self.sv, self.t_in, self.t_glide, self.t_land = sv, t_in, t_glide, t_land
        self.A, self.B = start, glide_end
        self.Z = sv.state_for(land['cx'], land['cy'], land['vh'], fov=start['fov'])
        self.land_state = dict(land)
        self.sweep = light_sweep      # (t0, t1, soft, base)

    def cam(self, t):
        if t <= self.t_glide:
            u = _trap((t - self.t_in) / (self.t_glide - self.t_in), 0.35) if t > self.t_in else 0.0
            return lerp_cam(self.A, self.B, u)
        T = self.t_land - self.t_glide
        x = (t - self.t_glide) / T
        u = _trap(x, min(0.3, 1.6 / T))
        c = lerp_cam(self.B, self.Z, u)      # 注视点 = 落点不动；画心偏移归零 = 落点在屏幕上平稳移到中心
        # 俯仰与偏航稍晚于推近（先降下来再转正），像飞下去
        up = _trap(max(0.0, (x - 0.08) / 0.92), min(0.35, 1.6 / T))
        c['pitch'] = self.B['pitch'] + (self.Z['pitch'] - self.B['pitch']) * up
        c['yaw'] = self.B['yaw'] + (self.Z['yaw'] - self.B['yaw']) * up
        return c

    def frame(self, t):
        sv = self.sv
        if self.sweep:
            t0, t1, soft, base = self.sweep
            u = _sm5((t - t0) / (t1 - t0))
            fx0 = (sv.Wsrc + soft) + (-soft * 1.2 - sv.Wsrc - soft) * u
            sv.light_front = (fx0, soft, base) if u < 1 else None
        return sv.render(self.cam(t))


def overview_shot(sv, t_in, t_glide, t_land, land, start=None, glide_end=None, light_sweep=None,
                  start_view=(70, 26), glide_view=(54, 29), fov=38.0):
    """默认构图：站在卷首一端斜看全卷——卷首近在下方、卷尾没入远处暗中（全长可见）；
    滑行 = 以卷首落点为轴缓缓环移（偏航 72°→50°、俯仰抬高），全长始终在画内；然后俯冲、转正、降入卷首。
    start/glide_end 可直接给相机 dict（tx,ty,yaw,pitch,dist,fov,ox,oy）覆盖默认。"""
    tgt = (land['cx'], land['cy'])
    if start is None:
        start = sv.fit(yaw=start_view[0], pitch=start_view[1], target=tgt, fov=fov, fill=0.92)
    if glide_end is None:
        glide_end = sv.fit(yaw=glide_view[0], pitch=glide_view[1], target=tgt, fov=fov, fill=0.90)
    return OverviewShot(sv, t_in, t_glide, t_land, land, start, glide_end, light_sweep)


def speed_report(shot, t0, t1, fps=30, res=720):
    """屏幕中心附近画面点的逐帧位移（px/帧 @720p）：在屏幕中心 3×3 网格反投到桌面，下一帧再投回来。"""
    sv = shot.sv
    k = res / sv.H
    peak = 0.0; tpk = t0
    n = int(round((t1 - t0) * fps))
    for i in range(n):
        ta, tb = t0 + i / fps, t0 + (i + 1) / fps
        ca, cb = shot.cam(ta), shot.cam(tb)
        r, d, f, C, fpx = sv.basis(ca)
        pts = []
        for u in (-0.15, 0, 0.15):
            for v in (-0.15, 0, 0.15):
                a, b = (u - ca.get('ox', 0)) * sv.WS / fpx, (v - ca.get('oy', 0)) * sv.HS / fpx
                D = r * a + d * b + f
                if D[2] <= 1e-4:
                    continue
                lam = -C[2] / D[2]; P = C + lam * D
                pts.append(P[:2])
        pts = np.array(pts)
        qa, _ = sv.project(ca, pts); qb, _ = sv.project(cb, pts)
        m = float(np.median(np.hypot(*(qb - qa).T))) * k
        if m > peak:
            peak, tpk = m, ta
    return peak, tpk
