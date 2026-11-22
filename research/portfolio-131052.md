# Verified local portfolio: 131,052 instructions

Date: 22 November 2026

## Result

We built a per-puzzle minimum portfolio from two public reference candidates:

- Juan-Severiano's attributed Apache-2.0 checkpoint: 132,515 instructions.
- Ishan Karnick's frontier dataset v18: 131,053 instructions.

For each of the 1,000 puzzles, both candidate programs were replayed under the exact arithmetic/register/value constraints. We selected the shorter valid program; ties retain the Juan-Severiano program. The serialized result was replayed a second time and independently reproduced byte-for-byte by the repository merge/audit script.

| Measure | Result |
|---|---:|
| Total instructions | **131,052** |
| Puzzles valid and complete | 1,000 / 1,000 |
| Invalid or incomplete | 0 |
| Rows from Juan-Severiano 132,515 | 640 |
| Rows from Ishan Karnick v18 | 360 |
| Median instructions per puzzle | 117 |
| 90th percentile | 217 |
| Shortest / longest program | 2 / 277 |
| Savings vs Juan-Severiano parent | 1,463 |
| Savings vs Ishan parent | 1 |
| Reduction vs sample submission (1,490,379) | 91.2068% |

Candidate SHA-256:

`1902b48b488380c9282a2537ad0279cc7f6c0d159f19360b019501fe0401ccef`

Puzzle SHA-256:

`b0c70d849eca078a0e1cf9a4f7b47fd40b7435663f6f84de6725f84724500428`

## Row-level lineage

The 360 rows selected from Ishan v18 break down as follows:

| Ishan source category | Selected rows |
|---|---:|
| Ishan graph-search polish / own solver | 224 |
| Alex Chilton Rudolph programs (CC0) | 125 |
| GoodPJW DAG-LNS | 11 |

The remaining 640 rows come from the Juan-Severiano 132,515 checkpoint. Its upstream notice credits the GoodPJW dataset v55 and the original public contributors. Preserve [the Juan-Severiano notice](upstream/132515-NOTICE.md), the [Ishan v18 credits](upstream/ishan-v18-CREDITS.md), and the [Ishan v18 manifest](upstream/ishan-v18-MANIFEST.md).

The complete per-puzzle source table is stored with the private candidate artifact as `elfcalc_submission_131052_origins.csv`.

## Comparison with public standings

A third-party CLIST snapshot observed on 22 November listed 126,659 as the leading score. Our local candidate is 4,393 instructions above that snapshot. This is not an official Kaggle rank; recheck the Kaggle leaderboard before submission.

## Research notes

A 6,000–8,000 total is below the elementary mathematical lower bound: 26,898 targets are absent from their puzzle's starting registers, and each such value requires at least one instruction to be generated. A public research project reports a stronger combined puzzle-level lower bound of 37,987; those external certificates have not yet been independently rechecked here.

The next work is to beat 131,052 through new, exact, per-puzzle search—not to relabel a public merge as an original algorithmic result. Priority methods include graph-cut-and-rebuild, value-graph search, target-cone re-synthesis, and register-aware instruction scheduling.

## Submission status

Prepared and independently replay-validated locally. **Not submitted to Kaggle.**
