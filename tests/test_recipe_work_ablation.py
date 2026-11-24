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
