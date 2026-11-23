"""Greedy value-DAG planner for shared arithmetic intermediates.

The planner operates on integer values, not physical registers. Its output is
an abstract recipe DAG that must later be scheduled, register-allocated, and
replayed by the VM validator before it can be used as a submission program.
"""
from __future__ import annotations

from dataclasses import dataclass

from .target_dna import ArithmeticRelation


@dataclass(frozen=True, slots=True)
class PlannedOperation:
    """One value-level arithmetic operation in the proposed DAG."""

    left: int
    operator: str
    right: int
    result: int
    is_target: bool


@dataclass(frozen=True, slots=True)
class SharedIntermediatePlan:
    """Greedy DAG proposal and its basic coverage accounting."""

    operations: tuple[PlannedOperation, ...]
    covered_targets: frozenset[int]
    missing_targets: tuple[int, ...]
    initial_values: frozenset[int]

    @property
    def instruction_count(self) -> int:
        return len(self.operations)

    @property
    def intermediate_count(self) -> int:
        return sum(not operation.is_target for operation in self.operations)


def _apply(left: int, operator: str, right: int, limit: int) -> int | None:
    if operator == "+":
        result = left + right
    elif operator == "-":
        if left <= right:
            return None
        result = left - right
    elif operator == "*":
        result = left * right
    elif operator == "/":
        if right == 0 or left % right:
            return None
        result = left // right
    else:
        raise ValueError(f"unsupported operator: {operator}")
    if result <= 0 or result > limit:
        return None
    return result


def _pair_recipes(values: tuple[int, ...], limit: int):
    """Yield canonical, exact one-instruction results from the value frontier."""
    for index, left in enumerate(values):
        for right in values[index:]:
            for operator in ("+", "*"):
                result = _apply(left, operator, right, limit)
                if result is not None:
                    yield ArithmeticRelation(left, operator, right, result)
            if left > right:
                result = _apply(left, "-", right, limit)
                if result is not None:
                    yield ArithmeticRelation(left, "-", right, result)
            elif right > left:
                result = _apply(right, "-", left, limit)
                if result is not None:
                    yield ArithmeticRelation(right, "-", left, result)
            if right and left % right == 0:
                result = _apply(left, "/", right, limit)
                if result is not None:
                    yield ArithmeticRelation(left, "/", right, result)
            if left and right % left == 0:
                result = _apply(right, "/", left, limit)
                if result is not None:
                    yield ArithmeticRelation(right, "/", left, result)


def _inverse_target_candidates(target: int, other: int, limit: int):
    """Yield candidate intermediates that combine with other to make target."""
    options = (
        (target - other, "+", target - other, other),
        (target + other, "-", target + other, other),
        (other - target, "-", other, other - target),
        (target // other if other and target % other == 0 else 0,
         "*", target // other if other and target % other == 0 else 0, other),
        (target * other, "/", target * other, other),
        (other // target if target and other % target == 0 else 0,
         "/", other, other // target if target and other % target == 0 else 0),
    )
    for candidate, operator, left, right in options:
        if 0 < candidate <= limit:
            yield candidate, ArithmeticRelation(left, operator, right, target)


def _candidate_target_yields(
    recipes_by_result: dict[int, ArithmeticRelation],
    available: tuple[int, ...],
    missing: frozenset[int],
    limit: int,
) -> dict[int, tuple[ArithmeticRelation, ...]]:
    """Invert target equations so only target-relevant candidates are scored."""
    found: dict[int, dict[int, ArithmeticRelation]] = {}
    for target in sorted(missing):
        for other in available:
            for candidate, relation in _inverse_target_candidates(target, other, limit):
                if candidate in recipes_by_result and candidate != target:
                    found.setdefault(candidate, {}).setdefault(target, relation)
    return {
        candidate: tuple(targets[target] for target in sorted(targets))
        for candidate, targets in found.items()
    }


def plan_shared_intermediates(
    starting_values: tuple[int, ...] | list[int],
    targets: tuple[int, ...] | list[int],
    value_limit: int,
    *,
    max_intermediates: int = 256,
) -> SharedIntermediatePlan:
    """Greedily construct a value DAG with high marginal target yield.

    At each round, consider every value reachable in one legal operation from
    the current frontier. A candidate's benefit is the number of still-missing
    targets it can unlock in one further operation, including itself if it is
    a target. Ties are resolved deterministically. This is deliberately a
    baseline heuristic, not a globally optimal solver.
    """
    starts = tuple(starting_values)
    goals = tuple(targets)
    if type(value_limit) is not int or value_limit <= 0:
        raise ValueError("value_limit must be a positive integer")
    if type(max_intermediates) is not int or max_intermediates < 0:
        raise ValueError("max_intermediates must be a nonnegative integer")
    if not starts or any(type(v) is not int or v <= 0 or v > value_limit for v in starts):
        raise ValueError("starting values must be positive integers within value_limit")
    if any(type(v) is not int or v <= 0 or v > value_limit for v in goals):
        raise ValueError("targets must be positive integers within value_limit")
    if len(set(goals)) != len(goals):
        raise ValueError("targets must be unique")

    available = set(starts)
    missing = set(goals).difference(available)
    operations: list[PlannedOperation] = []
    intermediate_count = 0

    while missing:
        frontier = tuple(sorted(available))
        best = None
        recipes_by_result: dict[int, ArithmeticRelation] = {}
        for recipe in _pair_recipes(frontier, value_limit):
            if recipe.result not in available:
                recipes_by_result.setdefault(recipe.result, recipe)

        # Instead of testing every possible intermediate against every known
        # value, invert each target equation. Work scales with targets × frontier
        # plus the pair-recipe frontier, not candidates × frontier.
        yields = _candidate_target_yields(
            recipes_by_result, frontier, frozenset(missing), value_limit
        )
        for candidate, recipe in recipes_by_result.items():
            immediate = candidate in missing
            unlocked = tuple(
                relation for relation in yields.get(candidate, ())
                if relation.result != candidate
            )
            gain = len(unlocked) + int(immediate)
            if gain == 0:
                continue

            # Consume a directly reachable target before speculative
            # intermediates: it costs one instruction and cannot be made cheaper
            # by postponing it. Among equal classes, maximize one-step target yield.
            rank = (int(immediate), gain, -candidate, recipe.operator, -recipe.left, -recipe.right)
            if best is None or rank > best[0]:
                best = (rank, recipe, unlocked, immediate)

        if best is None:
            break

        _, recipe, unlocked, immediate = best
        is_target = recipe.result in missing
        operations.append(PlannedOperation(
            recipe.left, recipe.operator, recipe.right, recipe.result, is_target
        ))
        available.add(recipe.result)
        missing.discard(recipe.result)
        if not is_target:
            intermediate_count += 1
            if intermediate_count > max_intermediates:
                available.remove(recipe.result)
                operations.pop()
                break

        for target_recipe in unlocked:
            if target_recipe.result not in missing:
                continue
            operations.append(PlannedOperation(
                target_recipe.left,
                target_recipe.operator,
                target_recipe.right,
                target_recipe.result,
                True,
            ))
            available.add(target_recipe.result)
            missing.remove(target_recipe.result)

    covered = frozenset(set(goals).difference(missing))
    return SharedIntermediatePlan(
        operations=tuple(operations),
        covered_targets=covered,
        missing_targets=tuple(sorted(missing)),
        initial_values=frozenset(starts),
    )
