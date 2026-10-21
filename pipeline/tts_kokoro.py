"""TTS adapter for Kokoro-82M (Apache-2.0). Reads the script on stdin, writes a wav.

Usage (set as tts_command in config.yaml, run with the Python that has kokoro-onnx installed):
  python tts_kokoro.py MODEL.onnx VOICES.bin VOICE OUT.wav
"""
import sys

import soundfile as sf
from kokoro_onnx import Kokoro

model, voices, voice, out = sys.argv[1:5]
samples, rate = Kokoro(model, voices).create(sys.stdin.read(), voice=voice, speed=1.0,
                                             lang="en-gb" if voice.startswith("b") else "en-us")
sf.write(out, samples, rate, format="WAV")  # out may end in .tmp, so name the format
