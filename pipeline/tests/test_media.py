import json
import shutil
import sys
from dataclasses import replace
from pathlib import Path

import pytest
import yaml

from pipeline.config import ConfigError, load_config, load_sources
from pipeline.media import make_script
from pipeline.runner import run_cycle

STUB = ("import sys,wave;sys.stdin.read();w=wave.open(sys.argv[1],'wb');w.setnchannels(1);"
        "w.setsampwidth(2);w.setframerate(16000);w.writeframes(b'\\0\\0'*16000);w.close()")

needs_ffmpeg = pytest.mark.skipif(not (shutil.which("ffmpeg") and shutil.which("ffprobe")), reason="ffmpeg missing")


def cfg_with(command, **kw):
    return replace(load_config(), media_enabled=True, tts_command=tuple(command), **kw)


def go(tmp_path, cfg):
    out = tmp_path / "out" / "feed.json"
    res = run_cycle(cfg, load_sources(), dry_run=True, db_path=tmp_path / "t.db", out_path=out)
    return res, json.loads(out.read_text()), out


def test_script_is_deterministic_and_short():
    item = {"category": "AI", "headline": "A thing happens", "summary": "It was big. Very big.", "source": "Wire"}
    s = make_script(item)
    assert s == "AI. A thing happens. It was big. Very big. Source: Wire."
    assert s == make_script(item)
    assert len(make_script({**item, "summary": "word " * 400}, 600)) <= 600


@needs_ffmpeg
def test_audio_made_once_then_skipped(tmp_path):
    cfg = cfg_with([sys.executable, "-c", STUB, "{wav}"])
    res, feed, out = go(tmp_path, cfg)
    assert res["media"]["made"] == 25
    assert all(i["audio_url"].endswith(".mp3") and i["duration_s"] > 0 for i in feed["prime"])
    assert not any("audio_url" in i for i in feed["cards"])
    assert len(list((out.parent / "media").glob("*.mp3"))) == 25
    res2, _, _ = go(tmp_path, cfg)
    assert res2["media"] == {"made": 0, "skipped": 25, "failed": 0, "deferred": 0}


@needs_ffmpeg
def test_failures_recorded_and_capped(tmp_path):
    cfg = cfg_with([sys.executable, "-c", "import sys; sys.exit(3)"], media_max_attempts=2)
    res, feed, _ = go(tmp_path, cfg)
    assert res["media"]["failed"] == 25 and res["media"]["made"] == 0
    assert all(i["audio_url"] is None for i in feed["prime"])  # feed stays valid without audio
    go(tmp_path, cfg)  # attempt 2
    res3, _, _ = go(tmp_path, cfg)  # capped: no more tries
    assert res3["media"]["failed"] == 25


def test_media_requires_command(tmp_path):
    p = tmp_path / "bad.yaml"
    p.write_text(yaml.safe_dump({"media_enabled": True}))
    with pytest.raises(ConfigError):
        load_config(p)


@needs_ffmpeg
def test_avatar_video_made_and_in_feed(tmp_path):
    pytest.importorskip("PIL")
    cfg = replace(cfg_with([sys.executable, "-c", STUB, "{wav}"]), avatar_enabled=True,
                  avatar_size=(220, 100))
    res, feed, out = go(tmp_path, cfg)
    assert res["media"]["failed"] == 0
    assert all(i["video_url"].endswith(".mp4") for i in feed["prime"])
    assert len(list((out.parent / "media").glob("*.mp4"))) == 25
