"""Factorial ablation of target-cone and shared-subgraph guidance.

All four arms use identical beam/depth/intermediate/expansion limits. Complete
witness and partial-motif side searches are disabled to isolate guidance.
Every returned covered target is independently replayed through the VM.
"""
from time import perf_counter
from unittest import TestCase
from unittest.mock import patch

import elfcalc.bounded_search as search
from elfcalc.puzzle import Puzzle
from elfcalc.register_schedule import estimate_peak_live_values, schedule_value_dag
from elfcalc.validation import validate_program


FIXTURES = (
    {"name": "shared_factor", "starts": (2, 3), "targets": (12, 18, 99), "limit": 1000},
    {"name": "shared_bridge", "starts": (2, 3), "targets": (12, 35), "limit": 1000},
    {"name": "deep_shared_bridge", "starts": (2, 3), "targets": (50, 75, 99), "limit": 1000},
    {"name": "multi_family", "starts": (2, 3, 5), "targets": (10, 12, 15, 18, 99), "limit": 1000},
    {"name": "overlapping_cones", "starts": (2, 3, 4, 5, 6),
     "targets": (12, 18, 20, 24, 30, 36, 40, 45), "limit": 120},
)


ARMS = (
    ("unguided", False, False),
    ("target_cone_only", True, False),
    ("shared_subgraph_only", False, True),
    ("combined", True, True),
)


class TargetConeSharedSubgraphAblationTests(TestCase):

    def test_factorial_guidance_ablation_with_identical_limits_and_vm_replay(self):
        rows = []
        common_limits = {
            "max_intermediates": 3,
            "max_depth": 5,
            "beam_width": 8,
            "max_expansions_per_state": 16,
            "enable_complete_witnesses": False,
            "enable_partial_motifs": False,
        }

        for fixture in FIXTURES:
            family_rows = []
            for arm, cone_enabled, shared_enabled in ARMS:
                counters = {"frontier_requests": 0, "frontiers_generated": 0,
                            "candidate_state_proposals": 0}
                native_pair = search._pair_recipes
                native_key = search._state_key

                def counted_pair(values, limit):
                    counters["frontiers_generated"] += 1
                    return native_pair(values, limit)

                def counted_key(state, starts):
                    counters["candidate_state_proposals"] += 1
                    return native_key(state, starts)

                native_cached = search._cached_pair_recipes

                def counted_frontier(values, limit):
                    counters["frontier_requests"] += 1
                    return native_cached(values, limit)

                search._cached_pair_recipes.cache_clear()
                started = perf_counter()
                with (
                    patch.object(search, "_pair_recipes", counted_pair),
                    patch.object(search, "_state_key", counted_key),
                    patch.object(search, "_cached_pair_recipes", counted_frontier),
                ):
                    plan = search.plan_bounded_beam(
                        fixture["starts"], fixture["targets"], fixture["limit"],
                        **common_limits,
                        enable_target_cone_guidance=cone_enabled,
                        enable_shared_subgraph_guidance=shared_enabled,
                    )
                elapsed = perf_counter() - started

                covered = tuple(sorted(plan.covered_targets))
                self.assertEqual(
                    set(covered).union(plan.missing_targets),
                    set(fixture["targets"]),
                    (fixture["name"], arm, covered, plan.missing_targets),
                )
                allocation = schedule_value_dag(
                    plan.operations, fixture["starts"], fixture["limit"]
                )
                replay = validate_program(
                    Puzzle(fixture["name"] + "_" + arm, fixture["starts"],
                           covered, fixture["limit"]),
                    allocation,
                )
                self.assertTrue(replay.complete, replay.error)

                row = {
                    "fixture": fixture["name"],
                    "arm": arm,
                    "coverage": len(covered),
                    "covered_targets": covered,
                    "instructions": len(plan.operations),
                    "peak_live": estimate_peak_live_values(plan.operations, fixture["starts"]),
                    "frontier_requests": counters["frontier_requests"],
                    "frontiers_generated": counters["frontiers_generated"],
                    "candidate_state_proposals": counters["candidate_state_proposals"],
                    "elapsed_seconds": round(elapsed, 6),
                    "limits": dict(common_limits),
                }
                rows.append(row)
                family_rows.append(row)

            self.assertEqual(len(family_rows), len(ARMS))
            # Each fixture must have exactly the same declared search limits
            # in all four arms; only the two guidance switches may differ.
            self.assertTrue(all(row["limits"] == family_rows[0]["limits"]
                                for row in family_rows))

        print("TARGET_CONE_SHARED_SUBGRAPH_FACTORIAL_ABLATION")
        for row in rows:
            print(row)
