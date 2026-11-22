# Competition datasets

## Important: keep raw competition data private

This repository is public. The `data/` directory is intentionally git-ignored, so competition files are not committed or exposed to people who may not have joined the competition. Kaggle competition rules commonly restrict redistribution and require participants to protect access to competition data; check the Santa 2026 rules before moving raw files to any external storage.

## Restore the files without re-uploading them to ChatGPT

On a machine with access to your Kaggle account:

1. Join **Santa 2026 — The Elf Calculator** and accept its rules on Kaggle.
2. Install the CLI: `python -m pip install kaggle`.
3. Configure Kaggle authentication using `~/.kaggle/kaggle.json` or `KAGGLE_API_TOKEN`.
4. From the repository root, run:

   ```bash
   bash scripts/fetch_kaggle_data.sh
   ```

The script downloads the competition archive and places `puzzles.csv` and `sample_submission.csv` in the local, ignored `data/` directory. It also copies `practice_puzzles.csv` if Kaggle includes it in the archive. If the practice file is a separate attachment, save it manually as `data/practice_puzzles.csv`.

Then run the audit and benchmark scripts using those local paths. The data stays on your machine and is not committed to this public repository.

## Current files inspected in the working session

The following SHA-256 fingerprints identify the exact CSVs inspected in this session. They are metadata only; the raw competition files are not stored in this public repository.

| File | Bytes | SHA-256 |
|---|---:|---|
| `puzzles.csv` | 416,612 | `b0c70d849eca078a0e1cf9a4f7b47fd40b7435663f6f84de6725f84724500428` |
| `practice_puzzles.csv` | 87,861 | `a87e4e0ad263f31af1a9e51459117212b03404339c5940be3aa6afd1596ff6d9` |
| `sample_submission.csv` | 20,882,318 | `5b9d3ba58b58c6b3c158ba2e7cc98ae66994a0f21168c95e65297214e274ab5d` |

These fingerprints are for integrity checks, not a substitute for the files. Recompute them after every download.
