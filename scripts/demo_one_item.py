"""Live demo (read-only): score ONE test item in EN, NATIVE-hi and TT-hi, and compare with the stored predictions.

By default it picks the shortest test item where EN and TT-hi answer the gold "no" correctly and
NATIVE-hi does not, which illustrates the paper's main finding ("no" disappears under native input).
Nothing is written to disk.

    python3 scripts/demo_one_item.py            # auto-pick
    python3 scripts/demo_one_item.py --pmid 123  # a specific test PMID
"""
import argparse, csv, json, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.data import build_prompt, join_context, load_items, load_protocol  # noqa: E402

MODEL = "Qwen/Qwen2.5-1.5B-Instruct"
PRED = ROOT / "results/preds/Qwen__Qwen2.5-1.5B-Instruct"


def stored(cond, lang):
    with open(PRED / f"test_{cond}_{lang}_P0.csv") as f:
        return {r["pmid"]: r for r in csv.DictReader(f)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pmid")
    args = ap.parse_args()
    cfg = load_protocol()  # refuses to run if the frozen protocol hash differs
    items = {it["pmid"]: it for it in load_items(cfg, "test")}
    trans = {r["pmid"]: r for r in map(json.loads, open(ROOT / "data/translations/items_test_hi.jsonl", encoding="utf-8"))}
    S = {"EN": stored("EN", "en"), "NATIVE": stored("NATIVE", "hi"), "TT": stored("TT", "hi")}

    pmid = args.pmid
    if pmid is None:
        cands = [p for p, r in S["EN"].items()
                 if r["gold"] == "no" and r["pred"] == "no" and S["TT"][p]["pred"] == "no" and S["NATIVE"][p]["pred"] != "no"]
        def margin(r):  # gap between best and second-best label log-likelihood in the stored run
            ll = sorted((float(r[f"ll_{l}"]) for l in ("yes", "no", "maybe")), reverse=True)
            return ll[0] - ll[1]
        # avoid near-ties, which can flip between GPUs (T4 fp16 vs Apple MPS)
        cands = [p for p in cands if min(margin(S[c][p]) for c in S) > 0.5]
        pmid = min(cands, key=lambda p: int(S["NATIVE"][p]["n_input_tokens"]))
    it, tr = items[pmid], trans[pmid]
    texts = {"EN": (it["question"], it["contexts"]),
             "NATIVE": (tr["question_x"], tr["contexts_x"]),
             "TT": (tr["question_tt"], tr["contexts_tt"])}

    print(f"PMID {pmid}   gold answer: {it['gold']}")
    for c in texts:
        print(f"  [{c:6}] Q: {texts[c][0]}")

    from src.score import LabelScorer  # imported late so the text above prints immediately
    t0 = time.time()
    scorer = LabelScorer(MODEL, chat_template=True, answer_prefix=cfg["prompt"]["answer_prefix"], dtype=cfg["models"]["dtype"])
    print(f"\nmodel loaded on {scorer.device} in {time.time() - t0:.0f}s\n")
    print(f"{'cond':7}{'tokens':>7}  {'ll_yes':>7} {'ll_no':>7} {'ll_maybe':>8}  pred   stored  match")
    for c, (q, ctxs) in texts.items():
        r = scorer.score(build_prompt(q, join_context(ctxs, cfg), cfg, "P0"))
        s = S[c][pmid]
        print(f"{c:7}{r['n_input_tokens']:>7}  {r['ll_yes']:7.2f} {r['ll_no']:7.2f} {r['ll_maybe']:8.2f}  {r['pred']:6} {s['pred']:6}  "
              f"{'yes' if r['pred'] == s['pred'] else 'NO (hardware/fp differences)'}")


if __name__ == "__main__":
    main()
