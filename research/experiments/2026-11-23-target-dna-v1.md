# Target DNA v1: arithmetic fingerprints and shared-intermediate discovery

**Date:** 2026-11-23  
**Status:** Research specification; implementation and score impact not yet measured  
**Protected incumbent:** 130,974 instructions  
**Research target:** 100,000 instructions  
**Dependency:** Run on the pinned puzzle set only when the documented data-analysis restriction clears.

## 1. Research question

Can we infer a compact arithmetic dependency structure from the starting values and required targets of each puzzle, then use that structure to prioritize shared intermediate values?

The object of optimization is a valid arithmetic computation DAG per puzzle. Cross-puzzle learning transfers recipes and ranking models only; register state is never shared between puzzles.

## 2. Three complementary DNA representations

For a puzzle with starting-value set S and target set T, build a fingerprint for each distinct value n in S union T.

### 2.1 Multiplicative DNA

Record:

- gcd(n, x) for selected x in S union T;
- exact quotient n/gcd(n,x), where defined;
- whether n divides x or x divides n;
- small-prime valuations v_p(n) for a fixed, declared prime bank;
- optional complete factorization only when obtained within a bounded factorization budget.

Prime valuations are useful because multiplication adds exponent vectors and exact division subtracts them. They are not mandatory: complete factorization of arbitrary 64-bit values can be expensive. The engine must retain a non-factorization fallback based on gcd and exact quotient relations.

### 2.2 Additive DNA

For pairs a,b from the current frontier F:

- a+b when within the value limit;
- positive |a-b| when nonzero;
- target gaps t-a and t-b when positive;
- whether a target is a one-operation result of two frontier values.

Use sorted values and bounded pair-generation rather than an unrestricted quadratic expansion on every state.

### 2.3 Computational DNA

For each value and candidate recipe, record:

- minimum known construction cost;
- prerequisite values;
- number of targets potentially reachable downstream;
- whether the recipe has been validated under positivity, exact division and value limits;
- estimated live-register demand;
- motif identity (e.g. shared product, affine transform, quotient chain).

A fingerprint is a search heuristic, not proof that two targets admit a cheaper shared program.

## 3. Target relation graph

Create a directed, typed graph over values.

An edge or hyperedge represents a *verified one-instruction relation*:
- (a,b) -> a+b
- (a,b) -> a-b when a>b
- (a,b) -> a*b when the product is within the puzzle limit
- (a,b) -> a/b when b is nonzero and divides a exactly
- reverse operand order where it changes the operation's validity or result.

Each edge stores operation, operands, result, and exact preconditions. Canonicalize operand order only for commutative operations (+ and *). Do not canonicalize subtraction or division as commutative.

Starting values are zero-cost roots. Required targets are marked terminals. A target may also be an internal node for later constructions.

## 4. Shared-intermediate value score

For a candidate intermediate x, estimate its utility using:

- target reachability: number of currently uncovered targets whose cheapest known construction can use x;
- marginal instruction cost: estimated cost to construct x plus downstream savings;
- reuse count: number of distinct useful target recipes consuming x;
- register burden: peak simultaneous live values induced by those recipes;
- risk: value-limit, exact-division, or uncertain-recipe constraints.

A first ranking heuristic is:

utility(x) = downstream_target_weight(x) * reuse_count(x)
             - construction_cost(x) - register_penalty(x) - risk_penalty(x)

Weights must be selected on a development split and evaluated on held-out puzzles. This utility is not the official objective; exact serialized instruction count remains authoritative.

## 5. Search procedure

For each puzzle:

1. Initialize the frontier with distinct starting values and mark targets already present.
2. Build bounded additive and multiplicative relation indexes.
3. Generate one-step target recipes from frontier pairs.
4. Generate candidate intermediates that participate in multiple target recipes.
5. Rank intermediates by marginal target yield and estimated cost.
6. Expand only a bounded top-k set, retaining Pareto alternatives over instruction cost, covered targets, and live-register demand.
7. Recompute exact dependencies when a new value is admitted.
8. Emit a candidate DAG only after all required targets have construction paths.
9. Schedule and allocate the DAG under the 48-register constraint.
10. Serialize and validate using the official evaluator.

### Pseudocode

```text
frontier := starting_values
covered := targets intersect frontier
recipes := empty
while uncovered_targets remain and budget remains:
    relations := enumerate_valid_one_step_relations(frontier)
    recipes += relations that produce uncovered targets
    candidates := intermediates_used_by_multiple_promising_recipes
    candidates += bounded_reverse_predecessors(uncovered_targets, frontier)
    x := argmax marginal_utility(candidates)
    if x is not already in frontier:
        add best validated construction for x
        frontier.add(x)
    update target coverage and Pareto states
schedule best complete dependency DAG
exact_replay(serialized_program)
```

This is a research outline, not executable code. The implementation must define bounded enumeration, state identity, dominance, and register scheduling precisely before benchmarking.

## 6. Soundness requirements

Every generated instruction must satisfy all of the following:

- both source registers are initialized before the instruction;
- source values are read before destination overwrite;
- result is a positive integer;
- division is exact and denominator nonzero;
- result does not exceed the puzzle value limit;
- register allocation respects the 48-register limit;
- the official evaluator confirms target coverage and instruction count.

Do not merge search states merely because they have the same set of computed values. Register placement, live values, covered targets, and remaining constraints may make states behaviorally different. Any state canonicalization or dominance rule requires a proof or exhaustive bounded validation.

## 7. First falsifiable experiments

### Experiment TDNA-01: fingerprint-only target ordering
Compare incumbent target order, magnitude order, and DNA-ranked order under the same search budget. Measure exact instruction cost and improvement rate on held-out puzzles.

### Experiment TDNA-02: shared-intermediate ranking
Compare a baseline that selects the next target independently against a selector that rewards intermediates used by multiple target recipes. Keep beam width, time budget, and seed schedule matched.

### Experiment TDNA-03: factorization ablation
Compare gcd/quotient-only fingerprints, bounded small-prime valuations, and optional complete factorization on a fixed subset. Record factorization time separately; reject complete factorization if its overhead outweighs search gains.

### Experiment TDNA-04: register-aware selection
Compare utility without register penalty against utility with estimated live-value pressure. Confirm with actual schedule and evaluator, because a low-cost DAG may still be infeasible under 48 registers.

For every experiment, preserve:
- pinned puzzle and evaluator hashes;
- source commit and deterministic seed;
- fixed development/held-out split;
- compute budget and runtime;
- per-puzzle baseline and candidate costs;
- valid/invalid counts;
- serialized candidate hash and exact replay report.

## 8. What would count as success?

A statistically attractive fingerprint or cluster is not a result by itself. Success requires reproducible instruction savings on held-out puzzles under matched compute budgets, followed by a complete 1,000-puzzle exact replay and provenance audit.

The first milestone is to beat the 130,859 external candidate with a fully verified, provenance-cleared portfolio. The 130,974 incumbent remains protected until that condition is met.

## 9. Current execution boundary

This document advances the research design only. It does not claim that the archive has been inspected, that code has been implemented, or that a new score has been measured. The previously documented data-analysis restriction remains in force; do not use another executor to perform equivalent blocked archive analysis. Resume implementation and experiments when that restriction clears.

No Kaggle submission is authorized by this document.
