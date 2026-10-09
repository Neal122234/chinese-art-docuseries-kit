"""第二集·南宋配音：逐句合成 → 对时 → 读音核对 →（后面）人声处理 → 配乐再让 → 混音；字幕按语音重对时。
（系统 python3 跑；合成调北宋集 voice/.venv 的 edge-tts（本目录 synth.py，缓存写本目录 work/tts）；ASR 调 /opt/anaconda3。）
复制自北宋集 series/voice/build_voice.py，改为读本集 plan/anchors.json，不再 import 北宋的 assemble。

用法（在 ep02_nansong/voice/ 下）：
  python3 build_voice.py fit        # 合成 + 对时（逐句提速/挪起点），写 work/timing.json，打印每句余量
  lockf -k ../../.heavy.lock python3 build_voice.py asr        # whisper base + large-v3-turbo 回写，拼音比对（work/asr_report*.txt）
  lockf -k ../../.heavy.lock python3 build_voice.py variants   # 多音字/专名：与同音替身逐句比 MFCC-DTW + F0 轮廓
    asr / variants 后面可跟若干句中片段，只核这几句，报告写 work/*_sel.txt（不覆盖全量报告）
  python3 build_voice.py subs       # 按 timing.json 的语音对时写 out/subs.srt（超 16 字在空格处拆条）
  lockf -k ../../.heavy.lock python3 build_voice.py mix <本集配乐.wav>   # 干声/配乐再让/混音 → out/audio/*.wav + 字幕 + 自检
改读音：只改下面 PRON（送去合成的文本），字幕原文在 plan/anchors.json，不动。
"""
import hashlib, json, math, os, re, shutil, subprocess, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
EP = os.path.dirname(HERE)                                   # series/ep02_nansong
SER = os.path.dirname(EP)                                    # series
ANCHORS = json.load(open(os.path.join(EP, 'plan', 'anchors.json')))   # [[起点(全局秒), 字幕原文], ...]
DUR = 296.0             # 第二版总长仍 296 s：s4 水图重做但窗口仍 166–222（十二段 180–204 每段 2 s），s5 起不后移

WORK = os.path.join(HERE, 'work'); TTS = os.path.join(WORK, 'tts')
OUTA = os.path.join(EP, 'out', 'audio'); SRT = os.path.join(EP, 'out', 'subs.srt')
VENV_PY = os.path.join(SER, 'voice', '.venv', 'bin', 'python')     # 北宋集的 edge-tts 环境（只读使用）
ASR_PY = '/opt/anaconda3/bin/python'
SR = 48000


def sid(frag):
    """含 frag 的句号（唯一）。"""
    hit = [i for i, (_, t) in enumerate(ANCHORS) if frag in t]
    assert len(hit) == 1, (frag, hit)
    return hit[0]


VOICE, PITCH, BASE_RATE = 'zh-CN-YunjianNeural', '-4Hz', -12
# 读音修正：只作用于送去合成的文本（等长替换，保证与字幕逐字对齐）。键 = (句号 或 None 表示全部, 原文片段)
PRON = {
    (sid('万壑松风'), '一一二四年'): '壹壹贰肆年',  # 原合成两个「一」连读粘成一个（whisper base/turbo 都听成「一二四年」「124年」）；
                                                  # 大写数字读音相同、不停顿，turbo 回写 1124 年。另试过「1124年」「１１２４年」「一/一」「一—一」
                                                  # 仍粘连，「一·一」「一-一」有 0.15 s 顿，「一、一」「一；一」停 0.35 s
    (sid('宿雨'), '朝'): '招',          # 「朝阳」此处是早晨的太阳 zhāo；原合成频谱最像「潮」cháo（北京朝阳区读法）
    (sid('一整卷'), '卷'): '绢',        # 「一整卷」手卷之卷 juàn；原合成频谱最像「捲」juǎn（北宋集同样问题，同样换绢）
    (sid('笔越少'), '笔'): '比',        # 句首「笔」被合成成上扬调，turbo 听成「别越少」（换「彼」也一样）；「比」回写为 bǐ
}
RATE_OVR = {}            # 句号 -> 起始 rate（%）
GAP_MIN, SHIFT_MAX, RATE_STEP, END_LIMIT = 0.30, 0.5, 2, DUR - 2.5
PRE, POST = 0.03, 0.12   # 语音起点前留 30 ms、末尾有效帧后留 120 ms 自然衰减（含 40 ms 淡出）

VOICE_LUFS = -16.0
DUCK_EXTRA = -4.0        # 人声下配乐在现有压低基础上再让 4 dB
ATTACK, RELEASE, HOLD, MERGE = 0.40, 1.20, 0.20, 2.0
TP_LIMIT = 10 ** (-1.5 / 20)     # 混音限幅 −1.5 dBFS（4× 过采样），给 AAC 编码留余量，成片实测 ≤ −1 dBTP

# 字幕（与北宋集 assemble.py 同参数）
MAXCH = 16


