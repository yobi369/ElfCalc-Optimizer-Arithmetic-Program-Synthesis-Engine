"""Register allocation for abstract shared-intermediate arithmetic plans.

The scheduler preserves every value with future uses and reuses dead or
uninitialized registers. It emits ordinary VM instructions and independently
replays them before returning a candidate.
"""
from __future__ import annotations

from collections import Counter
from typing import Sequence

from .machine import ArithmeticMachine, Instruction, MachineError, REGISTER_COUNT


def _reorder_for_liveness(operations: Sequence[object], starting_values: Sequence[int]) -> tuple[object, ...]:
    """Topologically reorder ready DAG nodes to reduce simultaneously live values."""
    pending = list(enumerate(operations))
    remaining = Counter()
    for operation in operations:
        remaining[operation.left] += 1
        remaining[operation.right] += 1
    available = set(starting_values)
    ordered = []
    while pending:
        ready = [(index, op) for index, op in pending if op.left in available and op.right in available]
        if not ready:
            raise ValueError("DAG contains a cycle, duplicate result, or missing dependency")
        ranked = []
        for index, op in ready:
            if op.result in available:
                raise ValueError("DAG result duplicates an already available value")
            uses = Counter((op.left, op.right))
            freed = sum(1 for value, count in uses.items() if remaining[value] == count)
            live_after = sum(1 for value in available if remaining[value] - uses[value] > 0)
            if remaining[op.result] > 0:
                live_after += 1
            is_target = bool(getattr(op, "is_target", False))
            ranked.append(((live_after, -freed, not is_target, op.result, index), index, op))
        _, chosen_index, chosen = min(ranked, key=lambda item: item[0])
        ordered.append(chosen)
        remaining[chosen.left] -= 1
        remaining[chosen.right] -= 1
        available.add(chosen.result)
        pending = [(index, op) for index, op in pending if index != chosen_index]
    return tuple(ordered)


def estimate_peak_live_values(
    operations: Sequence[object], starting_values: Sequence[int]
) -> int:
    """Estimate peak simultaneously-live value count under scheduler ordering.

    A value is live at a scheduling boundary when at least one operation still
    needs it as an operand. This is a DAG pressure estimate, not a physical
    register-allocation proof; schedule_value_dag performs the real allocation
    and VM replay.
    """
    ordered = _reorder_for_liveness(operations, starting_values)
    remaining = Counter()
    for operation in ordered:
        remaining[operation.left] += 1
        remaining[operation.right] += 1

    available = set(starting_values)
    peak = sum(1 for value in available if remaining[value] > 0)
    for operation in ordered:
        remaining[operation.left] -= 1
        remaining[operation.right] -= 1
        available.add(operation.result)
        live = sum(1 for value in available if remaining[value] > 0)
        peak = max(peak, live)
    return peak


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

    operations = _reorder_for_liveness(operations, starting_values)

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
        if any(type(value) is not int for value in (
            operation.left, operation.right, operation.result
        )):
            raise ValueError("DAG operands and results must be integers")
        if operation.operator not in {"+", "-", "*", "/"}:
            raise ValueError(f"unsupported DAG operator: {operation.operator!r}")
        if operation.operator == "+":
            expected = operation.left + operation.right
        elif operation.operator == "-":
            expected = operation.left - operation.right
        elif operation.operator == "*":
            expected = operation.left * operation.right
        else:
            if operation.right == 0 or operation.left % operation.right:
                raise ValueError("DAG division must be exact with a nonzero divisor")
            expected = operation.left // operation.right
        if expected <= 0 or expected > value_limit:
            raise ValueError("DAG operation result is outside the positive value limit")
        if operation.result != expected:
            raise ValueError(
                f"DAG result mismatch: {operation.left} {operation.operator} "
                f"{operation.right} != {operation.result}"
            )

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
