# Bilibili cover 1920x1200 (16:10): Qianli Jiangshan hi-res crop + title
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
SRC = "~/claude-projects/china-art/trailer/assets_v3/qianli/work_ds3_x27000-33500.npy"
SONG = "/System/Library/Fonts/Supplemental/Songti.ttc"
W, H = 1920, 1200
a = np.load(SRC, mmap_mode="r")
def bg(x0, y0=330, h=1450):
    w = int(h * W / H)
    im = Image.fromarray(np.ascontiguousarray(a[y0:y0 + h, x0:x0 + w])).resize((W, H), Image.LANCZOS)
    # smooth darkening of the sky only (top 60 %), so cream text reads at thumbnail size
    y = np.arange(H)[:, None, None] / (H * 0.60)
    sm = np.clip(y, 0, 1); sm = sm * sm * (3 - 2 * sm)
    g = 0.72 + 0.28 * sm
    return Image.fromarray((np.asarray(im).astype(np.float32) * g).clip(0, 255).astype(np.uint8))
def font(sz, idx=0): return ImageFont.truetype(SONG, sz, index=idx)
CREAM, SHADOW, RED = (246, 238, 220), (20, 14, 8), (178, 34, 30)
def text_shadow(base, xy, s, f, fill=CREAM, blur=10, spread=4, anchor="la"):
    sh = Image.new("RGBA", base.size, (0, 0, 0, 0)); d = ImageDraw.Draw(sh)
    d.text(xy, s, font=f, fill=SHADOW + (210,), anchor=anchor, stroke_width=spread, stroke_fill=SHADOW + (210,))
    base.alpha_composite(sh.filter(ImageFilter.GaussianBlur(blur)))
    ImageDraw.Draw(base).text(xy, s, font=f, fill=fill, anchor=anchor)
def seal(base, x, y, size, chars="北宋"):
    s = Image.new("RGBA", (size, size), (0, 0, 0, 0)); d = ImageDraw.Draw(s)
    d.rounded_rectangle([0, 0, size - 1, size - 1], radius=size // 14, fill=RED + (235,))
    f = font(int(size * 0.40), 0)
    # two characters stacked vertically, white (baiwen seal)
    d.text((size / 2, size * 0.29), chars[0], font=f, fill=(250, 240, 230, 255), anchor="mm")
    d.text((size / 2, size * 0.71), chars[1], font=f, fill=(250, 240, 230, 255), anchor="mm")
    # a little wear
    rng = np.random.default_rng(3); m = np.asarray(s).copy()
    holes = rng.random(m.shape[:2]) < 0.012; m[holes, 3] = (m[holes, 3] * 0.3).astype(np.uint8)
    base.alpha_composite(Image.fromarray(m), (x, y))

# A: horizontal title across the sky
im = bg(2300).convert("RGBA")
text_shadow(im, (W // 2, 330), "Claude的中式美学", font(168, 0), anchor="mm")
text_shadow(im, (W // 2 - 60, 505), "让 AI 试做一集纪录片 · 北宋篇", font(66, 1), anchor="mm", blur=8, spread=3)
seal(im, W // 2 + 430, 462, 96)
im.convert("RGB").save("cover_A.jpg", quality=92)

# B: vertical title in the right sky
im = bg(2900).convert("RGBA")
f_big, f_small, f_sub = font(210, 0), font(78, 0), font(62, 1)
x = W - 250
text_shadow(im, (x + 10, 120), "Claude的", f_small, anchor="ma")
for i, ch in enumerate("中式美学"):
    text_shadow(im, (x, 230 + i * 222), ch, f_big, anchor="ma")
xs = x - 200
col = ["让", "AI", "试", "做", "纪", "录", "片"]
for i, ch in enumerate(col):
    text_shadow(im, (xs, 250 + i * 74), ch, f_sub, anchor="ma", blur=7, spread=3)
seal(im, xs - 44, 250 + len(col) * 74 + 36, 88)
im.convert("RGB").save("cover_B.jpg", quality=92)
Image.fromarray(np.hstack([np.asarray(Image.open("cover_A.jpg").resize((960, 600))), np.asarray(Image.open("cover_B.jpg").resize((960, 600)))])).save("cover_AB.jpg", quality=88)
print("ok")

# A34: Xiaohongshu 3:4 (1080x1440) version of A
W, H = 1080, 1440
def bg34(x0, y0=0, h=2036):
    w = int(h * W / H)
    im = Image.fromarray(np.ascontiguousarray(a[y0:y0 + h, x0:x0 + w])).resize((W, H), Image.LANCZOS)
    y = np.arange(H)[:, None, None] / (H * 0.62)
    sm = np.clip(y, 0, 1); sm = sm * sm * (3 - 2 * sm)
    return Image.fromarray((np.asarray(im).astype(np.float32) * (0.70 + 0.30 * sm)).clip(0, 255).astype(np.uint8))
im = bg34(3000, y0=90, h=1946).convert("RGBA")
text_shadow(im, (W // 2, 250), "Claude的", font(120, 0), anchor="mm")
text_shadow(im, (W // 2, 440), "中式美学", font(200, 0), anchor="mm")
text_shadow(im, (W // 2 - 40, 640), "让 AI 试做一集纪录片 · 北宋篇", font(52, 1), anchor="mm", blur=8, spread=3)
seal(im, W // 2 + 340, 606, 76)
im.convert("RGB").save("cover_A34.jpg", quality=92)
print("A34 ok")