# ---------------------------------------------------------------- 句子
def sentences():
    out = []
    for i, (st, tx) in enumerate(ANCHORS):
        t = tx
        for (k, a), b in PRON.items():
            if k is None or k == i:
                assert len(a) == len(b), (a, b)
                t = t.replace(a, b)
        out.append(dict(i=i, anchor=float(st), text=tx, tts=t.replace(' ', '，') + '。'))
    return out


def tkey(s):
    return hashlib.sha1(f"{VOICE}|{rstr(s['rate'])}|{PITCH}|{s['tts']}".encode()).hexdigest()[:16]


def rstr(r): return r if isinstance(r, str) else f'{r:+d}%'


def synth(entries):
    plan = [dict(i=e['i'], tts=e['tts'], rate=rstr(e['rate']), pitch=PITCH, voice=VOICE) for e in entries]
    p = os.path.join(WORK, 'plan.json'); json.dump(plan, open(p, 'w'), ensure_ascii=False, indent=1)
    subprocess.run([VENV_PY, os.path.join(HERE, 'synth.py'), p], check=True)


def decode(path, sr=SR):
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', path, '-ac', '1', '-ar', str(sr), '-f', 'f32le', '-'],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).copy()


def frames_db(x, hop):
    n = len(x) // hop
    r = np.sqrt(np.mean(x[:n * hop].reshape(n, hop) ** 2, 1) + 1e-12)
    return 20 * np.log10(r)


def analyse(e):
    """解码、找语音起止（10 ms 帧 RMS，高于峰值 −45 dB 为有效），裁出片段，WordBoundary 换算成相对语音起点。"""
    k = tkey(e); mp3 = os.path.join(TTS, k + '.mp3'); meta = json.load(open(os.path.join(TTS, k + '.json')))
    x = decode(mp3); hop = SR // 100
    db = frames_db(x, hop); act = np.nonzero(db > db.max() - 45)[0]
    on = act[0] * hop / SR; off = (act[-1] + 1) * hop / SR
    a = max(0, int((on - PRE) * SR)); b = min(len(x), int((off + POST) * SR))
    clip = x[a:b].copy()
    fi, fo = int(0.005 * SR), int(0.04 * SR)
    clip[:fi] *= np.linspace(0, 1, fi, dtype=np.float32); clip[-fo:] *= np.linspace(1, 0, fo, dtype=np.float32)
    words = [dict(w, t=w['t'] - on) for w in meta['words']]
    tail_room = len(x) / SR - off                          # TTS 原文件语音后还剩多少静音（>0.1 s 说明合成没被截断）
    return dict(key=k, clip=clip, lead=on - a / SR, L=off - on, words=words, tail_room=tail_room,
                last_word_end=max(w['t'] + w['d'] for w in words) if words else 0.0)


def fit():
    S = sentences()
    for e in S: e['rate'] = RATE_OVR.get(e['i'], BASE_RATE); e['start'] = e['anchor']
    while True:
        synth(S)
        info = {e['i']: analyse(e) for e in S}
        changed = False
        for j, e in enumerate(S):
            nxt = S[j + 1]['anchor'] if j + 1 < len(S) else END_LIMIT + GAP_MIN
            if e['anchor'] + info[e['i']]['L'] + GAP_MIN > nxt and e['rate'] < 0:
                e['rate'] = min(0, e['rate'] + RATE_STEP); changed = True
        if not changed: break
    # 仍放不下：在 ±0.5 s 内挪起点（本句提前 / 下一句推后）
    for j, e in enumerate(S):
        e['L'] = info[e['i']]['L']
    for j, e in enumerate(S):
        nxt = S[j + 1] if j + 1 < len(S) else None
        lim = nxt['start'] if nxt else END_LIMIT + GAP_MIN
        over = e['start'] + e['L'] + GAP_MIN - lim
        if over <= 0: continue
        prev_end = S[j - 1]['start'] + S[j - 1]['L'] + GAP_MIN if j else 0.0
        can_early = min(SHIFT_MAX, e['start'] - prev_end)
        d = min(over, max(0.0, can_early)); e['start'] -= d; over -= d
        if over > 0 and nxt:
            nn = S[j + 2]['start'] if j + 2 < len(S) else END_LIMIT + GAP_MIN
            can_late = min(SHIFT_MAX - (nxt['start'] - nxt['anchor']), nn - GAP_MIN - (nxt['start'] + nxt['L']))
            d = min(over, max(0.0, can_late)); nxt['start'] += d; over -= d
        e['unfit'] = round(over, 3) if over > 1e-6 else 0.0
    rows = []
    for j, e in enumerate(S):
        f = info[e['i']]
        nxt = S[j + 1]['start'] if j + 1 < len(S) else END_LIMIT + GAP_MIN
        e.update(key=f['key'], lead=f['lead'], end=e['start'] + e['L'], gap=nxt - (e['start'] + e['L']),
                 words=f['words'], tail_room=f['tail_room'], last_word_end=f['last_word_end'])
        rows.append(f"{e['i']:2d} {e['start']:7.2f}{'*' if abs(e['start']-e['anchor'])>1e-6 else ' '} "
                    f"L={e['L']:5.2f} end={e['end']:7.2f} gap={e['gap']:5.2f} rate={e['rate']:+d}% "
                    f"tail={f['tail_room']:.2f} {e['text']}")
    json.dump(S, open(os.path.join(WORK, 'timing.json'), 'w'), ensure_ascii=False, indent=1)
    print('\n'.join(rows))
    bad = [e['i'] for e in S if e['gap'] < GAP_MIN - 1e-6]
    print(f"放不下的句：{bad or '无'}；提速句：{[(e['i'], e['rate']) for e in S if e['rate'] != BASE_RATE]}；"
          f"挪起点：{[(e['i'], round(e['start']-e['anchor'], 2)) for e in S if abs(e['start']-e['anchor'])>1e-6]}")
    return S


