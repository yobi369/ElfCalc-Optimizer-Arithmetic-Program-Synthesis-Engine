# Search diversity and frontier economics tournament

Date: 2026-11-24

## Question

Does preserving arithmetic provenance and reserving beam slots for structurally
different first-step recipes improve solution quality under a fixed declared
beam budget? Does exact frontier caching reduce repeated generation work?

## Design

The synthetic tournament crosses three beam configurations with caching on/off (six configurations per fixture):

1. Original-style deduplication + ordinary global-rank admission.
2. Provenance-aware identity + ordinary global-rank admission.
3. Provenance-aware identity + first-intermediate diversity reservation.

Each configuration is run with the same fixture-specific depth, beam width,
intermediate cap, and per-state expansion cap. Complete-witness and partial-
motif side searches are disabled so they cannot confound the beam comparison.

Four synthetic families are included: shared-factor subset coverage, two-stage
shared bridge, multiple target families with direct and shared yields, and a
provenance collision where distinct recipes produce the same value frontier.

Every result is passed through register scheduling and independently validated
against a synthetic puzzle containing exactly the covered targets. The
scheduler also performs its own local VM replay. Metrics include target
coverage, instruction count, peak live values, frontier requests,
candidate-state proposals, actual frontier generations, and elapsed time.

## Budget and measurement caveats

This is a controlled declared-budget experiment, not a claim of equal CPU
instructions. The planner's per-state recipe cap and beam width are identical
across configurations. Provenance and diversity change which candidates
survive, while caching changes the cost of obtaining a recipe frontier.

candidate_state_proposals counts child-state key evaluations; it is not the
number of states fully expanded. frontier_requests counts requests for
one-step recipe lists. frontiers_generated counts actual calls to the underlying
recipe generator, including cache misses. The cache-enabled wrapper is
instrumented beneath the LRU cache so cache hits are not miscounted as
generations. Wall-clock time is descriptive and runner-sensitive.

The test asserts that cache on/off cannot change deterministic plan quality and
that caching does not increase actual frontier generation. It prints the full
result matrix for CI logs. Timing comparisons should be repeated on the same
machine before drawing performance conclusions.

## Interpretation gates

- Provenance awareness is useful only if it improves coverage or lowers cost
  on at least one fixture without unacceptable frontier growth.
- Diversity reservation is useful only if it improves quality over provenance
  alone at the same beam width.
- Caching is useful only if it reduces actual frontier generations and/or
  stable-machine runtime without changing results.
- No strategy is promoted based on diversity counts alone.

## Initial tournament result

CI run 45348542333 passed on Python 3.10, 3.11, and 3.12. Its initial counters
showed caching reduced measured frontier generations to zero, but code review
found that the counter was not instrumented beneath the cache. That measurement
is invalid and was corrected before drawing any caching conclusion.

On the four initial fixtures, diversity reservation did not improve coverage,
instruction count, or peak-live pressure over provenance-only admission. In
the provenance-collision fixture, provenance-aware search retained a more
expensive proposal (5 rather than 4 instructions) at the same coverage. This
is a useful warning: preserving provenance can increase search cost without
helping every instance.

## Real-planner end-to-end ablation

A second test invokes the actual `plan_bounded_beam` entry point twice per
fixture. It switches only the beam-admission selector: ordinary global-rank
selection versus the production diversity selector. Provenance-aware state
identity, Pareto filtering, target-cone guidance, and the declared search
limits remain active in both arms. Complete-witness and partial-motif searches
are disabled. Both arms are checked by register scheduling and exact VM
validation for all covered targets.

CI run 45353027624 passed on Python 3.10, 3.11, and 3.12. The Python 3.11 log
recorded these metrics as (covered targets, instruction count, peak live,
missing targets):

| Synthetic family | Ordinary admission | Diversity reservation |
|---|---:|---:|
| shared_factor | (3, 5, 2, none) | (3, 5, 2, none) |
| shared_bridge | (2, 5, 2, none) | (2, 5, 2, none) |
| multi_family | (4, 5, 2, 99) | (4, 5, 2, 99) |
| provenance_collision | (2, 5, 2, 35) | (2, 5, 2, 35) |
| deep_power | (1, 3, 1, none) | (1, 3, 1, none) |

