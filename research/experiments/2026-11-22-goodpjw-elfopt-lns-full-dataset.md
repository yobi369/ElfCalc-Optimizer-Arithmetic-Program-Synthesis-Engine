# Full-dataset GoodPJW LNS experiment — 22 November 2026

## Result

The first two-configuration, full-dataset run completed successfully on GitHub Actions.

| Measure | Result |
|---|---:|
| Puzzles | 1,000 |
| Search runs | 2,000 |
| Wall time | 1,798.27 seconds |
| Baseline | 131,052 |
| New total | **131,047** |
| Instructions saved | **5** |
| Distinct improved puzzles | 5 |
| Exact replay audit | 1,000/1,000 complete; zero failures |

The five one-instruction reductions are:

| Puzzle | Before | After | Search configuration |
|---|---:|---:|---|
| scored_0161 | 157 | 156 | seed0-g3-o3 |
| scored_0423 | 90 | 89 | seed0-g3-o3 |
| scored_0626 | 159 | 158 | seed0-g3-o3 |
| scored_0737 | 112 | 111 | seed1-g4-o4 |
| scored_0778 | 123 | 122 | seed0-g3-o3 |

Seven search runs reported improvements, but two runs rediscovered improvements already found by the other configuration; the merged portfolio therefore improved five distinct puzzles by five instructions total.

## Validation

The final serialized `submission.csv` was independently replayed against the exact `puzzles.csv`:

- Exact header: `id,program`.
- Exactly 1,000 unique puzzle IDs, no missing or extra IDs.
- Every operation uses one of `+ - * /`, valid initialized registers, exact integer division, positive results, and the puzzle's value limit.
- Every target is generated or initially present.
- Per-program instruction and serialized-byte limits are respected.
- Result: **1,000 valid and complete; zero failures**.

Candidate SHA-256: `fada061b2aba1ba8dfbd0ed27083ec080f99238295c5fd08c5d2ee9703c4597a`.

The experiment artifact also includes the full run log, source attribution, optimizer binary hash, and Apache-2.0 notice.

## Interpretation

The LNS engine can find strict improvements, but this first full pass yielded only five instructions. It is evidence that the method works, not evidence that it has reached its limit. The next pass changes random seeds and increases the per-run search budget. A later stage should prioritize hardest puzzles and add register-aware recomputation/rematerialization to escape the limitations of value-DAG-only optimization.

## Provenance and licensing

The starting portfolio is the attributed 131,052 per-puzzle minimum merge of Juan-Severiano's checkpoint and Ishan Karnick's frontier v18. The five changed programs were produced by GoodPJW's `elfopt.cpp` optimizer from DAG-LNS Programs v151. The optimizer code is Apache-2.0; the upstream attribution and license notice are retained in the artifact and repository. Original puzzle-program lineage remains in the baseline origin map.

This is not an original solver score and has **not** been submitted to Kaggle.
