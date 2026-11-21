import unittest

from elfcalc.audit import audit_programs
from elfcalc.machine import Instruction
from elfcalc.puzzle import Puzzle


class BaselineAuditTests(unittest.TestCase):
    def setUp(self):
        self.puzzles = [
            Puzzle("p1", (2, 3), (5,), 10),
            Puzzle("p2", (4, 2), (2, 6), 10),
        ]

    def test_audits_valid_complete_programs(self):
        programs = {
            "p1": (Instruction(2, 0, "+", 1),),
            "p2": (Instruction(2, 0, "+", 1),),
        }
        report = audit_programs(self.puzzles, programs)
        self.assertEqual(report.puzzle_count, 2)
        self.assertEqual(report.valid_count, 2)
        self.assertEqual(report.complete_count, 2)
        self.assertEqual(report.total_instructions, 2)
        self.assertEqual(report.median_instructions, 1)
        self.assertEqual(report.failures, ())

    def test_reports_incomplete_programs(self):
        report = audit_programs(self.puzzles, {"p1": (), "p2": ()})
        self.assertEqual(report.valid_count, 2)
        self.assertEqual(report.complete_count, 0)
        self.assertEqual([item.puzzle_id for item in report.failures], ["p1", "p2"])

    def test_rejects_mismatched_submission_ids(self):
        with self.assertRaisesRegex(ValueError, "IDs do not match"):
            audit_programs(self.puzzles, {"p1": ()})

    def test_rejects_duplicate_puzzle_ids(self):
        with self.assertRaisesRegex(ValueError, "duplicate"):
            audit_programs([self.puzzles[0], self.puzzles[0]], {"p1": ()})


if __name__ == "__main__":
    unittest.main()
