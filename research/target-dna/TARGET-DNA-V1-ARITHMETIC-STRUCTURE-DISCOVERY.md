# Target DNA v1 — arithmetic structure discovery

**Status:** Research specification; no experiment or score improvement is claimed  
**Date:** 2026-11-23  
**Research objective:** Discover reusable arithmetic structure across each puzzle's target set and turn it into shorter valid instruction DAGs.

## 1. Research question

Given a puzzle's initial register values, target set, and value limit, can we identify a compact set of intermediate values whose computation unlocks many targets?

The unit of optimization is not an isolated target expression. It is a directed acyclic graph (DAG) of arithmetic operations. A value may be expensive to create once but valuable if many target derivations reuse it.

Cross-puzzle learning transfers patterns and recipes, never runtime register state. Every puzzle still has an independent program.

## 2. Target fingerprints

For every positive target t, compute a feature record:

- magnitude band: floor(log10(t));
- bit length;
- parity and residues modulo a fixed small-prime basis;
- gcd relationships with other targets and initial values;
- exact quotient relationships where divisibility holds;
- additive and subtractive relationships;
- prime-valuation fingerprint when factorization is available.

The prime-valuation fingerprint is the sparse vector v_p(t), where each coordinate is the exponent of prime p in t. Treat t=1 as the all-zero vector. Factorization is a feature generator, not a correctness dependency: all proposed arithmetic edges must be checked with exact integer arithmetic.

For large values, use a bounded factorization pipeline (small-prime stripping followed by deterministic-seeded Pollard rho / primality testing) and record whether factorization is complete. Never silently treat a partial factorization as complete.

## 3. Build the target relation graph

Create a typed graph whose vertices are:
- initial values;
- required target values;
- candidate intermediate values.

Add a directed recipe edge only when an operation is exactly valid:

- Addition: a + b = c.
- Subtraction: a - b = c, with a > b > 0.
- Multiplication: a * b = c and c <= value_limit.
- Division: a / b = c, with b > 0 and a mod b = 0.

Each edge records operand values, operation, output, source class, and proof checks. Commutative operations use canonical operand order for deduplication. Do not create edges that violate positivity or the puzzle's value limit.

### Candidate intermediate generation

Generate a bounded, deduplicated candidate set from:
1. gcd(a,b), when greater than 1;
2. exact quotients a/gcd(a,b) and b/gcd(a,b);
3. positive differences |a-b|;
4. exact ratios among targets and initial values;
5. products or sums only when they are within the value limit and are supported by a plausible target-reachability path.

A candidate is not automatically worth computing. It must be scored by downstream reachability and actual DAG cost.

## 4. Shared-intermediate value

For a candidate intermediate x, estimate its marginal value against the current available-value set S:

- direct target yield: number of uncovered targets reachable from x and one value in S by one legal operation;
- two-step yield: number of uncovered targets reachable through a bounded two-operation extension;
- reuse count: number of distinct target derivations that can consume x;
- construction cost: shortest known legal recipe to create x from S;
- register burden: estimated live-value pressure if the recipe and consumers are scheduled together.

Use a conservative score such as:

utility(x) = (weighted_new_targets + reuse_credit) / (construction_cost + register_penalty)

The weights must be fixed before each benchmark run. Record raw components as well as the aggregate score so the ranking can be audited.

Avoid double-counting: a target counts as newly covered once, regardless of how many recipes can produce it.

## 5. DAG selection as a budgeted coverage problem

Each candidate recipe is a small DAG fragment with:
- required input values;
- newly produced values;
- instruction cost;
- value-limit and exact-division preconditions;
- register-liveness estimate.

Select a compatible collection of fragments that maximizes uncovered target coverage under instruction and register budgets. A greedy marginal-coverage baseline is required; compare it with beam search and bounded local replacement. The optimizer must account for dependencies: a fragment cannot be selected unless its inputs are available or produced by selected predecessor fragments.

The final schedule is a topological ordering of the selected DAG, followed by register allocation. Register allocation may make a DAG infeasible but cannot by itself reduce its arithmetic instruction count. Report DAG cost and scheduled program cost separately.

## 6. Search loop

1. Seed S with the puzzle's initial values.
2. Generate exact one-step recipes from S and a bounded candidate-intermediate frontier.
3. Rank candidates by marginal target yield per construction cost.
4. Expand the best candidates, updating target coverage and reuse counts.
5. Apply bounded DAG-fragment replacement to remove redundant computations.
6. Schedule the DAG under the 48-register constraint.
7. Serialize and validate with the exact evaluator.
8. Retain only candidates that improve the matched baseline.

Use deterministic seeds and fixed compute budgets. Keep a held-out puzzle split so thresholds and weights are not tuned on the final evaluation set.

## 7. Required baselines and ablations

Compare on identical puzzle subsets and budgets:

- current incumbent solver;
- direct target-by-target synthesis;
- shared-intermediate greedy selection;
- greedy plus beam expansion;
- greedy plus DAG local replacement;
- each variant without factorization features;
- each variant without residue features;
- each variant without two-step yield.

This isolates whether Target DNA adds value beyond ordinary arithmetic search.

## 8. Correctness invariants

