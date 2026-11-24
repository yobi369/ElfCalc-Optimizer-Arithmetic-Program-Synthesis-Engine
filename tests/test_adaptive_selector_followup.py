"""Follow-up: do not let an early complete beam probe suppress a stronger motif probe."""
from time import perf_counter
from unittest import TestCase
from unittest.mock import patch

import elfcalc.bounded_search as search
from elfcalc.puzzle import Puzzle
from elfcalc.register_schedule import estimate_peak_live_values, schedule_value_dag
from elfcalc.validation import validate_program

FIXTURES = (
    ("shared_factor_chain", (2, 3, 5), (50, 75), 1000, 2, 4),
    ("shared_bridge", (2, 3), (12, 35), 1000, 3, 5),
    ("multi_family", (2, 3, 5), (10, 12, 15, 18), 1000, 3, 5),
)
STATE_BUDGET = 512
PROBE_STATES = 64
RECIPE_BUDGET = 32


class AdaptiveSelectorFollowupTests(TestCase):
    def _measure(self, callback):
        original = search._cached_pair_recipes
        work = {"frontier_requests": 0, "candidate_recipes": 0}

        def counted(values, limit):
            recipes = original(values, limit)
            work["frontier_requests"] += 1
            work["candidate_recipes"] += len(recipes)
            return recipes

        started = perf_counter()
        with patch.object(search, "_cached_pair_recipes", counted):
            result = callback()
        work["elapsed_seconds"] = round(perf_counter() - started, 6)
        return result, work

    def _replay(self, name, starts, targets, limit, operations):
        try:
            program = schedule_value_dag(operations, starts, limit)
        except (ValueError, RuntimeError):
            return None
        result = validate_program(
            Puzzle(name, starts, targets, limit), program
        )
        return operations if result.complete else None

    def test_partial_motif_signal_can_override_complete_but_longer_beam_probe(self):
        rows = []
        for name, starts, targets, limit, intermediates, depth in FIXTURES:
            beam_probe, beam_work = self._measure(lambda: search.plan_bounded_beam(
                starts, targets, limit,
                max_intermediates=intermediates, max_depth=depth,
                beam_width=8, max_expansions_per_state=RECIPE_BUDGET,
                max_total_state_expansions=PROBE_STATES,
                enable_complete_witnesses=False, enable_partial_motifs=False,
                enable_target_cone_guidance=False,
                enable_shared_subgraph_guidance=False,
            ))
            motif_probe, motif_work = self._measure(lambda: search._shared_subgraph_witnesses(
                starts, frozenset(targets), limit,
                max_intermediates=intermediates,
                max_recipes_per_state=RECIPE_BUDGET,
                max_states=PROBE_STATES, max_witnesses=64,
            ))

            beam_candidate = None
            if not beam_probe.missing_targets:
                beam_candidate = self._replay(
                    name + "_beam_probe", starts, targets, limit,
                    beam_probe.operations,
                )

            motif_candidates = []
            motif_coverage = 0
            for ops in motif_probe:
                values = set(starts).union(op.result for op in ops)
                motif_coverage = max(
                    motif_coverage, len(set(targets).intersection(values))
                )
                if len(ops) <= depth:
                    candidate = self._replay(
                        name + "_motif_probe", starts, targets, limit, ops
                    )
                    if candidate is not None:
                        motif_candidates.append(candidate)

            best_motif = min(
                motif_candidates,
                key=lambda ops: (
                    len(ops), estimate_peak_live_values(ops, starts)
                ),
            ) if motif_candidates else None

            beam_score = (
                len(beam_probe.covered_targets)
                / max(1, beam_work["candidate_recipes"])
            )
            motif_score = (
                motif_coverage / max(1, motif_work["candidate_recipes"])
            )
            if beam_candidate is not None and best_motif is not None:
                selected = min(
                    (("beam", beam_candidate), ("motif", best_motif)),
                    key=lambda item: (
                        len(item[1]),
                        estimate_peak_live_values(item[1], starts),
                        item[0],
                    ),
                )
                strategy, final_ops = selected
                continuation_work = {"candidate_recipes": 0}
            else:
                strategy = "motif" if motif_score > beam_score else "beam"
                final_ops = ()
                continuation_work = {"candidate_recipes": 0}
                if strategy == "beam" and beam_candidate is not None:
                    final_ops = beam_candidate
                elif strategy == "motif" and best_motif is not None:
                    final_ops = best_motif
                elif strategy == "beam":
                    continuation, continuation_work = self._measure(
                        lambda: search.plan_bounded_beam(
                            starts, targets, limit,
                            max_intermediates=intermediates, max_depth=depth,
                            beam_width=8, max_expansions_per_state=RECIPE_BUDGET,
                            max_total_state_expansions=STATE_BUDGET-PROBE_STATES,
                            enable_complete_witnesses=False,
                            enable_partial_motifs=False,
                            enable_target_cone_guidance=False,
                            enable_shared_subgraph_guidance=False,
                        )
                    )
                    final_ops = continuation.operations
                else:
                    continuation, continuation_work = self._measure(
                        lambda: search._shared_subgraph_witnesses(
                            starts, frozenset(targets), limit,
                            max_intermediates=intermediates,
                            max_recipes_per_state=RECIPE_BUDGET,
                            max_states=STATE_BUDGET-PROBE_STATES,
                            max_witnesses=64,
                        )
                    )
                    complete = [
                        ops for ops in continuation
                        if len(ops) <= depth
                        and self._replay(
                            name + "_motif_continuation", starts, targets,
                            limit, ops,
                        ) is not None
                    ]
                    final_ops = min(
                        complete,
                        key=lambda ops: (
                            len(ops), estimate_peak_live_values(ops, starts)
                        ),
                    ) if complete else ()
                    # A motif continuation can exhaust its witness frontier
                    # without a complete program. Fall back to beam rather
                    # than failing the whole adaptive portfolio.
                    if not final_ops:
                        fallback, fallback_work = self._measure(
                            lambda: search.plan_bounded_beam(
                                starts, targets, limit,
                                max_intermediates=intermediates, max_depth=depth,
                                beam_width=8, max_expansions_per_state=RECIPE_BUDGET,
                                max_total_state_expansions=STATE_BUDGET-PROBE_STATES,
                                enable_complete_witnesses=False,
                                enable_partial_motifs=False,
                                enable_target_cone_guidance=False,
                                enable_shared_subgraph_guidance=False,
                            )
                        )
                        final_ops = fallback.operations
                        continuation_work = {
                            "candidate_recipes": (
                                continuation_work["candidate_recipes"]
                                + fallback_work["candidate_recipes"]
                            )
                        }

            replayed = self._replay(
                name + "_adaptive_followup", starts, targets, limit, final_ops
            ) if final_ops else None
            rows.append({
                "fixture": name,
                "selected": strategy,
                "complete": replayed is not None,
                "instructions": len(replayed) if replayed is not None else None,
                "probe_beam_recipes": beam_work["candidate_recipes"],
                "probe_motif_recipes": motif_work["candidate_recipes"],
                "continuation_recipes": continuation_work["candidate_recipes"],
            })

        print("ADAPTIVE_SELECTOR_FOLLOWUP")
        for row in rows:
            print(row)
        self.assertEqual(len(rows), len(FIXTURES))
        self.assertTrue(all(row["complete"] for row in rows))
