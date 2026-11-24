"""Compare deterministic frontier-cache replacement policies on synthetic workloads.

The policies share the same entry capacity and exact recipe values. This isolates
replacement behavior from search quality; it does not model byte-level memory.
"""
from collections import OrderedDict
from time import perf_counter
from unittest import TestCase
from unittest.mock import patch

import elfcalc.bounded_search as search
from elfcalc.puzzle import Puzzle
from elfcalc.register_schedule import estimate_peak_live_values, schedule_value_dag
from elfcalc.validation import validate_program


FIXTURES = (
    ("overlapping_target_cones", (2, 3, 4, 5, 6), (12, 18, 20, 24, 30, 36, 40, 45), 120),
    ("multi_route_shared_values", (2, 3, 4, 6), (12, 18, 24, 36, 48, 54, 72, 90), 120),
    ("dense_factorial_branching", (2, 3, 4, 5, 7), (14, 20, 28, 35, 40, 42, 56, 70), 140),
)
POLICIES = ("lru", "fifo", "lfu")
CAPACITIES = (64, 128, 256)


class DeterministicFrontierCache:
    def __init__(self, capacity, policy, generator):
        self.capacity = capacity
        self.policy = policy
        self.generator = generator
        self.entries = OrderedDict()
        self.frequency = {}
        self.hits = 0
        self.misses = 0
        self.generated = 0
        self.evictions = 0

    def __call__(self, values, limit):
        key = (tuple(values), limit)
        if key in self.entries:
            self.hits += 1
            if self.policy == "lru":
                self.entries.move_to_end(key)
            if self.policy == "lfu":
                self.frequency[key] += 1
            return self.entries[key]

        self.misses += 1
        result = tuple(self.generator(values, limit))
        self.generated += 1
        if self.capacity == 0:
            return result

        if len(self.entries) >= self.capacity:
            if self.policy == "lfu":
                victim = min(self.entries, key=lambda item: (self.frequency[item], list(self.entries).index(item)))
            else:
                victim = next(iter(self.entries))
            del self.entries[victim]
            self.frequency.pop(victim, None)
            self.evictions += 1

        self.entries[key] = result
        self.frequency[key] = 1
        return result


class FrontierCachePolicyTests(TestCase):
    def test_replacement_policy_tournament_preserves_quality(self):
        for name, starts, targets, limit in FIXTURES:
            baseline = None
            rows = []
            for capacity in CAPACITIES:
                for policy in POLICIES:
                    native_generator = search._pair_recipes
                    cache = DeterministicFrontierCache(capacity, policy, native_generator)
                    started = perf_counter()
                    with patch.object(search, "_cached_pair_recipes", cache):
                        plan = search.plan_bounded_beam(
                            starts, targets, limit,
                            max_intermediates=2,
                            max_depth=3,
                            beam_width=8,
                            max_expansions_per_state=16,
                            enable_complete_witnesses=False,
                            enable_partial_motifs=False,
                        )
                    elapsed = perf_counter() - started
                    allocation = schedule_value_dag(plan.operations, starts, limit)
                    covered = tuple(sorted(plan.covered_targets))
                    replay = validate_program(
                        Puzzle(name, starts, covered, limit), allocation
                    )
                    self.assertTrue(replay.complete, replay.error)
                    quality = (
                        covered,
                        len(plan.operations),
                        estimate_peak_live_values(plan.operations, starts),
                        tuple(sorted(plan.missing_targets)),
                    )
                    if baseline is None:
                        baseline = quality
                    else:
                        self.assertEqual(quality, baseline, (name, capacity, policy))
                    rows.append({
                        "capacity": capacity,
                        "policy": policy,
                        "generated": cache.generated,
                        "hits": cache.hits,
                        "misses": cache.misses,
                        "size": len(cache.entries),
                        "evictions": cache.evictions,
                        "elapsed_seconds": round(elapsed, 6),
                        "quality": quality,
                    })
            print("FRONTIER_CACHE_POLICY", name, rows)