def load_timing():
    return json.load(open(os.path.join(WORK, 'timing.json')))


# ---------------------------------------------------------------- 读音核对（whisper 回写 + 拼音比对）
def asr(only=None):
    S = load_timing()
    tag = ''
    if only: S = [e for e in S if any(f in e['text'] for f in only)]; tag = '_sel'
    d = os.path.join(WORK, 'asr'); os.makedirs(d, exist_ok=True)
    items = []
    for e in S:
        w = os.path.join(d, f"{e['i']:02d}_{e['key']}.wav")
        if not os.path.exists(w):
            subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', os.path.join(TTS, e['key'] + '.mp3'), '-ac', '1', '-ar', '16000', w], check=True)
        items.append(dict(i=e['i'], wav=w, text=e['text']))
    jin = os.path.join(WORK, f'asr_in{tag}.json'); jout = os.path.join(WORK, f'asr_out{tag}.json')
    json.dump(items, open(jin, 'w'), ensure_ascii=False)
    subprocess.run([ASR_PY, os.path.join(HERE, 'asr_whisper.py'), jin, jout], check=True)
    subprocess.run([VENV_PY, os.path.join(HERE, 'pinyin_cmp.py'), jout, os.path.join(WORK, f'asr_report{tag}.txt')], check=True)
    print(open(os.path.join(WORK, f'asr_report{tag}.txt')).read())
    # base 对中文太吵（大量同音误写），再用本地已缓存的 whisper-large-v3-turbo（MLX）复核一遍
    jout2 = os.path.join(WORK, f'asr_out_turbo{tag}.json')
    subprocess.run([ASR_PY, os.path.join(HERE, 'asr_mlx.py'), jin, jout2], check=True)
    subprocess.run([VENV_PY, os.path.join(HERE, 'pinyin_cmp.py'), jout2, os.path.join(WORK, f'asr_report_turbo{tag}.txt')], check=True)
    print(open(os.path.join(WORK, f'asr_report_turbo{tag}.txt')).read())


