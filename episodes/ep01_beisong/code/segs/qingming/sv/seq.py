import sys, numpy as np, cv2
sys.path.insert(0, '~/claude-projects/china-art/series/lib')
import scrollview as SV
QM = '~/claude-projects/china-art/series/segs/qingming/work/qm.npy'
XS = '~/claude-projects/china-art/trailer/assets_v3/xishan/work_full.npy'
sv = SV.ScrollView(QM, 'qingming', [(XS, [2400, 700, 4700, 3450])], res=int(sys.argv[1]), ss=1)
sh = SV.overview_shot(sv, 8.5, float(sys.argv[3]), 18.2, {'cx': 37250, 'cy': 897, 'vh': 2190}, light_sweep=(9.3, 13.2, 5000, 0.45))
print('glide', SV.speed_report(sh, 8.5, sh.t_glide)); print('swoop', SV.speed_report(sh, sh.t_glide, 18.2))
ts = [float(x) for x in sys.argv[2].split(',')]; ims = []
for t in ts:
    fr = sh.frame(t); cv2.putText(fr, f'{t}', (6, 16), 0, 0.45, (255,255,255), 1); ims.append(fr)
while len(ims) % 3: ims.append(np.zeros_like(ims[0]))
g = np.vstack([np.hstack(ims[i:i+3]) for i in range(0, len(ims), 3)])
cv2.imwrite('~/claude-projects/china-art/series/segs/qingming/sv/seq.jpg', cv2.cvtColor(g, cv2.COLOR_RGB2BGR))
