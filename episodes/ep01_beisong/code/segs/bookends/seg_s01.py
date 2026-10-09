# -*- coding: utf-8 -*-
"""S0 片头 + S1 夜宴引子（全局 0:00–0:22，帧 0 = 0:00）。
世界坐标 = 夜宴图听乐段文件像素（文件 x = 原图 x − 63500）。
S0：暖暗绢底（溪山空白绢真实像素）上墨字渗出「北宋」「九六〇—一一二七」「看得真」→ 字收 → 夜宴从绢里浮现（2 s 叠化）
S1：人物占满画面 → 一次极缓推出（约 3.2%/s，锚点在琵琶女左侧，右边逐渐露出榻上的韩熙载），0:22 仍在匀速推出（雾转场由总装做）。
渲染：lockf -k series/.heavy.lock python3 segs/bookends/run.py segs/bookends/seg_s01.py segs/seg_s01.mp4"""
import os
import numpy as np
import engine as E

HERE = os.path.dirname(os.path.abspath(__file__))
YEYAN = '~/claude-projects/china-art/trailer/assets_v3/yeyan/work_listen_16000x3981.rgb'
SILK = os.path.join(HERE, 'work', 'silk.npy')        # 968×1720，溪山主峰左上空白绢，已调暖暗
SILK_VH = 880                                         # 绢底一屏高 = 880 个真实绢像素（720p ≈1.2:1，1080p ≈0.8:1）

C0 = dict(cx=7250, cy=1600, vh=2700)                  # 起：琵琶女、听众、侍立者占满画面
C1 = dict(cx=8580, cy=2000, vh=4010)                  # 终（t=23.6，窗口外）：t=22 时 vh≈3920，左琵琶女、右榻上韩熙载都在画内
T_MOVE0, T_MOVE1 = 7.2, 23.6

INK = '#1b1511'
OUT = [5.4, 6.5]                                      # 字收
XF = [6.6, 8.6]                                       # 夜宴从绢里浮现


def build():
    yeyan = np.memmap(YEYAN, np.uint8, 'r', shape=(3981, 16000, 3))
    unit = C0['vh'] / SILK_VH
    sh, sw = 968, 1720
    silk_origin = [C0['cx'] - sw / 2 * unit, C0['cy'] - sh / 2 * unit]
    layers = [
        {'name': 'silk', 'src': SILK, 'origin': silk_origin, 'unit': unit, 'cache_name': 'bookends_silk_s01'},
        {'name': 'yeyan', 'src': yeyan, 'origin': [0, 0], 'unit': 1, 'cache_name': 'yeyan_listen',
         'opacity': [[XF[0], 0.0], [XF[1], 1.0]]},
    ]
    fx = [
        {'type': 'tone', 'gain': [[0.0, 0.62], [1.6, 1.0]]},                    # 灯亮起（不从纯黑开始）
        # 落墨：「北宋」按笔顺一笔一笔写出（0.7–约 2.9 s），第一笔落下时一团淡墨沿绢丝洇开
        {'type': 'brush', 'text': '北宋', 'size': 118, 'weight': 'Regular', 'x': 0.640, 'y': 0.195,
         't0': 0.7, 'out': OUT, 'ink': INK, 'silk': 'silk', 'density': 0.95, 'seed': 3, 'speed': 5000, 'gap': 0.045},
        {'type': 'ink', 'text': '九六〇︱一一二七', 'size': 22, 'weight': 'Light', 'x': 0.516, 'y': 0.228,
         't0': 2.5, 'dur': 1.2, 'out': OUT, 'ink': INK, 'silk': 'silk', 'density': 0.9, 'order': 0.5, 'bleed': 0.07, 'seed': 4},
        {'type': 'ink', 'text': '看得真', 'size': 40, 'weight': 'Light', 'x': 0.433, 'y': 0.395,
         't0': 3.0, 'dur': 1.4, 'out': OUT, 'ink': INK, 'silk': 'silk', 'density': 0.92, 'order': 0.45, 'seed': 6},
    ]
    return {
        'fps': 30, 'duration': 22.0,
        'layers': layers,
        'camera': {'rest': C0, 'keys': [dict(t=0, **C0), dict(t=T_MOVE0, **C0), dict(t=T_MOVE1, ease=1.5, **C1)]},
        'fx': fx,
        'labels': [
            {'text': ['韓熙載夜宴圖︵局部︶', '五代　顧閎中︵傳︶', '北京故宮博物院藏'],
             'world': [5545, 300], 't0': 9.0, 't1': 15.4, 'fade': 0.8, 'color': '#EAE1CF',
             'title_size': 22, 'size': 19},
        ],
        'background': [110, 80, 52],
        'sharpen': 0.25,
    }
