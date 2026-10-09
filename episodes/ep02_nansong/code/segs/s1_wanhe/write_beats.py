# 从 seg_s1.py 的时间表 + 渲染日志里的斧落点写 beats.json（全局秒）。用法：python3 write_beats.py render.log
import sys, os, re, json, ast
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import seg_s1 as G
g = lambda t: round(G.T_GLOBAL0 + t, 2)
beats = []
if len(sys.argv) > 1:
    m = re.search(r'斧落点 (\[.*?\])', open(sys.argv[1]).read())
    if m:
        beats = [g(x) for x in ast.literal_eval(m.group(1))]
out = {
    'segment': 'S1 李唐《万壑松风图》',
    'file': os.path.abspath(os.path.join(HERE, '..', 'seg_s1.mp4')),
    'frame0_global_s': G.T_GLOBAL0, 'duration_s': G.DUR,
    'window_rule': '7–9 全貌静止（总装从绢底叠入）；49–56 全貌静止（雾转场底画），相机与 7 s 时完全相同',
    'picture_events_global_s': {
        'full_view_static(hanging scroll on silk wall)': [g(0), g(G.T_READ[0])],
        'label_on': [g(1.5), g(9.8)],
        'read_slow_push_to_main_peak(1.36x)': [g(G.T_READ[0]), g(G.T_READ[1])],
        'veil1_clouds_cross(full->cliff)': [g(G.VEIL1[0]), g(G.VEIL1[2])],
        'cliff_closeup_pale_underpainting(light ink only)': [g(G.XF1[1]), g(G.T_AXE[0])],
        'cliff_slow_push': [g(G.T_PUSHC[0]), g(G.T_PUSHC[1])],
        'HIGHLIGHT_axe_cut_strokes(dark ink lands facet by facet along brush axis, press on landing)': [g(G.T_AXE[0]), g(G.T_AXE[1])],
        'veil2_clouds_cross(cliff->waterfall)': [g(G.VEIL2[0]), g(G.VEIL2[2])],
        'HIGHLIGHT_waterfall_flowing + cloud_drift_over_pines': [g(G.XF2[1]), g(G.XF3[0])],
        'veil3_clouds_cross(waterfall->near full)': [g(G.VEIL3[0]), g(G.VEIL3[2])],
        'pull_back_to_full': [g(G.T_BACK[0]), g(G.T_BACK[1])],
        'full_view_static_end(fog transition base)': [g(G.T_BACK[1]), g(G.DUR)],
    },
    'axe_landings_in_view_global_s': beats,
    'subtitle_anchors_global_s': {
        '一一二四年 北宋画院的李唐 画下了《万壑松风图》': 9.5, '三年后 金兵攻破汴京 北宋灭亡': 16,
        '李唐渡江南下 到了临安 重新进入画院': 21, '他把一种笔法带到了南宋 用侧锋横扫': 31,
        '石头像被斧头劈开一样 人称斧劈皴': 36, '南宋的山水 从这里开始': 46},
}
json.dump(out, open(os.path.join(HERE, 'beats.json'), 'w'), ensure_ascii=False, indent=1)
print(json.dumps(out, ensure_ascii=False)[:400])
