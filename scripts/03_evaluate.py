"""Prompt 13: evaluate genuine prediction files under the frozen protocol.

Checks run before any metric: PMID alignment with the split, duplicate or missing rows,
gold labels against the official ground truth, valid label values, and no empty fields.

Usage:
    python scripts/03_evaluate.py --split dev
    python scripts/03_evaluate.py --split test
Outputs (results/tables/<split>/):
    table_A_scores.csv          model x condition x language: accuracy, macro-F1, per-class F1
    table_B_tt_vs_native.csv    Delta(TT - NATIVE) macro-F1, paired bootstrap CI, McNemar p, Holm p
    table_C_consistency.csv     agreement, kappa and flip rate vs the model's own EN predictions
    table_D_rq3.csv             number preservation, round-trip chrF, token fertility
    summary.json                everything above plus input files and protocol hash
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from pathlib import Path
from statistics import mean

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.data import PROTOCOL, join_context, load_items, load_protocol  # noqa: E402
from src.metrics import (LABELS, accuracy, cohen_kappa, holm, macro_f1,  # noqa: E402
                         mcnemar_exact, paired_bootstrap_delta, per_class_f1)
from src.rq3 import fertility, number_preservation  # noqa: E402


class EvalError(RuntimeError):
    pass


def read_preds(path: Path, expected_gold: dict) -> dict:
    with path.open() as f:
        rows = list(csv.DictReader(f))
    pmids = [r["pmid"] for r in rows]
    if len(pmids) != len(set(pmids)):
        raise EvalError(f"{path.name}: duplicate PMIDs")
    if set(pmids) != set(expected_gold):
        miss, extra = set(expected_gold) - set(pmids), set(pmids) - set(expected_gold)
        raise EvalError(f"{path.name}: PMID mismatch (missing {len(miss)}, extra {len(extra)})")
    for r in rows:
        if r["gold"] != expected_gold[r["pmid"]]:
            raise EvalError(f"{path.name}: gold label mismatch for {r['pmid']}")
        if r["pred"] not in LABELS:
            raise EvalError(f"{path.name}: invalid prediction {r['pred']!r} for {r['pmid']}")
        for k in ("ll_yes", "ll_no", "ll_maybe", "n_input_tokens"):
            if r.get(k) in (None, ""):
                raise EvalError(f"{path.name}: missing {k} for {r['pmid']}")
    return {r["pmid"]: r for r in rows}


def discover(pred_root: Path, split: str, template: str) -> dict:
    found = {}
    for p in sorted(pred_root.glob(f"*/{split}_*_{template}.csv")):
        _, cond, lang, _ = p.stem.split("_")
        found[(p.parent.name, cond, lang)] = p
    return found


def _scores(g, pv):
    return {"accuracy": round(100 * accuracy(g, pv), 2), "macro_f1": round(100 * macro_f1(g, pv), 2),
            **{f"f1_{k}": round(100 * v, 2) for k, v in per_class_f1(g, pv).items()}}


def evaluate(split: str, template: str = "P0", pred_root: Path | None = None,
             out_dir: Path | None = None, n_resamples: int | None = None) -> dict:
    cfg = load_protocol()
    pred_root = pred_root or ROOT / "results" / "preds"
    out_dir = out_dir or ROOT / "results" / "tables" / split
    st = cfg["statistics"]
    n_res = n_resamples or st["bootstrap"]["resamples"]

    items = load_items(cfg, split)
    gold = {it["pmid"]: it["gold"] for it in items}
    order = sorted(gold)
    files = discover(pred_root, split, template)
    if not files:
        raise EvalError(f"no prediction files for split={split} template={template}")
    preds = {k: read_preds(p, gold) for k, p in files.items()}
    models = sorted({m for m, _, _ in preds})
    langs = [l["code"] for l in cfg["languages"]["targets"]]
    g = [gold[p] for p in order]

    def vec(key):
        return [preds[key][p]["pred"] for p in order]

    table_a = [{"model": m, "condition": c, "lang": l, "n": len(order), **_scores(g, vec((m, c, l)))}
               for (m, c, l) in sorted(preds)]
    table_a.append({"model": "Majority", "condition": "-", "lang": "-", "n": len(order), **_scores(g, ["yes"] * len(g))})

    table_b, pvals = [], {}
    for m in models:
        for l in langs:
            a, b = (m, "NATIVE", l), (m, "TT", l)
            if a in preds and b in preds:
                bs = paired_bootstrap_delta(g, vec(a), vec(b), macro_f1, n_res, st["bootstrap"]["seed"], st["bootstrap"]["ci"])
                mc = mcnemar_exact(g, vec(a), vec(b))
                pvals[f"{m}|{l}"] = mc["p"]
                table_b.append({"model": m, "lang": l, "delta_macro_f1": round(100 * bs["delta"], 2),
                                "ci_low": round(100 * bs["ci_low"], 2), "ci_high": round(100 * bs["ci_high"], 2),
                                "native_only_correct": mc["a_only_correct"], "tt_only_correct": mc["b_only_correct"],
                                "mcnemar_p": mc["p"]})
    adj = holm(pvals)
    for r in table_b:
        r["holm_p"] = adj[f"{r['model']}|{r['lang']}"]
        r["effect_claimed"] = bool((r["ci_low"] > 0 or r["ci_high"] < 0) and r["holm_p"] < 0.05)

    table_c = []
    for m in models:
        if (m, "EN", "en") not in preds:
            continue
        en = vec((m, "EN", "en"))
        n_ok = sum(e == t for e, t in zip(en, g))
        for (mm, c, l) in sorted(preds):
            if mm == m and c != "EN":
                x = vec((m, c, l))
                flips = sum(e == t and y != t for e, y, t in zip(en, x, g))
                table_c.append({"model": m, "condition": c, "lang": l,
                                "agreement_with_en": round(100 * mean(e == y for e, y in zip(en, x)), 2),
                                "kappa_vs_en": round(cohen_kappa(en, x), 4),
                                "flip_en_correct_to_wrong": round(100 * flips / n_ok, 2) if n_ok else None})

    table_d = []
    try:
        import sacrebleu
    except ImportError:
        sacrebleu = None
    by_item = {it["pmid"]: it for it in items}
    for l in langs:
        tp = ROOT / cfg["translation"]["cache_dir"] / f"items_{split}_{l}.jsonl"
        if not tp.exists():
            continue
        recs = {r["pmid"]: r for r in map(json.loads, tp.read_text(encoding="utf-8").splitlines())}
        if set(recs) != set(gold):
            raise EvalError(f"{tp.name}: translated items do not cover the split exactly")
        src = [join_context(by_item[p]["contexts"], cfg) for p in order]
        xs = [join_context(recs[p]["contexts_x"], cfg) for p in order]
        tts = [join_context(recs[p]["contexts_tt"], cfg) for p in order]

        def pooled(rs):
            ns = sum(r["n_source"] for r in rs)
            return round(100 * sum(r["n_preserved"] for r in rs) / ns, 2) if ns else None

        row = {"lang": l,
               "number_preservation_en_to_x": pooled([number_preservation(s, x) for s, x in zip(src, xs)]),
               "number_preservation_roundtrip": pooled([number_preservation(s, t) for s, t in zip(src, tts)]),
               "roundtrip_chrF": round(sacrebleu.corpus_chrf(tts, [src]).score, 2) if sacrebleu else None}
        for m in models:
            if (m, "EN", "en") in preds and (m, "NATIVE", l) in preds:
                row[f"fertility_mean__{m}"] = round(mean(
                    fertility(int(preds[(m, "NATIVE", l)][p]["n_input_tokens"]), int(preds[(m, "EN", "en")][p]["n_input_tokens"]))
                    for p in order), 3)
        table_d.append(row)

    out_dir.mkdir(parents=True, exist_ok=True)
    for name, rows in [("table_A_scores", table_a), ("table_B_tt_vs_native", table_b),
                       ("table_C_consistency", table_c), ("table_D_rq3", table_d)]:
        if rows:
            keys = list(dict.fromkeys(k for r in rows for k in r))
            with (out_dir / f"{name}.csv").open("w", newline="") as f:
                w = csv.DictWriter(f, fieldnames=keys)
                w.writeheader()
                w.writerows(rows)
    summary = {"split": split, "template": template, "n_items": len(order),
               "protocol": PROTOCOL.name, "protocol_sha256": hashlib.sha256(PROTOCOL.read_bytes()).hexdigest(),
               "inputs": {"|".join(k): str(v.relative_to(ROOT)) if v.is_relative_to(ROOT) else str(v)
                          for k, v in files.items()},
               "bootstrap_resamples": n_res, "A": table_a, "B": table_b, "C": table_c, "D": table_d}
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2))
    return summary


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", required=True, choices=["dev", "test"])
    ap.add_argument("--template", default="P0", choices=["P0"])
    args = ap.parse_args()
    s = evaluate(args.split, args.template)
    print(f"split={s['split']} template={s['template']} n={s['n_items']} protocol={s['protocol']}")
    for r in s["A"]:
        print(f'  {r["model"]:38s} {r["condition"]:7s} {r["lang"]:3s} acc={r["accuracy"]:6.2f} macroF1={r["macro_f1"]:6.2f}')
    for r in s["B"]:
        print(f'  TT-NATIVE {r["model"]} {r["lang"]}: {r["delta_macro_f1"]:+.2f} [{r["ci_low"]:+.2f},{r["ci_high"]:+.2f}] holm_p={r["holm_p"]:.4f}')


if __name__ == "__main__":
    main()
