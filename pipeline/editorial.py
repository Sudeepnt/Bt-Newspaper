"""The "editorial" look: a dark newsroom, the headline in large serif type on the left, category and tag chips, a duration
badge, the story picture on a screen behind the host (top right), and a host who is bigger and graded to match.

Everything is drawn with Pillow in the 1280x720 design space; the host is any Presenter (the anime anchor for now).
"""
from __future__ import annotations

import math

import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter

from .avatar import _font, _wrap

DW = 1280
WHITE = (255, 255, 255, 255)
RED = (214, 52, 44, 255)
INK = (14, 14, 18, 255)


def newsroom_background(size, seed=7) -> Image.Image:
    """Dark open-plan newsroom: warm-black base, a wall of glowing monitors, ceiling light bars and desk bokeh, all blurred."""
    w, h = size
    rnd = np.random.default_rng(seed)
    base = np.zeros((h, w, 3), np.float32)
    yy = np.linspace(0, 1, h)[:, None]
    base[..., 0] = 16 + 14 * yy
    base[..., 1] = 14 + 10 * yy
    base[..., 2] = 18 + 8 * yy
    img = Image.fromarray(base.astype("uint8")).convert("RGB")

    glow = Image.new("RGB", size, (0, 0, 0))
    d = ImageDraw.Draw(glow)
    s = w / DW
    for _ in range(90):                                        # the monitor wall (far side, upper half)
        x, y = rnd.uniform(0, w), rnd.uniform(0.04 * h, 0.52 * h)
        mw, mh = rnd.uniform(40, 120) * s, rnd.uniform(24, 70) * s
        tint = [(70, 120, 200), (210, 150, 90), (90, 170, 160), (200, 90, 80), (170, 170, 190)][int(rnd.integers(0, 5))]
        k = rnd.uniform(0.25, 0.8)
        d.rectangle((x, y, x + mw, y + mh), fill=tuple(int(c * k) for c in tint))
    for i in range(5):                                         # ceiling light bars
        y = (22 + i * 9) * s
        d.rectangle((rnd.uniform(0, 0.4 * w), y, rnd.uniform(0.5 * w, w), y + 5 * s), fill=(230, 225, 215))
    for _ in range(60):                                        # desk lamps / bokeh in the lower half
        x, y, r = rnd.uniform(0, w), rnd.uniform(0.55 * h, 0.95 * h), rnd.uniform(5, 16) * s
        c = (255, 190, 120) if rnd.random() < 0.6 else (150, 190, 255)
        d.ellipse((x - r, y - r, x + r, y + r), fill=tuple(int(v * rnd.uniform(0.35, 0.8)) for v in c))
    glow = glow.filter(ImageFilter.GaussianBlur(11 * s)).point(lambda v: int(v * 0.75))
    img = Image.fromarray(np.clip(np.asarray(img, np.float32) + np.asarray(glow, np.float32), 0, 255).astype("uint8"))

    silhouettes = Image.new("L", size, 0)                      # dark desks and seated people in the mid-ground
    sd = ImageDraw.Draw(silhouettes)
    for _ in range(14):
        x, y = rnd.uniform(-0.05 * w, w), rnd.uniform(0.5 * h, 0.78 * h)
        sd.ellipse((x, y, x + 46 * s, y + 52 * s), fill=150)
        sd.rectangle((x - 20 * s, y + 46 * s, x + 66 * s, y + 130 * s), fill=150)
    silhouettes = silhouettes.filter(ImageFilter.GaussianBlur(6 * s))
    img = Image.composite(Image.new("RGB", size, (6, 6, 9)), img, silhouettes)
    img = img.filter(ImageFilter.GaussianBlur(1.6 * s))
    arr = np.asarray(img, np.float32)                          # vignette + a little grain so it reads as a photograph
    yy, xx = np.mgrid[0:h, 0:w]
    d2 = ((xx - w * 0.62) / (w * 0.75)) ** 2 + ((yy - h * 0.45) / (h * 0.8)) ** 2
    arr *= np.clip(1.15 - d2 * 0.9, 0.35, 1.0)[..., None]
    arr += rnd.normal(0, 2.2, arr.shape)
    return Image.fromarray(np.clip(arr, 0, 255).astype("uint8"))


def grade(img: Image.Image, dim=0.66, warm=0.06) -> Image.Image:
    """Match a bright cut-out to the dark set: dimmer, a little desaturated, a touch warm. Keeps the alpha."""
    rgb, a = img.convert("RGB"), img.getchannel("A")
    rgb = ImageEnhance.Color(rgb).enhance(0.8)
    rgb = ImageEnhance.Contrast(rgb).enhance(1.12)
    rgb = ImageEnhance.Brightness(rgb).enhance(dim)
    arr = np.asarray(rgb, np.float32)
    arr[..., 0] *= 1 + warm
    arr[..., 2] *= 1 - warm
    out = Image.fromarray(np.clip(arr, 0, 255).astype("uint8")).convert("RGBA")
    out.putalpha(a)
    return out


