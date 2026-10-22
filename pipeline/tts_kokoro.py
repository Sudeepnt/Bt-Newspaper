"""TTS adapter for Kokoro-82M (Apache-2.0). Reads the script on stdin, writes a wav.

Usage (set as tts_command in config.yaml, run with the Python that has kokoro-onnx installed):
  python tts_kokoro.py MODEL.onnx VOICES.bin VOICE OUT.wav [SPEED]
VOICE is a Kokoro voice name, or two joined by "+" for an even blend (e.g. af_nova+af_kore).
"""
import sys

import soundfile as sf
from kokoro_onnx import Kokoro

model, voices, voice, out = sys.argv[1:5]
speed = float(sys.argv[5]) if len(sys.argv) > 5 else 1.0
tts = Kokoro(model, voices)
names = voice.split("+")
style = sum(tts.get_voice_style(n) for n in names) / len(names) if len(names) > 1 else voice
samples, rate = tts.create(sys.stdin.read(), voice=style, speed=speed, lang="en-gb" if names[0].startswith("b") else "en-us")
sf.write(out, samples, rate, format="WAV")  # out may end in .tmp, so name the format
