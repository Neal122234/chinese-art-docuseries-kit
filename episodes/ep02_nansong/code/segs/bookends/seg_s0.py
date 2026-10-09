# -*- coding: utf-8 -*-
"""第二集 S0 片头（段窗口 = 全局 0–10 s，帧 0 = 0 s）。
暖暗绢底（北宋集同一块溪山空白绢，work/silk.npy 为 segs/bookends/work/silk.npy 的副本），镜头静止。
0–1.6 s 灯亮起（0.62→1）；0.7 s 起「南宋」按笔顺逐笔落墨（第一笔落下时一团淡墨沿绢丝洇开留水痕，同北宋集）；
小字「一一二七︱一二七九」、副题「留白」随后渗出；5.8–6.8 s 字收；6.8–10 s 纯绢（总装 7–9 s 叠入万壑松风全貌）。
渲染：lockf -k series/.heavy.lock python3 ep02_nansong/segs/bookends/run.py ep02_nansong/segs/bookends/seg_s0.py ep02_nansong/segs/seg_s0.mp4"""
import os

HERE = os.path.dirname(os.path.abspath(__file__))
SILK = os.path.join(HERE, 'work', 'silk.npy')      # 968×1720
C0 = dict(cx=860, cy=484, vh=880)
INK = '#1b1511'
OUT = [5.8, 6.8]


def build():
    fx = [
        {'type': 'tone', 'gain': [[0.0, 0.62], [1.6, 1.0]]},
        {'type': 'brush', 'text': '南宋', 'size': 118, 'weight': 'Regular', 'x': 0.640, 'y': 0.195,
         't0': 0.7, 'out': OUT, 'ink': INK, 'silk': 'silk', 'density': 0.95, 'seed': 3, 'speed': 5000, 'gap': 0.045},
        {'type': 'ink', 'text': '一一二七︱一二七九', 'size': 22, 'weight': 'Light', 'x': 0.516, 'y': 0.222, 'lead': 1.55,
         't0': 2.7, 'dur': 1.2, 'out': OUT, 'ink': INK, 'silk': 'silk', 'density': 0.9, 'order': 0.5, 'bleed': 0.07, 'seed': 4},
        {'type': 'ink', 'text': '留白', 'size': 40, 'weight': 'Light', 'x': 0.433, 'y': 0.395,
         't0': 3.3, 'dur': 1.4, 'out': OUT, 'ink': INK, 'silk': 'silk', 'density': 0.92, 'order': 0.45, 'seed': 6},
    ]
    return {
        'fps': 30, 'duration': 10.0,
        'layers': [{'name': 'silk', 'src': SILK, 'origin': [0, 0], 'unit': 1, 'cache_name': 'ep02_bookends_silk_s0'}],
        'camera': {'rest': C0, 'keys': [dict(t=0, **C0), dict(t=10.0, **C0)]},
        'fx': fx,
        'background': [110, 80, 52],
        'sharpen': 0.25,
    }
