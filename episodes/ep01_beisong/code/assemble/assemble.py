"""北宋试做章节总装：各段按全局时间码拼接 + 五处转场 + 字幕烧入 + 配乐铺底。可重跑、参数化。

用法（在 series/assemble/ 下）：
  python3 assemble.py subs                       # 只写 out/subs.srt
  python3 assemble.py audio                      # 只做配乐 work/music_mix.wav 并报告分区响度/峰值
  python3 assemble.py peek 20.5 99 170 ...       # 渲指定全局秒的帧 -> peek/at_XXX.jpg + peek/sheet.jpg
  python3 assemble.py video --t0 16 --t1 26 --height 480 --out test.mp4 --fast   # 短测试
  python3 assemble.py fogcheck [3]               # 两处雾转场每 3 帧查"雾不平涂"（雾区 24×24 块去绢纹后 std<1.2 的比例 ≤25%）
  lockf -k ../.heavy.lock python3 assemble.py video --out ../out/pilot_beisong_draft.mp4   # 整片
通用参数：--s4 / --s4mask 指定千里江山段与其水面遮罩（缺省自动：v2 存在用 v2，否则 v1 占位 + seg_s3 遮罩近似）。
配音版（v3 起）：--audio 指定外部音轨（缺省 work/music_mix.wav 纯配乐），--srt 指定烧入的字幕文件（缺省用下面 SUB_ANCHORS
  生成的锚点字幕）。配音、按语音对时的字幕由 ../voice/build_voice.py 生成：out/audio/mix.wav、out/subs.srt。
  lockf -k ../.heavy.lock python3 assemble.py video --audio ../out/audio/mix.wav --srt ../out/subs.srt --out ../out/pilot_beisong_v3.mp4
1080p 终版（v3_1080 起）：--res 1080 → 各段与水面遮罩读 segs_1080/（1920×1080 原生渲染），输出 1920×1080，
  字幕字号、雾纹理、遮罩模糊、转场坐标都按 H/720 比例放大（720 参考坐标不变），AAC 缺省 256k。
  segs_1080/ 缺某段时临时用 segs/ 的 720 段放大顶上（打印 WARN，只供短测试）；--strict 时缺段直接报错。
  nohup lockf -k ../.heavy.lock work/final_v3_1080.sh > work/final_v3_1080.log 2>&1 &
注意：out/subs.srt 现在归配音流水线所有；本脚本的锚点字幕只写 work/subs_anchor.srt（配乐压低区仍按锚点字幕算）。
"""
import argparse, json, os, re, subprocess, sys, math
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
SER = os.path.dirname(HERE)
SEGS = os.path.join(SER, 'segs')                  # 共用素材（fog_texture.png）与 720 段
SEGS_BY_RES = {720: SEGS, 1080: os.path.join(SER, 'segs_1080')}
SEG_NFR = {'seg_s01.mp4': 660, 'seg_s2.mp4': 2610, 'seg_s3.mp4': 2370, 'seg_s4.mp4': 2250, 'seg_s5.mp4': 1860,
           'seg_s6.mp4': 450, 'seg_s3_water_mask.mp4': 2370, 'seg_s4_water_mask.mp4': 2250}
OUT = os.path.join(SER, 'out')
WORK = os.path.join(HERE, 'work')
PEEK = os.path.join(HERE, 'peek')
FONT = os.path.join(SER, '..', 'trailer', 'fonts', 'SourceHanSerifSC-Regular.otf')
BED = os.path.join(SER, 'music', 'bed_pilot.wav')
FPS = 30
DUR = 292.0                      # 4:52，音画同长
NFR = int(round(DUR * FPS))

# ---------------------------------------------------------------- 时间线（全局秒）
SEG_START = {'s01': 0, 's2': 19, 's3': 97, 's4': 167, 's5': 230, 's6': 277}
SEG_FILE = {'s01': 'seg_s01.mp4', 's2': 'seg_s2.mp4', 's3': 'seg_s3.mp4', 's5': 'seg_s5.mp4', 's6': 'seg_s6.mp4'}

# 转场。fog：cover 雾起吞没 → swap 换段（雾全覆盖时）→ reveal 雾散露出。
TRANS = [
    dict(kind='fog', src='s01', dst='s2', cover=(18.2, 20.9), swap=21.15, reveal=(21.4, 24.4),
         cover_mode='rise', reveal_mode='peak', xc=640, yc=462),
    dict(kind='fog', src='s2', dst='s3', cover=(97.0, 100.7), swap=100.95, reveal=(101.2, 104.9),
         cover_mode='spread', reveal_mode='sink', xc=640, yc=462, push=0.025),
    # 水接水：先在两段共同水面里细波互换(detail)、再换水色(low)，最后全屏(full)
    dict(kind='water', src='s3', dst='s4', detail=(168.0, 171.8), low=(169.0, 173.2), full=(170.8, 174.4)),
    # 满屏石青→满屏天青（同色系叠化）：S4 推到石青铺满整屏（约 236.5 起）后，在 S5 段内"融釉"的同时叠入——
    # S4 的矿物颗粒先化开(detail)，颜色随后由石青转天青(low)；S5 开头那张石青底图里的几粒墨点在叠化期间提亮抹掉(lift)
    dict(kind='glaze', src='s4', dst='s5', low=(238.5, 240.0), detail=(238.3, 239.7), lift=(238.2, 240.2, 240.9)),
    # 全器淡为绢底
    dict(kind='fade', src='s5', dst='s6', span=(277.3, 280.3)),
]
for tr in TRANS:
    ks = [v for k, v in tr.items() if isinstance(v, tuple)]
    tr['a'] = min(v[0] for v in ks); tr['b'] = max(v[-1] for v in ks)

# ---------------------------------------------------------------- 字幕（分镜原文 + beats.json 锚点，全局秒）
SUB_ANCHORS = [
    (10, '五代的画里 人是主角 占满了整个画面'),
    (16, '到了北宋 人退到了山脚下'),
    (24, '北宋的画家 把一整座山 搬进了一幅绢里'),
    (29, '这是范宽的《谿山行旅图》'),
    (35, '山脚下 一队驮着货物的驴子正走出树林'),
    (41, '人在山前 不过一粒芝麻'),
    (59, '主峰顶天立地 扑面而来'),
    (64, '范宽用密密的墨点 一层层积出山石的坚硬'),
    (70, '后人叫它 雨点皴'),
    (76, '范宽说 与其学前人 不如学山水本身'),
    (81, '与其学山水 不如学自己的心'),
    (85, '他把名字藏在树叶间 直到一九五八年才被人发现'),
    (100, '同一个时代 另一位画家把目光投向了人间'),
    (107, '《清明上河图》 长五米多'),
    (111, '画了五百多个人'),
    (115, '手卷要从右往左 一段一段展开来看'),
    (122, '郊外的小路上 驴队驮着货物进城'),
    (130, '汴河上 船一艘接一艘'),
    (140, '虹桥下 一艘大船正放倒桅杆 要穿过桥洞'),
    (148, '船上的人忙作一团 桥上的人探出身子围观'),
    (161, '小到店铺招牌上的字 都画得清清楚楚'),
    (171, '水墨淡彩之外 北宋宫廷里还开出了一片青绿'),
    (177, '《千里江山图》 长近十二米'),
    (184, '画它的王希孟 只有十八岁'),
    (190, '据卷后蔡京的题跋 他得到宋徽宗亲自指点'),
    (197, '不到半年 便画成了这卷江山'),
    (216, '山头的蓝和绿 是磨碎的矿石'),
    (222, '石青 石绿 一层层罩染在绢上 九百年后依然鲜亮'),
    (235, '这种青 也被宋人烧进了瓷里'),
    (244, '汝窑青瓷水仙盆'),
    (248, '通身没有一笔花纹 美全在釉色本身'),
    (255, '釉薄的口沿 透出淡淡的粉'),
    (261, '釉厚的地方 积成一抹淡碧'),
    (267, '底下六个芝麻大的支钉痕 是烧制时托住它的地方'),
    (275, '汝窑存世不足百件 这一件连一道开片都没有'),
    (282, '北宋人想看见的 是事物本来的样子'),
]
MAXCH, MIN_D, MAX_D, GAP = 16, 3.0, 6.5, 0.25


