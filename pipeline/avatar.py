"""Phase 2b: news-style presenter video from audio, CPU only (Pillow + numpy + ffmpeg).

16:9 frame: presenter (left, cut out at the waist) on a soft blue studio, a framed monitor with the story image
slowly zooming (right), a dark headline bar with a channel badge (bottom). The presenter's mouth follows the
speech loudness, and she blinks and bobs slightly. This is a 2D animation, not neural lip-sync.
Layout numbers are in a 1280x720 design space and scaled to the output size.
"""
from __future__ import annotations

import hashlib
import math
import os
import subprocess
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

FPS = 25
LEVELS = 10
K_MIN, K_MAX = -0.25, 0.6        # vertical stretch of the lower face: closed .. wide open
MOUTH_REGION = (585, 255, 755, 430)   # in the presenter photo (1280x720)
MOUTH = (668, 310)
EYES = ((601, 216), (703, 202))       # eye centres in the presenter photo
PRES_SCALE = 0.66                     # she is small: bottom-left corner, about a third of the frame wide
PRES_X, PRES_Y = -211, 245            # where source (0, 0) lands in the design frame (feet/waist on the bottom edge)
MONITOR = (470, 28, 1262, 566)        # x0, y0, x1, y1 (outer bezel): ~50% of the screen
FULL = (0, 0, 1280, 575)              # cutaway: the news visual fills everything above the headline bar
CUTAWAY_FRAMES = 10                   # length of the expand / return transition
BAR = (110, 585, 1060, 685)
BADGE = (1075, 585, 1255, 685)
DESIGN = (1280, 720)


