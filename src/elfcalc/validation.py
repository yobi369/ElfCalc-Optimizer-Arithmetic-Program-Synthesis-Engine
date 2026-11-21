"""Trusted replay validator for candidate arithmetic programs."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Iterable, Sequence

from .machine import (
    MAX_INSTRUCTIONS,
    MAX_PROGRAM_BYTES,
    ArithmeticMachine,
    Instruction,
    MachineError,
)
from .puzzle import Puzzle


@dataclass(frozen=True, slots=True)
class ValidationResult:
    valid: bool
    instruction_count: int
    covered_targets: frozenset[int]
    missing_targets: tuple[int, ...]
    error: str | None = None

    @property
    def complete(self) -> bool:
        return self.valid and not self.missing_targets


def _serialized_program_size(instructions: Sequence[Instruction]) -> int:
    rows = [
        [instruction.operator, instruction.left, instruction.right, instruction.destination]
        for instruction in instructions
    ]
    try:
        encoded = json.dumps(rows, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    except (TypeError, ValueError, AttributeError) as exc:
        raise MachineError(f"program cannot be serialized: {exc}") from exc
    return len(encoded)


def validate_program(puzzle: Puzzle, program: Iterable[Instruction]) -> ValidationResult:
    """Replay every instruction and enforce the competition's structural limits."""
    try:
        instructions = tuple(program)
    except TypeError as exc:
        return ValidationResult(False, 0, frozenset(), puzzle.targets, str(exc))

    if len(instructions) > MAX_INSTRUCTIONS:
        return ValidationResult(
            False, len(instructions), frozenset(), puzzle.targets,
            f"program exceeds {MAX_INSTRUCTIONS} instructions",
        )
    try:
        if _serialized_program_size(instructions) > MAX_PROGRAM_BYTES:
            raise MachineError(f"program exceeds {MAX_PROGRAM_BYTES} UTF-8 bytes")
        machine = ArithmeticMachine(
            puzzle.starting_values,
            value_limit=puzzle.value_limit,
            require_positive=True,
        )
        machine.run(instructions)
    except (MachineError, TypeError, AttributeError) as exc:
        return ValidationResult(
            valid=False,
            instruction_count=len(instructions),
            covered_targets=frozenset(),
            missing_targets=puzzle.targets,
            error=str(exc),
        )

    covered = frozenset(set(puzzle.targets).intersection(machine.seen_values))
    missing = tuple(target for target in puzzle.targets if target not in covered)
    return ValidationResult(
        valid=True,
        instruction_count=len(instructions),
        covered_targets=covered,
        missing_targets=missing,
    )


def instruction_from_row(row: Sequence[object]) -> Instruction:
    """Convert [op, source_i, source_j, destination] into an instruction."""
    if len(row) != 4:
        raise ValueError("an instruction must contain [op, i, j, d]")
    operator, left, right, destination = row
    if not isinstance(operator, str):
        raise ValueError("instruction operator must be a string")
    if any(type(index) is not int for index in (left, right, destination)):
        raise ValueError("instruction register indexes must be integers")
    return Instruction(destination, left, operator, right)


def program_from_rows(rows: Sequence[Sequence[object]]) -> tuple[Instruction, ...]:
    if len(rows) > MAX_INSTRUCTIONS:
        raise ValueError(f"program exceeds {MAX_INSTRUCTIONS} instructions")
    return tuple(instruction_from_row(row) for row in rows)
