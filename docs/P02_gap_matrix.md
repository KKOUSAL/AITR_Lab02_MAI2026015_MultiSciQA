# P02 — Evidence-Based Gap Matrix

Source review: `../../paper_overleaf/main.tex`. Section numbers are as compiled: 5 = Comparative Analysis, 6 = Challenges, 7 = Research Gap.
**ORIGINAL** = a limitation reported by the cited paper itself. **INFERENCE** = my synthesis in the review, or an AI suggestion.

| # | Gap | Passage in my review | Original vs inference | Experimental question | Evidence that would test it |
|---|---|---|---|---|---|
| G1 | Translate-Test vs native is untested on **scientific** QA | Sec. 5.2 / Table 2: "Translate-Test … explicit comparison with native processing"; Sec. 8: "Translate-Test can be a useful baseline however should be compared with native processing" | ORIGINAL (Singh et al. 2025): TT beats multilingual LLMs for low-resource languages, native is better for mid-resource Hindi/Marathi (VERIFIED). INFERENCE: the effect may differ on biomedical evidence with dense numbers and terminology | Does the TT advantage hold, shrink or reverse on PubMedQA-style evidence across resource tiers? | Per-language macro-F1, native vs TT, same model, items and prompt; paired test |
| G2 | Per-language reporting and cross-lingual consistency | Sec. 4.2 Eq. 1–2; Sec. 7.2: "Macro-averaging can mask issues within certain languages" | INFERENCE (review synthesis) | Does a model give the same answer to the same item across languages? | Agreement with the model's own English answer; Cohen's κ per language |
| G3 | Tokenization cost imbalance | Sec. 6.1, 7.3; Ahia et al. 2023 | ORIGINAL (Ahia et al.): token counts vary strongly across languages [details of their findings TO VERIFY in the paper]. INFERENCE: cost relates to accuracy on scientific text | Do tokens per item (fertility) and number loss explain native-mode errors? | Tokens/item per language and tokenizer; number-preservation rate; error rate by fertility bin |
| G4 | LLM-as-judge calibration and fluency–factuality disentanglement | Sec. 6.4–6.5, 7.5; CAP, SHROOM-CAP | ORIGINAL (CAP/SHROOM-CAP): fluency and factuality are separable [TO VERIFY in the papers] | Does a multilingual judge mistake fluent answers for factual ones? | Human factuality labels plus judge scores per language |
| G5 | Multilingual retrieval for scientific evidence | Sec. 6.3, 7.4; MIRACL | ORIGINAL (MIRACL): general-domain Wikipedia retrieval in 18 languages [TO VERIFY]. INFERENCE: no scientific counterpart exists | Does retrieval quality drop for Indic-language scientific queries? | Recall@k / nDCG over a multilingual scientific corpus |

## Ranking (significance × resources × feasibility)

| Rank | Gap | Significance | Resources available | Feasibility (Colab T4, 4 weeks) |
|---|---|---|---|---|
| 1 | **G1** | High: it is the review's main open comparison | Data VERIFIED (PubMedQA, MIT); MT model VERIFIED (IndicTrans2, MIT) | High: zero-shot inference only |
| 2 | **G2** | Medium–high | Free by-product of the G1 runs | High |
| 3 | **G3** | Medium | Tokenizers are free; number check is regex | High |
| – | G4 | High | Needs native-speaker factuality annotation | Low |
| – | G5 | High | No scientific multilingual retrieval corpus verified | Low |

**Selected:** G1 as the main question, with G2 and G3 as supporting and depth analyses. Together they make one study (D01).

## Review claims needing re-verification before reuse in the new paper

- CAP and SHROOM-CAP "9 languages"; BenchMAX "16 target languages"; MIRACL "18 languages". None of these is used in this study's argument yet. If any is cited, verify it in the original paper.
- Ahia et al.: the exact finding cited in Sec. 7.3.
- Novelty: no separate literature search had been done before this matrix. See `P04_feasibility_novelty.md`.
