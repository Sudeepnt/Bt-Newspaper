"""A funky host drawn entirely in code (no image model, no artwork to license): magenta bob with a cyan streak,
big yellow headphones, a teal jacket with a star tee. Same engine as the other presenters (avatar.render_video).

Static layers (body, hair, headphones) are drawn once; each frame redraws only the face (eyes, brows, mouth, blush).
Coordinates are in a 520x650 character space, scaled to the output.
"""
from __future__ import annotations

import math

import numpy as np
from PIL import Image, ImageDraw

from .avatar import FPS, Presenter, studio_background

W, H = 520, 650
SCALE = 0.9
ORIGIN = (-4, 720 - H * SCALE)            # feet cut by the frame bottom, like the other hosts
SS = 3                                    # supersampling
INK = (34, 18, 54, 255)
SKIN = (248, 196, 156, 255)
SKIN_SHADE = (232, 164, 128, 255)
HAIR = (255, 62, 158, 255)
HAIR_DARK = (214, 30, 120, 255)
STREAK = (40, 224, 224, 255)
GOLD = (255, 214, 40, 255)
TEAL = (24, 196, 188, 255)
TEAL_DARK = (12, 150, 150, 255)
HEAD_BOX = (70, 10, 450, 430)             # the part that nods and tilts
FACE_BOX = (150, 185, 370, 375)           # redrawn every frame
HEAD_PIVOT = (260, 372)
BODY_PIVOT = (260, 650)
EYES = ((213, 258), (307, 258))
BASE_SMILE = {"neutral": 0.4, "happy": 0.85, "laugh": 1.0, "serious": 0.0}


class _Canvas:
    """Draw in character units on a supersampled RGBA image."""

    def __init__(self, box, q):
        self.box, self.q = box, q
        self.w, self.h = int((box[2] - box[0]) * q), int((box[3] - box[1]) * q)
        self.img = Image.new("RGBA", (self.w * SS, self.h * SS), (0, 0, 0, 0))
        self.d = ImageDraw.Draw(self.img)

    def p(self, x, y):
        return ((x - self.box[0]) * self.q * SS, (y - self.box[1]) * self.q * SS)

    def pts(self, pts):
        return [self.p(x, y) for x, y in pts]

    def lw(self, v):
        return max(1, int(v * self.q * SS))

    def poly(self, pts, fill, line=6):
        self.d.polygon(self.pts(pts), fill=fill, outline=INK, width=self.lw(line) if line else 0)

    def ellipse(self, cx, cy, rx, ry, fill, line=6):
        (x0, y0), (x1, y1) = self.p(cx - rx, cy - ry), self.p(cx + rx, cy + ry)
        self.d.ellipse((x0, y0, x1, y1), fill=fill, outline=INK if line else None, width=self.lw(line) if line else 0)

    def rrect(self, x0, y0, x1, y1, r, fill, line=6):
        a, b = self.p(x0, y0), self.p(x1, y1)
        self.d.rounded_rectangle((a[0], a[1], b[0], b[1]), radius=r * self.q * SS, fill=fill, outline=INK,
                                 width=self.lw(line))

    def line(self, pts, fill, width):
        self.d.line(self.pts(pts), fill=fill, width=self.lw(width), joint="curve")

    def done(self):
        return self.img.resize((self.w, self.h), Image.LANCZOS)


def _star(cx, cy, r, n=5, inner=0.45, rot=-90):
    out = []
    for k in range(n * 2):
        a = math.radians(rot + k * 180 / n)
        rr = r if k % 2 == 0 else r * inner
        out.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    return out


