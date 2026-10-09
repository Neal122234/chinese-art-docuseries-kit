"""第二版成片客观自检：音画时长、帧间突变、亮度、字幕对语音、"作品可见"（全貌干净停住时长 / 转场遮挡时长 /
水图十二段停住时长）、浪涌暗墨时长、16 帧联系表 → ../out/contact_v2.jpg。
用法：python3 work/verify_v2.py ../out/ep02_nansong_v2.mp4"""
import sys, os, re, json, subprocess, numpy as np, cv2
HERE = os.path.dirname(os.path.abspath(__file__)); ASM = os.path.dirname(HERE); EP = os.path.dirname(ASM)
sys.path.insert(0, ASM)
import assemble as A
V = sys.argv[1]
FPS = 30; W, H = 320, 180; Q = 4                    # 1/4 分辨率灰度
SUB_Y = 610 // Q                                    # 字幕带（y ≥ 610）不计入"作品可见"比较


def gray_frames(path, t0=0.0, dur=None):
    cmd = ['ffmpeg', '-v', 'error', '-ss', f'{t0:.4f}', '-i', path]
    if dur: cmd += ['-t', f'{dur:.4f}']
    cmd += ['-vf', f'scale={W}:{H}:flags=area,format=gray', '-f', 'rawvideo', '-']
    raw = subprocess.run(cmd, capture_output=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(-1, H, W)          # uint8（整片 8880 帧 ≈ 0.5 GB）


# 1) 音画时长
r = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'stream=codec_type,duration,nb_frames', '-of', 'csv=p=0', V],
                   capture_output=True, text=True).stdout
print('streams:', r.strip().replace('\n', ' | '))

# 2) 全片逐帧（1/4 灰度）：帧间突变、最低亮度
F = gray_frames(V)
N = len(F)
d = np.zeros(N - 1); means = np.zeros(N)
for c0 in range(0, N, 300):                          # 分块算，免得整片转 float 占 2 GB
    blk = F[c0:min(N, c0 + 301)].astype(np.float32)
    means[c0:c0 + len(blk)] = blk.mean((1, 2))
    d[c0:c0 + len(blk) - 1] = np.abs(np.diff(blk, axis=0)).mean((1, 2))
med = np.array([np.median(d[max(0, i - 15):i + 15]) for i in range(len(d))])
spk = np.nonzero(d > np.maximum(6.0, 5 * med))[0]
print(f'frames {N}  帧差 中位 {np.median(d):.2f} 最大 {d.max():.2f}（{(d.argmax() + 1) / FPS:.2f}s）  跳变帧 {len(spk)}'
      + ('' if not len(spk) else '：' + ', '.join(f'{(i + 1) / FPS:.2f}s({d[i]:.1f})' for i in spk[:12])))
print(f'全片平均亮度 最低 {means.min():.1f}/255 = {means.min() / 255:.0%}（{means.argmin() / FPS:.2f}s）')

# 3) 浪涌成泼墨：满屏暗墨时长（平均亮度低于两端画面较暗者的 80%）与最暗帧
tr = next(x for x in A.TRANS if x['kind'] == 'surge')
a, b = tr['win']; i0, i1 = int(round((a - 1) * FPS)), int(round((b + 1) * FPS))
ref = min(means[i0 - 1], means[i1 + 1]); thr = 0.8 * ref
dark = np.nonzero(means[i0:i1] < thr)[0]
print(f'浪涌 {a:.1f}–{b:.1f}s：两端平均亮度 {means[i0 - 1]:.0f}/{means[i1 + 1]:.0f}；低于 80%（{thr:.0f}）的时长 '
      f'{len(dark) / FPS:.2f}s' + (f'（{(i0 + dark[0]) / FPS:.2f}–{(i0 + dark[-1] + 1) / FPS:.2f}s）' if len(dark) else '')
      + f'；最暗帧 {means[i0:i1].min():.1f}/255 = {means[i0:i1].min() / 255:.0%}（{(i0 + means[i0:i1].argmin()) / FPS:.2f}s）')