**Result:** diversity reservation produced no quality improvement on any of
these five end-to-end fixtures. It also did not degrade the measured solution
quality. This is a neutral result, not evidence that diversity is generally
beneficial. The earlier adversarial unit tests establish that reservation can
preserve a branch with a valid multi-step completion that ordinary top-k
selection discards, but that constructed mechanism has not translated into
better output on these naturally ranked planner fixtures.

## Adaptive admission ablation

The adaptive selector begins with ordinary global-rank admission. It intervenes
only if the selected beam contains duplicate first-recipe roots and an excluded
distinct-root state has strictly greater immediate target yield than the
weakest selected state. It replaces only that weakest state. This is a bounded
heuristic; immediate yield is not a proof of future solvability.

CI run 45353886026 passed all 111 tests on Python 3.10, 3.11, and 3.12. Its
end-to-end synthetic ablation produced identical quality metrics for ordinary,
always-diverse, and adaptive admission:

| Synthetic family | Coverage | Instructions | Peak live |
|---|---:|---:|---:|
| shared_factor | 2 | 3 | 2 |
| shared_bridge | 1 | 2 | 1 |
| multi_family | 4 | 5 | 2 |
| provenance_collision | 2 | 5 | 2 |

All three policies matched on every family. The adversarial selector test
continues to show the intended branch-preservation mechanism, but the broader
synthetic results provide no evidence of a natural quality advantage. Keep
both diversity policies experimental; ordinary admission remains the
recommended default absent stronger evidence.

## Corrected cache economics observations

The corrected tournament's CI log shows that the 256-entry LRU frontier cache
substantially reduces actual recipe-frontier generation while preserving
quality. Selected examples:

| Family / strategy | Cache off: generations | Cache on: generations | Reduction |
|---|---:|---:|---:|
| shared_factor / original-style | 423 | 67 | 84.2% |
| shared_bridge / original-style | 1,038 | 201 | 80.6% |
| multi_family / original-style | 5,587 | 1,312 | 76.5% |
| multi_family / provenance | 5,948 | 731 | 87.7% |
| provenance_collision / provenance | 2,070 | 250 | 87.9% |

These are synthetic fixture counts, not competition-scale measurements.
Wall-clock improvements are smaller and runner-dependent; the evidence
supports caching as a reduction in repeated frontier construction, not a claim
of equivalent end-to-end speedup.

## Cache working-set capacity sweep

The follow-up sweep compared capacities 0 (disabled), 32, 64, 128, 256, 512,
and 1,024 across four fixtures in forward and reverse fixture order (56 planner
runs). CI run 45356337448 passed on Python 3.10, 3.11, and 3.12; Python 3.11
reported 112 passing tests. Every capacity produced the same per-fixture
coverage, instruction count, peak-live estimate, and missing-target set, and
every returned plan passed register scheduling and exact VM validation.
Forward/reverse order produced identical capacity-zero quality baselines.

Representative generation counts from the forward-order run:

| Fixture | Capacity 0 | 32 | 64 | 128 | 256 | 512 | 1,024 |
|---|---:|---:|---:|---:|---:|---:|---:|
| shared_factor | 478 | 70 | 67 | 67 | 67 | 67 | 67 |
| shared_bridge | 1,057 | 134 | 128 | 127 | 127 | 127 | 127 |
| multi_family | 5,622 | 1,362 | 1,180 | 1,090 | 969 | 954 | 954 |
| provenance_collision | 2,122 | 332 | 310 | 255 | 255 | 255 | 255 |

The capacity curve has a clear elbow. A 64-entry cache captures almost all
reuse in shared_factor; 128 captures the observed working set in shared_bridge
and provenance_collision; multi_family benefits through 256, with only a
small further reduction at 512 and none at 1,024. Capacity 256 is therefore a
reasonable compromise for these synthetic workloads: it captures most of the
measured reuse without retaining the larger 512/1,024-entry working sets.
This is a synthetic recommendation, not proof of the optimal competition
capacity.

Cache hits, misses, current size, and inferred evictions were recorded. The
test does not directly measure memory bytes. Wall-clock times varied little
and were not consistently monotonic with capacity, so no runtime-speedup claim
is made. The principal demonstrated benefit is reduced repeated frontier
generation with invariant plan quality.

## Cache replacement-policy tournament

