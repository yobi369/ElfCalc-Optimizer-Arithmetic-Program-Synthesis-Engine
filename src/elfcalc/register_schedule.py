"""Register allocation for abstract shared-intermediate arithmetic plans.

The scheduler preserves every value with future uses and reuses dead or
uninitialized registers. It emits ordinary VM instructions and independently
replays them before returning a candidate.
"""
from __future__ import annotations

from collections import Counter
from typing import Sequence

from .machine import ArithmeticMachine, Instruction, MachineError, REGISTER_COUNT


def schedule_value_dag(operations: Sequence[object], starting_values: Sequence[int],
                       value_limit: int) -> tuple[Instruction, ...]:
    """Lower a topologically ordered value DAG into a 48-register program.

    A register may be overwritten only after its current value's final use.
    The VM reads both operands before writing the destination, so a source
    register whose final use is the current instruction is reusable.
    """
    if not starting_values or len(starting_values) > REGISTER_COUNT:
        raise ValueError("starting_values must fit the machine register bank")
    if type(value_limit) is not int or value_limit <= 0:
        raise ValueError("value_limit must be a positive integer")

    remaining = Counter()
    for operation in operations:
        remaining[operation.left] += 1
        remaining[operation.right] += 1

    registers: list[int | None] = list(starting_values) + [None] * (
        REGISTER_COUNT - len(starting_values)
    )
    locations: dict[int, set[int]] = {}
    for index, value in enumerate(starting_values):
        locations.setdefault(value, set()).add(index)

    program: list[Instruction] = []
    for operation in operations:
        left_slots = locations.get(operation.left)
        right_slots = locations.get(operation.right)
        if not left_slots or not right_slots:
            raise ValueError(
                f"DAG is not schedulable: missing operand for {operation!r}"
            )
        left_register = min(left_slots)
        right_register = min(right_slots)

        remaining[operation.left] -= 1
        remaining[operation.right] -= 1

        free = [index for index, value in enumerate(registers) if value is None]
        if free:
            destination = min(free)
        else:
            reusable = [
                index for index, value in enumerate(registers)
                if value is not None and remaining[value] <= 0
            ]
            if not reusable:
                raise ValueError("DAG exceeds available registers under current ordering")
            destination = min(reusable)

        previous = registers[destination]
        if previous is not None:
            slots = locations[previous]
            slots.remove(destination)
            if not slots:
                del locations[previous]

        registers[destination] = operation.result
        locations.setdefault(operation.result, set()).add(destination)
        program.append(Instruction(
            destination=destination,
            left=left_register,
            operator=operation.operator,
            right=right_register,
        ))

    machine = ArithmeticMachine(
        starting_values, value_limit=value_limit, require_positive=True
    )
    try:
        machine.run(program)
    except MachineError as exc:
        raise ValueError(f"scheduled DAG failed VM replay: {exc}") from exc

    for operation in operations:
        if operation.result not in machine.seen_values:
            raise ValueError("scheduled program did not produce every DAG value")
    return tuple(program)
