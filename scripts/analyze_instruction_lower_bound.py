#!/usr/bin/env python3
"""Compute a rigorous per-puzzle instruction lower bound from the official puzzle CSV.

Every distinct target value absent from the initial registers must be produced by
at least one arithmetic instruction. One instruction produces exactly one
result, so the sum of these counts is a valid global lower bound.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--puzzles", type=Path, required=True)
    ap.add_argument("--output", type=Path)
    args = ap.parse_args()

    rows = list(csv.DictReader(args.puzzles.open(encoding="utf-8-sig", newline="")))
    total_targets = 0
    already_seeded = 0
    mandatory = 0
    per_puzzle = []
    for row in rows:
        seeds = set(json.loads(row["starting_values"]))
        targets = set(json.loads(row["targets"]))
        seeded = targets & seeds
        missing = targets - seeds
        total_targets += len(targets)
        already_seeded += len(seeded)
        mandatory += len(missing)
        per_puzzle.append({
            "id": row["id"],
            "distinct_targets": len(targets),
            "targets_already_in_start": len(seeded),
            "mandatory_outputs": len(missing),
        })

    report = {
        "puzzles": len(rows),
        "distinct_target_instances": total_targets,
        "targets_already_present_in_start": already_seeded,
        "mandatory_instruction_lower_bound": mandatory,
        "puzzles_sha256": sha256(args.puzzles),
        "proof": (
            "For each puzzle, every distinct target absent from its initial "
            "register values must appear as the result of at least one "
            "instruction. A single instruction writes one result value, so "
            "the sum of these per-puzzle counts is a valid lower bound."
        ),
        "per_puzzle": per_puzzle,
    }
    rendered = json.dumps(report, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k != "per_puzzle"}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
