"""第二集·南宋 总装用的五种"作品本身"的转场（assemble.py 调用）。全部在 1280×720 画面空间里算，只用两段真实画面像素 + 遮罩。

  Liubai  s2→s3 留白：踏歌的墨按浓淡倒序退回绢里（最淡的先退、上方先退），只剩左下巨石一角；
          这一角也退去的同时，墙与空绢由踏歌过渡到寒江独钓，寒江的船与渔翁在空绢上由浓到淡显出。
  Ripple  s3→s4 涟漪变水图：沿涟漪同心椭圆向外推的"波前"经过之处，涟漪线退、洞庭风细的水纹线落墨显出。
  Surge   s4→s5 浪涌成泼墨：浪线的墨沿线洇开、越积越浓涌满全屏，再按泼墨衣袍的墨形收拢，空处的墨退回纸里。
  Crack   s5→s6 墨干成开片：墨面先干（略褪、发灰），裂纹沿开片遮罩里的真实裂纹由近及远跑开，再整体化为釉面。
  墨的模型：画面 = 底色（绢/纸/釉） × 透射（1 − 墨）。墨退、墨显、墨积都只改"墨"，底色另行过渡。
"""
import os, math, heapq
import numpy as np, cv2

f32 = np.float32
LUMW = np.float32([0.299, 0.587, 0.114])


def ss(e0, e1, t):
    if e1 <= e0: return 1.0 if t >= e1 else 0.0
    x = min(1.0, max(0.0, (t - e0) / (e1 - e0)))
    return x * x * (3 - 2 * x)


def ssa(x):
    x = np.clip(x, 0.0, 1.0); return x * x * (3 - 2 * x)


def lum(img): return img @ LUMW


def noise(h, w, sig, seed, stretch=1.0):
    rng = np.random.default_rng(seed)
    n = cv2.GaussianBlur(rng.standard_normal((h, w)).astype(f32), (0, 0), sig)
    return n / (n.std() + 1e-6)


def rank01(v, mask):
    """mask 内按 v 排序的分位（0..1），mask 外 0。"""
    q = np.zeros(v.shape, f32)
    idx = np.nonzero(mask.ravel())[0]
    order = np.argsort(v.ravel()[idx], kind='stable')
    r = np.empty(len(idx), f32); r[order] = np.linspace(0, 1, len(idx), dtype=f32)
    q.ravel()[idx] = r
    return q


def split_lh(f, sig):
    lo = cv2.GaussianBlur(f, (0, 0), sig); return lo, f - lo


def silk_weave(W, H, tex_path, amp):
    """真实绢丝纹理（北宋集 fog_texture.png）的相对起伏，std≈amp。"""
    im = cv2.imread(tex_path, cv2.IMREAD_UNCHANGED)
    g = cv2.cvtColor(im[..., :3], cv2.COLOR_BGR2GRAY).astype(f32)
    s = H * 1.10 / im.shape[0] * 0.8
    g = cv2.resize(g, None, fx=s, fy=s, interpolation=cv2.INTER_AREA)
    hp = g - cv2.GaussianBlur(g, (0, 0), 2.0)
    hp = np.hstack([hp, cv2.flip(hp, 1)])
    hp = np.vstack([hp, cv2.flip(hp, 0)])
    hp = hp[:H, :W] if hp.shape[0] >= H and hp.shape[1] >= W else cv2.resize(hp, (W, H))
    return 1.0 + amp * hp / (hp.std() + 1e-6)