def nch(s): return len(s.replace(' ', ''))
def want(s): return min(MAX_D, max(MIN_D, nch(s) / 3.5 + 1.0))   # 约 3.5 字/秒 + 1 s


def build_cues():
    cues = []
    for i, (st, tx) in enumerate(SUB_ANCHORS):
        nxt = SUB_ANCHORS[i + 1][0] if i + 1 < len(SUB_ANCHORS) else DUR - 1.0
        room = nxt - GAP - st
        parts = [tx]
        if nch(tx) > MAXCH:                                  # 超 16 字在最居中的空格处拆两条（两条都要能 ≥3 s）
            sp = [k for k, c in enumerate(tx) if c == ' ']
            k = min(sp, key=lambda k: abs(nch(tx[:k]) - nch(tx[k + 1:])))
            a, b = tx[:k], tx[k + 1:]
            if room >= 2 * MIN_D + 0.1:
                parts = [a, b]
        t = st
        for j, p in enumerate(parts):
            d = want(p)
            if j == 0 and len(parts) == 2:
                d = min(d, room - 0.1 - MIN_D)
            end = min(t + d, nxt - GAP)
            cues.append((t, end, p))
            t = end + 0.1
    return cues


def fmt_ts(t):
    ms = int(round(t * 1000)); h, ms = divmod(ms, 3600000); m, ms = divmod(ms, 60000); s, ms = divmod(ms, 1000)
    return f'{h:02d}:{m:02d}:{s:02d},{ms:03d}'


def read_srt(path):
    """读 SRT → [(起, 止, 文本)]（全局秒）。"""
    cues = []
    for blk in re.split(r'\n\s*\n', open(path, encoding='utf-8').read().strip()):
        ln = blk.strip().splitlines()
        m = re.match(r'(\d+):(\d+):(\d+),(\d+)\s*-->\s*(\d+):(\d+):(\d+),(\d+)', ln[1])
        g = [int(x) for x in m.groups()]
        a = g[0] * 3600 + g[1] * 60 + g[2] + g[3] / 1000; b = g[4] * 3600 + g[5] * 60 + g[6] + g[7] / 1000
        cues.append((a, b, ' '.join(ln[2:])))
    return cues


def write_srt(cues, path):
    with open(path, 'w', encoding='utf-8') as f:
        for i, (a, b, t) in enumerate(cues, 1):
            f.write(f'{i}\n{fmt_ts(a)} --> {fmt_ts(b)}\n{t}\n\n')


# ---------------------------------------------------------------- 配乐
DUCK, BREATH = -26.0, -20.0
MERGE_GAP = 6.5          # 字幕间隙小于此不回升（免抽吸）
RAMP = 2.0               # 目标电平缓变时长（再经 2 s 平滑，实际 >3 s）


def bed_momentary():
    """ffmpeg ebur128 逐 0.1 s 的 M 值（缓存）。"""
    cache = os.path.join(WORK, 'bed_M.npy')
    if os.path.exists(cache) and os.path.getmtime(cache) > os.path.getmtime(BED):
        return np.load(cache)
    txt = os.path.join(WORK, 'bed_M.txt')
    subprocess.run(['ffmpeg', '-v', 'error', '-i', BED, '-af',
                    f'ebur128=metadata=1,ametadata=print:key=lavfi.r128.M:file={txt}', '-f', 'null', '-'], check=True)
    m = [float(l.split('=')[1]) for l in open(txt) if 'lavfi.r128.M' in l]
    arr = np.array(m, np.float64); np.save(cache, arr); return arr


def duck_zones(cues):
    z = []
    for a, b, _ in cues:
        if z and a - z[-1][1] < MERGE_GAP: z[-1][1] = max(z[-1][1], b)
        else: z.append([a, b])
    return z


def target_curve(tt, zones):
    """每 0.1 s 的目标响度：字幕区 DUCK，其余 BREATH；降在字幕开始前完成，升在字幕结束后开始。"""
    T = np.full_like(tt, BREATH)
    for a, b in zones:
        lo, hi = a - RAMP - 1.0, b + RAMP                      # 降：a-3..a-1（平滑后在 a 前压到位）；升：b..b+2
        for i, t in enumerate(tt):
            if lo <= t <= hi:
                if t < a - 1.0: w = 0.5 - 0.5 * math.cos(math.pi * (t - lo) / RAMP)
                elif t <= b: w = 1.0
                else: w = 0.5 + 0.5 * math.cos(math.pi * (t - b) / RAMP)
                T[i] = min(T[i], BREATH + (DUCK - BREATH) * w)
    return T


def energy_db(x): return 10 * np.log10(np.maximum(np.mean(10 ** (x / 10)), 1e-12))


