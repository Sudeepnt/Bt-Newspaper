"""Translation adapter for translate_command: M2M100 (Meta, MIT licence), English -> one language, fully offline.

Usage: translate_m2m.py <m2m language code> [model dir]   stdin: a JSON list of English strings, stdout: a JSON list.
Needs `pip install transformers torch sentencepiece` (Python >= 3.9). The ~1.9 GB model comes from Hugging Face; if that is
slow, `python pipeline/fetch_hf.py facebook/m2m100_418M /some/dir` downloads it with parallel connections, and the optional
second argument points the translator at that folder.
"""
import json
import sys

MODEL = "facebook/m2m100_418M"


def main(lang: str, model: str = MODEL) -> None:
    import torch
    from transformers import M2M100ForConditionalGeneration, M2M100Tokenizer
    texts = json.load(sys.stdin)
    device = "mps" if torch.backends.mps.is_available() else "cuda" if torch.cuda.is_available() else "cpu"
    tok = M2M100Tokenizer.from_pretrained(model)
    model = M2M100ForConditionalGeneration.from_pretrained(model).to(device).eval()
    tok.src_lang = "en"
    out = []
    for i in range(0, len(texts), 8):
        batch = tok(texts[i:i + 8], return_tensors="pt", padding=True, truncation=True, max_length=160).to(device)
        with torch.no_grad():
            ids = model.generate(**batch, forced_bos_token_id=tok.get_lang_id(lang), num_beams=3, max_new_tokens=200)
        out.extend(tok.batch_decode(ids, skip_special_tokens=True))
    json.dump(out, sys.stdout, ensure_ascii=False)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else MODEL)
