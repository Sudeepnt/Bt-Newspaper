"""Alternative video designs for produced clips. Same presenter, same audio-driven animation, different set.

  channel  a TV news channel: LIVE tag, story window, red tag + white headline bar, scrolling ticker of other headlines
  funky    pop / sticker look: moving gradient, halftone dots, tilted sticker photo, outlined presenter, kinetic captions

Both use the 1280x720 design space of avatar.py and the same cutaway idea (the picture takes over the screen).
"""
from __future__ import annotations

import hashlib
import math
import os
import subprocess
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

from .avatar import (FPS, K_MAX, K_MIN, Visual, _font, _wrap, cutaway_plan, envelope, motion, name_strap, plan_from_ranges, put_strap,
                     studio_background)

DW, DH = 1280, 720
TAG_DX = 150      # the channel set's LIVE | BOUGHT. tag sits right of the page's "n / 50" counter on the video's top-left
INK = (20, 14, 40, 255)
YELLOW = (255, 226, 40, 255)


def _ease(x):
    x = min(max(x, 0.0), 1.0)
    return 1 - (1 - x) ** 3


def _lerp(a, b, t):
    return a + (b - a) * t


def _bold(d, xy, text, font, fill, s, width=1.3):
    """The bundled DM Sans is a static regular: a same-colour stroke fakes bold."""
    d.text(xy, text, font=font, fill=fill, stroke_width=max(1, int(width * s)), stroke_fill=fill)


def _fit(d, text, font_path, max_w, max_h, s, hi=54, lo=22, max_lines=2, lead=1.12):
    for px in range(hi, lo - 1, -2):
        font = _font(font_path, int(px * s))
        lines = _wrap(d, text, font, max_w, max_lines)
        if lines and len(lines) * px * s * lead <= max_h:
            return font, lines
    font = _font(font_path, int(lo * s))
    return font, (_wrap(d, text, font, max_w, 4) or [text[:60]])


def _measure():
    return ImageDraw.Draw(Image.new("RGB", (4, 4)))


def _loop_strip(text, font, height, fill, bg, gap, y, stroke=0):
    """Two copies of a line of text side by side, spaced by the drawn ink width (PIL under-measures long lines),
    so cropping a window that moves right looks endless."""
    probe = Image.new("L", (int(_measure().textlength(text, font=font)) * 2 + 400, height), 0)
    ImageDraw.Draw(probe).text((0, y), text, font=font, fill=255, stroke_width=stroke)
    w = (probe.getbbox() or (0, 0, 1, 1))[2] + gap
    strip = Image.new("RGBA", (w * 2, height), bg)
    sd = ImageDraw.Draw(strip)
    for k in range(2):
        sd.text((k * w, y), text, font=font, fill=fill, stroke_width=stroke, stroke_fill=fill)
    return strip, w


# ---------------------------------------------------------------- channel

