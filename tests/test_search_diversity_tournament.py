"""Eight-way synthetic tournament for beam identity, diversity, and caching.

Run with: python -m unittest tests.test_search_diversity_tournament -v

The tournament reports frontier requests and generated candidate states, not a
fabricated count of fully expanded states. Runtime is descriptive.
"""
from __future__ import annotations

from itertools import product
from time import perf_counter
from unittest import TestCase
from unittest.mock import patch

import elfcalc.bounded_search as search
from elfcalc.register_schedule import estimate_peak_live_values, schedule_value_dag


FIXTURES = (
    {"name": "shared_factor", "starts": (2, 3), "targets": (12, 18, 99),
     "limit": 1000, "max_intermediates": 1, "max_depth": 3,
     "beam_width": 16, "max_expansions_per_state": 24},
    {"name": "shared_bridge", "starts": (2, 3), "targets": (12, 35),
     "limit": 1000, "max_intermediates": 2, "max_depth": 4,
     "beam_width": 12, "max_expansions_per_state": 24},
    {"name": "multi_family", "starts": (2, 3, 5), "targets": (10, 12, 15, 18, 99),
     "limit": 1000, "max_intermediates": 1, "max_depth": 5,
     "beam_width": 16, "max_expansions_per_state": 24},
    {"name": "provenance_collision", "starts": (2, 3), "targets": (10, 12, 35),
     "limit": 1000, "max_intermediates": 3, "max_depth": 5,
     "beam_width": 8, "max_expansions_per_state": 16},
)


def _original_state_key(state, starts):
    return (
        tuple(sorted(state.missing)),
        tuple(sorted(state.available)),
        len(state.operations),
        search._peak(state, starts),
        state.intermediates,
    )


def _ordinary_admission(states, beam_width, starts, limit, subgraph_support=None):
    return tuple(sorted(
        states,
        key=lambda state: search._rank(state, starts, limit, subgraph_support),
    )[:beam_width])


class SearchDiversityTournamentTests(TestCase):
    def test_eight_way_tournament_across_synthetic_families(self):
        rows = []
        configurations = (
            ("original_dedup", False, False),
            ("provenance", True, False),
            ("provenance_diverse", True, True),
        )

        for fixture in FIXTURES:
            for (strategy, provenance, diversity), cache_enabled in product(
                configurations, (False, True)
            ):
                counters = {
                    "frontier_requests": 0,
                    "candidate_state_proposals": 0,
                    "frontiers_generated": 0,
                }
                native_cached = search._cached_pair_recipes
                native_key = search._state_key
                native_admission = search._select_diverse_beam

                def counted_key(state, starts):
                    counters["candidate_state_proposals"] += 1
                    if provenance:
                        return native_key(state, starts)
                    return _original_state_key(state, starts)

                def counted_frontier(values, limit):
                    counters["frontier_requests"] += 1
                    if cache_enabled:
                        return native_cached(values, limit)
                    counters["frontiers_generated"] += 1
                    return tuple(search._pair_recipes(values, limit))

                selected_admission = native_admission if diversity else _ordinary_admission
                search._cached_pair_recipes.cache_clear()
                started = perf_counter()
                with (
                    patch.object(search, "_state_key", counted_key),
                    patch.object(search, "_select_diverse_beam", selected_admission),
                    patch.object(search, "_cached_pair_recipes", counted_frontier),
                ):
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
                self.assertTrue(allocation, (fixture["name"], strategy, cache_enabled))
                self.assertEqual(
                    set(plan.covered_targets).union(plan.missing_targets),
                    set(fixture["targets"]),
                )
                rows.append({
                    "fixture": fixture["name"],
                    "strategy": strategy,
                    "cache": cache_enabled,
                    "coverage": len(plan.covered_targets),
                    "instructions": len(plan.operations),
                    "peak_live": estimate_peak_live_values(plan.operations, fixture["starts"]),
                    "frontier_requests": counters["frontier_requests"],
                    "candidate_state_proposals": counters["candidate_state_proposals"],
                    "frontiers_generated": counters["frontiers_generated"],
                    "elapsed_seconds": round(elapsed, 6),
                })

        for fixture in FIXTURES:
            for strategy, _, _ in configurations:
                pair = [row for row in rows
                        if row["fixture"] == fixture["name"] and row["strategy"] == strategy]
                self.assertEqual(len(pair), 2)
                self.assertEqual(
                    (pair[0]["coverage"], pair[0]["instructions"], pair[0]["peak_live"]),
                    (pair[1]["coverage"], pair[1]["instructions"], pair[1]["peak_live"]),
                )

        print("SEARCH_DIVERSITY_FRONTIER_TOURNAMENT")
        for row in rows:
            print(row)