def robust_silk(P, deg3=True, sig=40):
    """画心里的绢底色：亮度做稳健三次曲面拟合（墨=暗于拟合的像素降权），色度取绢像素的平滑比。"""
    h, w = P.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w].astype(f32)
    u, v = xx / w - 0.5, yy / h - 0.5
    cols = [np.ones_like(u), u, v, u * u, u * v, v * v]
    if deg3: cols += [u ** 3, v ** 3, u * u * v, u * v * v]
    basis = np.stack(cols, -1).reshape(-1, len(cols))
    L = lum(P).ravel(); wgt = np.ones_like(L)
    for _ in range(8):
        Wt = np.sqrt(wgt)[:, None]
        c, *_ = np.linalg.lstsq(basis * Wt, L * Wt[:, 0], rcond=None)
        r = L - basis @ c
        s = 1.4826 * np.median(np.abs(r[wgt > 0.5])) + 1e-3
        wgt = np.where(r < -1.0 * s, 0.02, np.where(r > 2.5 * s, 0.1, 1.0))
    fit = (basis @ c).reshape(h, w).astype(f32)
    m = (wgt.reshape(h, w) > 0.5).astype(f32)
    den = cv2.GaussianBlur(m, (0, 0), sig) + 1e-4
    Lm = cv2.GaussianBlur(lum(P) * m, (0, 0), sig) / den
    return np.stack([fit * (cv2.GaussianBlur(P[..., k] * m, (0, 0), sig) / den) / (Lm + 1e-4) for k in range(3)], -1)


