"""Score one (model, condition, language, template, split) cell by label log-likelihood.

Usage:
    python scripts/02_score.py --model Qwen/Qwen2.5-3B-Instruct --condition EN --split dev
    python scripts/02_score.py --model Qwen/Qwen2.5-3B-Instruct --condition NATIVE --lang hi --split dev
The test split requires --confirm-test (all P07 §9 checklist items ticked first).
Outputs:
    results/preds/<model>/<split>_<COND>_<lang>_<tpl>.csv
    results/preds/<model>/<split>_<COND>_<lang>_<tpl>.meta.json
"""
import argparse
import csv
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import torch  # noqa: E402

from src.data import assert_no_leak, build_prompt, join_context, load_items, load_protocol  # noqa: E402
from src.metrics import accuracy, macro_f1  # noqa: E402
from src.score import LabelScorer  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--condition", required=True, choices=["EN", "NATIVE", "TT"])
    ap.add_argument("--lang", default="en")
    ap.add_argument("--split", required=True, choices=["dev", "test"])
    ap.add_argument("--template", default="P0", choices=["P0"])
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--confirm-test", action="store_true")
    ap.add_argument("--smoke", action="store_true",
                    help="pipeline check with a model outside the protocol; writes to results/smoke/ (not a result)")
    args = ap.parse_args()

    if args.split == "test" and not args.confirm_test:
        sys.exit("Refusing to score the TEST split without --confirm-test (complete the P07 §9 checklist).")
    if args.condition == "EN" and args.lang != "en":
        sys.exit("Condition EN uses --lang en")
    if args.condition != "EN" and args.lang == "en":
        sys.exit("NATIVE/TT need --lang in {hi,bn,or,pa}")

    cfg = load_protocol()
    listed = {m["id"]: m for m in cfg["models"]["list"]}
    if args.model not in listed and not args.smoke:
        sys.exit(f"{args.model} is not in protocol_v1 models; use --smoke for pipeline checks only")
    if args.smoke and args.split == "test":
        sys.exit("--smoke runs are dev-only")
    mcfg = listed.get(args.model, {"chat_template": True})
    torch.manual_seed(cfg["scoring"]["seed"])
    raw = json.loads((ROOT / cfg["data"]["items"]).read_text())
    items = load_items(cfg, args.split, args.limit)

    trans = {}
    if args.condition != "EN":
        tp = ROOT / cfg["translation"]["cache_dir"] / f"items_{args.split}_{args.lang}.jsonl"
        trans = {r["pmid"]: r for r in map(json.loads, tp.read_text(encoding="utf-8").splitlines())}
        missing = [it["pmid"] for it in items if it["pmid"] not in trans]
        if missing:
            sys.exit(f"{len(missing)} items lack translations, e.g. {missing[:3]}; run 01_translate.py first")

    scorer = LabelScorer(args.model, chat_template=mcfg["chat_template"],
                         answer_prefix=cfg["prompt"]["answer_prefix"], dtype=cfg["models"]["dtype"])

    rows, t0 = [], time.time()
    for it in items:
        if args.condition == "EN":
            q, ctx = it["question"], join_context(it["contexts"], cfg)
        else:
            r = trans[it["pmid"]]
            sfx = "x" if args.condition == "NATIVE" else "tt"
            q, ctx = r[f"question_{sfx}"], join_context(r[f"contexts_{sfx}"], cfg)
        prompt = build_prompt(q, ctx, cfg, args.template)
        assert_no_leak(prompt, raw[it["pmid"]])
        rows.append({"pmid": it["pmid"], "gold": it["gold"], **scorer.score(prompt)})
    secs = time.time() - t0

    tag = f"{args.split}_{args.condition}_{args.lang}_{args.template}"
    out = ROOT / "results" / ("smoke" if args.smoke else "preds") / args.model.replace("/", "__") / f"{tag}.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    cols = ["pmid", "gold", "pred", "ll_yes", "ll_no", "ll_maybe", "n_input_tokens"]
    with out.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)

    gold, pred = [r["gold"] for r in rows], [r["pred"] for r in rows]
    meta = {"model": args.model, "condition": args.condition, "lang": args.lang, "split": args.split,
            "template": args.template, "n": len(rows), "device": scorer.device, "seconds": round(secs, 1),
            "label_tokens": scorer.label_token_report(),
            "pred_distribution": {l: pred.count(l) for l in ("yes", "no", "maybe")},
            "accuracy": round(100 * accuracy(gold, pred), 2), "macro_f1": round(100 * macro_f1(gold, pred), 2),
            "torch": torch.__version__, "protocol_version": cfg["protocol_version"]}
    out.with_suffix(".meta.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False))
    print(json.dumps(meta, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