# ---------------------------------------------------------------- 多音字/专名：与同音替身比 MFCC-DTW + F0 轮廓
# (句中片段, 原文字（字幕原文里的字）, 该句第几次出现(0 起), {读音: 替身字})。替身替换在"送去合成的文本"的同一位置
VARIANTS = [
    ('万壑松风', '壑', 0, {'hè': '贺', 'huò': '或'}),
    ('重新进入', '重', 0, {'chóng': '虫', 'zhòng': '众'}),
    ('侧锋横扫', '横', 0, {'héng': '恒', 'hēng': '亨'}),
    ('石头像被', '劈', 0, {'pī': '批', 'pǐ': '痞'}),
    ('石头像被', '劈', 1, {'pī': '批', 'pǐ': '痞'}),
    ('石头像被', '称', 0, {'chēng': '撑', 'chèn': '趁'}),
    ('石头像被', '皴', 0, {'cūn': '村', 'qūn': '逡'}),
    ('用得更干脆', '干', 0, {'gān': '甘', 'gàn': '赣'}),
    ('的上方', '踏', 0, {'tà': '榻', 'tā': '他'}),
    ('丰年', '踏', 0, {'tà': '榻', 'tā': '他'}),
    ('踏着节拍', '踏', 0, {'tà': '榻', 'tā': '他'}),
    ('左下的巨石', '斧', 0, {'fǔ': '府', 'fǒu': '否'}),
    ('笔越少', '笔', 0, {'bǐ': '比', 'bié': '别'}),
    ('宋宁宗', '宁', 0, {'níng': '凝', 'nìng': '泞'}),
    ('宿雨', '畿', 0, {'jī': '机', 'qí': '旗', 'jǐ': '挤'}),
    ('宿雨', '甸', 0, {'diàn': '电', 'tián': '田'}),
    ('宿雨', '朝', 0, {'zhāo': '招', 'cháo': '潮'}),
    ('宿雨', '丽', 0, {'lì': '利', 'lí': '离'}),
    ('丰年', '乐', 0, {'lè': '勒', 'yuè': '月'}),
    ('丰年', '行', 0, {'xíng': '形', 'háng': '航'}),
    ('田埂上', '几', 0, {'jǐ': '挤', 'jī': '机'}),
    ('左下的巨石', '石', 0, {'shí': '时', 'dàn': '蛋'}),
    ('左下的巨石', '劈', 0, {'pī': '批', 'pǐ': '痞'}),
    ('左下的巨石', '皴', 0, {'cūn': '村', 'qūn': '逡'}),
    ('树枝向下', '拖', 1, {'tuō': '托', 'tuó': '驼'}),
    ('树枝向下', '称', 0, {'chēng': '撑', 'chèn': '趁'}),
    ('一只小船', '只', 0, {'zhī': '支', 'zhǐ': '纸'}),
    ('剩下的', '空', 0, {'kòng': '控', 'kōng': '箜'}),
    ('人称马一角', '角', 0, {'jiǎo': '脚', 'jué': '决'}),
    ('人称马一角', '角', 1, {'jiǎo': '脚', 'jué': '决'}),
    ('人称马一角', '称', 0, {'chēng': '撑', 'chèn': '趁'}),
    ('传为马远', '传', 0, {'chuán': '船', 'zhuàn': '赚'}),
    ('传为马远', '为', 0, {'wéi': '维', 'wèi': '味'}),
    ('空白就是江水', '空', 0, {'kòng': '控', 'kōng': '箜'}),
    ('野水无人渡', '尽', 0, {'jìn': '进', 'jǐn': '紧'}),
    ('野水无人渡', '横', 0, {'héng': '恒', 'hēng': '亨'}),
    ('一只空船', '只', 0, {'zhī': '支', 'zhǐ': '纸'}),
    ('一只空船', '空', 0, {'kōng': '箜', 'kòng': '控'}),
    ('躺在船尾', '尾', 0, {'wěi': '委', 'yǐ': '以'}),
    ('一份答卷', '答', 0, {'dá': '达', 'dā': '搭'}),
    ('一份答卷', '卷', 0, {'juàn': '倦', 'juǎn': '捲'}),
    ('一整卷', '卷', 0, {'juàn': '倦', 'juǎn': '捲'}),
    ('一整卷', '只', 0, {'zhǐ': '纸', 'zhī': '支'}),
    ('只用线', '只', 0, {'zhǐ': '纸', 'zhī': '支'}),
    ('做待诏', '待', 0, {'dài': '代', 'dāi': '呆'}),
    ('做待诏', '诏', 0, {'zhào': '照', 'zhāo': '招'}),
    ('细笔勾的', '勾', 0, {'gōu': '沟', 'gòu': '够'}),
    ('几大笔泼墨', '只', 0, {'zhǐ': '纸', 'zhī': '支'}),
    ('几大笔泼墨', '几', 0, {'jǐ': '挤', 'jī': '机'}),
    ('釉面布满', '釉', 0, {'yòu': '又', 'yóu': '由'}),
    ('这叫开片', '片', 0, {'piàn': '骗', 'piān': '偏'}),
    ('釉和胎', '釉', 0, {'yòu': '又', 'yóu': '由'}),
    ('釉和胎', '胎', 0, {'tāi': '苔', 'tái': '台'}),
    ('釉和胎', '缩', 0, {'suō': '梭', 'sù': '素'}),
    ('只留最要紧', '只', 0, {'zhǐ': '纸', 'zhī': '支'}),
    # 第二版 s4 新句
    ('每一段的水', '都', 0, {'dōu': '兜', 'dū': '督'}),
    ('每一段的水', '段', 0, {'duàn': '断', 'duǎn': '短'}),
    ('其中一段', '中', 0, {'zhōng': '钟', 'zhòng': '众'}),
    ('其中一段', '逆', 0, {'nì': '腻', 'nǐ': '你'}),
    ('其中一段', '停', 0, {'tíng': '亭', 'tǐng': '挺'}),
]


