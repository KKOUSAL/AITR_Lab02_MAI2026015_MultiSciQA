"""Translate PQA-L items EN->X (NATIVE inputs), then X->EN (TT inputs).

Usage:
    python scripts/01_translate.py --lang hi --split dev --limit 5
    python scripts/01_translate.py --lang hi --split test
Outputs:
    data/translations/<model>__<src>__<tgt>.jsonl     segment cache
    data/translations/items_<split>_<lang>.jsonl     assembled items (NATIVE + TT text)
    results/translation/report_<split>_<lang>.json   counts, truncations, timing
"""
import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.data import load_items, load_protocol, split_sentences  # noqa: E402
from src.translate import Translator, seg_key  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lang", required=True, choices=["hi", "or"])
    ap.add_argument("--split", required=True, choices=["dev", "test"])
    ap.add_argument("--limit", type=int, default=None)
    args = ap.parse_args()

    cfg = load_protocol()
    lang = next(l for l in cfg["languages"]["targets"] if l["code"] == args.lang)
    en = cfg["languages"]["reference"]["mt"]
    items = load_items(cfg, args.split, args.limit)

    # Segment: question = 1 segment; each context paragraph -> sentences
    seg_items = []
    for it in items:
        seg_items.append({"pmid": it["pmid"], "q": it["question"],
                          "ctx": [split_sentences(c) for c in it["contexts"]]})
    all_segs = [s["q"] for s in seg_items] + [x for s in seg_items for para in s["ctx"] for x in para]

    t0 = time.time()
    fwd = Translator(cfg["translation"]["en_to_x"], en, lang["mt"], cfg)
    x_segs = fwd.translate(all_segs)
    t_fwd = time.time() - t0
    fwd_map = dict(zip(all_segs, x_segs))

    t1 = time.time()
    back = Translator(cfg["translation"]["x_to_en"], lang["mt"], en, cfg)
    uniq_x = list(dict.fromkeys(x_segs))
    tt_segs = back.translate(uniq_x)
    t_back = time.time() - t1
    back_map = dict(zip(uniq_x, tt_segs))

    # Input-side truncation check: source segments longer than the tokenizer's limit
    def over_limit(tr, segs, src, tgt):
        lim = tr.tok.model_max_length if tr.tok.model_max_length < 10**6 else 256
        pre = tr.ip.preprocess_batch(segs, src_lang=src, tgt_lang=tgt)
        lens = [len(x) for x in tr.tok(pre, truncation=False)["input_ids"]]
        return sum(n > lim for n in lens), lim, max(lens)

    in_over_fwd, lim_f, max_f = over_limit(fwd, list(dict.fromkeys(all_segs)), en, lang["mt"])
    in_over_back, lim_b, max_b = over_limit(back, uniq_x, lang["mt"], en)

    out_path = ROOT / cfg["translation"]["cache_dir"] / f"items_{args.split}_{args.lang}.jsonl"
    with out_path.open("w", encoding="utf-8") as f:
        for s in seg_items:
            rec = {
                "pmid": s["pmid"], "lang": args.lang,
                "question_x": fwd_map[s["q"]],
                "contexts_x": [" ".join(fwd_map[x] for x in para) for para in s["ctx"]],
                "question_tt": back_map[fwd_map[s["q"]]],
                "contexts_tt": [" ".join(back_map[fwd_map[x]] for x in para) for para in s["ctx"]],
            }
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    def n_trunc(tr, segs):
        return sum(bool(tr.cache.data[seg_key(x)]["truncated"]) for x in segs)

    report = {
        "split": args.split, "lang": args.lang, "n_items": len(items),
        "n_segments": len(all_segs), "n_unique_segments": len(set(all_segs)),
        "output_truncated_fwd": n_trunc(fwd, set(all_segs)),
        "output_truncated_back": n_trunc(back, set(uniq_x)),
        "input_over_limit_fwd": in_over_fwd, "input_limit_fwd": lim_f, "max_input_tokens_fwd": max_f,
        "input_over_limit_back": in_over_back, "input_limit_back": lim_b, "max_input_tokens_back": max_b,
        "seconds_fwd": round(t_fwd, 1), "seconds_back": round(t_back, 1), "device": fwd.device,
        "models": [cfg["translation"]["en_to_x"], cfg["translation"]["x_to_en"]],
    }
    rp = ROOT / "results" / "translation" / f"report_{args.split}_{args.lang}.json"
    rp.parent.mkdir(parents=True, exist_ok=True)
    rp.write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))
    for s in seg_items[:2]:
        print("\nEN :", s["q"], "\nX  :", fwd_map[s["q"]], "\nTT :", back_map[fwd_map[s["q"]]])


if __name__ == "__main__":
    main()
