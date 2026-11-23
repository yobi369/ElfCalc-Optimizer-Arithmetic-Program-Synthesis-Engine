import unittest

from elfcalc.shared_intermediate import plan_shared_intermediates


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

    def test_rejects_target_above_value_limit(self):
        with self.assertRaises(ValueError):
            plan_shared_intermediates([7, 9], [63], 20)

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