def mfcc(x, sr=SR, n=13):
    x = np.append(x[0], x[1:] - 0.97 * x[:-1]); win = int(0.025 * sr); hop = int(0.01 * sr); nfft = 2048
    nf = 1 + max(0, (len(x) - win) // hop)
    idx = np.arange(win)[None, :] + hop * np.arange(nf)[:, None]
    P = np.abs(np.fft.rfft(x[idx] * np.hanning(win), nfft)) ** 2
    mel = lambda f: 2595 * np.log10(1 + f / 700); imel = lambda m: 700 * (10 ** (m / 2595) - 1)
    pts = imel(np.linspace(mel(80), mel(8000), 42)); bins = np.floor((nfft + 1) * pts / sr).astype(int)
    fb = np.zeros((40, nfft // 2 + 1))
    for m in range(1, 41):
        l, c, r = bins[m - 1], bins[m], bins[m + 1]
        fb[m - 1, l:c] = (np.arange(l, c) - l) / max(c - l, 1); fb[m - 1, c:r] = (r - np.arange(c, r)) / max(r - c, 1)
    E = np.log(P @ fb.T + 1e-10)
    k = np.arange(40); D = np.cos(np.pi / 40 * (k[None, :] + 0.5) * np.arange(n + 1)[:, None])
    C = E @ D.T
    C = C[:, 1:]; return (C - C.mean(0)) / (C.std(0) + 1e-6)


def dtw(a, b):
    D = np.sqrt(((a[:, None, :] - b[None, :, :]) ** 2).sum(-1))
    n, m = D.shape; acc = np.full((n + 1, m + 1), np.inf); acc[0, 0] = 0
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            acc[i, j] = D[i - 1, j - 1] + min(acc[i - 1, j], acc[i, j - 1], acc[i - 1, j - 1])
    return acc[n, m] / (n + m)


def f0_track(x, sr=SR, fmin=60, fmax=320):
    """逐 10 ms 的 F0（归一化自相关），清音帧为 nan。"""
    win, hop = int(0.04 * sr), int(0.01 * sr); lo, hi = int(sr / fmax), int(sr / fmin)
    nf = max(0, (len(x) - win) // hop + 1); out = np.full(nf, np.nan)
    for k in range(nf):
        fr = x[k * hop:k * hop + win].astype(np.float64); fr = fr - fr.mean()
        e = np.dot(fr, fr)
        if e < 1e-6: continue
        F = np.fft.rfft(fr, 2 * win); ac = np.fft.irfft(F * np.conj(F))[:win]
        seg = ac[lo:hi] / (ac[0] + 1e-12); j = int(np.argmax(seg))
        if seg[j] < 0.55: continue
        if 0 < j < len(seg) - 1:
            a, b, c = seg[j - 1], seg[j], seg[j + 1]; d = 0.5 * (a - c) / (a - 2 * b + c + 1e-12)
        else: d = 0.0
        out[k] = sr / (lo + j + d)
    return out


def contour(x, t0, t1, ref):
    """目标字时间段内的 F0 轮廓（半音，相对整句中位 F0），重采样到 8 点。"""
    f = f0_track(x[max(0, int(t0 * SR)):int(t1 * SR)])
    v = f[~np.isnan(f)]
    if len(v) < 3: return None
    st = 12 * np.log2(v / ref)
    return np.interp(np.linspace(0, len(st) - 1, 8), np.arange(len(st)), st)


def char_span(words, text_nopunct, pos):
    """第 pos 个汉字（去标点后）所在 WordBoundary 的时间段，按字数在词内均分。"""
    c = 0
    for w in words:
        t = re.sub(r'[^\u4e00-\u9fff]', '', w['text'])
        if c <= pos < c + len(t):
            per = w['d'] / max(len(t), 1); k = pos - c
            return w['t'] + k * per, w['t'] + (k + 1) * per
        c += len(t)
    raise KeyError(pos)


def variants(only=None):
    S = load_timing(); byi = {e['i']: e for e in S}
    ent = []; rows = []
    for (frag, ch, occ, alts) in VARIANTS:
        if only and not any(f in ANCHORS[sid(frag)][1] for f in only): continue
        i = sid(frag); e = byi[i]; tts = e['tts']
        tpos = [m.start() for m in re.finditer(ch, e['text'])][occ]       # 原文位置 = 合成文本位置（等长替换、空格→逗号）
        pos = len(re.sub(r'[^\u4e00-\u9fff]', '', tts[:tpos]))            # 去标点后的第几个汉字
        cur = tts[tpos]
        vs = [dict(i=i, ch=ch, occ=occ, rd=rd, pos=pos, rate=e['rate'], voice=VOICE,
                   tts=tts[:tpos] + sub + tts[tpos + 1:]) for rd, sub in alts.items()]
        ent += vs; rows.append((i, ch, occ, cur, vs))
    synth(ent)
    lines = []
    seg = lambda x, t0, t1: x[max(0, int((t0 - 0.06) * SR)):int((t1 + 0.06) * SR)]
    med = lambda x: np.nanmedian(f0_track(x))
    for (i, ch, occ, cur, vs) in rows:
        e = byi[i]
        base = decode(os.path.join(TTS, e['key'] + '.mp3')); bw = json.load(open(os.path.join(TTS, e['key'] + '.json')))['words']
        pos = vs[0]['pos']
        a0, a1 = char_span(bw, None, pos)
        fa = mfcc(seg(base, a0, a1)); res = []
        ca = contour(base, a0, a1, med(base))
        for v in vs:
            k = tkey(v); vx = decode(os.path.join(TTS, k + '.mp3')); vw = json.load(open(os.path.join(TTS, k + '.json')))['words']
            b0, b1 = char_span(vw, None, pos)
            cb = contour(vx, b0, b1, med(vx))
            dp = float(np.mean(np.abs(ca - cb))) if ca is not None and cb is not None else float('nan')
            res.append((dtw(fa, mfcc(seg(vx, b0, b1))), v['rd'], dp, cb))
        res.sort(key=lambda r: r[0])
        byp = min(res, key=lambda r: r[2] if r[2] == r[2] else 1e9)
        lines.append(f"句{i:2d} {ch}{'' if cur == ch else '→' + cur}#{occ}：频谱最像 {res[0][1]}，音高最像 {byp[1]}（" +
                     '，'.join(f'{r} 频谱 {d:.2f}/音高 {p:.1f}st' for d, r, p, _ in res) +
                     f"）原句轮廓 {'' if ca is None else ' '.join(f'{z:+.0f}' for z in ca)}  | {e['text']}")
    txt = '\n'.join(lines); open(os.path.join(WORK, 'variants_report_sel.txt' if only else 'variants_report.txt'), 'w').write(txt + '\n'); print(txt)


# ---------------------------------------------------------------- 混音
def ff_loud(path, extra=''):
    r = subprocess.run(['ffmpeg', '-nostats', '-i', path, '-af', f'{extra}ebur128=peak=true', '-f', 'null', '-'],
                       capture_output=True, text=True).stderr
    I = float(re.findall(r'I:\s+(-?[\d.]+) LUFS', r)[-1]); TP = float(re.findall(r'Peak:\s+(-?[\d.inf]+) dBFS', r)[-1])
    LRA = float(re.findall(r'LRA:\s+(-?[\d.]+) LU', r)[-1])
    return I, TP, LRA


def ff_series(path, key='S'):
    txt = os.path.join(WORK, f'ser_{key}.txt')
    subprocess.run(['ffmpeg', '-v', 'error', '-i', path, '-af',
                    f'ebur128=metadata=1,ametadata=print:key=lavfi.r128.{key}:file={txt}', '-f', 'null', '-'], check=True)
    return np.array([float(l.split('=')[1]) for l in open(txt) if f'lavfi.r128.{key}' in l])


def write_wav(path, x, ch):
    p = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'f32le', '-ar', str(SR), '-ac', str(ch), '-i', '-',
                          '-c:a', 'pcm_s24le', path], stdin=subprocess.PIPE)
    p.stdin.write(np.ascontiguousarray(x, np.float32).tobytes()); p.stdin.close(); assert p.wait() == 0


def read_wav(path, ch):
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', path, '-ac', str(ch), '-ar', str(SR), '-f', 'f32le', '-'],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).reshape(-1, ch).copy()


def backup(path):
    if os.path.exists(path):
        b = path + '.bak'
        if not os.path.exists(b): shutil.copy2(path, b)


def nch(s): return len(s.replace(' ', ''))


def split_parts(tx):
    """超 16 字在最居中的空格处拆开，拆出的部分仍超 16 字就继续拆（与北宋集 assemble.build_cues 同一拆法）。"""
    sp = [k for k, c in enumerate(tx) if c == ' ']
    if nch(tx) <= MAXCH or not sp: return [tx]
    k = min(sp, key=lambda k: abs(nch(tx[:k]) - nch(tx[k + 1:])))
    return split_parts(tx[:k]) + split_parts(tx[k + 1:])


def fmt_ts(t):
    ms = int(round(t * 1000)); h, ms = divmod(ms, 3600000); m, ms = divmod(ms, 60000); s, ms = divmod(ms, 1000)
    return f'{h:02d}:{m:02d}:{s:02d},{ms:03d}'


def write_srt(cues, path):
    with open(path, 'w', encoding='utf-8') as f:
        for i, (a, b, t) in enumerate(cues, 1):
            f.write(f'{i}\n{fmt_ts(a)} --> {fmt_ts(b)}\n{t}\n\n')


def sub_cues(S):
    """字幕条按语音对时：第 1 条 = 句起点（语音起点）；同一句拆开的后续条 = 其首字的 WordBoundary 时间 − 0.05 s；
    前一条结束于后一条开始前 0.1 s；句末条在语音结束后停 0.8 s（至少 1.6 s），不越过下一句开头前 0.25 s。"""
    cues = []
    for j, e in enumerate(S):
        parts = split_parts(e['text'])
        assert ''.join(p.replace(' ', '') for p in parts) == e['text'].replace(' ', ''), (e['text'], parts)
        nxt = S[j + 1]['start'] if j + 1 < len(S) else DUR - 1.0
        starts = [e['start']]; pos = 0
        for p in parts[:-1]:
            pos += len(re.sub(r'[^\u4e00-\u9fff]', '', p))
            t0, _ = char_span(e['words'], None, pos); starts.append(e['start'] + t0 - 0.05)
        for q, p in enumerate(parts):
            a = starts[q]
            b = starts[q + 1] - 0.1 if q + 1 < len(parts) else min(max(e['end'] + 0.8, a + 1.6), nxt - 0.25)
            cues.append((round(a, 3), round(b, 3), p))
    for (a, b, p), nx in zip(cues, cues[1:] + [(DUR, DUR, '')]):
        assert a < b <= nx[0] - 0.05, (a, b, p)
    return cues


def subs(S=None):
    S = S or load_timing()
    cues = sub_cues(S); backup(SRT); write_srt(cues, SRT)
    json.dump(cues, open(os.path.join(WORK, 'cues.json'), 'w'), ensure_ascii=False, indent=1)
    print(f'字幕 {len(cues)} 条 → {SRT}；最长 {max(nch(p) for _, _, p in cues)} 字；最短显示 {min(b - a for a, b, _ in cues):.2f}s')
    return cues


def mix(music):
    """music：本集配乐 wav 路径（整曲、已在字幕区压低的那一版，时长 ≥ DUR）。"""
    assert music and os.path.exists(music), f'需要本集配乐路径：python3 build_voice.py mix <music.wav>（{music}）'
    S = load_timing(); os.makedirs(OUTA, exist_ok=True)
    n = int(round(DUR * SR))
    # 1) 干声：逐句响度拉齐后放到时间线
    narr = np.zeros(n, np.float32); tmp = os.path.join(WORK, 'clip_tmp.wav')
    for e in S:
        f = analyse(e); c = f['clip']
        write_wav(tmp, c, 1); I, _, _ = ff_loud(tmp)
        c = c * np.float32(10 ** ((-19.0 - I) / 20))                     # 逐句先拉齐到 −19 LUFS（链路后整体再归一）
        a = int(round((e['start'] - f['lead']) * SR))
        assert a >= 0 and a + len(c) <= n, e['i']
        assert not np.any(narr[a:a + len(c)]), f"overlap at {e['i']}"
        narr[a:a + len(c)] = c; e['clip_a'] = a / SR; e['clip_b'] = (a + len(c)) / SR; e['I_raw'] = I
    raw = os.path.join(WORK, 'narr_raw.wav'); write_wav(raw, narr, 1); del narr
    # 2) 人声链：高通 → 去齿音 → 高频柔化 → 轻压缩（短时响度稳定）→ 双声道 → 归一到 −16 LUFS → 真峰值保险
    chain = ('highpass=f=75:p=2,deesser=i=0.35:m=0.5:f=0.45:s=o,highshelf=f=6500:g=-2.5:t=q:w=0.8,'
             'acompressor=threshold=0.089:ratio=2.2:attack=12:release=180:knee=4:makeup=1,pan=stereo|c0=c0|c1=c0')
    proc = os.path.join(WORK, 'narr_proc.wav')
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', raw, '-af', chain, '-ar', str(SR), '-c:a', 'pcm_f32le', proc], check=True)
    I, TP, _ = ff_loud(proc); g = VOICE_LUFS - I
    narr_out = os.path.join(OUTA, 'narration.wav'); backup(narr_out)
    for _ in range(2):                                   # 限幅会吃掉一点响度，第二遍补回
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', proc, '-af',
                        f'volume={g:.3f}dB,aresample=192000,alimiter=limit={10 ** (-1.5 / 20):.4f}:attack=3:release=60:level=false,aresample={SR}',
                        '-c:a', 'pcm_s24le', narr_out], check=True)
        I2, _, _ = ff_loud(narr_out); g += VOICE_LUFS - I2
        if abs(VOICE_LUFS - I2) < 0.1: break
    # 3) 配乐再让：人声句包络（起 0.4 s 在语音前压到位、句尾停 0.2 s 后 1.2 s 放回；句间 <2 s 合并不回升）
    zones = []
    for e in S:
        a, b = e['start'], e['end']
        if zones and a - zones[-1][1] < MERGE: zones[-1][1] = b
        else: zones.append([a, b])
    tt = np.arange(n) / SR; gdb = np.zeros(n, np.float32)
    for a, b in zones:
        i0, i1 = int((a - ATTACK) * SR), int((b + HOLD + RELEASE) * SR)
        t = tt[i0:i1]
        w = np.ones_like(t)
        up = t < a; w[up] = 0.5 - 0.5 * np.cos(np.pi * (t[up] - (a - ATTACK)) / ATTACK)
        dn = t > b + HOLD; w[dn] = 0.5 + 0.5 * np.cos(np.pi * (t[dn] - (b + HOLD)) / RELEASE)
        gdb[i0:i1] = np.minimum(gdb[i0:i1], DUCK_EXTRA * w)
    del tt
    mus = read_wav(music, 2)[:n]
    assert len(mus) == n, f'配乐短于 {DUR}s：{len(mus) / SR:.2f}s'
    mus *= (10 ** (gdb / 20))[:, None]; del gdb
    mus_out = os.path.join(OUTA, 'music_duck.wav'); backup(mus_out); write_wav(mus_out, mus, 2)
    # 4) 混音 + 真峰值限幅（4× 过采样）
    voc = read_wav(narr_out, 2)
    m = voc + mus; del voc, mus
    pre = os.path.join(WORK, 'mix_pre.wav'); write_wav(pre, m, 2); del m
    mix_out = os.path.join(OUTA, 'mix.wav'); backup(mix_out)
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', pre, '-af',
                    f'aresample=192000,alimiter=limit={TP_LIMIT:.4f}:attack=3:release=80:level=false,aresample={SR}',
                    '-c:a', 'pcm_s24le', mix_out], check=True)
    json.dump(S, open(os.path.join(WORK, 'timing.json'), 'w'), ensure_ascii=False, indent=1)
    # 5) 字幕
    subs(S)
    check(S, zones)


