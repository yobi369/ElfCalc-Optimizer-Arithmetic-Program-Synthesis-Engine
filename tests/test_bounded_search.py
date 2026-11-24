import unittest
from time import perf_counter

from elfcalc.bounded_search import (
    _backward_target_cone,
    _forward_anchor_pool,
    _multi_target_cone_support,
    _shared_completion_yield,
    _shared_subgraph_witnesses,
    _partial_subgraph_motifs,
    _State,
    _cached_pair_recipes,
    _state_key,
    _select_diverse_beam,
    plan_bounded_beam,
)
from elfcalc.register_schedule import estimate_peak_live_values, schedule_value_dag
from elfcalc.shared_intermediate import PlannedOperation


class BoundedBeamPlannerTests(unittest.TestCase):
    def test_beam_selection_reserves_distinct_first_recipe_families(self):
        same_root_a = _State(
            operations=(
                PlannedOperation(2, "+", 2, 4, False),
                PlannedOperation(2, "*", 3, 6, False),
            ),
            available=frozenset({2, 3, 4, 6}),
            missing=frozenset({10}),
            intermediates=2,
        )
        same_root_b = _State(
            operations=(
                PlannedOperation(2, "+", 2, 4, False),
                PlannedOperation(3, "+", 3, 6, False),
            ),
            available=frozenset({2, 3, 4, 6}),
            missing=frozenset({10}),
            intermediates=2,
        )
        different_root = _State(
            operations=(
                PlannedOperation(2, "*", 2, 4, False),
                PlannedOperation(2, "*", 3, 6, False),
            ),
            available=frozenset({2, 3, 4, 6}),
            missing=frozenset({10}),
            intermediates=2,
        )
        selected = _select_diverse_beam(
            (same_root_a, same_root_b, different_root),
            2, (2, 3), 1000,
        )
        roots = {
            next(op.operator for op in state.operations if not op.is_target)
            for state in selected
        }
        self.assertEqual(roots, {"+", "*"})

    def test_pair_recipe_frontier_cache_reuses_exact_results(self):
        _cached_pair_recipes.cache_clear()
        first = _cached_pair_recipes((2, 3, 5), 1000)
        second = _cached_pair_recipes((2, 3, 5), 1000)
        self.assertIs(first, second)
        self.assertEqual(
            {(r.left, r.operator, r.right, r.result) for r in first},
            {(r.left, r.operator, r.right, r.result) for r in second},
        )

    def test_state_key_preserves_distinct_recipe_provenance(self):
        left = _State(
            operations=(
                PlannedOperation(
                    2, "+", 2, 4, False
                ),
            ),
            available=frozenset({2, 3, 4}),
            missing=frozenset({10}),
            intermediates=1,
        )
        right = _State(
            operations=(
                __import__("elfcalc.shared_intermediate", fromlist=["PlannedOperation"]).PlannedOperation(
                    2, "*", 2, 4, False
                ),
            ),
            available=frozenset({2, 3, 4}),
            missing=frozenset({10}),
            intermediates=1,
        )
        self.assertEqual(len(left.operations), len(right.operations))
        self.assertEqual(left.available, right.available)
        self.assertNotEqual(_state_key(left, (2, 3)), _state_key(right, (2, 3)))

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

    def test_two_node_shared_subgraph_supports_multiple_targets(self):
        # 2+3=5, then 5+2=7; the pair 5 and 7 unlocks
        # both 12 (5+7) and 35 (5*7).
        from elfcalc.bounded_search import _shared_subgraph_support

        support = _shared_subgraph_support(
            (2, 3), frozenset({12, 35}), 1000
        )
        self.assertEqual(support[5], frozenset({12, 35}))

    def test_bridge_node_scores_joint_shared_target_completion(self):
        state = _State(
            operations=(),
            available=frozenset({2, 3, 5}),
            missing=frozenset({12, 35}),
            intermediates=1,
        )
        support = {5: frozenset({12, 35})}
        self.assertEqual(
            _shared_completion_yield(state, 7, 1000, support),
            2,
        )

    def test_shared_subgraph_witnesses_are_concrete_and_deterministic(self):
        args = ((2, 3), frozenset({12, 35}), 1000)
        first = _shared_subgraph_witnesses(*args)
        second = _shared_subgraph_witnesses(*args)
        self.assertEqual(first, second)
        self.assertTrue(first)
        witness = first[0]
        self.assertEqual(
            tuple(operation.result for operation in witness),
            (5, 7, 12, 35),
        )
        self.assertTrue(schedule_value_dag(witness, [2, 3], 1000))

    def test_bounded_witness_search_reaches_three_intermediate_motif(self):
        from elfcalc.bounded_search import _shared_subgraph_witnesses

        starts = (2, 3)
        goals = frozenset({250, 375})
        shallow = _shared_subgraph_witnesses(
            starts, goals, 1000, max_intermediates=2
        )
        self.assertEqual(shallow, ())

        plan = plan_bounded_beam(
            starts, tuple(sorted(goals)), 1000,
            max_intermediates=3, max_depth=5, beam_width=64,
        )
        self.assertEqual(plan.missing_targets, ())
        self.assertLessEqual(plan.intermediate_count, 3)
        self.assertTrue({250, 375}.issubset(
            {operation.result for operation in plan.operations}
        ))
        self.assertTrue(schedule_value_dag(plan.operations, starts, 1000))

    def test_equal_parameter_budget_strategy_comparison(self):
        # All modes share identical beam width, depth, intermediate budget,
        # and per-state expansion cap. Only the optional motif layers differ.
        common = dict(
            max_intermediates=1,
            max_depth=3,
            beam_width=32,
            max_expansions_per_state=64,
            motif_state_budget=128,
            motif_recipe_budget=16,
            motif_result_budget=16,
        )
        modes = {}
        elapsed_seconds = {}

        def run_mode(name, **flags):
            started = perf_counter()
            modes[name] = plan_bounded_beam(
                [2, 3], [12, 18, 99], 1000, **flags, **common
            )
            elapsed_seconds[name] = perf_counter() - started

        run_mode(
            "beam_only",
            enable_complete_witnesses=False,
            enable_partial_motifs=False,
        )
        run_mode(
            "complete_witness",
            enable_complete_witnesses=True,
            enable_partial_motifs=False,
        )
        run_mode(
            "partial_motif",
            enable_complete_witnesses=False,
            enable_partial_motifs=True,
        )
        metrics = {}
        for name, plan in modes.items():
            allocation = schedule_value_dag(plan.operations, [2, 3], 1000)
            self.assertTrue(allocation)
            self.assertEqual(
                set(plan.covered_targets).union(plan.missing_targets),
                {12, 18, 99},
            )
            metrics[name] = {
                "coverage": len(plan.covered_targets),
                "instructions": len(plan.operations),
                "peak_live": estimate_peak_live_values(plan.operations, [2, 3]),
            }
            self.assertLessEqual(metrics[name]["instructions"], common["max_depth"])
        self.assertEqual(set(metrics), {"beam_only", "complete_witness", "partial_motif"})
        print("SYNTHETIC_STRATEGY_METRICS", {
            name: {**metrics[name], "elapsed_seconds": elapsed_seconds[name]}
            for name in sorted(metrics)
        })
        self.assertGreaterEqual(
            len(modes["partial_motif"].covered_targets),
            2,
        )
        self.assertLessEqual(
            len(modes["partial_motif"].operations),
            common["max_depth"],
        )

    def test_strategy_comparison_on_two_stage_shared_bridge(self):
        # The 5 -> 7 bridge jointly unlocks 12 and 35:
        # 2+3=5, 5+2=7, 5+7=12, 5*7=35.
        common = dict(
            max_intermediates=2,
            max_depth=4,
            beam_width=24,
            max_expansions_per_state=32,
            motif_state_budget=256,
            motif_recipe_budget=24,
            motif_result_budget=24,
        )
        modes = {}
        elapsed = {}

        def run_mode(name, **flags):
            started = perf_counter()
            modes[name] = plan_bounded_beam(
                [2, 3], [12, 35], 1000, **flags, **common
            )
            elapsed[name] = perf_counter() - started

        run_mode("beam_only", enable_complete_witnesses=False,
                 enable_partial_motifs=False)
        run_mode("complete_witness", enable_complete_witnesses=True,
                 enable_partial_motifs=False)
        run_mode("partial_motif", enable_complete_witnesses=False,
                 enable_partial_motifs=True)

        metrics = {}
        for name, plan in modes.items():
            self.assertTrue(schedule_value_dag(plan.operations, [2, 3], 1000))
            self.assertEqual(
                set(plan.covered_targets).union(plan.missing_targets),
                {12, 35},
            )
            metrics[name] = {
                "coverage": len(plan.covered_targets),
                "instructions": len(plan.operations),
                "peak_live": estimate_peak_live_values(plan.operations, [2, 3]),
                "elapsed_seconds": elapsed[name],
            }
        print("SHARED_BRIDGE_STRATEGY_METRICS", metrics)
        self.assertEqual(metrics["beam_only"]["coverage"], 1)
        self.assertEqual(metrics["complete_witness"]["coverage"], 2)
        self.assertEqual(metrics["partial_motif"]["coverage"], 2)
        self.assertEqual(metrics["complete_witness"]["instructions"], 4)
        self.assertEqual(metrics["partial_motif"]["instructions"], 4)

    def test_witness_frontier_preserves_distinct_recipe_provenance(self):
        # 4 can be produced as either 2+2 or 2*2. Both derivations can
        # participate in a valid 4+6=10 witness and must not be collapsed
        # merely because their available-value sets and prefix lengths match.
        witnesses = _shared_subgraph_witnesses(
            (2, 3), frozenset({10}), 1000,
            max_intermediates=2,
            max_recipes_per_state=128,
            max_states=4096,
            max_witnesses=64,
        )
        four_recipes = {
            (op.operator, op.left, op.right)
            for witness in witnesses
            for op in witness
            if op.result == 4
        }
        self.assertIn(("+", 2, 2), four_recipes)
        self.assertIn(("*", 2, 2), four_recipes)
        for witness in witnesses:
            self.assertTrue(schedule_value_dag(witness, [2, 3], 1000))

    def test_partial_motif_finds_useful_subset_when_complete_witness_is_impossible(self):
        starts = (2, 3)
        goals = frozenset({12, 18, 99})
        complete = _shared_subgraph_witnesses(
            starts, goals, 1000,
            max_intermediates=1,
            max_recipes_per_state=128,
            max_states=4096,
            max_witnesses=64,
        )
        partial = _partial_subgraph_motifs(
            starts, goals, 1000,
            max_intermediates=1,
            max_recipes_per_state=128,
            max_states=4096,
            max_candidates=64,
        )
        self.assertEqual(complete, ())
        self.assertTrue(partial)
        operations, covered = partial[0]
        self.assertEqual(covered, frozenset({12, 18}))
        self.assertEqual(len(operations), 3)
        self.assertEqual(operations[0].result, 6)
        self.assertTrue(schedule_value_dag(operations, starts, 1000))

    def test_partial_motif_accumulates_multiple_target_families(self):
        # Direct targets 10 and 15 coexist with the shared-factor pair
        # 12 and 18. A single intermediate 6 unlocks the latter pair;
        # 99 is deliberately outside this one-intermediate frontier.
        starts = (2, 3, 5)
        goals = frozenset({10, 12, 15, 18, 99})
        complete = _shared_subgraph_witnesses(
            starts, goals, 1000,
            max_intermediates=1,
            max_recipes_per_state=128,
            max_states=4096,
            max_witnesses=64,
        )
        partial = _partial_subgraph_motifs(
            starts, goals, 1000,
            max_intermediates=1,
            max_recipes_per_state=128,
            max_states=4096,
            max_candidates=64,
        )
        self.assertEqual(complete, ())
        operations, covered = partial[0]
        self.assertEqual(covered, frozenset({10, 12, 15, 18}))
        self.assertEqual(len(operations), 5)
        self.assertIn(6, {op.result for op in operations})
        self.assertTrue(schedule_value_dag(operations, starts, 1000))

        plan = plan_bounded_beam(
            starts, sorted(goals), 1000,
            max_intermediates=1, max_depth=5, beam_width=32,
            enable_complete_witnesses=False,
            enable_partial_motifs=True,
        )
        self.assertEqual(set(plan.covered_targets), {10, 12, 15, 18})
        self.assertEqual(set(plan.missing_targets), {99})
        self.assertTrue(schedule_value_dag(plan.operations, starts, 1000))

    def test_multi_family_partial_motif_strategy_comparison(self):
        starts = [2, 3, 5]
        goals = [10, 12, 15, 18, 99]
        common = dict(
            max_intermediates=1,
            max_depth=5,
            beam_width=32,
            max_expansions_per_state=64,
            motif_state_budget=4096,
            motif_recipe_budget=128,
            motif_result_budget=64,
        )
        modes = {}
        elapsed = {}

        def run_mode(name, **flags):
            started = perf_counter()
            modes[name] = plan_bounded_beam(
                starts, goals, 1000, **flags, **common
            )
            elapsed[name] = perf_counter() - started

        run_mode("beam_only", enable_complete_witnesses=False,
                 enable_partial_motifs=False)
        run_mode("complete_witness", enable_complete_witnesses=True,
                 enable_partial_motifs=False)
        run_mode("partial_motif", enable_complete_witnesses=False,
                 enable_partial_motifs=True)

        metrics = {}
        for name, plan in modes.items():
            self.assertTrue(schedule_value_dag(plan.operations, starts, 1000))
            self.assertEqual(
                set(plan.covered_targets).union(plan.missing_targets),
                set(goals),
            )
            metrics[name] = {
                "coverage": len(plan.covered_targets),
                "instructions": len(plan.operations),
                "peak_live": estimate_peak_live_values(plan.operations, starts),
                "elapsed_seconds": elapsed[name],
            }
        print("MULTI_FAMILY_STRATEGY_METRICS", metrics)
        self.assertEqual(metrics["partial_motif"]["coverage"], 4)

    def test_partial_motifs_rank_target_yield_per_instruction(self):
        candidates = _partial_subgraph_motifs(
            (2, 3), frozenset({12, 18, 99}), 1000,
            max_intermediates=1, max_states=1024,
        )
        self.assertTrue(candidates)
        operations, covered = candidates[0]
        self.assertEqual(covered, frozenset({12, 18}))
        self.assertEqual(len(operations), 3)
        self.assertEqual(operations[0].result, 6)
        self.assertTrue(schedule_value_dag(operations, [2, 3], 1000))

    def test_partial_motif_respects_total_instruction_depth(self):
        plan = plan_bounded_beam(
            [2, 3], [12, 18, 99], 1000,
            max_intermediates=1, max_depth=2, beam_width=64,
        )
        self.assertLessEqual(len(plan.operations), 2)
        self.assertTrue(schedule_value_dag(plan.operations, [2, 3], 1000))

    def test_planner_returns_best_partial_motif_when_goals_remain(self):
        plan = plan_bounded_beam(
            [2, 3], [12, 18, 99], 1000,
            max_intermediates=1, max_depth=3, beam_width=64,
        )
        self.assertEqual(set(plan.covered_targets), {12, 18})
        self.assertEqual(set(plan.missing_targets), {99})
        self.assertTrue(schedule_value_dag(plan.operations, [2, 3], 1000))

    def test_beam_finds_two_node_shared_subgraph(self):
        plan = plan_bounded_beam(
            [2, 3], [12, 35], 1000,
            max_intermediates=2, max_depth=4, beam_width=128,
        )
        self.assertEqual(plan.missing_targets, ())
        self.assertEqual(plan.intermediate_count, 2)
        results = {op.result for op in plan.operations}
        self.assertTrue({5, 7, 12, 35}.issubset(results))
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
