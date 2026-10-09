# -*- coding: utf-8 -*-
# 【工具包说明】引擎示例段：溪山行旅图 立轴全貌 → 缓推 5 秒，演示 layers / flow / drift / fog 的写法。
# 输入：$CHINA_ART_ROOT/trailer/assets_v3/xishan/work_full.npy 与 series/spike/layers/*（大图，不在仓库里）；输出：mp4。
# 跑法：python3 engine/engine.py engine/demo_xishan.py demo.mp4（缺大图时只能读代码参考写法）。
"""示例段：溪山行旅图 立轴全貌（两侧真实绫墙）→ 缓推。5 秒。
渲染：lockf -k series/.heavy.lock python3 lib/engine.py lib/demo_xishan.py lib/demo.mp4"""
import engine as E

import os
_ROOT = os.environ.get('CHINA_ART_ROOT', '~/claude-projects/china-art')
SRC = os.path.join(_ROOT, 'trailer/assets_v3/xishan/work_full.npy')   # 24176×11105，整轴含裱
SPK = os.path.join(_ROOT, 'series/spike/layers/')
# spike 分层在 P2 坐标（画心 ds2）；P2 像素 (x,y) 左上角 = 源图 (560+2x, 3628+2y)
P2O = (560, 3628)
def p2w(x, y):
    return [P2O[0] + 2 * x, P2O[1] + 2 * y]
PAINT = [560, 3628, 560 + 2 * 4975, 3628 + 2 * 9956]          # 画心在源图中的矩形


def build():
    hs = E.hanging_scroll(SRC, 'xishan', fill_h=0.94)
    full = hs['full']
    layers = hs['layers'] + [
        # 画心分层（spike）：far=补过洞的整幅画心，cliff/mid/near 带 alpha；近景略快（视差 + 推拉视差）
        {'name': 'far', 'src': SPK + 'far.npy', 'origin': p2w(-640, -640), 'unit': 2, 'crop': PAINT, 'feather': 80,
         'cache_name': 'xishan_far'},
        {'name': 'cliff', 'src': SPK + 'cliff.npy', 'origin': p2w(-640, 3930), 'unit': 2, 'par': 1.004, 'zpar': 0.01,
         'cache_name': 'xishan_cliff'},
        {'name': 'mid', 'src': SPK + 'mid.npy', 'origin': p2w(-640, 6074), 'unit': 2, 'par': 1.01, 'zpar': 0.03,
         'cache_name': 'xishan_mid'},
        {'name': 'near', 'src': SPK + 'near.npy', 'origin': p2w(-640, 8667), 'unit': 2, 'par': 1.02, 'zpar': 0.06,
         'cache_name': 'xishan_near'},
    ]
    push = dict(cx=full['cx'], cy=full['cy'] - 900, vh=full['vh'] / 1.12)
    return {
        'fps': 30, 'duration': 5.0,
        'layers': layers,
        'camera': {'rest': full, 'keys': [dict(t=0, **full), dict(t=1.5, **full), dict(t=5.0, ease=1.2, **push)]},
        'fx': [
            # 主峰右侧细瀑：原画像素沿水线向下流
            {'type': 'flow', 'layer': 'far', 'mask': SPK + 'wf_mask.npy', 'origin': p2w(3950, 3200), 'unit': 2,
             'dir': [0, 1], 'speed': 90, 'period': 60, 'streak': 16},
            # 主峰脚下的烟霞带：真实雾/绢像素，缓慢漂移、轻微升降
            {'type': 'fog', 'after': 'cliff', 'par': 1.006, 'zpar': 0.02,
             'tex': {'src': SRC, 'rect': [2800, 15200, 2600, 1300], 'ds': 4},
             'band': [560, 15000, 10510, 16700], 'feather': 450, 'drift': [14, 0], 'rise': [40, 9], 'opacity': 0.32},
            # 驮队：刚体极缓左移（远小于一个身长）
            {'type': 'drift', 'layer': 'mid', 'sprite': SPK + 'caravan.npy', 'origin': p2w(3665, 8615), 'unit': 2,
             'path': [[0, 0, 0], [5, -30, 0]], 'body': 120, 'cache_name': 'xishan_caravan'},
        ],
        'labels': [
            {'text': ['谿山行旅圖', '北宋　范寬', '絹本淺設色', '二〇六·三×一〇三·三厘米', '臺北故宮博物院藏'],
             'x': 0.865, 'y': 0.14, 't0': 0.3, 't1': 4.6, 'fade': 0.9, 'color': '#2b251d'},
        ],
        'grade': {'gamma': 0.9, 'gain': 1.03},
        'sharpen': 0.25,
    }
