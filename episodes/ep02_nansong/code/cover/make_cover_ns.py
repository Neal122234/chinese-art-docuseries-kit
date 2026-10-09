# Southern Song covers from the hi-res 水图·黄河逆流 panel; same type system as the Northern Song cover.
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
a = np.load("~/claude-projects/china-art/series/lib/cache/mips/shuitu_scroll_bc69f58502/L0.npy", mmap_mode="r")
SONG = "/System/Library/Fonts/Supplemental/Songti.ttc"
CREAM, SHADOW, RED = (246, 238, 220), (20, 14, 8), (178, 34, 30)
def font(sz, idx=0): return ImageFont.truetype(SONG, sz, index=idx)
def bg(W, H, cx, x0lim=85250, x1lim=89050, y0=330, y1=3100):
    h = y1 - y0; w = int(h * W / H)
    if w > x1lim - x0lim: w = x1lim - x0lim; h = int(w * H / W)
    x0 = int(min(max(cx - w / 2, x0lim), x1lim - w)); yy = y1 - h
    im = Image.fromarray(np.ascontiguousarray(a[yy:yy + h, x0:x0 + w])).resize((W, H), Image.LANCZOS)
    y = np.arange(H)[:, None, None] / (H * 0.55); sm = np.clip(y, 0, 1); sm = sm * sm * (3 - 2 * sm)
    return Image.fromarray((np.asarray(im).astype(np.float32) * (0.62 + 0.38 * sm)).clip(0, 255).astype(np.uint8)).convert("RGBA")
def ts(base, xy, s, f, blur=10, spread=4):
    sh = Image.new("RGBA", base.size, (0, 0, 0, 0)); d = ImageDraw.Draw(sh)
    d.text(xy, s, font=f, fill=SHADOW + (210,), anchor="mm", stroke_width=spread, stroke_fill=SHADOW + (210,))
    base.alpha_composite(sh.filter(ImageFilter.GaussianBlur(blur))); ImageDraw.Draw(base).text(xy, s, font=f, fill=CREAM, anchor="mm")
def seal(base, x, y, size):
    s = Image.new("RGBA", (size, size), (0, 0, 0, 0)); d = ImageDraw.Draw(s)
    d.rounded_rectangle([0, 0, size - 1, size - 1], radius=size // 14, fill=RED + (235,))
    f = font(int(size * 0.40)); d.text((size / 2, size * .29), "南", font=f, fill=(250, 240, 230), anchor="mm"); d.text((size / 2, size * .71), "宋", font=f, fill=(250, 240, 230), anchor="mm")
    base.alpha_composite(s, (int(x), int(y)))
def make(W, H, name, t1, t2, sub, sz1, sz2, szs, ys):
    im = bg(W, H, 87400)
    if t2: ts(im, (W // 2, ys[0]), t1, font(sz1)); ts(im, (W // 2, ys[1]), t2, font(sz2))
    else: ts(im, (W // 2, ys[0]), t1, font(sz1))
    ts(im, (W // 2 - szs, ys[2]), sub, font(szs, 1), blur=8, spread=3)
    tw = ImageDraw.Draw(im).textlength(sub, font=font(szs, 1))
    seal(im, W // 2 - szs + tw / 2 + 20, ys[2] - szs * 0.8, int(szs * 1.5))
    im.convert("RGB").save(name, quality=92)
make(1920, 1200, "cover_ns_A.jpg", "Claude的中式美学②", None, "南宋 · 只留最要紧的一笔", 158, 0, 66, (330, 0, 505))
make(1080, 1440, "cover_ns_34.jpg", "Claude的", "中式美学②", "南宋 · 只留最要紧的一笔", 120, 190, 50, (250, 440, 640))
make(1440, 1080, "cover_ns_43.jpg", "Claude的中式美学②", None, "南宋 · 只留最要紧的一笔", 124, 0, 54, (280, 0, 430))
im = [Image.open(n) for n in ("cover_ns_A.jpg", "cover_ns_34.jpg", "cover_ns_43.jpg")]
c = Image.new("RGB", (960 + 450 + 800 + 20, 600), "white"); c.paste(im[0].resize((960, 600)), (0, 0)); c.paste(im[1].resize((450, 600)), (970, 0)); c.paste(im[2].resize((800, 600)), (1430, 0)); c.save("ns_all.jpg", quality=85)
