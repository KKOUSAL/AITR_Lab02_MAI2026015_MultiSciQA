# Research Decisions Log

Portable log of decisions, reasons, evidence and next actions (Prompt 01).
Labels: **VERIFIED** (primary source or actual execution) · **INFERRED** (plausible, needs testing) · **UNKNOWN** (no evidence yet).
Decisions are proposed with AI help; each Status records whether the student accepted or rejected it.

## Review scope (G0 → Lab 02)

- **Prior review:** *Evaluating Multilingual Robustness in Large Language Models for Scientific Literature Analysis* (K. Kousalanjan). Source in `../paper_overleaf/main.tex`, 9 references.
- **Scope as written (VERIFIED, read from the .tex):** a survey with no experiments (Sec. 3). It covers five robustness angles: capability, consistency, factuality, retrieval and evaluation. Benchmarks covered: PubMedQA, Indic-QA, CAP, BenchMAX, MIRACL, SHROOM-CAP. Approaches compared (Table 2): native multilingual, Translate-Test, multilingual RAG, post-generation verification. Gaps (Sec. 7): native science benchmarks, balanced per-language metrics, tokenization as a variable, multilingual retrieval grounding, calibrated auto-evaluation, reliability profiling.
- **Narrowed scope for Lab 02:** native vs Translate-Test processing for evidence-grounded *scientific* QA in Indic languages (Sec. 5.2 and 7.2–7.3 of the review).

## Decisions

| ID | Date | Decision | Reason | Evidence | Status |
|---|---|---|---|---|---|
| D01 | 2026-11-13 | Pathway **B (controlled comparative study)** | No training budget is needed; the review's Table 2 explicitly calls for "explicit comparison with native processing" | Review Sec. 5.2 (VERIFIED) | ACCEPTED by student (confirmed 2026-11-13) |
| D02 | 2026-11-13 | Primary dataset **PubMedQA PQA-L**, not Indic-QA | Indic-QA is general-domain (Wikipedia-type contexts), which breaks the "scientific" continuity; PubMedQA is expert-labelled research QA with an official test split | Jin et al. 2019 (VERIFIED, PDF Sec. 3, Table 5); repo `pubmedqa/pubmedqa` @1cbae8e, MIT (VERIFIED) | ACCEPTED by student (confirmed 2026-11-13) |
| D03 | 2026-11-13 | Use the **official 500-item test set** (`test_ground_truth.json`) for final evaluation; the other **500 items (CV portion) are the dev set** for prompt and format development only | Avoids test-set tuning; keeps results comparable to the published split | `scripts/00_data_sanity.py`: 500/500, disjoint, label match (VERIFIED by execution) | ACCEPTED by student (confirmed 2026-11-13) |
| D04 | 2026-11-13 | Languages: **Hindi, Bengali** (mid-resource) and **Odia, Punjabi** (very low-resource), plus English reference. Replaces the earlier Hindi/Tamil/Odia draft | Tiers are now taken directly from Singh et al. instead of assumed; two languages per tier make the tier contrast less dependent on one language | Singh et al. 2025 text: "Mid-resource languages like Hindi and Bengali…"; Odia and Punjabi listed as very low-resource (VERIFIED via arXiv HTML) | ACCEPTED by student (confirmed 2026-11-13) |
| D05 | 2026-11-13 | Translation with **IndicTrans2 distilled 200M** (en→indic, indic→en) | MIT license, covers all four languages, small enough for a T4 | HF model cards (VERIFIED: exist, MIT, gated, need IndicTransToolkit + `trust_remote_code`; card warns the `translation` pipeline breaks on transformers v5) | ACCEPTED by student (confirmed 2026-11-13) |
| D06 | 2026-11-13 | **RQ3 redesigned**: from "items with vs without numbers" to "number preservation through translation + token fertility" | 492 of 500 (98.4%) test contexts contain digits, so the original variable has no contrast | `results/sanity/data_sanity.json` (VERIFIED by execution) | ACCEPTED by student (confirmed 2026-11-13) |
| D07 | 2026-11-13 | **Primary metric macro-F1** (accuracy secondary) | Labels are imbalanced (55.2/33.8/11.0); Majority gets 55.2 accuracy but only 23.71 macro-F1 | Reproduced exactly by our script (VERIFIED) | ACCEPTED by student (confirmed 2026-11-13) |
| D08 | 2026-11-13 | **G2 gate:** the English zero-shot macro-F1 of each LLM must clearly exceed Majority (23.71). If it doesn't, switch to a larger model before any multilingual runs | A model at chance in English cannot show a native-vs-TT difference (floor effect) | Design rule (INFERRED necessity) | ACCEPTED by student (confirmed 2026-11-13) |
| D09 | 2026-11-13 | Model 2 = **Llama-3.2-3B-Instruct**; Gemma-2-2B-it rejected; Sarvam-1 is an optional exploratory 3rd model | Same size class as Qwen. Its official support covers Hindi only, giving a verifiable contrast. Gemma-2-2B is English-only. Sarvam-1 is a non-commercial base model | HF model cards (VERIFIED) | ACCEPTED by student (confirmed 2026-11-13) |
| D10 | 2026-11-13 | **Protocol v1 frozen**: `configs/protocol_v1.yaml`, SHA-256 `a9025bcf451a82cb1a3b32e58d1b4f87b936867b6f42b50134cf8ecc4c8e1bb9` | Fixes the primary metric, test split, conditions, prompt, scoring and statistics before any model output exists | No model outputs existed at freeze time (VERIFIED: `results/` holds only the data sanity output) | ACCEPTED by student (confirmed 2026-11-13) |
| D11 | 2026-11-13 | Instruction and answer words stay **English in all conditions**; only the evidence and question language varies | Translating "yes/no/maybe" would add an unverified label-translation confound | Design choice; listed as a limitation (fully native prompting not tested) | ACCEPTED by student (confirmed 2026-11-13) |
| D12 | 2026-11-13 | Regex sentence splitter accepted for MT segmentation | 4,787 test segments; 19 short ones, almost all genuine short sentences, one real mis-split ("Stock et al.") | Executed check (VERIFIED) | ACCEPTED by student (confirmed 2026-11-13) |

