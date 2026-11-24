"""Controlled comparison of beam search and completion-aware motif search.

Both strategies receive the same explicit state-expansion budget. Motif
proposals are scheduled and replayed through the exact VM before comparison.
"""
from time import perf_counter
from unittest import TestCase

from elfcalc.bounded_search import _shared_subgraph_witnesses, plan_bounded_beam
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


class CompletionAwareMotifAblationTests(TestCase):
    def test_equal_state_budget_beam_vs_completion_aware_motifs(self):
        rows = []
        for name, starts, targets, limit, intermediates, depth in FIXTURES:
            # Arm A: ordinary unguided beam. The explicit global cap counts
            # each partial state expanded, not each generated child proposal.
            started = perf_counter()
            beam = plan_bounded_beam(
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
            )
            beam_seconds = perf_counter() - started
            beam_covered = tuple(sorted(beam.covered_targets))
            beam_program = schedule_value_dag(beam.operations, starts, limit)
            beam_replay = validate_program(
                Puzzle(name + "_beam", starts, beam_covered, limit), beam_program
            )
            self.assertTrue(beam_replay.complete, (name, "beam", beam_replay.error))

            # Arm B: bounded completion-aware DFS. Its visited-state cap is
            # exactly the same as the beam's expanded-state cap. Each witness
            # includes the full dependency chain plus target-producing ops.
            started = perf_counter()
            witnesses = _shared_subgraph_witnesses(
                starts, frozenset(targets), limit,
                max_intermediates=intermediates,
                max_recipes_per_state=RECIPE_BUDGET,
                max_states=STATE_BUDGET,
                max_witnesses=64,
            )
            motif_seconds = perf_counter() - started

            valid = []
            for operations in witnesses:
                if len(operations) > depth:
                    continue
                try:
                    program = schedule_value_dag(operations, starts, limit)
                except (ValueError, RuntimeError):
                    continue
                replay = validate_program(
                    Puzzle(name + "_motif", starts, targets, limit), program
                )
                if replay.complete:
                    valid.append((
                        len(operations),
                        estimate_peak_live_values(operations, starts),
                        tuple((op.result, op.operator, op.left, op.right)
                              for op in operations),
                        operations,
                    ))

            motif = min(valid) if valid else None
            rows.append({
                "fixture": name,
                "state_budget_each": STATE_BUDGET,
                "beam_coverage": len(beam_covered),
                "beam_instructions": len(beam.operations),
                "beam_peak_live": estimate_peak_live_values(beam.operations, starts),
                "motif_witnesses_found": len(witnesses),
                "motif_complete": motif is not None,
                "motif_instructions": len(motif[3]) if motif else None,
                "motif_peak_live": motif[1] if motif else None,
                "motif_operations": tuple(
                    (op.left, op.operator, op.right, op.result)
                    for op in motif[3]
                ) if motif else None,
                "beam_seconds": round(beam_seconds, 6),
                "motif_seconds": round(motif_seconds, 6),
            })

        print("COMPLETION_AWARE_MOTIF_EQUAL_STATE_BUDGET_ABLATION")
        for row in rows:
            print(row)
        self.assertEqual(len(rows), len(FIXTURES))
        self.assertTrue(all(row["state_budget_each"] == STATE_BUDGET for row in rows))
        # The witness search discovers the tighter 3-operation shared
        # construction: 5*5=25, 2*25=50, 3*25=75.
        first = rows[0]
        self.assertTrue(first["motif_complete"], first)
        self.assertEqual(first["motif_instructions"], 3, first)
        self.assertEqual(
            {op[3] for op in first["motif_operations"]},
            {25, 50, 75},
            first,
        )
