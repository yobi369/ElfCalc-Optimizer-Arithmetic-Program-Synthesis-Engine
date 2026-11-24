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
one-step recipe lists. frontiers_generated counts actual calls to the underlying recipe generator, including cache misses. The cache-enabled wrapper is instrumented beneath the LRU cache so cache hits are not miscounted as generations. Wall-clock time is descriptive and runner-sensitive.

The test asserts that cache on/off cannot change deterministic plan quality and that caching does not increase actual frontier generation. It prints the full result matrix for CI logs. Timing comparisons should be
repeated on the same machine before drawing performance conclusions.

## Interpretation gates

- Provenance awareness is useful only if it improves coverage or lowers cost
  on at least one fixture without unacceptable frontier growth.
- Diversity reservation is useful only if it improves quality over provenance
  alone at the same beam width.
- Caching is useful only if it reduces actual frontier generations and/or
  stable-machine runtime without changing results.
- No strategy is promoted based on diversity counts alone.

## Initial CI result and interpretation

CI run 45348542333 passed on Python 3.10, 3.11, and 3.12. Its initial counters
showed caching reduced measured frontier generations to zero, but code review
found that the counter was not instrumented beneath the cache. That measurement
is therefore invalid and is being corrected before drawing any caching conclusion.

On the four initial fixtures, diversity reservation did not improve coverage,
instruction count, or peak-live pressure over provenance-only admission. In
the provenance-collision fixture, provenance-aware search retained a more
expensive proposal (5 rather than 4 instructions) at the same coverage. This is
a useful warning: preserving provenance can increase search cost without
helping every instance. These small fixtures do not establish a general result.

This is synthetic-only research. It does not inspect the competition archive,
change the production solver, alter the frozen 130,974-instruction incumbent,
or submit to Kaggle.
