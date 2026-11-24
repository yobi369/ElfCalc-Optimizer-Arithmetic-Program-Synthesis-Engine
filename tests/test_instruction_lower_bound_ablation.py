"""Ablate admissible instruction lower-bound pruning on synthetic puzzles.

The lower bound grants all target values for free when checking direct
reachability. It may therefore underestimate work, but must never overestimate
the additional instructions required for a complete solution.
"""
from time import perf_counter
from unittest import TestCase
from unittest.mock import patch

import elfcalc.bounded_search as search
from elfcalc.puzzle import Puzzle
from elfcalc.register_schedule import schedule_value_dag
from elfcalc.validation import validate_program


FIXTURES = (
    ("shared_factor_chain", (2, 3, 5), (50, 75), 1000, 2, 4),
    ("shared_bridge", (2, 3), (12, 35), 1000, 3, 5),
    ("multi_family", (2, 3, 5), (10, 12, 15, 18), 1000, 3, 5),
)
STATE_BUDGET = 512
RECIPE_BUDGET = 32


class InstructionLowerBoundAblationTests(TestCase):
    def _run(self, fixture, enabled):
        name, starts, targets, limit, intermediates, depth = fixture
        original = search._cached_pair_recipes
        work = {"frontier_requests": 0, "candidate_recipes": 0}

        def counted(values, value_limit):
            recipes = original(values, value_limit)
            work["frontier_requests"] += 1
            work["candidate_recipes"] += len(recipes)
            return recipes

        started = perf_counter()
        with patch.object(search, "_cached_pair_recipes", counted):
            plan = search.plan_bounded_beam(
                starts, targets, limit,
                max_intermediates=intermediates,
                max_depth=depth,
                beam_width=8,
                max_expansions_per_state=RECIPE_BUDGET,
                max_total_state_expansions=STATE_BUDGET,
                enable_complete_witnesses=False,
                enable_partial_motifs=False,
                enable_target_cone_guidance=False,
                enable_shared_subgraph_guidance=False,
                enable_instruction_lower_bound_pruning=enabled,
            )
        work["elapsed_seconds"] = round(perf_counter() - started, 6)
        program = schedule_value_dag(plan.operations, starts, limit)
        replay = validate_program(
            Puzzle(name + ("_lb" if enabled else "_baseline"),
                   starts, targets, limit),
            program,
        )
        return plan, replay, work

    def test_lower_bound_pruning_preserves_exact_fixture_solutions(self):
        rows = []
        for fixture in FIXTURES:
            baseline, baseline_replay, baseline_work = self._run(fixture, False)
            pruned, pruned_replay, pruned_work = self._run(fixture, True)
            row = {
                "fixture": fixture[0],
                "baseline_complete": baseline_replay.complete,
                "pruned_complete": pruned_replay.complete,
                "baseline_instructions": len(baseline.operations),
                "pruned_instructions": len(pruned.operations),
                "baseline_coverage": len(baseline.covered_targets),
                "pruned_coverage": len(pruned.covered_targets),
                "baseline_recipe_work": baseline_work,
                "pruned_recipe_work": pruned_work,
            }
            rows.append(row)
            self.assertTrue(baseline_replay.complete, row)
            self.assertTrue(pruned_replay.complete, row)
            self.assertLessEqual(len(pruned.operations), len(baseline.operations), row)

        print("INSTRUCTION_LOWER_BOUND_ABLATION")
        for row in rows:
            print(row)
        self.assertEqual(len(rows), len(FIXTURES))

    def test_lower_bound_never_exceeds_known_fixture_solution_cost(self):
        for name, starts, targets, limit, intermediates, depth in FIXTURES:
            state = search._State(
                operations=(),
                available=frozenset(starts),
                missing=frozenset(set(targets).difference(starts)),
                intermediates=0,
            )
            lower_bound = search._remaining_instruction_lower_bound(
                state, frozenset(targets), limit
            )
            # The known bounded fixture solutions use no more than depth
            # instructions. This is a conservative sanity check, not a proof
            # of optimality for the arithmetic puzzle.
            self.assertLessEqual(lower_bound, depth, name)
