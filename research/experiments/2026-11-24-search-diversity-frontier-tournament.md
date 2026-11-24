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

Every result is passed through register scheduling and independently validated against a synthetic puzzle containing exactly the covered targets. The scheduler also performs its own local VM replay.
Metrics include target coverage, instruction count, peak live values, frontier
requests, candidate-state proposals, actual frontier generations, and elapsed
time.

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

## Decision and next experiment

Do not promote diversity reservation into the production solver on this
evidence. Keep it experimental. The next useful test is an adaptive selector:
reserve a distinct-root slot only when the current top-ranked beam is
structurally concentrated and the candidate alternative has demonstrable
multi-step target support. Compare ordinary, always-diverse, and adaptive
admission under the same declared budget on a broader deterministic synthetic
fixture bank. Measure coverage, instruction count, peak-live pressure, state
proposals, frontier generations, and runtime. The adaptive policy must show
a repeatable quality gain before it is considered for production.

This remains synthetic-only research. The competition archive has not been
re-inspected, the frozen 130,974-instruction incumbent is unchanged, and no
Kaggle submission has been made.


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

The corrected tournament's CI log also shows that the 256-entry LRU frontier
cache substantially reduces actual recipe-frontier generation while
preserving quality. Selected examples:

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
of equivalent end-to-end speedup. Cache hits, misses, and evictions were not
yet recorded as a full memory/working-set profile.

## Next experiment: cache working-set economics

Hold the search policy fixed and compare cache capacities 0 (disabled), 32,
64, 128, 256, 512, and 1,024 on a larger deterministic synthetic fixture
bank. Record cache hit/miss/current-size statistics, actual frontier
generations, elapsed time, and peak memory if a reliable measurement is
available. Repeat fixtures in a fixed order and reverse order to expose order
sensitivity. Every capacity must produce identical plan-quality metrics and
exact VM replay. The aim is to identify the smallest cache that captures most
reusable work without unnecessary memory retention. No production change
until the measured working-set curve justifies it.

The competition archive remains uninspected in this research phase. The
130,974-instruction incumbent remains frozen, and no Kaggle submission has
been made.
