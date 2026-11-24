"""Higher-branching synthetic stress test for frontier-cache working sets.

These fixtures deliberately create overlapping target equations and multiple
routes to useful intermediate values. They are bounded experiments, not
competition-data measurements.
"""
from functools import lru_cache
from time import perf_counter
from unittest import TestCase
from unittest.mock import patch

import elfcalc.bounded_search as search
from elfcalc.puzzle import Puzzle
from elfcalc.register_schedule import estimate_peak_live_values, schedule_value_dag
from elfcalc.validation import validate_program


CAPACITIES = (0, 64, 128, 256, 512)
STRESS_FIXTURES = (
    {
        "name": "overlapping_target_cones",
        "starts": (2, 3, 4, 5, 6),
        "targets": (12, 18, 20, 24, 30, 36, 40, 45),
        "limit": 120,
    },
    {
        "name": "multi_route_shared_values",
        "starts": (2, 3, 4, 6),
        "targets": (12, 18, 24, 36, 48, 54, 72, 90),
        "limit": 120,
    },
    {
        "name": "dense_factorial_branching",
        "starts": (2, 3, 4, 5, 7),
        "targets": (14, 20, 28, 35, 40, 42, 56, 70),
        "limit": 140,
    },
)


class FrontierCacheStressTests(TestCase):

    def test_stress_working_set_sweep_preserves_exact_quality(self):
        for fixture in STRESS_FIXTURES:
            baseline = None
            rows = []
            for capacity in CAPACITIES:
                generated = {"count": 0}
                native_generator = search._pair_recipes

                def counted_generator(values, limit):
                    generated["count"] += 1
                    return tuple(native_generator(values, limit))

                cached = lru_cache(maxsize=capacity)(counted_generator) if capacity else None
                started = perf_counter()
                with patch.object(search, "_pair_recipes", counted_generator):
                    if cached is not None:
                        with patch.object(search, "_cached_pair_recipes", cached):
                            plan = search.plan_bounded_beam(
                                fixture["starts"], fixture["targets"], fixture["limit"],
                                max_intermediates=2,
                                max_depth=3,
                                beam_width=8,
                                max_expansions_per_state=16,
                                enable_complete_witnesses=False,
                                enable_partial_motifs=False,
                            )
                    else:
                        with patch.object(
                            search, "_cached_pair_recipes",
                            lambda values, limit: counted_generator(values, limit),
                        ):
                            plan = search.plan_bounded_beam(
                                fixture["starts"], fixture["targets"], fixture["limit"],
                                max_intermediates=2,
                                max_depth=3,
                                beam_width=8,
                                max_expansions_per_state=16,
                                enable_complete_witnesses=False,
                                enable_partial_motifs=False,
                            )
                elapsed = perf_counter() - started

                allocation = schedule_value_dag(
                    plan.operations, fixture["starts"], fixture["limit"]
                )
                covered = tuple(sorted(plan.covered_targets))
                replay = validate_program(
                    Puzzle(fixture["name"], fixture["starts"], covered, fixture["limit"]),
                    allocation,
                )
                self.assertTrue(replay.complete, replay.error)
                quality = (
                    covered,
                    len(plan.operations),
                    estimate_peak_live_values(plan.operations, fixture["starts"]),
                    tuple(sorted(plan.missing_targets)),
                )
                if baseline is None:
                    baseline = quality
                else:
                    self.assertEqual(quality, baseline, (fixture["name"], capacity))

                info = cached.cache_info() if cached is not None else None
                rows.append({
                    "capacity": capacity,
                    "generated": generated["count"],
                    "hits": info.hits if info else 0,
                    "misses": info.misses if info else generated["count"],
                    "size": info.currsize if info else 0,
                    "evictions": max(0, info.misses - info.currsize) if info else 0,
                    "elapsed_seconds": round(elapsed, 6),
                    "quality": quality,
                })

            cached_rows = [row for row in rows if row["capacity"]]
            for row in cached_rows:
                self.assertLessEqual(
                    row["generated"], rows[0]["generated"],
                    (fixture["name"], row["capacity"]),
                )
            print("FRONTIER_CACHE_STRESS", fixture["name"], rows)
