# P16 — Critical Peer Review of `paper/main.tex`

**Reviewer:** Claude Code (AI), acting as a sceptical external reviewer. **Date:** 2026-11-17.
**Version reviewed:** `paper/main.tex` as of 07:55 on 2026-11-17 (7 pages, before this review's fixes).
**Method:** I read the whole paper, then checked every numeric claim against `results/tables/test/summary.json`, `results/exploratory/`, `results/pilot/` and `baseline_validation.md` with a script. I re-ran the detectors behind the claims I doubted and ran one new analysis (the interaction test, M2). Issues are rated by whether they change a conclusion.

## 1. Summary of the submission

The paper asks whether Translate-Test (TT) beats native processing for biomedical yes/no/maybe QA in Hindi (mid-resource) and Odia (very low-resource). It uses the PubMedQA test set machine-translated with IndicTrans2 and a zero-shot Qwen2.5-1.5B model with a pre-registered protocol. It reports TT − NATIVE = +12.88 macro-F1 (Hindi) and +12.42 (Odia), both significant. It concludes that the general-domain finding (native is competitive for mid-resource languages) does not transfer.

## 2. Overall assessment

**Recommendation: accept with major revisions** (by workshop or student-paper standards).

**Strengths**
- S1. The pipeline is validated against the published Majority baseline (exact match). This is rare and convincing.
- S2. The paired design, the pre-registered decision rules and two agreeing criteria (bootstrap CI and Holm-corrected McNemar) make the headline effects robust. Both are large (CI lower bounds above +7).
- S3. Negative and inconvenient results are reported: H2 is contradicted, both NATIVE conditions score below Majority in accuracy, and the Odia translator degenerated.
- S4. Provenance is unusually complete: hashed protocol versions, a decision log, an AI log, and import hashes for results.
- S5. Per-class analysis turns a single number into a mechanism-level observation (loss of "no").

**Main weaknesses.** Each conclusion says slightly more than the evidence supports (M1–M4). One factual statement is wrong (M3). The TT condition has a construct problem that the paper doesn't discuss (M1).

## 3. Major issues

**M1. TT is a round trip, so it is close to EN by construction.**
TT-X = EN → X → EN. Any information the model needs survives as long as the round trip roughly reconstructs the English source. Round-trip chrF is 80.6 (Hindi) and 69.2 (Odia), so TT is essentially noisy English. The comparison therefore measures "Indic-script text vs slightly corrupted English" rather than "reading a paper written in X vs translating it". In a real setting the X text is authored natively, and TT would involve only one translation step from human-written X. The paper lists machine-translated input as a limitation but not this asymmetry. It also concludes that "TT is the stronger and cheaper default", which is a deployment claim the design can't support.
*Requested:* state the asymmetry in Method or Limitations, and limit the conclusion to this design and model.

**M2. "TT helps both tiers by the same amount" was never tested.**
The H2 rejection is valid on its own (TT > NATIVE is significant for Hindi). But the Discussion and Conclusion claim *equality* of the two gaps, which is a claim about the interaction. I ran a paired bootstrap (same 500 PMIDs, 10,000 resamples, seed 2026): gap(hi) − gap(or) = **+0.46, 95% CI [−5.01, +6.13]**. There is no detectable difference, but differences of up to about 6 points can't be ruled out.
*Requested:* report this CI and replace "the same amount" with "no detectable difference".

**M3. Factual error: the Hindi degeneration claim.**
Section 5.5 says the 18 flagged Hindi items come "all from repeated patterns already in the source text". I checked all 18 against the English source: **none** of the source texts contain the pattern. Fourteen contain IndicTrans2 "....." runs that ended with EOS before the token limit, so they were not counted as truncations. Four are detector false positives on abbreviations (e.g., "ई. ए. 1"). Hindi degeneration therefore exists, at a much lower rate (14 items vs 398 for Odia). "Hindi: 0" is only true for *truncation*.
*Requested:* correct the sentence and distinguish truncation from degeneration.

**M4. Two causal-sounding claims go beyond the data.**
(a) "The failure of NATIVE therefore lies mainly in the model's comprehension of Indic-script input, not in the translation." This is inconsistent with the paper's own alternative (iii): machine-translated Indic text may be unnatural, which is a translation-side cause.
(b) "So on this task lost numbers rarely change the yes/no/maybe answer." No item-level analysis links number loss to answer changes. This is inferred from aggregate scores.
*Requested:* rephrase (a) as "consistent with" and drop or qualify (b) as untested. The pre-registered RQ3 wording ("relate to failures") also promises an analysis that was not done; say so.

## 4. Minor issues

- m1. **Two different fertility definitions.** The pilot gives 4.5× (content tokens only), but Table D and the text give 3.6× for Hindi. The evaluator divides *full prompt* lengths (`n_input_tokens`, which include the English instruction and chat template), and this lowers the ratio. Define this, or a reader will see a contradiction.
- m2. **Pre-registration wording.** "Frozen before any model output existed" is true only of v1. v2–v4 came after dev outputs (and a smoke test) but before any test output. The next sentence gets this right; make the first one precise too.
- m3. **Abstract is about 330 words**, with too many numbers. Trim it to the question, the design, two headline results, the H2 contradiction and one caveat.
- m4. **Figure 3 (left):** the legend sits in the middle of the plot area. Move it or drop it, since there is only one model.
- m5. **AI-use paragraph** lists AI errors up to #17 only. Add the non-blocking Colab login (#19) and the unverified claim about model size (#21).
- m6. **Overfull line** in the Metrics paragraph (26 pt). This is cosmetic.
- m7. "Correct-looking translation followed by …" in Section 5.5: no Odia reader checked these outputs. Say "a translation of plausible length", or mark it as unchecked.
- m8. Singh et al. are described as finding that native input "scores better" for Hindi and Marathi. Their exact numbers aren't quoted, so readers can't judge how strong the prior was. Consider one sentence giving their numbers (from P02/P03).

## 5. Things I checked that are correct

- Every table value matches `summary.json` after rounding. Derived values are correct: 44.59 − 42.92 = 1.67; 44.59 − 41.28 = 3.31; 506/5285 = 9.6%; Odia translation time (1259 + 1455 s) ≈ 45 min, Hindi (488 + 482 s) ≈ 16 min.
- Discordant counts (136/33, 106/42), κ values and flip rates match Tables B and C.
- The exploratory clean-subset numbers match `results/exploratory/degeneration_subset.json`.
- The Odia degeneration count holds up under the stricter rule: 398 items with character runs and 3 flagged only by the fragment rule (consistent with the 9 fragment-type truncations).
- No `[PENDING]` placeholders remain, and the paper compiles.

## 6. Issues that cannot be fixed in this submission (stated as limitations)

- A single 1.5B model, and one language per tier.
- No native-authored Indic scientific text.
- Uncalibrated scoring with a yes-bias.
- No human check of translations, especially Odia.

These are already in Section 7. M1 adds the round-trip asymmetry.

## 7. Author response (fixes applied 2026-11-17)

| Issue | Action |
|---|---|
| M1 | Added the round-trip asymmetry to Limitations; Conclusion now limited to "this model and design" |
| M2 | Interaction CI reported in RQ1 and the abstract; "the same amount" → "no detectable difference (CI ±~6)" |
| M3 | Section 5.5 corrected: Hindi 14 items with dot runs (no truncations) + 4 detector false positives |
| M4 | (a) rephrased as "consistent with"; (b) replaced with an explicit statement that the item-level link was not tested |
| m1 | Fertility defined as full-prompt token ratio; pilot difference explained |
| m2 | Pre-registration sentence made precise |
| m3 | Abstract shortened |
| m4 | Legend removed from the forest plot |
| m5 | AI-use paragraph updated |
| m6 | Left as is (cosmetic) |
| m7 | "plausible-length translation, not checked by an Odia reader" |
| m8 | Not done; the numbers are in `docs/P02_gap_matrix.md` |
