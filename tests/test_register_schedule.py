import unittest

from elfcalc.register_schedule import schedule_value_dag
from elfcalc.shared_intermediate import plan_shared_intermediates
from elfcalc.validation import validate_program
from elfcalc.puzzle import Puzzle


class RegisterScheduleTests(unittest.TestCase):
    def test_lowers_shared_intermediate_plan_and_replays(self):
        starts = (2, 3)
        plan = plan_shared_intermediates(starts, (8, 12), 20)
        program = schedule_value_dag(plan.operations, starts, 20)
        puzzle = Puzzle("scheduled_shared_dag", starts, (8, 12), 20)
        result = validate_program(puzzle, program)
        self.assertTrue(result.complete, result.error)
        self.assertEqual(len(program), plan.instruction_count)

    def test_reuses_register_only_after_last_use(self):
        starts = tuple(range(1, 49))
        plan = plan_shared_intermediates(starts, (49, 51), 100)
        program = schedule_value_dag(plan.operations, starts, 100)
        puzzle = Puzzle("full_register_bank", starts, (49, 51), 100)
        result = validate_program(puzzle, program)
        self.assertTrue(result.complete, result.error)
        self.assertEqual(len(program), 2)
        self.assertEqual(program[0].destination, 0)

    def test_rejects_dag_with_incorrect_declared_result(self):
        class Operation:
            left = 2
            operator = "+"
            right = 3
            result = 6

        with self.assertRaisesRegex(ValueError, "result mismatch"):
            schedule_value_dag((Operation(),), (2, 3), 10)

    def test_rejects_inexact_dag_division(self):
        class Operation:
            left = 7
            operator = "/"
            right = 2
            result = 3

        with self.assertRaisesRegex(ValueError, "division must be exact"):
            schedule_value_dag((Operation(),), (7, 2), 10)

    def test_rejects_dag_with_missing_operand(self):
        class Operation:
            left = 100
            operator = "+"
            right = 2
            result = 102

        with self.assertRaisesRegex(ValueError, "missing operand"):
            schedule_value_dag((Operation(),), (2, 3), 200)


if __name__ == "__main__":
    unittest.main()
