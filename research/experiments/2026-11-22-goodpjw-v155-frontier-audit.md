# GoodPJW v155 public-frontier audit — 22 November 2026

## Result

The latest public-pool refresh artifact (GitHub Actions run `45051976216`) contains GoodPJW's current Kaggle dataset release, version 155:

- Dataset: `goodpjw2008/santa-2026-dag-lns-programs`
- Declared dataset license: Apache-2.0
- Dataset description: Apache-2.0 applies to GoodPJW's own code and programs its search shortened; all other programs retain the terms of the public notebook or dataset from which they came.
- Candidate file: `our_programs.csv` (byte-identical to `public_frontier.csv`)
- Candidate SHA-256: `4c4ef08ee0782f0a3637b7d696dc3395e69441403a63a447304c946fe1c672c5`
- Candidate score: **131,007** instructions.

The candidate was independently replayed against the official 1,000-puzzle data bundled in the same refresh artifact: 1,000/1,000 complete and valid, zero failures. This is a local verification of the downloaded candidate, not a Kaggle submission by this repository.

## Comparison with our current 131,047 candidate

A per-puzzle comparison found:

- GoodPJW v155 is shorter on 36 puzzles, saving 41 instructions in those rows.
- It is longer on one puzzle (`scored_0757`) by one instruction.
- Net portfolio improvement if merged by shortest valid row: **40 instructions**, giving 131,007.
- The earlier local candidate remains better on `scored_0757`; retain it in any technical merge.

The public candidate is 5,652 instructions above the screenshot's first-place score of 126,659 and 31,008 above the below-100,000 research target. It is a useful new baseline, not a top-four result.

## Licensing gate — do not publish a merged submission yet

The Kaggle dataset description explicitly says that rows not shortened by GoodPJW's search retain their upstream notebook/dataset terms. The downloaded archive does not include a per-puzzle source map for `our_programs.csv`; the dataset description directs users to credit tables in GoodPJW's Kaggle notebooks.

Therefore, although the candidate is technically valid and the dataset itself declares Apache-2.0, its row-level reuse rights are not yet fully audited. Do not redistribute or submit a merged file as Apache-2.0 until the relevant notebook source/credit tables have been retrieved and each inherited row's license has been checked. The repository's authenticated notebook-source workflow is intended for this audit and requires the `KAGGLE_API_TOKEN` GitHub Actions secret; never put that token in chat.

## Separate Atakan control

The completed Atakan v151 frontier/interface-closure run (`45051202535`) improved its 131,052 baseline by one instruction to 131,051 (1/1,000 puzzles improved; 1,999/2,000 search attempts found no improvement). The candidate replayed 1,000/1,000, but it does not beat our 131,047 candidate. A higher-budget Atakan run and a second GoodPJW LNS run are still running separately.

## Reproducibility

- Public-pool refresh run: https://github.com/yobi369/ElfCalc-Optimizer-Arithmetic-Program-Synthesis-Engine/actions/runs/45051976216
- Atakan v151 run: https://github.com/yobi369/ElfCalc-Optimizer-Arithmetic-Program-Synthesis-Engine/actions/runs/45051202535
- Atakan artifact ID: `14766361265`
- Public-pool artifact ID: `14765897333`
- Official puzzle SHA-256: `b0c70d849eca078a0e1cf9a4f7b47fd40b7435663f6f84de6725f84724500428`
