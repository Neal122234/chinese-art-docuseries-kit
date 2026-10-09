import sys, json, numpy as np, cv2
sys.path.insert(0, '~/claude-projects/china-art/series/lib')
import scrollview as SV
QM = '~/claude-projects/china-art/series/segs/qingming/work/qm.npy'
XS = '~/claude-projects/china-art/trailer/assets_v3/xishan/work_full.npy'
sv = SV.ScrollView(QM, 'qingming', [(XS, [2400, 700, 4700, 3450])], res=int(sys.argv[2]) if len(sys.argv)>2 else 360, ss=1)
W = sv.Wsrc
vs = json.loads(sys.argv[1]); ims = []
for v in vs:
    c = dict(tx=W * 0.62, ty=900, yaw=52.0, pitch=24.0, dist=W * 0.55, fov=34.0); c.update(v)
    for k in ('tx','dist'):
        if c[k] < 5: c[k] *= W
    fr = sv.render(c); cv2.putText(fr, json.dumps(v), (6, 16), 0, 0.4, (255,255,255), 1)
    ims.append(fr)
while len(ims) % 2: ims.append(np.zeros_like(ims[0]))
g = np.vstack([np.hstack(ims[i:i+2]) for i in range(0, len(ims), 2)])
cv2.imwrite('~/claude-projects/china-art/series/segs/qingming/sv/var.jpg', cv2.cvtColor(g, cv2.COLOR_RGB2BGR))
