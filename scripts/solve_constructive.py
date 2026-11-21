#!/usr/bin/env python3
"""Generate a constructive candidate and optionally retain shorter fallback programs."""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import statistics
import time
from pathlib import Path

from elfcalc.audit import audit_programs
from elfcalc.construct import solve_constructive
from elfcalc.puzzle import load_puzzles
from elfcalc.submission import load_submission, write_submission
from elfcalc.validation import validate_program


def _sha256(path: Path | None) -> str | None:
    if path is None or not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--puzzles", default="data/puzzles.csv")
    parser.add_argument("--fallback", default="data/sample_submission.csv")
    parser.add_argument("--output", default="outputs/constructive.csv")
    parser.add_argument("--report", default="outputs/constructive-report.json")
    args = parser.parse_args()

    started = time.perf_counter()
    puzzle_path = Path(args.puzzles)
    fallback_path = Path(args.fallback) if args.fallback else None
    output_path = Path(args.output)
    report_path = Path(args.report) if args.report else None

    puzzles = load_puzzles(puzzle_path)
    fallback = (
        load_submission(fallback_path)
        if fallback_path is not None and fallback_path.exists()
        else {}
    )
    puzzle_ids = [puzzle.puzzle_id for puzzle in puzzles]
    if fallback and set(fallback) != set(puzzle_ids):
        raise ValueError("fallback submission IDs do not match the selected puzzle dataset")

    programs = {}
    per_puzzle = []
    improved = fallback_used = failed = 0

    for index, puzzle in enumerate(puzzles, start=1):
        baseline = fallback.get(puzzle.puzzle_id)
        if baseline is not None:
            baseline_check = validate_program(puzzle, baseline)
            if not baseline_check.complete:
                raise ValueError(
                    f"fallback program for {puzzle.puzzle_id} is invalid: "
                    f"{baseline_check.error or baseline_check.missing_targets}"
                )

        source = "constructive"
        try:
            candidate = solve_constructive(puzzle)
            check = validate_program(puzzle, candidate)
            if not check.complete:
                raise ValueError(check.error or "candidate is incomplete")
            if baseline is None or len(candidate) < len(baseline):
                selected = candidate
                improved += int(baseline is not None and len(candidate) < len(baseline))
            else:
                selected = baseline
                source = "fallback"
                fallback_used += 1
        except (ValueError, RecursionError):
            failed += 1
            if baseline is None:
                raise
            selected = baseline
            source = "fallback"
            fallback_used += 1

        programs[puzzle.puzzle_id] = selected
        per_puzzle.append({
            "id": puzzle.puzzle_id,
            "instructions": len(selected),
            "source": source,
        })

        if index % 25 == 0 or index == len(puzzles):
            print(f"Processed {index}/{len(puzzles)} puzzles")

    write_submission(output_path, puzzle_ids, programs)
    audit = audit_programs(puzzles, programs)
    if audit.complete_count != len(puzzles):
        raise ValueError(f"generated submission failed replay: {len(audit.failures)} failure(s)")

    elapsed = time.perf_counter() - started
    print(f"Output: {output_path}")
    print(f"Total instructions: {audit.total_instructions:,}")
    print(f"Median instructions: {audit.median_instructions:g}")
    print(f"Maximum instructions: {audit.maximum_instructions:,}")
    print(f"Programs improved over fallback: {improved}")
    print(f"Fallback programs used: {fallback_used}")
    print(f"Constructor failures: {failed}")

    if report_path is not None:
        report_path.parent.mkdir(parents=True, exist_ok=True)
        counts = [item["instructions"] for item in per_puzzle]
        report = {
            "solver": "elfcalc-constructive-v2",
            "method": "all feasible positional bases 2..32; signed-window widths 3..8; streaming signed-window widths 9..14",
            "python_version": platform.python_version(),
            "runtime_seconds": round(elapsed, 3),
            "puzzles": len(puzzles),
            "valid_programs": audit.valid_count,
            "complete_programs": audit.complete_count,
            "total_instructions": audit.total_instructions,
            "median_instructions": statistics.median(counts) if counts else 0,
            "minimum_instructions": min(counts) if counts else 0,
            "maximum_instructions": max(counts) if counts else 0,
            "improved_over_fallback": improved,
            "fallback_programs_used": fallback_used,
            "constructor_failures": failed,
            "puzzles_sha256": _sha256(puzzle_path),
            "fallback_sha256": _sha256(fallback_path),
            "submission_sha256": _sha256(output_path),
            "per_puzzle": per_puzzle,
        }
        report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(f"Report: {report_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
