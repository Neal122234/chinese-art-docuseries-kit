import sys, os, numpy as np, cv2
S = '~/claude-projects/china-art/series/'
C = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, S + 'lib'); sys.path.insert(0, S + 'segs/qingming'); sys.path.insert(0, S + 'segs/qianli')
import engine as E
os.chdir(S + 'segs/qingming'); import s3
R = E.Renderer(s3.mask_seg(), 1080); i = 2280; w = s3.weight('E', i / 30)
m = np.clip(R.render(i / 30).astype(np.float32) * w + 0.5, 0, 255).astype(np.uint8)
cv2.imwrite(C + '/s3m_f2280.png', m)
os.chdir(S + 'segs/qianli'); import render_v1 as V1
R = E.Renderer(dict(V1.seg_A_mask(), ss=1), 1080); i = 120
m = R.render(i / 30)            # t<8 → wa = 1
cv2.imwrite(C + '/s4m_f0120.png', m)
for a, b in (('s3m_f2280', 'v2_seg_s3_water_mask_f2280'), ('s4m_f0120', 'v2_seg_s4_water_mask_f0120')):
    x = cv2.imread(f'{C}/{a}.png', 0); y = cv2.imread(f'{C}/{b}.png', 0)
    d = cv2.resize(x, (1280, 720), interpolation=cv2.INTER_AREA).astype(np.float32)
    print(a, x.shape, '1080→720 平均差 %.2f  最大 %d  均值 %.1f vs %.1f' % (np.abs(d - y).mean(), np.abs(d - y).max(), d.mean(), y.mean()))
