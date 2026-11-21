#!/usr/bin/env python3
"""Compare the constructive portfolio with and without shared-intermediate DAG search."""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import statistics
import time
from pathlib import Path

from elfcalc.construct import solve_constructive
from elfcalc.puzzle import load_puzzles
from elfcalc.validation import validate_program


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--puzzles", default="data/practice_puzzles.csv")
    parser.add_argument("--output", default="outputs/shared-dag-benchmark.json")
    args = parser.parse_args()

    puzzle_path = Path(args.puzzles)
    output_path = Path(args.output)
    puzzles = load_puzzles(puzzle_path)
    rows = []
    with_dag_total = without_dag_total = 0
    improved = tied = regressed = failures = 0
    started = time.perf_counter()

    for index, puzzle in enumerate(puzzles, start=1):
        try:
            baseline = solve_constructive(puzzle, include_shared_dag=False)
            candidate = solve_constructive(puzzle, include_shared_dag=True)
            baseline_check = validate_program(puzzle, baseline)
            candidate_check = validate_program(puzzle, candidate)
            if not baseline_check.complete or not candidate_check.complete:
                raise ValueError("one or both portfolio candidates failed exact replay")
            before, after = len(baseline), len(candidate)
            without_dag_total += before
            with_dag_total += after
            improved += int(after < before)
            tied += int(after == before)
            regressed += int(after > before)
            rows.append({"id": puzzle.puzzle_id, "without_dag": before, "with_dag": after})
        except (ValueError, RecursionError) as exc:
            failures += 1
            rows.append({"id": puzzle.puzzle_id, "error": str(exc)})
        if index % 25 == 0 or index == len(puzzles):
            print(f"Benchmarked {index}/{len(puzzles)} puzzles")

    comparable = len(rows) - failures
    report = {
        "experiment": "shared-intermediate-dag-ablation",
        "python_version": platform.python_version(),
        "dataset": str(puzzle_path),
        "dataset_sha256": sha256(puzzle_path),
        "puzzles": len(puzzles),
        "comparable_puzzles": comparable,
        "failures": failures,
        "without_dag_total_instructions": without_dag_total,
        "with_dag_total_instructions": with_dag_total,
        "instruction_delta": with_dag_total - without_dag_total,
        "improved_puzzles": improved,
        "tied_puzzles": tied,
        "regressed_puzzles": regressed,
        "median_without_dag": statistics.median(
            row["without_dag"] for row in rows if "without_dag" in row
        ) if comparable else None,
        "median_with_dag": statistics.median(
            row["with_dag"] for row in rows if "with_dag" in row
        ) if comparable else None,
        "runtime_seconds": round(time.perf_counter() - started, 3),
        "per_puzzle": rows,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: value for key, value in report.items() if key != "per_puzzle"}, indent=2))
    print(f"Report: {output_path}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
