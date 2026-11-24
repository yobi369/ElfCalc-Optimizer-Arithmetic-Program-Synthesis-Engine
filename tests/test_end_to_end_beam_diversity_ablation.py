"""End-to-end synthetic ablation of beam diversity in the real planner.

Runs plan_bounded_beam with identical declared limits, switching only the
beam-admission policy. This is not a scored-archive experiment and does not
assume diversity must win.
"""
from unittest import TestCase
from unittest.mock import patch

import elfcalc.bounded_search as search
from elfcalc.puzzle import Puzzle
from elfcalc.register_schedule import estimate_peak_live_values, schedule_value_dag
from elfcalc.validation import validate_program


class EndToEndBeamDiversityAblationTests(TestCase):

    def test_real_planner_with_and_without_diversity_reservation(self):
        fixtures = (
            ("shared_factor", (2, 3), (12, 18, 99), 1000),
            ("shared_bridge", (2, 3), (12, 35), 1000),
            ("multi_family", (2, 3, 5), (10, 12, 15, 18, 99), 1000),
            ("provenance_collision", (2, 3), (10, 12, 35), 1000),
            ("deep_power", (2,), (256,), 1000),
        )
        common = dict(
            max_intermediates=3,
            max_depth=5,
            beam_width=12,
            max_expansions_per_state=64,
            enable_complete_witnesses=False,
            enable_partial_motifs=False,
        )

        def ordinary_admission(states, beam_width, starts, limit,
                               subgraph_support=None):
            ranked = sorted(
                states,
                key=lambda state: search._rank(
                    state, starts, limit, subgraph_support
                ),
            )
            return tuple(ranked[:beam_width])

        matrix = {}
        for name, starts, targets, limit in fixtures:
            search._cached_pair_recipes.cache_clear()
            with patch.object(
                search, "_select_diverse_beam", side_effect=ordinary_admission
            ):
                ordinary = search.plan_bounded_beam(
                    starts, targets, limit, **common
                )

            search._cached_pair_recipes.cache_clear()
            diverse = search.plan_bounded_beam(
                starts, targets, limit, **common
            )

            fixture_metrics = {}
            for strategy, plan in (("ordinary", ordinary), ("diverse", diverse)):
                self.assertEqual(
                    set(plan.covered_targets).union(plan.missing_targets),
                    set(targets).difference(starts),
                )
                allocation = schedule_value_dag(plan.operations, starts, limit)
                if plan.covered_targets:
                    replay = validate_program(
                        Puzzle(
                            f"{name}_{strategy}",
                            tuple(starts),
                            tuple(sorted(plan.covered_targets)),
                            limit,
                        ),
                        allocation,
                    )
                    self.assertTrue(replay.complete, replay.error)
                fixture_metrics[strategy] = (
                    len(plan.covered_targets),
                    len(plan.operations),
                    estimate_peak_live_values(plan.operations, starts),
                    tuple(sorted(plan.missing_targets)),
                )
            matrix[name] = fixture_metrics

        print("END_TO_END_BEAM_DIVERSITY_ABLATION", matrix)
        # The experiment reports differences rather than presupposing a winner.
        # Both strategies must produce replayable plans under identical limits.
        self.assertEqual(set(matrix), {fixture[0] for fixture in fixtures})
