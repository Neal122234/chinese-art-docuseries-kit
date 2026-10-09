# 【工具包说明】读音核对：ASR 回写与原文都转成去声调拼音（数字先转汉字），逐句列出不一致处。
# 输入：asr_*.py 的 out.json；输出：report.txt（OK/DIF + 差异片段，末行为不一致句数）。
# 跑法：$TTS_PY pinyin_cmp.py asr_out.json report.txt（需 pypinyin；通常由 build_voice.py asr 调用）。
"""ASR 回写与原文按拼音（去声调）比对，列出不一致处。用法：.venv/bin/python pinyin_cmp.py asr_out.json report.txt"""
import difflib, json, re, sys
from pypinyin import lazy_pinyin, Style

D = '零一二三四五六七八九'
def num2cn(s):
    def rep(m):
        t = m.group(0); nxt = m.string[m.end():m.end() + 1]
        if len(t) == 4 and nxt == '年': return ''.join(D[int(c)] for c in t)
        n = int(t)
        if n < 10: return D[n]
        if n < 100: return ('' if n // 10 == 1 else D[n // 10]) + '十' + (D[n % 10] if n % 10 else '')
        if n < 1000: return D[n // 100] + '百' + (('零' + D[n % 100]) if 0 < n % 100 < 10 else (num2cn(str(n % 100)) if n % 100 else ''))
        return ''.join(D[int(c)] for c in t)
    return re.sub(r'\d+', rep, s)

def hz(s): return re.sub(r'[^一-鿿]', '', num2cn(s))
def py(s): return lazy_pinyin(s, style=Style.NORMAL, v_to_u=True)

rows = []; bad = 0
for it in json.load(open(sys.argv[1])):
    a, b = hz(it['text']), hz(it['asr'])
    pa, pb = py(a), py(b)
    sm = difflib.SequenceMatcher(a=pa, b=pb, autojunk=False)
    diffs = [(a[i1:i2], b[j1:j2]) for op, i1, i2, j1, j2 in sm.get_opcodes() if op != 'equal']
    flag = 'OK ' if not diffs else 'DIF'
    bad += bool(diffs)
    rows.append(f"{flag} {it['i']:2d} 原文 {a}\n       回写 {b}" + ('' if not diffs else '\n       差异 ' + '；'.join(f'{x or "∅"}→{y or "∅"}' for x, y in diffs)))
rows.append(f'拼音不一致的句：{bad}')
open(sys.argv[2], 'w').write('\n'.join(rows) + '\n')
