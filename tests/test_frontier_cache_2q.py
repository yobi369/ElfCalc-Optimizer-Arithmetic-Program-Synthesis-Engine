"""Compare a scan-resistant 2Q frontier cache with LRU and FIFO."""
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
CAPACITIES = (64, 128, 256)


class TwoQFrontierCache:
    """Probationary FIFO plus protected LRU; only a second hit earns protection."""

    def __init__(self, capacity, generator):
        self.capacity = capacity
        self.probation_limit = max(1, capacity // 4)
        self.generator = generator
        self.probation = OrderedDict()
        self.protected = OrderedDict()
        self.hits = self.misses = self.generated = self.evictions = self.promotions = 0

    def __call__(self, values, limit):
        key = (tuple(values), limit)
        if key in self.protected:
            self.hits += 1
            self.protected.move_to_end(key)
            return self.protected[key]
        if key in self.probation:
            self.hits += 1
            self.promotions += 1
            value = self.probation.pop(key)
            self.protected[key] = value
            self._trim()
            return value
        self.misses += 1
        value = tuple(self.generator(values, limit))
        self.generated += 1
        if self.capacity:
            self.probation[key] = value
            self._trim()
        return value

    def _trim(self):
        while len(self.probation) > self.probation_limit:
            self.probation.popitem(last=False)
            self.evictions += 1
        while len(self.probation) + len(self.protected) > self.capacity:
            if self.probation:
                self.probation.popitem(last=False)
            else:
                self.protected.popitem(last=False)
            self.evictions += 1


class LRUFrontierCache:
    def __init__(self, capacity, generator):
        self.capacity, self.generator = capacity, generator
        self.entries = OrderedDict()
        self.hits = self.misses = self.generated = self.evictions = 0

    def __call__(self, values, limit):
        key = (tuple(values), limit)
        if key in self.entries:
            self.hits += 1
            self.entries.move_to_end(key)
            return self.entries[key]
        self.misses += 1
        value = tuple(self.generator(values, limit))
        self.generated += 1
        if self.capacity:
            if len(self.entries) >= self.capacity:
                self.entries.popitem(last=False)
                self.evictions += 1
            self.entries[key] = value
        return value


class FIFOFrontierCache(LRUFrontierCache):
    def __call__(self, values, limit):
        key = (tuple(values), limit)
        if key in self.entries:
            self.hits += 1
            return self.entries[key]
        self.misses += 1
        value = tuple(self.generator(values, limit))
        self.generated += 1
        if self.capacity:
            if len(self.entries) >= self.capacity:
                self.entries.popitem(last=False)
                self.evictions += 1
            self.entries[key] = value
        return value


class FrontierCache2QTests(TestCase):
    def test_2q_scan_resistance_and_planner_quality(self):
        for name, starts, targets, limit in FIXTURES:
            baseline, rows = None, []
            for capacity in CAPACITIES:
                for policy_name, cache_type in (("lru", LRUFrontierCache), ("fifo", FIFOFrontierCache), ("2q", TwoQFrontierCache)):
                    cache = cache_type(capacity, search._pair_recipes)
                    started = perf_counter()
                    with patch.object(search, "_cached_pair_recipes", cache):
                        plan = search.plan_bounded_beam(
                            starts, targets, limit, max_intermediates=2, max_depth=3,
                            beam_width=8, max_expansions_per_state=16,
                            enable_complete_witnesses=False, enable_partial_motifs=False,
                        )
                    elapsed = perf_counter() - started
                    allocation = schedule_value_dag(plan.operations, starts, limit)
                    covered = tuple(sorted(plan.covered_targets))
                    replay = validate_program(Puzzle(name, starts, covered, limit), allocation)
                    self.assertTrue(replay.complete, replay.error)
                    quality = (covered, len(plan.operations), estimate_peak_live_values(plan.operations, starts), tuple(sorted(plan.missing_targets)))
                    if baseline is None:
                        baseline = quality
                    else:
                        self.assertEqual(quality, baseline, (name, capacity, policy_name))
                    rows.append({
                        "capacity": capacity, "policy": policy_name, "generated": cache.generated,
                        "hits": cache.hits, "misses": cache.misses,
                        "size": len(cache.probation) + len(cache.protected) if isinstance(cache, TwoQFrontierCache) else len(cache.entries),
                        "evictions": cache.evictions, "promotions": getattr(cache, "promotions", 0),
                        "elapsed_seconds": round(elapsed, 6), "quality": quality,
                    })
            print("FRONTIER_CACHE_2Q", name, rows)

    def test_2q_rejects_one_pass_scan_without_evicting_hot_entries(self):
        hot = tuple(("hot", index) for index in range(4))
        scan = tuple(("scan", index) for index in range(40))

        def generator(values, limit):
            return ((values, "+", values, values),)

        lru, twoq = LRUFrontierCache(16, generator), TwoQFrontierCache(16, generator)
        for key in hot:
            lru(key, 100)
            twoq(key, 100)
        for key in hot:
            lru(key, 100)
            twoq(key, 100)
        for key in scan:
            lru(key, 100)
            twoq(key, 100)
        lru_before, twoq_before = lru.generated, twoq.generated
        for key in hot:
            lru(key, 100)
            twoq(key, 100)
        self.assertEqual(lru.generated - lru_before, len(hot))
        self.assertEqual(twoq.generated - twoq_before, 0)
        self.assertEqual(twoq.promotions, len(hot))
