"""Trusted replay validator for candidate arithmetic programs."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Sequence

from .machine import ArithmeticMachine, Instruction, MachineError
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


def validate_program(puzzle: Puzzle, program: Iterable[Instruction]) -> ValidationResult:
    """Replay every instruction against the puzzle's exact machine constraints."""
    instructions = tuple(program)
    try:
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
    return tuple(instruction_from_row(row) for row in rows)