CI run 45360112421 passed on Python 3.10, 3.11, and 3.12. It compared LRU,
FIFO, and LFU at capacities 64, 128, and 256 across the three higher-branching
fixtures. All 27 configurations produced identical plan-quality tuples within
each fixture and passed exact VM validation.

Actual frontier generations:

| Fixture | Capacity | LRU | FIFO | LFU |
|---|---:|---:|---:|---:|
| overlapping_target_cones | 64 | 523 | 534 | 748 |
| overlapping_target_cones | 128 | 476 | 489 | 624 |
| overlapping_target_cones | 256 | 428 | 431 | 433 |
| multi_route_shared_values | 64 | 411 | 420 | 549 |
| multi_route_shared_values | 128 | 329 | 344 | 366 |
| multi_route_shared_values | 256 | 314 | 314 | 314 |
| dense_factorial_branching | 64 | 550 | 556 | 828 |
| dense_factorial_branching | 128 | 507 | 518 | 665 |
| dense_factorial_branching | 256 | 435 | 438 | 456 |

LRU generated the fewest or tied for fewest frontiers in all nine comparisons.
FIFO was close, with a small generation penalty in most cases. LFU was
consistently worse, especially at smaller capacities; a plausible explanation
is that one-off high-frequency entries can remain resident while recently
reused working-set entries are evicted. This explanation is a hypothesis, not
a separately proven mechanism.

Runner timing agrees directionally that LFU has extra overhead, but absolute
elapsed times varied across Python versions and jobs. Do not infer a reliable
wall-clock speedup from this single CI matrix. The stronger result is that LRU
minimizes recomputation in these fixtures without changing output quality.

**Decision:** retain LRU as the cache replacement policy. No evidence justifies
the added complexity of LFU or replacing LRU with FIFO.


## 2Q scan-resistant cache tournament

CI run 45362079641 passed on Python 3.10, 3.11, and 3.12. The corrected run
reported 116 passing tests on each interpreter. It compared 2Q with LRU and
FIFO at capacities 64, 128, and 256 on the three higher-branching fixtures.
All configurations preserved identical plan-quality tuples within each
fixture, and returned plans passed exact scheduling/VM validation. The
adversarial scan-resistance test also passed: four repeatedly accessed hot
entries were promoted and survived a 40-key one-pass scan.

Actual frontier generations:

| Fixture | Capacity | LRU | FIFO | 2Q |
|---|---:|---:|---:|---:|
| overlapping_target_cones | 64 | 523 | 534 | 963 |
| overlapping_target_cones | 128 | 476 | 489 | 713 |
| overlapping_target_cones | 256 | 428 | 431 | 438 |
| multi_route_shared_values | 64 | 411 | 420 | 680 |
| multi_route_shared_values | 128 | 329 | 344 | 413 |
| multi_route_shared_values | 256 | 314 | 314 | 322 |
| dense_factorial_branching | 64 | 550 | 556 | 988 |
| dense_factorial_branching | 128 | 507 | 518 | 843 |
| dense_factorial_branching | 256 | 435 | 438 | 460 |

2Q generated more frontiers than LRU in all nine comparisons. At capacities
64 and 128 the penalty was substantial; at 256 it was smaller but remained
consistent. The scan-resistance micro-test demonstrates the policy's intended
mechanism, but that mechanism did not translate into lower recomputation on
these planner workloads. Timing was runner-dependent and is not used to claim
a stable performance difference.

**Decision:** retain the existing 256-entry LRU cache. Keep 2Q as a tested
alternative only; do not integrate it into the planner. The cache-policy
evidence now favors LRU over FIFO, LFU, and 2Q on the tested synthetic
families, while none of these experiments establishes competition-scale
optimality.

## Updated decision and next direction

The cache replacement-policy branch is complete for the current synthetic
workloads. Avoid further cache-policy variants unless a new access-pattern
hypothesis predicts a measurable benefit. The next research direction should
move back toward arithmetic search quality rather than cache micro-optimization:
design a controlled experiment that increases search diversity only when a
target-cone or shared-subgraph signal predicts a concrete missing-target
completion, then compare it against ordinary admission with exact replay.
Keep it experimental until it improves more than adversarial hand-built cases.

The competition archive remains uninspected in this research phase. The
130,974-instruction incumbent remains frozen, and no Kaggle submission has
been made.
