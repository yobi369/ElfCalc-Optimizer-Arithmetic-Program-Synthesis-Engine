"""Puzzle model and CSV parsing for the Santa 2026 competition."""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path

from .machine import MAX_VALUE, REGISTER_COUNT


@dataclass(frozen=True, slots=True)
class Puzzle:
    puzzle_id: str
    starting_values: tuple[int, ...]
    targets: tuple[int, ...]
    value_limit: int
    registers: int = REGISTER_COUNT

    def __post_init__(self) -> None:
        if not self.puzzle_id:
            raise ValueError("puzzle_id cannot be empty")
        if not self.starting_values:
            raise ValueError("starting_values cannot be empty")
        if len(self.starting_values) > self.registers:
            raise ValueError("starting_values exceed the available registers")
        if any(type(value) is not int or value <= 0 for value in self.starting_values):
            raise ValueError("starting_values must contain positive integers")
        if any(type(value) is not int or value <= 0 for value in self.targets):
            raise ValueError("targets must contain positive integers")
        if tuple(sorted(self.targets)) != self.targets:
            raise ValueError("targets must be in increasing order")
        if len(set(self.targets)) != len(self.targets):
            raise ValueError("targets must not contain duplicates")
        if type(self.value_limit) is not int or not 1 <= self.value_limit <= MAX_VALUE:
            raise ValueError(f"value_limit must be in [1, {MAX_VALUE}]")
        if self.registers != REGISTER_COUNT:
            raise ValueError(f"competition puzzles must have {REGISTER_COUNT} registers")
        if any(value > self.value_limit for value in self.starting_values):
            raise ValueError("starting value exceeds value_limit")
        if any(value > self.value_limit for value in self.targets):
            raise ValueError("target exceeds value_limit")

    @property
    def initially_covered(self) -> frozenset[int]:
        return frozenset(set(self.starting_values).intersection(self.targets))

    @property
    def missing_targets(self) -> tuple[int, ...]:
        initial = set(self.starting_values)
        return tuple(target for target in self.targets if target not in initial)

    @property
    def instruction_lower_bound(self) -> int:
        """Each instruction can introduce at most one previously unseen target."""
        return len(self.missing_targets)


def _json_int_array(raw: str, field: str) -> tuple[int, ...]:
    try:
        values = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"{field} is not valid JSON") from exc
    if not isinstance(values, list):
        raise ValueError(f"{field} must be a JSON array")
    if any(type(value) is not int for value in values):
        raise ValueError(f"{field} must contain only integers")
    return tuple(values)


def load_puzzles(path: str | Path) -> list[Puzzle]:
    """Load puzzles.csv or practice_puzzles.csv using the documented schema."""
    puzzles: list[Puzzle] = []
    with Path(path).open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        required = {"id", "starting_values", "targets", "value_limit", "registers"}
        missing = required.difference(reader.fieldnames or ())
        if missing:
            raise ValueError(f"missing required CSV columns: {sorted(missing)}")

        for line_number, row in enumerate(reader, start=2):
            try:
                puzzles.append(
                    Puzzle(
                        puzzle_id=row["id"],
                        starting_values=_json_int_array(row["starting_values"], "starting_values"),
                        targets=_json_int_array(row["targets"], "targets"),
                        value_limit=int(row["value_limit"]),
                        registers=int(row["registers"]),
                    )
                )
            except (TypeError, ValueError) as exc:
                raise ValueError(f"invalid puzzle at CSV line {line_number}: {exc}") from exc
    return puzzles


def load_practice_metadata(path: str | Path) -> dict[str, dict[str, str]]:
    """Return optional practice-only metadata without coupling it to solver logic."""
    metadata: dict[str, dict[str, str]] = {}
    with Path(path).open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        fields = set(reader.fieldnames or ())
        if not {"id", "family", "design_tier", "lower_bound"}.issubset(fields):
            raise ValueError("practice CSV is missing expected metadata columns")
        for row in reader:
            metadata[row["id"]] = {
                "family": row["family"],
                "design_tier": row["design_tier"],
                "lower_bound": row["lower_bound"],
            }
    return metadata
