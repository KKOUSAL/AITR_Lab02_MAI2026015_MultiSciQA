"""EXPLORATORY (not pre-registered, added after test results were seen; see D16).
Odia IndicTrans2 outputs often end in a degenerate run of repeated characters ("......").
Re-estimate TT - NATIVE on the subset of items with no degenerate segment, and measure
fertility with the degenerate runs stripped. Primary results are unchanged."""
import csv, json, re, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.metrics import macro_f1, accuracy, paired_bootstrap_delta, mcnemar_exact

ROOT = Path(__file__).resolve().parents[1]
DEGEN = re.compile(r"(.)\1{20,}|(?:(\S{1,3}) ){20,}")
PRED = ROOT / "results/preds/Qwen__Qwen2.5-1.5B-Instruct"

def preds(cond, lang):
    with open(PRED / f"test_{cond}_{lang}_P0.csv") as f:
        return {r["pmid"]: r for r in csv.DictReader(f)}

out = {}
for lang in ["hi", "or"]:
    items = [json.loads(l) for l in open(ROOT / f"data/translations/items_test_{lang}.jsonl")]
    degen = {it["pmid"] for it in items if any(DEGEN.search(s) for s in [it["question_x"], *it["contexts_x"]])}
    nat, tt = preds("NATIVE", lang), preds("TT", lang)
    for name, keep in [("degenerate", lambda p: p in degen), ("clean", lambda p: p not in degen)]:
        pm = sorted(p for p in nat if keep(p))
        g = [nat[p]["gold"] for p in pm]; a = [nat[p]["pred"] for p in pm]; b = [tt[p]["pred"] for p in pm]
        d = paired_bootstrap_delta(g, a, b, macro_f1, n_resamples=10000, seed=2026)
        d = {k: (round(100 * v, 2) if k != "n_resamples" else v) for k, v in d.items()}
        mc = mcnemar_exact(g, a, b)
        out[f"{lang}_{name}"] = {"n": len(pm), "native_acc": round(100 * accuracy(g, a), 2), "tt_acc": round(100 * accuracy(g, b), 2),
            "native_macro_f1": round(100 * macro_f1(g, a), 2), "tt_macro_f1": round(100 * macro_f1(g, b), 2), "delta": d, "mcnemar": mc}
# fertility (Qwen tokens X / EN) with degenerate runs removed
from transformers import AutoTokenizer
tok = AutoTokenizer.from_pretrained("Qwen/Qwen2.5-1.5B-Instruct")
en = {}
sys.path.insert(0, str(ROOT))
from src.data import load_protocol, load_items
for it in load_items(load_protocol(), "test", None):
    en[it["pmid"]] = len(tok(" ".join(it["contexts"]))["input_ids"])
for lang in ["hi", "or"]:
    items = [json.loads(l) for l in open(ROOT / f"data/translations/items_test_{lang}.jsonl")]
    raw = [len(tok(" ".join(it["contexts_x"]))["input_ids"]) / en[it["pmid"]] for it in items]
    cln = [len(tok(" ".join(DEGEN.sub(lambda m: m.group(0)[:3], s) for s in it["contexts_x"]))["input_ids"]) / en[it["pmid"]] for it in items]
    out[f"fertility_{lang}"] = {"raw_mean": round(sum(raw) / len(raw), 3), "degeneration_stripped_mean": round(sum(cln) / len(cln), 3)}
json.dump(out, open(ROOT / "results/exploratory/degeneration_subset.json", "w"), indent=2, default=str)
for k, v in out.items():
    print(k, json.dumps(v, default=str))

# --- Interaction (added after peer review P16): is the TT-NATIVE gap different for hi vs or?
# Same 500 PMIDs in both languages, so resample items jointly (paired).
import numpy as np
P = {(c, l): preds(c, l) for c in ("NATIVE", "TT") for l in ("hi", "or")}
pm = sorted(P[("NATIVE", "hi")])
gold = np.array([P[("NATIVE", "hi")][p]["gold"] for p in pm])
arr = {k: np.array([v[p]["pred"] for p in pm]) for k, v in P.items()}
def gap(idx, l):
    g = gold[idx].tolist()
    return macro_f1(g, arr[("TT", l)][idx].tolist()) - macro_f1(g, arr[("NATIVE", l)][idx].tolist())
rng = np.random.default_rng(2026); n = len(pm); full = np.arange(n)
point = gap(full, "hi") - gap(full, "or")
ds = []
for _ in range(10000):
    idx = rng.integers(0, n, n); ds.append(gap(idx, "hi") - gap(idx, "or"))
lo, hi_ = np.quantile(ds, [0.025, 0.975])
out["interaction_gap_hi_minus_or"] = {"delta": round(100 * point, 2), "ci_low": round(float(100 * lo), 2), "ci_high": round(float(100 * hi_), 2), "n_resamples": 10000}
json.dump(out, open(ROOT / "results/exploratory/degeneration_subset.json", "w"), indent=2, default=str)
print("interaction", out["interaction_gap_hi_minus_or"])
