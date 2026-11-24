import unittest

from elfcalc.bounded_search import (
    _backward_target_cone,
    _forward_anchor_pool,
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
