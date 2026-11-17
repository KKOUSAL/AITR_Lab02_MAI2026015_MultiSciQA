# 5-minute demo script

Setup before the demo:
- Open a terminal in the repo.
- Open `paper/main.pdf` (page 4: Table 2) and `results/figures/test/fig1_forest_tt_vs_native.png`.
- Run `python3 scripts/demo_one_item.py` once beforehand, so the model is cached and loads in about 12 s.

| Time | Show | Say (key points) |
|---|---|---|
| 0:00–0:40 | Paper title + abstract | Question: Singh et al. found that translate-test (TT) helps very low-resource Indic languages but not mid-resource ones. Does that hold for *scientific* evidence? PubMedQA, Hindi (mid) vs Odia (very low), Qwen2.5-1.5B, zero-shot. |
| 0:40–1:20 | Fig. 1 pipeline; `configs/protocol_v4.yaml` + `.sha256` | NATIVE and TT start from the same translation. The protocol is frozen and hashed; code refuses to run if it changes. Versions 1→4 were all before any test output (`research_decisions.md`). |
| 1:20–2:00 | **Live:** `python3 scripts/00_data_sanity.py` then `python3 -m pytest -q` | The pipeline reproduces the published Majority baseline exactly (55.20/23.71); 25 tests include the answer-leakage check. |
| 2:00–3:00 | **Live:** `python3 scripts/demo_one_item.py` | One real test item, gold "no": English → "no", native Hindi → "maybe", translate-test → "no". Same model, same evidence, only the language differs. The live scores match the stored Colab run. Note the 4× token count in Hindi. |
| 3:00–4:00 | Table 2 + forest plot | TT − NATIVE = +12.88 (Hindi) and +12.42 (Odia), both significant. H1 supported, **H2 contradicted**. The model almost stops answering "no" under native input (7/169 Hindi). The gap difference is +0.46 [−5.0, +6.1], so no detectable tier effect. |
| 4:00–4:40 | Paper §5.5 + Limitations | Honest caveats: Odia translator degeneration (still +13.0 on clean items); TT is a round trip, so it is close to English by construction; one 1.5B model; machine-translated "native" text. |
| 4:40–5:00 | `ai_assistance_log.md`, `docs/P16_peer_review.md` | AI use: Claude Code wrote most of the code; every result is traced to a file. The log records AI errors that were caught, including one found by the AI's own peer review. |

Likely viva questions:
1. *Why label log-likelihood instead of generation?* It is deterministic, has no parsing failures, and all three labels are single tokens (`src/score.py`).
2. *Why is TT so close to EN?* It is a round trip (chrF 80.6 / 69.2). With native-authored text, the advantage may be smaller (Limitation 3).
3. *How do you know the answer did not leak?* Only `QUESTION` and `CONTEXTS` reach the prompt; `assert_no_leak` checks `LONG_ANSWER`, and a unit test runs it on all 1,000 items.
4. *Why both bootstrap and McNemar?* The bootstrap gives a CI on macro-F1 (the primary metric); McNemar tests per-item correctness. An effect is claimed only if both agree; Holm corrects for the two languages.
5. *What would you do next?* Calibration, a second and larger model, and a native-speaker check of 30 Hindi translations.
