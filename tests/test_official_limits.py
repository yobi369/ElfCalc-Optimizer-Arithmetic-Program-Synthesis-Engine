import csv
import json
import tempfile
import unittest
from pathlib import Path

from elfcalc.machine import Instruction, MAX_INSTRUCTIONS, MAX_PROGRAM_BYTES
from elfcalc.puzzle import Puzzle
from elfcalc.submission import load_submission, write_submission
from elfcalc.validation import validate_program


class OfficialLimitTests(unittest.TestCase):
    def test_rejects_value_limit_above_official_maximum(self):
        with self.assertRaisesRegex(ValueError, "value_limit"):
            Puzzle("too_large", (1,), (1,), 10**18 + 1)

    def test_validator_rejects_more_than_4096_instructions(self):
        puzzle = Puzzle("limit", (1,), (1,), 10)
        program = (Instruction(0, 0, "+", 0),) * (MAX_INSTRUCTIONS + 1)
        result = validate_program(puzzle, program)
        self.assertFalse(result.valid)
        self.assertIn("4096", result.error)

    def test_loader_rejects_program_cell_over_128_kib(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "submission.csv"
            with path.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.writer(handle)
                writer.writerow(["id", "program"])
                writer.writerow(["p1", " " * (MAX_PROGRAM_BYTES + 1) + "[]"])
            with self.assertRaisesRegex(ValueError, "UTF-8 bytes"):
                load_submission(path)

    def test_loader_requires_exact_column_order(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "submission.csv"
            with path.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.writer(handle)
                writer.writerow(["program", "id"])
                writer.writerow(["[]", "p1"])
            with self.assertRaisesRegex(ValueError, "exactly the columns"):
                load_submission(path)


if __name__ == "__main__":
    unittest.main()
