"""Frontier-cache working-set sweep with exact plan/replay invariants."""
from functools import lru_cache
from time import perf_counter
from unittest import TestCase
from unittest.mock import patch

import elfcalc.bounded_search as search
from tests.test_search_diversity_tournament import FIXTURES
from elfcalc.puzzle import Puzzle
from elfcalc.register_schedule import schedule_value_dag, estimate_peak_live_values
from elfcalc.validation import validate_program


CAPACITIES = (0, 32, 64, 128, 256, 512, 1024)


class FrontierCacheEconomicsTests(TestCase):

    def test_cache_capacity_sweep_preserves_quality_and_reports_working_set(self):
        baseline = {}
        rows = []
        fixture_orders = (FIXTURES, tuple(reversed(FIXTURES)))

        for order_index, fixtures in enumerate(fixture_orders):
            for fixture in fixtures:
                for capacity in CAPACITIES:
                    generated = {"count": 0}

                    def counted_generator(values, limit):
                        generated["count"] += 1
                        return native_generator(values, limit)

                    native_generator = search._pair_recipes
                    cached = lru_cache(maxsize=capacity)(counted_generator) if capacity else None
                    requests = {"count": 0}
                    started = perf_counter()
                    with patch.object(search, "_pair_recipes", counted_generator):
                        if cached is not None:
                            with patch.object(search, "_cached_pair_recipes", cached):
                                plan = search.plan_bounded_beam(
                                    fixture["starts"], fixture["targets"], fixture["limit"],
                                    max_intermediates=fixture["max_intermediates"],
                                    max_depth=fixture["max_depth"],
                                    beam_width=fixture["beam_width"],
                                    max_expansions_per_state=fixture["max_expansions_per_state"],
                                    enable_complete_witnesses=False,
                                    enable_partial_motifs=False,
                                )
                        else:
                            def uncached(values, limit):
                                requests["count"] += 1
                                return counted_generator(values, limit)
                            with patch.object(search, "_cached_pair_recipes", uncached):
                                plan = search.plan_bounded_beam(
                                    fixture["starts"], fixture["targets"], fixture["limit"],
                                    max_intermediates=fixture["max_intermediates"],
                                    max_depth=fixture["max_depth"],
                                    beam_width=fixture["beam_width"],
                                    max_expansions_per_state=fixture["max_expansions_per_state"],
                                    enable_complete_witnesses=False,
                                    enable_partial_motifs=False,
                                )
                    elapsed = perf_counter() - started
                    allocation = schedule_value_dag(
                        plan.operations, fixture["starts"], fixture["limit"]
                    )
                    covered = tuple(sorted(plan.covered_targets))
                    self.assertTrue(covered, (fixture["name"], capacity))
                    replay = validate_program(
                        Puzzle(fixture["name"], fixture["starts"], covered, fixture["limit"]),
                        allocation,
                    )
                    self.assertTrue(replay.complete, replay.error)
                    quality = (
                        covered, len(plan.operations),
                        estimate_peak_live_values(plan.operations, fixture["starts"]),
                        tuple(sorted(plan.missing_targets)),
                    )
                    key = (fixture["name"], order_index)
                    if capacity == 0:
                        baseline[key] = quality
                    else:
                        self.assertEqual(quality, baseline[key])

                    info = cached.cache_info() if cached is not None else None
                    row = {
                        "order": order_index,
                        "fixture": fixture["name"],
                        "capacity": capacity,
                        "frontiers_generated": generated["count"],
                        "hits": info.hits if info else 0,
                        "misses": info.misses if info else requests["count"],
                        "current_size": info.currsize if info else 0,
                        "evictions": max(0, info.misses - info.currsize) if info else 0,
                        "elapsed_seconds": round(elapsed, 6),
                        "quality": quality,
                    }
                    rows.append(row)

        print("FRONTIER_CACHE_CAPACITY_SWEEP")
        for row in rows:
            print(row)
