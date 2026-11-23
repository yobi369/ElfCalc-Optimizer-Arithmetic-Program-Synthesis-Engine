# Shared-Intermediate DAG Solver: Engineering Checkpoint

Date: 2026-11-23

## Delivered components

- `src/elfcalc/target_dna.py`: exact arithmetic fingerprints and relation extraction.
- `src/elfcalc/shared_intermediate.py`: deterministic greedy value-DAG planner.
- `src/elfcalc/register_schedule.py`: liveness-aware lowering from value operations to the 48-register VM.
- `src/elfcalc/shared_solver.py`: plan → schedule → VM replay validation pipeline.
- `src/elfcalc/construct.py`: the end-to-end shared solver is included as an additional candidate in the constructive solver portfolio.

## Planner improvements

1. Directly reachable targets are prioritized over speculative intermediates. This prevents an intermediate with higher apparent one-step yield from delaying a target that already costs only one instruction.
2. Candidate scoring now inverts target equations. For each missing target and currently available value, it derives the exact candidate values that could combine with that value to produce the target. Only candidates already present in the legal one-operation frontier are scored.
3. The inverse target-cone implementation is checked against a brute-force relation enumerator on a deterministic bounded arithmetic fixture.

## Register scheduling

The scheduler counts future operand uses and protects every value with outstanding uses. It allocates an uninitialized register when available; otherwise it reuses a register only after its current value's final use. The emitted program is replayed through `ArithmeticMachine`, and every abstract DAG result must appear during replay.

The scheduler also validates each declared DAG operation before allocation: integer operands/results, supported operator, exact division, positive bounded result, and equality between declared and computed result.

## Verification

The GitHub Actions Python matrix passed on Python 3.10, 3.11, and 3.12 for commit:

`9b9c87071f53c4b53ede6516fc780f76f5e2bec3`

The tests cover:
- direct target closure and direct-target-first selection;
- shared intermediate reuse;
- bounded arithmetic and invalid targets;
- equivalence of inverse target cones to brute-force relation discovery;
- liveness-aware register reuse with all 48 registers initially occupied;
- rejection of malformed DAG operations and inexact division;
- end-to-end scheduling and trusted VM replay.

## Limits and next gate

This is a verified solver component, not yet a demonstrated competition-score improvement. The greedy planner is not globally optimal, the register allocator follows the DAG's current topological order rather than searching alternate schedules, and no full 1,000-puzzle benchmark or official score has been run from this checkpoint.

Next:
1. benchmark the new candidate against the frozen incumbent on the authenticated competition data when permitted;
2. measure runtime, instruction delta, register pressure, and completeness separately;
3. introduce bounded beam search over alternative DAGs and schedules only where the greedy candidate has headroom;
4. promote a candidate only after exact full-dataset replay and provenance checks.

Current frozen incumbent remains **130,974 instructions**. No new score is claimed here.
