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
PRESENTER_DX = -330                   # shifts her to the left third of the frame
MONITOR = (680, 45, 1255, 420)        # x0, y0, x1, y1 (outer bezel)
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


def _blink(img: Image.Image, level: int) -> Image.Image:
    """level 0 open, 1 half, 2 closed: skin-coloured lid over each eye plus a lash line."""
    if level == 0:
        return img
    ov = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    px = img.convert("RGB")
    for cx, cy in EYES:
        # lid colour: a blend of the skin just above the eye and the cheek below it
        up = np.asarray(px.crop((cx - 12, cy - 22, cx + 12, cy - 17))).reshape(-1, 3)
        low = np.asarray(px.crop((cx - 10, cy + 20, cx + 10, cy + 28))).reshape(-1, 3)
        skin = tuple(int(v) for v in (np.median(up, axis=0) * 0.6 + np.median(low, axis=0) * 0.4))
        bottom = cy + 7 if level == 2 else cy - 1
        d.ellipse((cx - 25, cy - 11, cx + 25, bottom + 3), fill=skin + (255,))
    ov = ov.filter(ImageFilter.GaussianBlur(3.0))
    d = ImageDraw.Draw(ov)
    for cx, cy in EYES:
        y = cy + (4 if level == 2 else -3)
        d.arc((cx - 22, y - 6, cx + 22, y + 6), 20, 160, fill=(45, 30, 28, 200), width=2)
    out = img.copy()
    out.alpha_composite(ov)
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


class Presenter:
    """Pre-rendered presenter variants (mouth level x blink level) at output size."""

    def __init__(self, cutout_path, size):
        self.size = size
        self.s = size[0] / DESIGN[0]
        base = Image.open(cutout_path).convert("RGBA")
        self.v = {}
        for blink in (0, 1, 2):
            for i in range(LEVELS):
                k = K_MIN + (K_MAX - K_MIN) * i / (LEVELS - 1)
                im = _blink(_mouth(base, k), blink)
                self.v[(i, blink)] = im.resize(size, Image.LANCZOS)
        self.background = studio_background(size)


def _cover(img: Image.Image, w: int, h: int, zoom: float) -> Image.Image:
    iw, ih = img.size
    scale = max(w / iw, h / ih) * zoom
    nw, nh = int(iw * scale) + 1, int(ih * scale) + 1
    r = img.resize((nw, nh), Image.BILINEAR)
    left, top = (nw - w) // 2, (nh - h) // 2
    return r.crop((left, top, left + w, top + h))


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


def overlay_layer(size, headline, credit, channel, font_path) -> Image.Image:
    """Everything that sits on top of the presenter and does not move: bezel, headline bar, badge."""
    s = size[0] / DESIGN[0]
    layer = Image.new("RGBA", size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    mx0, my0, mx1, my1 = _scale(MONITOR, s)
    inset = int(round(9 * s))
    d.rounded_rectangle((mx0, my0, mx1, my1), radius=int(14 * s), outline=(18, 22, 30, 255), width=inset)
    d.rounded_rectangle((mx0, my0, mx1, my1), radius=int(14 * s), outline=(190, 195, 205, 255), width=max(2, int(3 * s)))
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
    if credit:
        cf = _font(font_path, max(9, int(15 * s)))
        label = credit if len(credit) < 48 else credit[:45] + "..."
        d.text((mx0 + int(14 * s), my1 + int(8 * s)), label, font=cf, fill=(235, 240, 250, 235))
    return layer


def render_video(audio_path, out_mp4, presenter: Presenter, headline, monitor_image, credit="", channel="BOUGHT.",
                 font_path=None, seed="") -> None:
    out_mp4 = Path(out_mp4)
    tmp = out_mp4.with_suffix(".mp4.tmp")
    size, s = presenter.size, presenter.s
    env = envelope(audio_path)
    n = len(env)
    over = overlay_layer(size, headline, credit, channel, font_path)
    mx0, my0, mx1, my1 = _scale(MONITOR, s)
    inset = int(round(9 * s))
    mw, mh = (mx1 - mx0) - 2 * inset, (my1 - my0) - 2 * inset
    shot = monitor_image.convert("RGB")
    rnd = int(hashlib.sha1(str(seed).encode()).hexdigest(), 16)
    next_blink = 40 + rnd % 40
    blink_seq = {}
    while next_blink < n:
        for j, lv in enumerate((1, 2, 2, 1)):
            blink_seq[next_blink + j] = lv
        next_blink += 75 + (rnd >> 8) % 60
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{size[0]}x{size[1]}",
           "-r", str(FPS), "-i", "-", "-i", str(audio_path), "-c:v", "libx264", "-preset", "veryfast",
           "-crf", "26", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "96k", "-shortest",
           "-movflags", "+faststart", "-f", "mp4", str(tmp)]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    try:
        for i, e in enumerate(env):
            frame = presenter.background.copy()
            bob = int(round((1.6 * math.sin(i / FPS * 2 * math.pi / 3.2) + 1.8 * e) * s))
            pres = presenter.v[(int(round(e * (LEVELS - 1))), blink_seq.get(i, 0))]
            frame.paste(pres, (int(PRESENTER_DX * s), bob), pres)  # paste (not alpha_composite) allows negative x
            zoom = 1.0 + 0.14 * i / max(1, n - 1)                    # slow push-in on the monitor
            frame.paste(_cover(shot, mw, mh, zoom), (mx0 + inset, my0 + inset))
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
