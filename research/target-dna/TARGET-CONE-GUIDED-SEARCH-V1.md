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

## Witness-guided shared-subgraph proposals

The experimental planner now has a bounded witness-construction path in addition to its beam-ranking heuristics. For each bounded first recipe, it enumerates a capped second-recipe frontier, then checks whether the two intermediates jointly expose every currently missing target. A successful witness stores the actual PlannedOperation sequence, including operand dependencies, rather than only a score or candidate-value signal.

Every witness is passed through schedule_value_dag, which performs register allocation and local VM replay before it can be returned. The path is bounded by 128 first recipes and 256 second recipes per first recipe, and is eligible only when the caller's intermediate and depth budgets permit two intermediates plus the target-producing operations. It remains experimental; it is not integrated into the production solver and has not been evaluated against the scored competition archive.

Synthetic witness:
- Starts: 2, 3
- Intermediates: 5 (= 2 + 3), 7 (= 5 + 2)
- Targets: 12 (= 5 + 7), 35 (= 5 * 7)
- Four total instructions; exact scheduler/VM replay required.

CI run for commit d81e64a562eff3ee07106a7a309cca6c4e832f47 passed on Python 3.10, 3.11, and 3.12:
https://github.com/yobi369/ElfCalc-Optimizer-Arithmetic-Program-Synthesis-Engine/actions/runs/45343171796

## Alternative witness selection

The witness path now retains a bounded set of concrete two-intermediate proposals (up to 64) instead of returning the first schedulable proposal. Each candidate must pass register scheduling and local VM replay. Verified proposals are ranked by instruction count, estimated peak live values, and a deterministic structural tie-break. This creates an explicit cost-versus-register-pressure selection point while preserving reproducibility. The witness enumeration remains capped at 128 first recipes and 256 second recipes per first recipe; reaching the witness cap stops enumeration, so this is not an exhaustive search or global optimum proof.

A regression test checks that the 2,3 -> 5,7 -> 12,35 witness is concrete, deterministic, and accepted by the scheduler/VM replay.

## Bounded multi-stage motif witnesses

The concrete witness constructor has been generalized from exactly two intermediates to a bounded deterministic depth-first value-DAG search. It grows one non-target intermediate at a time, checks after each stage whether the currently available values jointly expose all missing goals, and caps branching at 128 recipes per state, total visited states at 4,096, and retained witnesses at 64. The planner derives the intermediate budget from both the caller's intermediate limit and remaining instruction depth after reserving one final instruction per missing target.

Every returned witness is still passed through the register scheduler and exact local VM replay. Verified alternatives are ranked by instruction count, estimated peak live values, and deterministic structure. A regression fixture uses starts 2 and 3 to build 5, 25, and 125, then unlocks targets 250 and 375. A two-intermediate search is expected not to find that fixture; a three-intermediate search must.

This expands the bounded motif horizon; it does not make the search complete, globally optimal, or suitable for production integration without further benchmarking.

## Partial motif yield-density search

Added `_partial_subgraph_motifs`, a bounded deterministic search that records a motif whenever its currently available values expose one or more missing targets, then continues expanding the DAG to see whether additional targets can be unlocked. It ranks proposals by exact target yield per emitted instruction (`covered_targets / instruction_count`), then absolute coverage, instruction count, and deterministic structure. Bounds are 128 recipes per state, 4,096 visited states, and 128 retained proposals by default. Every selected proposal is passed through register scheduling and local VM replay.

The planner compares these partial proposals against its best incomplete beam state and can return a verified partial plan with explicit covered and missing target sets. A regression fixture uses starts 2 and 3: the intermediate 6 unlocks 12 and 18 in two additional operations, while 99 remains uncovered. This is an objective-aligned local heuristic, not a guarantee of globally optimal target coverage or instruction count. It remains experimental and is not wired into the production solver.

## Controlled strategy comparison

The experimental planner now exposes independent switches for complete-witness proposals and partial-yield motif proposals. This permits synthetic comparisons among beam-only, beam plus complete witnesses, and beam plus partial motifs while holding the beam width, depth, intermediate budget, and per-state expansion cap constant. A regression test runs all three modes on the same 2,3 → {12,18,99} fixture and validates every returned plan through the register scheduler and VM replay.

The planner exposes shared motif-search caps (`motif_state_budget`, `motif_recipe_budget`, and `motif_result_budget`) so both auxiliary methods can be run under identical declared state, branching, and retained-result limits. The regression fixture uses 128 states, 16 recipes per state, and 16 retained results for either auxiliary method, alongside identical beam limits. This is still not a fully equal wall-clock or primitive-operation budget: candidate generation and scoring costs differ by method. Results must therefore be reported with that caveat. The test asserts correctness and coverage accounting, not that one strategy always wins. No competition archive was used.

### First synthetic comparison results (2026-11-24)

