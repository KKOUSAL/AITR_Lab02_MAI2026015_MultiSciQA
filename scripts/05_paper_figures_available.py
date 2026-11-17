"""Paper figures from results that exist now (dev baseline + Hindi pilot). Real data only.

Usage: python scripts/05_paper_figures_available.py
Inputs:  results/preds/Qwen__Qwen2.5-1.5B-Instruct/dev_EN_en_P0.csv, results/pilot/pilot_translation_hi.json
Outputs: paper/figures/fig_baseline_confusion.pdf, paper/figures/fig_pilot_tokens.pdf (+ .png)
"""
import csv, json
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "paper" / "figures"
OUT.mkdir(parents=True, exist_ok=True)
L = ["yes", "no", "maybe"]

rows = list(csv.DictReader(open(ROOT / "results/preds/Qwen__Qwen2.5-1.5B-Instruct/dev_EN_en_P0.csv")))
cm = [[sum(1 for r in rows if r["gold"] == g and r["pred"] == p) for p in L] for g in L]
fig, ax = plt.subplots(figsize=(3.3, 2.8))
ax.imshow([[v / sum(row) for v in row] for row in cm], cmap="Blues", vmin=0, vmax=1)
for i in range(3):
    for j in range(3):
        frac = cm[i][j] / sum(cm[i])
        ax.text(j, i, f"{cm[i][j]}\n({100*frac:.0f}%)", ha="center", va="center", fontsize=8,
                color="white" if frac > 0.6 else "black")
ax.set_xticks(range(3), L); ax.set_yticks(range(3), L)
ax.set_xlabel("Predicted"); ax.set_ylabel("Gold")
for ext in ("pdf", "png"):
    fig.savefig(OUT / f"fig_baseline_confusion.{ext}", dpi=200, bbox_inches="tight")
plt.close(fig)

p = json.load(open(ROOT / "results/pilot/pilot_translation_hi.json"))
fig, ax = plt.subplots(figsize=(3.0, 2.2))
ax.bar(["English", "Hindi"], [p["qwen_tokens_en"], p["qwen_tokens_hi"]], color=["#4C72B0", "#DD8452"])
for i, v in enumerate([p["qwen_tokens_en"], p["qwen_tokens_hi"]]):
    ax.text(i, v, f"{v:,}", ha="center", va="bottom", fontsize=8)
ax.set_ylabel("Qwen2.5 tokens (47 sentences)")
ax.set_title(f"Fertility {p['fertility_hi_vs_en']}x", fontsize=9)
ax.set_ylim(0, p["qwen_tokens_hi"] * 1.15)
for ext in ("pdf", "png"):
    fig.savefig(OUT / f"fig_pilot_tokens.{ext}", dpi=200, bbox_inches="tight")
plt.close(fig)
print("figures written:", sorted(x.name for x in OUT.iterdir()))
