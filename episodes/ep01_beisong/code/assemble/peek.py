"""抽帧拼图：python3 peek.py out.jpg file:t[:label] ...（t 为段内秒）"""
import sys, subprocess, numpy as np, cv2
out = sys.argv[1]; items = sys.argv[2:]
W, H = 400, 225; tiles = []
for it in items:
    f, t = it.rsplit(':', 1)
    b = subprocess.run(['ffmpeg', '-v', 'error', '-ss', t, '-i', f, '-frames:v', '1', '-vf', f'scale={W}:{H}',
                        '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-'], capture_output=True).stdout
    im = np.frombuffer(b, np.uint8).reshape(H, W, 3).copy() if len(b) == W*H*3 else np.zeros((H, W, 3), np.uint8)
    cv2.putText(im, f'{f.split("/")[-1][:14]} {t}', (4, 16), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 0, 255), 1)
    tiles.append(im)
cols = 4
while len(tiles) % cols: tiles.append(np.zeros((H, W, 3), np.uint8))
rows = [np.hstack(tiles[i:i+cols]) for i in range(0, len(tiles), cols)]
cv2.imwrite(out, np.vstack(rows), [cv2.IMWRITE_JPEG_QUALITY, 85])
