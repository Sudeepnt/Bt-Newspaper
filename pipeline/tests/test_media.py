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
                  avatar_size=(320, 180))
    res, feed, out = go(tmp_path, cfg)
    assert res["media"]["failed"] == 0
    assert all(i["video_url"].split("?")[0].endswith(".mp4") for i in feed["prime"])
    assert len(list((out.parent / "media").glob("*.mp4"))) == 25


@needs_ffmpeg
def test_anime_clip_with_laugh_and_cutaway(tmp_path):
    pytest.importorskip("PIL")
    from pipeline.clip import make_clip
    cfg = replace(cfg_with([sys.executable, "-c", STUB, "{wav}"]), avatar_size=(320, 180))
    spec = tmp_path / "s.yaml"
    spec.write_text(yaml.safe_dump({
        "name": "t", "character": "anime", "headline": "Hello there", "image": "public/assets/podcast-earth.jpg",
        "segments": [{"text": "Hi.", "mood": "happy"}, {"laugh": 0.5},
                     {"text": "Bye.", "cutaway": True}]}))
    feed = tmp_path / "feed.json"
    feed.write_text(json.dumps({"prime": [{"id": "abc"}]}))
    spec.write_text(spec.read_text() + "attach_to: abc\n")
    res = make_clip(spec, cfg, feed_path=feed)
    assert Path(res["mp4"]).exists() and 3 < res["duration_s"] < 8   # stub speech is 1 s per segment
    item = json.loads(feed.read_text())["prime"][0]
    assert item["video_url"].endswith("t.mp4") and item["duration_s"] == res["duration_s"]


def test_mascot_presenter_renders_all_moods():
    import numpy as np
    from pipeline.avatar import motion
    from pipeline.mascot import MascotPresenter
    p = MascotPresenter(size=(640, 360))
    m = motion(np.zeros(30), "t")
    sizes = set()
    for mood, blink in (("neutral", 0), ("happy", 1), ("laugh", 0), ("serious", 2)):
        im = p.frame(0.3, blink, m, 3, mood)
        assert im.mode == "RGBA" and im.getchannel("A").getbbox()
        sizes.add(im.size)
    assert len(sizes) == 1


@needs_ffmpeg
def test_podcast_builds_one_episode_with_chapters_and_is_idempotent(tmp_path):
    from pipeline.podcast import attach_podcast, build_podcast, story_script
    marker = tmp_path / "calls.txt"
    stub = ("import sys,wave;sys.stdin.read();open(%r,'a').write('x');w=wave.open(sys.argv[1],'wb');w.setnchannels(1);"
            "w.setsampwidth(2);w.setframerate(16000);w.writeframes(b'\\0\\0'*16000);w.close()" % str(marker))
    cfg = replace(load_config(), media_enabled=True, podcast_enabled=True, podcast_stories=3, podcast_gap_seconds=0.5,
                  tts_command=(sys.executable, "-c", stub, "{wav}"), audio_base_url="/media")
    feed = {"generated_at": "2026-10-13T04:00:00Z",
            "prime": [{"id": f"s{i}", "headline": f"Headline {i}", "summary": "A summary.", "source": "Wire",
                       "category": "AI" if i < 2 else "Business"} for i in range(5)], "cards": [], "glance": []}
    out, cache = tmp_path / "media", tmp_path / "cache"
    res = build_podcast(cfg, feed, out, cache)
    assert res["complete"] and res["built"] and res["new"] == 5          # intro + 3 stories + outro
    assert attach_podcast(cfg, feed, out)
    ch = feed["podcast"]["chapters"]
    assert [c["id"] for c in ch] == ["s0", "s1", "s2"]
    assert ch[0]["start"] == 1.5 and ch[1]["start"] == pytest.approx(ch[0]["end"] + 0.5)   # 1 s intro + 0.5 s gap, then each story + gap
    assert feed["podcast"]["duration_s"] == pytest.approx(5 * 1.0 + 4 * 0.5)
    res2 = build_podcast(cfg, feed, out, cache)                          # nothing changed: no TTS calls, no rebuild
    assert res2["new"] == 0 and not res2["built"] and marker.read_text() == "x" * 5
    feed["prime"][1]["headline"] = "Changed"                             # one story changes: only it is re-read
    assert not attach_podcast(cfg, {**feed, "podcast": None}, out)       # stale episode is not attached
    res3 = build_podcast(cfg, feed, out, cache)
    assert res3["new"] == 1 and res3["built"]
    assert story_script({"id": "x", "headline": "Hi", "summary": "S", "category": "AI"}, 2, "AI").startswith("Story 2. Next.")


