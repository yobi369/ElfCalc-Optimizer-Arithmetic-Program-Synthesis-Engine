"""Isolate target-cone and shared-subgraph signals under equal beam limits."""
from unittest import TestCase

from elfcalc.bounded_search import (
    _multi_target_cone_support,
    _shared_subgraph_support,
    plan_bounded_beam,
)
from elfcalc.puzzle import Puzzle
from elfcalc.register_schedule import estimate_peak_live_values, schedule_value_dag
from elfcalc.validation import validate_program


FIXTURES = (
    ("shared_bridge", (2, 3), (12, 35), 1000, 2, 4, 1, 1),
    ("shared_factor", (2, 3), (12, 18, 99), 1000, 1, 3, 4, 4),
    ("power_chain", (2,), (65536,), 100000, 3, 4, 2, 2),
)
MODES = (
    ("unguided", False, False),
    ("target_cone_only", True, False),
    ("shared_subgraph_only", False, True),
    ("combined", True, True),
)


class GuidanceSignalAblationTests(TestCase):
    def test_signals_identify_known_shared_arithmetic_motifs(self):
        cone = _multi_target_cone_support(
            frozenset({12, 18}), (2, 3), 1000, 2, 128
        )
        self.assertEqual(cone[6], frozenset({12, 18}))

        shared = _shared_subgraph_support(
            (2, 3), frozenset({12, 35}), 1000
        )
        self.assertEqual(shared[5], frozenset({12, 35}))

    def test_shared_subgraph_only_can_reach_its_predicted_target_completions(self):
        # Shared construction: 2 + 3 = 5, then 5 + 2 = 7;
        # the two targets follow as 5 + 7 = 12 and 5 * 7 = 35.
        plan = plan_bounded_beam(
            (2, 3),
            (12, 35),
            1000,
            max_intermediates=3,
            max_depth=5,
            beam_width=8,
            max_expansions_per_state=16,
            enable_complete_witnesses=False,
            enable_partial_motifs=False,
            enable_target_cone_guidance=False,
            enable_shared_subgraph_guidance=True,
        )
        allocation = schedule_value_dag(plan.operations, (2, 3), 1000)
        self.assertEqual(plan.covered_targets, frozenset({12, 35}))
        replay = validate_program(Puzzle("shared_subgraph_goal_admission", (2, 3),
                                         (12, 35), 1000), allocation)
        self.assertTrue(replay.complete, replay.error)

    def test_guidance_ablation_under_identical_search_limits_and_exact_replay(self):
        results = {}
        for name, starts, targets, limit, intermediates, depth, width, expansions in FIXTURES:
            fixture_rows = {}
            for mode, cone_enabled, shared_enabled in MODES:
                plan = plan_bounded_beam(
                    starts,
                    targets,
                    limit,
                    max_intermediates=intermediates,
                    max_depth=depth,
                    beam_width=width,
                    max_expansions_per_state=expansions,
                    enable_complete_witnesses=False,
                    enable_partial_motifs=False,
                    enable_target_cone_guidance=cone_enabled,
                    enable_shared_subgraph_guidance=shared_enabled,
                )
                allocation = schedule_value_dag(plan.operations, starts, limit)
                covered = tuple(sorted(plan.covered_targets))
                replay = validate_program(Puzzle(name, starts, covered, limit), allocation)
                self.assertTrue(replay.complete, (name, mode, replay.error))
                self.assertEqual(
                    set(covered).union(plan.missing_targets),
                    set(targets).difference(starts),
                    (name, mode),
                )
                fixture_rows[mode] = {
                    "coverage": len(covered),
                    "covered_targets": covered,
                    "instructions": len(plan.operations),
                    "peak_live": estimate_peak_live_values(plan.operations, starts),
                    "missing": tuple(sorted(plan.missing_targets)),
                }
            results[name] = fixture_rows
        print("GUIDANCE_SIGNAL_ABLATION", results)
        self.assertEqual(set(results), {fixture[0] for fixture in FIXTURES})
        for fixture_rows in results.values():
            self.assertEqual(set(fixture_rows), {mode[0] for mode in MODES})
