# 1080 静帧 vs 第二版 720 同帧：1080 缩到 720 后求平均差、相位相关位移；输出并排对比图
import cv2, numpy as np, glob, os, sys
C = os.path.dirname(os.path.abspath(__file__))
pairs = []
for f in sorted(glob.glob(C + '/s*_f*.*')):
    b = os.path.basename(f); seg, fr = b.split('_f'); fr = fr.split('.')[0]
    ref = f'{C}/v2_seg_{seg}_f{fr}.png'
    if os.path.exists(ref): pairs.append((seg, fr, f, ref))
rows = []
for seg, fr, f, ref in pairs:
    a = cv2.imread(f); r = cv2.imread(ref)
    assert a.shape[:2] == (1080, 1920), (f, a.shape)
    d = cv2.resize(a, (1280, 720), interpolation=cv2.INTER_AREA)
    g1 = cv2.cvtColor(d, cv2.COLOR_BGR2GRAY).astype(np.float32); g0 = cv2.cvtColor(r, cv2.COLOR_BGR2GRAY).astype(np.float32)
    (dx, dy), resp = cv2.phaseCorrelate(g0, g1, cv2.createHanningWindow((1280, 720), cv2.CV_32F))
    mad = np.abs(d.astype(np.float32) - r.astype(np.float32)).mean()
    diff = np.abs(d.astype(np.float32) - r.astype(np.float32)).max(2)
    p99 = np.percentile(diff, 99.5)
    print(f'{seg:4s} f{fr}  1080→720 平均差 {mad:5.2f}  99.5%分位 {p99:5.1f}  位移 ({dx:+.2f},{dy:+.2f}) px@720  r={resp:.2f}')
    L = cv2.resize(r, (960, 540), interpolation=cv2.INTER_AREA); R = cv2.resize(a, (960, 540), interpolation=cv2.INTER_AREA)
    Dm = cv2.applyColorMap(np.clip(cv2.resize(diff, (480, 270)) * 4, 0, 255).astype(np.uint8), cv2.COLORMAP_INFERNO)
    Dm = cv2.copyMakeBorder(Dm, 0, 270, 0, 0, cv2.BORDER_CONSTANT)
    row = np.hstack([L, R, Dm])
    cv2.putText(row, f'{seg} f{fr}  v2-720 | 1080 | |diff|x4', (10, 30), 0, 0.9, (0, 0, 255), 2)
    rows.append(row)
for i in range(0, len(rows), 6):
    cv2.imwrite(f'{C}/sheet{i // 6}.jpg', np.vstack(rows[i:i + 6]), [cv2.IMWRITE_JPEG_QUALITY, 82])
print('sheets', (len(rows) + 5) // 6)