# 4) 字幕与语音
S = json.load(open(os.path.join(EP, 'voice', 'work', 'timing.json')))
raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', os.path.join(EP, 'out', 'audio', 'narration.wav'), '-ac', '1', '-ar', '16000',
                      '-f', 'f32le', '-'], capture_output=True).stdout
x = np.frombuffer(raw, np.float32); hop = 160
e = 20 * np.log10(np.sqrt(np.convolve(x ** 2, np.ones(800) / 800, 'same')[::hop]) + 1e-9)
C = A.read_srt(os.path.join(EP, 'out', 'subs.srt'))
offs = []
for s in S:
    c = min(C, key=lambda c: abs(c[0] - s['start']))
    j0 = int((s['start'] - 0.6) * 100); on = np.nonzero(e[j0:j0 + 160] > -45)[0]
    onset = (j0 + on[0]) / 100 if len(on) else None
    offs.append((c[0], onset - c[0] if onset is not None else None, c[2]))
bad = [o for o in offs if o[1] is None or abs(o[1]) > 0.25]
v = np.array([o[1] for o in offs if o[1] is not None])
print(f'字幕对语音：{len(offs)} 句 / {len(C)} 条，起音−字幕起点 中位 {np.median(v) * 1000:+.0f} ms，最大偏差 {np.abs(v).max() * 1000:.0f} ms；'
      f'>250 ms 的 {len(bad)} 句' + ('' if not bad else '：' + '; '.join(f'{o[0]:.1f}s {o[2][:8]}' for o in bad)))
print(f'字幕最后一条止于 {C[-1][1]:.2f}s，末句语音止于 {S[-1]["end"]:.2f}s（片长 {N / FPS:.3f}s）')


# 5) 作品可见：全貌干净停住（作品框内与参考全貌帧平均差 < 1.5 灰阶，字幕带除外）
def runs(mask, t0):
    out = []; i = 0
    while i < len(mask):
        if mask[i]:
            j = i
            while j < len(mask) and mask[j]: j += 1
            out.append((t0 + i / FPS, t0 + j / FPS)); i = j
        else: i += 1
    return out


WORKS = [  # 名称, 参考全貌时刻, 作品框 (x0,y0,x1,y1)@720p, 搜索区间
    ('李唐《万壑松风图》', 12.0, (410, 24, 870, 696), (7, 60)),
    ('马远《踏歌图》', 58.0, (448, 27, 832, 690), (50, 110)),
    ('传马远《寒江独钓图》', 125.0, (44, 110, 976, 610), (110, 170)),
    ('梁楷《泼墨仙人》', 230.0, (374, 34, 746, 686), (218, 250)),
    ('南宋官窑青瓷', 277.0, (360, 40, 760, 690), (250, 285)),
]
print('作品全貌干净停住（与参考全貌帧差 < 1.5 灰阶，字幕带不计）：')
for name, tref, (x0, y0, x1, y1), (sa, sb) in WORKS:
    ys, ye, xs, xe = y0 // Q, min(y1 // Q, SUB_Y), x0 // Q, x1 // Q
    R = F[int(round(tref * FPS)), ys:ye, xs:xe].astype(np.float32)
    ia, ib = int(sa * FPS), int(sb * FPS)
    dd = np.abs(F[ia:ib, ys:ye, xs:xe].astype(np.float32) - R).mean((1, 2))
    rr = [x for x in runs(dd < 1.5, sa) if x[1] - x[0] >= 0.5]
    tot = sum(b_ - a_ for a_, b_ in rr)
    print(f'  {name}：合计 {tot:.1f}s ' + ' '.join(f'[{a_:.1f}–{b_:.1f} {b_ - a_:.1f}s]' for a_, b_ in rr)
          + ('' if tot >= 6 else '  ← 不足 6 s'))

# 6) 水图：长案全卷与十二段停住（相邻帧差 < 0.25 的连续段，179–205 s）
sa, sb = 172.5, 205.5
ia, ib = int(sa * FPS), int(sb * FPS)
st = runs(d[ia:ib] < 0.25, sa)
st = [x for x in st if x[1] - x[0] >= 0.5]
print(f'水图 {sa}–{sb}s 画面静止段 {len(st)} 个：' + ' '.join(f'[{a_:.2f}–{b_:.2f} {b_ - a_:.2f}s]' for a_, b_ in st))