def envelope(audio_path, fps=FPS) -> np.ndarray:
    """Loudness 0..1 per video frame, smoothed so the mouth does not flicker."""
    pcm = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", str(audio_path), "-f", "s16le", "-ac", "1",
                          "-ar", "16000", "-"], capture_output=True, check=True, timeout=120).stdout
    x = np.frombuffer(pcm, np.int16).astype(np.float32) / 32768
    hop = 16000 // fps
    n = max(1, len(x) // hop)
    rms = np.sqrt((x[: n * hop].reshape(n, hop) ** 2).mean(axis=1))
    ref = np.percentile(rms, 90) or 1.0
    env = np.clip(rms / ref, 0, 1) ** 0.8
    return np.convolve(env, np.array([0.25, 0.5, 0.25]), mode="same")


def _mouth(base: Image.Image, k: float) -> Image.Image:
    x0, y0, x1, y1 = MOUTH_REGION
    reg = base.crop(MOUTH_REGION)
    w, h = reg.size
    ml = MOUTH[1] - y0
    nh = max(1, int(round((h - ml) * (1 + k))))
    new = Image.new("RGBA", (w, h))
    new.paste(reg.crop((0, 0, w, ml)), (0, 0))
    new.paste(reg.crop((0, ml, w, h)).resize((w, nh), Image.BICUBIC), (0, ml))
    if nh < h - ml:
        new.paste(reg.crop((0, ml + nh, w, h)), (0, ml + nh))
    yy, xx = np.mgrid[0:h, 0:w]
    m = np.clip(1 - np.hypot((xx - (MOUTH[0] - x0)) / 85, (yy - ml) / 95), 0, 1)
    mask = Image.fromarray((np.minimum(1, m * 2.5) * 255).astype("uint8"))
    out = base.copy()
    out.paste(Image.composite(new, reg, mask), (x0, y0))
    return out


EYE_BOX = (545, 165, 765, 255)


def _blink(img: Image.Image, level: int) -> Image.Image:
    """level 0 open, 1 half, 2 closed: skin-coloured lid over each eye plus a lash line (patch-local, fast)."""
    if level == 0:
        return img
    ox, oy = EYE_BOX[:2]
    patch = img.crop(EYE_BOX)
    ov = Image.new("RGBA", patch.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    px = patch.convert("RGB")
    for cx, cy in ((x - ox, y - oy) for x, y in EYES):
        # lid colour: a blend of the skin just above the eye and the cheek below it
        up = np.asarray(px.crop((cx - 12, cy - 22, cx + 12, cy - 17))).reshape(-1, 3)
        low = np.asarray(px.crop((cx - 10, cy + 20, cx + 10, cy + 28))).reshape(-1, 3) if cy + 28 <= patch.height else up
        skin = tuple(int(v) for v in (np.median(up, axis=0) * 0.6 + np.median(low, axis=0) * 0.4))
        bottom = cy + 7 if level == 2 else cy - 1
        d.ellipse((cx - 25, cy - 11, cx + 25, bottom + 3), fill=skin + (255,))
    ov = ov.filter(ImageFilter.GaussianBlur(3.0))
    d = ImageDraw.Draw(ov)
    for cx, cy in ((x - ox, y - oy) for x, y in EYES):
        y = cy + (4 if level == 2 else -3)
        d.arc((cx - 22, y - 6, cx + 22, y + 6), 20, 160, fill=(45, 30, 28, 200), width=2)
    patch.alpha_composite(ov)
    out = img.copy()
    out.paste(patch, (ox, oy))
    return out


def _font(path, size):
    f = ImageFont.truetype(str(path), size)
    try:
        f.set_variation_by_name("Bold")
    except Exception:  # static font or no 'Bold' instance
        pass
    return f


def _scale(box, s):
    return tuple(int(round(v * s)) for v in box)


def studio_background(size) -> Image.Image:
    """Soft blue studio: gradient, blurred light panels, vignette. Deterministic."""
    w, h = size
    yy = np.linspace(0, 1, h)[:, None, None]
    top, bottom = np.array([70, 120, 190]), np.array([22, 48, 108])
    img = Image.fromarray((top + (bottom - top) * yy).repeat(w, axis=1).astype("uint8"))
    panels = Image.new("RGBA", size, (0, 0, 0, 0))
    d = ImageDraw.Draw(panels)
    for i in range(7):
        x = int(w * (0.05 + i * 0.15))
        d.rectangle((x, int(h * 0.05), x + int(w * 0.08), int(h * 0.8)), fill=(190, 215, 255, 55 if i % 2 else 30))
    panels = panels.filter(ImageFilter.GaussianBlur(w * 0.012))
    img = img.convert("RGBA")
    img.alpha_composite(panels)
    return img


CROP = (250, 0, 1050, 720)           # the part of the 1280x720 cutout that contains her
HEAD_PIVOT = (650, 485)              # neck, in cutout coordinates
BODY_PIVOT = (650, 720)              # waist
BROWS = (545, 140, 770, 200)
HEAD_BOX = (300, 0, 1000, 580)


def _soft_ellipse(w, h, power=1.0):
    yy, xx = np.mgrid[0:h, 0:w]
    m = np.clip(1 - np.hypot((xx - w / 2) / (w / 2), (yy - h / 2) / (h / 2)), 0, 1) ** power
    return Image.fromarray((np.minimum(1, m * 3) * 255).astype("uint8"))


def _shift_patch(img, box, dx, dy):
    """Move the pixels inside box by (dx, dy), feathered at the edges (brow raise, gaze shift)."""
    if not dx and not dy:
        return
    reg = img.crop(box)
    w, h = reg.size
    moved = reg.copy()
    moved.paste(reg, (int(dx), int(dy)))
    img.paste(Image.composite(moved, reg, _soft_ellipse(w, h)), box[:2])


def motion(env: np.ndarray, seed: str, fps=FPS) -> dict:
    """Per-frame body language derived from the speech loudness plus slow, seed-dependent drift."""
    n = len(env)
    rnd = np.random.default_rng(int(hashlib.sha1(str(seed).encode()).hexdigest()[:8], 16))
    t = np.arange(n) / fps
    ph = rnd.uniform(0, 2 * np.pi, 6)
    # emphasis = how fast the voice gets louder; smoothed and decaying so a nod/brow-raise lasts ~0.3 s
    rise = np.clip(np.diff(env, prepend=env[0]) * fps, 0, None)
    emph = np.zeros(n)
    for i in range(1, n):
        emph[i] = max(emph[i - 1] * 0.88, min(1.0, rise[i] / 2.5))
    gaze = np.zeros(n)
    cur, tgt, nxt = 0.0, 0.0, int(rnd.integers(30, 70))
    for i in range(n):
        if i >= nxt:
            tgt = float(rnd.choice([-2.5, -1.5, 0, 0, 1.5, 2.5]))
            nxt = i + int(rnd.integers(40, 90))
        cur += (tgt - cur) * 0.25
        gaze[i] = cur
    return {
        "head_angle": 1.3 * np.sin(2 * np.pi * t / 4.1 + ph[0]) + 0.7 * np.sin(2 * np.pi * t / 2.3 + ph[1]),
        "head_dy": -4.0 * emph + 1.5 * np.sin(2 * np.pi * t / 3.3 + ph[2]),
        "head_dx": 2.0 * np.sin(2 * np.pi * t / 5.0 + ph[3]),
        "body_angle": 0.45 * np.sin(2 * np.pi * t / 6.0 + ph[4]),
        "breath": 1 + 0.004 * np.sin(2 * np.pi * t / 3.8 + ph[5]),
        "drift": 1 + 0.03 * t / max(t[-1], 1e-6),                # slow camera push-in
        "brow": np.clip(emph * 1.3, 0, 1),
        "gaze": gaze,
        "emph": emph,
    }


class Presenter:
    """Holds the cutout and animates it frame by frame: mouth, blink, brows, gaze, head tilt/nod, breathing."""

    def __init__(self, cutout_path, size):
        self.size = size
        self.s = size[0] / DESIGN[0]
        self.base = Image.open(cutout_path).convert("RGBA")
        self.background = studio_background((int(size[0] * 1.06), int(size[1] * 1.06)))   # a little larger, so it can drift
        head = Image.new("L", self.base.size, 0)                 # 1 above the neck, 0 below, soft in between
        ramp = np.clip((HEAD_PIVOT[1] + 30 - np.arange(self.base.size[1])) / 70, 0, 1)
        self.head_mask = Image.fromarray((np.repeat(ramp[:, None], self.base.size[0], axis=1) * 255).astype("uint8"))
        self.skin = {}

    @property
    def origin(self):
        """Where the frame image lands in the 1280x720 design frame."""
        return CROP[0] * PRES_SCALE + PRES_X, PRES_Y

    def frame(self, mouth_k, blink, m, i, mood="neutral"):
        """One presenter RGBA image at output scale for frame i."""
        img = self.base.copy()
        img = _mouth(img, mouth_k)
        _shift_patch(img, BROWS, 0, -round(4.5 * float(m["brow"][i])))
        gx = round(float(m["gaze"][i]))
        for cx, cy in EYES:
            _shift_patch(img, (cx - 24, cy - 9, cx + 24, cy + 9), gx, 0)
        img = _blink(img, blink)
        # head: rotate/nod about the neck on a small crop, blended into the unmoved body through the soft mask
        hb = HEAD_BOX
        head = img.crop(hb).rotate(float(m["head_angle"][i]), resample=Image.BILINEAR,
                                   center=(HEAD_PIVOT[0] - hb[0], HEAD_PIVOT[1] - hb[1]),
                                   translate=(float(m["head_dx"][i]), float(m["head_dy"][i])))
        img.paste(head, hb[:2], self.head_mask.crop(hb))
        # body: slow sway, breathing and camera push-in about the waist, as one affine on the cropped figure
        img = img.crop(CROP)
        sc = float(m["breath"][i] * m["drift"][i])
        ang = math.radians(float(m["body_angle"][i]))
        px, py = BODY_PIVOT[0] - CROP[0], BODY_PIVOT[1] - CROP[1]
        c, sn = math.cos(ang) / sc, math.sin(ang) / sc
        img = img.transform(img.size, Image.AFFINE, (c, sn, px - c * px - sn * py, -sn, c, py + sn * px - c * py),
                            Image.BILINEAR)
        k = self.s * PRES_SCALE
        return img.resize((round(img.width * k), round(img.height * k)), Image.LANCZOS)


def _cover(img: Image.Image, w: int, h: int, zoom: float = 1.0) -> Image.Image:
    iw, ih = img.size
    scale = max(w / iw, h / ih) * zoom
    nw, nh = int(iw * scale) + 1, int(ih * scale) + 1
    r = img.resize((nw, nh), Image.BICUBIC)
    left, top = (nw - w) // 2, (nh - h) // 2
    return r.crop((left, top, left + w, top + h))


class Visual:
    """The news image, shown whole: scaled to fit inside the frame (nothing cropped away), with a blurred copy
    filling any spare space. The slow zoom is small, so the subject never leaves the frame."""

    def __init__(self, img: Image.Image):
        self.img = img.convert("RGB")
        small = self.img.copy()
        small.thumbnail((48, 48))
        self.back = small.filter(ImageFilter.GaussianBlur(3))

    def render(self, w: int, h: int, zoom: float) -> Image.Image:
        iw, ih = self.img.size
        if abs((iw / ih) / (w / h) - 1) < 0.12:             # nearly the same shape: fill the frame, trim a sliver
            return _cover(self.img, w, h, zoom)
        out = _cover(self.back, w, h)
        k = min(w / iw, h / ih) * zoom
        fg = self.img.resize((max(1, int(iw * k)), max(1, int(ih * k))), Image.BICUBIC)
        out.paste(fg, ((w - fg.width) // 2, (h - fg.height) // 2))
        return out.crop((0, 0, w, h))


def _wrap(draw, text, font, max_w, max_lines=2):
    words, lines, cur = text.split(), [], ""
    for wd in words:
        t = f"{cur} {wd}".strip()
        if draw.textlength(t, font=font) <= max_w or not cur:
            cur = t
        else:
            lines.append(cur)
            cur = wd
    lines.append(cur)
    return lines if len(lines) <= max_lines else None


def overlay_layer(size, headline, channel, font_path) -> Image.Image:
    """Everything that sits on top of the presenter and does not move: bezel, headline bar, badge."""
    s = size[0] / DESIGN[0]
    layer = Image.new("RGBA", size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    # bar
    bx0, by0, bx1, by1 = _scale(BAR, s)
    d.rounded_rectangle((bx0, by0, bx1, by1), radius=int(40 * s), fill=(10, 28, 70, 240), outline=(120, 150, 210, 255),
                        width=max(1, int(2 * s)))
    pad = int(36 * s)
    max_w = bx1 - bx0 - 2 * pad
    for px in range(54, 25, -2):
        font = _font(font_path, int(px * s))
        lines = _wrap(d, headline, font, max_w)
        if lines and len(lines) * px * 1.12 <= (BAR[3] - BAR[1]) - 14:
            break
    lh = int(font.size * 1.12)
    y = by0 + ((by1 - by0) - lh * len(lines)) // 2
    for line in lines:
        d.text((bx0 + pad, y), line, font=font, fill=(255, 255, 255, 255), stroke_width=max(1, int(1.3 * s)),
               stroke_fill=(255, 255, 255, 255))  # stroke fakes bold: the bundled DM Sans is a static regular
        y += lh
    # channel badge
    gx0, gy0, gx1, gy1 = _scale(BADGE, s)
    d.rounded_rectangle((gx0, gy0, gx1, gy1), radius=int(14 * s), fill=(244, 240, 230, 255), outline=(120, 150, 210, 255),
                        width=max(1, int(2 * s)))
    bf = _font(font_path, int(40 * s))
    tw = d.textlength(channel, font=bf)
    d.text((gx0 + (gx1 - gx0 - tw) / 2, gy0 + (gy1 - gy0 - bf.size) / 2 - 2 * s), channel, font=bf, fill=(12, 30, 74, 255),
           stroke_width=max(1, int(1.3 * s)), stroke_fill=(12, 30, 74, 255))
    return layer


def cutaway_plan(n: int, seed: str, chance: float) -> np.ndarray:
    """Per-frame cutaway progress 0..1: 0 = presenter + monitor, 1 = news visual fills the screen, presenter gone.
    Some stories (decided by the seed) get one cutaway from ~25% to ~80% of the clip; the voice never stops."""
    p = np.zeros(n)
    rnd = np.random.default_rng(int(hashlib.sha1(("cut" + str(seed)).encode()).hexdigest()[:8], 16))
    if n < FPS * 8 or rnd.random() >= chance:
        return p
    start, end = int(n * rnd.uniform(0.18, 0.30)), int(n * rnd.uniform(0.70, 0.85))
    t = np.arange(n)
    ramp_in = np.clip((t - start) / CUTAWAY_FRAMES, 0, 1)
    ramp_out = np.clip((end - t) / CUTAWAY_FRAMES, 0, 1)
    x = np.minimum(ramp_in, ramp_out)
    return x * x * (3 - 2 * x)               # smoothstep


def plan_from_ranges(n: int, ranges) -> np.ndarray:
    """Cutaway progress for explicit (start_s, end_s) windows, with the same smooth in/out as cutaway_plan."""
    t = np.arange(n)
    p = np.zeros(n)
    for a, b in ranges:
        x = np.minimum(np.clip((t - a * FPS) / CUTAWAY_FRAMES, 0, 1), np.clip((b * FPS - t) / CUTAWAY_FRAMES, 0, 1))
        p = np.maximum(p, x * x * (3 - 2 * x))
    return p


def _lerp_box(a, b, t):
    return tuple(a[i] + (b[i] - a[i]) * t for i in range(4))


def extract_poster(mp4, jpg=None) -> Path:
    """One still frame of the finished video (a second or so in, when the headline is on screen). The page shows this
    instead of loading the video, so nothing is downloaded until someone presses play. Skips if it already exists."""
    mp4 = Path(mp4)
    jpg = Path(jpg) if jpg else mp4.with_suffix(".jpg")
    if jpg.exists():
        return jpg
    tmp = jpg.with_suffix(".jpg.tmp")
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-ss", "1.6", "-i", str(mp4), "-frames:v", "1", "-q:v", "3",
           "-f", "image2", str(tmp)]
    subprocess.run(cmd, check=True, timeout=60)
    os.replace(tmp, jpg)
    return jpg


def render_video(audio_path, out_mp4, presenter: Presenter, headline, monitor_image, credit="", channel="BOUGHT.",
                 font_path=None, seed="", cutaway_chance=0.6, moods=None, cut_ranges=None) -> None:
    out_mp4 = Path(out_mp4)
    tmp = out_mp4.with_suffix(".mp4.tmp")
    size, s = presenter.size, presenter.s
    env = envelope(audio_path)
    n = len(env)
    mo = motion(env, seed)
    cut = plan_from_ranges(n, cut_ranges) if cut_ranges is not None else cutaway_plan(n, seed, cutaway_chance)
    over = overlay_layer(size, headline, channel, font_path)
    shot = Visual(monitor_image)
    cf = _font(font_path, max(9, int(15 * s)))
    credit = credit if len(credit) < 48 else credit[:45] + "..."
    rnd = int(hashlib.sha1(str(seed).encode()).hexdigest(), 16)
    next_blink = 40 + rnd % 40
    blink_seq = {}
    while next_blink < n:
        for j, lv in enumerate((1, 2, 2, 1)):
            blink_seq[next_blink + j] = lv
        next_blink += 75 + (rnd >> 8) % 60
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{size[0]}x{size[1]}",
           "-r", str(FPS), "-i", "-", "-i", str(audio_path), "-c:v", "libx264", "-preset", "veryfast",
           "-crf", "21", "-profile:v", "high", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "128k", "-shortest",
           "-movflags", "+faststart", "-f", "mp4", str(tmp)]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    try:
        bgw, bgh = presenter.background.size
        for i, e in enumerate(env):
            c = float(cut[i])
            # the studio drifts a few pixels, so the set feels like it has depth
            ox = int((bgw - size[0]) / 2 * (1 + math.sin(i / FPS * 2 * math.pi / 9.0)))
            oy = int((bgh - size[1]) / 2 * (1 + math.sin(i / FPS * 2 * math.pi / 11.0 + 1)))
            frame = presenter.background.crop((ox, oy, ox + size[0], oy + size[1]))
            if c < 1:  # presenter slides out to the left and fades while the visual takes over
                pres = presenter.frame(K_MIN + (K_MAX - K_MIN) * float(e), blink_seq.get(i, 0), mo, i,
                                       moods[i] if moods is not None else "neutral")
                mask = pres.getchannel("A")
                if c > 0:
                    mask = mask.point(lambda v: int(v * (1 - c)))
                ox0, oy0 = presenter.origin
                frame.paste(pres, (int((ox0 - 120 * c) * s), int(oy0 * s)), mask)
            box = _scale(_lerp_box(MONITOR, FULL, c), s)
            bez = int(round(9 * s * (1 - c)))
            zoom = 1.0 + 0.04 * i / max(1, n - 1)                     # gentle push-in; the image stays inside the frame
            w, h = box[2] - box[0] - 2 * bez, box[3] - box[1] - 2 * bez
            frame.paste(shot.render(w, h, zoom), (box[0] + bez, box[1] + bez))
            if bez:
                d = ImageDraw.Draw(frame)
                d.rounded_rectangle(box, radius=int(14 * s), outline=(18, 22, 30, 255), width=bez)
                d.rounded_rectangle(box, radius=int(14 * s), outline=(190, 195, 205, 255), width=max(1, int(3 * s * (1 - c))))
            if credit:
                d = ImageDraw.Draw(frame)
                tw = d.textlength(credit, font=cf)
                d.text((box[2] - bez - tw - 10 * s, box[3] - bez - 24 * s), credit, font=cf, fill=(255, 255, 255, 235),
                       stroke_width=1, stroke_fill=(0, 0, 0, 200))
            frame.alpha_composite(over)
            p.stdin.write(frame.convert("RGB").tobytes())
        p.stdin.close()
        if p.wait(timeout=300) != 0:
            raise RuntimeError("ffmpeg failed")
        os.replace(tmp, out_mp4)
    finally:
        if p.poll() is None:
            p.kill()
        tmp.unlink(missing_ok=True)