## Open items (UNKNOWN)

1. Hardware and time budget. Currently **assumed** to be Colab T4 plus a local M1 (8 GB), over 4 weeks.
2. ~~Second LLM~~: resolved by D09.
3. Whether re-running the official `split_dataset.py` (seed 0) reproduces the shipped test set. The check was blocked in the AI session; it needs a manual run (see `baseline_validation.md`).
4. Indic-QA code/data repo `github.com/ayushayush591/IndicQA-Benchmark`: the link is stated in the paper but has not been visited.

## Next actions

- Student confirms D09–D12 and the hardware budget.
- Student accepts the gated terms on HF for IndicTrans2 (both directions) and Llama-3.2-3B-Instruct.
- Phase III (Prompts 08–11): environment test on Colab, then modules in the build order of P07 §3, then the G2 English baseline.

## Protocol change log

| ID | Date | Change | Reason | Test results seen before change? | Conditions to rerun | Status |
|---|---|---|---|---|---|---|
| D13 | 2026-11-16 | **Protocol v1 → v2** (`configs/protocol_v2.yaml`, SHA-256 `669ea359fccb1d83f18827419376fe118970d283330faf991784c4992875a148`). Models: Qwen2.5-3B → **Qwen2.5-1.5B-Instruct**, Llama-3.2-3B → **Llama-3.2-1B-Instruct**. Hardware: Colab T4 → **local Apple M1 8 GB (MPS)**. Everything else is identical (24 changed diff lines, all in header, models, gate note and budget). | No CUDA GPU; 3B fp16 (6.2–6.4 GB) exceeds free memory (3.7 GB measured); network aborted the 3B download after ~11 h. Smaller set is 7.6 GB total. | **No.** No model predictions existed (`results/preds/` absent); only a 5-item dev smoke test with an unlisted 0.5B model | None (nothing had run). Claims will be limited to 1–1.5B models. | ACCEPTED by student (chose option 1, 2026-11-16) |
| D14 | 2026-11-16 | **Protocol v2 → v3** (`configs/protocol_v3.yaml`, SHA-256 `453902dd356e71e81142ad69ca1e755d340aea846e4239bb8cc618364b6d2989`). **Llama-3.2-1B removed**; the optional Sarvam-1 is removed too. **Qwen2.5-1.5B-Instruct is the only model.** Holm family is now 4 tests. Nothing else changed (22 diff lines: header, model list, Holm comment). | Local M1 is heavily swapping (5–6.7 GB of swap in use); translation alone measured ~6 s/sentence, so a second model would roughly double scoring time. Student decision: "leave the process with llama as it's taking time". | **Dev only**: the Qwen EN dev G2 run (63.00/45.10) had been seen. **No test-split outputs existed.** Llama had produced no outputs at all. | None. **Comparator design still satisfies the assignment:** 2 baselines (Majority; English-original upper reference) plus 2 compared pipelines (NATIVE vs TT). **Lost:** the cross-model robustness check, which becomes a stated limitation ("single 1.5B model"). | ACCEPTED by student (2026-11-16) |
| D15 | 2026-11-16 | **Protocol v3 → v4** (`configs/protocol_v4.yaml`, SHA-256 `c9871f6a3cfc887a34fdd7282a8140a8ee23c2393cf66462ef6ab1d53c438702`). (1) Languages **hi + or** only (bn, pa dropped). (2) Prompt-sensitivity templates P1/P2 dropped. (3) Translation **and** test scoring run on **Colab T4**, using transformers 4.51.3 for both. | Student: "cut wherever possible to make this task complete faster". Local MT measured 4.7 s/sentence (CPU greedy) to 10.2 s (CPU beam 5); MPS beam 5 used 8.4 GB and caused swapping (`results/logs`, AI log #18). hi + or keeps one language per resource tier, the fallback pre-registered in P04. | **Dev only** (Qwen EN dev G2). **No test outputs existed.** | None. **Lost:** bn/pa replication within tiers (each tier now rests on one language) and the prompt-sensitivity analysis. Both go in Limitations. Deeper analyses kept: error/number-preservation (RQ3) and token-fertility efficiency. | ACCEPTED by student (2026-11-16) |

## D16 — Exploratory analysis of Odia translation degeneration (added 2026-11-17, AFTER test results)
- **Observation:** In 506/5,285 Odia EN→X sentences, IndicTrans2 hit max_new_tokens without EOS (497: trailing repeated '.', 9: repeated fragments). 401/500 Odia items are affected; Hindi has 0 truncations.
- **Decision:** The primary pre-registered analysis is unchanged and uses the outputs as produced. An exploratory clean-subset re-estimate and a fertility check with the runs stripped are added in `scripts/06_exploratory_degeneration.py`, labelled "not pre-registered" in the paper.
- **Result:** Odia clean subset (n=99): Δ +13.02 [+2.50, +22.35], McNemar p=0.016. Affected subset (n=401): +12.47. Fertility changes by about 1%.
- **Status:** ACCEPTED by student (2026-11-17).
