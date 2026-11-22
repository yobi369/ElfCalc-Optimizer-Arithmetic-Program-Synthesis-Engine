# Higher-budget GoodPJW LNS on the 130,981 frontier

## Objective

Improve the independently replayed 130,981 source-aware frontier without changing the incumbent unless the resulting 1,000-row submission passes exact replay and has a strictly lower total.

## Pinned inputs

- Official puzzle file: SHA-256 `b0c70d849eca078a0e1cf9a4f7b47fd40b7435663f6f84de6725f84724500428`.
- Starting portfolio: GoodPJW authenticated dataset `our_programs.csv`, SHA-256 `23da4454cd5cb8f2281669f1bf57904eae084352c9ae6a5cf5f423820583a09d`.
- Starting total: **130,981**.
- Optimizer: GoodPJW `elfopt.cpp` from DAG-LNS Programs, Apache-2.0 source; compiled binary SHA-256 `90edda23b996335a7841123a7c9137dc48180c8db20e7473ed557995788768b2`.
- All candidate outputs are locally replayed against the pinned official puzzles before being considered.

## Search configuration

A new two-configuration pass is running with a five-second internal LNS budget per puzzle/configuration, ten-second external timeout, and three worker processes:

1. seed 2, group 4, orders 5, pairs 2, helpers 2, kicks 3, kick slack 2.
2. seed 3, group 5, orders 6, pairs 3, helpers 2, kicks 4, kick slack 3.

This differs from the earlier 131,052-baseline experiment (two configurations, two-second internal budget). The higher budget and altered neighborhood sizes are intended to test whether more aggressive value-DAG neighborhoods can improve the newer 130,981 frontier.

## Initial hard-puzzle profile

The largest current programs are concentrated in large-value, low-seed puzzles. Examples include:

- `scored_0051`: 277 instructions, 32 new targets, 2 starting values.
- `scored_0218`: 276 instructions, 32 new targets, 1 starting value.
- `scored_0321`: 275 instructions, 32 new targets, 4 starting values.
- `scored_0729`: 273 instructions, 32 new targets, 2 starting values.
- `scored_0762`: 273 instructions, 31 new targets, 2 starting values.

These are priority candidates for targeted longer search after the broad pass. This profile is descriptive only; it does not assert that the hardest-by-length puzzles are necessarily the easiest to improve.

## Promotion criteria

- Exactly 1,000 unique puzzle IDs and exact `id,program` schema.
- All operations valid; initialized registers only; exact division; positive bounded intermediate values.
- 48-register, 4,096-instruction, and 131,072-byte limits respected.
- Every target reached.
- Total strictly below 130,981.
- Preserve the source/origin map and optimizer license notice.
- No Kaggle submission without explicit user authorization.

## Status

Search launched locally on 2026-11-22. Results will be appended after the run completes and the full replay audit passes.


## Incumbent update during the run

After this search started, a newer GoodPJW v72 source-embedded patch was reconstructed and independently replayed at **130,976** (see `2026-11-22-goodpjw-130976-independent-replay.md`). This LNS run remains based on the pinned v71 130,981 input because it was already underway. Its output will therefore be treated as an auxiliary candidate bank and merged puzzle-by-puzzle against 130,976; no row from this run can displace a shorter v72 program. The promoted result must be strictly below 130,976 and pass full replay.
