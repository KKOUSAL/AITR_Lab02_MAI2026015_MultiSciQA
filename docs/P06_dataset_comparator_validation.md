# P06 — Dataset and Comparator Validation Sheet

## Primary dataset: PubMedQA PQA-L

| Item | Value | Status |
|---|---|---|
| Official source | github.com/pubmedqa/pubmedqa, commit `1cbae8e` (2023-04-18) | VERIFIED (cloned) |
| Licence | MIT | VERIFIED (repo LICENSE) |
| Files | `data/ori_pqal.json` (1,000 items keyed by PMID); `data/test_ground_truth.json` (500 PMID → label) | VERIFIED |
| Item fields | `QUESTION`, `CONTEXTS` (list), `LABELS` (section names), `MESHES`, `YEAR`, `reasoning_required_pred`, `reasoning_free_pred`, `final_decision`, `LONG_ANSWER` | VERIFIED (inspected) |
| Benchmark protocol | Reasoning-required setting: input = question + context; output = yes/no/maybe; metrics are accuracy and macro-F1 (Jin et al., Sec. 5 and Table 5) | VERIFIED |
| Test-set size | 4,787 context sentences (median 19 words, p99 55, max 97) + 500 questions; 101,136 context words | VERIFIED (executed) |

### Leakage risks and controls

| Risk | Control |
|---|---|
| **Answer fields in the item:** `LONG_ANSWER` (the abstract's conclusion), `reasoning_required_pred` and `reasoning_free_pred` (annotator answers), `final_decision` | The input builder reads **only** `QUESTION` and `CONTEXTS`. A unit test asserts that none of the other fields appears in any prompt. |
| Test-set tuning | The prompt template, label set and scoring rule are frozen in `configs/protocol_v1.yaml` *before* any test run. Dev (500) is used only for pipeline debugging and the G2 English check. |
| Document-level overlap | There is one item per PMID and 0 duplicate questions (VERIFIED). Dev and test are disjoint (VERIFIED). |
| Pretraining contamination | PubMedQA is public (2019), so the LLMs may have seen it. It cannot be removed. It affects all conditions equally, so the **paired differences** (the primary quantity) are less affected than absolute scores. Reported as a threat. |
| Section headers (`LABELS`) in English inside native-language input | Excluded from the input. Context paragraphs are joined with a blank line. |

## Translation system

| Item | Value | Status |
|---|---|---|
| EN→X | `ai4bharat/indictrans2-en-indic-dist-200M` | VERIFIED (card) |
| X→EN (TT) | `ai4bharat/indictrans2-indic-en-dist-200M` | VERIFIED (card) |
| Language codes | `hin_Deva`, `ben_Beng`, `ory_Orya`, `pan_Guru`, `eng_Latn` | VERIFIED (IndicTrans2 README) |
| Licence | MIT (code and checkpoints) | VERIFIED |
| Access | Gated: accept the terms on HF; needs `IndicTransToolkit` and `trust_remote_code=True` | VERIFIED (card) |
| Pitfall | The card warns the `translation` pipeline is unsupported on transformers v5, so pin `transformers<5` | VERIFIED (card) |
| Pitfall | It is a sentence-level model; long inputs must be sentence-split and length-checked (truncation is counted) | INFERRED, checked in Phase III |

## LLM comparators

| Model | Params | Licence / gating | Stated languages | Role | Status |
|---|---|---|---|---|---|
| `Qwen/Qwen2.5-3B-Instruct` | 3.09B | `qwen-research`, not gated | "over 29 languages" (which Indic languages are included is not stated) | Model 1 | VERIFIED (card) |
| `meta-llama/Llama-3.2-3B-Instruct` | 3.21B | Llama 3.2 Community License, gated | Officially: en, de, fr, it, pt, **hi**, es, th. Bengali, Odia and Punjabi are not supported | **Model 2** (D09) | VERIFIED (card) |
| `google/gemma-2-2b-it` | ~2.6B | Gemma terms, gated | English | Rejected: English-only | VERIFIED (card) |
| `sarvamai/sarvam-1` | ~2B | Sarvam non-commercial; base model, not instruction-tuned | 10 Indic languages including all four targets | Optional exploratory 3rd model (log-likelihood scoring works with base models) | VERIFIED (card) |

**Why Llama-3.2-3B as model 2:** it is the same size class as Qwen, so the comparison is fair. Its official support list contains Hindi but not Bengali, Odia or Punjabi, which adds a second, *verifiable* support contrast inside one model.

**Simplest credible baseline:** Majority (reproduced exactly), plus English zero-shot Qwen2.5-3B on the same items and scoring rule.

## Independent-verification checklist (before any test run)

- [ ] HF account has accepted the gated terms for both IndicTrans2 models and Llama-3.2.
- [ ] `IndicTransToolkit` installs; 5 dev sentences translate EN→hi→EN and print readably.
- [ ] Each target script renders in the output (no `<unk>`-only strings).
- [ ] The prompt-leakage unit test passes.
- [ ] Label tokenization is logged for each model (how many tokens " yes", " no" and " maybe" take).
- [ ] English dev run: macro-F1 > 23.71 (G2 gate, D08).
