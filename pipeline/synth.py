# 【工具包说明】edge-tts 逐句合成（联网，微软在线 TTS），按 (voice, rate, pitch, 文本) 哈希缓存 mp3 + 字词时间戳 json。
# 输入：plan.json（build_voice.py 写）；输出：$TTS_DIR/<hash>.mp3 + <hash>.json。
# TTS_DIR 由 build_voice.py 通过环境变量传入；单独跑时缺省 $EP_DIR/voice/work/tts（EP_DIR 缺省本机 series/ep02_nansong）。
# 跑法：$TTS_PY synth.py plan.json（TTS_PY = 装了 edge-tts 的 python，见 scripts/bootstrap.sh）。
"""edge-tts 逐句合成（在 voice/.venv 里跑）。读 work/plan.json 的每句 {i, tts, rate, pitch, voice}，
按 (voice, rate, pitch, tts) 的哈希缓存到 work/tts/<hash>.mp3 + <hash>.json（WordBoundary：offset/duration 秒 + text）。
用法：.venv/bin/python synth.py work/plan.json
"""
import asyncio, hashlib, json, os, sys
import edge_tts

HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.environ.get('CHINA_ART_ROOT', '~/claude-projects/china-art')
_EP = os.environ.get('EP_DIR', os.path.join(_ROOT, 'series', 'ep02_nansong'))
TTS = os.environ.get('TTS_DIR', os.path.join(_EP, 'voice', 'work', 'tts'))   # 原为本文件旁的 work/tts


def key(s):
    return hashlib.sha1(f"{s['voice']}|{s['rate']}|{s['pitch']}|{s['tts']}".encode()).hexdigest()[:16]


async def one(s, sem):
    k = key(s); mp3 = os.path.join(TTS, k + '.mp3'); js = os.path.join(TTS, k + '.json')
    if os.path.exists(mp3) and os.path.exists(js): return k, False
    async with sem:
        for attempt in range(4):
            try:
                c = edge_tts.Communicate(s['tts'], s['voice'], rate=s['rate'], pitch=s['pitch'], boundary='WordBoundary')
                audio = bytearray(); wb = []
                async for ch in c.stream():
                    if ch['type'] == 'audio': audio += ch['data']
                    elif ch['type'] == 'WordBoundary':
                        wb.append(dict(t=ch['offset'] / 1e7, d=ch['duration'] / 1e7, text=ch['text']))
                if not audio: raise RuntimeError('empty audio')
                with open(mp3 + '.part', 'wb') as f: f.write(audio)
                os.replace(mp3 + '.part', mp3)
                json.dump(dict(s, key=k, words=wb), open(js, 'w'), ensure_ascii=False, indent=1)
                return k, True
            except Exception as e:
                print(f"  retry {s['i']} ({e})", flush=True); await asyncio.sleep(2 + attempt * 2)
        raise RuntimeError(f"synth failed: {s['i']}")


async def main(plan):
    os.makedirs(TTS, exist_ok=True)
    P = json.load(open(plan))
    sem = asyncio.Semaphore(4)
    res = await asyncio.gather(*[one(s, sem) for s in P])
    print(f'synth: {len(res)} 句，新合成 {sum(n for _, n in res)}', flush=True)


if __name__ == '__main__':
    asyncio.run(main(sys.argv[1]))