def build_audio(cues, report=True):
    os.makedirs(WORK, exist_ok=True)
    M = bed_momentary()                                   # 0.1 s 步长
    tt = np.arange(len(M)) * 0.1
    zones = duck_zones(cues)
    T = target_curve(tt, zones)
    # 慢速电平跟随：8 s 能量窗的短时响度 Ls；输出 ≈ 目标 + 0.5×(Ls − 区段均值)，保留一半乐句起伏
    e = 10 ** (np.maximum(M, -70) / 10)
    k = np.hanning(81); k /= k.sum()
    Ls = 10 * np.log10(np.convolve(e, k, mode='same') + 1e-12)
    lo_f, hi_f = int(5 / 0.1), int(285 / 0.1)          # 片头淡入/片尾淡出不跟随（保留原曲淡入淡出形状）
    Ls[:lo_f] = Ls[lo_f]; Ls[hi_f:] = Ls[hi_f]
    # 区段划分（按目标值）
    seg_id = np.zeros(len(tt), int); cur = 0
    for i in range(1, len(tt)):
        if (T[i] <= (DUCK + BREATH) / 2) != (T[i - 1] <= (DUCK + BREATH) / 2): cur += 1
        seg_id[i] = cur
    Lz = np.zeros(len(tt))
    for s in np.unique(seg_id):
        msk = seg_id == s; Lz[msk] = energy_db(Ls[msk])
    G = T - (0.5 * Ls + 0.5 * Lz)
    G = np.clip(G, -12, 18)
    # 两轮校正：实测各区积分响度，微调偏移
    corr = np.zeros(len(tt))
    for _ in range(2):
        Gs = smooth(np.minimum(G + corr, 18.0), 20)
        out_M = M + Gs                                   # 近似：增益缓变，M 线性可加
        for s in np.unique(seg_id):
            msk = (seg_id == s) & (M > -60)
            tgt = T[seg_id == s].min() if T[seg_id == s].min() <= DUCK + 0.5 else BREATH
            core = msk & (np.abs(T - tgt) < 0.2)
            if core.sum() < 10: continue
            corr[seg_id == s] += tgt - gated(out_M[core])
    Gs = smooth(np.minimum(G + corr, 18.0), 20)            # 总增益上限 +18 dB（安静乐段不硬拉）
    np.save(os.path.join(WORK, 'gain_db.npy'), Gs)
    # 施加增益
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', BED, '-f', 'f32le', '-ac', '2', '-ar', '48000', '-'],
                         capture_output=True, check=True).stdout
    x = np.frombuffer(raw, np.float32).reshape(-1, 2).copy(); del raw
    n = int(DUR * 48000)
    if len(x) < n: x = np.vstack([x, np.zeros((n - len(x), 2), np.float32)])
    x = x[:n]
    ts = (np.arange(n) / 48000.0)
    g = 10 ** (np.interp(ts, tt, Gs) / 20).astype(np.float32); del ts
    x *= g[:, None]; del g
    over = np.abs(x) > 0.84
    print(f'限幅前：样本峰值 {20*np.log10(np.abs(x).max()):.1f} dBFS，超 −1.5 dBFS 的样本 {over.sum()} 个'
          f'（涉及 {len(np.unique(np.nonzero(over)[0] // 4800))} 个 0.1 s 窗）')
    tmp = os.path.join(WORK, 'music_pre.wav'); out = os.path.join(WORK, 'music_mix.wav')
    p = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'f32le', '-ar', '48000', '-ac', '2', '-i', '-',
                          '-c:a', 'pcm_f32le', tmp], stdin=subprocess.PIPE)
    p.stdin.write(x.tobytes()); p.stdin.close(); p.wait(); del x
    # 真峰值保险：限幅到 −1.5 dBFS（4× 过采样），再实测
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', tmp, '-af',
                    'aresample=192000,alimiter=limit=0.84:attack=5:release=80:level=false,aresample=48000',
                    '-c:a', 'pcm_s24le', out], check=True)
    os.remove(tmp)
    if report: audio_report(out, zones)
    return out


def smooth(x, half):
    k = np.ones(2 * half + 1) / (2 * half + 1)
    xp = np.pad(x, half, mode='edge')
    return np.convolve(xp, k, mode='valid')


def gated(m):
    m = m[m > -70]
    if len(m) == 0: return -70
    L = energy_db(m); m2 = m[m > L - 10]
    return energy_db(m2) if len(m2) else L


def audio_report(path, zones):
    txt = os.path.join(WORK, 'mix_M.txt')
    r = subprocess.run(['ffmpeg', '-nostats', '-i', path, '-af',
                        f'ebur128=metadata=1:peak=true,ametadata=print:key=lavfi.r128.M:file={txt}', '-f', 'null', '-'],
                       capture_output=True, text=True).stderr
    I = re.findall(r'I:\s+(-?[\d.]+) LUFS', r)[-1]; TP = re.findall(r'Peak:\s+(-?[\d.]+) dBFS', r)[-1]
    M = np.array([float(l.split('=')[1]) for l in open(txt) if 'lavfi.r128.M' in l])
    tt = np.arange(len(M)) * 0.1
    dur = float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', path],
                               capture_output=True, text=True).stdout)
    print(f'music_mix: 时长 {dur:.3f}s  积分 {I} LUFS  真峰值 {TP} dBTP')
    edges = [0.0]
    for a, b in zones: edges += [a, b]
    edges.append(DUR)
    for i in range(len(edges) - 1):
        a, b = edges[i], edges[i + 1]
        kind = '字幕' if i % 2 == 1 else '呼吸'
        ia, ib = (a + 2.5, b - 0.5) if kind == '呼吸' else (a, b)
        if kind == '呼吸' and (i == 0): ia = 3.0
        msk = (tt >= ia) & (tt < ib)
        if msk.sum() < 10: continue
        print(f'  {kind} {a:6.1f}-{b:6.1f}s  积分≈{gated(M[msk]):6.1f} LUFS')


# ---------------------------------------------------------------- 视频读取
class Reader:
    def __init__(self, path, W, H, gray=False):
        self.path, self.W, self.H, self.gray = path, W, H, gray
        self.n = int(subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-count_packets',
                                     '-show_entries', 'stream=nb_read_packets', '-of', 'csv=p=0', path],
                                    capture_output=True, text=True).stdout.strip())
        self.proc = None; self.nxt = None; self.last = (None, None)
        self.bpf = W * H * (1 if gray else 3)
        wh = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=width,height',
                             '-of', 'csv=p=0', path], capture_output=True, text=True).stdout.strip().split(',')
        self.src_wh = (int(wh[0]), int(wh[1]))
        up = self.src_wh[1] < H
        self.vf = 'null' if self.src_wh == (W, H) else f'scale={W}:{H}:flags={"lanczos" if up else "area"}'

    def _open(self, idx):
        self.close()
        vf = self.vf
        self.proc = subprocess.Popen(['ffmpeg', '-v', 'error', '-ss', f'{idx / FPS:.6f}', '-i', self.path, '-vf', vf,
                                      '-f', 'rawvideo', '-pix_fmt', 'gray' if self.gray else 'rgb24', '-'],
                                     stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, bufsize=self.bpf * 2)
        self.nxt = idx

    def get(self, idx):
        idx = max(0, min(self.n - 1, idx))
        if self.last[0] == idx: return self.last[1]
        if self.proc is None or idx < self.nxt or idx > self.nxt + 90: self._open(idx)
        while True:
            b = self.proc.stdout.read(self.bpf)
            if len(b) < self.bpf:               # 意外读尽：退回上一帧
                return self.last[1]
            fr = np.frombuffer(b, np.uint8).reshape(self.H, self.W, *([] if self.gray else [3]))
            self.nxt += 1
            if self.nxt - 1 == idx:
                self.last = (idx, fr); return fr

    def close(self):
        if self.proc:
            self.proc.stdout.close(); self.proc.kill(); self.proc.wait(); self.proc = None


def ss(e0, e1, t):
    """smoothstep 缓入缓出"""
    if e1 <= e0: return 1.0 if t >= e1 else 0.0
    x = min(1.0, max(0.0, (t - e0) / (e1 - e0)))
    return x * x * (3 - 2 * x)


def ssa(x):
    x = np.clip(x, 0.0, 1.0); return x * x * (3 - 2 * x)


