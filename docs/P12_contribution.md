# P12 — Contribution Pathway and Comparison Plan (protocol v4)

**Validated baseline:** Qwen2.5-1.5B-Instruct, zero-shot, English, dev split: accuracy 63.00, macro-F1 45.10, vs Majority 55.20/23.71 (`baseline_validation.md` B1). G2 gate passed.

| Pathway | Scientific question | Code changes | Compute | Risk | Verdict |
|---|---|---|---|---|---|
| A. Reproduce Singh et al. under a new condition | Does the TT-vs-native finding replicate on Indic-QA, then transfer to science? | New dataset loader; their models (7B+) | High; impossible locally | Their models don't fit on available hardware | Rejected |
| **B. Controlled comparison** | On scientific QA, does TT beat native processing for a very low-resource language (Odia) but not a mid-resource one (Hindi)? | None beyond what's built | ~30–40 min on Colab T4 | Single 1.5B model; machine-translated "native" text | **Chosen** |
| C. Targeted modification | Does a number/terminology-preserving glossary improve TT? | Glossary + constrained MT | Medium | Only meaningful if the RQ3 pilot shows number loss; the pilot shows 34/34 preserved | Deferred; motivation not supported by pilot |

**This is not a novelty claim.** It is a controlled test of whether a published general-domain finding (Singh et al. 2025) transfers to evidence-based biomedical QA.

## Fair test plan (frozen in `configs/protocol_v4.yaml`)

- Same 500 official test items, same prompt (P0), same label log-likelihood scoring, same cached translations, for all 5 conditions: EN, NATIVE-hi, TT-hi, NATIVE-or, TT-or.
- Primary contrast: Δ macro-F1 (TT − NATIVE) per language, with a paired bootstrap 95% CI (10k) and exact McNemar, Holm over 2 tests.
- Deeper analyses: (1) error analysis (confusion matrices, EN→X answer flips, yes-bias); (2) efficiency (token fertility per language); (3) number preservation through MT.
