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


def _rank(state: _State, starts: tuple[int, ...], limit: int) -> tuple:
    # Coverage is primary. Direct one-step reachability is a useful potential
    # signal; cost and live pressure then control resource efficiency.
    return (
        len(state.missing),
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
                if recipe.result not in state.available
            ]

            # Prefer target-producing moves, then moves that expose more
            # missing targets immediately. Stable recipe order breaks ties.
            def recipe_rank(recipe):
                next_available = state.available.union((recipe.result,))
                probe = _State(
                    state.operations, frozenset(next_available),
                    state.missing.difference((recipe.result,)), state.intermediates,
                )
                return (
                    int(recipe.result in state.missing),
                    _direct_yield(probe, value_limit),
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
            frontier, key=lambda state: _rank(state, starts, value_limit)
        )[:beam_width])
        if beam and _rank(beam[0], starts, value_limit) < _rank(best, starts, value_limit):
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