# ---------------------------------------------------------------- 雾 v2：多层体积烟云，镜头穿行
# 每层 = 一张横向拉长的烟云密度场（多尺度噪声 + 域扭曲），随时间"翻卷"（扭曲场自己在走）；
# 层有深度：镜头前进时近层放大得快、横漂得快（视差），最近一层从镜头旁掠过；
# 受光：密度场上沿亮、下沿压一层淡墨（宋画烘染云的明暗），所以雾有体积，任何一帧都不是平涂；
# 材质：fog_texture.png 的真实绢丝纹理（只取相对起伏）；颜色取两段画面的亮部绢色。
# 雾里"深色先透"：画里的墨（山、树）比淡绢更早从薄雾里透出来、更晚被吞没（空气透视）。
FOG_Q = 2                                            # 雾场在 1/2 分辨率里算，再放大（雾本身是低频）
FOG_LAYERS = [                                       # 由远及近。zr 镜头前进时每秒放大率；vx/vy 横漂 px/s（720p）
    dict(zr=0.025, vx=8, vy=-4, stretch=2.6, sig=(44, 22, 10, 4), cap=1.00, tint=0.12, seed=11),
    dict(zr=0.060, vx=-14, vy=-7, stretch=2.4, sig=(54, 26, 12, 5), cap=0.92, tint=0.06, seed=23),
    dict(zr=0.120, vx=20, vy=-11, stretch=2.2, sig=(64, 30, 14, 5), cap=0.88, tint=0.0, seed=37),
    dict(zr=0.240, vx=-27, vy=-15, stretch=2.0, sig=(76, 36, 16, 6), cap=0.70, tint=0.0, seed=41),
]
FOG_WHITE = np.float32([241, 234, 219])             # 绢上留白的云色（和画面亮部绢色混合）
FOG_INK = np.float32([58, 50, 42])                   # 暗部淡墨


def _fbm(rng, h, w, sig, stretch, amps=(1.0, 0.48, 0.2, 0.1)):
    """横向拉长的多尺度噪声，std≈1"""
    acc = np.zeros((h, w), np.float32)
    ws = max(16, int(round(w / stretch)))
    for s, a in zip(sig, amps):
        n = cv2.GaussianBlur(rng.standard_normal((h, ws)).astype(np.float32), (0, 0), s / math.sqrt(stretch))
        n = cv2.resize(n, (w, h), interpolation=cv2.INTER_CUBIC)
        acc += a * n / (n.std() + 1e-6)
    return acc / (acc.std() + 1e-6)