def test_looks_are_picked_per_category_and_rotate_for_unknown_ones():
    from pipeline.styles import pick_look
    looks = {"AI": {"character": "mascot", "style": "funky"}, "Technology": {"character": "photo", "style": "studio"}}
    cfg = replace(load_config(), avatar_looks=looks)
    assert pick_look({"id": "a", "category": "AI"}, cfg) == ("mascot", "funky")
    assert pick_look({"id": "b", "category": "technology"}, cfg) == ("photo", "studio")           # case-insensitive
    other = {pick_look({"id": str(i), "category": "World"}, cfg) for i in range(40)}
    assert other == {("mascot", "funky"), ("photo", "studio")}                                    # unknown: rotates over the looks
    assert pick_look({"id": "a", "category": "World"}, cfg) == pick_look({"id": "a", "category": "World"}, cfg)
    assert pick_look({"id": "a", "category": "AI"}, replace(load_config(), avatar_looks={})) == ("photo", "studio")   # no looks: original
    with pytest.raises(ConfigError):
        import yaml as _y, tempfile
        p = Path(tempfile.mkdtemp()) / "c.yaml"
        p.write_text(_y.safe_dump({"avatar_looks": {"AI": {"character": "robot", "style": "funky"}}}))
        load_config(p)


@needs_ffmpeg
def test_mixed_looks_render_with_different_hosts_and_sets(tmp_path):
    pytest.importorskip("PIL"); pytest.importorskip("numpy")
    looks = {"AI": {"character": "mascot", "style": "funky"}, "Technology": {"character": "photo", "style": "studio"},
             "Tech business": {"character": "anime", "style": "channel"}}
    cfg = cfg_with([sys.executable, "-c", STUB, "{wav}"], avatar_enabled=True, avatar_size=(320, 180), avatar_looks=looks,
                   avatar_cutaway_chance=0, media_time_budget_seconds=600)
    res, feed, out = go(tmp_path, cfg)
    media = out.parent / "media"
    cats = {i["category"] for i in feed["prime"]}
    assert {"AI", "Technology", "Tech business"} <= cats
    assert all(i.get("video_url") and (media / Path(i["video_url"].split("?")[0]).name).exists() for i in feed["prime"])
    sizes = {(media / Path(i["video_url"].split("?")[0]).name).stat().st_size for i in feed["prime"]}
    assert len(sizes) > 5                                                                          # not 25 copies of one look


