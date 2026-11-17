"""Evaluation metrics and paired statistics (protocol_v1: metrics, statistics)."""
from __future__ import annotations

from collections import Counter

import numpy as np
from scipy.stats import binomtest

LABELS = ("yes", "no", "maybe")


def _check(gold, pred):
    if len(gold) != len(pred):
        raise ValueError(f"length mismatch {len(gold)} vs {len(pred)}")
    bad = {x for x in list(gold) + list(pred) if x not in LABELS}
    if bad:
        raise ValueError(f"unknown labels {bad}")


def accuracy(gold, pred) -> float:
    _check(gold, pred)
    return float(np.mean([g == p for g, p in zip(gold, pred)]))


def per_class_f1(gold, pred) -> dict:
    _check(gold, pred)
    out = {}
    for c in LABELS:
        tp = sum(g == c and p == c for g, p in zip(gold, pred))
        fp = sum(g != c and p == c for g, p in zip(gold, pred))
        fn = sum(g == c and p != c for g, p in zip(gold, pred))
        prec = tp / (tp + fp) if tp + fp else 0.0
        rec = tp / (tp + fn) if tp + fn else 0.0
        out[c] = 2 * prec * rec / (prec + rec) if prec + rec else 0.0
    return out


def macro_f1(gold, pred) -> float:
    return float(np.mean(list(per_class_f1(gold, pred).values())))


def confusion(gold, pred) -> dict:
    _check(gold, pred)
    c = Counter(zip(gold, pred))
    return {g: {p: c[(g, p)] for p in LABELS} for g in LABELS}


def cohen_kappa(a, b) -> float:
    """Agreement between two prediction vectors (e.g., X-condition vs own EN predictions)."""
    _check(a, b)
    n = len(a)
    po = sum(x == y for x, y in zip(a, b)) / n
    ca, cb = Counter(a), Counter(b)
    pe = sum(ca[l] * cb[l] for l in LABELS) / (n * n)
    return 1.0 if pe == 1 else (po - pe) / (1 - pe)


def paired_bootstrap_delta(gold, pred_a, pred_b, metric=macro_f1,
                           n_resamples: int = 10000, seed: int = 2026, ci: float = 0.95) -> dict:
    """Delta = metric(B) - metric(A), resampling items with replacement (paired)."""
    _check(gold, pred_a)
    _check(gold, pred_b)
    gold, pred_a, pred_b = map(np.asarray, (gold, pred_a, pred_b))
    rng = np.random.default_rng(seed)
    n = len(gold)
    point = metric(gold.tolist(), pred_b.tolist()) - metric(gold.tolist(), pred_a.tolist())
    deltas = np.empty(n_resamples)
    for i in range(n_resamples):
        idx = rng.integers(0, n, n)
        g = gold[idx].tolist()
        deltas[i] = metric(g, pred_b[idx].tolist()) - metric(g, pred_a[idx].tolist())
    lo, hi = np.quantile(deltas, [(1 - ci) / 2, 1 - (1 - ci) / 2])
    return {"delta": float(point), "ci_low": float(lo), "ci_high": float(hi), "n_resamples": n_resamples}


def mcnemar_exact(gold, pred_a, pred_b) -> dict:
    """Exact McNemar test on per-item correctness (two-sided binomial on discordant pairs)."""
    _check(gold, pred_a)
    _check(gold, pred_b)
    a_only = sum(g == a and g != b for g, a, b in zip(gold, pred_a, pred_b))
    b_only = sum(g != a and g == b for g, a, b in zip(gold, pred_a, pred_b))
    n = a_only + b_only
    p = 1.0 if n == 0 else binomtest(a_only, n, 0.5).pvalue
    return {"a_only_correct": a_only, "b_only_correct": b_only, "p": float(p)}


def holm(pvals: dict) -> dict:
    """Holm-Bonferroni adjusted p-values, keyed like the input."""
    keys = sorted(pvals, key=pvals.get)
    m = len(keys)
    adj, running = {}, 0.0
    for i, k in enumerate(keys):
        running = max(running, min(1.0, (m - i) * pvals[k]))
        adj[k] = running
    return adj
