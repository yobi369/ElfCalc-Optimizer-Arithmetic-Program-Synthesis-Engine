"""Bounded beam search over arithmetic value-DAG fragments.

This module is deliberately experimental and is not wired into the production
solver. It explores a deterministic, resource-bounded frontier and returns a
proposal only; callers must schedule and replay it with the VM validator.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .register_schedule import estimate_peak_live_values, schedule_value_dag
from .shared_intermediate import (
    PlannedOperation,
    SharedIntermediatePlan,
    _pair_recipes,
    _recipe_order,
    _inverse_target_candidates,
)


@dataclass(frozen=True, slots=True)
class _State:
    operations: tuple[PlannedOperation, ...]
    available: frozenset[int]
    missing: frozenset[int]
    intermediates: int


def _state_key(
    state: _State, starts: tuple[int, ...]
) -> tuple[tuple[int, ...], tuple[int, ...], int, int, int]:
    """Deduplicate equivalent frontiers without erasing cost/pressure trade-offs."""
    return (
        tuple(sorted(state.missing)),
        tuple(sorted(state.available)),
        len(state.operations),
        _peak(state, starts),
        state.intermediates,
    )


def _direct_yield(state: _State, limit: int) -> int:
    """Count distinct missing targets reachable in one legal next operation."""
    reachable = set()
    values = tuple(sorted(state.available))
    for recipe in _pair_recipes(values, limit):
        if recipe.result in state.missing:
            reachable.add(recipe.result)
    return len(reachable)


def _peak(state: _State, starts: tuple[int, ...]) -> int:
    return estimate_peak_live_values(state.operations, starts)



def _forward_anchor_pool(
    starts: tuple[int, ...], limit: int, depth: int, cap: int
) -> tuple[int, ...]:
    """Build a deterministic, capped pool of values forward-reachable from starts."""
    known = set(starts)
    frontier = set(starts)
    for _ in range(depth):
        additions: set[int] = set()
        ordered = tuple(sorted(known))
        for recipe in _pair_recipes(ordered, limit):
            if recipe.result not in known:
                additions.add(recipe.result)
                if len(known) + len(additions) >= cap:
                    break
        if not additions:
            break
        room = max(0, cap - len(known))
        selected = set(sorted(additions)[:room])
        if not selected:
            break
        known.update(selected)
        frontier = selected
    return tuple(sorted(known))


def _backward_target_cone(
    goals: frozenset[int],
    anchors: tuple[int, ...],
    limit: int,
    depth: int,
    cap: int,
) -> frozenset[int]:
    """Approximate exact reverse-reachable operands for the missing targets.

    Inverse equations are evaluated against a bounded forward-reachable anchor
    pool. This is a heuristic cone, not a completeness proof: the cap and depth
    deliberately bound the work.
    """
    cone = set(goals)
    frontier = set(goals)
    for _ in range(depth):
        additions: set[int] = set()
        for target in sorted(frontier):
            for anchor in anchors:
                if anchor == target:
                    continue
                for candidate, _relation in _inverse_target_candidates(
                    target, anchor, limit
                ):
                    if candidate not in cone:
                        additions.add(candidate)
                        if len(cone) + len(additions) >= cap:
                            break
                if len(cone) + len(additions) >= cap:
                    break
            if len(cone) + len(additions) >= cap:
                break
        if not additions:
            break
        room = max(0, cap - len(cone))
        selected = set(sorted(additions)[:room])
        if not selected:
            break
        cone.update(selected)
        frontier = selected
    return frozenset(cone)



def _multi_target_cone_support(
    goals: frozenset[int],
    anchors: tuple[int, ...],
    limit: int,
    depth: int,
    cap_per_target: int,
) -> dict[int, frozenset[int]]:
    """Map each reverse-cone value to the goals it can potentially unlock.

    Cones are constructed independently per goal so shared values retain their
    target provenance. A value supported by several goals is a candidate
    shared intermediate. Per-goal caps keep this computation deterministic
    and bounded; this remains a heuristic reachability signal.
    """
    support: dict[int, set[int]] = {}
    for goal in sorted(goals):
        cone = _backward_target_cone(
            frozenset((goal,)), anchors, limit, depth, cap_per_target
        )
        for value in cone:
            support.setdefault(value, set()).add(goal)
    return {
        value: frozenset(targets)
        for value, targets in sorted(support.items())
    }



def _shared_completion_yield(
    state: _State,
    candidate: int,
    limit: int,
    subgraph_support: dict[int, frozenset[int]],
) -> int:
    """Count supported goals exposed by adding a second node to a known prefix."""
    supported_goals: set[int] = set()
    for first in state.available:
        supported_goals.update(subgraph_support.get(first, ()))
    if not supported_goals:
        return 0
    available = tuple(sorted(state.available.union((candidate,))))
    return len({
        recipe.result
        for recipe in _pair_recipes(available, limit)
        if recipe.result in state.missing and recipe.result in supported_goals
    })


def _rank(
    state: _State,
    starts: tuple[int, ...],
    limit: int,
    subgraph_support: dict[int, frozenset[int]] | None = None,
) -> tuple:
    # Coverage is primary. Direct reachability and retained shared-subgraph
    # potential then guide incomplete states; cost and live pressure follow.
    shared_potential = max(
        (len(subgraph_support.get(value, ())) for value in state.available),
        default=0,
    ) if subgraph_support else 0
    return (
        len(state.missing),
        -shared_potential,
        -_direct_yield(state, limit),
        len(state.operations),
        _peak(state, starts),
        state.intermediates,
        tuple(sorted(state.missing)),
        tuple(sorted(state.available)),
    )


def _pareto_by_coverage(
    states: Iterable[_State], starts: tuple[int, ...]
) -> tuple[_State, ...]:
    """Preserve cost/pressure trade-offs separately for each coverage pattern."""
    groups: dict[frozenset[int], list[_State]] = {}
    for state in states:
        groups.setdefault(state.missing, []).append(state)
    kept = []
    for missing in sorted(groups, key=lambda values: tuple(sorted(values))):
        candidates = groups[missing]
        for candidate in candidates:
            cost = len(candidate.operations)
            pressure = _peak(candidate, starts)
            dominated = False
            for other in candidates:
                if other is candidate:
                    continue
                other_cost = len(other.operations)
                other_pressure = _peak(other, starts)
                if (other_cost <= cost and other_pressure <= pressure
                        and (other_cost < cost or other_pressure < pressure)):
                    dominated = True
                    break
            if not dominated:
                kept.append(candidate)
    return tuple(kept)



def _shared_subgraph_support(
    starts: tuple[int, ...],
    goals: frozenset[int],
    limit: int,
    *,
    max_first_recipes: int = 128,
    max_second_recipes_per_first: int = 256,
) -> dict[int, frozenset[int]]:
    """Find first nodes of bounded two-intermediate DAGs that unlock goals.

    For each first recipe from the actual starting frontier, enumerate a
    capped second frontier using that first result, then measure which goals
    become one operation away. The returned support is a look-ahead heuristic:
    it does not claim the second node is already available to the beam.
    """
    support: dict[int, set[int]] = {}
    first_recipes = [
        recipe for recipe in _pair_recipes(tuple(sorted(set(starts))), limit)
        if recipe.result not in starts and recipe.result not in goals
    ]
    first_recipes.sort(key=_recipe_order)
    for first in first_recipes[:max_first_recipes]:
        second_frontier = tuple(sorted(set(starts).union((first.result,))))
        second_recipes = [
            recipe for recipe in _pair_recipes(second_frontier, limit)
            if recipe.result not in second_frontier and recipe.result not in goals
        ]
        second_recipes.sort(key=_recipe_order)
        unlocked: set[int] = set()
        for second in second_recipes[:max_second_recipes_per_first]:
            available = tuple(sorted(set(second_frontier).union((second.result,))))
            for target_recipe in _pair_recipes(available, limit):
                if target_recipe.result in goals:
                    unlocked.add(target_recipe.result)
            if len(unlocked) == len(goals):
                break
        if unlocked:
            support[first.result] = unlocked
    return {
        value: frozenset(targets)
        for value, targets in sorted(support.items())
    }


def plan_bounded_beam(
    starting_values: tuple[int, ...] | list[int],
    targets: tuple[int, ...] | list[int],
    value_limit: int,
    *,
    max_intermediates: int = 8,
    max_depth: int = 4,
    beam_width: int = 32,
    max_expansions_per_state: int = 512,
) -> SharedIntermediatePlan:
    """Search a bounded beam of partial arithmetic DAGs.

    Each expansion adds exactly one legal operation. Non-target values consume
    the intermediate budget; target values are covered immediately. The search
    is deterministic and bounded by depth, beam width, and per-state expansion
    count. It is not complete and makes no optimality claim.
    """
    if type(value_limit) is not int or value_limit <= 0:
        raise ValueError("value_limit must be a positive integer")
    starts = tuple(starting_values)
    goals = tuple(targets)
    if not starts or any(type(v) is not int or v <= 0 or v > value_limit for v in starts):
        raise ValueError("starting values must be positive integers within value_limit")
    if any(type(v) is not int or v <= 0 or v > value_limit for v in goals):
        raise ValueError("targets must be positive integers within value_limit")
    if len(set(goals)) != len(goals):
        raise ValueError("targets must be unique")
    for name, value, minimum in (
        ("value_limit", value_limit, 1),
        ("beam_width", beam_width, 1),
        ("max_expansions_per_state", max_expansions_per_state, 1),
        ("max_depth", max_depth, 0),
        ("max_intermediates", max_intermediates, 0),
    ):
        if type(value) is not int or value < minimum:
            raise ValueError(f"{name} must be an integer >= {minimum}")

    initial = _State(
        operations=(),
        available=frozenset(starts),
        missing=frozenset(set(goals).difference(starts)),
        intermediates=0,
    )
    beam = (initial,)
    best = initial
    # Reverse target equations are joined only against a bounded forward
    # closure from the initial registers. This gives the beam a target-directed
    # candidate filter without making the search complete or unbounded.
    anchor_pool = _forward_anchor_pool(starts, value_limit, max_depth, 512)
    target_support = _multi_target_cone_support(
        initial.missing, anchor_pool, value_limit, max_depth, 1024
    )
    target_cone = frozenset(target_support)
    # A second, bounded look-ahead detects two-node shared subgraphs. Unlike
    # reverse-cone support, this explicitly asks whether a first intermediate
    # can lead to a second intermediate that jointly exposes several goals.
    subgraph_support = _shared_subgraph_support(
        starts, initial.missing, value_limit
    )
    seen = {_state_key(initial, starts)}

    for _depth in range(max_depth):
        expanded: list[_State] = []
        for state in beam:
            if not state.missing:
                return SharedIntermediatePlan(
                    state.operations, frozenset(goals), (), frozenset(starts)
                )
            recipes = [
                recipe for recipe in _pair_recipes(tuple(sorted(state.available)), value_limit)
                if recipe.result not in state.available and recipe.result in target_cone
            ]
            # A capped reverse cone can miss a useful branch. Retain a small,
            # deterministic direct-potential escape hatch rather than pruning
            # the entire state.
            if not recipes:
                fallback = [
                    recipe for recipe in _pair_recipes(tuple(sorted(state.available)), value_limit)
                    if recipe.result not in state.available
                ]
                fallback.sort(key=lambda recipe: (
                    -int(recipe.result in state.missing),
                    -_direct_yield(
                        _State(state.operations, state.available.union((recipe.result,)),
                               state.missing.difference((recipe.result,)), state.intermediates),
                        value_limit,
                    ),
                    _recipe_order(recipe),
                ))
                recipes = fallback[:16]

            # Prefer target-producing moves, then moves that expose more
            # missing targets immediately. Stable recipe order breaks ties.
            def recipe_rank(recipe):
                next_available = state.available.union((recipe.result,))
                probe = _State(
                    state.operations, frozenset(next_available),
                    state.missing.difference((recipe.result,)), state.intermediates,
                )
                # Once a promising first node is present, explicitly score
                # candidate bridge nodes by the number of its supported goals
                # that become reachable. This prevents the beam from retaining
                # the prefix while pruning the bridge needed to complete it.
                return (
                    int(recipe.result in state.missing),
                    _shared_completion_yield(
                        state, recipe.result, value_limit, subgraph_support
                    ),
                    _direct_yield(probe, value_limit),
                    len(target_support.get(recipe.result, ())),
                    len(subgraph_support.get(recipe.result, ())),
                    tuple(-part if isinstance(part, int) else part
                          for part in _recipe_order(recipe)[:2]),
                    _recipe_order(recipe),
                )

            recipes.sort(key=recipe_rank, reverse=True)
            recipes = recipes[:max_expansions_per_state]
            for recipe in recipes:
                is_target = recipe.result in state.missing
                if not is_target and state.intermediates >= max_intermediates:
                    continue
                operation = PlannedOperation(
                    recipe.left, recipe.operator, recipe.right,
                    recipe.result, is_target,
                )
                child = _State(
                    operations=state.operations + (operation,),
                    available=state.available.union((recipe.result,)),
                    missing=state.missing.difference((recipe.result,)),
                    intermediates=state.intermediates + int(not is_target),
                )
                key = _state_key(child, starts)
                if key in seen:
                    continue
                seen.add(key)
                expanded.append(child)

        if not expanded:
            break
        frontier = _pareto_by_coverage(expanded, starts)
        beam = tuple(sorted(
            frontier, key=lambda state: _rank(state, starts, value_limit, subgraph_support)
        )[:beam_width])
        if beam and _rank(beam[0], starts, value_limit, subgraph_support) < _rank(best, starts, value_limit, subgraph_support):
            best = beam[0]
        complete = [state for state in beam if not state.missing]
        if complete:
            winner = min(complete, key=lambda state: (
                len(state.operations), _peak(state, starts),
                tuple((op.result, op.operator, op.left, op.right) for op in state.operations),
            ))
            # A proposal is not trusted until the production scheduler has
            # allocated registers and replayed every instruction in the VM.
            schedule_value_dag(winner.operations, starts, value_limit)
            return SharedIntermediatePlan(
                winner.operations, frozenset(goals), (), frozenset(starts)
            )

    if best.operations:
        schedule_value_dag(best.operations, starts, value_limit)
    return SharedIntermediatePlan(
        operations=best.operations,
        covered_targets=frozenset(set(goals).difference(best.missing)),
        missing_targets=tuple(sorted(best.missing)),
        initial_values=frozenset(starts),
    )
