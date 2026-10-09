# 稠密补点：按当前映射在每对瓦片的重叠区按网格取小块做相位相关，把残余错位转成原瓦片坐标下的对应点
import cv2, numpy as np, os, itertools, sys
p = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'wanhe_stitch_render2.py')
ns = {'__file__': p}; exec(open(p).read().split('# 增益（1/8）')[0], ns)
T, inv, weight, X0, Y0, IM, cor = ns['T'], ns['inv'], ns['weight'], ns['X0'], ns['Y0'], ns['IM'], ns['cor']
D = os.path.dirname(p) + '/../wanhe/'
GR = [cv2.cvtColor(im, cv2.COLOR_BGR2GRAY) for im in IM]
S = 192; STEP = 112
def dog(a): return cv2.GaussianBlur(a, (0, 0), 1.2) - cv2.GaussianBlur(a, (0, 0), 5)
win = cv2.createHanningWindow((S, S), cv2.CV_32F)
out = {}; tot = 0; mags = []
for i, j in itertools.combinations(range(len(T)), 2):
    ci, cj = cor[i] - [X0, Y0], cor[j] - [X0, Y0]
    lo = np.maximum(ci.min(0), cj.min(0)); hi = np.minimum(ci.max(0), cj.max(0)) - S
    if (hi - lo).min() < 0: continue
    P, Q = [], []
    for y in range(int(lo[1]), int(hi[1]) + 1, STEP):
        for x in range(int(lo[0]), int(hi[0]) + 1, STEP):
            yy, xx = np.mgrid[y:y + S, x:x + S].astype(np.float32)
            pxi, pyi = inv(i, xx + X0, yy + Y0); pxj, pyj = inv(j, xx + X0, yy + Y0)
            if weight(pxi, pyi).min() <= 0 or weight(pxj, pyj).min() <= 0: continue
            a = dog(cv2.remap(GR[i], pxi, pyi, cv2.INTER_CUBIC).astype(np.float32)); b = dog(cv2.remap(GR[j], pxj, pyj, cv2.INTER_CUBIC).astype(np.float32))
            if a.std() < 2.5 or b.std() < 2.5: continue
            (dx, dy), r = cv2.phaseCorrelate(a, b, win)
            if r < 0.25 or np.hypot(dx, dy) > 25: continue
            c = S / 2
            m = np.array([[x + c, y + c]], np.float32)
            pi = inv(i, m[:, :1] + X0, m[:, 1:] + Y0); pj = inv(j, m[:, :1] + dx + X0, m[:, 1:] + dy + Y0)
            P.append([pi[0][0, 0], pi[1][0, 0]]); Q.append([pj[0][0, 0], pj[1][0, 0]]); mags.append(np.hypot(dx, dy))
    if P:
        out['%s-%s_p' % (T[i], T[j])] = np.array(P, np.float32); out['%s-%s_q' % (T[i], T[j])] = np.array(Q, np.float32); tot += len(P)
        print(T[i], T[j], len(P), flush=True)
np.savez(D + 'work/stitch_matches_dense.npz', **out)
print('dense pts', tot, 'current |d| median %.2f p90 %.2f max %.2f' % (np.median(mags), np.percentile(mags, 90), max(mags)))
