import sys, time, json, numpy as np, cv2
sys.path.insert(0, '~/claude-projects/china-art/series/lib')
import scrollview as SV, engine as E
QM = '~/claude-projects/china-art/series/segs/qingming/work/qm.npy'
XS = '~/claude-projects/china-art/trailer/assets_v3/xishan/work_full.npy'
SILK = [(XS, [2400, 700, 4700, 3450])]
res = int(sys.argv[1]); ss = int(sys.argv[2]); ts = [float(x) for x in sys.argv[3].split(',')]
cams = json.loads(sys.argv[4]) if len(sys.argv) > 4 else None
sv = SV.ScrollView(QM, 'qingming', SILK, tone=(0.84, 0.80, 0.71), res=res, ss=ss)
sh = SV.overview_shot(sv, 8.5, 13.6, 18.2, {'cx': 37250, 'cy': 897, 'vh': 2190}, light_sweep=(9.2, 13.0, 5000, 0.42))
if cams:
    for k, v in cams.items(): setattr(sh, k, dict(getattr(sh, k), **v))
for t in ts:
    t0 = time.time(); fr = sh.frame(t)
    cv2.imwrite(f'~/claude-projects/china-art/series/segs/qingming/sv/t_{t:05.2f}.jpg', cv2.cvtColor(fr, cv2.COLOR_RGB2BGR), [cv2.IMWRITE_JPEG_QUALITY, 88])
    print(t, round(time.time() - t0, 2), 's', flush=True)
