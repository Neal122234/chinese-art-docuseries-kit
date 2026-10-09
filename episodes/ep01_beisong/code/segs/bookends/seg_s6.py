# -*- coding: utf-8 -*-
"""S6 结尾（渲染窗口 = 全局 4:37–4:52，帧 0 = 4:37）。
0–3 s 纯绢底（与片头同一块溪山空白绢，供总装与 S5 全器叠化）；
4:40.3 起竖排墨字依次渗出「真山」「人间」「青绿」「天青」（间隔 0.8 s）；4:45.6 「下一章　南宋」；
4:49 起字淡去、灯暗下（绢仍可见，不到纯黑）。镜头 4:40 起极缓推近（约 0.8%/s），不旋转。
渲染：lockf -k series/.heavy.lock python3 segs/bookends/run.py segs/bookends/seg_s6.py segs/seg_s6.mp4"""
import os
import engine as E

HERE = os.path.dirname(os.path.abspath(__file__))
SILK = os.path.join(HERE, 'work', 'silk.npy')     # 968×1720
C0 = dict(cx=860, cy=484, vh=880)
C1 = dict(cx=860, cy=470, vh=880 / 1.11)          # t=16.5（窗口外）
INK = '#1b1511'
OUT = [12.0, 14.0]


def build():
    words = ['真山', '人间', '青绿', '天青']
    fx = []
    for i, w in enumerate(words):
        fx.append({'type': 'ink', 'text': w, 'size': 34, 'weight': 'Regular', 'x': 0.622 - i * 0.072, 'y': 0.235 + i * 0.045,
                   't0': 3.3 + 0.8 * i, 'dur': 1.4, 'out': OUT, 'ink': INK, 'silk': 'silk', 'density': 0.9,
                   'order': 0.4, 'seed': 20 + i})
    fx.append({'type': 'ink', 'text': '下一章　南宋', 'size': 24, 'weight': 'Light', 'x': 0.316, 'y': 0.47,
               't0': 8.6, 'dur': 1.8, 'out': OUT, 'ink': INK, 'silk': 'silk', 'density': 0.86, 'order': 0.5, 'seed': 30})
    fx.append({'type': 'tone', 'gain': [[0, 1.0], [12.0, 1.0], [14.6, 0.52]]})
    return {
        'fps': 30, 'duration': 15.0,
        'layers': [{'name': 'silk', 'src': SILK, 'origin': [0, 0], 'unit': 1, 'cache_name': 'bookends_silk_s6'}],
        'camera': {'rest': C0, 'keys': [dict(t=0, **C0), dict(t=3.0, **C0), dict(t=16.5, ease=1.5, **C1)]},
        'fx': fx,
        'background': [110, 80, 52],
        'sharpen': 0.25,
    }
