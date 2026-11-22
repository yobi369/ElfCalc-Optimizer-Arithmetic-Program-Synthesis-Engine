# Submission checkpoint — 130,976 instructions

## Current research incumbent

- Candidate: GoodPJW source-aware frontier v72, reconstructed by applying its source-embedded data patch to the v71 attached `our_programs.csv`.
- File in the local verified bundle: `submission.csv`.
- Rows: 1,000.
- Exact schema: `id,program`.
- Total instructions: **130,976**.
- Independent exact replay: **1,000/1,000 valid and complete**, zero failures.
- Candidate SHA-256: `f06d968ae8cd3eaf5d06739bd999a4b1d6c87ddf9a7697686a7827f333b4ae46`.
- Official puzzle data SHA-256: `b0c70d849eca078a0e1cf9a4f7b47fd40b7435663f6f84de6725f84724500428`.

The source patch was extracted as data; the third-party notebook was not executed. All instructions were replayed against the exact pinned official puzzle file. The candidate package is available in this conversation's verified artifact: `santa-2026-130976-verified-candidate.zip`.

## Provenance and clearance

This is a mixed-source public-reference frontier assembled by GoodPJW from public notebook outputs, notebook-source patches, and attached datasets. The local origin map distinguishes the 84 rows touched by the v72 patch from the 916 v71 base rows, but the complete upstream author/license lineage for every individual row has not yet been established.

- Do not describe this as an original solver score.
- Do not redistribute the mixed-source CSV until row-level attribution and license review are complete.
- Check the current Kaggle competition rules before deciding whether to submit a public-reference merge.
- No Kaggle submission has been made from this project session.

See [the independent 130,976 replay report](research/experiments/2026-11-22-goodpjw-130976-independent-replay.md) and [the authenticated solver-source audit](research/experiments/2026-11-22-authenticated-solver-source-audit.md).

## Reproduce the candidate

The original v71 dataset and v72 patch were retrieved from authenticated Kaggle sources. The verification report records the base dataset, source notebook, compressed patch, candidate, and official puzzle hashes. The v72 patch can be reconstructed by:

1. Downloading GoodPJW's v71 attached `our_programs.csv`.
2. Retrieving `goodpjw2008/santa-2026-source-aware-frontier-lb-130-976`.
3. Extracting the `_PATCH` base64/zlib payload from the notebook source as data.
4. Applying `_PATCH['ours']` to the v71 program map.
5. Serializing in the official `id,program` format.
6. Running the repository's exact replay validator against the pinned `puzzles.csv`.

The authenticated retrieval workflow is [here](.github/workflows/fetch-authenticated-kernel-sources.yml). Its successful source/output retrieval artifacts are retained in GitHub Actions for their artifact-retention period.

## Competitive position snapshot

Against the leaderboard values supplied in this research session:

| Position | Score | Gap above this candidate |
|---|---:|---:|
| 1st | 126,659 | 4,317 |
| 2nd | 126,660 | 4,316 |
| 3rd | 128,059 | 2,917 |
| 4th | 128,300 | 2,676 |
| Current research incumbent | **130,976** | — |

These are a user-provided leaderboard snapshot, not a fresh official Kaggle confirmation. The live leaderboard may change.

## Historical checkpoints

- 131,047: GoodPJW LNS portfolio, independently replayed.
- 131,007: GoodPJW v155 frontier, independently replayed.
- 130,981: GoodPJW source-aware v71 frontier, independently replayed.
- 130,976: GoodPJW source-aware v72 patch, independently replayed; current incumbent.

The current higher-budget GoodPJW LNS pass began from the 130,981 predecessor. Its results will be merged against 130,976 and promoted only if the full merged candidate is strictly shorter and passes exact replay.

## Official submission procedure

Only after the competition rules and provenance are reviewed, and after explicit user authorization to submit, use:

```bash
kaggle competitions submit -c santa-2026 -f submission.csv -m "Exact replay-validated arithmetic program portfolio"
kaggle competitions submissions -c santa-2026
```

Never paste Kaggle credentials or API tokens into chat or commit them to this repository.
