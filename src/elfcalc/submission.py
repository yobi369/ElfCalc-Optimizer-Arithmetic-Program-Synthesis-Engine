"""Kaggle submission CSV parsing and serialization."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Mapping, Sequence

from .machine import MAX_INSTRUCTIONS, MAX_PROGRAM_BYTES, Instruction
from .validation import program_from_rows


def _program_json(program: Sequence[Instruction]) -> str:
    if len(program) > MAX_INSTRUCTIONS:
        raise ValueError(f"program exceeds {MAX_INSTRUCTIONS} instructions")
    payload = json.dumps(rows_from_program(program), separators=(",", ":"), ensure_ascii=False)
    if len(payload.encode("utf-8")) > MAX_PROGRAM_BYTES:
        raise ValueError(f"program exceeds {MAX_PROGRAM_BYTES} UTF-8 bytes")
    return payload


def load_submission(path: str | Path) -> dict[str, tuple[Instruction, ...]]:
    """Load the official two-column id,program submission format."""
    programs: dict[str, tuple[Instruction, ...]] = {}
    with Path(path).open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        required = {"id", "program"}
        missing = required.difference(reader.fieldnames or ())
        if missing:
            raise ValueError(f"submission is missing required columns: {sorted(missing)}")

        for line_number, row in enumerate(reader, start=2):
            puzzle_id = row["id"]
            if not puzzle_id:
                raise ValueError(f"empty puzzle id at CSV line {line_number}")
            if puzzle_id in programs:
                raise ValueError(f"duplicate puzzle id {puzzle_id!r}")
            raw = row["program"]
            if len(raw.encode("utf-8")) > MAX_PROGRAM_BYTES:
                raise ValueError(f"program for {puzzle_id!r} exceeds {MAX_PROGRAM_BYTES} UTF-8 bytes")
            try:
                raw_program = json.loads(raw)
                if not isinstance(raw_program, list):
                    raise ValueError("program must be a JSON array")
                programs[puzzle_id] = program_from_rows(raw_program)
            except (json.JSONDecodeError, TypeError, ValueError) as exc:
                raise ValueError(
                    f"invalid program for {puzzle_id!r} at CSV line {line_number}: {exc}"
                ) from exc
    return programs


def rows_from_program(program: Sequence[Instruction]) -> list[list[object]]:
    """Serialize instructions as [operator, source_i, source_j, destination]."""
    return [
        [instruction.operator, instruction.left, instruction.right, instruction.destination]
        for instruction in program
    ]


def write_submission(
    path: str | Path,
    puzzle_ids: Sequence[str],
    programs: Mapping[str, Sequence[Instruction]],
) -> None:
    """Write programs in the official CSV schema and caller-supplied puzzle order."""
    expected = set(puzzle_ids)
    supplied = set(programs)
    if expected != supplied:
        missing = sorted(expected - supplied)
        extra = sorted(supplied - expected)
        raise ValueError(f"program IDs do not match puzzle IDs; missing={missing}, extra={extra}")
    if len(expected) != len(puzzle_ids):
        raise ValueError("puzzle_ids contains duplicates")

    with Path(path).open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["id", "program"], lineterminator="\n")
        writer.writeheader()
        for puzzle_id in puzzle_ids:
            writer.writerow({"id": puzzle_id, "program": _program_json(programs[puzzle_id])})
