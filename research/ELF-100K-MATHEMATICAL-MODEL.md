# ELF-100K mathematical model and first experiment

**Status:** Design note grounded in the repository VM and puzzle model  
**Date:** 2026-11-23  
**Target:** 100,000 instructions; research objective, not a forecast

## 1. Exact computational model

The repository's VM and puzzle parser establish the following model:

- Each puzzle is solved independently.
- There are exactly 48 registers.
- The only operations are addition, subtraction, multiplication, and exact division.
- Initial values and all computed results must be positive integers.
- Every computed result must be at most that puzzle's `value_limit` (at most (10^{18})).
- Division by zero and non-exact division are invalid.
- All source registers must already be initialized.
- Both source values are read before the destination register is overwritten.
- A target is considered covered once its value has appeared in an initial or computed register; overwriting that register later does not remove coverage.
- One instruction writes one destination and can introduce at most one previously unseen target value.
- The official submission permits at most 4,096 instructions and 131,072 serialized bytes per program.

The evaluator counts instructions, not source-code brevity. A shared library or common recipe across puzzle programs does not mean that runtime register values are shared across puzzles. Cross-puzzle discoveries can transfer recipes, transformations, and search guidance, but each puzzle's program must independently compute its values.

## 2. The unavoidable target-production floor

The frozen score-landscape report records 26,898 target occurrences not present in their corresponding puzzle's starting registers. Because one instruction can introduce at most one new target value:

[
L = sum_{p=1}^{1000} |mathrm{targets}(p) setminus mathrm{startingValues}(p)| = 26,898
]

Thus every complete 1,000-puzzle portfolio must use at least 26,898 instructions on the pinned puzzle set. This is a simple unconditional lower bound, not an optimality claim.

For the 130,974 incumbent:

[
130,974 - 26,898 = 104,076
]

There are therefore 104,076 instructions above this basic target-production floor. These include non-target intermediate computations and any avoidable work such as duplicate results.

For a 100,000 candidate:

[
100,000 - 26,898 = 73,102
]

The target requires eliminating 30,974 instructions, equivalent to reducing the incumbent's above-floor cost by about 29.76%.

This reframes the problem. We are not trying to reduce the number of required target appearances; we are trying to make the intermediate computational scaffolding dramatically more efficient.

## 3. First experiment: instruction-economy decomposition

Before building another large search engine, instrument a frozen, fully replayed candidate and classify every instruction result:

- **New required target:** the result is a target not previously observed in that puzzle.
- **Useful non-target intermediate:** the result is not a target but is later consumed by an instruction that contributes to a new required target or another useful intermediate.
- **Dead intermediate:** the result is never consumed by a later instruction that contributes to a required target.
- **Duplicate result:** the value already existed in an initial register or earlier result.

For every puzzle, record:
- total instruction count;
- number of missing targets;
- target-producing instruction count;
- useful intermediate count;
- dead intermediate count;
- duplicate-result count;
- maximum register pressure / live-value count;
- register lifetime and last-use positions;
- instruction count per newly covered target.

A target may also be used as an intermediate; classify by whether its value is a required target first, then separately record its downstream uses. Do not double-count categories.

**Primary output:** a per-puzzle table and aggregate decomposition that shows exactly where the 104,076 above-floor instructions are spent.

**Hypothesis:** The most promising puzzles are not necessarily just the longest. They are those with the highest intermediate overhead per missing target and the most repeated or dead computational structure.

## 4. Follow-up research derived from the decomposition

### A. Algebraic compression

Search for exact semantic-preserving rewrites that reduce the number of intermediate values. Each rewrite must have explicit preconditions and be proven valid under positive-integer, exact-division, and value-limit constraints.

### B. Register-lifetime and schedule optimization

A register allocation change alone cannot reduce the instruction count, but better scheduling can expose reuse, avoid recomputation, and enable more compact DAGs within 48 registers. Measure these effects separately.

### C. Shared recipe transfer across puzzles

Mine reusable *recipes*, not shared runtime state. A recipe is a proven transformation pattern with parameterized inputs and explicit value-limit/divisibility preconditions. Evaluate transfer on held-out puzzles.

### D. Backward and meet-in-the-middle synthesis

Use target requirements to search for low-cost predecessor constructions. Canonicalize states only where equivalence is sound. Compare against matched forward-search baselines.

### E. Candidate portfolio optimization

For each puzzle, combine only exact-replay-valid candidates with traceable provenance. The per-puzzle minimum is a lower-envelope diagnostic; the final merged CSV must be serialized and replayed independently.

## 5. Falsifiable experiment order

1. Reproduce the 130,974 incumbent from its frozen artifact and pinned puzzle file.
2. Generate the instruction-economy decomposition for the incumbent and for the 130,859, 130,914, and 130,939 public candidates.
3. Compare per-puzzle overhead and identify high-overhead strata.
4. Test whether operation/graph fingerprints predict which solver family wins on held-out puzzles.
5. Select a small set of high-overhead puzzles and run one new algebraic or reverse-synthesis experiment against fixed baselines.
6. Promote only improvements that pass exact replay and provenance/license review.

## 6. Reproducibility

Use the pinned official puzzle hash:

`b0c70d849eca078a0e1cf9a4f7b47fd40b7435663f6f84de6725f84724500428`

Record candidate hash, evaluator hash/version, experiment seed, compute budget, and all per-puzzle outputs. The existing data-analysis limit currently blocks archive inspection and score decomposition; do not bypass it using another executor. Resume the archive inspection and decomposition when data analysis is available.

## 7. Source files used to establish semantics

- `src/elfcalc/machine.py`
- `src/elfcalc/puzzle.py`
- `src/elfcalc/validation.py`
- `research/score-landscape-2026-11-22.md`

These describe the project's local VM and puzzle model. Before final competition claims, confirm that they match the official evaluator and current competition rules.
