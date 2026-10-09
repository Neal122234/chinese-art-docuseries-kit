import sys, json, numpy as np, cv2
sys.path.insert(0, '~/claude-projects/china-art/series/lib')
import scrollview as SV
QM = '~/claude-projects/china-art/series/segs/qingming/work/qm.npy'
XS = '~/claude-projects/china-art/trailer/assets_v3/xishan/work_full.npy'
sv = SV.ScrollView(QM, 'qingming', [(XS, [2400, 700, 4700, 3450])], res=int(sys.argv[2]), ss=1)
ims = []
for v in json.loads(sys.argv[1]):
    c = sv.fit(**v); print(v, {k: round(x) for k, x in c.items()})
    fr = sv.render(c); cv2.putText(fr, json.dumps(v), (6, 16), 0, 0.4, (255,255,255), 1); ims.append(fr)
while len(ims) % 2: ims.append(np.zeros_like(ims[0]))
g = np.vstack([np.hstack(ims[i:i+2]) for i in range(0, len(ims), 2)])
cv2.imwrite('~/claude-projects/china-art/series/segs/qingming/sv/var.jpg', cv2.cvtColor(g, cv2.COLOR_RGB2BGR))
