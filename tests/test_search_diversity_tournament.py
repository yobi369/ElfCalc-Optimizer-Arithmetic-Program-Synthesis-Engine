"""Six-configuration synthetic tournament for beam identity, diversity, and caching.

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
from elfcalc.puzzle import Puzzle
from elfcalc.validation import validate_program
from elfcalc.shared_intermediate import PlannedOperation


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

    def test_diversity_reserves_a_slot_for_a_lower_ranked_distinct_root(self):
        starts = (2, 3, 4, 5)
        missing = frozenset((11,))
        available = frozenset((2, 3, 4, 5, 6, 8))
        root_a = PlannedOperation(2, "+", 4, 6, False)
        root_b = PlannedOperation(3, "+", 3, 6, False)
        tail_a = PlannedOperation(3, "+", 5, 8, False)
        tail_b = PlannedOperation(2, "*", 4, 8, False)
        top_a = search._State((root_a, tail_a), available, missing, 2)
        second_a = search._State((root_a, tail_b), available, missing, 2)
        lower_ranked_b = search._State((root_b, tail_a), available, missing, 2)

        # The ordinary rank ties these states; input order represents the
        # deterministic tie-break. Two top slots would otherwise be spent on
        # descendants of the same first recipe.
        ranked = (top_a, second_a, lower_ranked_b)
        with patch.object(search, "_rank", side_effect=lambda state, *_: (
            0 if state is top_a else 1 if state is second_a else 2
        )):
            selected = search._select_diverse_beam(
                ranked, 2, starts, 100
            )

        self.assertEqual(selected, (top_a, lower_ranked_b))
        self.assertEqual(
            (selected[0].operations[0].result, selected[0].operations[0].operator,
             selected[0].operations[0].left, selected[0].operations[0].right),
            (6, "+", 2, 4),
        )
        self.assertEqual(
            (selected[1].operations[0].result, selected[1].operations[0].operator,
             selected[1].operations[0].left, selected[1].operations[0].right),
            (6, "+", 3, 3),
        )

    def test_reserved_branch_survives_to_expose_a_target_the_leader_cannot(self):
        starts = (2, 3, 4, 5)
        missing = frozenset((40,))
        root_a = PlannedOperation(2, "+", 4, 6, False)
        root_b = PlannedOperation(3, "+", 5, 8, False)
        leader = search._State(
            (root_a,), frozenset((*starts, 6)), missing, 1
        )
        alternative = search._State(
            (root_b,), frozenset((*starts, 8)), missing, 1
        )

        # The leader has no one-step recipe for 40; the distinct branch does:
        # 8 * 5 = 40. Force the leader to rank first to test reservation itself.
        self.assertEqual(search._direct_yield(leader, 100), 0)
        self.assertEqual(search._direct_yield(alternative, 100), 1)
        with patch.object(search, "_rank", side_effect=lambda state, *_: (
            0 if state is leader else 1
        )):
            selected = search._select_diverse_beam(
                (leader, alternative), 2, starts, 100
            )

        self.assertEqual(selected, (leader, alternative))
        surviving = selected[1]
        next_recipe = next(
            recipe for recipe in search._cached_pair_recipes(
                tuple(sorted(surviving.available)), 100
            )
            if recipe.result == 40
        )
        completion = PlannedOperation(
            next_recipe.left, next_recipe.operator,
            next_recipe.right, next_recipe.result, True,
        )
        winning_operations = surviving.operations + (completion,)
        allocation = schedule_value_dag(winning_operations, starts, 100)
        replay = validate_program(
            Puzzle("reserved_branch_completion", starts, (40,), 100),
            allocation,
        )
        self.assertTrue(replay.complete, replay.error)
        self.assertEqual(len(allocation), 2)
        self.assertEqual(search._direct_yield(leader, 100), 0)

    def test_six_configuration_tournament_across_synthetic_families(self):
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
                native_pair_recipes = search._pair_recipes
                native_key = search._state_key
                native_admission = search._select_diverse_beam

                def counted_key(state, starts):
                    counters["candidate_state_proposals"] += 1
                    if provenance:
                        return native_key(state, starts)
                    return _original_state_key(state, starts)

                def counted_pair_recipes(values, limit):
                    counters["frontiers_generated"] += 1
                    return native_pair_recipes(values, limit)

                def counted_frontier(values, limit):
                    counters["frontier_requests"] += 1
                    if cache_enabled:
                        return native_cached(values, limit)
                    return tuple(search._pair_recipes(values, limit))

                selected_admission = native_admission if diversity else _ordinary_admission
                search._cached_pair_recipes.cache_clear()
                started = perf_counter()
                with (
                    patch.object(search, "_state_key", counted_key),
                    patch.object(search, "_select_diverse_beam", selected_admission),
                    patch.object(search, "_cached_pair_recipes", counted_frontier),
                    patch.object(search, "_pair_recipes", counted_pair_recipes),
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
                self.assertEqual(len(allocation), len(plan.operations))
                covered = tuple(sorted(plan.covered_targets))
                self.assertTrue(covered, (fixture["name"], strategy, cache_enabled))
                replay = validate_program(
                    Puzzle(fixture["name"], fixture["starts"], covered, fixture["limit"]),
                    allocation,
                )
                self.assertTrue(replay.complete, replay.error)
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
                cached = next(row for row in pair if row["cache"])
                uncached = next(row for row in pair if not row["cache"])
                self.assertLessEqual(cached["frontiers_generated"], uncached["frontiers_generated"])

        print("SEARCH_DIVERSITY_FRONTIER_TOURNAMENT")
        for row in rows:
            print(row)
