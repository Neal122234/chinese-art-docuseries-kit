"""留白转场用：踏歌全貌的墙面（s2 同一墙面/相机/调色，去掉立轴与它的投影），→ work/tage_wall.png"""
import os, sys, cv2
S2 = '/Users/mr.ni/claude-projects/china-art/series/ep02_nansong/segs/s2_tage'
sys.path.insert(0, S2); sys.path.insert(0, '/Users/mr.ni/claude-projects/china-art/series/lib')
import engine as E
import seg_s2
spec = seg_s2.build()
samples = [(seg_s2.SRC, [4900, 200, 7600, 1300]), (seg_s2.SRC, [3300, 4550, 5700, 5250])]
hs = E.hanging_scroll(seg_s2.SRC, 'tage', fill_h=0.94, samples=samples, shadow_strength=0.0)
seg = dict(spec['seg']); seg['layers'] = [hs['layers'][0]]; seg['fx'] = []; seg['camera'] = spec['shots']['A']
R = E.Renderer(seg, 720)
fr = R.render(0.0)
cv2.imwrite(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tage_wall.png'), cv2.cvtColor(fr, cv2.COLOR_RGB2BGR))
print('ok', fr.shape)
