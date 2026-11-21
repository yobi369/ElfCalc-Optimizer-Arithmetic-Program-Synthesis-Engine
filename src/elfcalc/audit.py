"""Reproducible validation and instruction-count audit for a submission."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from statistics import median
from typing import Sequence

from .puzzle import Puzzle, load_puzzles
from .submission import load_submission
from .validation import ValidationResult, validate_program


@dataclass(frozen=True, slots=True)
class PuzzleAudit:
    puzzle_id: str
    result: ValidationResult


@dataclass(frozen=True, slots=True)
class BaselineAudit:
    puzzle_count: int
    valid_count: int
    complete_count: int
    total_instructions: int
    median_instructions: float
    minimum_instructions: int
    maximum_instructions: int
    failures: tuple[PuzzleAudit, ...]


def audit_programs(
    puzzles: Sequence[Puzzle],
    programs: dict,
) -> BaselineAudit:
    """Validate every puzzle program and aggregate its instruction counts."""
    puzzle_ids = [puzzle.puzzle_id for puzzle in puzzles]
    if len(set(puzzle_ids)) != len(puzzle_ids):
        raise ValueError("puzzle dataset contains duplicate IDs")
    expected, supplied = set(puzzle_ids), set(programs)
    if expected != supplied:
        raise ValueError(
            "submission IDs do not match puzzle IDs; "
            f"missing={sorted(expected - supplied)}, extra={sorted(supplied - expected)}"
        )

    results: list[PuzzleAudit] = []
    counts: list[int] = []
    valid_count = complete_count = 0
    for puzzle in puzzles:
        result = validate_program(puzzle, programs[puzzle.puzzle_id])
        results.append(PuzzleAudit(puzzle.puzzle_id, result))
        counts.append(result.instruction_count)
        valid_count += int(result.valid)
        complete_count += int(result.complete)

    failures = tuple(item for item in results if not item.result.complete)
    return BaselineAudit(
        puzzle_count=len(puzzles),
        valid_count=valid_count,
        complete_count=complete_count,
        total_instructions=sum(counts),
        median_instructions=median(counts) if counts else 0,
        minimum_instructions=min(counts) if counts else 0,
        maximum_instructions=max(counts) if counts else 0,
        failures=failures,
    )


def audit_submission_files(
    puzzle_path: str | Path,
    submission_path: str | Path,
) -> BaselineAudit:
    """Load official CSV files and return a complete replay audit."""
    puzzles = load_puzzles(puzzle_path)
    programs = load_submission(submission_path)
    return audit_programs(puzzles, programs)
