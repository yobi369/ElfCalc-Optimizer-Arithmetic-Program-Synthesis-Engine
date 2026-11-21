import csv
import json
import tempfile
import unittest
from pathlib import Path

from elfcalc.machine import Instruction
from elfcalc.submission import load_submission, write_submission


class SubmissionIOTests(unittest.TestCase):
    def test_round_trip_official_format(self):
        program = (Instruction(2, 0, "+", 1), Instruction(3, 2, "*", 2))
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "submission.csv"
            write_submission(path, ["puzzle_b", "puzzle_a"], {
                "puzzle_a": (),
                "puzzle_b": program,
            })
            loaded = load_submission(path)

        self.assertEqual(list(loaded), ["puzzle_b", "puzzle_a"])
        self.assertEqual(loaded["puzzle_b"], program)
        self.assertEqual(loaded["puzzle_a"], ())

    def test_creates_missing_output_directories(self):
        program = (Instruction(2, 0, "+", 1),)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "nested" / "output" / "submission.csv"
            write_submission(path, ["p1"], {"p1": program})
            self.assertTrue(path.exists())
            self.assertEqual(load_submission(path)["p1"], program)

    def test_rejects_duplicate_ids(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "submission.csv"
            with path.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(handle, fieldnames=["id", "program"])
                writer.writeheader()
                writer.writerow({"id": "p1", "program": "[]"})
                writer.writerow({"id": "p1", "program": "[]"})
            with self.assertRaisesRegex(ValueError, "duplicate"):
                load_submission(path)

    def test_rejects_program_id_mismatch(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "submission.csv"
            with self.assertRaisesRegex(ValueError, "do not match"):
                write_submission(path, ["p1"], {})

    def test_rejects_malformed_program_json(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "submission.csv"
            with path.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(handle, fieldnames=["id", "program"])
                writer.writeheader()
                writer.writerow({"id": "p1", "program": "not-json"})
            with self.assertRaisesRegex(ValueError, "invalid program"):
                load_submission(path)


if __name__ == "__main__":
    unittest.main()
