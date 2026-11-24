import unittest

from elfcalc.shared_intermediate import (
    _apply,
    _candidate_target_yields,
    _pair_recipes,
    _pair_recipes_for_pair,
    _recipe_order,
    plan_shared_intermediates,
)


class SharedIntermediatePlannerTests(unittest.TestCase):
    def test_direct_target_is_covered_without_intermediate(self):
        plan = plan_shared_intermediates([2, 3], [5, 6], 20)
        self.assertEqual(plan.covered_targets, frozenset({5, 6}))
        self.assertEqual(plan.missing_targets, ())
        self.assertEqual(plan.intermediate_count, 0)

    def test_shared_intermediate_unlocks_multiple_targets(self):
        # 2*3=6 creates one reusable value; 6+2=8 and 6*2=12.
        plan = plan_shared_intermediates([2, 3], [8, 12], 20)
        self.assertEqual(plan.covered_targets, frozenset({8, 12}))
        self.assertEqual(plan.missing_targets, ())
        self.assertEqual(plan.intermediate_count, 1)
        self.assertEqual(plan.instruction_count, 3)
        # The cost-aware tie-break now selects 6 (2*3), which has lower
        # estimated live-value pressure under the scheduler's ordering.
        self.assertEqual(plan.operations[0].result, 6)

    def test_inverse_target_cones_match_brute_force_relations(self):
        available = (2, 3, 4, 6, 8, 12)
        limit = 100
        recipes = {
            recipe.result: recipe
            for recipe in _pair_recipes(available, limit)
            if recipe.result not in available
        }
        missing = frozenset(range(1, 31))
        indexed = _candidate_target_yields(recipes, available, missing, limit)

        for candidate in recipes:
            expected = set()
            for target in missing:
                if target == candidate:
                    continue  # The candidate's own target status is scored separately.
                for other in available:
                    for left, right in ((candidate, other), (other, candidate)):
                        if any(
                            _apply(left, operator, right, limit) == target
                            for operator in ("+", "-", "*", "/")
                        ):
                            expected.add(target)
            actual = {relation.result for relation in indexed.get(candidate, ())}
            self.assertEqual(actual, expected, candidate)

    def test_incremental_pair_frontier_matches_full_rebuild(self):
        values = (2, 3, 4, 6, 8, 12)
        limit = 100
        full = {}
        for recipe in _pair_recipes(values, limit):
            if recipe.result not in values:
                previous = full.get(recipe.result)
                if previous is None or _recipe_order(recipe) < _recipe_order(previous):
                    full[recipe.result] = recipe

        incremental = {}
        for index, value in enumerate(values):
            for other in values[:index + 1]:
                for recipe in _pair_recipes_for_pair(value, other, limit):
                    if recipe.result in values:
                        continue
                    previous = incremental.get(recipe.result)
                    if previous is None or _recipe_order(recipe) < _recipe_order(previous):
                        incremental[recipe.result] = recipe
        self.assertEqual(incremental, full)

    def test_two_intermediate_chain_unlocks_a_target(self):
        plan = plan_shared_intermediates([2, 3], [16], 20)
        self.assertEqual(plan.covered_targets, frozenset({16}))
        self.assertEqual(plan.missing_targets, ())
        self.assertEqual(plan.intermediate_count, 2)
        self.assertEqual(tuple(op.result for op in plan.operations), (4, 8, 16))

    def test_independent_intermediates_cooperate_to_make_target(self):
        # 2/2=1 and 5*5=25 are independent; 1+25=26.
        plan = plan_shared_intermediates([2, 5], [26], 100)
        self.assertEqual(plan.covered_targets, frozenset({26}))
        self.assertEqual(plan.missing_targets, ())
        self.assertEqual(plan.intermediate_count, 2)
        self.assertEqual(tuple(op.result for op in plan.operations), (1, 25, 26))

    def test_cooperating_search_does_not_reuse_missing_target_as_intermediate(self):
        from elfcalc.shared_intermediate import _best_cooperating_intermediates

        available = (2, 5)
        missing = frozenset({7, 26})
        recipes = {
            recipe.result: recipe
            for recipe in _pair_recipes(available, 100)
            if recipe.result not in available
        }
        result = _best_cooperating_intermediates(recipes, missing, 100)
        self.assertIsNotNone(result)
        first, second, target_recipes = result
        self.assertNotIn(first.result, missing)
        self.assertNotIn(second.result, missing)
        self.assertTrue(all(recipe.result not in (first.result, second.result)
                            for recipe in target_recipes))

    def test_cooperating_intermediates_respect_budget(self):
        plan = plan_shared_intermediates([2, 5], [26], 100, max_intermediates=1)
        self.assertEqual(plan.missing_targets, (26,))
        self.assertEqual(plan.intermediate_count, 0)

    def test_two_intermediate_chain_respects_budget(self):
        plan = plan_shared_intermediates([2, 3], [16], 20, max_intermediates=1)
        self.assertEqual(plan.covered_targets, frozenset())
        self.assertEqual(plan.missing_targets, (16,))
        self.assertEqual(plan.intermediate_count, 0)

    def test_rejects_target_above_value_limit(self):
        with self.assertRaises(ValueError):
            plan_shared_intermediates([7, 9], [63], 20)

    def test_direct_targets_are_prioritized_over_speculative_intermediates(self):
        plan = plan_shared_intermediates([2, 3, 4], [5, 14], 20)
        self.assertTrue(plan.operations[0].is_target)
        self.assertEqual(plan.operations[0].result, 5)
        self.assertEqual(plan.missing_targets, ())

    def test_generated_operations_stay_within_value_limit(self):
        plan = plan_shared_intermediates([7, 9], [16, 18], 20)
        self.assertEqual(plan.missing_targets, ())
        self.assertTrue(all(0 < op.result <= 20 for op in plan.operations))

    def test_initial_targets_are_already_covered(self):
        plan = plan_shared_intermediates([2, 3], [2, 3], 10)
        self.assertEqual(plan.operations, ())
        self.assertEqual(plan.covered_targets, frozenset({2, 3}))

    def test_intermediate_budget_is_respected(self):
        plan = plan_shared_intermediates([2, 3], [8, 12], 20, max_intermediates=0)
        self.assertEqual(plan.missing_targets, (8, 12))
        self.assertEqual(plan.intermediate_count, 0)

    def test_invalid_duplicate_targets_rejected(self):
        with self.assertRaises(ValueError):
            plan_shared_intermediates([2, 3], [5, 5], 10)


if __name__ == "__main__":
    unittest.main()
