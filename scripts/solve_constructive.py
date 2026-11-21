#!/usr/bin/env python3
"""Generate a constructive candidate and optionally retain shorter fallback programs."""

from __future__ import annotations

import argparse
from pathlib import Path

from elfcalc.construct import solve_constructive
from elfcalc.puzzle import load_puzzles
from elfcalc.submission import load_submission, write_submission
from elfcalc.validation import validate_program


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--puzzles", default="data/puzzles.csv")
    parser.add_argument("--fallback", default="data/sample_submission.csv")
    parser.add_argument("--output", default="outputs/constructive.csv")
    args = parser.parse_args()

    puzzles = load_puzzles(args.puzzles)
    fallback_path = Path(args.fallback) if args.fallback else None
    fallback = load_submission(fallback_path) if fallback_path and fallback_path.exists() else {}
    puzzle_ids = [puzzle.puzzle_id for puzzle in puzzles]
    if fallback and set(fallback) != set(puzzle_ids):
        raise ValueError("fallback submission IDs do not match the selected puzzle dataset")
    programs = {}
    improved = 0
    failed = 0

    for index, puzzle in enumerate(puzzles, start=1):
        baseline = fallback.get(puzzle.puzzle_id)
        try:
            candidate = solve_constructive(puzzle)
            check = validate_program(puzzle, candidate)
            if not check.complete:
                raise ValueError(check.error or "candidate is incomplete")
            if baseline is None or len(candidate) < len(baseline):
                programs[puzzle.puzzle_id] = candidate
                improved += int(baseline is not None and len(candidate) < len(baseline))
            else:
                programs[puzzle.puzzle_id] = baseline
        except (ValueError, RecursionError):
            failed += 1
            if baseline is None:
                raise
            programs[puzzle.puzzle_id] = baseline

        if index % 25 == 0 or index == len(puzzles):
            print(f"Processed {index}/{len(puzzles)} puzzles")

    write_submission(args.output, [puzzle.puzzle_id for puzzle in puzzles], programs)
    total = sum(len(program) for program in programs.values())
    print(f"Output: {args.output}")
    print(f"Total instructions: {total:,}")
    print(f"Programs improved over fallback: {improved}")
    print(f"Constructor failures/fallbacks: {failed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
