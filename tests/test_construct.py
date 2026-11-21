import unittest

from elfcalc.construct import solve_constructive
from elfcalc.puzzle import Puzzle
from elfcalc.validation import validate_program


class ConstructiveSolverTests(unittest.TestCase):
    def test_solves_small_shared_target_puzzle(self):
        puzzle = Puzzle("toy", (3,), (1, 2, 5, 8), 9)
        program = solve_constructive(puzzle)
        result = validate_program(puzzle, program)
        self.assertTrue(result.complete, result.error)
        self.assertEqual(len(program), 4)

    def test_returns_empty_program_when_all_targets_are_initial(self):
        puzzle = Puzzle("already_done", (2, 3), (2, 3), 10)
        self.assertEqual(solve_constructive(puzzle), ())

    def test_never_exceeds_value_limit(self):
        puzzle = Puzzle("bounded", (3,), (1, 2, 5, 8, 9), 9)
        program = solve_constructive(puzzle)
        self.assertTrue(validate_program(puzzle, program).complete)


if __name__ == "__main__":
    unittest.main()
