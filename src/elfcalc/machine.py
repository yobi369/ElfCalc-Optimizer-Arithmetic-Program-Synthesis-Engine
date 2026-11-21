"""Small, deterministic exact-integer virtual machine.

The instruction representation is an internal project model. The official Kaggle
serialization adapter maps competition rows to this model after schema checks.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Sequence

REGISTER_COUNT = 48
MAX_INSTRUCTIONS = 4096
MAX_PROGRAM_BYTES = 131072
MAX_VALUE = 10**18
OPERATORS = frozenset({"+", "-", "*", "/"})


class MachineError(ValueError):
    """Raised when an instruction violates machine semantics or constraints."""


@dataclass(frozen=True, slots=True)
class Instruction:
    """Compute left OP right and store the result in destination."""

    destination: int
    left: int
    operator: str
    right: int


class ArithmeticMachine:
    """Execute instructions over a fixed bank of 48 integer registers."""

    def __init__(
        self,
        initial_values: Sequence[int],
        *,
        value_limit: int | None = None,
        require_positive: bool = True,
    ) -> None:
        if len(initial_values) > REGISTER_COUNT:
            raise MachineError(f"at most {REGISTER_COUNT} initial registers are allowed")
        if not initial_values:
            raise MachineError("at least one initial value is required")
        if any(type(value) is not int for value in initial_values):
            raise MachineError("initial values must be integers")
        if require_positive and any(value <= 0 for value in initial_values):
            raise MachineError("initial values must be positive")
        if value_limit is not None and any(abs(v) > value_limit for v in initial_values):
            raise MachineError("an initial value exceeds value_limit")

        self.registers: list[int | None] = list(initial_values) + [None] * (
            REGISTER_COUNT - len(initial_values)
        )
        self.value_limit = value_limit
        self.require_positive = require_positive
        self.instruction_count = 0
        self.seen_values = set(initial_values)

    @staticmethod
    def _index(index: int, label: str) -> None:
        if type(index) is not int or not 0 <= index < REGISTER_COUNT:
            raise MachineError(f"{label} register index must be in [0, {REGISTER_COUNT - 1}]")

    def execute(self, instruction: Instruction) -> int:
        """Execute one instruction and return the newly stored integer."""
        self._index(instruction.destination, "destination")
        self._index(instruction.left, "left")
        self._index(instruction.right, "right")

        if instruction.operator not in OPERATORS:
            raise MachineError(f"unsupported operator: {instruction.operator!r}")

        lhs = self.registers[instruction.left]
        rhs = self.registers[instruction.right]
        if lhs is None or rhs is None:
            raise MachineError("instruction reads an uninitialized register")

        if instruction.operator == "+":
            result = lhs + rhs
        elif instruction.operator == "-":
            result = lhs - rhs
        elif instruction.operator == "*":
            result = lhs * rhs
        else:
            if rhs == 0:
                raise MachineError("division by zero")
            quotient, remainder = divmod(lhs, rhs)
            if remainder != 0:
                raise MachineError("division must be exact")
            result = quotient

        if self.require_positive and result <= 0:
            raise MachineError("result must be positive")
        if self.value_limit is not None and abs(result) > self.value_limit:
            raise MachineError("result exceeds value_limit")

        self.registers[instruction.destination] = result
        self.instruction_count += 1
        self.seen_values.add(result)
        return result

    def run(self, program: Iterable[Instruction]) -> "ArithmeticMachine":
        """Execute a complete program, stopping at the first invalid instruction."""
        for instruction in program:
            self.execute(instruction)
        return self

    def contains_all(self, targets: Iterable[int]) -> bool:
        """Return whether every target appeared in an initial or computed register."""
        return all(target in self.seen_values for target in targets)
