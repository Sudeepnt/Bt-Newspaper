"""The anime news anchor: same engine as the photo presenter (avatar.render_video), different face rigging.

The artwork is flat-shaded, so instead of warping pixels we paint over the face: the original mouth/eyes are covered
with the local skin colour and new mouth shapes, closed eyes and happy arcs are drawn on top (4x supersampled).
Coordinates are in the cutout's own pixel space (527x650).
"""
from __future__ import annotations

import math

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

from .avatar import FPS, Presenter, studio_background, _shift_patch

EYES = ((221, 227), (312, 227))
MOUTH = (263, 299)
HEAD_PIVOT = (264, 372)
BODY_PIVOT = (264, 650)
HEAD_BOX = (60, 0, 470, 450)
SCALE = 0.9                    # 527 px wide -> ~474 px: the cut sides of the jacket hide behind the frame edge / monitor
ORIGIN = (-4, 720 - 650 * SCALE)
SS = 4                         # supersampling for drawn shapes
INK = (74, 36, 38, 255)
MOUTH_IN = (122, 40, 56, 255)
TONGUE = (226, 110, 118, 255)
TEETH = (252, 246, 240, 255)
BASE_SMILE = {"neutral": 0.35, "happy": 0.8, "laugh": 1.0, "serious": 0.0}


def _median(img, box):
    return tuple(int(v) for v in np.median(np.asarray(img.crop(box).convert("RGB")).reshape(-1, 3), axis=0))


def _cover(img, box, color, blur=1.6):
    """Flat-colour feathered patch (the art is flat-shaded, so this is invisible)."""
    ov = Image.new("L", img.size, 0)
    ImageDraw.Draw(ov).ellipse(box, fill=255)
    ov = ov.filter(ImageFilter.GaussianBlur(blur))
    img.paste(Image.new("RGBA", img.size, color + (255,)), (0, 0), ov)


