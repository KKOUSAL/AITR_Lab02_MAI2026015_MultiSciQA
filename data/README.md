# Data

**PubMedQA PQA-L** (Jin et al., 2019). MIT licence. Source: https://github.com/pubmedqa/pubmedqa (commit `1cbae8e`).
```bash
git clone https://github.com/pubmedqa/pubmedqa.git data/raw/pubmedqa_repo
```
Files used: `data/ori_pqal.json` (1,000 labelled items) and `data/test_ground_truth.json` (official 500-item test set).

- `data/splits/test_pmids.txt`: the official test set. It is used once, for final evaluation.
- `data/splits/dev_pmids.txt`: the other 500 items. Used for prompt and format development only.

Machine translations (Phase III) will be cached under `data/translations/` together with the translation model ID and version.
