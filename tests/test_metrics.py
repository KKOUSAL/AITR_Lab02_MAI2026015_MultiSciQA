import pytest

from src.data import load_items, load_protocol
from src.metrics import (accuracy, cohen_kappa, confusion, holm, macro_f1,
                         mcnemar_exact, paired_bootstrap_delta, per_class_f1)

CFG = load_protocol()


def test_majority_reproduces_published_baseline():
    """Jin et al. 2019, Table 5: Majority = 55.20 acc / 23.71 macro-F1 on the test set."""
    gold = [x["gold"] for x in load_items(CFG, "test")]
    pred = ["yes"] * len(gold)
    assert round(100 * accuracy(gold, pred), 2) == 55.20
    assert round(100 * macro_f1(gold, pred), 2) == 23.71


def test_perfect_and_hand_computed():
    g = ["yes", "no", "maybe", "yes"]
    assert macro_f1(g, g) == 1.0
    p = ["yes", "yes", "maybe", "no"]
    f = per_class_f1(g, p)        # yes: P=1/2 R=1/2; no: 0; maybe: 1
    assert f["yes"] == pytest.approx(0.5) and f["no"] == 0 and f["maybe"] == 1
    assert confusion(g, p)["no"]["yes"] == 1


def test_kappa_known_values():
    a = ["yes", "no"] * 10
    assert cohen_kappa(a, a) == pytest.approx(1.0)
    # Hand example: po=0.5, pe=0.5 -> kappa 0
    assert cohen_kappa(["yes", "yes", "no", "no"], ["yes", "no", "yes", "no"]) == pytest.approx(0.0)


def test_bootstrap_identical_predictions_zero_delta():
    g = ["yes", "no", "maybe"] * 20
    r = paired_bootstrap_delta(g, g, g, n_resamples=200)
    assert r["delta"] == 0 and r["ci_low"] == 0 and r["ci_high"] == 0


def test_bootstrap_sign_and_determinism():
    g = ["yes", "no", "maybe", "no"] * 25
    worse = ["yes"] * 100
    r1 = paired_bootstrap_delta(g, worse, g, n_resamples=300)
    r2 = paired_bootstrap_delta(g, worse, g, n_resamples=300)
    assert r1 == r2 and r1["delta"] > 0 and r1["ci_low"] > 0


def test_mcnemar():
    g = ["yes"] * 20
    a = ["yes"] * 20
    b = ["no"] * 20
    r = mcnemar_exact(g, a, b)
    assert r["a_only_correct"] == 20 and r["b_only_correct"] == 0 and r["p"] < 1e-5
    assert mcnemar_exact(g, a, a)["p"] == 1.0


def test_holm():
    adj = holm({"a": 0.01, "b": 0.04, "c": 0.03})
    assert adj["a"] == pytest.approx(0.03)
    assert adj["c"] == pytest.approx(0.06)
    assert adj["b"] == pytest.approx(0.06)     # monotone


def test_rejects_bad_labels():
    with pytest.raises(ValueError):
        macro_f1(["yes"], ["Yes"])