def _draw_mouth(img, a: float, smile: float, skin):
    cx, cy = MOUTH
    box = (cx - 30, cy - 15, cx + 30, cy + 15)
    _cover(img, box, skin)
    W, H = (box[2] - box[0]) * SS, (box[3] - box[1]) * SS
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    ox, oy = box[0], box[1]
    X = lambda x: (x - ox) * SS
    Y = lambda y: (y - oy) * SS
    w = 34 + 5 * a + 3 * smile
    n = 48
    us = np.linspace(-1, 1, n)
    arch = 1 - us ** 2
    base = cy + smile * 2.4 * arch                                  # corners up when smiling
    xs = cx + us * w / 2
    if a < 0.07:                                                    # closed: one soft line
        pts = [(X(x), Y(y)) for x, y in zip(xs, base)]
        d.line(pts, fill=INK, width=int(1.7 * SS), joint="curve")
        for sx in (-1, 1):                                          # little corner ticks
            x, y = cx + sx * w / 2, cy
            d.line([(X(x), Y(y - 0.5)), (X(x + sx * 1.6), Y(y - 1.6 * smile - 0.2))], fill=INK, width=int(1.4 * SS))
    else:
        depth = 1.2 + a * 15
        upper = base - 0.9 * arch * min(1, a * 3)
        lower = base + depth * arch ** 0.75
        poly = [(X(x), Y(y)) for x, y in zip(xs, upper)] + [(X(x), Y(y)) for x, y in zip(xs[::-1], lower[::-1])]
        shape = Image.new("L", (W, H), 0)
        ImageDraw.Draw(shape).polygon(poly, fill=255)
        fill = Image.new("RGBA", (W, H), MOUTH_IN)
        fd = ImageDraw.Draw(fill)
        tooth_h = min(depth * 0.5, 3.4)                             # upper teeth strip
        tpoly = [(X(x), Y(y)) for x, y in zip(xs[6:-6], upper[6:-6])] + \
                [(X(x), Y(y + tooth_h * (1 - u * u) ** 0.5)) for x, y, u in zip(xs[6:-6][::-1], upper[6:-6][::-1], us[6:-6][::-1])]
        fd.polygon(tpoly, fill=TEETH)
        tw = w * 0.34
        fd.ellipse((X(cx - tw), Y(cy + depth * 0.45), X(cx + tw), Y(cy + depth * 1.25 + smile)), fill=TONGUE)   # tongue
        layer.paste(fill, (0, 0), shape)
        d.line([(X(x), Y(y)) for x, y in zip(xs, upper)], fill=INK, width=int(1.5 * SS), joint="curve")
        d.line([(X(x), Y(y)) for x, y in zip(xs, lower)], fill=INK, width=int(1.3 * SS), joint="curve")
    img.alpha_composite(layer.resize((W // SS, H // SS), Image.LANCZOS), (ox, oy))


def _draw_eyes(img, state: str, skin):
    """state: open | half | closed | happy"""
    if state == "open":
        return
    for cx, cy in EYES:
        top = cy - 12 if state != "half" else cy - 12
        bottom = cy + 13 if state != "half" else cy - 2
        _cover(img, (cx - 29, top - 2, cx + 29, bottom + 3), skin, 2.0)
        W, H = 64 * SS, 40 * SS
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(layer)
        ox, oy = cx - 32, cy - 20
        X = lambda x: (x - ox) * SS
        Y = lambda y: (y - oy) * SS
        if state == "happy":                                        # ^ ^  upward arc
            pts = [(X(cx + u * 19), Y(cy + 4 - 11 * (1 - u * u))) for u in np.linspace(-1, 1, 30)]
            d.line(pts, fill=INK, width=int(3.2 * SS), joint="curve")
        else:                                                       # closed lid, slightly curved down, lash flick
            yb = cy + (0 if state == "half" else 3)
            pts = [(X(cx + u * 20), Y(yb + 3.5 * (1 - u * u))) for u in np.linspace(-1, 1, 30)]
            d.line(pts, fill=INK, width=int(2.6 * SS), joint="curve")
            side = 1 if cx > 260 else -1
            d.line([(X(cx + side * 20), Y(yb)), (X(cx + side * 25), Y(yb - 2.5))], fill=INK, width=int(2 * SS))
        img.alpha_composite(layer.resize((W // SS, H // SS), Image.LANCZOS), (ox, oy))


def _blush(img, amount: float):
    if amount <= 0:
        return
    ov = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    for cx, cy in EYES:
        d.ellipse((cx - 20, cy + 14, cx + 20, cy + 32), fill=(240, 120, 110, int(70 * amount)))
    img.alpha_composite(ov.filter(ImageFilter.GaussianBlur(6)))


class AnimePresenter(Presenter):
    def __init__(self, cutout_path, size, scale=SCALE, origin=ORIGIN):
        self.size = size
        self.scale, self._origin = scale, origin
        self.s = size[0] / 1280
        self.base = Image.open(cutout_path).convert("RGBA")
        self.background = studio_background((int(size[0] * 1.06), int(size[1] * 1.06)))
        ramp = np.clip((402 - np.arange(self.base.size[1])) / 55, 0, 1)
        self.head_mask = Image.fromarray((np.repeat(ramp[:, None], self.base.size[0], axis=1) * 255).astype("uint8"))
        self.skin = _median(self.base, (236, 322, 292, 332))      # chin/cheek just under the mouth
        self.eye_skin = _median(self.base, (200, 252, 245, 262))

    @property
    def origin(self):
        return self._origin

    def frame(self, mouth_k, blink, m, i, mood="neutral"):
        t = i / FPS
        a = float(np.clip((mouth_k + 0.25) / 0.85, 0, 1))          # avatar's loudness-driven value 0..1
        img = self.base.copy()
        laugh = mood == "laugh"
        smile = BASE_SMILE.get(mood, 0.35)
        if laugh:
            a = 0.55 + 0.4 * (0.5 + 0.5 * math.sin(t * 2 * math.pi * 3.2))   # ha-ha-ha opening/closing
        eyes = "happy" if laugh else ("closed" if blink == 2 else "half" if blink == 1 else "open")
        gx = round(float(m["gaze"][i]) * 0.6)
        if gx and eyes == "open":
            for cx, cy in EYES:
                _shift_patch(img, (cx - 20, cy - 10, cx + 20, cy + 10), gx, 0)
        _draw_eyes(img, eyes, self.eye_skin)
        _draw_mouth(img, a, smile, self.skin)
        _blush(img, 1.0 if laugh else 0.35 if mood == "happy" else 0.0)
        # head
        ang = float(m["head_angle"][i]) * (0.8 if not laugh else 1.0)
        dy = float(m["head_dy"][i])
        if laugh:
            dy += 3.5 * math.sin(t * 2 * math.pi * 3.2)
            ang += 1.6 * math.sin(t * 2 * math.pi * 1.6)
        hb = HEAD_BOX
        head = img.crop(hb).rotate(ang, resample=Image.BILINEAR, center=(HEAD_PIVOT[0] - hb[0], HEAD_PIVOT[1] - hb[1]),
                                   translate=(float(m["head_dx"][i]), dy))
        img.paste(head, hb[:2], self.head_mask.crop(hb))
        sc = float(m["breath"][i] * m["drift"][i]) * (1 + (0.006 * math.sin(t * 2 * math.pi * 3.2) if laugh else 0))
        rad = math.radians(float(m["body_angle"][i]))
        px, py = BODY_PIVOT
        c, sn = math.cos(rad) / sc, math.sin(rad) / sc
        img = img.transform(img.size, Image.AFFINE, (c, sn, px - c * px - sn * py, -sn, c, py + sn * px - c * py),
                            Image.BILINEAR)
        k = self.s * self.scale
        return img.resize((round(img.width * k), round(img.height * k)), Image.LANCZOS)
