#!/usr/bin/env python3
"""Audit a Santa 2026 puzzle CSV against an official-format submission CSV."""

from __future__ import annotations

import argparse
import sys

from elfcalc.audit import audit_submission_files


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--puzzles", default="data/puzzles.csv", help="path to puzzles.csv")
    parser.add_argument(
        "--submission",
        default="data/sample_submission.csv",
        help="path to sample_submission.csv or a candidate submission",
    )
    args = parser.parse_args()

    try:
        report = audit_submission_files(args.puzzles, args.submission)
    except (OSError, ValueError) as exc:
        print(f"AUDIT ERROR: {exc}", file=sys.stderr)
        return 2

    print(f"Puzzles:              {report.puzzle_count}")
    print(f"Valid programs:       {report.valid_count}/{report.puzzle_count}")
    print(f"Complete programs:    {report.complete_count}/{report.puzzle_count}")
    print(f"Total instructions:   {report.total_instructions:,}")
    print(f"Median instructions:  {report.median_instructions:g}")
    print(f"Minimum instructions: {report.minimum_instructions:,}")
    print(f"Maximum instructions: {report.maximum_instructions:,}")

    if report.failures:
        print("\nIncomplete or invalid programs:")
        for item in report.failures:
            result = item.result
            state = "invalid" if not result.valid else "incomplete"
            print(
                f"- {item.puzzle_id}: {state}; "
                f"instructions={result.instruction_count}; "
                f"missing_targets={list(result.missing_targets)}; "
                f"error={result.error or '-'}"
            )
        return 1

    print("\nAUDIT PASSED: every supplied program is valid and covers every target.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
