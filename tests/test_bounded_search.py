import unittest

from elfcalc.bounded_search import plan_bounded_beam


class BoundedBeamPlannerTests(unittest.TestCase):
    def test_finds_three_intermediate_power_chain(self):
        # 2 -> 4 -> 16 -> 256 -> 65536.
        plan = plan_bounded_beam(
            [2], [65536], 100000,
            max_intermediates=3, max_depth=4, beam_width=24,
        )
        self.assertEqual(plan.missing_targets, ())
        self.assertEqual(plan.intermediate_count, 3)
        self.assertEqual(plan.operations[-1].result, 65536)

    def test_respects_intermediate_budget(self):
        plan = plan_bounded_beam(
            [2], [65536], 100000,
            max_intermediates=2, max_depth=4, beam_width=24,
        )
        self.assertEqual(plan.missing_targets, (65536,))
        self.assertLessEqual(plan.intermediate_count, 2)

    def test_is_deterministic(self):
        args = ([2, 3], [16, 24], 100)
        first = plan_bounded_beam(*args, max_depth=3, beam_width=12)
        second = plan_bounded_beam(*args, max_depth=3, beam_width=12)
        self.assertEqual(first, second)

    def test_initial_target_needs_no_operations(self):
        plan = plan_bounded_beam([2, 3], [2, 3], 20)
        self.assertEqual(plan.operations, ())
        self.assertEqual(plan.missing_targets, ())


if __name__ == "__main__":
    unittest.main()
