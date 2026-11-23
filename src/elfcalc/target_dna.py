"""Exact, bounded feature extraction for Target DNA arithmetic discovery.

This module is a search aid, not a solver or proof of program validity. Every
relation is checked with Python integers and puzzle value limits.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import gcd


@dataclass(frozen=True, slots=True)
class TargetFingerprint:
    value: int
    bit_length: int
    decimal_magnitude: int
    residues: tuple[int, ...]
    parity: int


@dataclass(frozen=True, slots=True)
class ArithmeticRelation:
    left: int
    operator: str
    right: int
    result: int


@dataclass(frozen=True, slots=True)
class TargetDNA:
    fingerprints: tuple[TargetFingerprint, ...]
    candidate_intermediates: tuple[int, ...]
    relations: tuple[ArithmeticRelation, ...]


def fingerprint(value: int, moduli: tuple[int, ...] = (3, 5, 7, 11, 13, 17, 19)) -> TargetFingerprint:
    """Build inexpensive deterministic features; does not require factorization."""
    if type(value) is not int or value <= 0:
        raise ValueError("Target DNA accepts positive integers only")
    if any(type(m) is not int or m <= 1 for m in moduli):
        raise ValueError("moduli must be integers greater than one")
    return TargetFingerprint(
        value=value,
        bit_length=value.bit_length(),
        decimal_magnitude=len(str(value)) - 1,
        residues=tuple(value % m for m in moduli),
        parity=value & 1,
    )


def _candidate_intermediates(values: tuple[int, ...], value_limit: int) -> tuple[int, ...]:
    found: set[int] = set()
    for i, left in enumerate(values):
        for right in values[i + 1:]:
            common = gcd(left, right)
            if 1 < common < value_limit and common not in values:
                found.add(common)

            difference = abs(left - right)
            if 0 < difference <= value_limit and difference not in values:
                found.add(difference)

            if common > 1:
                for quotient in (left // common, right // common):
                    if 1 < quotient <= value_limit and quotient not in values:
                        found.add(quotient)

            if left % right == 0:
                quotient = left // right
                if 1 < quotient <= value_limit and quotient not in values:
                    found.add(quotient)
            if right % left == 0:
                quotient = right // left
                if 1 < quotient <= value_limit and quotient not in values:
                    found.add(quotient)

    return tuple(sorted(found))


def _relations(values: tuple[int, ...], value_limit: int) -> tuple[ArithmeticRelation, ...]:
    """Enumerate exact pairwise operations whose results are in the known universe."""
    universe = set(values)
    edges: set[ArithmeticRelation] = set()
    for i, left in enumerate(values):
        for right in values[i:]:
            operations = (
                ("+", left + right),
                ("*", left * right),
            )
            for operator, result in operations:
                if result <= value_limit and result in universe:
                    edges.add(ArithmeticRelation(left, operator, right, result))

            if left > right:
                difference = left - right
                if difference in universe:
                    edges.add(ArithmeticRelation(left, "-", right, difference))
            elif right > left:
                difference = right - left
                if difference in universe:
                    edges.add(ArithmeticRelation(right, "-", left, difference))

            if right != 0 and left % right == 0:
                quotient = left // right
                if quotient in universe:
                    edges.add(ArithmeticRelation(left, "/", right, quotient))
            if left != 0 and right % left == 0:
                quotient = right // left
                if quotient in universe:
                    edges.add(ArithmeticRelation(right, "/", left, quotient))

    return tuple(sorted(edges, key=lambda e: (e.result, e.operator, e.left, e.right)))


def analyze_targets(
    starting_values: tuple[int, ...] | list[int],
    targets: tuple[int, ...] | list[int],
    value_limit: int,
) -> TargetDNA:
    """Create a deterministic first-pass target fingerprint and relation map.

    The candidate frontier is intentionally bounded to pairwise gcd,
    difference, and exact quotient features. It does not claim these values
    are cheap or useful; downstream search must price their construction.
    """
    if type(value_limit) is not int or value_limit <= 0:
        raise ValueError("value_limit must be a positive integer")
    starts = tuple(starting_values)
    goals = tuple(targets)
    if any(type(v) is not int or v <= 0 for v in starts + goals):
        raise ValueError("starting values and targets must be positive integers")
    if any(v > value_limit for v in starts + goals):
        raise ValueError("starting value or target exceeds value_limit")

    universe = tuple(sorted(set(starts).union(goals)))
    candidates = _candidate_intermediates(universe, value_limit)
    expanded = tuple(sorted(set(universe).union(candidates)))
    return TargetDNA(
        fingerprints=tuple(fingerprint(v) for v in universe),
        candidate_intermediates=candidates,
        relations=_relations(expanded, value_limit),
    )
