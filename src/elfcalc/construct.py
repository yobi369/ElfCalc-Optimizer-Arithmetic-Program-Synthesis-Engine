"""Independent constructive arithmetic-program synthesis.

The first solver portfolio uses positional bases, reusable constants, exact
one-step target closure, and bounded difference/factor anchors. It is a
heuristic constructor, not a proof of optimality.
"""

from __future__ import annotations

from .machine import Instruction, MAX_INSTRUCTIONS
from .puzzle import Puzzle
from .validation import validate_program


class _RegisterBuilder:
    def __init__(self, puzzle: Puzzle, protected_values: set[int]):
        self.puzzle = puzzle
        self.values: list[int | None] = list(puzzle.starting_values) + [None] * (
            puzzle.registers - len(puzzle.starting_values)
        )
        self.locations: dict[int, set[int]] = {}
        for index, value in enumerate(puzzle.starting_values):
            self.locations.setdefault(value, set()).add(index)
        self.protected = set(protected_values)
        self.ages = [0] * puzzle.registers
        self.program: list[Instruction] = []
        self.remaining = set(puzzle.targets) - set(puzzle.starting_values)

    def register(self, value: int) -> int | None:
        slots = self.locations.get(value)
        return min(slots) if slots else None

    def direct(self, target: int) -> tuple[str, int, int] | None:
        for value in sorted(self.locations):
            left = self.register(value)
            assert left is not None
            other = target - value
            if other > 0 and other in self.locations:
                return "+", left, self.register(other)
            other = value - target
            if other > 0 and other in self.locations:
                return "-", left, self.register(other)
            other = value + target
            if other in self.locations:
                return "-", self.register(other), left
            if target % value == 0 and target // value in self.locations:
                return "*", left, self.register(target // value)
            if value % target == 0 and value // target in self.locations:
                return "/", left, self.register(value // target)
            other = target * value
            if other in self.locations:
                return "/", self.register(other), left
        return None

    def emit(
        self, operator: str, left: int, right: int, pinned: frozenset[int] = frozenset()
    ) -> int:
        first, second = self.values[left], self.values[right]
        if first is None or second is None:
            raise ValueError("constructor attempted to read an undefined register")
        if operator == "+":
            result = first + second
        elif operator == "-":
            result = first - second
        elif operator == "*":
            result = first * second
        elif operator == "/" and second and first % second == 0:
            result = first // second
        else:
            raise ValueError("constructor attempted an illegal arithmetic operation")
        if not 1 <= result <= self.puzzle.value_limit:
            raise ValueError("constructor exceeded value_limit")
        existing = self.register(result)
        if existing is not None:
            return existing

        candidates = [
            index for index in range(self.puzzle.registers)
            if index not in pinned
        ]
        reusable = [
            index for index in candidates
            if self.values[index] is None
            or len(self.locations[self.values[index]]) > 1
        ]
        if reusable:
            destination = min(reusable)
        else:
            candidates = [
                index for index in candidates
                if self.values[index] not in self.protected
            ]
            if not candidates:
                raise ValueError("not enough scratch registers for protected constants")
            self.ages[left] = self.ages[right] = len(self.program) + 1
            destination = min(candidates, key=lambda index: (self.ages[index], index))

        previous = self.values[destination]
        if previous is not None:
            self.locations[previous].remove(destination)
            if not self.locations[previous]:
                del self.locations[previous]
        self.values[destination] = result
        self.locations.setdefault(result, set()).add(destination)
        self.program.append(Instruction(destination, left, operator, right))
        self.ages[left] = self.ages[right] = self.ages[destination] = len(self.program)
        self.remaining.discard(result)
        return destination

    def ensure_constant(self, value: int, pinned: frozenset[int] = frozenset()) -> int:
        existing = self.register(value)
        if existing is not None:
            return existing
        if value < 1 or value > self.puzzle.value_limit:
            raise ValueError("constant is outside the puzzle's positive value range")
        direct = self.direct(value)
        if direct is not None:
            return self.emit(*direct, pinned=pinned)
        if value == 1:
            source = next(
                (index for index, item in enumerate(self.values) if item is not None),
                None,
            )
            if source is None:
                raise ValueError("cannot construct one without a defined source")
            return self.emit("/", source, source, pinned=pinned)
        half = self.ensure_constant(value // 2, pinned)
        doubled = self.emit("+", half, half, pinned=pinned)
        if value % 2:
            one = self.ensure_constant(1, pinned | frozenset({doubled}))
            return self.emit("+", doubled, one, pinned=pinned)
        return doubled


def _digits(value: int, base: int) -> list[int]:
    output = []
    while value:
        value, digit = divmod(value, base)
        output.append(digit)
    return output


def _candidate_bases(puzzle: Puzzle) -> list[int]:
    missing = set(puzzle.targets) - set(puzzle.starting_values)
    maximum = min(puzzle.value_limit, max(missing, default=1), 32)
    ranked = []
    for base in range(2, maximum + 1):
        constants = {1, base}
        estimate = 0
        for target in missing:
            digits = _digits(target, base)
            constants.update(digit for digit in digits if digit)
            estimate += max(0, len(digits) - 1) + sum(bool(digit) for digit in digits[:-1])
        scratch_reserve = 4
        needed = len(constants - set(puzzle.starting_values))
        if len(puzzle.starting_values) + needed + scratch_reserve > puzzle.registers:
            continue
        ranked.append((estimate + needed, base))
    selected = {base for _, base in sorted(ranked)[:5]}
    selected.update(
        base for base in (2, 3, 4, 5, 8, 10, 12, 16, 20, 24, 32)
        if base <= maximum and any(candidate == base for _, candidate in ranked)
    )
    return sorted(selected)


def _solve_base(puzzle: Puzzle, base: int) -> tuple[Instruction, ...]:
    missing = set(puzzle.targets) - set(puzzle.starting_values)
    if not missing:
        return ()
    constants = {1, base}
    for target in missing:
        constants.update(digit for digit in _digits(target, base) if digit)
    builder = _RegisterBuilder(puzzle, constants)

    # First exploit any targets already reachable in one operation.
    changed = True
    while changed and builder.remaining:
        changed = False
        for target in sorted(builder.remaining):
            recipe = builder.direct(target)
            if recipe is not None:
                builder.emit(*recipe)
                changed = True
    if not builder.remaining:
        return tuple(builder.program)

    for constant in sorted(constants):
        builder.ensure_constant(constant)
        if not builder.remaining:
            return tuple(builder.program)

    def estimate(value: int) -> int:
        if builder.register(value) is not None:
            return 0
        digits = _digits(value, base)
        return max(0, len(digits) - 1) + sum(bool(digit) for digit in digits[:-1]) + 2

    def build(value: int, pinned: frozenset[int] = frozenset()) -> int:
        existing = builder.register(value)
        if existing is not None:
            return existing
        direct = builder.direct(value)
        if direct is not None:
            return builder.emit(*direct, pinned=pinned)
        if value < base:
            return builder.ensure_constant(value, pinned)
        quotient, remainder = divmod(value, base)
        source = build(quotient, pinned)
        base_register = builder.register(base)
        if base_register is None:
            base_register = builder.ensure_constant(base, pinned | frozenset({source}))
        product = builder.emit("*", source, base_register, pinned=frozenset({base_register}))
        if remainder:
            digit = builder.register(remainder)
            if digit is None:
                digit = builder.ensure_constant(remainder, frozenset({product, base_register}))
            return builder.emit("+", product, digit, pinned=frozenset({base_register}))
        return product

    # Build easy targets first so their values become reusable anchors.
    ordered = sorted(missing, key=lambda value: (estimate(value), value))
    for target in ordered:
        if target not in builder.remaining:
            continue
        if builder.register(target) is not None:
            builder.remaining.discard(target)
            continue
        direct = builder.direct(target)
        if direct is not None:
            builder.emit(*direct)
            continue

        best_cost = estimate(target)
        best_kind = ("build", target, None, None)
        known_values = sorted(
            builder.locations,
            key=lambda value: (abs(target - value), value),
        )
        for anchor in known_values[:10]:
            if anchor == target:
                continue
            difference = abs(target - anchor)
            if difference:
                cost = estimate(difference) + 1
                if cost < best_cost:
                    best_cost = cost
                    best_kind = ("difference", difference, anchor, "+" if target > anchor else "-")
            if 1 < anchor < target and target % anchor == 0:
                quotient = target // anchor
                cost = estimate(quotient) + 1
                if cost < best_cost:
                    best_cost = cost
                    best_kind = ("product", quotient, anchor, "*")
            elif anchor > target and anchor % target == 0:
                divisor = anchor // target
                cost = estimate(divisor) + 1
                if cost < best_cost:
                    best_cost = cost
                    best_kind = ("quotient", divisor, anchor, "/")

        kind, argument, anchor, operation = best_kind
        if kind == "build":
            build(target)
        else:
            anchor_register = builder.register(anchor)
            if anchor_register is None:
                build(target)
            else:
                argument_register = build(argument, frozenset({anchor_register}))
                if kind == "difference" and operation == "-":
                    builder.emit("-", anchor_register, argument_register)
                elif kind == "difference":
                    builder.emit("+", anchor_register, argument_register)
                elif kind == "product":
                    builder.emit("*", anchor_register, argument_register)
                else:
                    builder.emit("/", anchor_register, argument_register)

        if not builder.remaining:
            break
        if len(builder.program) > MAX_INSTRUCTIONS:
            raise ValueError("constructed program exceeds the instruction limit")

    if builder.remaining:
        raise ValueError(f"constructor did not cover targets: {sorted(builder.remaining)}")
    result = tuple(builder.program)
    validation = validate_program(puzzle, result)
    if not validation.complete:
        raise ValueError(validation.error or f"constructed program misses {validation.missing_targets}")
    return result


def solve_constructive(puzzle: Puzzle) -> tuple[Instruction, ...]:
    """Try a deterministic portfolio of positional bases and return its shortest result."""
    if not set(puzzle.targets) - set(puzzle.starting_values):
        return ()
    candidates = []
    for base in _candidate_bases(puzzle):
        try:
            candidate = _solve_base(puzzle, base)
        except (ValueError, KeyError, RecursionError):
            continue
        if len(candidate) <= MAX_INSTRUCTIONS:
            candidates.append(candidate)
    if not candidates:
        raise ValueError(f"no valid constructive candidate found for {puzzle.puzzle_id}")
    return min(candidates, key=lambda program: (len(program), program))
