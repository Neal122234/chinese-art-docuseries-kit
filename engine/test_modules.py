# -*- coding: utf-8 -*-
# 【工具包说明】模块近景自检段：用 demo_xishan 的素材，近景看 flow（瀑布）/ drift（驼队）/ fog（雾吞没）。
# 输入：同 demo_xishan.py；环境变量 VIEW=caravan|fall|engulf 选视角；输出：抽帧 png。
# 跑法：VIEW=fall python3 engine/engine.py engine/test_modules.py tm.png --stills 0,60
"""模块自检段（近景看 flow / drift / fog）。VIEW=caravan|fall|engulf
  VIEW=fall lockf -k series/.heavy.lock python3 lib/engine.py lib/test_modules.py lib/review/tm.png --stills 0,60"""
import os
import demo_xishan as D

VIEWS = {
    'caravan': dict(cx=8700, cy=21000, vh=1500),
    'fall': dict(cx=8900, cy=13200, vh=3000),
    'engulf': dict(cx=5552, cy=16500, vh=6000),
}


def build():
    seg = D.build()
    v = os.environ.get('VIEW', 'caravan')
    st = VIEWS[v]
    seg['camera'] = {'rest': st, 'keys': [dict(t=0, **st), dict(t=4, **st)]}
    seg['duration'] = 4.0
    seg['labels'] = []
    if v == 'engulf':
        seg['fx'].append({'type': 'fog', 'mode': 'screen', 'after': '__top__',
                          'tex': {'src': D.SRC, 'rect': [2800, 15200, 2600, 1300], 'ds': 2}, 'scale': 1.1,
                          'drift': [0.01, -0.02], 'opacity': 0.0, 'lighten': 1.12,
                          'cover': [[0, 0.0], [2, 0.55], [4, 1.0]]})
    return seg
