# -*- coding: utf-8 -*-
"""第二集 S7 结尾（段窗口 = 全局 278–296 s，帧 0 = 278 s）。
278–284 纯绢底静止（总装在此把官窑全器淡为绢底）；284 起镜头极缓推近（约 0.8%/s，不旋转）。
284.6 起五个竖排小字依次出现（间隔 0.8 s）：每个字的「一」先按笔锋一笔横写落墨（起笔处淡墨洇开），
随后第二个字渗进绢里——「一角」「一诗」「一水」「一墨」「一裂」，合旁白 286「南宋人 只留最要紧的一笔」。
290.6 起「下一章　元」渗出；293.2–295.6 字淡去；292 起灯暗下（到 0.42，不到纯黑）。
渲染：lockf -k series/.heavy.lock python3 ep02_nansong/segs/bookends/run.py ep02_nansong/segs/bookends/seg_s7.py ep02_nansong/segs/seg_s7.mp4"""
import os

HERE = os.path.dirname(os.path.abspath(__file__))
SILK = os.path.join(HERE, 'work', 'silk.npy')      # 968×1720
T0 = 278.0                                          # 段窗口起点（全局秒）
C0 = dict(cx=860, cy=484, vh=880)
C1 = dict(cx=860, cy=470, vh=880 / 1.11)           # t=19.5（窗口外）
INK = '#1b1511'
SIZE, LEAD = 42, 1.16
WORDS = ['一角', '一诗', '一水', '一墨', '一裂']
W0, DW = 284.6, 0.8                                 # 第一字起笔（全局），间隔
OUT = [293.2 - T0, 295.6 - T0]


def build():
    fx = []
    for i, w in enumerate(WORDS):
        x, y = 0.676 - i * 0.076, 0.205 + i * 0.042
        tb = W0 + DW * i - T0
        # 「一」：一笔横写（笔锋从左到右约 0.55 s，起笔处淡墨洇开）
        fx.append({'type': 'brush', 'text': w[0], 'size': SIZE, 'weight': 'Regular', 'x': x, 'y': y,
                   't0': tb, 'out': OUT, 'ink': INK, 'silk': 'silk', 'density': 0.93, 'seed': 40 + i,
                   'speed': 1500, 'gap': 0.0, 'bloom': 0.42, 'bloom_gain': 0.5, 'halo': 0.2})
        # 第二个字：紧接着渗进绢里（与「一」同一列、下一格）
        fx.append({'type': 'ink', 'text': w[1], 'size': SIZE, 'weight': 'Regular', 'x': x, 'y': y + SIZE * LEAD / 720,
                   't0': tb + 0.50, 'dur': 1.3, 'out': OUT, 'ink': INK, 'silk': 'silk', 'density': 0.9,
                   'order': 0.4, 'seed': 20 + i})
    fx.append({'type': 'ink', 'text': '下一章　元', 'size': 24, 'weight': 'Light', 'x': 0.296, 'y': 0.515,
               't0': 290.6 - T0, 'dur': 1.6, 'out': OUT, 'ink': INK, 'silk': 'silk', 'density': 0.88, 'order': 0.5, 'seed': 30})
    fx.append({'type': 'tone', 'gain': [[0, 1.0], [292.0 - T0, 1.0], [295.95 - T0, 0.42]]})
    return {
        'fps': 30, 'duration': 18.0,
        'layers': [{'name': 'silk', 'src': SILK, 'origin': [0, 0], 'unit': 1, 'cache_name': 'ep02_bookends_silk_s7'}],
        'camera': {'rest': C0, 'keys': [dict(t=0, **C0), dict(t=284.0 - T0, **C0), dict(t=19.5, ease=1.5, **C1)]},
        'fx': fx,
        'background': [110, 80, 52],
        'sharpen': 0.25,
    }
