# P04 — Feasibility and Novelty Verification

## Search strings used (2026-11-13, one web search engine; not exhaustive)

- `multilingual PubMedQA translated Hindi OR Indic OR low-resource biomedical question answering translate-test LLM`
- `"Indic QA Benchmark" dataset huggingface`

Still to run, in Google Scholar and Semantic Scholar:
- `"PubMedQA" (Hindi OR Bengali OR Odia OR Punjabi OR Indic)`
- `"translate-test" biomedical OR medical question answering`
- `multilingual medical QA benchmark Indian languages`
- `machine translation number preservation biomedical`

## Neighbouring work

| Published work | VERIFIED contribution (source) | Limitation relative to my question | Proposed difference | Evidence still missing |
|---|---|---|---|---|
| Singh et al. 2025, Indic QA Benchmark (Findings NAACL) | 11 Indic languages, context-grounded QA; TT better for Punjabi/Gujarati/Odia/Assamese, native better for Hindi/Marathi (arXiv HTML) | General-domain contexts, not scientific evidence | Same comparison on biomedical research abstracts | Exact metric values per language (tables not parsed) |
| Jin et al. 2019, PubMedQA (EMNLP) | 1k expert-labelled research QA; Majority 55.20/23.71; Human 78.00/72.19 (PDF, Table 5) | English only | Translated Indic conditions | — |
| Yeginbergen, Oronoz, Agerri 2026, Effects of Cross-lingual Evidence in Multilingual Medical QA (arXiv 2604.20531) | Medical QA in En/Es/Fr/It + Basque/Kazakh; for low-resource languages, combining English and target-language retrieval works best (arXiv abstract) | No Indic languages; studies retrieval sources, not TT vs native | Indic languages; processing pipeline instead of evidence source | Whether they test translate-test (not in abstract) |
| Agrawal, Fazili, Jyothi 2024, Translation Errors Significantly Impact Low-Resource Languages… (EACL) | Translation inconsistencies in XNLI disproportionately affect low-resource languages; Hindi/Urdu re-annotated (arXiv abstract) | NLI, not scientific QA | Measures number loss in scientific MT | — (used as a threat-to-validity citation) |
| Qiu et al. 2024, MMedBench (Nature Communications) | UNKNOWN: page blocked by login redirect | — | — | Languages covered; whether any are Indic |
| BanglaMedQA | UNKNOWN: seen only in a search snippet | — | — | Everything |

**Novelty status (INFERRED, qualified):** one search found no published Indic translation of PubMedQA and no TT-vs-native study on Indic scientific QA. The contribution should be phrased as *"a controlled test of whether a published general-domain finding transfers to scientific QA"*, not as a new method. Do not claim "first" without the remaining Scholar searches.

## Resource access

| Resource | Status | Licence | Notes |
|---|---|---|---|
| PubMedQA PQA-L + test ground truth | VERIFIED (downloaded, sanity-checked) | MIT | 1,000 items; split 500/500 |
| IndicTrans2 en-indic dist-200M | VERIFIED (card) | MIT | Gated: accept the terms with an HF account |
| IndicTrans2 indic-en dist-200M | VERIFIED (card) | MIT | Gated; needs IndicTransToolkit; `transformers<5` advised |
| Qwen2.5-3B-Instruct | VERIFIED (card) | `qwen-research` (research use) | 3.09B; fits a T4 in fp16 (INFERRED: about 6.2 GB weights) |
| Second LLM | UNKNOWN | — | Check Llama-3.2-3B-Instruct, Gemma-2-2B-it, or an Indic-focused model |

## Compute and time estimate (INFERRED; assumes Colab T4 and 4 weeks)

- Translation: test contexts total 101,136 English words (VERIFIED by `00_data_sanity.py`). EN→X for 4 languages, then X→EN for TT, is about 0.8M words of MT. Sentence-batched IndicTrans2-200M on a T4 should take a few hours. Cache all translations to disk once.
- LLM scoring: score the three label options by log-likelihood (no free generation). 500 items × (1 EN + 4 native + 4 TT) × 2 models = 9,000 forward passes. Under 2 GPU-hours.
- Bottleneck: Odia/Punjabi token fertility may lengthen inputs several-fold. This is measured, not guessed, in RQ3.

## Go / no-go

**GO (conditional).** Data and translation models are legally accessible, the baseline protocol is reproduced exactly (Majority 55.20/23.71), and compute is modest.
Conditions: (1) at G2, English zero-shot macro-F1 must clearly exceed Majority (D08); (2) a second LLM is verified.

**Fallbacks**

| If… | Then… |
|---|---|
| IndicTrans2 access is denied or broken | NLLB-200-distilled-600M (check its licence: it is CC-BY-NC) |
| The 3B model is at chance in English | Qwen2.5-7B-Instruct in 4-bit on the T4 |
| There is no time for 4 languages | Keep Hindi (mid) + Odia (very low), the minimum tier contrast |
