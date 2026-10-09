# 【工具包说明】ASR 复核①：faster-whisper base 逐句把合成语音转写回文字，供 pinyin_cmp.py 与原文比拼音。
# 输入：build_voice.py asr 写的 in.json（每句 wav 路径）；输出：out.json（每句加 asr 字段）。离线（HF_HUB_OFFLINE=1），模型须先下载到 HF 缓存。
# 跑法：$ASR_PY asr_whisper.py in.json out.json [模型名，缺省 base]（通常由 build_voice.py asr 调用）。
"""faster-whisper base（small 的本地缓存缺 model.bin）（CTranslate2 int8，CPU）逐句转写。用法：/opt/anaconda3/bin/python asr_whisper.py in.json out.json"""
import json, os, sys
os.environ.setdefault("HF_HUB_OFFLINE", "1")
from faster_whisper import WhisperModel
items = json.load(open(sys.argv[1]))
m = WhisperModel(sys.argv[3] if len(sys.argv) > 3 else 'base', device='cpu', compute_type='int8', cpu_threads=4)
out = []
for it in items:
    segs, _ = m.transcribe(it['wav'], language='zh', beam_size=5, initial_prompt='以下是普通话的句子。',
                           condition_on_previous_text=False, vad_filter=False)
    it['asr'] = ''.join(s.text for s in segs).strip()
    print(it['i'], it['asr'], flush=True)
    out.append(it)
json.dump(out, open(sys.argv[2], 'w'), ensure_ascii=False, indent=1)
