"""Tests for scripts/03_evaluate.py. Synthetic prediction files live in a temp dir only."""
import csv
import importlib.util

import pytest

from src.data import ROOT, load_items, load_protocol

spec = importlib.util.spec_from_file_location("ev", ROOT / "scripts" / "03_evaluate.py")
ev = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ev)

CFG = load_protocol()
DEV = load_items(CFG, "dev")


def write(dirp, model, name, rows):
    d = dirp / model
    d.mkdir(parents=True, exist_ok=True)
    with (d / name).open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["pmid", "gold", "pred", "ll_yes", "ll_no", "ll_maybe", "n_input_tokens"])
        w.writeheader()
        w.writerows(rows)


def rows(pred_fn, ntok=100):
    return [{"pmid": it["pmid"], "gold": it["gold"], "pred": pred_fn(it), "ll_yes": -1, "ll_no": -2,
             "ll_maybe": -3, "n_input_tokens": ntok} for it in DEV]


def test_majority_row_and_identical_conditions(tmp_path):
    write(tmp_path / "p", "M", "dev_EN_en_P0.csv", rows(lambda it: it["gold"]))
    write(tmp_path / "p", "M", "dev_NATIVE_hi_P0.csv", rows(lambda it: "yes", 300))
    write(tmp_path / "p", "M", "dev_TT_hi_P0.csv", rows(lambda it: "yes", 120))
    s = ev.evaluate("dev", pred_root=tmp_path / "p", out_dir=tmp_path / "o", n_resamples=200)
    a = {(r["model"], r["condition"], r["lang"]): r for r in s["A"]}
    assert a[("M", "EN", "en")]["macro_f1"] == 100.0
    assert a[("Majority", "-", "-")]["accuracy"] == 55.2
    b = s["B"][0]
    assert b["delta_macro_f1"] == 0 and not b["effect_claimed"]          # identical predictions
    c = {r["condition"]: r for r in s["C"]}
    assert c["NATIVE"]["agreement_with_en"] == 55.2                      # EN perfect, X all-yes
    assert (tmp_path / "o" / "summary.json").exists()


def test_rejects_missing_items(tmp_path):
    write(tmp_path / "p", "M", "dev_EN_en_P0.csv", rows(lambda it: "yes")[:-1])
    with pytest.raises(ev.EvalError, match="PMID mismatch"):
        ev.evaluate("dev", pred_root=tmp_path / "p", out_dir=tmp_path / "o", n_resamples=10)


def test_rejects_wrong_gold(tmp_path):
    r = rows(lambda it: "yes")
    r[0]["gold"] = "no" if r[0]["gold"] != "no" else "yes"
    write(tmp_path / "p", "M", "dev_EN_en_P0.csv", r)
    with pytest.raises(ev.EvalError, match="gold label mismatch"):
        ev.evaluate("dev", pred_root=tmp_path / "p", out_dir=tmp_path / "o", n_resamples=10)


def test_rejects_invalid_label_and_duplicates(tmp_path):
    r = rows(lambda it: "yes")
    r[3]["pred"] = "Yes"
    write(tmp_path / "p", "M", "dev_EN_en_P0.csv", r)
    with pytest.raises(ev.EvalError, match="invalid prediction"):
        ev.evaluate("dev", pred_root=tmp_path / "p", out_dir=tmp_path / "o", n_resamples=10)
    r = rows(lambda it: "yes")
    r[-1] = dict(r[0])
    write(tmp_path / "q", "M", "dev_EN_en_P0.csv", r)
    with pytest.raises(ev.EvalError, match="duplicate"):
        ev.evaluate("dev", pred_root=tmp_path / "q", out_dir=tmp_path / "o", n_resamples=10)
