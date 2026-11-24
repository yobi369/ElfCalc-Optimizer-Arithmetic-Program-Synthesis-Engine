"""Adaptive beam admission ablation on deterministic synthetic fixtures.

The adaptive policy intervenes only when the selected beam is root-concentrated
and an excluded distinct-root candidate has strictly stronger immediate target
yield than the weakest selected state. All proposals are scheduler/VM validated.
"""
from unittest import TestCase
from unittest.mock import patch

import elfcalc.bounded_search as search
from tests.test_search_diversity_tournament import FIXTURES, _ordinary_admission
from elfcalc.puzzle import Puzzle
from elfcalc.register_schedule import estimate_peak_live_values, schedule_value_dag
from elfcalc.validation import validate_program


class AdaptiveBeamSelectorTests(TestCase):

    def test_adaptive_reserves_only_for_a_distinct_branch_with_stronger_yield(self):
        starts = (2, 3, 4, 5)
        limit = 100
        target = 72
        root_a = search._State(
            operations=(
                search.PlannedOperation(2, "+", 4, 6, False),
                search.PlannedOperation(3, "+", 5, 8, False),
            ),
            available=frozenset((*starts, 6, 8)),
            missing=frozenset((target,)),
            intermediates=2,
        )
        sibling_a = search._State(
            operations=(
                search.PlannedOperation(2, "+", 4, 6, False),
                search.PlannedOperation(3, "*", 3, 9, False),
            ),
            available=frozenset((*starts, 6, 9)),
            missing=frozenset((target,)),
            intermediates=2,
        )
        alternative_b = search._State(
            operations=(
                search.PlannedOperation(3, "+", 5, 8, False),
                search.PlannedOperation(3, "*", 3, 9, False),
            ),
            available=frozenset((*starts, 8, 9)),
            missing=frozenset((target,)),
            intermediates=2,
        )
        def adversarial_rank(state, *_args):
            return (0 if state is root_a else 1 if state is sibling_a else 2,)

        with patch.object(search, "_rank", side_effect=adversarial_rank):
            selected = search._select_adaptive_beam(
                (root_a, sibling_a, alternative_b), 2, starts, limit
            )
        self.assertEqual(selected, (root_a, alternative_b))
        self.assertEqual(search._direct_yield(alternative_b, limit), 1)

    def test_adaptive_end_to_end_ablation_matches_exact_replay(self):
        policies = (
            ("ordinary", _ordinary_admission),
            ("always_diverse", search._select_diverse_beam),
            ("adaptive", search._select_adaptive_beam),
        )
        rows = []
        for fixture in FIXTURES:
            for name, selector in policies:
                search._cached_pair_recipes.cache_clear()
                with patch.object(search, "_select_diverse_beam", selector):
                    plan = search.plan_bounded_beam(
                        fixture["starts"], fixture["targets"], fixture["limit"],
                        max_intermediates=fixture["max_intermediates"],
                        max_depth=fixture["max_depth"],
                        beam_width=fixture["beam_width"],
                        max_expansions_per_state=fixture["max_expansions_per_state"],
                        enable_complete_witnesses=False,
                        enable_partial_motifs=False,
                    )
                allocation = schedule_value_dag(
                    plan.operations, fixture["starts"], fixture["limit"]
                )
                covered = tuple(sorted(plan.covered_targets))
                self.assertTrue(covered, (fixture["name"], name))
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
                    "policy": name,
                    "coverage": len(plan.covered_targets),
                    "instructions": len(plan.operations),
                    "peak_live": estimate_peak_live_values(plan.operations, fixture["starts"]),
                })

        for fixture in FIXTURES:
            family = [row for row in rows if row["fixture"] == fixture["name"]]
            self.assertEqual(len(family), 3)
        print("ADAPTIVE_BEAM_ABLATION")
        for row in rows:
            print(row)