# ====================================================================== 留白
class Liubai:
    def __init__(self, tr, A, B, Bblank, Awall, tex_path):
        self.tr = tr
        H, W = A.shape[:2]
        A = A.astype(f32); B = B.astype(f32); Bb = Bblank.astype(f32)
        x0, y0, x1, y1 = tr['rect']                                     # 踏歌画心（屏幕像素）
        P = A[y0:y1, x0:x1]
        bg = robust_silk(P)
        weave = silk_weave(W, H, tex_path, 0.018)
        Ab = A.copy(); Ab[y0:y1, x0:x1] = bg * weave[y0:y1, x0:x1, None]
        self.Ablank = Ab
        dA = np.zeros_like(A); dA[y0:y1, x0:x1] = 1.0 - P / np.maximum(Ab[y0:y1, x0:x1], 1.0)
        self.dA = np.clip(dA, -1.5, 0.97).astype(f32)
        kA = cv2.GaussianBlur(np.abs(lum(self.dA)), (0, 0), 0.8)
        inside = np.zeros((H, W), bool); inside[y0:y1, x0:x1] = True
        yy, xx = np.mgrid[0:H, 0:W].astype(f32)
        # 一角：左下巨石（以画心左下角为心的椭圆，边界随机起伏；墨浓处在边界上留得更久，由下面的排序自然实现）
        cx, cy, rx, ry = tr['corner']
        rho = np.sqrt(((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2) + 0.07 * noise(H, W, 14, 5)
        self.wc = wc = (1.0 - ssa((rho - 0.80) / 0.30)) * inside
        T1, T2 = tr['recede']; T3, T4 = tr['corner_recede']
        q = rank01(kA, inside)                                          # 0 = 最淡
        vpos = np.clip((yy - y0) / (y1 - y0), 0, 1)                      # 上方先退（山先退，退向一角）
        jit = 0.10 * noise(H, W, 6, 9)
        tmain = T1 + (T2 - T1) * np.clip(0.80 * q + 0.20 * vpos, 0, 1) + jit
        tcorn = T3 + (T4 - T3) * q + 0.5 * jit
        self.tr_A = (tmain * (1 - wc) + tcorn * wc).astype(f32)
        self.dA_soft = cv2.GaussianBlur(self.dA, (0, 0), 1.4)
        # 寒江：船、渔翁、竿、钓丝 = 相对空绢底板的墨；浓的先显
        dB = 1.0 - B / np.maximum(Bb, 1.0)
        self.dB = np.clip(dB, -1.0, 0.97).astype(f32)
        kB = cv2.GaussianBlur(np.abs(lum(self.dB)), (0, 0), 0.8)
        T5, T6 = tr['appear']
        mB = kB > 0.03
        qB = rank01(kB, mB)
        self.ta_B = np.where(mB, T5 + (T6 - T5) * (1.0 - qB) + 0.5 * jit, T6 + 0.2).astype(f32)
        self.dB_soft = cv2.GaussianBlur(self.dB, (0, 0), 1.4)
        self.Bb = Bb
        self.hw = tr.get('hw', 0.35)
        self.Awall = Awall.astype(f32)
        self.loA, self.hiA = split_lh(self.Awall, 2.5)
        self.loB, self.hiB = split_lh(Bb, 2.5)

    def render(self, t):
        tr = self.tr; hw = self.hw
        ws = ss(*tr['scroll_fade'], t)                                    # 空了的立轴（连同投影）隐入墙里
        g0, g1 = tr['ground']
        wg = ss(g0, g1, t)                                                # 墙面光色转到寒江那面墙，寒江的空绢显出
        wa = ss(g0, g1 - 0.25 * (g1 - g0), t); wb = ss(g0 + 0.25 * (g1 - g0), g1, t)   # 细纹略错开
        mA = (1.0 - ssa((t - (self.tr_A - hw)) / (2 * hw))) * (1.0 - ssa(ws * 1.25))   # 还剩多少墨（随立轴一起隐去）
        s = (0.75 * (1.0 - mA) * (mA > 0.001))[..., None]                # 退的途中墨略晕开（渗回绢里）
        dAt = (self.dA * (1 - s) + self.dA_soft * s) * mA[..., None]
        mB = ssa((t - (self.ta_B - hw)) / (2 * hw)) * ssa((wg - 0.2) * 1.6)     # 船的墨只落在寒江的绢上
        sb = (0.75 * (1.0 - mB) * (mB > 0.001))[..., None]                # 刚显时略晕，落定变清
        dBt = (self.dB * (1 - sb) + self.dB_soft * sb) * mB[..., None]
        if wg <= 0.0:
            G = self.Ablank * (1 - ws) + self.Awall * ws
        else:
            Gw = self.loA * (1 - wg) + self.loB * wg + self.hiA * (1 - wa) + self.hiB * wb
            G = (self.Ablank * (1 - ws) + self.Awall * ws) * (1 - wg) + Gw * wg if ws < 1.0 else Gw
            if ws < 1.0:   # 两步重叠时：立轴残余按 (1-ws) 叠在过渡中的墙上
                G = Gw + (self.Ablank - self.Awall) * (1 - ws) * (1 - wg)
        return G * (1.0 - dAt) * (1.0 - dBt)


# ====================================================================== 涟漪变水图
class Ripple:
    """波前 = 与涟漪同心、同纵横比的椭圆，由入水点向外推；经过处寒江的细节（涟漪线、绢纹、钓丝）退，
    水图洞庭风细的水纹线落墨显出（前沿处墨略浓，按水纹线遮罩）；颜色（低频）用更宽的过渡带跟着走。"""
    def __init__(self, tr, H=720, W=1280):
        self.tr = tr
        cx, cy = tr['center']; asp = tr['asp']
        yy, xx = np.mgrid[0:H, 0:W].astype(f32)
        self.rho = (np.sqrt((xx - cx) ** 2 + ((yy - cy) / asp) ** 2) + 18 * noise(H, W, 30, 23)).astype(f32)
        self.rmax = float(np.sqrt(max(cx, W - cx) ** 2 + (max(cy, H - cy) / asp) ** 2)) + 60

    def fields(self, t):
        a, b = self.tr['front']; bd, bc = self.tr['band'], self.tr['band_color']
        x = min(1.0, max(0.0, (t - a) / (b - a)))
        p = ss(0, 1, x) * 0.3 + x * 0.7                                  # 起步略缓、之后近匀速外推（像又一圈涟漪）
        r = -bd + p * (self.rmax + 2 * bd)
        rc = -bc * 0.5 + p * (self.rmax + bc)
        self.ahead = ssa((r + 1.3 * bd - self.rho) / bd + 0.5)             # 前沿外侧一个带宽内
        return ssa((r - self.rho) / bd + 0.5), ssa((rc - self.rho) / bc + 0.5)

    def render(self, t, f3, f4, m4, m3=None):
        Wd, Wc = self.fields(t)
        f3 = f3.astype(f32); f4 = f4.astype(f32)
        sg = self.tr.get('color_sigma', 36)
        c3 = cv2.GaussianBlur(f3, (0, 0), sg); c4 = cv2.GaussianBlur(f4, (0, 0), sg)
        d3 = f3 - c3; d4 = f4 - c4
        out = c3 * (1 - Wc[..., None]) + c4 * Wc[..., None] + d3 * (1 - Wd[..., None]) + d4 * Wd[..., None]
        if m3 is not None:                                                # 前沿前方那一圈涟漪线先"吃墨"变浓，随即化成水纹
            lead = self.ahead * (1 - Wd)
            R = np.clip(m3.astype(f32) / (255.0 * self.tr.get('m3_peak', 0.8)), 0, 1)
            out = out * (1.0 - self.tr.get('lead', 0.25) * (lead * R))[..., None]
        if m4 is not None:                                                # 前沿处水纹线墨色略浓（新落的墨）
            L = m4.astype(f32) / 255.0
            out = out * (1.0 - self.tr.get('fresh', 0.30) * (4 * Wd * (1 - Wd) * L))[..., None]
        return out


# ====================================================================== 浪涌成泼墨
def ground_of(f, k=31, sig=26):
    """底色（绢/纸）：亮度上包络——膨胀取局部最亮，再平滑。"""
    g = cv2.dilate(f, np.ones((k, k), np.uint8))
    return cv2.GaussianBlur(g, (0, 0), sig) * 0.985 + 1.0


class Surge:
    """墨 = 1 − 画面/底色。黄河浪线的墨先沿线洇开、层层积浓（涌满全屏），再按泼墨衣袍的墨形收拢：
    衣袍处墨留下并换成泼墨的墨质，空处的墨由淡到浓次第退回纸里；底色由绢灰转纸黄。"""
    def __init__(self, tr, f5_still):
        self.tr = tr
        f5 = f5_still.astype(f32)
        G5 = ground_of(f5); D5 = 1.0 - lum(f5) / lum(G5)
        H, W = D5.shape
        Ds = cv2.GaussianBlur(np.clip(D5, 0, 1), (0, 0), tr.get('settle_sigma', 10))
        hi = float(np.percentile(Ds, 97))
        q = np.clip(Ds / max(hi, 1e-3), 0, 1) ** 0.8                      # 纸处≈0 同时开始清，越近衣袍墨芯越晚定（边界顺着墨形收拢）
        a, b = tr['settle']
        self.tset = (a + (b - a) * q + 0.06 * noise(H, W, 40, 31)).astype(f32)

    def render(self, t, f4, f5):
        tr = self.tr
        f4 = f4.astype(f32); f5 = f5.astype(f32)
        G4 = ground_of(f4); G5 = ground_of(f5)
        D4 = np.clip(1.0 - f4 / G4, -0.6, 0.985); D5 = np.clip(1.0 - f5 / G5, -0.6, 0.985)
        # 1) 积墨：浪线加浓（同一笔墨叠 k 遍）+ 沿线洇开（按线的密度成片）
        ka = ss(*tr['accum'], t)
        k = 1.0 + tr['k_max'] * ka
        sig = 2.0 + tr['bleed_sigma'] * ka
        Dl = np.clip(lum(D4), 0, 1)
        B = cv2.GaussianBlur(Dl, (0, 0), sig)
        B = B / (B.max() * 0.55 + 1e-4)
        wash = np.clip(tr['wash_max'] * ka * B, 0, 0.9)[..., None]
        T4 = np.clip(1.0 - D4, 0.015, None) ** k * (1.0 - wash)
        I4 = 1.0 - T4
        # 2) 收拢：逐像素由积满的浪墨过渡到泼墨（纸处先清、浓处最后定）
        hw = tr.get('hw', 0.55)
        w = ssa((t - (self.tset - hw)) / (2 * hw))[..., None]
        s = (0.4 * 4 * w * (1 - w))                                       # 过渡途中墨略晕（湿）
        I5 = D5 * (1 - s) + cv2.GaussianBlur(D5, (0, 0), 2.0) * s
        I = I4 * (1 - w) + I5 * w
        wg = ss(*tr['ground'], t)
        G = G4 * (1 - wg) + G5 * wg
        return G * (1.0 - I)


# ====================================================================== 墨干成开片
def crack_arrival(mask, center, v_front, v_crack, thr=0.25, seed=41):
    """裂纹到达时间（秒，相对起点）：遮罩线上的像素；由 center 向外的前沿先点着每条裂纹离前沿最近处，
    再沿裂纹（8 邻域）以 v_crack 跑开。线外 = inf。"""
    H, W = mask.shape
    on = mask > thr
    yy, xx = np.mgrid[0:H, 0:W].astype(f32)
    cx, cy = center
    rng = np.random.default_rng(seed)
    t0 = np.sqrt((xx - cx) ** 2 + ((yy - cy) / 0.8) ** 2) / v_front + 0.12 * noise(H, W, 25, seed)
    t0 = t0 + 0.9 * (1 - on)                                             # 只在线上点火
    T = np.full((H, W), np.inf, np.float64)
    idx = np.flatnonzero(on)
    # 每条裂纹只从少数点点火：先按 t0 排序，逐点 Dijkstra 松弛（线像素很少，纯 Python 可接受）
    T.ravel()[idx] = t0.ravel()[idx]
    heap = [(T.ravel()[i], i) for i in idx]; heapq.heapify(heap)
    step = [(-1, -1, 1.414), (-1, 0, 1), (-1, 1, 1.414), (0, -1, 1), (0, 1, 1), (1, -1, 1.414), (1, 0, 1), (1, 1, 1.414)]
    onf = on.ravel(); Tf = T.ravel()
    while heap:
        tv, i = heapq.heappop(heap)
        if tv > Tf[i]: continue
        y, x = divmod(i, W)
        for dy, dx, c in step:
            yy2, xx2 = y + dy, x + dx
            if 0 <= yy2 < H and 0 <= xx2 < W:
                j = yy2 * W + xx2
                if onf[j]:
                    nt = tv + c / v_crack
                    if nt < Tf[j]:
                        Tf[j] = nt; heapq.heappush(heap, (nt, j))
    return T.astype(f32)


def _line_kernel(theta, s_al=6.0, s_ac=0.9, s_bg=2.6, r=15):
    y, x = np.mgrid[-r:r + 1, -r:r + 1].astype(f32)
    c, s_ = np.cos(theta), np.sin(theta)
    u = c * x + s_ * y; v = -s_ * x + c * y
    g1 = np.exp(-u * u / (2 * s_al ** 2) - v * v / (2 * s_ac ** 2)); g1 /= g1.sum()
    g2 = np.exp(-u * u / (2 * s_al ** 2) - v * v / (2 * s_bg ** 2)); g2 /= g2.sum()
    return (g2 - g1).astype(f32)                     # 暗细线 → 正响应


def crack_net(f6, lo_q=88.0, hi_q=95.5, min_len=40):
    """从官窑微距照片本身找真实开片线（12 个方向的细线滤波取最大 + 滞后阈值 + 去短碎段 + 去点状黑斑）。"""
    L = cv2.GaussianBlur(f6.astype(f32) @ np.float32([.2, .4, .4]), (0, 0), 0.6)
    L = L / cv2.GaussianBlur(L, (0, 0), 20)
    resp = np.max([cv2.filter2D(L, -1, _line_kernel(th)) for th in np.linspace(0, np.pi, 12, endpoint=False)], 0)
    g1 = cv2.GaussianBlur(L, (0, 0), 0.9); g2 = cv2.GaussianBlur(L, (0, 0), 2.6)
    iso = g2 - g1                                    # 各向同性：点状黑斑与线一样亮，线的方向响应远大于它
    lo, hi = np.percentile(resp, [lo_q, hi_q])
    dot = cv2.dilate(((iso > 0.9 * resp) & (iso > lo)).astype(np.uint8), np.ones((5, 5), np.uint8)) > 0
    weak = ((resp > lo) & ~dot).astype(np.uint8); strong = (resp > hi) & ~dot
    n, lab, st, _ = cv2.connectedComponentsWithStats(weak, 8)
    keep = np.zeros(n, bool); keep[np.unique(lab[strong])] = True; keep[0] = False
    keep &= np.maximum(st[:, cv2.CC_STAT_WIDTH], st[:, cv2.CC_STAT_HEIGHT]) >= min_len
    return (np.clip((resp - lo) / (hi - lo), 0, 1) * keep[lab]).astype(f32)


class Crack:
    """泼墨的墨面先"干"（略褪、转灰），随后裂纹沿官窑釉面的真实开片线由近及远跑开：墨处裂开露出纸色，
    纸处是一道发丝暗线，都带一点深度阴影；最后墨面（低频先、细节后）化为釉面，裂纹网与 s6 的开片逐像素重合。
    开片线 = s6 开片遮罩 ∪ 从同一张微距照片找出的细线（遮罩较保守，只用它网不成网）。"""
    def __init__(self, tr, f6_still, m6_still):
        self.tr = tr
        m = m6_still.astype(f32) / 255.0
        m = np.clip(m / max(float(m.max()), 1e-3), 0, 1)
        net = np.maximum(crack_net(f6_still), m)
        self.m = net
        arr = crack_arrival(net, tr['center'], tr['v_front'], tr['v_crack'], thr=0.2)
        a, b = tr['crack']
        fin = np.isfinite(arr)
        arr[fin] = a + (b - a) * arr[fin] / max(float(np.percentile(arr[fin], 99)), 1e-3)
        arr[~fin] = b + 5.0
        self.arr = np.minimum(arr, b + 5.0).astype(f32)
        self.md = np.clip(cv2.GaussianBlur(cv2.dilate(net, np.ones((2, 2), np.uint8)), (0, 0), 0.6) * 1.25, 0, 1)

    def render(self, t, f5, f6):
        tr = self.tr
        f5 = f5.astype(f32); f6 = f6.astype(f32)
        G5 = ground_of(f5)
        D = 1.0 - f5 / G5
        ink = np.clip(lum(D), 0, 1)
        dry = ss(*tr['dry'], t)
        if dry > 0:                                                       # 墨干：略褪、偏灰
            gray = ink[..., None]
            D = (D * (1 - 0.35 * dry) + gray * 0.35 * dry) * (1 - 0.12 * dry)
            f5 = G5 * (1.0 - D)
        # 裂开（到达后 0.15 s 张开）
        ca = self.md * ssa((t - self.arr) / 0.15 + 0.5)
        if ca.max() > 0:
            inkw = ssa(ink / 0.22)[..., None]
            col = (G5 * 1.02) * inkw + (f5 * 0.62) * (1 - inkw)             # 墨处露纸、纸处发丝暗线
            sh = np.roll(np.roll(ca, 2, 0), 1, 1) * (1 - ca)                # 右下 1 px 深度阴影
            f5 = f5 * (1 - 0.30 * sh)[..., None]
            f5 = f5 * (1 - ca[..., None]) + col * ca[..., None]
        # 釉化：低频先、细节后
        wl = ss(*tr['glaze_lo'], t); wd = ss(*tr['glaze_hi'], t)
        if wl <= 0 and wd <= 0: return f5
        lo5, d5 = split_lh(f5, 14.0); lo6, d6 = split_lh(f6, 14.0)
        return lo5 * (1 - wl) + lo6 * wl + d5 * (1 - wd) + d6 * wd
