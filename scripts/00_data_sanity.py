"""G1/G2 first executable milestone: PubMedQA PQA-L data sanity check.

Stdlib only. Verifies dataset integrity, the official 500/500 test/CV split,
label distributions, and the Majority baseline against Jin et al. (2019),
Table 5: Majority = 55.20 acc / 23.71 macro-F1 on the PQA-L test set.

Usage (from repo root):
    python scripts/00_data_sanity.py
Outputs:
    results/sanity/data_sanity.json
    data/splits/test_pmids.txt, data/splits/dev_pmids.txt
"""
import json
import platform
import re
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "pubmedqa_repo" / "data"
OUT = ROOT / "results" / "sanity"
SPLITS = ROOT / "data" / "splits"
LABELS = ("yes", "no", "maybe")


def macro_f1(gold, pred):
    f1s = []
    for c in LABELS:
        tp = sum(g == c and p == c for g, p in zip(gold, pred))
        fp = sum(g != c and p == c for g, p in zip(gold, pred))
        fn = sum(g == c and p != c for g, p in zip(gold, pred))
        prec = tp / (tp + fp) if tp + fp else 0.0
        rec = tp / (tp + fn) if tp + fn else 0.0
        f1s.append(2 * prec * rec / (prec + rec) if prec + rec else 0.0)
    return sum(f1s) / len(f1s)


def dist(labels):
    c = Counter(labels)
    n = len(labels)
    return {k: {"n": c[k], "pct": round(100 * c[k] / n, 2)} for k in LABELS}


def main():
    pqal = json.loads((RAW / "ori_pqal.json").read_text())
    test_gt = json.loads((RAW / "test_ground_truth.json").read_text())

    # --- integrity checks -------------------------------------------------
    assert len(pqal) == 1000, f"expected 1000 PQA-L items, got {len(pqal)}"
    required = {"QUESTION", "CONTEXTS", "LONG_ANSWER", "final_decision"}
    missing = [p for p, v in pqal.items() if not required <= v.keys()]
    assert not missing, f"items missing fields: {missing[:5]}"
    bad = [p for p, v in pqal.items() if v["final_decision"] not in LABELS]
    assert not bad, f"unexpected labels: {bad[:5]}"
    empty = [p for p, v in pqal.items()
             if not v["QUESTION"].strip() or not "".join(v["CONTEXTS"]).strip()]
    assert not empty, f"empty question/context: {empty[:5]}"

    # --- split checks -----------------------------------------------------
    test_ids = set(test_gt)
    assert len(test_ids) == 500
    assert test_ids <= pqal.keys(), "test ids not in PQA-L"
    dev_ids = set(pqal) - test_ids
    assert len(dev_ids) == 500 and not (dev_ids & test_ids)
    label_mismatch = [p for p in test_ids if test_gt[p] != pqal[p]["final_decision"]]
    assert not label_mismatch, f"ground-truth/PQA-L label mismatch: {label_mismatch[:5]}"
    dup_q = len(pqal) - len({v["QUESTION"].strip().lower() for v in pqal.values()})

    # --- Majority baseline (predict 'yes') on official test set -------------
    t_sorted = sorted(test_ids)
    gold = [test_gt[p] for p in t_sorted]
    pred = ["yes"] * len(gold)
    acc = sum(g == p for g, p in zip(gold, pred)) / len(gold)
    mf1 = macro_f1(gold, pred)

    # --- descriptive stats for RQ3 (numbers in evidence) -------------------
    num_re = re.compile(r"\d")
    ctx_words = [len(" ".join(pqal[p]["CONTEXTS"]).split()) for p in t_sorted]
    has_num = sum(bool(num_re.search(" ".join(pqal[p]["CONTEXTS"]))) for p in t_sorted)

    report = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "source": "github.com/pubmedqa/pubmedqa @ 1cbae8e (data/ori_pqal.json, data/test_ground_truth.json)",
        "n_pqal": len(pqal),
        "n_test": len(test_ids),
        "n_dev": len(dev_ids),
        "duplicate_questions_case_insensitive": dup_q,
        "label_dist_all": dist([v["final_decision"] for v in pqal.values()]),
        "label_dist_test": dist(gold),
        "label_dist_dev": dist([pqal[p]["final_decision"] for p in dev_ids]),
        "majority_baseline_test": {"accuracy": round(100 * acc, 2), "macro_f1": round(100 * mf1, 2)},
        "published_majority_jin2019_table5": {"accuracy": 55.20, "macro_f1": 23.71},
        "test_context_words": {"min": min(ctx_words), "mean": round(sum(ctx_words) / len(ctx_words), 1),
                               "max": max(ctx_words), "total": sum(ctx_words)},
        "test_items_with_digits_in_context": {"n": has_num, "pct": round(100 * has_num / 500, 1)},
    }

    OUT.mkdir(parents=True, exist_ok=True)
    SPLITS.mkdir(parents=True, exist_ok=True)
    (OUT / "data_sanity.json").write_text(json.dumps(report, indent=2))
    (SPLITS / "test_pmids.txt").write_text("\n".join(t_sorted) + "\n")
    (SPLITS / "dev_pmids.txt").write_text("\n".join(sorted(dev_ids)) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
