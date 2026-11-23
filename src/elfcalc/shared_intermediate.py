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


def _pair_recipes_for_pair(left: int, right: int, limit: int):
    """Yield legal recipes for one unordered pair of available values."""
    if left > right:
        left, right = right, left
    for operator in ("+", "*"):
        result = _apply(left, operator, right, limit)
        if result is not None:
            yield ArithmeticRelation(left, operator, right, result)
    if right > left:
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


def _pair_recipes(values: tuple[int, ...], limit: int):
    """Yield canonical, exact one-instruction results from the value frontier."""
    for index, left in enumerate(values):
        for right in values[index:]:
            yield from _pair_recipes_for_pair(left, right, limit)


def _recipe_order(recipe: ArithmeticRelation) -> tuple[int, int, int, int, int]:
    """Match the canonical pair/operator order used by the full frontier scan."""
    operator_order = {"+": 0, "*": 1, "-": 2, "/": 3}
    low, high = sorted((recipe.left, recipe.right))
    return (low, high, operator_order[recipe.operator], recipe.left, recipe.right)


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


def _best_two_intermediate_chain(
    recipes_by_result: dict[int, ArithmeticRelation],
    available: tuple[int, ...],
    missing: frozenset[int],
    limit: int,
):
    """Find the best exact two-intermediate chain that unlocks missing targets.

    Build the target-side bridge index once, then join it against the
    one-operation frontier. This avoids a nested inverse search over every
    target × first-anchor × second-anchor combination.
    """
    bridge_targets: dict[int, dict[int, ArithmeticRelation]] = {}
    for target in sorted(missing):
        for target_anchor in available:
            for bridge, target_recipe in _inverse_target_candidates(target, target_anchor, limit):
                if bridge in available or bridge == target:
                    continue
                targets_for_bridge = bridge_targets.setdefault(bridge, {})
                previous = targets_for_bridge.get(target)
                if previous is None or _recipe_order(target_recipe) < _recipe_order(previous):
                    targets_for_bridge[target] = target_recipe

    chains: dict[int, dict[int, dict[int, tuple[ArithmeticRelation, ArithmeticRelation]]]] = {}
    for first in sorted(recipes_by_result):
        if first in missing:
            continue
        for first_anchor in available:
            for bridge_recipe in _pair_recipes_for_pair(first, first_anchor, limit):
                bridge = bridge_recipe.result
                if bridge not in bridge_targets or bridge in available or bridge == first:
                    continue
                targets_for_bridge = chains.setdefault(first, {}).setdefault(bridge, {})
                for target, target_recipe in bridge_targets[bridge].items():
                    previous = targets_for_bridge.get(target)
                    candidate_pair = (bridge_recipe, target_recipe)
                    if previous is None or (
                        _recipe_order(candidate_pair[0]), _recipe_order(candidate_pair[1])
                    ) < (
                        _recipe_order(previous[0]), _recipe_order(previous[1])
                    ):
                        targets_for_bridge[target] = candidate_pair

    best = None
    for first in sorted(chains):
        for bridge in sorted(chains[first]):
            target_map = chains[first][bridge]
            recipes = tuple(target_map[target] for target in sorted(target_map))
            first_recipe = recipes_by_result[first]
            bridge_recipe = recipes[0][0]
            target_recipes = tuple(pair[1] for pair in recipes)
            rank = (len(target_recipes), -first, -bridge, tuple(_recipe_order(r) for r in target_recipes))
            if best is None or rank > best[0]:
                best = (rank, first_recipe, bridge_recipe, target_recipes)
    return None if best is None else best[1:]


def _extend_recipe_frontier(
    recipes_by_result: dict[int, ArithmeticRelation],
    available: set[int],
    newly_available: set[int],
    limit: int,
) -> None:
    """Incrementally add recipes involving newly available values."""
    for value in newly_available:
        recipes_by_result.pop(value, None)
    ordered_available = tuple(sorted(available))
    ordered_new = tuple(sorted(newly_available))
    new_set = set(newly_available)
    for value in ordered_new:
        for other in ordered_available:
            if other in new_set and other < value:
                continue
            for recipe in _pair_recipes_for_pair(value, other, limit):
                if recipe.result in available:
                    continue
                previous = recipes_by_result.get(recipe.result)
                if previous is None or _recipe_order(recipe) < _recipe_order(previous):
                    recipes_by_result[recipe.result] = recipe

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
    recipes_by_result: dict[int, ArithmeticRelation] = {}
    for recipe in _pair_recipes(tuple(sorted(available)), value_limit):
        if recipe.result not in available:
            previous = recipes_by_result.get(recipe.result)
            if previous is None or _recipe_order(recipe) < _recipe_order(previous):
                recipes_by_result[recipe.result] = recipe

    while missing:
        frontier = tuple(sorted(available))
        best = None

        # Instead of testing every possible intermediate against every known
        # value, invert each target equation. Work scales with targets × frontier
        # plus the pair-recipe frontier, not candidates × frontier.
        yields = _candidate_target_yields(
            recipes_by_result, frontier, frozenset(missing), value_limit
        )
        # Only candidates with immediate target value or a nonzero inverse
        # target cone can improve coverage. Avoid scanning the entire pairwise
        # recipe table when most generated values are irrelevant this round.
        relevant_candidates = sorted(
            set(yields).union(missing.intersection(recipes_by_result))
        )
        for candidate in relevant_candidates:
            recipe = recipes_by_result[candidate]
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
            if intermediate_count + 2 > max_intermediates:
                break
            chain = _best_two_intermediate_chain(
                recipes_by_result, frontier, frozenset(missing), value_limit
            )
            if chain is None:
                break
            first_recipe, bridge_recipe, target_recipes = chain
            operations.append(PlannedOperation(
                first_recipe.left, first_recipe.operator, first_recipe.right,
                first_recipe.result, False,
            ))
            operations.append(PlannedOperation(
                bridge_recipe.left, bridge_recipe.operator, bridge_recipe.right,
                bridge_recipe.result, False,
            ))
            available.update((first_recipe.result, bridge_recipe.result))
            intermediate_count += 2
            newly_available = {first_recipe.result, bridge_recipe.result}
            for target_recipe in target_recipes:
                if target_recipe.result not in missing:
                    continue
                operations.append(PlannedOperation(
                    target_recipe.left, target_recipe.operator, target_recipe.right,
                    target_recipe.result, True,
                ))
                available.add(target_recipe.result)
                newly_available.add(target_recipe.result)
                missing.remove(target_recipe.result)
            _extend_recipe_frontier(
                recipes_by_result, available, newly_available, value_limit
            )
            continue

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

        newly_available = {recipe.result}
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
            newly_available.add(target_recipe.result)
            missing.remove(target_recipe.result)

        # Maintain the reachable-recipe frontier incrementally. Every unordered
        # value pair is visited once when its newer endpoint enters the frontier,
        # instead of rebuilding the full O(n^2) pair table on every greedy round.
        _extend_recipe_frontier(
            recipes_by_result, available, newly_available, value_limit
        )

    covered = frozenset(set(goals).difference(missing))
    return SharedIntermediatePlan(
        operations=tuple(operations),
        covered_targets=covered,
        missing_targets=tuple(sorted(missing)),
        initial_values=frozenset(starts),
    )
