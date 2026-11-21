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



def _shared_prefix_order(values: set[int], base: int, estimate) -> list[int]:
    """Greedily order targets by shared most-significant positional prefixes.

    Nearby targets in this ordering are more likely to reuse quotient/prefix
    values already materialized by the recursive base constructor.
    """
    digits = {value: tuple(reversed(_digits(value, base))) for value in values}
    remaining = set(values)
    if not remaining:
        return []
    first = min(remaining, key=lambda value: (estimate(value), digits[value], value))
    ordered = [first]
    remaining.remove(first)
    while remaining:
        previous = digits[ordered[-1]]

        def priority(value: int):
            current = digits[value]
            common = 0
            for left, right in zip(previous, current):
                if left != right:
                    break
                common += 1
            return (-common, estimate(value), digits[value], value)

        selected = min(remaining, key=priority)
        ordered.append(selected)
        remaining.remove(selected)
    return ordered


def _candidate_bases(puzzle: Puzzle) -> list[int]:
    """Enumerate every positional base that leaves a small scratch reserve."""
    missing = set(puzzle.targets) - set(puzzle.starting_values)
    maximum = min(puzzle.value_limit, max(missing, default=1), 32)
    selected = []
    for base in range(2, maximum + 1):
        constants = {1, base}
        for target in missing:
            constants.update(digit for digit in _digits(target, base) if digit)
        needed = len(constants - set(puzzle.starting_values))
        if len(puzzle.starting_values) + needed + 4 <= puzzle.registers:
            selected.append(base)
    return selected

def _solve_base(puzzle: Puzzle, base: int, shared_prefix: bool = False) -> tuple[Instruction, ...]:
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
    ordered = (
        _shared_prefix_order(missing, base, estimate)
        if shared_prefix
        else sorted(missing, key=lambda value: (estimate(value), value))
    )
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


def _signed_window_terms(value: int, width: int) -> list[tuple[int, int]]:
    """Encode a positive integer as high-to-low signed odd binary windows."""
    digits = []
    modulus = 1 << width
    while value:
        digit = 0
        if value & 1:
            digit = value % modulus
            if digit >= modulus // 2:
                digit -= modulus
            value -= digit
        digits.append(digit)
        value //= 2

    positions = [index for index in range(len(digits) - 1, -1, -1) if digits[index]]
    if not positions:
        return []
    terms = [(0, digits[positions[0]])]
    previous = positions[0]
    for position in positions[1:]:
        terms.append((previous - position, digits[position]))
        previous = position
    if previous:
        terms.append((previous, 0))
    return terms


def _solve_signed_window(puzzle: Puzzle, width: int) -> tuple[Instruction, ...]:
    missing = set(puzzle.targets) - set(puzzle.starting_values)
    if not missing:
        return ()
    terms = {target: _signed_window_terms(target, width) for target in missing}
    needed = {1}
    for target_terms in terms.values():
        for shift, digit in target_terms:
            if digit:
                needed.add(abs(digit))
            while shift:
                step = min(10, shift)
                needed.add(1 << step)
                shift -= step

    if len(puzzle.starting_values) + len(needed - set(puzzle.starting_values)) + 4 > puzzle.registers:
        raise ValueError("signed-window constants leave too few scratch registers")

    builder = _RegisterBuilder(puzzle, needed)
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

    for constant in sorted(needed):
        builder.ensure_constant(constant)
        if not builder.remaining:
            return tuple(builder.program)

    for target in sorted(missing, key=lambda item: (len(terms[item]), item)):
        if target not in builder.remaining:
            continue
        recipe = builder.direct(target)
        if recipe is not None:
            builder.emit(*recipe)
            continue
        target_terms = terms[target]
        if not target_terms or target_terms[0][1] <= 0:
            raise ValueError("signed representation has no positive leading digit")
        accumulator = builder.ensure_constant(target_terms[0][1])
        for shift, digit in target_terms[1:]:
            while shift:
                step = min(10, shift)
                factor = builder.register(1 << step)
                if factor is None:
                    factor = builder.ensure_constant(1 << step, frozenset({accumulator}))
                accumulator = builder.emit("*", accumulator, factor, pinned=frozenset({factor}))
                shift -= step
            if digit:
                constant = builder.register(abs(digit))
                if constant is None:
                    constant = builder.ensure_constant(abs(digit), frozenset({accumulator}))
                accumulator = builder.emit(
                    "+" if digit > 0 else "-",
                    accumulator,
                    constant,
                    pinned=frozenset({constant}),
                )
        if target not in builder.locations:
            raise ValueError(f"signed-window construction did not produce target {target}")
        if not builder.remaining:
            break
        if len(builder.program) > MAX_INSTRUCTIONS:
            raise ValueError("signed-window program exceeds the instruction limit")

    if builder.remaining:
        raise ValueError(f"signed-window solver missed targets: {sorted(builder.remaining)}")
    result = tuple(builder.program)
    validation = validate_program(puzzle, result)
    if not validation.complete:
        raise ValueError(validation.error or "signed-window program failed validation")
    return result


