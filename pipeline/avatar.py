"""Phase 2b: talking-presenter video from audio, CPU only (Pillow + numpy + ffmpeg).

A 2D "mouth flap": the presenter photo's lower face is stretched vertically in proportion to the speech
loudness. No neural model, so it is cheap but visibly stylised, not true lip-sync.
"""
from __future__ import annotations

import os
import subprocess
from pathlib import Path

import numpy as np
from PIL import Image

FPS = 25
LEVELS = 12
K_MIN, K_MAX = -0.25, 0.6      # vertical stretch of the lower face: closed .. wide open
# region around the mouth in the source photo (x0, y0, x1, y1) and the mouth line
REGION = (585, 255, 755, 430)
MOUTH = (668, 310)


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
    x0, y0, x1, y1 = REGION
    reg = base.crop(REGION)
    w, h = reg.size
    ml = MOUTH[1] - y0
    nh = max(1, int(round((h - ml) * (1 + k))))
    new = Image.new("RGB", (w, h))
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


def frames_for(image_path, size) -> list:
    """LEVELS pre-rendered frames at output size (and 2.2:1 crop to fit the newspaper's video slot)."""
    base = Image.open(image_path).convert("RGB")
    w, h = base.size
    crop_h = int(w / (size[0] / size[1]))
    box = (0, 0, w, min(h, crop_h))
    out = []
    for i in range(LEVELS):
        k = K_MIN + (K_MAX - K_MIN) * i / (LEVELS - 1)
        out.append(_mouth(base, k).crop(box).resize(size, Image.LANCZOS).tobytes())
    return out


def render_video(audio_path, out_mp4, image_path, size=(1100, 500), cache=None) -> None:
    out_mp4 = Path(out_mp4)
    tmp = out_mp4.with_suffix(".mp4.tmp")
    env = envelope(audio_path)
    frames = cache if cache is not None else frames_for(image_path, size)
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{size[0]}x{size[1]}",
           "-r", str(FPS), "-i", "-", "-i", str(audio_path), "-c:v", "libx264", "-preset", "veryfast",
           "-crf", "28", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "64k", "-shortest",
           "-movflags", "+faststart", "-f", "mp4", str(tmp)]
    try:
        p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        for e in env:
            p.stdin.write(frames[int(round(e * (LEVELS - 1)))])
        p.stdin.close()
        if p.wait(timeout=300) != 0:
            raise RuntimeError("ffmpeg failed")
        os.replace(tmp, out_mp4)
    finally:
        tmp.unlink(missing_ok=True)