class Fog:
    """雾的共用材质（真实绢丝纹理）与各层密度图集（1/2 分辨率，约 2.4 倍画面大，边界镜像）。"""
    def __init__(self, W, H):
        im = cv2.imread(os.path.join(SEGS, 'fog_texture.png'), cv2.IMREAD_UNCHANGED)
        rgb = cv2.cvtColor(im[..., :3], cv2.COLOR_BGR2RGB).astype(np.float32)
        s = H * 1.10 / im.shape[0]
        lum = cv2.cvtColor(rgb[:, :1290], cv2.COLOR_RGB2GRAY)
        lum = cv2.resize(cv2.GaussianBlur(lum, (0, 0), 0.5), None, fx=s, fy=s, interpolation=cv2.INTER_AREA)
        lo = cv2.GaussianBlur(lum, (0, 0), 2.5 * s / 0.72)                  # 只留丝线级纹理（单色）
        wv = np.clip(1.0 + 0.45 * (lum / np.maximum(lo, 1.0) - 1.0), 0.93, 1.07).astype(np.float32)
        for ax in (1, 0):                                                   # 去掉贯穿全幅的直线（折痕/粗纬线）
            m = wv.mean(axis=ax); hp = m - cv2.GaussianBlur(m.reshape(-1, 1), (0, 0), 6).ravel()
            hp = np.where(np.abs(hp) > 2.0 * hp.std(), hp, 0.0).astype(np.float32)
            wv = wv - (hp[:, None] if ax == 1 else hp[None, :])
        wv = np.hstack([wv, cv2.flip(wv, 1)])
        oy, ox = max(0, (wv.shape[0] - H) // 2), max(0, (wv.shape[1] - W) // 2)
        self.weave = np.ascontiguousarray(wv[oy:oy + H, ox:ox + W])[..., None]
        self.W, self.H = W, H
        q = FOG_Q; self.hq, self.wq = H // q, W // q
        sc = H / 720.0; self.sc = sc
        ah, aw = int(self.hq * 2.4), int(self.wq * 2.4)
        self.atlas = []
        for L in FOG_LAYERS:
            rng = np.random.default_rng(L['seed'])
            sig = [x * sc * 2 / q for x in L['sig']]
            d = _fbm(rng, ah, aw, sig, L['stretch'])
            w1 = _fbm(rng, ah, aw, (sig[0] * 1.3, sig[1]), 1.6, (1.0, 0.4))  # 域扭曲场（翻卷）
            w2 = _fbm(rng, ah, aw, (sig[0] * 1.3, sig[1]), 1.6, (1.0, 0.4))
            yy, xx = np.mgrid[0:ah, 0:aw].astype(np.float32)
            A = 26 * sc * 2 / q
            d = cv2.remap(d, xx + A * w1, yy + A * w2, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
            lo_, hi_ = np.percentile(d, [8, 97])
            d = np.clip((d - lo_) / (hi_ - lo_), 0, 1)
            d = (d * d * (3 - 2 * d)).astype(np.float32)                      # 拉开成团块与空隙
            ws = _fbm(rng, ah, aw, (6.0 * sc * 2 / q, 3.0 * sc * 2 / q), 5.0, (1.0, 0.45))  # 烟丝：横向细纹（宋画淡墨横扫的烟岚）
            self.atlas.append((d, w1.astype(np.float32), w2.astype(np.float32), ws.astype(np.float32)))
        yq, xq = np.mgrid[0:self.hq, 0:self.wq].astype(np.float32)
        self.xq, self.yq = xq, yq


def light_tone(fr):
    f = fr.reshape(-1, 3).astype(np.float32)
    y = f @ np.float32([0.299, 0.587, 0.114])
    lo, hi = np.percentile(y, [60, 92])
    return f[(y >= lo) & (y <= hi)].mean(0)


def zoom_about(fr, z, cx, cy):
    if abs(z - 1) < 1e-4: return fr
    M = np.float32([[z, 0, cx * (1 - z)], [0, z, cy * (1 - z)]])
    return cv2.warpAffine(fr, M, (fr.shape[1], fr.shape[0]), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)


class FogTrans:
    """多层烟云转场。
    cover：rise 自下升起（烟霞锁腰）/ spread 自画中雾带 (xc,yc) 横向漫开，镜头同时朝雾带缓推（push）；
    swap 在雾全覆盖时换段；
    reveal：peak 云海面从上往下沉，主峰峰顶先露出雾上，雾收成腰间一带再散 / sink 顶先散、雾沉到林间再散。
    各层进度有先后（近层先到先走），近层从镜头旁掠过；雾里深色（墨）先透出、后被吞没。"""
    def __init__(self, tr, fog, W, H, get):
        self.tr, self.fog, self.W, self.H = tr, fog, W, H
        sc = H / 720.0; self.sc = sc; q = FOG_Q
        c0 = light_tone(get(tr['src'], tr['cover'][0]))
        c1 = light_tone(get(tr['dst'], tr['reveal'][1]))
        self.c0 = np.minimum(0.45 * c0 * 1.12 + 0.55 * FOG_WHITE, 250)              # 雾比景亮，偏绢上留白
        self.c1 = np.minimum(0.45 * c1 * 1.12 + 0.55 * FOG_WHITE, 250)
        self.t_a = tr['cover'][0]
        self.vp = (tr['xc'] * sc / q, tr['yc'] * sc / q)                          # 镜头前进的消失点
        hq, wq = fog.hq, fog.wq
        xx, yy = fog.xq, fog.yq
        if tr['cover_mode'] == 'spread':
            self.rho = np.sqrt((xx - self.vp[0]) ** 2 + ((yy - self.vp[1]) / 0.38) ** 2)
            self.rho_max = float(self.rho.max())
        rng = np.random.default_rng(7 + int(tr['cover'][0]))
        en = _fbm(rng, int(hq * 1.6), int(wq * 1.6), (52 * sc * 2 / q, 26 * sc * 2 / q), 2.0, (1.0, 0.25))
        self.env_n = en                                                           # 雾前沿/云海面的起伏（不成直线、不成椭圆）
        self.env_f = _fbm(rng, int(hq * 1.6), int(wq * 1.6), (22 * sc * 2 / q, 10 * sc * 2 / q), 2.5, (1.0, 0.4))  # 细一级的云头
        self.last_alpha = None

    def env(self, t, fine=False):
        en = self.env_f if fine else self.env_n; hq, wq = self.fog.hq, self.fog.wq
        dt = t - self.t_a
        oy, ox = (en.shape[0] - hq) / 2, (en.shape[1] - wq) / 2 + 6 * self.sc * dt / FOG_Q
        M = np.float32([[1, 0, ox], [0, 1, oy]])
        return cv2.warpAffine(en, M, (wq, hq), flags=cv2.INTER_LINEAR | cv2.WARP_INVERSE_MAP, borderMode=cv2.BORDER_REFLECT)

    def color(self, t):
        tr = self.tr
        k = ss(tr['cover'][1] - 0.6, tr['reveal'][0] + 0.8, t)
        return self.c0 * (1 - k) + self.c1 * k

    # 覆盖场：0 = 无雾，1 = 满雾（每层按自己的进度）
    def cov(self, t, i):
        tr = self.tr; fog = self.fog; hq, wq = fog.hq, fog.wq
        c0, c1 = tr['cover']; r0, r1 = tr['reveal']
        en = self._en if getattr(self, '_en_t', None) == t else self.env(t)
        self._en, self._en_t = en, t
        Y = fog.yq + 0.09 * hq * en
        n = len(FOG_LAYERS); near = i / (n - 1)
        if t < c1:
            p = min(1.0, ss(c0, c1, t) * (1.0 + (0.30 if tr['cover_mode'] == 'rise' else 0.12) * near))
            if tr['cover_mode'] == 'rise':
                band = 0.34 * hq; m = band
                yf = (hq + m) - p * (hq + 2 * m)
                return ssa((Y - yf) / band + 0.5)
            band = 0.26 * wq; m = band
            R = -m + p * (self.rho_max + 2 * m)
            en2 = self._en2 if getattr(self, '_en2_t', None) == t else self.env(t, fine=True)
            self._en2, self._en2_t = en2, t
            return ssa((R - self.rho - 0.12 * wq * en - 0.07 * wq * en2) / band + 0.5)
        if t <= r0:
            return np.ones_like(Y)
        x = min(1.0, (t - r0) / (r1 - r0) * (1.0 + 0.45 * near))
        yc = tr['yc'] * self.sc / FOG_Q
        band = 0.34 * hq; m = band
        if tr['reveal_mode'] == 'peak':
            ytop = -m + ss(0.0, 0.62, x) * (yc - 30 * self.sc / FOG_Q + m)
            ybot = (hq + m) - ss(0.22, 0.78, x) * (hq + m - (yc + 70 * self.sc / FOG_Q))
            Yb = fog.yq - 0.08 * hq * en
            return ssa((Y - ytop) / band + 0.5) * ssa((ybot - Yb) / band + 0.5) * (1 - ss(0.55, 1.0, x))
        ytop = -m + ss(0.0, 0.78, x) * (0.74 * hq + m)
        return ssa((Y - ytop) / band + 0.5) * (1 - ss(0.5, 1.0, x))

    def layer(self, t, i):
        """该层在屏幕（1/2 分辨率）上的密度、不透明度、明暗"""
        fog = self.fog; L = FOG_LAYERS[i]; d_at, w1, w2, ws_at = fog.atlas[i]
        dt = t - self.t_a; q = FOG_Q; sc = self.sc
        z = math.exp(L['zr'] * dt)
        ah, aw = d_at.shape
        bx = (fog.xq - self.vp[0]) / z + aw / 2 + L['vx'] * sc * dt / q
        by = (fog.yq - self.vp[1]) / z + ah / 2 + L['vy'] * sc * dt / q * (1 if self.tr['cover_mode'] == 'rise' else 0.4)
        wu = 15 * sc * dt / q                                              # 扭曲场自己在走 → 云团翻卷变形
        A = 30 * sc / q
        ox = cv2.remap(w1, bx + wu, by - 0.5 * wu, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
        oy = cv2.remap(w2, bx - 0.7 * wu, by + wu, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
        mx, my = bx + A * ox, by + A * oy
        d = cv2.remap(d_at, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
        wsp = cv2.remap(ws_at, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
        cov = self.cov(t, i)
        thr = 1.30 - 1.60 * cov
        soft = 0.40 if (i == 0 and t < self.tr['reveal'][0]) else 0.55
        c0_, c1_ = self.tr['cover']
        soft += 0.55 * (1 - ss(c0_, c0_ + 0.55 * (c1_ - c0_), t))                  # 刚漫开的头一两秒边缘更虚（免成剪纸边）
        a = ssa((d - thr) / soft + 0.5) * L['cap'] * (1 - ss(2.3, 3.6, z))   # 边缘宽而软；最近层放大到过镜头时淡去
        if i > 0: a = a * ssa(d * 1.35 - 0.12)                                   # 前层成团：团块浓、空隙透
        # 受光：上沿亮、下沿压淡墨
        db = cv2.GaussianBlur(d, (0, 0), 7.0 * sc * 2 / q)
        dy = 11.0 * sc * 2 / q
        above = cv2.warpAffine(db, np.float32([[1, 0, 0], [0, 1, dy]]), (d.shape[1], d.shape[0]),
                               borderMode=cv2.BORDER_REPLICATE)
        fine = d - cv2.GaussianBlur(d, (0, 0), 4.0 * sc * 2 / q)              # 烟丝级细节（横向拉长的细纹）
        shade = np.clip(0.66 + 1.45 * (db - above) + 0.55 * (db - 0.5) + 2.4 * fine, 0.0, 1.10)
        return a, shade, wsp

    def render(self, t, src_fr, dst_fr):
        tr = self.tr
        c0, c1 = tr['cover']; r0, r1 = tr['reveal']
        if t < tr['swap']:
            base = src_fr.astype(np.float32)
            pz = tr.get('push', 0.0)
            if pz: base = zoom_about(base, 1 + pz * max(0.0, t - c0), tr['xc'] * self.sc, tr['yc'] * self.sc)
        else:
            base = dst_fr.astype(np.float32)
        if t < c0 or t > r1:
            self.last_alpha = None; return base
        col = self.color(t)
        dark_col = col * 0.76 + FOG_INK * 0.24                                # 云团背光面
        haze = col * 0.80 + FOG_INK * 0.20                                    # 后层：淡墨烘染的深处（烘云托月：云是留白，四周染淡墨）
        n = len(FOG_LAYERS)
        C = np.zeros((self.fog.hq, self.fog.wq, 3), np.float32); Aq = np.zeros((self.fog.hq, self.fog.wq), np.float32)
        for i in range(n):
            a, sh, wsp = self.layer(t, i)
            if i == 0 and c1 <= t <= r0: a = np.ones_like(a)                   # 全覆盖时后层不透光
            else:                                                              # 雾团边缘羽化（免剪纸边）；刚漫开时更虚
                sg = (2.5 + 7.0 * (1 - ss(c0, c0 + 0.6 * (c1 - c0), t))) * self.sc * 2 / FOG_Q
                a = cv2.GaussianBlur(a, (0, 0), sg)
            if i == 0: lc = haze[None, None, :] * (0.74 + 0.42 * sh)[..., None]
            else: lc = dark_col[None, None, :] + (col - dark_col)[None, None, :] * sh[..., None]
            tint = FOG_LAYERS[i]['tint']
            if tint: lc = lc * (1 - tint) + (col * 0.82)[None, None, :] * tint   # 远层略灰
            lc = lc * (1 + (0.05 if i == 0 else 0.035) * wsp)[..., None]
            C = C * (1 - a[..., None]) + lc * a[..., None]
            Aq = Aq * (1 - a) + a
        Cf = cv2.resize(C, (self.W, self.H), interpolation=cv2.INTER_CUBIC)
        Af = np.clip(cv2.resize(Aq, (self.W, self.H), interpolation=cv2.INTER_CUBIC), 0, 1)
        # 深色先透：墨比绢先从薄雾里露出、后被吞没（全覆盖时不透）
        if t < c1: kap = 0.70 * (1 - ss(c0 + 0.35 * (c1 - c0), c1, t))
        elif t <= r0: kap = 0.0
        else: kap = 0.70 * ss(r0, r0 + 0.45 * (r1 - r0), t)
        if kap > 0:
            lum = base @ np.float32([0.299, 0.587, 0.114])
            ref = float(np.percentile(lum[::8, ::8], 85))
            dk = cv2.GaussianBlur(np.clip((ref - lum) / (0.55 * ref), 0, 1), (0, 0), 1.2 * self.sc)
            k = 1 - kap * dk
            Af = Af * k; Cf = Cf * k[..., None]
        self.last_alpha = Af
        return base * (1 - Af[..., None]) + Cf * self.fog.weave


def fog_flat_stats(img, alpha=None, blk=24):
    """雾不平涂的客观检查：去掉绢丝级纹理（缩到 640 宽 + σ2 模糊）后，按 24×24 块算亮度标准差。
    只统计雾覆盖 >0.5 的块。返回 (有雾块数, 平涂块比例[std<1.2], 雾区块均值的离散度)。"""
    y = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY).astype(np.float32)
    y = cv2.GaussianBlur(cv2.resize(y, (640, 360), interpolation=cv2.INTER_AREA), (0, 0), 2.0)
    hb, wb = 360 // blk, 640 // blk
    yb = y[:hb * blk, :wb * blk].reshape(hb, blk, wb, blk)
    sd = yb.std(axis=(1, 3)); mu = yb.mean(axis=(1, 3))
    if alpha is None: m = np.ones_like(sd, bool)
    else:
        a = cv2.resize(alpha.astype(np.float32), (640, 360), interpolation=cv2.INTER_AREA)
        m = a[:hb * blk, :wb * blk].reshape(hb, blk, wb, blk).mean(axis=(1, 3)) > 0.5
    if m.sum() == 0: return 0, 0.0, 0.0
    return int(m.sum()), float((sd[m] < 1.2).mean()), float(mu[m].std())


def split_lh(fr, sig):
    f = fr.astype(np.float32); lo = cv2.GaussianBlur(f, (0, 0), sig); return lo, f - lo


# ---------------------------------------------------------------- 字幕渲染
class SubRenderer:
    def __init__(self, cues, W, H):
        self.cues = cues; self.W, self.H = W, H
        sc = H / 720.0; size = int(round(32 * sc))
        font = ImageFont.truetype(FONT, size)
        self.patches = []
        col = np.float32([0xED, 0xE6, 0xD8])
        for a, b, text in cues:
            parts = text.split(' '); gap = int(round(0.6 * size))
            widths = [font.getbbox(p)[2] - font.getbbox(p)[0] for p in parts]
            tw = sum(widths) + gap * (len(parts) - 1)
            pad = int(12 * sc); ph = size + 2 * pad + int(10 * sc); pw = tw + 2 * pad
            m = Image.new('L', (pw, ph), 0); d = ImageDraw.Draw(m); x = pad
            asc = font.getmetrics()[0]
            for p, wdt in zip(parts, widths):
                d.text((x - font.getbbox(p)[0], pad + int(3 * sc)), p, font=font, fill=255); x += wdt + gap
            txt = np.asarray(m, np.float32) / 255.0
            sh1 = np.roll(np.roll(txt, max(1, int(round(sc))), 0), max(1, int(round(sc))), 1)
            sh1 = cv2.GaussianBlur(sh1, (0, 0), 0.8 * sc) * 0.75                         # 1 px 柔阴影
            halo = cv2.GaussianBlur(cv2.dilate(txt, np.ones((3, 3), np.uint8)), (0, 0), 3.2 * sc) * 0.55  # 柔光晕，亮底上保字清楚
            ash = np.clip(1 - (1 - sh1) * (1 - halo), 0, 1)
            x0 = (W - pw) // 2; y0 = int(round(H * 0.905 - ph / 2))
            self.patches.append((a, b, x0, y0, txt, ash))
        self.col = col; self.shcol = np.float32([18, 13, 8])

    def apply(self, img, t):
        for a, b, x0, y0, txt, ash in self.patches:
            if t < a or t > b: continue
            k = min(1.0, (t - a) / 0.3, (b - t) / 0.3); k = k * k * (3 - 2 * k)
            if k <= 0: continue
            h, w = txt.shape
            reg = img[y0:y0 + h, x0:x0 + w].astype(np.float32)
            s = (ash * k)[..., None]; reg = reg * (1 - s) + self.shcol * s
            tt = (txt * k)[..., None]; reg = reg * (1 - tt) + self.col * tt
            img[y0:y0 + h, x0:x0 + w] = np.clip(reg + 0.5, 0, 255).astype(np.uint8)
        return img


def check_glyphs(cues):
    font = ImageFont.truetype(FONT, 32)
    tofu = np.asarray(font.getmask('\U000F0000'))
    chars = sorted(set(''.join(t for _, _, t in cues)) - {' '})
    bad = []
    for ch in chars:
        m = np.asarray(font.getmask(ch))
        if m.size == 0 or (m.shape == tofu.shape and np.array_equal(m, tofu)): bad.append(ch)
    return chars, bad


# ---------------------------------------------------------------- 合成器
class Compositor:
    def __init__(self, W, H, s4, s4mask, cues, burn_subs=True, res=720, strict=False):
        self.W, self.H = W, H
        files = {k: seg_path(v, res, strict) for k, v in SEG_FILE.items()}; files['s4'] = s4
        self.readers = {k: Reader(v, W, H) for k, v in files.items()}
        self.m3 = Reader(seg_path('seg_s3_water_mask.mp4', res, strict), W, H, gray=True)
        self.m4 = Reader(s4mask, W, H, gray=True) if s4mask else None
        for k, r in list(self.readers.items()) + [('m3', self.m3), ('m4', self.m4)]:
            if r: print(f'  {k:3s} {r.src_wh[0]}×{r.src_wh[1]} {os.path.relpath(r.path, SER)}', flush=True)
        self.fog = Fog(W, H)
        self.fogtr = {}
        self.subs = SubRenderer(cues, W, H) if burn_subs else None
        self.sc = H / 720.0

    def seg_frame(self, seg, t):
        return self.readers[seg].get(int(round((t - SEG_START[seg]) * FPS)))

    def owner(self, t):
        own = TRANS[0]['src']
        for tr in TRANS:
            if t >= (tr.get('swap') or (tr['a'] + tr['b']) / 2): own = tr['dst']
        return own

    def frame(self, n):
        t = n / FPS
        tr = next((x for x in TRANS if x['a'] <= t <= x['b']), None)
        if tr is None:
            img = self.seg_frame(self.owner(t), t).copy()
        else:
            k = tr['kind']
            if k == 'fog':
                key = id(tr)
                if key not in self.fogtr:
                    self.fogtr[key] = FogTrans(tr, self.fog, self.W, self.H, lambda s, tt: self._still(s, tt))
                src = self.seg_frame(tr['src'], t) if t < tr['swap'] else None
                dst = self.seg_frame(tr['dst'], t) if t >= tr['swap'] else None
                out = self.fogtr[key].render(t, src, dst)
            elif k == 'water':
                f3 = self.seg_frame('s3', t); f4 = self.seg_frame('s4', t)
                i3 = int(round((t - SEG_START['s3']) * FPS)); i4 = int(round((t - SEG_START['s4']) * FPS))
                m = self.m3.get(i3).astype(np.float32) / 255.0
                if self.m4 is not None: m = m * (self.m4.get(i4).astype(np.float32) / 255.0)
                m = cv2.GaussianBlur(m, (0, 0), 24 * self.sc)[..., None]
                sig = 9 * self.sc
                lo3, d3 = split_lh(f3, sig); lo4, d4 = split_lh(f4, sig)
                wd = ss(*tr['detail'], t); wl = ss(*tr['low'], t); wf = ss(*tr['full'], t)
                # 水色（低频）全屏同步换，免出色块；细节：水面里先换，非水面（船、山脚）晚一步浮出
                wde = m * wd + (1 - m) * wf
                out = lo3 * (1 - wl) + lo4 * wl + d3 * (1 - wde) + d4 * wde
            elif k == 'glaze':
                f4 = self.seg_frame('s4', t); f5 = self.seg_frame('s5', t).astype(np.float32)
                if 'lift' in tr:                                  # 提亮 S5 底图里的孤立墨点（只提暗于局部均值的部分）
                    l0, l1, l2 = tr['lift']; kl = 0.9 * ss(l0, l0 + 0.3, t) * (1 - ss(l1, l2, t))
                    if kl > 0:
                        bl = cv2.GaussianBlur(f5, (0, 0), 36 * self.sc)
                        f5 = f5 + kl * np.clip(bl - f5, 0, None)
                sig = 22 * self.sc
                lo4, d4 = split_lh(f4, sig); lo5, d5 = split_lh(f5, sig)
                wl = ss(*tr['low'], t); wd = ss(*tr['detail'], t)
                out = lo4 * (1 - wl) + lo5 * wl + d4 * (1 - wd) + d5 * wd
            else:  # fade
                a = self.seg_frame(tr['src'], t).astype(np.float32); b = self.seg_frame(tr['dst'], t).astype(np.float32)
                w = ss(*tr['span'], t); out = a * (1 - w) + b * w
            img = np.clip(out + 0.5, 0, 255).astype(np.uint8)
        if self.subs: img = self.subs.apply(img, t)
        return img

    def _still(self, seg, t):
        r = Reader(self.readers[seg].path, self.W, self.H)
        fr = r.get(int(round((t - SEG_START[seg]) * FPS))).copy(); r.close(); return fr

    def close(self):
        for r in self.readers.values(): r.close()
        self.m3.close()
        if self.m4: self.m4.close()


FOG_FLAT_MAX, FOG_SPREAD_MIN = 0.25, 5.0


def fog_check(comp, step=3):
    """两处雾转场逐帧（每 step 帧）检查：雾覆盖 >0.5 的 24×24 块里，去绢纹后 std<1.2 的"平涂块"比例 ≤ FOG_FLAT_MAX，
    且雾区块均值的离散度 ≥ FOG_SPREAD_MIN（有浓淡）。只统计雾块数 ≥ 全屏 15% 的帧。不带字幕渲。"""
    subs, comp.subs = comp.subs, None
    ok_all = True
    for tr in [x for x in TRANS if x['kind'] == 'fog']:
        rows = []
        for n in range(int(round(tr['a'] * FPS)), int(round(tr['b'] * FPS)) + 1, step):
            img = comp.frame(n)
            ft = comp.fogtr.get(id(tr))
            A = ft.last_alpha if ft is not None else None
            if A is None: continue
            nb, flat, spread = fog_flat_stats(img, A)
            if nb < 0.15 * (360 // 24) * (640 // 24): continue
            rows.append((n / FPS, nb, flat, spread))
        r = np.array(rows)
        bad = r[(r[:, 2] > FOG_FLAT_MAX) | (r[:, 3] < FOG_SPREAD_MIN)]
        ok_all &= len(bad) == 0
        print(f"雾 {tr['src']}→{tr['dst']} {tr['a']:.1f}-{tr['b']:.1f}s：检查 {len(r)} 帧；平涂块比例 最大 {r[:, 2].max():.2f}"
              f"（{r[r[:, 2].argmax(), 0]:.2f}s）中位 {np.median(r[:, 2]):.2f}；浓淡离散度 最小 {r[:, 3].min():.1f}"
              f"（{r[r[:, 3].argmin(), 0]:.2f}s）中位 {np.median(r[:, 3]):.1f}；不合格 {len(bad)} 帧"
              + ('' if len(bad) == 0 else '  例：' + ', '.join(f'{x[0]:.2f}s' for x in bad[:6])))
    print('雾不平涂检查：' + ('通过' if ok_all else '不通过') + f'（阈值：平涂块 ≤{FOG_FLAT_MAX:.0%}，离散度 ≥{FOG_SPREAD_MIN}）')
    comp.subs = subs
    return ok_all


def complete(path, nfr=2250):
    """渲完的段：ffprobe 读得出且帧数对（渲染中的文件没有 moov，读不出）"""
    if nfr is None: nfr = 2250
    if not os.path.exists(path): return False
    r = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-count_packets', '-show_entries',
                        'stream=nb_read_packets', '-of', 'csv=p=0', path], capture_output=True, text=True).stdout.strip()
    return r.isdigit() and int(r) == nfr


def seg_path(name, res=720, strict=False):
    """按分辨率取段文件。1080 缺段/未渲完：strict 报错，否则退回 720 段（Reader 放大）并警告。"""
    p = os.path.join(SEGS_BY_RES[res], name)
    if res == 720 or complete(p, SEG_NFR.get(name)): return p
    if strict: raise SystemExit(f'--strict：{p} 缺失或帧数不对（应 {SEG_NFR.get(name)} 帧）')
    print(f'WARN {name}：segs_1080 里没有完整的 1080 段，临时用 720 段放大（只供测试）', flush=True)
    return os.path.join(SEGS, name)


def pick_s4(a):
    v2 = seg_path('seg_s4.mp4', a.res, a.strict); v2m = seg_path('seg_s4_water_mask.mp4', a.res, a.strict)
    s4 = a.s4 or (v2 if complete(v2) else os.path.join(SEGS, 'qianli', 'review', 'seg_s4_v1.mp4'))
    if a.s4mask is not None: m = a.s4mask or None
    else: m = v2m if (s4 == v2 and complete(v2m)) else None
    return s4, m


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('cmd', choices=['subs', 'audio', 'peek', 'video', 'fogcheck'])
    ap.add_argument('times', nargs='*', type=float)
    ap.add_argument('--t0', type=float, default=0.0); ap.add_argument('--t1', type=float, default=DUR)
    ap.add_argument('--res', type=int, choices=[720, 1080], default=720, help='段源分辨率：720 读 segs/，1080 读 segs_1080/')
    ap.add_argument('--height', type=int, help='输出高度（缺省 = --res；短测试可用 480）')
    ap.add_argument('--strict', action='store_true', help='--res 1080 时任何段不是完整 1080 段就报错（终版用）')
    ap.add_argument('--abr', help='AAC 码率（缺省 720:192k，1080:256k）')
    ap.add_argument('--out'); ap.add_argument('--fast', action='store_true')
    ap.add_argument('--s4'); ap.add_argument('--s4mask')
    ap.add_argument('--nosubs', action='store_true')
    ap.add_argument('--audio', help='外部音轨（如 ../out/audio/mix.wav），替换缺省的 work/music_mix.wav')
    ap.add_argument('--srt', help='烧入这个 SRT（如 ../out/subs.srt），替换缺省的锚点字幕')
    a = ap.parse_args()
    os.makedirs(WORK, exist_ok=True); os.makedirs(OUT, exist_ok=True); os.makedirs(PEEK, exist_ok=True)
    cues = build_cues()                                   # 锚点字幕：配乐压低区按它算
    write_srt(cues, os.path.join(WORK, 'subs_anchor.srt'))
    bcues = read_srt(a.srt) if a.srt else cues            # 烧入画面的字幕
    if a.cmd == 'subs':
        for c in bcues: print(f'{c[0]:7.2f}-{c[1]:7.2f} ({c[1]-c[0]:.1f}s) {c[2]}')
        chars, bad = check_glyphs(bcues); print(f'字形检查：{len(chars)} 个字，缺字 {bad or "无"}')
        print('降音区：', [(round(x, 1), round(y, 1)) for x, y in duck_zones(cues)])
        return
    if a.cmd == 'audio':
        build_audio(cues); return
    H = a.height or a.res; W = int(round(H * 16 / 9 / 2)) * 2
    abr = a.abr or ('256k' if a.res == 1080 else '192k')
    s4, s4m = pick_s4(a)
    print(f'res = {a.res}  out = {W}×{H}\ns4 = {s4}\ns4 mask = {s4m or "(无，用 seg_s3 遮罩近似)"}', flush=True)
    comp = Compositor(W, H, s4, s4m, bcues, burn_subs=not a.nosubs, res=a.res, strict=a.strict)
    if a.cmd == 'fogcheck':
        fog_check(comp, step=int(a.times[0]) if a.times else 3); comp.close(); return
    if a.cmd == 'peek':
        tiles = []
        for t in a.times:
            img = comp.frame(int(round(t * FPS)))
            p = os.path.join(PEEK, f'at_{t:07.2f}.jpg')
            cv2.imwrite(p, cv2.cvtColor(img, cv2.COLOR_RGB2BGR), [cv2.IMWRITE_JPEG_QUALITY, 90])
            th = cv2.resize(img, (480, 270), interpolation=cv2.INTER_AREA).copy()
            cv2.putText(th, f'{t:.2f}', (6, 18), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 40, 40), 1)
            tiles.append(th)
        while len(tiles) % 4: tiles.append(np.zeros_like(tiles[0]))
        sheet = np.vstack([np.hstack(tiles[i:i + 4]) for i in range(0, len(tiles), 4)])
        cv2.imwrite(os.path.join(PEEK, 'sheet.jpg'), cv2.cvtColor(sheet, cv2.COLOR_RGB2BGR), [cv2.IMWRITE_JPEG_QUALITY, 85])
        comp.close(); print('peek ->', os.path.join(PEEK, 'sheet.jpg')); return
    # video
    if a.audio:
        mix = os.path.abspath(a.audio)
        ad = float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', mix],
                                  capture_output=True, text=True).stdout)
        assert abs(ad - DUR) < 0.01, f'外部音轨时长 {ad:.3f}s ≠ {DUR}s'
    else:
        mix = os.path.join(WORK, 'music_mix.wav')
        if not os.path.exists(mix): build_audio(cues, report=False)
    print(f'audio = {mix}\nsubs = {a.srt or "(锚点字幕)"}{" (不烧)" if a.nosubs else ""}', flush=True)
    n0, n1 = int(round(a.t0 * FPS)), int(round(min(a.t1, DUR) * FPS))
    out = a.out or os.path.join(HERE, 'test.mp4')
    venc = ['-c:v', 'libx264', '-preset', 'veryfast' if a.fast else 'medium', '-crf', '20' if a.fast else '18',
            '-pix_fmt', 'yuv420p', '-profile:v', 'high', '-tune', 'film']
    cmd = ['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
           '-ss', f'{n0 / FPS:.6f}', '-t', f'{(n1 - n0) / FPS:.6f}', '-i', mix,
           '-map', '0:v', '-map', '1:a', *venc, '-c:a', 'aac', '-b:a', abr, '-ar', '48000',
           '-movflags', '+faststart', '-shortest', out]
    enc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    import time; t_start = time.time()
    for n in range(n0, n1):
        enc.stdin.write(comp.frame(n).tobytes())
        if (n - n0) % 300 == 0:
            el = time.time() - t_start
            print(f'[{el:6.0f}s] frame {n - n0}/{n1 - n0}  ({(n - n0) / max(el, 1e-3):.1f} fps)', flush=True)
    enc.stdin.close(); enc.wait(); comp.close()
    print(f'done {out}  ({time.time() - t_start:.0f}s)', flush=True)


if __name__ == '__main__':
    main()