The controlled comparison now covers two fixtures, all three strategies, and Python 3.10/3.11/3.12 CI environments. All plans were register-scheduled and VM-replayed.

**Fixture A — shared factor:** starts `(2, 3)`, targets `(12, 18, 99)`, depth 3, one intermediate. All three strategies covered 2/3 targets in 3 instructions with peak-live 2. This fixture is not discriminative: the ordinary beam already discovers the useful factor 6.

**Fixture B — two-stage bridge:** starts `(2, 3)`, targets `(12, 35)`, depth 4, two intermediates. The ordinary beam covered 1/2 targets in 2 instructions (peak-live 1). Both complete-witness and partial-motif search covered 2/2 in 4 instructions (peak-live 2), using the shared bridge `2+3=5`, `5+2=7`, then `5+7=12` and `5*7=35`. The regression test now locks in this coverage distinction.

Wall-clock observations for Fixture B varied by CI interpreter/runner: approximately 1.14–2.59 seconds per strategy. Complete-witness was marginally faster than partial-motif in these three runs, but the difference is too small and environment-sensitive to support a speed claim. The meaningful result is coverage: the motif searches recover the second target that beam-only misses under these declared limits.

**Interpretation:** complete-witness and partial-motif both help on this deliberately constructed shared-bridge case. Partial-motif search has not yet demonstrated an advantage over complete-witness search on this fixture. The next experiment should target partial motifs that unlock useful subsets when no bounded complete witness exists, and compare several structurally distinct synthetic families. These results are synthetic only; they do not establish improvement on the Kaggle puzzle set or justify production integration.

### Search-state provenance correction

A further static review found that the complete-witness DFS keyed visited states only by available values and prefix length. That could merge two different arithmetic derivations that reached the same value frontier at the same depth, potentially discarding a distinct valid witness before register-pressure evaluation. The key now includes a canonicalized operation-provenance signature. Partial-motif state signatures are also canonicalized so equivalent operation sets reached in different expansion orders do not consume duplicate state budget.

A regression fixture confirms that both `2+2=4` and `2*2=4` derivations survive when each can participate in a valid `4+6=10` witness. All returned witnesses are scheduled and replayed. CI passed all 98 tests on Python 3.10, 3.11, and 3.12. This preserves alternative provenance; it does not claim globally optimal witness enumeration.

### Partial-motif advantage isolated (2026-11-24)

A targeted synthetic fixture now isolates the precise capability partial motifs are intended to provide. Starts are `(2, 3)`; goals are `(12, 18, 99)`; the auxiliary search is allowed only one intermediate.

- Complete-witness search returns no proposal: it requires all three goals to be exposed by the same available frontier, and 99 is not reachable within this one-intermediate budget.
- Partial-motif search returns a replayable three-instruction proposal covering 12 and 18: `2*3=6`, `6*2=12`, `6*3=18`.
- Goal 99 remains explicitly uncovered.

This directly demonstrates the intended distinction: partial search can preserve a useful subset even when no complete witness exists under the same intermediate budget. The test checks both outcomes and sends the partial proposal through register scheduling and VM replay. It does not yet show that partial motifs improve the final competition objective, nor that they outperform ordinary beam search on a broad fixture distribution.

A second subset fixture tests accumulation across target families: starts `(2, 3, 5)`, goals `(10, 12, 15, 18, 99)`, one intermediate. The initial values already expose 10 and 15; intermediate 6 then exposes 12 and 18. Partial search should retain a five-instruction proposal covering four of five goals, while complete-witness search cannot cover 99 within the one-intermediate limit. This checks that partial search can preserve direct yields while adding a shared-factor motif, rather than only succeeding on one isolated pair.

### Partial-motif ranking correction

The multi-family fixture exposed a ranking flaw: pure yield-density-first ranking preferred the two direct targets (2/2 instructions) over a five-instruction motif covering four of five targets. For a solver whose primary objective is completing as many targets as possible, that is the wrong default when retaining a partial plan for later composition. Both motif candidate ordering and planner-level partial-plan selection now prioritize absolute target coverage first, use yield density as the next discriminator, and then account for instruction count and register pressure. The intended 4/5 candidate is now the preferred partial proposal in the multi-family fixture.

### Multi-family comparison result (2026-11-24)

The planner-level comparison ran beam-only, complete-witness-enabled, and partial-motif-enabled modes on the same `(2, 3, 5)` → `(10, 12, 15, 18, 99)` fixture, with identical beam limits and motif caps. All three modes returned the same 4/5 coverage in five instructions, with peak-live 2. Runtime was approximately 4.5–6.5 seconds per mode across CI runners and is not meaningfully different. Thus, although the partial-motif helper can explicitly retain a useful subset when no complete witness exists, it did **not** improve the final planner result over beam-only on this fixture. The current evidence supports partial motifs as a fallback/candidate-generation capability, not as a demonstrated performance improvement. Production integration remains unjustified.
