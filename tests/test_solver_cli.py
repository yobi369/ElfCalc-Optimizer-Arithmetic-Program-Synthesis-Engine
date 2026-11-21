import csv
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from elfcalc.machine import Instruction
from elfcalc.submission import load_submission, write_submission
from elfcalc.puzzle import load_puzzles
from elfcalc.audit import audit_programs


class ConstructiveCliTests(unittest.TestCase):
    def test_generates_valid_submission_and_report(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            puzzles_path = root / "puzzles.csv"
            with puzzles_path.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(
                    handle,
                    fieldnames=["id", "starting_values", "targets", "value_limit", "registers"],
                )
                writer.writeheader()
                writer.writerow({
                    "id": "toy",
                    "starting_values": "[3]",
                    "targets": "[1,2,5,8,9]",
                    "value_limit": 9,
                    "registers": 48,
                })

            fallback_path = root / "fallback.csv"
            fallback = (
                Instruction(1, 0, "+", 0),
                Instruction(2, 0, "/", 0),
                Instruction(3, 0, "-", 2),
                Instruction(4, 0, "+", 3),
                Instruction(5, 0, "+", 4),
                Instruction(6, 0, "*", 0),
            )
            write_submission(fallback_path, ["toy"], {"toy": fallback})

            output_path = root / "nested" / "candidate.csv"
            report_path = root / "nested" / "report.json"
            script = Path(__file__).resolve().parents[1] / "scripts" / "solve_constructive.py"
            completed = subprocess.run(
                [
                    sys.executable, str(script),
                    "--puzzles", str(puzzles_path),
                    "--fallback", str(fallback_path),
                    "--output", str(output_path),
                    "--report", str(report_path),
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
            self.assertTrue(output_path.exists())
            self.assertTrue(report_path.exists())

            puzzles = load_puzzles(puzzles_path)
            programs = load_submission(output_path)
            audit = audit_programs(puzzles, programs)
            self.assertEqual(audit.complete_count, 1)
            self.assertLess(len(programs["toy"]), len(fallback))

            report = json.loads(report_path.read_text(encoding="utf-8"))
            self.assertEqual(report["puzzles"], 1)
            self.assertEqual(report["complete_programs"], 1)
            self.assertEqual(report["improved_over_fallback"], 1)


if __name__ == "__main__":
    unittest.main()
