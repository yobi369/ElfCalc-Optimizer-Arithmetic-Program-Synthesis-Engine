import unittest

from elfcalc.puzzle import Puzzle
from elfcalc.shared_solver import solve_shared_intermediate
from elfcalc.validation import validate_program


class SharedIntermediateSolverTests(unittest.TestCase):
    def test_solves_and_validates_reusable_intermediate_puzzle(self):
        puzzle = Puzzle("shared_solver_toy", (2, 3), (8, 12), 20)
        program = solve_shared_intermediate(puzzle)
        result = validate_program(puzzle, program)
        self.assertTrue(result.complete, result.error)
        self.assertEqual(len(program), 3)

    def test_returns_empty_program_when_targets_are_initial(self):
        puzzle = Puzzle("shared_solver_initial", (2, 3), (2, 3), 10)
        self.assertEqual(solve_shared_intermediate(puzzle), ())

    def test_rejects_uncovered_target_set(self):
        puzzle = Puzzle("shared_solver_incomplete", (7, 9), (17, 19), 20)
        with self.assertRaisesRegex(ValueError, "missed"):
            solve_shared_intermediate(puzzle)


if __name__ == "__main__":
    unittest.main()
