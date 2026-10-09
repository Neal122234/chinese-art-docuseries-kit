"""万壑松风拼接大图是梯形（上窄下宽约 7%，来自整幅图的拍摄透视），逐行水平重采样成矩形立轴（含上下隔水/地头）。
输出 work/wanhe_scroll.npy（世界坐标 = 此图像素）。映射：x' = (x-L(y))*WT/(R(y)-L(y)), y' = y-Y0。"""
import numpy as np, cv2, json, os
HERE = os.path.dirname(os.path.abspath(__file__))
SRC = '~/claude-projects/china-art/series/ep02_nansong/assets/wanhe/wanhe_mosaic_4876x6332.rgb'
Y0, Y1 = 30, 6316
# 画心左右边（程序逐行检测后直线拟合，向内收 8 px）
def L(y): return 328 + 8 - 0.018 * (y - 40)
def R(y): return 4484 - 8 + 0.0301 * (y - 40)
WT = 4290
if __name__ == '__main__':
    a = np.memmap(SRC, np.uint8, 'r', shape=(6332, 4876, 3))
    H = Y1 - Y0
    out = np.lib.format.open_memmap(HERE + '/work/wanhe_scroll.tmp.npy', 'w+', np.uint8, (H, WT, 3))
    xs = np.arange(WT, dtype=np.float32) + 0.5
    for r0 in range(0, H, 512):
        r1 = min(H, r0 + 512)
        ys = np.arange(r0, r1, dtype=np.float32) + Y0
        sy0 = int(ys[0]) - 2; sy1 = int(ys[-1]) + 3
        blk = np.ascontiguousarray(a[sy0:sy1])
        mx = (L(ys)[:, None] + xs[None, :] * ((R(ys) - L(ys)) / WT)[:, None] - 0.5).astype(np.float32)
        my = np.broadcast_to((ys - sy0)[:, None], mx.shape).astype(np.float32)
        out[r0:r1] = cv2.remap(blk, mx, np.ascontiguousarray(my), cv2.INTER_LANCZOS4, borderMode=cv2.BORDER_REFLECT)
    out.flush(); del out
    os.replace(HERE + '/work/wanhe_scroll.tmp.npy', HERE + '/work/wanhe_scroll.npy')
    json.dump({'Y0': Y0, 'WT': WT, 'L': 'x=336-0.018*(y-40)', 'R': 'x=4476+0.0301*(y-40)', 'shape': [H, WT]},
              open(HERE + '/work/rectify.json', 'w'), indent=1)
    print('ok', H, WT)