Every emitted instruction must satisfy:
- source registers are initialized;
- both source values are read before destination overwrite;
- result is a positive integer;
- division is exact;
- result does not exceed value_limit;
- target coverage is based on values actually produced;
- register count and instruction/serialization limits are respected.

The official evaluator is authoritative. Static graph reachability is only a search aid and is never accepted as proof that a serialized program is valid.

## 9. Experiment record

For every run, save:
- puzzle input hash and puzzle identifiers;
- solver commit and configuration;
- deterministic seed and compute budget;
- candidate DAG and serialized program hashes;
- instruction count, target coverage, and validation result;
- per-target production trace;
- intermediate reuse histogram;
- register pressure and schedule;
- baseline comparison and failure reason.

No score claim is valid without exact replay across the required puzzle set.

## 10. First falsifiable hypotheses

**H1 — shared-factor signal:** Target pairs with a non-trivial gcd are more likely than random matched pairs to admit a lower-cost shared-intermediate construction.

**H2 — intermediate leverage:** A small number of intermediate values account for a disproportionate share of useful target derivations.

**H3 — structural strata:** Puzzles with dense target-relation graphs benefit more from DAG selection than sparse puzzles.

**H4 — feature ablation:** Prime-valuation and residue features improve candidate ordering only if they outperform a simple exact-arithmetic graph baseline on held-out puzzles.

A hypothesis is rejected if its corresponding ablation does not improve held-out instruction cost under matched budgets.

## 11. Current execution boundary

This document is a research design, not an implementation or benchmark result. The previously recorded data-analysis restriction still blocks inspection of the authenticated candidate archive and full score decomposition. Do not route equivalent archive analysis through another executor. Repository documentation and static research design may continue; archive-dependent experiments resume only when the restriction clears.

## 12. Promotion gate

A Target DNA candidate may replace the incumbent only after:
1. exact validation on every required puzzle;
2. independent replay and reproducible hashes;
3. no regression in the aggregate objective;
4. source and license provenance review;
5. documented per-puzzle changes.

The 130,974 incumbent remains protected. The 100,000-instruction objective is aspirational, not a promised outcome. No Kaggle submission is made without explicit user approval.

## Implementation update — 23 November 2026

The first shared-intermediate planner now has three concrete engineering layers:

1. **Inverse target cones:** invert each missing target against the current value frontier to identify candidate intermediates that can unlock it. The inverse equations are regression-tested against brute-force exact arithmetic.
2. **Incremental recipe frontier:** seed the reachable pair-recipe table once, then add only pairs that involve newly available values. This avoids rebuilding all old-old pairs after every greedy selection. A regression test compares the incremental table with a complete rebuild on a fixed frontier.
3. **Register-aware lowering and replay:** lower the selected value DAG into the 48-register VM using last-use liveness, reject malformed DAG arithmetic before allocation, and replay the emitted instructions.

The test suite now includes inverse-cone equivalence, incremental-frontier equivalence, register-liveness behavior, malformed-DAG rejection, and end-to-end VM replay. The latest CI run passed on Python 3.10, 3.11, and 3.12.

**Evidence boundary:** these tests establish implementation correctness on their covered cases. They do not establish a reduction in the 130,974-instruction full-dataset incumbent. A full 1,000-puzzle run and exact score comparison remain required before promotion. The shared-intermediate planner is not yet a verified score improvement.

## Register-pressure-aware lowering — 23 November 2026

The register scheduler now performs a deterministic topological reordering before assigning physical registers. At each step it considers only operations whose operands are available, then prefers the operation that:

1. Leaves the fewest values with outstanding future uses;
2. Releases the greatest number of last-use operands;
3. Prefers a target-producing operation when the live-value cost is tied;
4. Uses stable result and original-position tie-breaks.

The ordering pass rejects cycles, unresolved dependencies, and duplicate produced values. The existing allocator then assigns one of the 48 physical registers, reusing a dead source register only after its final use, and independently replays the emitted instructions through the local arithmetic VM.

Regression coverage includes two interleaved dependency chains where the original topological order retains unnecessary live intermediates, a true two-node dependency cycle, missing dependencies, malformed arithmetic, and full VM replay. CI passed all 67 tests on Python 3.10, 3.11, and 3.12.

This improves the lowering layer's ability to fit a valid DAG into the register bank. It does not change the DAG's arithmetic instruction count and has not yet been shown to reduce the full competition score. The next research step is to make DAG selection itself aware of liveness, so candidate intermediates are priced by both target yield and the register pressure they create.

## Target-relevant frontier filtering — 23 November 2026

The greedy selector no longer scans every generated pair recipe at every round. It now scores only the union of:
- values that appear in the inverse target-cone index; and
- directly reachable missing targets.

All other one-step recipes have zero immediate target yield and cannot win the current greedy objective, so excluding them from the ranking loop preserves the selected candidate while reducing avoidable frontier scans. A deterministic regression assertion locks the chosen shared intermediate for the two-target fixture. CI passed all 67 tests on Python 3.10, 3.11, and 3.12.

The planner is still greedy and one-step. This optimization reduces ranking work; it does not establish a full-dataset instruction reduction.

