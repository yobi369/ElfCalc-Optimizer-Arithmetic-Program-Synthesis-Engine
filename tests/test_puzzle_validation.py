import csv
import json
import tempfile
import unittest
from pathlib import Path

from elfcalc.puzzle import Puzzle, load_puzzles
from elfcalc.validation import program_from_rows, validate_program


class PuzzleParsingTests(unittest.TestCase):
    def test_load_documented_csv_schema(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "puzzles.csv"
            with path.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(
                    handle,
                    fieldnames=["id", "starting_values", "targets", "value_limit", "registers"],
                )
                writer.writeheader()
                writer.writerow({
                    "id": "example_0001",
                    "starting_values": json.dumps([3]),
                    "targets": json.dumps([1, 2, 5, 8]),
                    "value_limit": 9,
                    "registers": 48,
                })
            puzzles = load_puzzles(path)
        self.assertEqual(len(puzzles), 1)
        self.assertEqual(puzzles[0].instruction_lower_bound, 4)

    def test_rejects_unsorted_targets(self):
        with self.assertRaisesRegex(ValueError, "increasing"):
            Puzzle("bad", (3,), (2, 1), 9)

    def test_rejects_non_48_register_puzzle(self):
        with self.assertRaisesRegex(ValueError, "48"):
            Puzzle("bad", (3,), (1,), 9, registers=8)


class ProgramValidationTests(unittest.TestCase):
    def setUp(self):
        self.puzzle = Puzzle("example_0001", (3,), (1, 2, 5, 8), 9)

    def test_worked_example_is_valid_and_complete(self):
        rows = [
            ["/", 0, 0, 1],
            ["-", 0, 1, 2],
            ["+", 0, 2, 3],
            ["+", 0, 3, 4],
        ]
        result = validate_program(self.puzzle, program_from_rows(rows))
        self.assertTrue(result.complete)
        self.assertEqual(result.instruction_count, 4)
        self.assertEqual(result.missing_targets, ())

    def test_rejects_non_exact_division(self):
        rows = [["/", 0, 1, 2]]
        puzzle = Puzzle("division", (7, 2), (3,), 7)
        result = validate_program(puzzle, program_from_rows(rows))
        self.assertFalse(result.valid)
        self.assertIn("exact", result.error)

    def test_rejects_intermediate_value_over_limit(self):
        rows = [["*", 0, 1, 2], ["/", 2, 1, 3]]
        puzzle = Puzzle("limit", (8, 8), (8,), 10)
        result = validate_program(puzzle, program_from_rows(rows))
        self.assertFalse(result.valid)
        self.assertIn("value_limit", result.error)

    def test_targets_remain_covered_after_overwrite(self):
        puzzle = Puzzle("overwrite", (2, 3), (5,), 10)
        rows = [["+", 0, 1, 2], ["*", 0, 1, 2]]
        result = validate_program(puzzle, program_from_rows(rows))
        self.assertTrue(result.complete)

    def test_incomplete_program_is_valid_but_not_complete(self):
        result = validate_program(self.puzzle, ())
        self.assertTrue(result.valid)
        self.assertFalse(result.complete)
        self.assertEqual(result.missing_targets, (1, 2, 5, 8))


if __name__ == "__main__":
    unittest.main()
