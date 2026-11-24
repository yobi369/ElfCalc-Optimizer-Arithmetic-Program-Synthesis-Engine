"""Adversarial multi-step beam branch-survival test.

This is a synthetic search-control experiment, not a scored-archive test.
It grows legal states from actual arithmetic recipe frontiers, applies both
beam admission policies at equal width, and validates the surviving solution
through register scheduling and exact VM replay.
"""
from unittest import TestCase
from unittest.mock import patch

import elfcalc.bounded_search as search
from elfcalc.puzzle import Puzzle
from elfcalc.register_schedule import schedule_value_dag
from elfcalc.shared_intermediate import PlannedOperation
from elfcalc.validation import validate_program


class AdversarialBeamBranchSurvivalTests(TestCase):

    def test_diversity_preserves_a_real_two_step_branch_under_rank_pressure(self):
        starts = (2, 3, 4, 5)
        target = 72
        limit = 100

        def recipe(values, result, operator, left, right):
            return next(
                item for item in search._cached_pair_recipes(tuple(sorted(values)), limit)
                if (item.result, item.operator, item.left, item.right)
                == (result, operator, left, right)
            )

        # Both roots and all second-layer nodes are produced by the real exact
        # arithmetic frontier, not hand-authored arithmetic assertions.
        root_a_recipe = recipe(starts, 6, "+", 2, 4)
        root_b_recipe = recipe(starts, 8, "+", 3, 5)
        root_a = PlannedOperation(2, "+", 4, 6, False)
        root_b = PlannedOperation(3, "+", 5, 8, False)

        root_a_values = frozenset((*starts, 6))
        root_b_values = frozenset((*starts, 8))
        second_8 = recipe(root_a_values, 8, "+", 3, 5)
        second_9_a = recipe(root_a_values, 9, "*", 3, 3)
        second_9_b = recipe(root_b_values, 9, "*", 3, 3)

        def child(root, first, second):
            return search._State(
                operations=(root, PlannedOperation(
                    second.left, second.operator, second.right,
                    second.result, False,
                )),
                available=frozenset((*starts, first.result, second.result)),
                missing=frozenset((target,)),
                intermediates=2,
            )

        sibling_a = child(root_a, root_a_recipe, second_8)
        sibling_a_2 = child(root_a, root_a_recipe, second_9_a)
        alternative_b = child(root_b, root_b_recipe, second_9_b)

        # Confirm the branch distinction using real one-step frontiers:
        # A+8 and A+9 each lack one operand; B+9 exposes 8*9=72.
        self.assertEqual(search._direct_yield(sibling_a, limit), 0)
        self.assertEqual(search._direct_yield(sibling_a_2, limit), 0)
        self.assertEqual(search._direct_yield(alternative_b, limit), 1)

        ranked = (sibling_a, sibling_a_2, alternative_b)

        # Controlled adversarial pressure: the search heuristic overvalues
        # descendants of root A. Both admission policies receive the same
        # candidates and beam width; only the reservation rule differs.
        def adversarial_rank(state, *_args):
            if state is sibling_a:
                return (0,)
            if state is sibling_a_2:
                return (1,)
            return (2,)

        with patch.object(search, "_rank", side_effect=adversarial_rank):
            ordinary = tuple(sorted(ranked, key=lambda state: search._rank(state, starts, limit))[:2])
            diverse = search._select_diverse_beam(ranked, 2, starts, limit)

        self.assertEqual(ordinary, (sibling_a, sibling_a_2))
        self.assertEqual(diverse, (sibling_a, alternative_b))

        # Continue the selected alternative through a real recipe, scheduler,
        # and exact VM validator. The ordinary beam has no surviving state
        # that can emit 72 in one legal next operation.
        completion_recipe = recipe(alternative_b.available, 72, "*", 8, 9)
        completion = PlannedOperation(
            completion_recipe.left, completion_recipe.operator,
            completion_recipe.right, completion_recipe.result, True,
        )
        operations = alternative_b.operations + (completion,)
        allocation = schedule_value_dag(operations, starts, limit)
        replay = validate_program(
            Puzzle("adversarial_branch_survival", starts, (target,), limit),
            allocation,
        )
        self.assertTrue(replay.complete, replay.error)
        self.assertEqual(len(allocation), 3)
        self.assertEqual(
            {(op.left, op.operator, op.right, op.result) for op in operations},
            {(3, "+", 5, 8), (3, "*", 3, 9), (8, "*", 9, 72)},
        )
