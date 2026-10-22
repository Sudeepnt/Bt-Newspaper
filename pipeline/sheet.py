"""A host drawn from a character reference sheet: one cut-out bust (pipeline/assets/sheet/neutral.png, made from the sheet's
Neutral tile) whose mouth is painted open and shut from the voice, with a little head sway. Same interface as AnimePresenter."""
from __future__ import annotations

import math

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

MOUTH = (172, 281)          # centre of the closed mouth in the cut-out (308 x 392)
SKIN_AT = (172, 304)        # a patch of cheek/chin just under the mouth


class SheetPresenter:
    def __init__(self, cutout_path, size, scale=1.5, origin=(700, 120), grade=False):
        self.size, self.scale, self._origin = size, scale, origin
        self.s = size[0] / 1280
        self.grade = grade                                  # already a dark painting: the editorial look must not dim it again
        self.base = Image.open(cutout_path).convert("RGBA")
        px = np.asarray(self.base.convert("RGB"), np.float32)
        x, y = MOUTH                                        # the skin on both sides of the mouth, so the patch matches its shading
        side = np.concatenate([px[y - 4:y + 4, x - 40:x - 26].reshape(-1, 3), px[y - 4:y + 4, x + 26:x + 40].reshape(-1, 3)])
        self.skin = tuple(int(v) for v in np.median(side, axis=0))

    @property
    def origin(self):
        return self._origin

    def _mouth(self, img, a):
        """Paint the mouth over the closed one: a = 0 closed .. 1 wide open. Supersampled so the edges are smooth."""
        if a < 0.08:
            return
        S = 4
        cx, cy = MOUTH
        x0, y0, x1, y1 = cx - 46, cy - 26, cx + 46, cy + 34
        patch = Image.new("RGBA", ((x1 - x0) * S, (y1 - y0) * S), self.skin + (0,))      # skin-coloured, so the soft edge does not darken
        d = ImageDraw.Draw(patch)
        mx, my = (cx - x0) * S, (cy - y0) * S
        d.ellipse((mx - 27 * S, my - 8 * S, mx + 27 * S, my + 6 * S), fill=self.skin + (255,))   # skin over the closed line
        w = (13 + 8 * a) * S
        h = (2 + 21 * a) * S
        top, bot = my - h * 0.3, my + h * 0.7
        mouth = Image.new("L", patch.size, 0)
        ImageDraw.Draw(mouth).ellipse((mx - w, top, mx + w, bot), fill=255)
        inside = Image.new("RGBA", patch.size, (74, 24, 32, 255))
        ind = ImageDraw.Draw(inside)
        ind.ellipse((mx - w * 0.7, my + h * 0.05, mx + w * 0.7, bot + h * 0.5), fill=(190, 82, 92, 255))   # tongue, clipped by the mouth
        if a > 0.45:                                                                                      # a hint of upper teeth when wide
            ind.rectangle((mx - w * 0.6, top, mx + w * 0.6, top + h * 0.16), fill=(238, 232, 226, 255))
        patch.paste(inside, (0, 0), mouth)
        d.arc((mx - w, top, mx + w, bot), 200, 340, fill=(64, 34, 32, 255), width=max(1, int(1.8 * S)))     # upper lip line
        patch = patch.resize((x1 - x0, y1 - y0), Image.BOX)           # BOX: Lanczos rings a pale halo round the edge
        feather = patch.getchannel("A").filter(ImageFilter.GaussianBlur(1.6))
        patch.putalpha(feather)
        img.alpha_composite(patch, (x0, y0))

    def frame(self, mouth_k, blink, m, i, mood="neutral"):
        a = float(np.clip((mouth_k + 0.25) / 0.85, 0, 1))
        img = self.base.copy()
        self._mouth(img, a)
        ang = float(m["head_angle"][i]) * 0.55
        dy = float(m["head_dy"][i]) * 1.2
        img = img.rotate(ang, resample=Image.BICUBIC, center=(img.width / 2, img.height), translate=(0, dy))
        k = self.s * self.scale
        return img.resize((round(img.width * k), round(img.height * k)), Image.LANCZOS)
