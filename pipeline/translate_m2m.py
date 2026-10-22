"""Translation adapter for translate_command: M2M100 (Meta, MIT licence) run by CTranslate2 (MIT), English -> one language.

Usage: translate_m2m.py <language code> <model dir>   stdin: a JSON list of English strings, stdout: a JSON list.
Runs on a plain CPU with ~0.7 GB of RAM and no PyTorch: `pip install ctranslate2 sentencepiece`. The model dir is the
8-bit CTranslate2 conversion of facebook/m2m100_418M (~470 MB), made once on any machine with
`pip install transformers torch sentencepiece` and the original model (see pipeline/README.md, "Translations").
"""
import json
import os
import sys


def _translate(translator, sp, texts, lang, beam=3):
    source = [["__en__"] + sp.encode(t, out_type=str)[:160] + ["</s>"] for t in texts]
    results = translator.translate_batch(source, target_prefix=[[f"__{lang}__"]] * len(texts), beam_size=beam,
                                         max_batch_size=16, batch_type="examples", max_decoding_length=200)
    return [sp.decode(r.hypotheses[0][1:]) for r in results]


def main(lang: str, model_dir: str) -> None:
    import ctranslate2
    import sentencepiece as spm
    texts = json.load(sys.stdin)
    sp = spm.SentencePieceProcessor(model_file=os.path.join(model_dir, "sentencepiece.bpe.model"))
    translator = ctranslate2.Translator(model_dir, device="cpu", compute_type="int8", intra_threads=min(4, os.cpu_count() or 2))
    out = _translate(translator, sp, texts, lang)
    # Some small languages make the model copy the English back; a second try with "The ..." in front often breaks it.
    again = [i for i, t in enumerate(texts) if len(t.split()) > 2 and out[i].strip(" .") == t.strip(" .")]
    if again:
        retry = _translate(translator, sp, ["The " + texts[i][0].lower() + texts[i][1:] for i in again], lang)
        for i, text in zip(again, retry):
            if text.strip(" .") != texts[i].strip(" ."):
                out[i] = text
        again = [i for i in again if out[i].strip(" .") == texts[i].strip(" .")]
        if again:                                          # last try: plain greedy decoding
            for i, text in zip(again, _translate(translator, sp, [texts[i] for i in again], lang, beam=1)):
                out[i] = text
    json.dump(out, sys.stdout, ensure_ascii=False)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
