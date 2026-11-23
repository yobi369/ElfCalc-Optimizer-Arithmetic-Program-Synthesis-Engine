"""End-to-end shared-intermediate solver built from the value-DAG planner."""
from __future__ import annotations

from .puzzle import Puzzle
from .register_schedule import schedule_value_dag
from .shared_intermediate import plan_shared_intermediates
from .validation import validate_program
from .machine import Instruction


def solve_shared_intermediate(puzzle: Puzzle) -> tuple[Instruction, ...]:
    """Plan, schedule, and VM-validate a shared-intermediate candidate.

    This constructor is intentionally independent of the main solver portfolio
    until benchmark evidence demonstrates that it improves full-dataset score.
    """
    plan = plan_shared_intermediates(
        puzzle.starting_values, puzzle.targets, puzzle.value_limit
    )
    if plan.missing_targets:
        raise ValueError(f"shared-intermediate planner missed {plan.missing_targets}")

    program = schedule_value_dag(
        plan.operations, puzzle.starting_values, puzzle.value_limit
    )
    result = validate_program(puzzle, program)
    if not result.complete:
        raise ValueError(result.error or f"candidate misses {result.missing_targets}")
    if not plan.covered_targets.issubset(result.covered_targets):
        raise ValueError("VM replay disagrees with value-DAG target coverage")
    return program
