"""Figures from results/tables/<split>/summary.json (written by 03_evaluate.py). PNG + PDF.

Usage: python scripts/04_figures.py --split test
  fig1_forest_tt_vs_native   Delta(TT - NATIVE) macro-F1 with 95% CI per language x model
  fig2_fertility_vs_drop     token fertility vs macro-F1 drop (EN - NATIVE)
  fig3_number_preservation   share of numbers preserved, EN->X and EN->X->EN
A figure is skipped (with a message) when its inputs do not exist yet.
"""
import argparse
import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.data import load_protocol  # noqa: E402

MARKERS = ["o", "s", "^", "D"]


def short(m):
    return m.split("__")[-1]


def save(fig, out, name):
    out.mkdir(parents=True, exist_ok=True)
    for ext in ("png", "pdf"):
        fig.savefig(out / f"{name}.{ext}", dpi=200, bbox_inches="tight")
    plt.close(fig)
    print("wrote", out / f"{name}.png")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", required=True, choices=["dev", "test"])
    args = ap.parse_args()
    cfg = load_protocol()
    tiers = {l["code"]: l["tier"].replace("_", " ") for l in cfg["languages"]["targets"]}
    order = [l["code"] for l in cfg["languages"]["targets"]]
    s = json.loads((ROOT / "results" / "tables" / args.split / "summary.json").read_text())
    out = ROOT / "results" / "figures" / args.split

    if s["B"]:
        models = sorted({r["model"] for r in s["B"]})
        fig, ax = plt.subplots(figsize=(5.5, 2.2))
        for mi, m in enumerate(models):
            rows = {r["lang"]: r for r in s["B"] if r["model"] == m}
            for li, l in enumerate(order):
                if l in rows:
                    r = rows[l]
                    y = li + (mi - (len(models) - 1) / 2) * 0.2
                    ax.errorbar(r["delta_macro_f1"], y,
                                xerr=[[r["delta_macro_f1"] - r["ci_low"]], [r["ci_high"] - r["delta_macro_f1"]]],
                                fmt=MARKERS[mi % 4], color=f"C{mi}", capsize=3, label=short(m) if li == 0 else None)
        ax.axvline(0, color="grey", lw=0.8, ls="--")
        ax.set_yticks(range(len(order)), [f"{l} ({tiers[l]})" for l in order])
        ax.set_ylim(len(order) - 0.5, -0.5)
        ax.set_xlabel("Δ macro-F1, TT − NATIVE (points, 95% bootstrap CI)")
        if len(models) > 1:
            ax.legend(fontsize=7, frameon=False)
        else:
            ax.set_title(short(models[0]), fontsize=8)
        save(fig, out, "fig1_forest_tt_vs_native")
    else:
        print("skip fig1: no NATIVE/TT pairs yet")

    a = {(r["model"], r["condition"], r["lang"]): r["macro_f1"] for r in s["A"]}
    pts = [(m, r["lang"], r[k], a[(m, "EN", "en")] - a[(m, "NATIVE", r["lang"])])
           for r in s["D"] for k in r if k.startswith("fertility_mean__")
           for m in [k.split("fertility_mean__")[1]]
           if (m, "EN", "en") in a and (m, "NATIVE", r["lang"]) in a]
    if pts:
        fig, ax = plt.subplots(figsize=(4.5, 3.2))
        for mi, m in enumerate(sorted({p[0] for p in pts})):
            sub = [p for p in pts if p[0] == m]
            ax.scatter([p[2] for p in sub], [p[3] for p in sub], marker=MARKERS[mi % 4], color=f"C{mi}", label=short(m))
            for p in sub:
                ax.annotate(p[1], (p[2], p[3]), fontsize=7, xytext=(3, 3), textcoords="offset points")
        ax.set_xlabel("Token fertility (NATIVE ÷ EN input tokens)")
        ax.set_ylabel("macro-F1 drop, EN − NATIVE (points)")
        ax.legend(fontsize=7, frameon=False)
        save(fig, out, "fig2_fertility_vs_drop")
    else:
        print("skip fig2: needs EN + NATIVE runs and translations")

    d = [r for r in s["D"] if r.get("number_preservation_en_to_x") is not None]
    if d:
        fig, ax = plt.subplots(figsize=(4.5, 3))
        xs = list(range(len(d)))
        ax.bar([x - 0.2 for x in xs], [r["number_preservation_en_to_x"] for r in d], 0.4, label="EN→X")
        ax.bar([x + 0.2 for x in xs], [r["number_preservation_roundtrip"] for r in d], 0.4, label="EN→X→EN")
        ax.set_xticks(xs, [f'{r["lang"]}\n({tiers[r["lang"]]})' for r in d])
        ax.set_ylabel("Numbers preserved (%)")
        ax.set_ylim(0, 100)
        ax.legend(fontsize=7, frameon=False)
        save(fig, out, "fig3_number_preservation")
    else:
        print("skip fig3: no translations yet")


if __name__ == "__main__":
    main()
