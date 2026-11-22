#!/usr/bin/env python3
"""Merge two complete Santa 2026 submissions by per-puzzle minimum length.

Both parents and the serialized result are replayed through elfcalc's exact
validator. The first parent wins ties so the output is deterministic.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

from elfcalc.puzzle import load_puzzles
from elfcalc.validation import program_from_rows, validate_program


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_submission(path: Path, expected_ids: set[str]) -> dict[str, list]:
    programs = {}
    with path.open("r", encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream)
        if reader.fieldnames != ["id", "program"]:
            raise ValueError(f"{path}: expected exact id,program header")
        for row in reader:
            puzzle_id = row["id"]
            if not puzzle_id or puzzle_id in programs:
                raise ValueError(f"{path}: empty or duplicate puzzle ID")
            programs[puzzle_id] = json.loads(row["program"])
    if set(programs) != expected_ids:
        raise ValueError(
            f"{path}: ID mismatch; missing={len(expected_ids-set(programs))}, "
            f"extra={len(set(programs)-expected_ids)}"
        )
    return programs


def audit(program_rows: list, puzzle, label: str) -> None:
    result = validate_program(puzzle, program_from_rows(program_rows))
    if not result.valid or not result.complete:
        raise ValueError(
            f"{label} failed for {puzzle.puzzle_id}: "
            f"{result.error}; missing={list(result.missing_targets)[:5]}"
        )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--puzzles", type=Path, required=True)
    parser.add_argument("--first", type=Path, required=True)
    parser.add_argument("--second", type=Path, required=True)
    parser.add_argument("--first-name", default="first")
    parser.add_argument("--second-name", default="second")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--origins", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()

    puzzles = load_puzzles(args.puzzles)
    puzzle_ids = {p.puzzle_id for p in puzzles}
    if len(puzzle_ids) != len(puzzles):
        raise ValueError("Puzzle file contains duplicate IDs")

    first = load_submission(args.first, puzzle_ids)
    second = load_submission(args.second, puzzle_ids)
    selected = {}
    origins = {}
    first_counts = {}
    second_counts = {}

    for puzzle in puzzles:
        pid = puzzle.puzzle_id
        audit(first[pid], puzzle, args.first_name)
        audit(second[pid], puzzle, args.second_name)
        first_counts[pid] = len(first[pid])
        second_counts[pid] = len(second[pid])
        if len(first[pid]) <= len(second[pid]):
            selected[pid] = first[pid]
            origins[pid] = args.first_name
        else:
            selected[pid] = second[pid]
            origins[pid] = args.second_name

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.origins.parent.mkdir(parents=True, exist_ok=True)
    args.report.parent.mkdir(parents=True, exist_ok=True)

    with args.output.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream, lineterminator="\n")
        writer.writerow(("id", "program"))
        for puzzle in puzzles:
            pid = puzzle.puzzle_id
            writer.writerow((pid, json.dumps(selected[pid], separators=(",", ":"))))

    with args.origins.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream, lineterminator="\n")
        writer.writerow(("id", "selected_source", "selected_instructions",
                         "first_instructions", "second_instructions"))
        for puzzle in puzzles:
            pid = puzzle.puzzle_id
            writer.writerow((pid, origins[pid], len(selected[pid]),
                             first_counts[pid], second_counts[pid]))

    # Replay the exact bytes that will be submitted, not only in-memory rows.
    serialized = load_submission(args.output, puzzle_ids)
    for puzzle in puzzles:
        audit(serialized[puzzle.puzzle_id], puzzle, "serialized output")

    counts = [len(serialized[p.puzzle_id]) for p in puzzles]
    report = {
        "puzzles": len(puzzles),
        "valid_and_complete": len(puzzles),
        "invalid_or_incomplete": 0,
        "first_total": sum(first_counts.values()),
        "second_total": sum(second_counts.values()),
        "merged_total": sum(counts),
        "savings_vs_first": sum(first_counts.values()) - sum(counts),
        "savings_vs_second": sum(second_counts.values()) - sum(counts),
        "selected_rows_by_source": dict(Counter(origins.values())),
        "puzzles_sha256": sha256(args.puzzles),
        "first_sha256": sha256(args.first),
        "second_sha256": sha256(args.second),
        "merged_sha256": sha256(args.output),
        "origins_sha256": sha256(args.origins),
        "tie_policy": "first parent wins ties",
    }
    args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    print("AUDIT PASSED: both parents and serialized output are valid and complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
