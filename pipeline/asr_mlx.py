# 【工具包说明】ASR 复核②：mlx-whisper large-v3-turbo（Apple Silicon）逐句转写，与 base 结果互相印证读音。
# 输入：in.json（每句 wav）；输出：out.json（加 asr 字段）。离线，须先下载 mlx-community/whisper-large-v3-turbo 到 HF 缓存。
# 跑法：$ASR_PY asr_mlx.py in.json out.json（通常由 build_voice.py asr 调用）。
"""mlx-whisper large-v3-turbo（本地缓存）逐句转写，复核用。用法：/opt/anaconda3/bin/python asr_mlx.py in.json out.json"""
import json, os, sys
os.environ.setdefault("HF_HUB_OFFLINE", "1")
import mlx_whisper
items = json.load(open(sys.argv[1])); out = []
for it in items:
    r = mlx_whisper.transcribe(it['wav'], path_or_hf_repo='mlx-community/whisper-large-v3-turbo', language='zh',
                               initial_prompt='以下是普通话的句子。', condition_on_previous_text=False, verbose=None)
    it['asr'] = r['text'].strip(); print(it['i'], it['asr'], flush=True); out.append(it)
json.dump(out, open(sys.argv[2], 'w'), ensure_ascii=False, indent=1)
