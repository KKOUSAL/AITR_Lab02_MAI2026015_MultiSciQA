# P14 — Results and Discussion (evidence-based outline)

Status: **Parts A and B are both analysed from real outputs.** The test runs come from `notebooks/02_colab_full_experiment.ipynb` (EN) and `notebooks/03_colab_rerun_translation.ipynb` (NATIVE/TT). Every value is in `results/tables/test/` and `results/exploratory/`.

---

## Part A — Analyses of measured results

### A1. English baseline behaviour (dev, n = 500, real: `results/pilot/g2_error_analysis_dev.json`)

**Direct observations**
- Qwen2.5-1.5B zero-shot: accuracy 63.00, macro-F1 45.10; Majority 55.20/23.71.
- Recall by gold label: yes 250/276 (90.6%), no 60/169 (35.5%), maybe 5/55 (9.1%).
- Predictions: 398 yes / 84 no / 18 maybe. For gold-"no" items predicted "yes", the median log-likelihood gap (yes − no) is 3.13 nats.
- Wrong answers have a smaller margin between the top two labels than correct ones (median 1.91 vs 3.08).
- Accuracy by input length (terciles at 346 / 428 tokens): short 66.1, medium 62.0, long 60.8.

**Possible mechanisms (not tested)**
- An affirmative prior in instruction-tuned models, or label-frequency effects in pretraining, could produce the "yes" bias.
- "maybe" is rare as a one-word answer in general text, which may depress its likelihood under label scoring.

**Alternative explanations**
- The bias may come from the scoring method (raw log-likelihood, no calibration) rather than the model's "beliefs"; a calibrated or generative evaluation might differ.
- The length trend is small (5.3 points from short to long) with about 166 items per bin. It may be noise: no test was run, so no claim is made.

**Unsupported claims to avoid:** "the model cannot detect negative findings" (it gets 35.5% of "no" right); "longer abstracts cause errors" (not tested).

**Consequence for the main comparison:** the yes-bias is shared by all conditions, because they use the same model and scoring. Paired NATIVE-vs-TT differences remain interpretable, but per-class F1 must be reported, since macro-F1 is dominated by the weak "no" and "maybe" classes.

### A2. Translation pilot (dev, 5 items, Hindi only; real: `results/pilot/pilot_translation_hi.json`)

**Direct observations**
- 47 sentences EN→hi, 0 truncated; 32 also translated back to English (the run was stopped for speed).
- Numbers preserved: **34/34** EN→hi (after native-digit normalisation); **20/20** in the round trip.
- **Token fertility:** the same content costs Qwen **6,079 tokens in Hindi vs 1,352 in English (4.5×)**.

**Interpretation limits:** 5 items is a pipeline check, not an estimate. The 100% number preservation may not hold for Odia or for the full test set; H3 stays open.

**Why the fertility finding matters:** a 4.5× longer input means 4.5× more compute and cost in the NATIVE condition. Long inputs may also dilute attention; this is a candidate mechanism for RQ1, to be checked against the test results, not assumed. It is consistent with Ahia et al. 2023 (tokenization cost imbalance), which is cited in the review.

**Data artefact found:** the PubMedQA source text contains broken decimals (e.g., "14. 1%"). The translator preserves them as-is. The number metric counts "14" and "1" on both sides, so the comparison stays fair. Report this in the data section.

---

## Part B — Test-set analysis plan (pre-registered decision rules)

| RQ / H | Table / figure | Supported if… | Contradicted if… |
|---|---|---|---|
| RQ1 / H1 (TT > NATIVE for Odia) | Table B, Fig. 1 | Δ(TT − NATIVE) CI for `or` excludes 0 on the positive side **and** Holm p < 0.05 | Δ ≤ 0 or CI includes 0. Report as a negative transfer result. |
| RQ1 / H2 (NATIVE ≥ TT for Hindi) | Table B, Fig. 1 | No significant positive Δ for `hi` | Significant TT advantage for Hindi |
| RQ2 (consistency) | Table C | Descriptive: agreement, κ and flip rate vs own EN answers | — |
| RQ3 / H3 (number loss larger for Odia) | Table D, Fig. 3 | Lower preservation for `or` than `hi`, EN→X and round trip | Equal or higher preservation for `or` |
| Efficiency | Table D, Fig. 2 | Descriptive fertility per language | — |

**For each RQ, write separately:** direct observation → possible mechanism → alternative explanations → what is not claimed.