def check(S=None, zones=None):
    S = S or load_timing()
    narr, mus, mixp = (os.path.join(OUTA, f) for f in ('narration.wav', 'music_duck.wav', 'mix.wav'))
    for p in (narr, mus, mixp):
        d = float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'stream=duration,sample_rate,channels', '-of',
                                  'csv=p=0', p], capture_output=True, text=True).stdout.strip().split(',')[-1] or 0)
        I, TP, LRA = ff_loud(p)
        print(f"{os.path.basename(p):15s} 时长 {d:.3f}s  积分 {I:6.1f} LUFS  真峰值 {TP:5.1f} dBTP  LRA {LRA:4.1f} LU")
    # 人声短时响度（3 s）在说话段的分布
    Sv = ff_series(narr, 'S'); tt = np.arange(len(Sv)) * 0.1
    act = np.zeros(len(Sv), bool)
    for e in S: act |= (tt >= e['start'] + 1.5) & (tt <= e['end'])
    v = Sv[act & (Sv > -40)]
    print(f"人声短时响度（语音段内）：中位 {np.median(v):.1f}，P10 {np.percentile(v,10):.1f}，P90 {np.percentile(v,90):.1f} LUFS")
    # 逐句：不重叠、尾部能量（片段末 50 ms / 语音后 0.15–0.3 s）
    x = read_wav(narr, 1)[:, 0]; worst_tail, worst_after, gaps = -200, -200, []
    for j, e in enumerate(S):
        a, b = int(e['clip_a'] * SR), int(e['clip_b'] * SR)
        pk = 20 * np.log10(np.abs(x[a:b]).max() + 1e-9)
        tail = 20 * np.log10(np.sqrt(np.mean(x[b - 2400:b] ** 2)) + 1e-9) - pk
        aft = 20 * np.log10(np.sqrt(np.mean(x[int((e['end'] + 0.15) * SR):int((e['end'] + 0.3) * SR)] ** 2)) + 1e-9)
        worst_tail = max(worst_tail, tail); worst_after = max(worst_after, aft)
        if j + 1 < len(S): gaps.append(S[j + 1]['start'] - e['end'])
    print(f"句间隔最小 {min(gaps):.2f}s（要求 ≥{GAP_MIN}）；片段末 50 ms 能量最大 {worst_tail:.1f} dB（相对句峰值）；"
          f"语音后 0.15–0.3 s 最大 {worst_after:.1f} dBFS；合成原文件语音后余量最小 {min(e['tail_room'] for e in S):.2f}s；"
          f"末句结束 {S[-1]['end']:.2f}s")
    # 抽 4 段 10 s
    for t0 in (31.0, 81.0, 145.0, 253.0):
        seg = os.path.join(WORK, 'win.wav')
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', str(t0), '-t', '10', '-i', mixp, '-c:a', 'pcm_f32le', seg], check=True)
        I, TP, _ = ff_loud(seg); Sm = ff_series(seg, 'S'); Mm = ff_series(seg, 'M')
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', str(t0), '-t', '10', '-i', narr, '-c:a', 'pcm_f32le', seg], check=True)
        Iv, _, _ = ff_loud(seg)
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', str(t0), '-t', '10', '-i', mus, '-c:a', 'pcm_f32le', seg], check=True)
        Im, _, _ = ff_loud(seg)
        print(f"  {t0:5.0f}–{t0+10:.0f}s  混音 I {I:6.1f}  S最大 {Sm[30:].max():6.1f}  M最大 {Mm.max():6.1f} LUFS  真峰值 {TP:5.1f} dBTP"
              f"  | 人声 {Iv:6.1f} / 配乐 {Im:6.1f} LUFS")


if __name__ == '__main__':
    os.makedirs(WORK, exist_ok=True)
    cmd = sys.argv[1]
    if cmd == 'mix': mix(sys.argv[2] if len(sys.argv) > 2 else None)
    elif cmd in ('asr', 'variants'): {'asr': asr, 'variants': variants}[cmd](sys.argv[2:] or None)
    else: {'fit': fit, 'subs': subs, 'check': check}[cmd]()
