import unittest

from elfcalc.bounded_search import (
    _backward_target_cone,
    _forward_anchor_pool,
    _multi_target_cone_support,
    plan_bounded_beam,
)
from elfcalc.register_schedule import schedule_value_dag


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
        # The planner itself now requires the same register allocator and VM
        # replay used by the production lowering path.
        self.assertTrue(schedule_value_dag(plan.operations, [2], 100000))

    def test_reverse_cone_contains_three_step_power_chain(self):
        anchors = _forward_anchor_pool((2,), 100000, 4, 512)
        cone = _backward_target_cone(frozenset({65536}), anchors, 100000, 4, 4096)
        self.assertTrue({2, 4, 16, 256, 65536}.issubset(cone))

    def test_reverse_cone_inverts_all_arithmetic_directions(self):
        # t=20 with anchor 5 admits x+5, x-5, x*5, and x/5.
        cone = _backward_target_cone(
            frozenset({20}), (5,), 1000, 1, 128
        )
        self.assertTrue({15, 25, 4, 100}.issubset(cone))

        # t=5 with anchor 25 admits 25-x=5 and 25/x=5.
        reverse = _backward_target_cone(
            frozenset({5}), (25,), 1000, 1, 128
        )
        self.assertIn(20, reverse)

        # Exact division in both orientations: 21/3=7 and 21/3=7
        # when solving the unknown divisor.
        quotient = _backward_target_cone(
            frozenset({7}), (3, 21), 1000, 1, 128
        )
        self.assertIn(21, quotient)
        self.assertIn(3, quotient)

    def test_multi_target_cone_identifies_shared_intermediate(self):
        # 6 can unlock 12 via 6*2 and 18 via 6*3.
        support = _multi_target_cone_support(
            frozenset({12, 18}), (2, 3), 1000, 1, 128
        )
        self.assertEqual(support[6], frozenset({12, 18}))

    def test_beam_uses_shared_intermediate_for_multiple_targets(self):
        plan = plan_bounded_beam(
            [2, 3], [12, 18], 1000,
            max_intermediates=1, max_depth=3, beam_width=64,
        )
        self.assertEqual(plan.missing_targets, ())
        self.assertEqual(plan.intermediate_count, 1)
        self.assertIn(6, {op.result for op in plan.operations})
        self.assertTrue(schedule_value_dag(plan.operations, [2, 3], 1000))

    def test_multi_target_cone_is_deterministic(self):
        args = (frozenset({12, 18, 24}), (2, 3), 1000, 2, 128)
        self.assertEqual(
            _multi_target_cone_support(*args),
            _multi_target_cone_support(*args),
        )

    def test_reverse_cone_is_bounded_and_deterministic(self):
        anchors = _forward_anchor_pool((2, 3), 1000, 3, 128)
        first = _backward_target_cone(frozenset({72}), anchors, 1000, 3, 256)
        second = _backward_target_cone(frozenset({72}), anchors, 1000, 3, 256)
        self.assertEqual(first, second)
        self.assertLessEqual(len(first), 256)

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

    def test_rejects_invalid_value_limit(self):
        with self.assertRaises(ValueError):
            plan_bounded_beam([2], [4], 0)

    def test_initial_target_needs_no_operations(self):
        plan = plan_bounded_beam([2, 3], [2, 3], 20)
        self.assertEqual(plan.operations, ())
        self.assertEqual(plan.missing_targets, ())


if __name__ == "__main__":
    unittest.main()
