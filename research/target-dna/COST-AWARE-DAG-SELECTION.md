# Cost-Aware Value-DAG Selection — Research Design

**Status:** design specification; not yet benchmark-validated  
**Date:** 2026-11-24  
**Baseline protection:** the 130,974-instruction incumbent remains frozen until a complete exact replay proves a better candidate.

## Why this research exists

The current shared-intermediate planner primarily ranks a candidate by immediate target yield. Its serial-chain and cooperating-pair fallbacks each spend two intermediate instructions and then choose the alternative with the larger number of unlocked targets.

That is a useful coverage heuristic, but it does not fully price the downstream cost of the resulting DAG. Two fragments that cover the same number of targets can differ in:

- total arithmetic instructions;
- number of speculative intermediates;
- reuse of each intermediate across targets;
- peak number of simultaneously live values;
- register-allocation feasibility under the 48-register limit;
- future opportunities created or blocked by the new frontier.

A cost-aware selector should compare complete, replayable fragments rather than isolated recipe counts.

## Proposed objective

For a candidate fragment (F), track a vector rather than prematurely collapsing every concern into one arbitrary scalar:

[
C(F) = ( -T(F), I(F), P(F), L(F), -R(F) )
]

Where:

- (T(F)): distinct newly covered targets;
- (I(F)): total instructions, including target-producing operations;
- (P(F)): speculative intermediate instructions;
- (L(F)): estimated peak live values during a valid topological schedule;
- (R(F)): reuse benefit, measured as the number of downstream target operations supported per intermediate.

Use Pareto dominance first. Candidate A dominates B only when A is no worse on every dimension and strictly better on at least one. Keep non-dominated alternatives for the next planning decision where the search budget permits.

For deterministic selection from a bounded frontier, use lexicographic policy:
1. maximize newly covered targets;
2. minimize total instructions per newly covered target;
3. minimize speculative intermediates;
4. minimize peak live values;
5. maximize intermediate reuse;
6. stable recipe-order tie-break.

Do not treat this ordering as a proof of global optimality. It is an explicit, testable policy.

## Peak-live estimate

For each candidate fragment:

1. Build its value dependency DAG, with starting values available at time zero.
2. Count remaining operand uses for every value.
3. At each step, consider only operations whose operands are available.
4. Simulate the deterministic liveness scheduler's choice rule.
5. Decrement operand use counts, add the produced result, and count values with outstanding future uses.
6. Record the maximum live count.
7. Reject malformed fragments with cycles, missing dependencies, or duplicate results.

The estimate must use the same readiness and liveness semantics as the actual register scheduler. The actual scheduler and VM replay remain the final authority. Peak live values are a pressure indicator, not a replacement for physical register allocation.

## Candidate fragment construction

Represent each alternative as a complete fragment:
- its intermediate recipes;
- its target recipes;
- the set of newly covered targets;
- its instruction count;
- its intermediate count;
- its estimated peak liveness.

For the existing two-hop fallback, compare:
- first intermediate → bridge intermediate → targets;
- independent intermediate A + intermediate B → targets.

The fragments currently have equal speculative intermediate cost, but their target-operation counts and live-value profiles can differ. The same interface should later support bounded three-operation motifs without introducing an unbounded Cartesian search.

## Safety and correctness invariants

- Every arithmetic result must be exact, positive, and within the puzzle value limit.
- A missing target must never be used as a speculative intermediate merely because it is also a desired output.
- Each fragment must be a valid DAG with no duplicate produced values.
- The register scheduler must lower it into the 48-register machine.
- The local VM must replay the emitted program.
- The official evaluator remains authoritative.
- No candidate replaces the frozen incumbent until all scored puzzles have been replayed and aggregate instruction count and serialized size have been verified.
- No Kaggle submission is made without explicit user approval.

## Test plan

1. Peak-live estimator agrees with hand-calculated small DAGs.
2. A serial chain and cooperating pair with equal target yield are ranked by measured live pressure.
3. Lower instruction cost wins when target coverage is equal.
4. More target coverage wins only according to the declared policy, with cost-per-target as the next discriminator.
5. Equal-cost/equal-pressure alternatives resolve deterministically.
6. Cycles, missing dependencies, duplicate results, and invalid arithmetic are rejected.
7. Selected fragments pass register scheduling and exact VM replay.
8. Existing planner and scheduler regression tests remain green.

## Benchmark protocol

Do not infer score improvement from unit tests or synthetic fixtures. When authorized data-analysis access is available:

- run the frozen incumbent and candidate on the identical complete puzzle set;
- record per-puzzle instruction deltas, coverage, and serialized byte counts;
- report wins, ties, losses, aggregate delta, worst regressions, and runtime;
- preserve the incumbent if any correctness, size, or replay check fails;
- archive the exact code revision and experiment configuration.

## Current evidence boundary

This document is a research design, not a measured result. No full-dataset benchmark is claimed here. The current verified aggregate remains 130,974 instructions.
