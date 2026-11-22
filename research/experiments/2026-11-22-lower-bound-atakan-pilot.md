# Exact score floor and Atakan optimizer pilot — 22 November 2026

## Exact structural lower bound

The official scored puzzle file used in this experiment has SHA-256:

`b0c70d849eca078a0e1cf9a4f7b47fd40b7435663f6f84de6725f84724500428`

A direct count over all 1,000 puzzles gives:

- Distinct target instances across puzzles: **26,902**
- Target instances already present in their puzzle's starting registers: **4**
- Distinct target values absent from starting registers: **26,898**

For each puzzle, every distinct target absent from its initial registers must be produced by at least one instruction. An instruction writes one result value, so it cannot produce two different target values in the same step. Summing the missing-target counts across puzzles therefore proves a global lower bound of **26,898 instructions**.

This is a structural lower bound, not a claim that it is attainable. It establishes that a 6,000–8,000 total is below the feasible range for this dataset. The reproducible analyzer is `scripts/analyze_instruction_lower_bound.py`:

```bash
python scripts/analyze_instruction_lower_bound.py --puzzles data/puzzles.csv --output outputs/instruction-lower-bound.json
```

## Atakan multiplier-frontier and interface-closure pilot

We inspected the Apache-2.0 Atakan Aldemir optimizer sources bundled in GoodPJW's public dataset v151. The bundle's `atakan_optimizers/NOTICE.md` identifies the sources as unchanged extractions from the public notebook *Santa 2026 | Joint Recipes for Large Puzzles* and credits the original author.

Two binaries were built locally from that bundle:

- `elf_multiplier_frontier.cpp` — SHA-256 `758fe59b9e89f731e972e70c1de1fda034aed10b49de1ded8f3b8fd9fcd80574`
- `elf_interface_closure.cpp` — SHA-256 `633524282c64452b21638a62bbcf2943634cde48372d952d6b04b6f794ae6bb6`

Both were run against the eight highest-instruction programs in the 131,052 candidate, then a repeat sweep was run against the ten highest-instruction programs. The tested configurations were:

- Frontier: `8 4200 9 10 9 20261123 1500`
- Interface closure: `90 26 7 20261123 4150`

The ten-puzzle sweep completed 20 optimizer runs in 18.1 seconds. Every returned program passed exact local replay and target-coverage validation. **No strict instruction-count improvements were found.**

This is a narrow pilot, not evidence that the methods cannot help elsewhere. Next experiments should vary frontier styles/salts and sample puzzles across the full difficulty distribution, then evaluate the methods as a full-dataset pass. The 131,052 candidate remains the verified baseline until a better complete portfolio passes independent replay and provenance review.

## Reproducibility and attribution

- Puzzle data remains local and is not committed.
- The Atakan optimizer source bundle is Apache-2.0; its upstream `NOTICE.md` is retained with the source archive.
- This experiment used the optimizer binaries against the existing candidate and did not import third-party program portfolios.
- No Kaggle submission or leaderboard score is claimed.
