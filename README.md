# Native vs Translate-Test for Multilingual Scientific QA (Hindi, Odia)

AITR Lab 02 — Kota Kousalanjan (IIIT Allahabad, mai2026015@iiita.ac.in)

## Problem

On general Indic QA, translating the input to English first (Translate-Test, TT) beats native multilingual processing for very low-resource languages (Singh et al., NAACL Findings 2025). **Does this transfer to scientific evidence?** We test this on PubMedQA biomedical yes/no/maybe QA, machine-translated into Hindi (mid-resource) and Odia (very low-resource), using Qwen2.5-1.5B-Instruct zero-shot. The full brief is in `docs/G1_research_brief.md`.

## Status

| Part | State |
|---|---|
| Pipeline validation (Majority 55.20 / 23.71 reproduced exactly) | ✅ done |
| English baseline, dev (63.00 acc / 45.10 macro-F1) + error analysis | ✅ done |
| Hindi translation pilot (5 dev items) | ✅ done |
| Test run: translation + 5 scoring conditions (Colab T4) | ✅ done: EN 63.60/44.59; TT − NATIVE = +12.88 (hi), +12.42 (or), both significant |
| Exploratory: Odia translation degeneration (D16) | ✅ done |
| Critical peer review (P16) + fixes | ✅ `docs/P16_peer_review.md` |
| 5-minute demo script | ✅ `docs/demo_script.md` |
| Paper | ✅ `paper/main.tex` (7 pages, compiles with tectonic) |

## Repository layout

```
configs/protocol_v{1..4}.yaml + .sha256   frozen protocols (v4 is current; code refuses to run if the hash differs)
data/README.md                           dataset acquisition
data/splits/                             official test PMIDs / dev PMIDs
data/translations/                       cached machine translations (generated)
src/                                     data.py, translate.py, score.py, metrics.py, rq3.py, device.py
scripts/                                 00_data_sanity, 01_translate, 02_score, 03_evaluate, 04_figures,
                                         05_paper_figures_available, env_check, download_models.sh, bench_translate
tests/                                   25 unit tests (leakage, splits, metrics, evaluator, RQ3)
notebooks/02_colab_full_experiment.ipynb  Colab run (produced test EN)
notebooks/03_colab_rerun_translation.ipynb Colab rerun (translation + NATIVE/TT) with a blocking HF login
results/                                 genuine outputs only: sanity/, preds/, pilot/, logs/, env/, tables/, figures/
paper/                                   main.tex, references.bib, figures/
docs/                                    P02-P07, P12, P14 planning and analysis documents
research_decisions.md  baseline_validation.md  ai_assistance_log.md
```

## Setup

Compute requirements: the dev baseline runs on an Apple M1 with 8 GB (about 12 min). Translation needs a GPU: the M1 measured 4.7–10 s per sentence, so use a Colab T4.

```bash
python3 -m venv --system-site-packages .venv                      # executed (Python 3.13.5)
.venv/bin/python -m pip install sentencepiece sacrebleu accelerate IndicTransToolkit   # executed
.venv/bin/python -m pip install 'transformers==4.51.3'            # executed: needed for IndicTrans2 (see Notes)
hf auth login                                                    # executed in macOS Terminal (needs a TTY)
```
Exact versions: `requirements.txt` (local) and `results/colab_env.txt` (written by the Colab run).
Gated models: accept the terms on HF for `ai4bharat/indictrans2-en-indic-dist-200M` and `ai4bharat/indictrans2-indic-en-dist-200M`.

## Data

```bash
git clone https://github.com/pubmedqa/pubmedqa.git data/raw/pubmedqa_repo   # executed, commit 1cbae8e (MIT licence)
python3 scripts/00_data_sanity.py                                         # executed: 500/500 split, Majority 55.20/23.71
```

## Reproduce

| Step | Command | Status |
|---|---|---|
| Unit tests | `python3 -m pytest -q` | ✅ 25 passed |
| English baseline (dev) | `python3 scripts/02_score.py --model Qwen/Qwen2.5-1.5B-Instruct --condition EN --split dev` | ✅ 63.00 / 45.10, 720 s on M1 |
| Evaluate dev | `.venv/bin/python scripts/03_evaluate.py --split dev` | ✅ |
| Paper figures (available data) | `python3 scripts/05_paper_figures_available.py` | ✅ |
| Translate test | `python scripts/01_translate.py --lang {hi,or} --split test` | ✅ Colab T4: hi 16 min, or 45 min |
| Score test | `python scripts/02_score.py --model Qwen/Qwen2.5-1.5B-Instruct --condition {EN,NATIVE,TT} --lang {en,hi,or} --split test --confirm-test` | ✅ Colab T4 |
| Tables + statistics | `.venv/bin/python scripts/03_evaluate.py --split test` | ✅ `results/tables/test/` |
| Figures | `.venv/bin/python scripts/04_figures.py --split test` | ✅ `results/figures/test/` |
| Live one-item demo (read-only, ~25 s on M1) | `python3 scripts/demo_one_item.py` | ✅ matches the stored Colab predictions |
| Exploratory (not pre-registered) | `python3 scripts/06_exploratory_degeneration.py` | ✅ `results/exploratory/` |

Seeds: 2026 everywhere. The bootstrap uses 10,000 resamples.

## Notes and known issues

- **transformers ≥ 4.56 breaks IndicTrans2's remote code** (`AttributeError` on `past_key_values`). Pin 4.51.3 for translation.
- **`HF_HUB_OFFLINE=1` crashes tokenizer loading** in transformers 4.57.3 (Hub API call in `_patch_mistral_regex`).
- On slow networks, use `scripts/download_models.sh`. It disables Xet and only accepts a download once the weight file is verified, because `hf download` can exit 0 after a network drop.
- In Colab, `login()` does not block under "Run all". Notebook 03 uses `getpass` and checks access before translating.
- IndicTrans2 (EN→Odia) degenerates on about 10% of sentences (trailing '....'). See D16.
- The PubMedQA source text contains broken decimals (e.g., `14. 1%`). They are kept as-is.

## Limitations

A single 1.5B model; one language per tier; Odia translation degeneration; machine-translated "native" inputs; possible pretraining contamination; uncalibrated scoring with a yes-bias; no prompt-sensitivity analysis. See `paper/main.tex` §Limitations and `research_decisions.md` D13–D15.

## Minimum reproduction checklist (for a second student)

- [ ] Clone this repo and PubMedQA; run `scripts/00_data_sanity.py` and check Majority = 55.20 / 23.71.
- [ ] `pytest -q`: all pass, including the protocol-hash check.
- [ ] Score EN dev with Qwen2.5-1.5B and check it is within about ±1 point of 63.00 / 45.10 (hardware nondeterminism).
- [ ] Run the Colab notebook and compare `results/tables/test/summary.json` with the paper.

## Credits and licences

PubMedQA (MIT); IndicTrans2 (MIT, AI4Bharat); Qwen2.5 (`qwen-research` licence). No model weights or tokens are stored in this repository.

## Citation

Kousalanjan, K. (2026). *Native or Translate-Test? A Controlled Study of Multilingual Scientific Question Answering in Hindi and Odia.* AITR Lab 02, IIIT Allahabad.
