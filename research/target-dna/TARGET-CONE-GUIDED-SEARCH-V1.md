# Target-Cone-Guided Beam Search v1

## Status

Implemented as an experimental extension to `src/elfcalc/bounded_search.py`.
It is not integrated into the production solver and has not been evaluated on the scored puzzle archive. The existing 130,974-instruction incumbent is unchanged.

## Research hypothesis

A forward beam wastes expansions on values that are arithmetically legal but have no short route to any uncovered target. Reverse arithmetic equations can cheaply identify a subset of candidate operands that may participate in a target-reaching chain.

For a target \(t\) and known anchor \(a\), the reverse operator set derives candidate values \(x\) satisfying one of:

- \(x+a=t\)
- \(x-a=t\)
- \(a-x=t\)
- \(x\cdot a=t\)
- \(x/a=t\)
- \(a/x=t\)

Only positive integral candidates within the puzzle value limit are retained. The implementation reuses the exact inverse-equation helper already used by the shared-intermediate planner.

## Algorithm

1. Construct a deterministic forward-reachable anchor pool from the initial values using legal one-instruction arithmetic.
2. Bound the pool to 512 distinct values and the closure depth to the configured beam depth.
3. Starting from uncovered targets, repeatedly invert target equations against every anchor in the pool.
4. Bound the accumulated reverse cone to 4,096 values.
5. Preserve per-target cone provenance instead of flattening all goals into one union. Values occurring in several target cones are recognized as shared-intermediate candidates.
6. During beam expansion, prefer legal recipes whose result lies in the reverse cone; use the number of supported goals as an additional deterministic ranking signal.
7. If a capped cone produces no legal expansion for a state, retain a deterministic escape hatch of up to 16 ordinary frontier recipes, ranked by immediate target yield.
8. Completed proposals still pass through the production register scheduler and exact VM replay before being returned.

## Why this is not a completeness claim

The anchor pool and reverse cone are both capped. A useful operand may lie outside the pool, and a useful chain may exceed the configured depth. The escape hatch only activates when the cone yields no expansion; it does not guarantee recovery of every useful branch. Therefore this is a target-directed heuristic, not a complete synthesizer, admissible lower-bound search, or globally optimal planner.

## Verification

Unit fixtures cover:

- the existing three-intermediate power chain \(2\to4\to16\to256\to65536\);
- reverse-cone inclusion of the chain's intermediate values;
- per-target support attribution and a shared value (6) that unlocks both targets 12 and 18;
- an end-to-end beam fixture that finds the single shared intermediate and VM-replays both targets;
- inversion coverage for addition, both subtraction orientations, multiplication, and exact division with either the unknown dividend or divisor;
- deterministic output and enforcement of the cone cap;
- beam determinism, intermediate budgets, invalid value limits, and initial-target handling;
- exact scheduler/VM replay for completed proposals.

CI run for the initial target-cone integration passed on Python 3.10, 3.11, and 3.12:
https://github.com/yobi369/ElfCalc-Optimizer-Arithmetic-Program-Synthesis-Engine/actions/runs/45340798949

The cap adjustment and expanded target-cone fixtures have separate CI runs in progress:
https://github.com/yobi369/ElfCalc-Optimizer-Arithmetic-Program-Synthesis-Engine/actions/runs/45340829360

## Multi-target cone extension

The beam now builds a separate bounded reverse cone for each missing target and retains a mapping from each candidate value to the targets supported by that value. Shared values receive a stronger ranking signal. The synthetic fixture uses starting values 2 and 3: the intermediate 6 unlocks both 12 and 18 in one operation each. This explicitly tests multi-target leverage rather than only checking that an intermediate belongs to a union of cones.

## Next research gates

1. Confirm all Python-version CI jobs pass on the cap-adjusted, test-expanded commit.
2. Add adversarial fixtures where a target requires a reverse operand not present in the shallow anchor pool, documenting when the fallback is and is not sufficient.
3. Compare cone-guided and unguided search under identical deterministic expansion budgets on synthetic fixtures before touching the scored archive.
4. Only after the data-analysis restriction clears, benchmark on the full puzzle set and compare exact per-puzzle output against the frozen incumbent.
5. Do not promote or submit a candidate without complete exact replay, provenance audit, and explicit user approval for Kaggle submission.

## Score integrity

No new full-dataset score is claimed. No Kaggle submission has been made. The frozen incumbent remains 130,974 instructions.


## Two-node shared-subgraph look-ahead

The bounded beam now computes a deterministic, capped look-ahead over two-intermediate DAG fragments from the actual starting frontier. It scores a first intermediate by the number of missing targets that become directly reachable after a legal second intermediate. This is separate from the reverse-cone signal: it explicitly preserves the relationship between the first node, a second bridge node, and the jointly exposed targets.

Synthetic fixture: starts 2 and 3 produce 5, then 7; the pair 5 and 7 produces both 12 and 35. Tests assert the support attribution and require the beam's completed plan to pass the register scheduler and VM replay. The helper is capped at 128 first recipes and 256 second recipes per first recipe. It remains a heuristic and is not integrated into the production solver or evaluated on the scored archive.