def _solve_signed_window_streaming(puzzle: Puzzle, width: int) -> tuple[Instruction, ...]:
    """Build wider signed-window digits lazily to avoid pinning a large constant table."""
    missing = set(puzzle.targets) - set(puzzle.starting_values)
    if not missing:
        return ()
    terms = {target: _signed_window_terms(target, width) for target in missing}
    builder = _RegisterBuilder(puzzle, {1})

    # Cheap target closure can avoid constructing any window constants.
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

    for target in sorted(missing, key=lambda item: (len(terms[item]), item)):
        if target not in builder.remaining:
            continue
        target_terms = terms[target]
        if not target_terms or target_terms[0][1] <= 0:
            raise ValueError("signed representation has no positive leading digit")

        accumulator = builder.ensure_constant(target_terms[0][1])
        for shift, digit in target_terms[1:]:
            while shift:
                step = min(10, shift)
                factor_value = 1 << step
                factor = builder.ensure_constant(
                    factor_value, pinned=frozenset({accumulator})
                )
                accumulator = builder.emit(
                    "*", accumulator, factor, pinned=frozenset({factor})
                )
                shift -= step
            if digit:
                digit_register = builder.ensure_constant(
                    abs(digit), pinned=frozenset({accumulator})
                )
                accumulator = builder.emit(
                    "+" if digit > 0 else "-",
                    accumulator,
                    digit_register,
                    pinned=frozenset({digit_register}),
                )

        if builder.register(target) is None:
            raise ValueError(f"streaming signed-window construction missed {target}")
        if len(builder.program) > MAX_INSTRUCTIONS:
            raise ValueError("streaming signed-window program exceeds instruction limit")

    result = tuple(builder.program)
    validation = validate_program(puzzle, result)
    if not validation.complete:
        raise ValueError(validation.error or "streaming signed-window candidate failed validation")
    return result



def _solve_shared_intermediate_dag(puzzle: Puzzle) -> tuple[Instruction, ...]:
    """Construct reusable one-level DAG nodes that unlock multiple targets.

    A node is accepted only when its value makes at least two currently
    uncovered targets directly reachable from the existing value set. The
    resulting targets are then emitted through the ordinary register builder.
    This bounded beam-free pass is deterministic and keeps exact arithmetic.
    """
    missing = set(puzzle.targets) - set(puzzle.starting_values)
    if not missing:
        return ()

    builder = _RegisterBuilder(puzzle, set())
    while builder.remaining:
        # First consume all targets already reachable without adding a node.
        changed = True
        while changed:
            changed = False
            for target in sorted(builder.remaining):
                recipe = builder.direct(target)
                if recipe is not None:
                    builder.emit(*recipe)
                    changed = True
        if not builder.remaining:
            break

        known = sorted(builder.locations)
        best = None
        # Enumerate legal one-instruction expressions over currently known
        # values. Each accepted expression must unlock at least two targets.
        for left_value in known:
            left = builder.register(left_value)
            assert left is not None
            for right_value in known:
                right = builder.register(right_value)
                assert right is not None
                expressions = [
                    ("+", left_value + right_value, "+"),
                    ("-", left_value - right_value, "-"),
                    ("*", left_value * right_value, "*"),
                ]
                if right_value and left_value % right_value == 0:
                    expressions.append(("/", left_value // right_value, "/"))
                for operator, result, _ in expressions:
                    if result <= 0 or result > puzzle.value_limit:
                        continue
                    if result in builder.locations or result in builder.remaining:
                        continue
                    gain = 0
                    for target in builder.remaining:
                        if target == result:
                            continue
                        for anchor in known:
                            if (result + anchor == target or
                                abs(result - anchor) == target or
                                result * anchor == target or
                                (anchor and result % anchor == 0 and result // anchor == target) or
                                (result and anchor % result == 0 and anchor // result == target)):
                                gain += 1
                                break
                    if gain < 2:
                        continue
                    candidate = (gain, -result, operator, left, right, result)
                    if best is None or candidate > best:
                        best = candidate

        if best is None:
            break
        _, _, operator, left, right, _ = best
        builder.emit(operator, left, right)

    if builder.remaining:
        raise ValueError(f"shared-intermediate DAG missed targets: {sorted(builder.remaining)}")
    result = tuple(builder.program)
    validation = validate_program(puzzle, result)
    if not validation.complete:
        raise ValueError(validation.error or "shared-intermediate DAG failed validation")
    return result


def solve_constructive(puzzle: Puzzle, include_shared_dag: bool = True) -> tuple[Instruction, ...]:
    """Try positive-radix and signed-window constructions; retain the shortest."""
    if not set(puzzle.targets) - set(puzzle.starting_values):
        return ()
    candidates = []
    if include_shared_dag:
        try:
            candidates.append(_solve_shared_intermediate_dag(puzzle))
        except (ValueError, KeyError, RecursionError):
            pass
    feasible_bases = _candidate_bases(puzzle)
    for base in feasible_bases:
        try:
            candidates.append(_solve_base(puzzle, base))
        except (ValueError, KeyError, RecursionError):
            continue
    # A second ordering pass deliberately clusters targets with common
    # high-order digits so recursive prefix values can be reused.
    for base in (2, 4, 8, 10, 16, 32):
        if base not in feasible_bases:
            continue
        try:
            candidates.append(_solve_base(puzzle, base, shared_prefix=True))
        except (ValueError, KeyError, RecursionError):
            continue
    for width in (3, 4, 5, 6, 7, 8):
        try:
            candidates.append(_solve_signed_window(puzzle, width))
        except (ValueError, KeyError, RecursionError):
            continue
    # Wider windows reduce the number of signed digits. Build their constants
    # lazily so the 48-register machine is not consumed by a large digit table.
    for width in (9, 10, 11, 12, 13, 14):
        try:
            candidates.append(_solve_signed_window_streaming(puzzle, width))
        except (ValueError, KeyError, RecursionError):
            continue
    candidates = [candidate for candidate in candidates if len(candidate) <= MAX_INSTRUCTIONS]
    if not candidates:
        raise ValueError(f"no valid constructive candidate found for {puzzle.puzzle_id}")
    return min(
        candidates,
        key=lambda program: (
            len(program),
            tuple((item.operator, item.left, item.right, item.destination) for item in program),
        ),
    )
