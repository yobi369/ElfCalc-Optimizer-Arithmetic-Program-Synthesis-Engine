# GoodPJW v72 130,976 frontier — independent replay

## Result

**130,976 instructions** across all 1,000 scored puzzles; independently replayed with zero failures.

The v72 notebook source embeds a compressed patch to the v71 attached dataset. The patch was extracted as data (the notebook was not executed) and its `ours` map was applied to the v71 `our_programs.csv`.

## Reproducibility hashes

| Item | SHA-256 |
|---|---|
| Official `puzzles.csv` | `b0c70d849eca078a0e1cf9a4f7b47fd40b7435663f6f84de6725f84724500428` |
| v71 base `our_programs.csv` | `23da4454cd5cb8f2281669f1bf57904eae084352c9ae6a5cf5f423820583a09d` |
| v72 source notebook | `b009a61bd1672c139935ae747c8bd9b6af0b70f206242f7cca16581c5aed8c62` |
| Compressed patch payload | `c331a1496d23ffefcc9105955dc00a3fbb3905374b6a9271fafb097913e83803` |
| Reconstructed candidate CSV | `f06d968ae8cd3eaf5d06739bd999a4b1d6c87ddf9a7697686a7827f333b4ae46` |

## Independent replay checks

- Exact `id,program` header and 1,000 unique puzzle IDs.
- Every instruction parsed and replayed.
- Only initialized registers used; all register indexes in 0–47.
- Exact division only; all intermediate values positive and within each puzzle's limit.
- 4,096-instruction maximum and 131,072-byte serialized program limit.
- Every target reached.
- Result: 1,000/1,000 valid and complete, zero failures.

## Change from v71

84 program rows changed; 4 are shorter, none are longer, 80 are equal length. Net reduction: **5 instructions** (130,981 → 130,976).

## Cross-check against retrieved output banks

All retrieved complete candidate CSVs were independently replayed. The best standalone outputs among those pulls were Ozertuu's 130,979 and Alex Chilton's 130,979. Neither improves any row beyond the reconstructed v72 130,976 candidate. The source-aware v72 candidate remains the best in this retrieved pool.

## Provenance and submission status

This is a mixed-source public frontier assembled by GoodPJW from notebook outputs, notebook-source patches, and attached datasets. The current artifact's row-origin file distinguishes v71 base rows from v72 patch rows, but does not yet establish full upstream row-level author/license lineage. Keep the candidate for local research; complete attribution review before redistribution. It has **not** been submitted to Kaggle.
