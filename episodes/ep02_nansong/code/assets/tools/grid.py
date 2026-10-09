# usage: grid.py SRC out.jpg x0 y0 x1 y1 outW [step]
# SRC: .npy | .rgb (name must contain _<W>x<H>.rgb) | image file
import sys, re, numpy as np
from PIL import Image, ImageDraw
Image.MAX_IMAGE_PIXELS = None
src, out = sys.argv[1], sys.argv[2]
x0, y0, x1, y1, ow = map(int, sys.argv[3:8]); step = int(sys.argv[8]) if len(sys.argv) > 8 else 0
s = max(1, (x1 - x0) // ow // 3)
if src.endswith('.npy') or src.endswith('.rgb'):
    if src.endswith('.npy'):
        a = np.load(src, mmap_mode='r')
    else:
        W, H = map(int, re.findall(r'_(\d+)x(\d+)\.rgb$', src)[0]); a = np.memmap(src, np.uint8, 'r', shape=(H, W, 3))
    c = np.array(a[y0:y1:s, x0:x1:s]); im = Image.fromarray(c)
else:
    im = Image.open(src).convert('RGB').crop((x0, y0, x1, y1))
sc = ow / (x1 - x0)
import cv2
im = Image.fromarray(cv2.resize(np.asarray(im), (ow, max(1, int((y1 - y0) * sc))), interpolation=cv2.INTER_AREA))
d = ImageDraw.Draw(im)
steps = [1, 2, 5, 10, 20, 25, 50, 100, 200, 250, 500, 1000, 2000, 5000]
if not step: step = steps[min(len(steps) - 1, np.searchsorted(steps, (x1 - x0) / 8))]
for gx in range((x0 // step + 1) * step, x1, step):
    X = (gx - x0) * sc; d.line([(X, 0), (X, im.height)], fill=(255, 0, 0), width=1); d.text((X + 2, 2), str(gx), fill=(255, 255, 0))
for gy in range((y0 // step + 1) * step, y1, step):
    Y = (gy - y0) * sc; d.line([(0, Y), (im.width, Y)], fill=(255, 0, 0), width=1); d.text((2, Y + 2), str(gy), fill=(255, 255, 0))
im.save(out, quality=88)
