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

## Decision and next experiment

Keep ordinary beam admission as the default; diversity and adaptive
reservation remain experimental because no natural synthetic quality gain has
been demonstrated. Retain the existing 256-entry cache as a sensible
synthetic working-set compromise, but do not claim it is competition-optimal
or tune the production solver solely from these fixtures.

The next experiment should broaden the synthetic fixture bank toward larger
DAGs and repeated-frontier patterns, especially cases with overlapping target
cones, high arithmetic branching, and multiple independent routes to shared
intermediates. Compare cache capacities around the observed elbow (64, 128,
256, 512) under fixed declared search limits. Measure generation counts,
hits/misses/evictions, quality, and repeated wall-clock samples on a stable
machine if available. Do not integrate new beam heuristics or change production
settings until evidence is repeatable.

The competition archive remains uninspected in this research phase. The
130,974-instruction incumbent remains frozen, and no Kaggle submission has
been made.