class Editorial:
    def __init__(self, size, headline, image, channel, font_path, serif_path, category, subhead, duration, tags=None):
        from .avatar import Visual
        self.size, self.s = size, size[0] / DW
        s = self.s
        self.channel, self.font_path, self.serif_path = channel, font_path, serif_path
        self.category = (category or "TOP STORY").upper()
        self.bg = newsroom_background((int(size[0] * 1.05), int(size[1] * 1.05)))
        self.shot = Visual(image)
        self.duration = f"{int(duration // 60)}:{int(duration % 60):02d}"
        words = [w.strip(".,:;!?'\"").upper() for w in headline.split() if len(w) > 4]
        self.tags = tags or [self.category] + sorted(set(words), key=lambda x: -len(x))[:3]
        m = ImageDraw.Draw(Image.new("RGBA", (8, 8)))
        # headline: the biggest serif size that fits three lines in the left column
        self.col = int(530 * s)        # ends before the page's play button in the middle of the video
        for px in range(86, 38, -2):
            f = _font(serif_path, int(px * s))
            lines = _wrap(m, headline, f, self.col)
            if lines and len(lines) <= 3:
                break
        self.hfont, self.hlines = f, lines[:3]
        self.dfont = _font(font_path, int(25 * s))
        self.deck = _wrap(m, subhead, self.dfont, self.col)[:2] if subhead else []
        self.static = self._static()

    def _static(self):
        s, W, H = self.s, *self.size
        L = Image.new("RGBA", self.size, (0, 0, 0, 0))
        d = ImageDraw.Draw(L)
        lf = _font(self.serif_path, int(46 * s))                       # logo, top left
        d.text((int(48 * s), int(84 * s)), "Bought", font=lf, fill=WHITE)
        d.text((int(48 * s), int(126 * s)), "Media", font=lf, fill=WHITE)
        mw = d.textlength("Media", font=lf)
        d.ellipse((int(48 * s + mw + 3 * s), int(160 * s), int(48 * s + mw + 11 * s), int(168 * s)), fill=RED)
        chip = _font(self.font_path, int(15 * s))                      # category chip
        cw = d.textlength(self.category, font=chip)
        cy0 = int(300 * s)
        self.headline_y = int(cy0 + 46 * s)
        d.rounded_rectangle((int(48 * s), cy0, int(48 * s + cw + 28 * s), int(cy0 + 30 * s)), radius=int(4 * s), fill=(244, 240, 232, 255))
        d.text((int(62 * s), cy0 + int(6 * s)), self.category, font=chip, fill=INK)
        lh = int(self.hfont.size * 1.04)                              # headline
        y = self.headline_y
        for line in self.hlines:
            d.text((int(48 * s), y), line, font=self.hfont, fill=WHITE)
            y += lh
        y += int(10 * s)
        for line in self.deck:                                         # deck
            d.text((int(48 * s), y), line, font=self.dfont, fill=(236, 232, 226, 235))
            y += int(self.dfont.size * 1.3)
        tf = _font(self.font_path, int(14 * s))                        # tag row, bottom left
        x, ty = int(48 * s), int(664 * s)
        for i, t in enumerate(self.tags):
            w = d.textlength(t, font=tf)
            if i == 0:
                d.rounded_rectangle((x - int(10 * s), ty - int(7 * s), x + w + int(10 * s), ty + int(24 * s)), radius=int(3 * s), fill=(244, 240, 232, 255))
                d.text((x, ty), t, font=tf, fill=INK)
            else:
                d.text((x, ty), t, font=tf, fill=(230, 226, 220, 230))
            x += int(w + 34 * s)
            if i < len(self.tags) - 1 and i > 0:
                d.line((x - int(17 * s), ty + 2, x - int(17 * s), ty + int(20 * s)), fill=(200, 196, 190, 160), width=1)
        df = _font(self.font_path, int(18 * s))                        # duration badge, bottom right
        dw = d.textlength(self.duration, font=df)
        d.rounded_rectangle((int(1280 * s - 48 * s - dw - 22 * s), int(656 * s), int(1280 * s - 48 * s), int(692 * s)), radius=int(6 * s), fill=(8, 8, 10, 215))
        d.text((int(1280 * s - 48 * s - dw - 11 * s), int(664 * s)), self.duration, font=df, fill=WHITE)
        # left-to-right shade so the type reads over the room
        shade = np.zeros((H, W), np.float32)
        xs = np.linspace(0, 1, W)[None, :]
        shade[:] = np.clip(0.78 - xs * 1.15, 0, 0.78) * 255
        sh = Image.new("RGBA", self.size, (0, 0, 0, 0))
        sh.putalpha(Image.fromarray(shade.astype("uint8")))
        return Image.alpha_composite(sh, L)

    def background(self, t):
        bw, bh = self.bg.size
        ox = int((bw - self.size[0]) / 2 * (1 + math.sin(t * 2 * math.pi / 13.0)))
        oy = int((bh - self.size[1]) / 2 * (1 + math.sin(t * 2 * math.pi / 17.0 + 1)))
        return self.bg.crop((ox, oy, ox + self.size[0], oy + self.size[1])).convert("RGBA")

    def screen(self, frame, i, n):
        """The story picture on a monitor in the top right, behind the host."""
        s = self.s
        box = (int(930 * s), int(46 * s), int(1244 * s), int(300 * s))
        d = ImageDraw.Draw(frame)
        d.rectangle((box[0] - 8, box[1] - 8, box[2] + 8, box[3] + 8), fill=(10, 10, 14, 255))
        pic = self.shot.render(box[2] - box[0], box[3] - box[1], 1.0 + 0.03 * i / max(1, n - 1)).convert("RGBA")
        pic = ImageEnhance.Brightness(pic.convert("RGB")).enhance(0.72).convert("RGBA")
        frame.paste(pic, (box[0], box[1]))
        glow = Image.new("RGBA", frame.size, (0, 0, 0, 0))
        ImageDraw.Draw(glow).rectangle((box[0] - 14, box[1] - 14, box[2] + 14, box[3] + 14), outline=(110, 150, 220, 70), width=10)
        frame.alpha_composite(glow.filter(ImageFilter.GaussianBlur(10 * s)))

    def overlay(self, frame):
        frame.alpha_composite(self.static)