def broadcast_background(size):
    """A blue newsroom: glass wall with a blurred skyline, a globe on the left, a glossy desk. Deterministic."""
    W, H = size
    rnd = np.random.RandomState(7)
    yy = np.linspace(0, 1, H)[:, None, None]
    stops = [(0.0, (18, 52, 128)), (0.45, (64, 126, 208)), (0.72, (40, 92, 170)), (1.0, (12, 30, 78))]
    col = np.zeros((H, 1, 3))
    for (a, ca), (b, cb) in zip(stops, stops[1:]):
        m = (yy >= a) & (yy <= b)
        f = (yy - a) / (b - a)
        col = np.where(m, np.array(ca) + (np.array(cb) - np.array(ca)) * f, col)
    img = Image.fromarray(col.repeat(W, axis=1).astype("uint8")).convert("RGBA")
    # skyline
    city = Image.new("RGBA", size, (0, 0, 0, 0))
    d = ImageDraw.Draw(city)
    base = int(H * 0.70)
    x = int(W * 0.30)
    while x < W * 0.92:
        bw = int(rnd.uniform(0.03, 0.07) * W)
        bh = int(rnd.uniform(0.12, 0.42) * H)
        tone = int(rnd.uniform(80, 130))
        d.rectangle((x, base - bh, x + bw, base), fill=(tone, tone + 40, tone + 95, 235))
        for wy in range(base - bh + 8, base - 6, 14):
            for wx in range(x + 5, x + bw - 5, 11):
                if rnd.rand() < 0.45:
                    d.rectangle((wx, wy, wx + 4, wy + 6), fill=(210, 232, 255, 200))
        x += bw + int(rnd.uniform(0, 0.012) * W)
    img.alpha_composite(city.filter(ImageFilter.GaussianBlur(W * 0.0025)))
    # glass wall: dark mullions with a light edge
    glass = Image.new("RGBA", size, (0, 0, 0, 0))
    g = ImageDraw.Draw(glass)
    for k in range(7):
        gx = int(W * (0.17 + k * 0.135))
        g.rectangle((gx, 0, gx + int(W * 0.011), int(H * 0.72)), fill=(10, 30, 86, 150))
        g.rectangle((gx + int(W * 0.011), 0, gx + int(W * 0.014), int(H * 0.72)), fill=(170, 210, 255, 60))
    g.rectangle((0, int(H * 0.05), W, int(H * 0.05) + int(H * 0.012)), fill=(10, 30, 86, 120))
    img.alpha_composite(glass.filter(ImageFilter.GaussianBlur(1.2)))
    # globe, left
    globe = Image.new("RGBA", size, (0, 0, 0, 0))
    gd = ImageDraw.Draw(globe)
    cx, cy, r = int(W * 0.04), int(H * 0.50), int(W * 0.21)
    gd.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(30, 80, 170, 120), outline=(150, 200, 255, 120), width=3)
    for k in range(1, 5):
        rx = int(r * k / 5)
        gd.ellipse((cx - rx, cy - r, cx + rx, cy + r), outline=(150, 200, 255, 70), width=2)
    for k in range(-3, 4):
        ry = int(r * 0.95 * abs(k) / 4)
        gd.line((cx - int((r * r - (k * r / 4) ** 2) ** 0.5), cy + int(k * r / 4), cx + int((r * r - (k * r / 4) ** 2) ** 0.5), cy + int(k * r / 4)),
                fill=(150, 200, 255, 70), width=2)
    img.alpha_composite(globe.filter(ImageFilter.GaussianBlur(1.5)))
    # desk
    desk = Image.new("RGBA", size, (0, 0, 0, 0))
    dd = ImageDraw.Draw(desk)
    dy = int(H * 0.715)
    dd.rectangle((0, dy, W, H), fill=(14, 36, 88, 255))
    dd.rectangle((0, dy, W, dy + int(H * 0.012)), fill=(150, 200, 255, 200))
    dd.rectangle((0, dy + int(H * 0.012), W, dy + int(H * 0.06)), fill=(32, 76, 150, 255))
    img.alpha_composite(desk)
    return img


