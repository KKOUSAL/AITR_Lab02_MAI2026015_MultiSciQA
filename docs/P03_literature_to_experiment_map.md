# P03 — Literature-to-Experiment Map

**Bridge:** Singh et al. 2025 (TT vs native, general Indic QA) + Jin et al. 2019 (PubMedQA, English scientific QA) → **native vs Translate-Test zero-shot LLM** → **executable baseline: English zero-shot on the PubMedQA official test set** → **planned test: the same model on EN→X translated items, run natively vs back-translated (TT), X ∈ {hi, bn, or, pa}**.

## Methods from the review that can be implemented

| Method | Original paper | Algorithm | Dataset | Code / model access | Metric | Known limitation | Compute |
|---|---|---|---|---|---|---|---|
| Majority and published PubMedQA baselines | Jin et al. 2019 | Predict "yes"; BioBERT multi-phase (reported) | PQA-L, official test set of 500 | VERIFIED: repo `pubmedqa/pubmedqa` @1cbae8e, MIT; `evaluation.py` included | Accuracy, macro-F1. Reported: Majority 55.20/23.71, Human 78.00/72.19, BioBERT best 68.1 acc (Table 5, VERIFIED) | English only | CPU |
| Native multilingual zero-shot LLM | Review Table 2; Singh et al. 2025 evaluate this setting | Prompt the LLM with question and context in language X | PQA-L translated to X | Qwen2.5-3B-Instruct: VERIFIED exists, `qwen-research` license, 3.09B params. Second model UNKNOWN | macro-F1 per language | Uneven capability across languages; translated inputs are not native-authored | T4, about 1–2 h per model for all languages (INFERRED) |
| Translate-Test | Singh et al. 2025 (VERIFIED: compared and reported); review Table 2 | X→EN with an MT system, then the English pipeline | Same as above | IndicTrans2 en-indic and indic-en dist-200M: VERIFIED, MIT, gated. Singh et al. code link stated but not visited (UNKNOWN) | Same as above | Translation errors compound; Agrawal et al. 2024 (EACL) show translation errors hit low-resource languages hardest (VERIFIED abstract) | T4, translating about 100k words × 4 languages × 2 directions (INFERRED: a few GPU-hours) |

## Three candidate study designs

| | (A) Reproduction + extension | **(B) Controlled comparison**, recommended | (C) Targeted modification |
|---|---|---|---|
| Smallest working baseline | Reproduce a Singh et al. TT-vs-native result for one language, then extend it to PubMedQA | English zero-shot LLM on the PubMedQA test set | The same baseline plus one change (for example, a glossary that preserves terms and numbers during translation) |
| Testable question | Does the published effect replicate, and does it transfer to science? | Native vs TT per resource tier on scientific QA | Does preserving numbers and terms improve TT? |
| Resource burden | High: needs their data, models and protocol | Low–medium | Medium: needs (B) first |
| Evidence required | Matching their numbers within tolerance | Paired per-language differences, CIs, error analysis | Ablation with vs without the change |
| Risk | Their models (e.g., Airavata, Aya) may not fit on a T4 | Floor effect if the small LLM is weak in English | Depends on (B) showing number loss |

**Recommendation:** (B). (C) is an optional extension only if the RQ3 results show translation loses numbers, and only if time remains.

## Must personally verify before coding

1. IndicTrans2 language codes for Odia (`ory_Orya`) and Punjabi (`pan_Guru`) in the model's supported list.
2. The licence and gating of the second LLM.
3. That Qwen2.5-3B tokenizes Odia and Punjabi scripts without heavy `<unk>` or byte fallback. This is measured anyway in RQ3.
4. The Ahia et al. finding as cited.
