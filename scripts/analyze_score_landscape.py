#!/usr/bin/env python3
"""Replay-audit a candidate and summarize the Santa 2026 score landscape."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import statistics
from pathlib import Path

from elfcalc.puzzle import load_puzzles
from elfcalc.validation import program_from_rows, validate_program


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--puzzles", type=Path, required=True)
    parser.add_argument("--submission", type=Path, required=True)
    parser.add_argument("--leaderboard-score", type=int, default=None)
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()

    puzzles = load_puzzles(args.puzzles)
    programs = {}
    with args.submission.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != ["id", "program"]:
            raise ValueError("submission must have exactly id,program columns")
        for row in reader:
            if row["id"] in programs:
                raise ValueError(f"duplicate submission ID: {row['id']}")
            programs[row["id"]] = program_from_rows(json.loads(row["program"]))

    expected = {p.puzzle_id for p in puzzles}
    if set(programs) != expected:
        raise ValueError(
            f"submission IDs mismatch: missing={len(expected-set(programs))}, "
            f"extra={len(set(programs)-expected)}"
        )

    rows = []
    valid_count = complete_count = 0
    failures = []
    for puzzle in puzzles:
        program = programs[puzzle.puzzle_id]
        result = validate_program(puzzle, program)
        valid_count += int(result.valid)
        complete_count += int(result.complete)
        if not result.complete:
            failures.append({
                "id": puzzle.puzzle_id,
                "error": result.error,
                "missing_targets": list(result.missing_targets),
            })
        non_seed_targets = len(puzzle.missing_targets)
        rows.append({
            "id": puzzle.puzzle_id,
            "instructions": len(program),
            "targets": len(puzzle.targets),
            "non_seed_targets": non_seed_targets,
            "starting_values": len(puzzle.starting_values),
            "instructions_per_non_seed_target": (
                len(program) / non_seed_targets if non_seed_targets else 0.0
            ),
        })

    counts = [row["instructions"] for row in rows]
    mandatory_floor = sum(row["non_seed_targets"] for row in rows)
    ordered = sorted(rows, key=lambda row: (-row["instructions"], row["id"]))
    report = {
        "puzzle_count": len(puzzles),
        "valid_count": valid_count,
        "complete_count": complete_count,
        "failure_count": len(failures),
        "failures": failures,
        "total_instructions": sum(counts),
        "median_instructions": statistics.median(counts),
        "mean_instructions": statistics.mean(counts),
        "p90_instructions": sorted(counts)[math.ceil(0.90 * len(counts)) - 1],
        "minimum_instructions": min(counts),
        "maximum_instructions": max(counts),
        "total_targets": sum(row["targets"] for row in rows),
        "non_seed_targets": mandatory_floor,
        "unconditional_instruction_lower_bound": mandatory_floor,
        "candidate_sha256": sha256(args.submission),
        "puzzles_sha256": sha256(args.puzzles),
        "leaderboard_score_snapshot": args.leaderboard_score,
        "gap_to_leaderboard_snapshot": (
            sum(counts) - args.leaderboard_score
            if args.leaderboard_score is not None else None
        ),
        "top_25_hardest": ordered[:25],
    }

    print(json.dumps(report, indent=2))
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    if failures:
        print(f"\nAUDIT FAILED: {len(failures)} programs are incomplete or invalid.")
        return 1
    print("\nAUDIT PASSED: all programs replay and cover every target.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
