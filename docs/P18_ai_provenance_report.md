# P18 — AI Use and Research-Integrity Report

**Tool:** Claude Code (model `claude-opus-5-5`), one terminal session, 2026-11-13 to 2026-11-17, with web search and fetch for source checks.
**Primary record:** `ai_assistance_log.md` (22 rows), `research_decisions.md` (D01–D16), and the logs in `results/logs/` and `results/env/`.

## 1. What the AI did

| Activity | AI role | Verification method |
|---|---|---|
| Reading the brief and the G0 review | Summarised requirements; mapped review gaps to experiments | Student read and confirmed decisions D01–D08 |
| Literature and source checks | Fetched primary pages (ACL Anthology, arXiv, HF cards, GitHub) | Values quoted from primary pages; PubMedQA Table 5 read from the PDF text |
| Protocol design | Drafted the RQs, hypotheses, metrics, statistics and frozen YAML | YAML parsed, hashed and enforced by code; student confirmed each version |
| Code | Wrote all `src/`, `scripts/`, `tests/` | 25 unit tests; reproduction of the published Majority baseline; executed runs with logs |
| Debugging | Diagnosed 6 failures from tracebacks and logs | Each fix was re-executed; failed logs kept |
| Analysis and writing | Error analysis, pilot metrics, paper draft, README | Every number traced to a file in `results/` |

## 2. Real AI limitations, errors and corrections (from the log)

1. **Unsupported claim** (log #4): the AI labelled Tamil "mid-resource" without a source. Checking Singh et al. led to Hindi/Bengali (mid) and Odia/Punjabi (very low) instead.
2. **Design error caught by execution** (#3): RQ3 originally compared abstracts with vs without numbers, but 98.4% of test abstracts contain digits, so the variable had no contrast.
3. **Syntax error** (#9): the first frozen YAML was invalid. Found by `yaml.safe_load` before hashing.
4. **Bug in AI code** (#15): the evaluator crashed on paths outside the repo. Caught by an AI-written test.
5. **False success** (#16): the download script trusted `hf download`'s exit code and logged "OK" for models that had not downloaded after a network drop. It was **noticed because the cache sizes did not match the expected sizes**; a second bug (a reserved zsh variable) followed.
6. **Silent change to an experimental setting** (#17): a `sed` patch commented out `num_beams`, which would have changed the protocol's beam size without any error. It was caught on review before any output was used.
7. **Wrong environment advice** (#13, #14): `! hf auth login` cannot read a hidden token, and `HF_HUB_OFFLINE=1` crashes transformers 4.57 tokenizer loading.
8. **Non-blocking login in a notebook** (#19): the AI's Colab notebook let translation start before authentication; the first full run produced only EN. The scoring cells' filtered output also hid the failures.
9. **Unverified comparison** (#21): the AI's draft claimed that Singh et al.'s models were larger; it was softened because it had not been checked.
10. **Factual error in the AI's own draft** (#22): the paper said the Hindi degenerate items came from the source text. The AI's own peer review re-checked this and found it false.
11. **Wrong citation ID**: a guessed ACL Anthology ID for Agrawal et al. pointed to a different paper. Replaced with the verified arXiv record.

## 3. Decisions that depended on human judgement

- Accepting the study design (D01–D12). These were AI proposals; the student's role was review and acceptance.
- **Hardware and scope trade-offs, made by the student:** smaller models (D13), dropping Llama (D14), using Colab for translation, and "cut wherever possible" (D15).
- Accepting gated licences and logging in to Hugging Face (performed by the student).
- **Still required from the student:** reviewing and accepting the interpretation of the test results (P14 Part B, D16), checking Hindi translation quality as a reader of the language, and filling the open "Human decision" cells in log rows 14–17, 19, 20 and 22.

## 4. What was learned about vibe coding

- Running code is the most reliable check. Three AI errors (#3, #9, #15) were caught only because the code was executed or tested, not by reading it.
- "Success" messages need independent confirmation (#16): exit codes, logs and even the AI's own summaries can be wrong.
- The most dangerous errors are silent ones. #17 would have produced valid-looking but off-protocol translations. Freezing the protocol and checking its hash, plus diffing every edit, are the guards.
- Environment problems (network, memory, library versions) cost more time than the research code itself.

## 5. Remaining risks

- RQ1 rests on one 1.5B model and machine-translated "native" text; the H2 contradiction may not generalise.
- The exploratory analysis (D16) was designed after the test results were seen.
- Each protocol revision was made before test outputs existed, but after the dev baseline was seen (v3, v4). No change touched the scoring, prompt or metrics, which limits the risk.
- Dev and test runs use different hardware and library versions (documented).
- The AI wrote almost all of the code. The student must be able to explain `src/score.py` (label log-likelihood), `src/metrics.py` (bootstrap, McNemar, Holm) and the leakage controls in the viva.
