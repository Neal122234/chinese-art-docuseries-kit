"""1080 终版客观自检：和 720 配音版同时刻抽帧比构图 + 出联系表。
用法：python3 check_1080.py ../../out/pilot_beisong_v3_1080.mp4 ../../out/pilot_beisong_v3.mp4 ../../out/contact_1080.jpg
比对：1080 帧缩到 1280×720（area）后与 720 帧求平均绝对差（0–255）与整帧相位相关位移（px@720）。"""
import subprocess, sys, numpy as np, cv2

src, ref, contact = sys.argv[1:4]
CMP_T = [12.0, 45.0, 86.0, 125.0, 147.0, 195.0, 226.0, 262.0]           # 8 个同时刻（避开转场）
CONTACT_T = [1.5, 21.0, 45.0, 59.3, 68.0, 86.0, 99.5, 110.0,
             147.0, 171.0, 180.0, 195.0, 226.0, 239.5, 250.0, 270.0]    # 16 个关键帧（含各高光与转场）


def grab(path, t, w, h):
    b = subprocess.run(['ffmpeg', '-v', 'error', '-ss', f'{t:.3f}', '-i', path, '-frames:v', '1',
                        '-vf', f'scale={w}:{h}:flags=area', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'],
                       capture_output=True).stdout
    return np.frombuffer(b, np.uint8).reshape(h, w, 3)


win = cv2.createHanningWindow((1280, 720), cv2.CV_32F)
worst_d, worst_s = 0.0, 0.0
print('时刻     平均差  位移(px@720)')
for t in CMP_T:
    a = grab(src, t, 1280, 720); b = grab(ref, t, 1280, 720)
    d = float(np.abs(a.astype(np.float32) - b.astype(np.float32)).mean())
    ga = cv2.cvtColor(a, cv2.COLOR_RGB2GRAY).astype(np.float32); gb = cv2.cvtColor(b, cv2.COLOR_RGB2GRAY).astype(np.float32)
    (dx, dy), r = cv2.phaseCorrelate(gb, ga, win)
    s = float(np.hypot(dx, dy)); worst_d = max(worst_d, d); worst_s = max(worst_s, s)
    print(f'{t:7.1f}s  {d:6.2f}  {s:5.2f} (dx {dx:+.2f}, dy {dy:+.2f}, r {r:.2f})')
print(f'最大平均差 {worst_d:.2f}，最大位移 {worst_s:.2f} px@720')

tiles = []
for t in CONTACT_T:
    im = grab(src, t, 480, 270).copy()
    cv2.putText(im, f'{int(t // 60)}:{t % 60:04.1f}', (6, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 40, 40), 1, cv2.LINE_AA)
    tiles.append(im)
sheet = np.vstack([np.hstack(tiles[i:i + 4]) for i in range(0, 16, 4)])
cv2.imwrite(contact, cv2.cvtColor(sheet, cv2.COLOR_RGB2BGR), [cv2.IMWRITE_JPEG_QUALITY, 88])
# 另存 1080 原尺寸字幕区裁切（检查 48 px 字幕在 1080 下的清晰度）
sub = grab(src, 26.0, 1920, 1080)[900:1080, 360:1560]
import os
cv2.imwrite(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'contact_1080_subcrop.jpg'), cv2.cvtColor(np.ascontiguousarray(sub), cv2.COLOR_RGB2BGR),
            [cv2.IMWRITE_JPEG_QUALITY, 90])
print('contact ->', contact)