class MascotPresenter(Presenter):
    def __init__(self, cutout_path=None, size=(1280, 720), scale=SCALE, origin=ORIGIN):
        self.size = size
        self.s = size[0] / 1280
        self.scale, self._origin = scale, origin
        self.q = self.s * scale
        self.background = studio_background((int(size[0] * 1.06), int(size[1] * 1.06)))
        self._build()

    @property
    def origin(self):
        return self._origin

    # ---- static layers

    def _build(self):
        q = self.q
        full = (0, 0, W, H)
        c = _Canvas(full, q)
        # neck + torso + tee + jacket
        c.poly([(228, 330), (292, 330), (298, 430), (222, 430)], SKIN)
        c.poly([(30, 650), (36, 490), (78, 432), (190, 402), (330, 402), (442, 432), (484, 490), (490, 650)], TEAL)
        c.poly([(206, 404), (314, 404), (292, 650), (228, 650)], (255, 255, 255, 255), line=5)
        c.poly(_star(260, 560, 40), GOLD, line=5)
        c.poly([(190, 402), (222, 408), (226, 650), (170, 650)], HAIR, line=5)           # jacket facings
        c.poly([(330, 402), (298, 408), (294, 650), (350, 650)], HAIR, line=5)
        c.poly([(150, 410), (212, 396), (240, 470), (196, 470)], TEAL_DARK, line=5)        # popped collar
        c.poly([(370, 410), (308, 396), (280, 470), (324, 470)], TEAL_DARK, line=5)
        c.ellipse(260, 405, 40, 22, SKIN_SHADE, line=0)
        self.body = c.done()
        # head: hair behind the face, face, ears
        hb = _Canvas(HEAD_BOX, q)
        hb.ellipse(260, 232, 152, 162, HAIR_DARK)
        hb.poly([(112, 250), (108, 352), (96, 398), (150, 392), (196, 340), (190, 250)], HAIR)    # bob, flicking out
        hb.poly([(408, 250), (412, 352), (424, 398), (370, 392), (324, 340), (330, 250)], HAIR)
        hb.ellipse(160, 262, 22, 30, SKIN)
        hb.ellipse(360, 262, 22, 30, SKIN)
        hb.ellipse(260, 255, 102, 120, SKIN)
        self.head_base = hb.done()
        # head front: fringe, streak, headphones
        ht = _Canvas(HEAD_BOX, q)
        ht.poly([(156, 252), (150, 196), (170, 136), (222, 100), (292, 92), (352, 122), (374, 188), (368, 252),
                 (346, 214), (318, 170), (278, 190), (240, 168), (204, 206), (180, 238)], HAIR)
        ht.poly([(196, 112), (232, 102), (258, 106), (226, 176), (206, 200), (186, 184)], STREAK, line=4)
        ht.line([(128, 232), (146, 140), (200, 82), (260, 70), (320, 82), (374, 140), (392, 232)], INK, 22)
        ht.line([(128, 232), (146, 140), (200, 82), (260, 70), (320, 82), (374, 140), (392, 232)], GOLD, 13)
        for x0 in (112, 360):
            ht.rrect(x0, 206, x0 + 48, 306, 20, GOLD)
            ht.ellipse(x0 + 24, 256, 12, 12, HAIR, line=4)
        self.head_top = ht.done()

    # ---- face (every frame)

    def _face(self, a, smile, eyes, mood, gx, brow):
        q = self.q
        c = _Canvas(FACE_BOX, q)
        laugh = mood == "laugh"
        # blush and freckles, a cheek star
        c.ellipse(190, 308, 20, 11, (255, 120, 140, 150 if mood in ("happy", "laugh") else 70), line=0)
        c.ellipse(330, 308, 20, 11, (255, 120, 140, 150 if mood in ("happy", "laugh") else 70), line=0)
        for dx, dy in ((-8, 0), (4, 5), (14, -2)):
            c.ellipse(332 + dx, 292 + dy, 2.2, 2.2, SKIN_SHADE, line=0)
        c.poly(_star(176, 296, 11, inner=0.5), GOLD, line=2.5)
        # brows: raised when excited, inner ends pulled down when serious
        for sgn, (ex, ey) in zip((-1, 1), EYES):
            by = ey - 44 - brow * 4.5
            ox, ix = ex + 26 * sgn, ex - 26 * sgn
            oy, iy = (by - 2, by + 7) if mood == "serious" else (by + 5, by + 1)
            c.line([(ox, oy), (ex, by - 6 + (3 if mood == "serious" else 0)), (ix, iy)], INK, 8)
        # eyes
        for k, (ex, ey) in enumerate(EYES):
            if eyes == "happy":                                                              # ^ ^ (laughing)
                c.line([(ex - 24, ey + 8), (ex, ey - 14), (ex + 24, ey + 8)], INK, 9)
            elif eyes == "closed":
                c.line([(ex - 24, ey + 2), (ex, ey + 10), (ex + 24, ey + 2)], INK, 8)
            else:
                ry = 34 if eyes == "open" else 17
                c.ellipse(ex, ey, 27, ry, (255, 255, 255, 255), line=5)
                ix = ex + gx
                c.ellipse(ix, ey + 2, 17, min(ry - 3, 22), (24, 120, 230, 255), line=0)
                c.ellipse(ix, ey + 3, 9, min(ry - 6, 12), INK, line=0)
                c.ellipse(ix - 6, ey - 7, 5, 5, (255, 255, 255, 255), line=0)
        # nose
        c.line([(256, 288), (262, 300), (270, 300)], INK, 5)
        # mouth
        mx, my = 260, 332
        hw = 30 + 12 * smile
        if laugh:
            a = max(a, 0.6)
        if a < 0.1 and not laugh:
            if smile < 0.05:
                c.line([(mx - hw * 0.7, my + 2), (mx + hw * 0.7, my + 2)], INK, 6)
            else:
                dip = 6 + 12 * smile
                c.line([(mx - hw + i * hw / 6, my + dip * math.sin(math.pi * i / 12)) for i in range(13)], INK, 6)
        else:
            h = 8 + 44 * a
            half = hw * (0.82 + 0.25 * a)
            top = my - 8 - 4 * a
            box = c.p(mx - half, top) + c.p(mx + half, my + h)
            mouth = Image.new("RGBA", c.img.size, (0, 0, 0, 0))
            md = ImageDraw.Draw(mouth)
            md.ellipse(box, fill=(110, 28, 60, 255))
            mask = mouth.getchannel("A")
            md.ellipse(c.p(mx - half * 0.6, my + h * 0.5) + c.p(mx + half * 0.6, my + h * 1.5), fill=(240, 110, 130, 255))
            if a > 0.2:
                md.rectangle(c.p(mx - half, top - 2) + c.p(mx + half, top + 6 + h * 0.2), fill=(255, 255, 255, 255))
            clipped = Image.new("RGBA", mouth.size, (0, 0, 0, 0))
            clipped.paste(mouth, (0, 0), mask)
            c.img.alpha_composite(clipped)
            c.d.ellipse(box, outline=INK, width=c.lw(6))
        return c.done()

    def frame(self, mouth_k, blink, m, i, mood="neutral"):
        t = i / FPS
        a = float(np.clip((mouth_k + 0.25) / 0.85, 0, 1))
        laugh = mood == "laugh"
        smile = BASE_SMILE.get(mood, 0.4)
        if laugh:
            a = 0.55 + 0.4 * (0.5 + 0.5 * math.sin(t * 2 * math.pi * 3.2))
        eyes = "happy" if laugh else ("closed" if blink == 2 else "half" if blink == 1 else "open")
        gx = float(m["gaze"][i]) * 0.5
        face = self._face(a, smile, eyes, mood, gx, float(m["brow"][i]))
        q = self.q
        head = self.head_base.copy()
        head.alpha_composite(face, (int((FACE_BOX[0] - HEAD_BOX[0]) * q), int((FACE_BOX[1] - HEAD_BOX[1]) * q)))
        head.alpha_composite(self.head_top)
        ang = float(m["head_angle"][i]) * (1.0 if laugh else 0.8)
        dy = float(m["head_dy"][i]) + (3.5 * math.sin(t * 2 * math.pi * 3.2) if laugh else 0)
        if laugh:
            ang += 1.6 * math.sin(t * 2 * math.pi * 1.6)
        head = head.rotate(ang, resample=Image.BILINEAR,
                           center=((HEAD_PIVOT[0] - HEAD_BOX[0]) * q, (HEAD_PIVOT[1] - HEAD_BOX[1]) * q),
                           translate=(float(m["head_dx"][i]) * q, dy * q))
        img = self.body.copy()
        img.alpha_composite(head, (int(HEAD_BOX[0] * q), int(HEAD_BOX[1] * q)))
        sc = float(m["breath"][i] * m["drift"][i])
        rad = math.radians(float(m["body_angle"][i]))
        px, py = BODY_PIVOT[0] * q, BODY_PIVOT[1] * q
        cs, sn = math.cos(rad) / sc, math.sin(rad) / sc
        return img.transform(img.size, Image.AFFINE, (cs, sn, px - cs * px - sn * py, -sn, cs, py + sn * px - cs * py),
                             Image.BILINEAR)
