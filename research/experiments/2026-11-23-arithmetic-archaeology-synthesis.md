# Arithmetic archaeology: structural synthesis experiments

**Date:** 2026-11-23  
**Status:** Research design; no candidate score claimed  
**Protected incumbent:** 130,974 instructions  
**Target:** 100,000 instructions  
**Execution note:** This document defines experiments only. The authenticated archive and candidate programs have not been newly inspected in this phase.

## Thesis

Treat each puzzle as a constrained arithmetic circuit whose outputs are a set of required values. The goal is not simply to find a short expression for each target independently. It is to discover a compact *shared computation DAG within each puzzle* that generates many targets, while respecting positive-integer arithmetic, exact division, value limits, 48 registers, and the official evaluator.

The unconventional angle is to mine the geometry of the target set and the algebraic structure of intermediate values before searching instruction sequences.

## Experiment A — Target-set geometry

For each puzzle, represent every required target by several complementary signatures:

1. Prime-valuation vector: for each prime factor p, record v_p(n). This turns multiplication into vector addition and exact division into vector subtraction subject to nonnegative exponents.
2. Magnitude and logarithmic distance: use log(n), digit length, and ratios to neighboring targets.
3. Residue fingerprint: n mod m for a fixed bank of small moduli, chosen before evaluation.
4. Additive/multiplicative neighborhood: count pairs (a,b) from initial values and targets for which a+b=n, |a-b|=n, ab=n, or a/b=n under exact divisibility.
5. Shared-factor graph: connect targets with gcd greater than one; annotate edges by quotient and gcd.

Cluster and rank targets by these signatures. The signatures are search heuristics only; they do not establish that two targets share a cheap construction.

**Test:** On a fixed development split, compare target ordering and candidate-generation yield against the incumbent ordering and a simple magnitude ordering. Report exact instruction cost, valid-target coverage per search budget, and held-out performance.

## Experiment B — Algebraic motif mining

Build a DAG from each valid program. Canonicalize commutative operands, preserve operation and value semantics, and identify recurring motifs:

- multiply then add/subtract (affine forms);
- multiply then exact divide (ratio simplification);
- repeated doubling/halving chains;
- shared products feeding several sums;
- difference-of-products patterns;
- factor-and-recombine patterns;
- repeated constructions of the same value through different paths.

Mine motifs across puzzles as *parameterized recipes*. Each recipe must carry explicit preconditions: operand positivity, exact divisibility, value-limit safety, and any ordering assumptions. A recipe is useful only if it reduces exact instruction count on held-out puzzles.

## Experiment C — Reverse target cones

For a target t, enumerate algebraically possible final operations:

- addition: t = a + b;
- subtraction: t = a - b or t = b - a, with positive result;
- multiplication: t = a*b;
- exact division: t = a/b or t = b/a.

Use known initial values, other required targets, and forward-reachable frontier values as candidate operands. Rank predecessor pairs using target-set geometry and shared-DAG potential. Continue backward only when a predecessor has a plausible low-cost construction.

Avoid unsound state merging: two states are equivalent only if their register contents, covered-target set, and all relevant constraints are equivalent under a proved canonicalization.

**Test:** Compare against matched forward search on the same puzzle subset, time budget, and evaluator. Measure best exact cost and improvement rate, not number of explored states alone.

## Experiment D — Target hypergraph and set cover

A candidate arithmetic DAG can produce multiple required targets. Model each verified DAG fragment as a hyperedge from its prerequisite values to the set of targets it produces. Search for combinations with low total instruction cost, accounting for prerequisite construction and register pressure.

This is not ordinary set cover: hyperedges have dependencies, may share subexpressions, and can become infeasible under the register/value constraints. Use integer programming or bounded branch-and-bound only after a sound cost model is defined.

**Test:** For small puzzle instances, compare the optimizer's chosen DAG with exhaustive enumeration or a trusted lower bound. Then scale to high-overhead puzzles.

## Experiment E — Search by marginal target yield

For every partial program state, estimate the marginal cost of covering each remaining target and the number of other targets likely to benefit from the same intermediate. Prioritize operations with high expected downstream target yield, not just immediate target hits.

Keep heuristic estimates separate from exact objective values. Use beam search, Pareto frontiers, or evolutionary selection over:
- exact instructions used;
- targets covered;
- live-register pressure;
- reusable intermediate frontier;
- diversity of construction motifs.

**Test:** Ablate each heuristic independently. Use deterministic seeds and equal compute budgets. Reject a heuristic if its gains disappear on held-out puzzles.

## Required instrumentation

For each experiment record puzzle hash, evaluator hash, source commit, seed, budget, per-puzzle baseline and candidate score, validity, output hash, and provenance. Also record:
- number of newly covered targets per instruction;
- non-target intermediate count;
- duplicate values;
- dead values;
- maximum live values;
- motif frequencies;
- target-family coverage;
- time to first improvement and best-so-far curve.

A target may later serve as an intermediate. Count its instruction once as a target-producing instruction and separately record its downstream use; do not double-count instruction categories.

## Stop/go criteria

- **Go:** reproducible exact savings on held-out puzzles, with no validity failures and a traceable transformation/search path.
- **Pivot:** attractive motif statistics but no exact cost reduction after equal-budget tests.
- **Stop:** gains depend on evaluator mismatch, puzzle leakage, unlicensed source material, or unrepeatable stochastic outcomes.

## Immediate dependency

The authenticated source archive must be inspected when the data-analysis restriction clears. Until then, do not claim these experiments have run, do not infer archive contents, and do not use another execution route to perform equivalent blocked analysis.

## Submission boundary

The 130,974 incumbent remains frozen. No experimental output replaces it until the full 1,000-puzzle candidate is serialized, independently replayed, audited for provenance, and shown to improve the exact score. No Kaggle submission is authorized by this research plan.
