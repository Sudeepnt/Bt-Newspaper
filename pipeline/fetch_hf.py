"""Download a Hugging Face model repo with many parallel, resumable connections (stdlib only).

Single downloads from huggingface.co are often throttled per connection; 16 ranges at once is several times faster.
Usage: python fetch_hf.py facebook/m2m100_418M /path/to/dir [file ...]
Without file names it fetches the files an M2M100/Marian-style model needs. Re-running resumes: finished parts are kept.
"""
import concurrent.futures as cf
import os
import sys
import time
import urllib.request

DEFAULT_FILES = ["config.json", "generation_config.json", "sentencepiece.bpe.model", "special_tokens_map.json",
                 "tokenizer_config.json", "vocab.json", "pytorch_model.bin"]
PART = 64 * 1024 * 1024
WORKERS = 16


def _open(url, start, end):
    req = urllib.request.Request(url, headers={"Range": f"bytes={start}-{end}", "User-Agent": "bought-fetch/0.1"})
    return urllib.request.urlopen(req, timeout=60)


def _size(url):
    with _open(url, 0, 0) as r:
        return int(r.headers["Content-Range"].split("/")[1])


def _fetch_part(url, part_path, start, end):
    want = end - start + 1
    if os.path.exists(part_path) and os.path.getsize(part_path) == want:
        return want
    for attempt in range(8):
        try:
            with _open(url, start, end) as r, open(part_path + ".tmp", "wb") as f:
                while chunk := r.read(1 << 20):
                    f.write(chunk)
            if os.path.getsize(part_path + ".tmp") != want:
                raise IOError("short part")
            os.replace(part_path + ".tmp", part_path)
            return want
        except Exception as e:                                   # a dropped connection just retries this part
            time.sleep(min(2 * attempt + 1, 15))
    raise RuntimeError(f"part {start}-{end} of {url} failed")


def fetch(repo, dest, files):
    os.makedirs(dest, exist_ok=True)
    for name in files:
        target = os.path.join(dest, name)
        url = f"https://huggingface.co/{repo}/resolve/main/{name}"
        size = _size(url)
        if os.path.exists(target) and os.path.getsize(target) == size:
            print(f"{name}: already there", flush=True)
            continue
        parts_dir = target + ".parts"
        os.makedirs(parts_dir, exist_ok=True)
        spans = [(i, s, min(s + PART, size) - 1) for i, s in enumerate(range(0, size, PART))]
        done, started = 0, time.time()
        with cf.ThreadPoolExecutor(WORKERS) as pool:
            futures = [pool.submit(_fetch_part, url, os.path.join(parts_dir, f"{i:05d}"), s, e) for i, s, e in spans]
            for fut in cf.as_completed(futures):
                done += fut.result()
                print(f"{name}: {done / 1e6:.0f}/{size / 1e6:.0f} MB  ({done / max(1, time.time() - started) / 1e6:.2f} MB/s)", flush=True)
        with open(target + ".tmp", "wb") as out:
            for i, _, _ in spans:
                with open(os.path.join(parts_dir, f"{i:05d}"), "rb") as p:
                    while chunk := p.read(1 << 22):
                        out.write(chunk)
        os.replace(target + ".tmp", target)
        for i, _, _ in spans:
            os.remove(os.path.join(parts_dir, f"{i:05d}"))
        os.rmdir(parts_dir)
        print(f"{name}: done ({size / 1e6:.0f} MB)", flush=True)


if __name__ == "__main__":
    fetch(sys.argv[1], sys.argv[2], sys.argv[3:] or DEFAULT_FILES)