# 7) 转场：画面既不是前一段也不是后一段（与两段原帧差都 > 4 灰阶）的时长；
#    其中"两件作品的结构都看不清"（与两段原帧的边缘相关都 < 0.5）的时长
def edges(g):
    gx = cv2.Sobel(g, cv2.CV_32F, 1, 0, ksize=3); gy = cv2.Sobel(g, cv2.CV_32F, 0, 1, ksize=3)
    m = np.sqrt(gx * gx + gy * gy)[:SUB_Y]; return (m - m.mean()).ravel()


def corr(p, q): return float((p * q).sum() / (np.sqrt((p * p).sum() * (q * q).sum()) + 1e-6))


print('转场（混合 = 与两段原帧差都 > 4；看不清 = 与两段边缘相关都 < 0.5）：')
for tr in A.TRANS:
    a, b = tr['win']; ia, ib = int(round(a * FPS)), int(round(b * FPS)) + 1
    Fs = gray_frames(os.path.join(A.SEGS, A.SEG_FILE[tr['src']]), (ia / FPS) - A.SEG_START[tr['src']], (ib - ia) / FPS)
    Fd = gray_frames(os.path.join(A.SEGS, A.SEG_FILE[tr['dst']]), (ia / FPS) - A.SEG_START[tr['dst']], (ib - ia) / FPS)
    n = min(len(Fs), len(Fd), ib - ia)
    mix = 0; lost = 0; lost_t = []
    for k in range(n):
        o = F[ia + k].astype(np.float32); fs = Fs[k].astype(np.float32); fd = Fd[k].astype(np.float32)
        ds = np.abs(o - fs)[:SUB_Y].mean(); dd_ = np.abs(o - fd)[:SUB_Y].mean()
        if ds > 4 and dd_ > 4: mix += 1
        eo = edges(o)
        if corr(eo, edges(fs)) < 0.5 and corr(eo, edges(fd)) < 0.5: lost += 1; lost_t.append((ia + k) / FPS)
    print(f"  {tr['kind']:6s} {tr['src']}→{tr['dst']} {a:.1f}–{b:.1f}s（{b - a:.1f}s）：混合 {mix / FPS:.2f}s，看不清 {lost / FPS:.2f}s"
          + (f'（{lost_t[0]:.2f}–{lost_t[-1]:.2f}）' if lost_t else ''))

# 8) 联系表
KEYS = [(44.5, '瀑布 无云带'), (52.75, '挂墙叠化'), (63.8, '全貌→题诗'), (79.5, '宫阙 无雾'), (100.8, '拉回全貌'),
        (112.4, '留白 一角'), (169.3, '涟漪变水图'), (178.8, '长案全卷'), (181.0, '残段'), (191.0, '黄河逆流段'),
        (203.0, '细浪漂漂'), (208.0, '黄河题名'), (217.4, '浪涌'), (218.6, '衣袍露出'), (249.2, '墨干开裂'), (287.8, '结尾一笔')]
tiles = []
for t, name in KEYS:
    b_ = subprocess.run(['ffmpeg', '-v', 'error', '-ss', f'{t:.3f}', '-i', V, '-frames:v', '1', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-'],
                        capture_output=True).stdout
    f = np.frombuffer(b_, np.uint8).reshape(720, 1280, 3)
    th = cv2.resize(f, (480, 270), interpolation=cv2.INTER_AREA).copy()
    cv2.putText(th, f'{t:.2f}s', (6, 18), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (40, 40, 255), 1)
    tiles.append(th)
sheet = np.vstack([np.hstack(tiles[i:i + 4]) for i in range(0, 16, 4)])
out = os.path.join(EP, 'out', 'contact_v2.jpg')
cv2.imwrite(out, sheet, [cv2.IMWRITE_JPEG_QUALITY, 88]); print('contact ->', out)
