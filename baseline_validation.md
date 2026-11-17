# Baseline Validation Report

Status labels: **VERIFIED** · **UNCERTAIN** · **NEEDS CORRECTION**

## B0 — Data and Majority baseline (`scripts/00_data_sanity.py`, run 2026-11-13, Python 3.13.5, macOS arm64)

| Check | Expected (source) | Observed | Status |
|---|---|---|---|
| PQA-L size | 1,000 (Jin et al. 2019, Table 1) | 1,000 | VERIFIED |
| Label distribution | yes 55.2 / no 33.8 / maybe 11.0 % (Table 1) | 55.2 / 33.8 / 11.0 | VERIFIED |
| Test/CV split | 500 / 500 (Sec. 3) | 500 / 500, disjoint; test labels match PQA-L | VERIFIED |
| Majority on test | 55.20 acc / 23.71 macro-F1 (Table 5) | 55.20 / 23.71 | VERIFIED |
| Duplicate questions | none expected | 0 | VERIFIED |
| Official `split_dataset.py` (seed 0) regenerates the shipped test set | identical PMID set | not run (blocked in the AI session) | UNCERTAIN |

**Manual check to run (student):**
```bash
mkdir -p /tmp/sc/data /tmp/sc/preprocess
cp data/raw/pubmedqa_repo/data/ori_pqal.json /tmp/sc/data/
cp data/raw/pubmedqa_repo/preprocess/split_dataset.py /tmp/sc/preprocess/
(cd /tmp/sc/preprocess && python3 split_dataset.py pqal)
python3 -c "import json;a=set(json.load(open('/tmp/sc/data/test_set.json')));b=set(json.load(open('data/raw/pubmedqa_repo/data/test_ground_truth.json')));print(a==b,len(a&b))"
```
Whatever the result, the study uses the shipped `test_ground_truth.json`, which is the official one. A mismatch would only show that Python's random generator has changed since 2019; it is not a defect in the data.

## B1 — English zero-shot LLM (G2)

Audit of the implementation against the protocol and the original methodology (Prompt 10):

| Item | Original (Jin et al. 2019) | This study | Acceptable? |
|---|---|---|---|
| Setting | Reasoning-required: question + context | Same; only `QUESTION` + `CONTEXTS` (leakage test passes on all 1,000 items) | VERIFIED (unit test) |
| Test split | Official 500 | Same IDs as `test_ground_truth.json` (unit test) | VERIFIED |
| Metric | Accuracy, macro-F1 | Same; the implementation reproduces Majority 55.20/23.71 exactly (unit test) | VERIFIED |
| Model / training | Fine-tuned BioBERT | Zero-shot 3B LLM, label log-likelihood | Deliberate deviation: our baseline is a *zero-shot LLM*, so numbers are **not** expected to match BioBERT's 68.1; Majority and Human bracket the plausible range |
| Section headers | (not specified for this use) | Excluded | Deliberate deviation (D11/P06) |

Results (dev split, protocol v2, local M1 / MPS; source `results/preds/<model>/dev_EN_en_P0.{csv,meta.json}`, log `results/logs/g2_*`):

| Model | Accuracy | Macro-F1 | Pred. distribution (yes/no/maybe) | G2 gate (> 23.71) |
|---|---|---|---|---|
| Qwen2.5-1.5B-Instruct (run 2026-11-16, 720 s) | 63.00 | 45.10 | 398 / 84 / 18 | **PASS** |
| Llama-3.2-1B-Instruct | not run: removed from the protocol in v3 (D14) | | | |
| **Qwen2.5-1.5B-Instruct, TEST split** (Colab T4, protocol v4, 44 s) | **63.60** | **44.59** | 398 / 84 / 18 | PASS (above Majority 55.20/23.71 on the same split) |

**Qwen2.5-1.5B dev details (VERIFIED by execution).** Per-class F1: yes 74.18, no 47.43, maybe 13.70. Confusion (rows = gold): yes→{yes 250, no 18, maybe 8}; no→{yes 104, no 60, maybe 5}; maybe→{yes 44, no 6, maybe 5}. Median input 386.5 tokens. Labels are single tokens (`Ġyes`, `Ġno`, `Ġmaybe`), so there is no multi-token scoring bias.

**Interpretation (limited to what was measured).** The result is above Majority on both metrics and below published fine-tuned BioBERT (68.1 acc, test) and single-human performance (78.00/72.19, test). The splits differ (dev vs test), so this is a plausibility check, not a replication. There is a strong **"yes" bias**: 104 of 169 gold-"no" items were predicted "yes", and "maybe" is rarely predicted. This is reported as baseline behaviour, not corrected, because the protocol is frozen (no calibration step).

**Failed attempt (kept for provenance).** The first run, with `HF_HUB_OFFLINE=1`, crashed before scoring: transformers 4.57.3 `_patch_mistral_regex` calls the Hub API while loading the tokenizer. Log: `results/logs/g2_qwen15_dev_EN.failed_offline.log`. It was rerun online with no code change.


**Test EN (VERIFIED, recomputed locally from the imported CSV by `03_evaluate.py`).** Per-class F1: yes 75.37, no 47.43, maybe 10.96. Confusion: yes→{254, 15, 7}, no→{102, 60, 7}, maybe→{42, 9, 4}. Dev → test difference: +0.60 acc, −0.51 macro-F1, consistent with the dev estimate. The same yes-bias appears on test.
