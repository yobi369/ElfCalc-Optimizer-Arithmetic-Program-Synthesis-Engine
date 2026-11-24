"""Measure actual recipe-frontier work for beam and motif search.

Equal visited-state caps are not treated as equal compute. This experiment
counts frontier requests and candidate recipes returned by the shared recipe
generator, then validates all accepted programs with the exact VM.
"""
from time import perf_counter
from unittest import TestCase
from unittest.mock import patch

import elfcalc.bounded_search as search
from elfcalc.puzzle import Puzzle
from elfcalc.register_schedule import estimate_peak_live_values, schedule_value_dag
from elfcalc.validation import validate_program


FIXTURES = (
    ("shared_factor_chain", (2, 3, 5), (50, 75), 1000, 2, 4),
    ("shared_bridge", (2, 3), (12, 35), 1000, 3, 5),
    ("multi_family", (2, 3, 5), (10, 12, 15, 18), 1000, 3, 5),
)
STATE_BUDGET = 512
RECIPE_BUDGET = 32


class RecipeWorkAblationTests(TestCase):
    def _measure(self, callback):
        original = search._cached_pair_recipes
        counts = {"frontier_requests": 0, "candidate_recipes": 0}

        def counted(values, limit):
            recipes = original(values, limit)
            counts["frontier_requests"] += 1
            counts["candidate_recipes"] += len(recipes)
            return recipes

        started = perf_counter()
        with patch.object(search, "_cached_pair_recipes", counted):
            result = callback()
        counts["elapsed_seconds"] = round(perf_counter() - started, 6)
        return result, counts

    def test_report_actual_recipe_work_not_only_state_counts(self):
        rows = []
        for name, starts, targets, limit, intermediates, depth in FIXTURES:
            beam, beam_work = self._measure(lambda: search.plan_bounded_beam(
                starts, targets, limit,
                max_intermediates=intermediates,
                max_depth=depth,
                beam_width=8,
                max_expansions_per_state=RECIPE_BUDGET,
                max_total_state_expansions=STATE_BUDGET,
                enable_complete_witnesses=False,
                enable_partial_motifs=False,
                enable_target_cone_guidance=False,
                enable_shared_subgraph_guidance=False,
            ))
            beam_program = schedule_value_dag(beam.operations, starts, limit)
            beam_replay = validate_program(
                Puzzle(name + "_recipe_beam", starts,
                       tuple(sorted(beam.covered_targets)), limit),
                beam_program,
            )
            self.assertTrue(beam_replay.complete, (name, "beam", beam_replay.error))

            witnesses, motif_work = self._measure(lambda: search._shared_subgraph_witnesses(
                starts, frozenset(targets), limit,
                max_intermediates=intermediates,
                max_recipes_per_state=RECIPE_BUDGET,
                max_states=STATE_BUDGET,
                max_witnesses=64,
            ))
            valid = []
            for operations in witnesses:
                if len(operations) > depth:
                    continue
                try:
                    program = schedule_value_dag(operations, starts, limit)
                except (ValueError, RuntimeError):
                    continue
                replay = validate_program(
                    Puzzle(name + "_recipe_motif", starts, targets, limit), program
                )
                if replay.complete:
                    valid.append(operations)

            winner = min(
                valid,
                key=lambda ops: (
                    len(ops),
                    estimate_peak_live_values(ops, starts),
                    tuple((op.result, op.operator, op.left, op.right) for op in ops),
                ),
            ) if valid else None
            rows.append({
                "fixture": name,
                "state_cap_each": STATE_BUDGET,
                "beam_instructions": len(beam.operations),
                "motif_instructions": len(winner) if winner else None,
                "beam_recipe_work": beam_work,
                "motif_recipe_work": motif_work,
                "motif_witnesses": len(witnesses),
            })

        print("ACTUAL_RECIPE_WORK_ABLATION")
        for row in rows:
            print(row)
        self.assertEqual(len(rows), len(FIXTURES))


    def test_motif_seeded_beam_hybrid_is_exactly_replayed(self):
        rows = []
        for name, starts, targets, limit, intermediates, depth in FIXTURES[:2]:
            witnesses, motif_work = self._measure(lambda: search._shared_subgraph_witnesses(
                starts, frozenset(targets), limit,
                max_intermediates=intermediates,
                max_recipes_per_state=RECIPE_BUDGET,
                max_states=STATE_BUDGET,
                max_witnesses=8,
            ))
            candidates = []
            continuation_work = {
                "frontier_requests": 0,
                "candidate_recipes": 0,
                "elapsed_seconds": 0.0,
            }
            # Seed the ordinary beam with each motif's concrete non-target
            # dependency chain, then let the beam discover any remaining goals.
            for witness in witnesses[:4]:
                # First preserve the motif's complete DAG: target-producing
                # operations are part of the solution and must not be discarded.
                try:
                    direct_program = schedule_value_dag(witness, starts, limit)
                except (ValueError, RuntimeError):
                    direct_program = None
                if direct_program is not None:
                    direct_replay = validate_program(
                        Puzzle(name + "_hybrid_direct", starts, targets, limit),
                        direct_program,
                    )
                    if direct_replay.complete:
                        candidates.append(witness)

                prefix = tuple(op for op in witness if not op.is_target)
                seeded_values = tuple(starts) + tuple(op.result for op in prefix)
                remaining = tuple(
                    target for target in targets if target not in seeded_values
                )
                if not remaining:
                    combined = witness
                    try:
                        program = schedule_value_dag(combined, starts, limit)
                    except (ValueError, RuntimeError):
                        continue
                    replay = validate_program(
                        Puzzle(name + "_hybrid_direct", starts, targets, limit),
                        program,
                    )
                    if replay.complete:
                        candidates.append(combined)
                    continue

                continuation, work = self._measure(lambda: search.plan_bounded_beam(
                    seeded_values, remaining, limit,
                    max_intermediates=max(0, intermediates - len(prefix)),
                    max_depth=max(0, depth - len(prefix)),
                    beam_width=8,
                    max_expansions_per_state=RECIPE_BUDGET,
                    max_total_state_expansions=STATE_BUDGET,
                    enable_complete_witnesses=False,
                    enable_partial_motifs=False,
                    enable_target_cone_guidance=False,
                    enable_shared_subgraph_guidance=False,
                ))
                for key in ("frontier_requests", "candidate_recipes"):
                    continuation_work[key] += work[key]
                continuation_work["elapsed_seconds"] += work["elapsed_seconds"]
                combined = prefix + continuation.operations
                if len(combined) > depth:
                    continue
                try:
                    program = schedule_value_dag(combined, starts, limit)
                except (ValueError, RuntimeError):
                    continue
                replay = validate_program(
                    Puzzle(name + "_hybrid", starts, targets, limit), program
                )
                if replay.complete:
                    candidates.append(combined)

            winner = min(
                candidates,
                key=lambda ops: (
                    len(ops),
                    estimate_peak_live_values(ops, starts),
                    tuple((op.result, op.operator, op.left, op.right) for op in ops),
                ),
            ) if candidates else None
            rows.append({
                "fixture": name,
                "hybrid_complete": winner is not None,
                "hybrid_instructions": len(winner) if winner else None,
                "motif_discovery_work": motif_work,
                "beam_continuation_work": continuation_work,
                "total_candidate_recipes": (
                    motif_work["candidate_recipes"]
                    + continuation_work["candidate_recipes"]
                ),
                "seeds_examined": min(4, len(witnesses)),
            })

        print("MOTIF_SEEDED_BEAM_HYBRID")
        for row in rows:
            print(row)
        self.assertEqual(len(rows), 2)


    def test_best_of_beam_and_motif_portfolio_is_exactly_replayed(self):
        rows = []
        for name, starts, targets, limit, intermediates, depth in FIXTURES:
            beam, beam_work = self._measure(lambda: search.plan_bounded_beam(
                starts, targets, limit,
                max_intermediates=intermediates,
                max_depth=depth,
                beam_width=8,
                max_expansions_per_state=RECIPE_BUDGET,
                max_total_state_expansions=STATE_BUDGET,
                enable_complete_witnesses=False,
                enable_partial_motifs=False,
                enable_target_cone_guidance=False,
                enable_shared_subgraph_guidance=False,
            ))
            candidates = [("beam", beam.operations, beam_work)]
            witnesses, motif_work = self._measure(lambda: search._shared_subgraph_witnesses(
                starts, frozenset(targets), limit,
                max_intermediates=intermediates,
                max_recipes_per_state=RECIPE_BUDGET,
                max_states=STATE_BUDGET,
                max_witnesses=64,
            ))
            for operations in witnesses:
                if len(operations) > depth:
                    continue
                try:
                    program = schedule_value_dag(operations, starts, limit)
                except (ValueError, RuntimeError):
                    continue
                replay = validate_program(
                    Puzzle(name + "_portfolio_motif", starts, targets, limit), program
                )
                if replay.complete:
                    candidates.append(("motif", operations, motif_work))

            valid = []
            for strategy, operations, work in candidates:
                try:
                    program = schedule_value_dag(operations, starts, limit)
                except (ValueError, RuntimeError):
                    continue
                replay = validate_program(
                    Puzzle(name + "_portfolio_" + strategy, starts, targets, limit),
                    program,
                )
                if replay.complete:
                    valid.append((strategy, operations, work))

            winner = min(
                valid,
                key=lambda item: (
                    len(item[1]),
                    estimate_peak_live_values(item[1], starts),
                    tuple((op.result, op.operator, op.left, op.right)
                          for op in item[1]),
                ),
            ) if valid else None
            rows.append({
                "fixture": name,
                "portfolio_complete": winner is not None,
                "winner": winner[0] if winner else None,
                "instructions": len(winner[1]) if winner else None,
                "peak_live": estimate_peak_live_values(winner[1], starts) if winner else None,
                "beam_candidate_recipes": beam_work["candidate_recipes"],
                "motif_candidate_recipes": motif_work["candidate_recipes"],
                "portfolio_candidate_recipes": (
                    beam_work["candidate_recipes"] + motif_work["candidate_recipes"]
                ),
            })

        print("BEST_OF_BEAM_MOTIF_PORTFOLIO")
        for row in rows:
            print(row)
        self.assertEqual(len(rows), len(FIXTURES))
        self.assertTrue(all(row["portfolio_complete"] for row in rows))


    def test_adaptive_search_routes_remaining_budget_to_better_probe(self):
        """Probe both strategies cheaply, then spend the remaining budget once."""
        probe_states = 64
        continuation_states = STATE_BUDGET - probe_states
        rows = []

        for name, starts, targets, limit, intermediates, depth in FIXTURES:
            beam_probe, beam_probe_work = self._measure(lambda: search.plan_bounded_beam(
                starts, targets, limit,
                max_intermediates=intermediates,
                max_depth=depth,
                beam_width=8,
                max_expansions_per_state=RECIPE_BUDGET,
                max_total_state_expansions=probe_states,
                enable_complete_witnesses=False,
                enable_partial_motifs=False,
                enable_target_cone_guidance=False,
                enable_shared_subgraph_guidance=False,
            ))
            motif_probe, motif_probe_work = self._measure(
                lambda: search._shared_subgraph_witnesses(
                    starts, frozenset(targets), limit,
                    max_intermediates=intermediates,
                    max_recipes_per_state=RECIPE_BUDGET,
                    max_states=probe_states,
                    max_witnesses=64,
                )
            )

            motif_complete = []
            motif_coverage = 0
            for operations in motif_probe:
                values = set(starts).union(op.result for op in operations)
                coverage = len(set(targets).intersection(values))
                motif_coverage = max(motif_coverage, coverage)
                if coverage == len(set(targets)) and len(operations) <= depth:
                    try:
                        program = schedule_value_dag(operations, starts, limit)
                    except (ValueError, RuntimeError):
                        continue
                    replay = validate_program(
                        Puzzle(name + "_adaptive_motif_probe", starts, targets, limit),
                        program,
                    )
                    if replay.complete:
                        motif_complete.append(operations)

            beam_complete = None
            if not beam_probe.missing_targets:
                try:
                    program = schedule_value_dag(beam_probe.operations, starts, limit)
                except (ValueError, RuntimeError):
                    program = None
                if program is not None:
                    replay = validate_program(
                        Puzzle(name + "_adaptive_beam_probe", starts, targets, limit),
                        program,
                    )
                    if replay.complete:
                        beam_complete = beam_probe.operations

            def rank(coverage, work):
                recipes = max(1, work["candidate_recipes"])
                return (coverage / recipes, coverage, -recipes)

            if beam_complete is not None or motif_complete:
                options = []
                if beam_complete is not None:
                    options.append(("beam", beam_complete))
                options.extend(("motif", ops) for ops in motif_complete)
                selected_strategy, selected_ops = min(
                    options,
                    key=lambda item: (
                        len(item[1]),
                        estimate_peak_live_values(item[1], starts),
                        item[0],
                    ),
                )
                continuation_ops = selected_ops
                continuation_work = {
                    "frontier_requests": 0,
                    "candidate_recipes": 0,
                    "elapsed_seconds": 0.0,
                }
                continuation_complete = True
            else:
                beam_score = rank(
                    len(beam_probe.covered_targets), beam_probe_work
                )
                motif_score = rank(motif_coverage, motif_probe_work)
                selected_strategy = (
                    "beam" if beam_score >= motif_score else "motif"
                )
                if selected_strategy == "beam":
                    continuation, continuation_work = self._measure(
                        lambda: search.plan_bounded_beam(
                            starts, targets, limit,
                            max_intermediates=intermediates,
                            max_depth=depth,
                            beam_width=8,
                            max_expansions_per_state=RECIPE_BUDGET,
                            max_total_state_expansions=continuation_states,
                            enable_complete_witnesses=False,
                            enable_partial_motifs=False,
                            enable_target_cone_guidance=False,
                            enable_shared_subgraph_guidance=False,
                        )
                    )
                    continuation_ops = continuation.operations
                    continuation_complete = not continuation.missing_targets
                else:
                    continuation, continuation_work = self._measure(
                        lambda: search._shared_subgraph_witnesses(
                            starts, frozenset(targets), limit,
                            max_intermediates=intermediates,
                            max_recipes_per_state=RECIPE_BUDGET,
                            max_states=continuation_states,
                            max_witnesses=64,
                        )
                    )
                    complete = []
                    for operations in continuation:
                        if len(operations) > depth:
                            continue
                        try:
                            program = schedule_value_dag(operations, starts, limit)
                        except (ValueError, RuntimeError):
                            continue
                        replay = validate_program(
                            Puzzle(name + "_adaptive_motif_continuation",
                                   starts, targets, limit),
                            program,
                        )
                        if replay.complete:
                            complete.append(operations)
                    continuation_ops = min(
                        complete,
                        key=lambda ops: (
                            len(ops),
                            estimate_peak_live_values(ops, starts),
                        ),
                    ) if complete else ()
                    continuation_complete = bool(complete)

            selected_program = None
            if continuation_complete:
                try:
                    selected_program = schedule_value_dag(
                        continuation_ops, starts, limit
                    )
                except (ValueError, RuntimeError):
                    selected_program = None
            final_replay = (
                validate_program(
                    Puzzle(name + "_adaptive_final", starts, targets, limit),
                    selected_program,
                ) if selected_program is not None else None
            )
            total_recipes = (
                beam_probe_work["candidate_recipes"]
                + motif_probe_work["candidate_recipes"]
                + continuation_work["candidate_recipes"]
            )
            rows.append({
                "fixture": name,
                "selected_strategy": selected_strategy,
                "complete": bool(final_replay and final_replay.complete),
                "instructions": len(continuation_ops) if final_replay and final_replay.complete else None,
                "probe_beam_recipes": beam_probe_work["candidate_recipes"],
                "probe_motif_recipes": motif_probe_work["candidate_recipes"],
                "continuation_recipes": continuation_work["candidate_recipes"],
                "total_candidate_recipes": total_recipes,
                "probe_coverage": {
                    "beam": len(beam_probe.covered_targets),
                    "motif": motif_coverage,
                },
            })

        print("ADAPTIVE_SEARCH_PORTFOLIO")
        for row in rows:
            print(row)
        self.assertEqual(len(rows), len(FIXTURES))
        self.assertTrue(all(row["complete"] for row in rows))