## Part B results (test, n = 500; VERIFIED from `results/tables/test/summary.json`; interpretation ACCEPTED by student 2026-11-17)

| Condition | Acc | Macro-F1 | F1 yes / no / maybe |
|---|---|---|---|
| Majority | 55.20 | 23.71 | 71.1 / 0.0 / 0.0 |
| EN | 63.60 | 44.59 | 75.4 / 47.4 / 11.0 |
| NATIVE-hi | 41.60 | 30.04 | 63.5 / 7.8 / 18.8 |
| TT-hi | 62.20 | 42.92 | 74.7 / 46.2 / 7.9 |
| NATIVE-or | 47.60 | 28.86 | 65.2 / 17.4 / 4.1 |
| TT-or | 60.40 | 41.28 | 72.7 / 45.8 / 5.4 |

**RQ1 / H1 (Odia): SUPPORTED.** Δ(TT − NATIVE) = +12.42 [+7.09, +17.58], Holm p = 1.4e-7 (TT-only correct 106 vs NATIVE-only 42).
**RQ1 / H2 (Hindi): CONTRADICTED.** Δ = +12.88 [+7.79, +17.87], Holm p = 9.4e-16 (136 vs 33). The tier pattern from Singh et al. does not transfer to this setting. Gap difference hi − or (paired bootstrap, added after the P16 review, exploratory) = +0.46 [−5.01, +6.13]: no detectable difference, but up to about 6 points cannot be excluded.
- *Observation:* NATIVE loses the "no" class (recall 7/169 hi, 21/169 or, vs 60/169 EN); Hindi shifts to "maybe" (211 predictions), Odia to "yes" (384).
- *Possible mechanisms (untested):* weak Indic comprehension in a 1.5B model; biomedical terminology; machine-translated "native" text.
- *Alternatives:* uncalibrated scoring could amplify default-label behaviour; the language effect cannot be separated from the tier effect (one language per tier).
- *Not claimed:* that native processing is worse in general, or any causal mechanism.

**RQ2.** Agreement / κ vs own EN answers: TT-hi 88.8 / 0.68, TT-or 84.8 / 0.58, NATIVE-hi 54.6 / 0.16, NATIVE-or 66.2 / 0.06. The higher NATIVE-or agreement is driven by its "yes" shift (κ is near chance). EN-correct → wrong flips: NATIVE 42.8% / 34.0%, TT 8.2% / 12.3%.

**RQ3 / H3: SUPPORTED (descriptive, as pre-registered).** Number preservation EN→X: hi 93.46, or 81.45; round trip: 90.36, 78.94; round-trip chrF: 80.63, 69.22. Fertility: hi 3.60×, or 7.82×. The higher Odia token cost did not produce a larger NATIVE loss, so fertility alone does not explain the drop.

**Exploratory (D16, not pre-registered):** Odia IndicTrans2 degeneration (506/5,285 sentences; 401/500 items). On the clean subset (n = 99): Δ +13.02 [+2.50, +22.35], p = 0.016. Affected subset: +12.47. Fertility changes by about 1% when the runs are stripped. The degeneration does not explain the result. Correction after P16: Hindi also has shorter dot runs in 14 items (none truncated, none present in the English source). Odia has 398 items with runs and 3 with fragment repetition.

**Note:** the 5-item pilot's 100% number preservation did not hold at scale (93.5% for Hindi). This is a reminder that pilot results are not estimates.

## Limitations to report regardless of outcome

1. Single 1.5B model (D13, D14): no cross-model check.
2. One language per tier (D15): a tier effect cannot be separated from a language effect.
3. "Native" text is machine-translated, not written by native speakers (the BenchMAX critique).
4. Possible PubMedQA pretraining contamination (the paired design reduces its impact).
5. Uncalibrated log-likelihood scoring with a strong yes-bias (A1).
6. The prompt-sensitivity analysis was dropped (D15).
7. Odia translation degeneration (D16).

## Follow-up experiments (ranked by cost vs information)

1. **Label calibration** (e.g., contextual calibration on dev): cheap; tests whether the yes-bias changes the NATIVE/TT gap.
2. **Second model** (Llama-3.2-1B, already downloaded locally): cheap on Colab; tests cross-model robustness.
3. **Native-speaker check** of 30 Hindi translations: low compute, needs a human; directly addresses the main validity threat.