def test_badges_rules_priority_and_engagement():
    from pipeline.badges import assign_badges
    cfg = replace(load_config(), badges_enabled=True, badges_exclusive_sources=("The Wire",), badges_min_events=30)

    def item(i, **kw):
        return {"id": i, "headline": "A thing happens", "category": "Technology", "source": "Other",
                "published_at": "2026-10-13T00:00:00Z", **kw}
    feed = {"generated_at": "2026-10-13T04:00:00Z",
            "prime": [item("a", category="AI", source="The Wire", published_at="2026-10-13T03:00:00Z"),   # exclusive + new
                      item("b", headline="OpenAI ships a new model", category="AI"), item("c"), item("d")],
            "cards": [item("e")], "glance": [item("f"), item("g")]}
    engagement = {"c": {"views": 500, "reads": 40}, "d": {"views": 300}, "f": {"glances": 90}, "g": {"glances": 90, "reads": 10},
                  "e": {"reads": 41}}
    counts = assign_badges(cfg, feed, engagement)
    ids = lambda x: [b["id"] for b in x["badges"]]
    assert ids(feed["prime"][0]) == ["exclusive"]                     # exclusive + new earned: only the strongest is shown
    assert ids(feed["prime"][1]) == []                                # there is no AI badge, whatever the story is about
    assert ids(feed["prime"][2]) == ["most-viewed"]                   # 500 beats 300 (and it also won most-read? no: one badge)
    assert ids(feed["cards"][0]) == ["most-read"]                     # 41 reads beats 40
    assert ids(feed["glance"][0]) == [] and ids(feed["glance"][1]) == []   # a tie in glances wins nothing
    assert feed["prime"][3]["badges"] == []
    assert "ai" not in counts and all(len(i["badges"]) <= 1 for s in ("prime", "cards", "glance") for i in feed[s])
    many = {"generated_at": "2026-10-13T04:00:00Z", "cards": [], "glance": [],
            "prime": [item(str(n), published_at="2026-10-13T03:00:00Z") for n in range(8)]}
    assert assign_badges(replace(cfg, badges_max_per_type=3), many, {})["new"] == 3        # "New" only on the first few
    assert [i["id"] for i in many["prime"] if i["badges"]] == ["0", "1", "2"]
    many["cards"] = [dict(many["prime"][0]), dict(many["prime"][1])]                       # same articles again in another slot
    assign_badges(replace(cfg, badges_max_per_type=3), many, {})
    assert [i["id"] for i in many["prime"] if i["badges"]] == ["0", "1", "2"]             # duplicates do not cost a story its badge
    quiet = {"generated_at": "2026-10-13T04:00:00Z", "prime": [item("c")], "cards": [], "glance": []}
    assign_badges(cfg, quiet, {"c": {"views": 5}})
    assert quiet["prime"][0]["badges"] == []                          # under badges_min_events: a quiet day shows none


def test_translations_cached_attached_and_only_new_text_is_sent(tmp_path):
    from pipeline.translate import attach_translations, build_translations
    log = tmp_path / "calls.txt"
    fake = ("import sys,json;t=json.load(sys.stdin);open(%r,'a').write(sys.argv[1]+':'+str(len(t))+'\\n');"
            "print(json.dumps([sys.argv[1].upper()+' '+x for x in t]))" % str(log))
    cfg = replace(load_config(), translate_languages=("hi-IN", "es-ES"), translate_command=(sys.executable, "-c", fake, "{lang}"))
    feed = {"prime": [{"id": "a", "headline": "One", "summary": "Sum one."}, {"id": "b", "headline": "Two", "summary": "Sum one."}],
            "cards": [], "glance": []}
    cache = tmp_path / "t.json"
    st = build_translations(cfg, feed, tmp_path, cache)
    assert st["translated"] == 6 and st["failed"] == 0                  # 3 unique texts (the repeated summary counts once) x 2 languages
    assert log.read_text().splitlines() == ["hi:3", "es:3"]              # M2M code for hi-IN is hi; one call per language
    assert attach_translations(cfg, feed, tmp_path, cache) == ["hi-IN", "es-ES"]
    assert feed["translations_available"] == ["hi-IN", "es-ES"]
    data = json.loads((tmp_path / "translations" / "hi-IN.json").read_text())
    assert data["a"] == {"headline": "HI One", "summary": "HI Sum one."}
    feed["prime"].append({"id": "c", "headline": "Three", "summary": "Sum one."})     # one new text: only it is translated
    log.write_text("")
    assert build_translations(cfg, feed, tmp_path, cache)["translated"] == 2
    assert log.read_text().splitlines() == ["hi:1", "es:1"]
    bad = replace(cfg, translate_command=(sys.executable, "-c", "import sys;sys.exit(3)"), translate_languages=("de",))
    st = build_translations(bad, feed, tmp_path, cache)
    assert st["failed"] == 1 and attach_translations(bad, feed, tmp_path, cache) == []   # a failed language is simply not offered