class Channel:
    """TV news channel set in the style of a broadcast: anchor large at centre-left, story window with a BREAKING
    caption top right, TOP STORY headline + sub-line, an UP NEXT panel, and a one-after-another news strip."""

    def __init__(self, size, headline, image, credit, channel, font_path, category, ticker, subhead=""):
        self.size, self.s = size, size[0] / DW
        s = self.s
        self.font_path, self.channel, self.credit = font_path, channel, credit
        self.bgimg = broadcast_background((int(size[0] * 1.06), int(size[1] * 1.06)))
        self.shot = Visual(image)
        self.category = (category or "TOP STORY").upper()
        self.headline = headline.upper()
        self.subhead = subhead
        m = _measure()
        self.hfont, self.hlines = _fit(m, self.headline, font_path, (975 - 44) * s, 56 * s, s, hi=46, lo=22, max_lines=2)
        self.wfont, self.wlines = _fit(m, self.headline, font_path, (619 - 24) * s, 68 * s, s, hi=28, lo=15, max_lines=2)
        self.sfont = _font(font_path, int(21 * s))
        self.cf = _font(font_path, max(9, int(14 * s)))
        self.items = [t for t in (ticker or [])] or ["The day's top stories, in a minute"]
        self.strip = self._ticker(self.items)
        self.static = self._static()

    def _static(self):
        s, W, H = self.s, *self.size
        L = Image.new("RGBA", self.size, (0, 0, 0, 0))
        d = ImageDraw.Draw(L)
        d.rectangle((0, int(676 * s), W, H), fill=(8, 18, 48, 255))                    # news strip
        d.rectangle((0, int(676 * s), W, int(679 * s)), fill=(150, 200, 255, 255))
        d.rectangle((int(30 * s), int(682 * s), int(150 * s), int(714 * s)), fill=(225, 30, 45, 255))
        _bold(d, (int(46 * s), int(686 * s)), "NEWS", _font(self.font_path, int(22 * s)), (255, 255, 255, 255), s, 0.9)
        # top-left: LIVE | BOUGHT
        tx = TAG_DX
        d.rectangle((int((30 + tx) * s), int(24 * s), int((108 + tx) * s), int(56 * s)), fill=(225, 30, 45, 255))
        d.rectangle((int((108 + tx) * s), int(24 * s), int((236 + tx) * s), int(56 * s)), fill=(250, 251, 255, 255))
        return L

    def _ticker(self, items):
        s = self.s
        text = "      |      ".join(items) + "      |"
        return _loop_strip(text, _font(self.font_path, int(22 * s)), int(32 * s), (235, 240, 255, 255), (0, 0, 0, 0),
                           int(70 * s), int(3 * s))

    def background(self, t):
        bw, bh = self.bgimg.size
        ox = int((bw - self.size[0]) / 2 * (1 + math.sin(t * 2 * math.pi / 9.0)))
        oy = int((bh - self.size[1]) / 2 * (1 + math.sin(t * 2 * math.pi / 11.0 + 1)))
        return self.bgimg.crop((ox, oy, ox + self.size[0], oy + self.size[1]))

    def draw(self, frame, i, n, t, c, e):
        s = self.s
        win, full = (625, 84, 1244, 396), (0, 0, 1280, 520)           # photo; cutaway fills above the lower third
        box = [int(_lerp(win[k], full[k], c) * s) for k in range(4)]
        d = ImageDraw.Draw(frame)
        zoom = 1.0 + 0.04 * i / max(1, n - 1)
        if c < 1:
            d.rectangle((box[0] - 2, box[1] - 2, box[2] + 2, box[3] + 2 + int(106 * s * (1 - c))), fill=(255, 255, 255, 255))
        frame.paste(self.shot.render(box[2] - box[0], box[3] - box[1], zoom), (box[0], box[1]))
        if c < 1:                                                      # BREAKING tag + caption under the photo
            cap = (625, 396, 1244, 502)
            y0, y1 = int(cap[1] * s), int(cap[3] * s)
            keep = 1 - c
            if keep > 0.02:
                layer = Image.new("RGBA", (int((cap[2] - cap[0]) * s), y1 - y0), (0, 0, 0, 0))
                ld = ImageDraw.Draw(layer)
                ld.rectangle((0, 0, layer.width, layer.height), fill=(250, 251, 255, 255))
                ld.rectangle((0, 0, int(200 * s), int(26 * s)), fill=(225, 30, 45, 255))
                _bold(ld, (int(12 * s), int(3 * s)), "BREAKING NEWS", _font(self.font_path, int(18 * s)), (255, 255, 255, 255), s, 0.6)
                lh = int(self.wfont.size * 1.1)
                yy = int(28 * s) + (layer.height - int(28 * s) - lh * len(self.wlines)) // 2
                for line in self.wlines:
                    _bold(ld, (int(12 * s), yy), line, self.wfont, (14, 34, 86, 255), s, 0.7)
                    yy += lh
                layer.putalpha(layer.getchannel("A").point(lambda v: int(v * keep)))
                frame.alpha_composite(layer, (int(cap[0] * s), y0))
        if self.credit:
            cr = self.credit if len(self.credit) < 48 else self.credit[:45] + "..."
            tw = d.textlength(cr, font=self.cf)
            d.text((box[2] - tw - 8 * s, box[3] - 22 * s), cr, font=self.cf, fill=(255, 255, 255, 235),
                   stroke_width=1, stroke_fill=(0, 0, 0, 200))

    def lower(self, frame, i, t):
        s, W = self.s, self.size[0]
        frame.alpha_composite(self.static)
        d = ImageDraw.Draw(frame)
        pulse = 0.55 + 0.45 * math.sin(t * 2 * math.pi * 1.1)
        r = int(5 * s)
        d.ellipse((int((40 + TAG_DX) * s), int(40 * s) - r, int((40 + TAG_DX) * s) + 2 * r, int(40 * s) + r), fill=(255, int(255 * pulse), int(255 * pulse), 255))
        lf = _font(self.font_path, int(19 * s))
        _bold(d, (int((58 + TAG_DX) * s), int(28 * s)), "LIVE", lf, (255, 255, 255, 255), s, 0.7)
        cw = d.textlength(self.channel, font=lf)
        _bold(d, (int((172 + TAG_DX) * s - cw / 2), int(28 * s)), self.channel, lf, (14, 34, 86, 255), s, 0.7)
        bf = _font(self.font_path, int(40 * s))                        # logo, top right
        lw = d.textlength(self.channel, font=bf)
        _bold(d, (int(1244 * s - lw), int(22 * s)), self.channel, bf, (255, 255, 255, 255), s, 1.4)
        d.rectangle((int(1244 * s - lw), int(68 * s), int(1244 * s), int(71 * s)), fill=(225, 30, 45, 255))
        # lower third: TOP STORY tag, headline, sub-line (slides in from the left)
        off = int((1 - _ease(t / 0.55)) * -1100 * s)
        tag, head, sub = (42, 520, 242, 556), (42, 556, 1018, 628), (42, 628, 1018, 662)
        two = len(self.hlines) > 1
        d.rectangle([int(tag[0] * s) + off, int(tag[1] * s), int(tag[2] * s) + off, int(tag[3] * s)], fill=(225, 30, 45, 255))
        tf = _font(self.font_path, int(22 * s))
        tw = d.textlength(self.category, font=tf)
        _bold(d, (int((tag[0] + tag[2]) / 2 * s - tw / 2) + off, int(526 * s)), self.category, tf, (255, 255, 255, 255), s, 0.9)
        d.rectangle([int(head[0] * s) + off, int(head[1] * s), int(head[2] * s) + off, int(head[3] * s)], fill=(250, 251, 255, 255))
        d.rectangle([int(sub[0] * s) + off, int(sub[1] * s), int(sub[2] * s) + off, int(sub[3] * s)], fill=(14, 34, 86, 255))
        lh = int(self.hfont.size * 1.08)
        y = int(head[1] * s) + (int((head[3] - head[1]) * s) - lh * len(self.hlines)) // 2
        for line in self.hlines:
            _bold(d, (int(head[0] * s) + int(22 * s) + off, y), line, self.hfont, (14, 34, 86, 255), s, 1.2)
            y += lh
        if self.subhead:
            d.text((int(head[0] * s) + int(22 * s) + off, int(sub[1] * s) + int((sub[3] - sub[1]) * s / 2 - self.sfont.size * 0.62)),
                   self.subhead[:96], font=self.sfont, fill=(240, 245, 255, 255))
        # UP NEXT panel: two headlines at a time, rotating
        px0, py0, px1, py1 = 1034, 520, 1244, 662
        d.rectangle([int(px0 * s), int(py0 * s), int(px1 * s), int(py1 * s)], fill=(14, 34, 86, 235))
        d.rectangle([int(px0 * s), int(py0 * s), int(px1 * s), int((py0 + 30) * s)], fill=(225, 30, 45, 255))
        _bold(d, (int((px0 + 12) * s), int((py0 + 4) * s)), "UP NEXT", _font(self.font_path, int(18 * s)), (255, 255, 255, 255), s, 0.8)
        nf = _font(self.font_path, int(15 * s))
        pair = int(t / 4.0) % max(1, (len(self.items) + 1) // 2)
        for row in range(2):
            idx = pair * 2 + row
            if idx >= len(self.items):
                break
            lines = _wrap(d, self.items[idx], nf, (px1 - px0 - 40) * s, 8) or [self.items[idx][:40]]
            if len(lines) > 2:
                lines = [lines[0], lines[1].rstrip() + "..."]
            yy = int((py0 + 38 + row * 50) * s)
            d.rectangle((int((px0 + 12) * s), yy + int(5 * s), int((px0 + 18) * s), yy + int(11 * s)), fill=(225, 30, 45, 255))
            for ln in lines[:2]:
                d.text((int((px0 + 26) * s), yy), ln, font=nf, fill=(240, 245, 255, 255))
                yy += int(19 * s)
        strip, w = self.strip                                          # news strip, one headline after another
        x = int(t * 95 * s) % w
        frame.alpha_composite(strip.crop((x, 0, x + W - int(170 * s), strip.height)), (int(160 * s), int(682 * s)))


# ---------------------------------------------------------------- funky

PALETTE = [(255, 52, 130), (255, 140, 40), (255, 214, 52), (60, 214, 190), (120, 80, 255), (255, 52, 130)]


def _gradient(size):
    """Diagonal colour field that repeats every `width` px in x, so shifting the crop loops forever."""
    W, H = size
    x = np.arange(W * 2)[None, :] + 0.45 * np.arange(H)[:, None]
    u = (x % W) / W * (len(PALETTE) - 1)
    lo = np.floor(u).astype(int)
    f = (u - lo)[..., None]
    f = f * f * (3 - 2 * f)
    pal = np.array(PALETTE, dtype=np.float32)
    return Image.fromarray((pal[lo] * (1 - f) + pal[np.minimum(lo + 1, len(PALETTE) - 1)] * f).astype("uint8"))


def _halftone(size, gap):
    W, H = size
    L = Image.new("RGBA", (W + 2 * gap, H + 2 * gap), (0, 0, 0, 0))
    d = ImageDraw.Draw(L)
    for row, y in enumerate(range(0, L.height + gap, gap)):
        for x in range(0 if row % 2 == 0 else gap // 2, L.width + gap, gap):
            r = gap * 0.34 * (0.35 + 0.65 * (x / L.width))        # dots grow to the right
            d.ellipse((x - r, y - r, x + r, y + r), fill=(0, 0, 0, 52))
    return L


def _outline(rgba, grow, color):
    """The silhouette grown by about `grow` px: blur then threshold (PIL's MaxFilter is ~40x slower at this size)."""
    a = rgba.getchannel("A").filter(ImageFilter.GaussianBlur(grow * 0.62))
    out = Image.new("RGBA", rgba.size, color)
    out.putalpha(a.point(lambda v: min(255, v * 12)))
    return out


def _word_timeline(captions, per=5):
    groups = []
    for a, b, text in captions:
        words = text.split()
        if not words:
            continue
        tot = sum(len(w) + 2 for w in words)
        t, ws = a, []
        for w in words:
            dur = (b - a) * (len(w) + 2) / tot
            ws.append((t, t + dur, w))
            t += dur
        for k in range(0, len(ws), per):
            chunk = ws[k:k + per]
            groups.append({"t0": chunk[0][0], "t1": chunk[-1][1], "w": chunk})
    return groups


class Funky:
    """Moving gradient, halftone dots, tilted sticker photo, spinning starburst, outlined presenter, pop-in captions."""

    def __init__(self, size, headline, image, credit, channel, font_path, category, ticker, captions, laughs):
        self.size, self.s = size, size[0] / DW
        s = self.s
        self.font_path, self.channel = font_path, channel
        self.category = (category or "NEWS").upper()
        self.shot = Visual(image)
        self.grad = _gradient(size)
        self.gap = int(34 * s)
        self.dots = _halftone(size, self.gap)
        self.words = _word_timeline(captions or [])
        self.laughs = list(laughs)
        self.hfont, self.hlines = _fit(_measure(), headline, font_path, 980 * s, 66 * s, s, hi=40, lo=20)
        self.marquee = self._marquee(ticker)
        self.cap_font = _font(font_path, int(48 * s))
        self.laugh_font = _font(font_path, int(96 * s))
        self.star = self._star()

    def _star(self):
        s = self.s
        S = int(190 * s)
        im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        pts = []
        for k in range(28):
            r = (S / 2 - 3) * (1.0 if k % 2 == 0 else 0.78)
            a = math.pi * 2 * k / 28
            pts.append((S / 2 + r * math.cos(a), S / 2 + r * math.sin(a)))
        d.polygon(pts, fill=YELLOW, outline=INK, width=max(2, int(4 * s)))
        text = self.category[:9]
        font, _ = _fit(d, text, self.font_path, S * 0.7, S * 0.4, s, hi=34, lo=14, max_lines=1)
        tw = d.textlength(text, font=font)
        _bold(d, (S / 2 - tw / 2, S / 2 - font.size * 0.55), text, font, INK, s, 1.0)
        return im

    def _marquee(self, items):
        s = self.s
        text = "   *   ".join(x.upper() for x in (items or ["BOUGHT.", "NEWS IN A MINUTE"])) + "   *"
        return _loop_strip(text, _font(self.font_path, int(24 * s)), int(48 * s), YELLOW, INK, int(46 * s), int(10 * s), 1)

    def background(self, t):
        s, W, H = self.s, *self.size
        ox = int(t * 70 * s) % W
        bg = self.grad.crop((ox, 0, ox + W, H)).convert("RGBA")
        bg.alpha_composite(self.dots, (-int(t * 14 * s) % self.gap - self.gap, -int(t * 9 * s) % self.gap - self.gap))
        return bg

    def sticker(self, pres, e, t):
        """White + ink outline around the presenter, like a die-cut sticker; hops a little with the voice."""
        s = self.s
        out = Image.new("RGBA", pres.size, (0, 0, 0, 0))
        out.alpha_composite(_outline(pres, max(3, int(10 * s)), INK))
        out.alpha_composite(_outline(pres, max(2, int(6 * s)), (255, 255, 255, 255)))
        out.alpha_composite(pres)
        return out

    def card(self, frame, i, n, t, c, e):
        s = self.s
        zoom = 1.0 + 0.05 * i / max(1, n - 1)
        pop = 1 + 0.02 * e
        w, h = int(_lerp(660, 1280, c) * pop * s), int(_lerp(392, 640, c) * pop * s)
        cx, cy = _lerp(870, 640, c), _lerp(292, 320, c)
        bord = max(2, int(_lerp(11, 0, c) * s))
        card = Image.new("RGBA", (w, h), (255, 255, 255, 255))
        card.paste(self.shot.render(w - 2 * bord, h - 2 * bord, zoom).convert("RGBA"), (bord, bord))
        pad = int(30 * s)
        layer = Image.new("RGBA", (w + pad, h + pad), (0, 0, 0, 0))
        ImageDraw.Draw(layer).rectangle((pad // 2, pad // 2, pad // 2 + w, pad // 2 + h), fill=INK)   # hard comic shadow
        layer = Image.composite(layer, Image.new("RGBA", layer.size, (0, 0, 0, 0)), layer.getchannel("A"))
        shifted = Image.new("RGBA", layer.size, (0, 0, 0, 0))
        shifted.alpha_composite(layer, (int(10 * s * (1 - c)), int(12 * s * (1 - c))))
        shifted.alpha_composite(card, (pad // 2, pad // 2))
        ang = (-4.5 + 1.5 * math.sin(t * 1.7) + 0.6 * math.sin(t * 4.1)) * (1 - c)
        shifted = shifted.rotate(ang, resample=Image.BICUBIC, expand=True)
        frame.alpha_composite(shifted, (int(cx * s - shifted.width / 2), int(cy * s - shifted.height / 2)))
        return cx, cy

    def overlay(self, frame, i, n, t, c, e, card):
        s, W, H = self.s, *self.size
        k = _ease(t / 0.45)                                        # headline ribbon drops in at the start
        rib = Image.new("RGBA", (int(1040 * s), int(86 * s)), (0, 0, 0, 0))
        rd = ImageDraw.Draw(rib)
        rd.rectangle((0, 0, rib.width, rib.height), fill=INK)
        rd.rectangle((0, 0, int(14 * s), rib.height), fill=YELLOW)
        lh = int(self.hfont.size * 1.08)
        y = (rib.height - lh * len(self.hlines)) // 2
        for line in self.hlines:
            _bold(rd, (int(32 * s), y), line, self.hfont, (255, 255, 255, 255), s, 1.0)
            y += lh
        rib = rib.rotate(-1.4 + 0.5 * math.sin(t * 2.2), resample=Image.BICUBIC, expand=True)
        if c < 1:
            frame.alpha_composite(rib, (int(24 * s), int(_lerp(-130, 4, k) * s - 110 * s * c)))
        if c < 0.99:                                               # spinning starburst on the photo's corner
            st = self.star.rotate(t * 28, resample=Image.BICUBIC)
            sc = (1 + 0.07 * math.sin(t * 6)) * _ease(t / 0.6) * (1 - c)
            if sc > 0.02:
                st = st.resize((max(2, int(st.width * sc)), max(2, int(st.height * sc))), Image.BICUBIC)
                frame.alpha_composite(st, (int((card[0] - 330 + 10) * s - st.width / 2), int((card[1] + 196 - 10) * s - st.height / 2)))
        self.caption(frame, t, c)
        strip, w = self.marquee
        x = int(t * 130 * s) % w
        frame.alpha_composite(strip.crop((x, 0, x + W, strip.height)), (0, H - strip.height))
        ImageDraw.Draw(frame).rectangle((0, H - strip.height, W, H - strip.height + max(2, int(3 * s))), fill=YELLOW)
        bf = _font(self.font_path, int(28 * s))                    # channel sticker, tilted
        chip = Image.new("RGBA", (int(168 * s), int(52 * s)), (0, 0, 0, 0))
        cd = ImageDraw.Draw(chip)
        cd.rounded_rectangle((0, 0, chip.width - 1, chip.height - 1), radius=int(10 * s), fill=(255, 255, 255, 255),
                             outline=INK, width=max(2, int(3 * s)))
        tw = cd.textlength(self.channel, font=bf)
        _bold(cd, (chip.width / 2 - tw / 2, 8 * s), self.channel, bf, INK, s)
        chip = chip.rotate(5, resample=Image.BICUBIC, expand=True)
        frame.alpha_composite(chip, (int(1086 * s), int(20 * s)))

    def caption(self, frame, t, c):
        s, H = self.s, self.size[1]
        laugh = any(a <= t <= b for a, b in self.laughs)
        if laugh:
            words, act, font = ["HA", "HA", "HA!"], int(t * 4.2) % 3, self.laugh_font
        else:
            words, act, font = None, 0, self.cap_font
            for g in self.words:
                if g["t0"] - 0.05 <= t <= g["t1"] + 0.35:
                    words = [w[2] for w in g["w"]]
                    act = max([j for j, w in enumerate(g["w"]) if w[0] <= t + 0.02] or [0])
        if not words:
            return
        meas = _measure()
        gap = int(14 * s)
        widths = [meas.textlength(w, font=font) for w in words]
        maxw = (780 if c == 0 else 1100) * s
        lines, cur, curw = [], [], 0
        for j in range(len(words)):
            if cur and curw + widths[j] + gap > maxw:
                lines.append(cur); cur, curw = [], 0
            cur.append(j); curw += widths[j] + gap
        lines.append(cur)
        lh = int(font.size * 1.16)
        cx = (870 if c == 0 else 640) * s
        base_y = H - int(66 * s) - lh * len(lines)
        for ln, idxs in enumerate(lines):
            x = cx - (sum(widths[j] + gap for j in idxs) - gap) / 2
            for j in idxs:
                hot = j == act
                pop = 1 + 0.16 * max(0.0, 1 - ((t * 7) % 1.0) * 1.6) if hot else 1.0
                piece = Image.new("RGBA", (int(widths[j] + 40 * s), int(lh * 1.4)), (0, 0, 0, 0))
                ImageDraw.Draw(piece).text((20 * s, lh * 0.15), words[j], font=font, fill=YELLOW if hot else (255, 255, 255, 255),
                                           stroke_width=max(3, int(7 * s)), stroke_fill=INK)
                if pop != 1.0:
                    pw, ph = piece.size
                    piece = piece.resize((int(pw * pop), int(ph * pop)), Image.BICUBIC)
                    dx, dy = (piece.width - pw) / 2, (piece.height - ph) / 2
                else:
                    dx = dy = 0
                frame.alpha_composite(piece, (int(x - 20 * s - dx), int(base_y + ln * lh - dy)))
                x += widths[j] + gap


# ---------------------------------------------------------------- presenters and looks

CHARACTERS = ("photo", "anime", "mascot")
STYLES = ("studio", "channel", "funky")


def build_presenter(character, style, cfg, resolve):
    """The host for a look. The anime anchor is drawn larger and to the left for the channel set (as in the clips)."""
    size = tuple(cfg.avatar_size)
    if character == "mascot":
        from .mascot import MascotPresenter
        return MascotPresenter(size=size)
    if character == "anime":
        from .anime import AnimePresenter
        big = {"scale": 0.95, "origin": (8, 18)} if style == "channel" else {}
        return AnimePresenter(resolve("pipeline/assets/anime/cutout_raw.png"), size, **big)
    from .avatar import Presenter
    return Presenter(resolve(cfg.avatar_image), size)


def pick_look(item, cfg, rank=None):
    """(character, style) for a story: its category's look from config, else one of the looks picked by the story id,
    so a feed never shows one identical video over and over. Without avatar_looks everything is the original look."""
    if rank is not None and rank < cfg.avatar_first_count and cfg.avatar_first_look:
        return (cfg.avatar_first_look["character"], cfg.avatar_first_look["style"])
    looks = cfg.avatar_looks
    if not looks:
        return ("photo", "studio")
    by_category = {str(k).lower(): v for k, v in looks.items()}
    look = by_category.get(str(item.get("category", "")).lower())
    if look is None:
        ordered = [looks[k] for k in sorted(looks)]
        look = ordered[int(hashlib.sha1(str(item["id"]).encode()).hexdigest(), 16) % len(ordered)]
    return (look["character"], look["style"])


# ---------------------------------------------------------------- render loop

def render_styled(style, audio_path, out_mp4, presenter, headline, image, credit="", channel="BOUGHT.", font_path=None,
                  seed="", moods=None, cut_ranges=None, cutaway_chance=0.6, category="", ticker=None, captions=None,
                  laughs=(), subhead="", script="", journalist=None) -> None:
    out_mp4 = Path(out_mp4)
    tmp = out_mp4.with_suffix(".mp4.tmp")
    size, s = presenter.size, presenter.s
    env = envelope(audio_path)
    n = len(env)
    mo = motion(env, seed)
    strap = name_strap(size, journalist, font_path)
    cut = plan_from_ranges(n, cut_ranges) if cut_ranges is not None else cutaway_plan(n, seed, cutaway_chance)
    if not captions and script:                                   # no timings: spread the script over the speech
        captions = [(0.35, max(1.0, n / FPS - 0.6), script)]
    if style == "channel":
        st = Channel(size, headline, image, credit, channel, font_path, category, ticker, subhead)
    elif style == "funky":
        st = Funky(size, headline, image, credit, channel, font_path, category, ticker, captions, laughs)
    else:
        raise ValueError(f"unknown style {style!r}")
    rnd = int(hashlib.sha1(str(seed).encode()).hexdigest(), 16)
    next_blink, blink_seq = 40 + rnd % 40, {}
    while next_blink < n:
        for j, lv in enumerate((1, 2, 2, 1)):
            blink_seq[next_blink + j] = lv
        next_blink += 75 + (rnd >> 8) % 60
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{size[0]}x{size[1]}",
           "-r", str(FPS), "-i", "-", "-i", str(audio_path), "-c:v", "libx264", "-preset", "veryfast", "-crf", "21",
           "-profile:v", "high", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "128k", "-shortest",
           "-movflags", "+faststart", "-f", "mp4", str(tmp)]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    try:
        for i, e in enumerate(env):
            t, c, e = i / FPS, float(cut[i]), float(e)
            frame = st.background(t)
            if c < 1:
                pres = presenter.frame(K_MIN + (K_MAX - K_MIN) * e, blink_seq.get(i, 0), mo, i,
                                       moods[i] if moods is not None else "neutral")
                ox0, oy0 = presenter.origin
                if style == "funky":
                    pres = st.sticker(pres, e, t)
                    pos = (int((ox0 - 4 - 120 * c) * s), int((oy0 - abs(math.sin(t * 5.2)) * 5 * e) * s))
                else:
                    pos = (int((ox0 - 120 * c) * s), int(oy0 * s))
                mask = pres.getchannel("A")
                if c > 0:
                    mask = mask.point(lambda v: int(v * (1 - c)))
                frame.paste(pres, pos, mask)
            if style == "funky":
                card = st.card(frame, i, n, t, c, e)
                st.overlay(frame, i, n, t, c, e, card)
            else:
                st.draw(frame, i, n, t, c, e)
                st.lower(frame, i, t)
            put_strap(frame, strap, style, s, c)
            p.stdin.write(frame.convert("RGB").tobytes())
        p.stdin.close()
        if p.wait(timeout=600) != 0:
            raise RuntimeError("ffmpeg failed")
        os.replace(tmp, out_mp4)
    finally:
        if p.poll() is None:
            p.kill()
        tmp.unlink(missing_ok=True)
