# ELF-100K: Research Program for a 100,000-Instructions Candidate

**Status:** Research charter / hypotheses, not an implemented optimizer  
**Date:** 2026-11-23  
**Verified incumbent:** 130,974 instructions  
**Aspirational target:** 100,000 instructions  
**Submission status:** No Kaggle submission authorized or made

## 1. Research thesis

We will stop treating the task solely as 1,000 independent program-shortening problems. We will investigate whether the puzzle collection has a smaller latent computational structure: recurring transformations, algebraic equivalence classes, reusable intermediate computations, and complementary solver strengths.

The target requires a reduction of 30,974 instructions (about 23.65%) from the verified incumbent. This is a research objective, not a forecast or promise. Every claimed improvement must be measured by the official evaluator on the pinned puzzle set.

## 2. Non-negotiable correctness and evidence rules

1. Pin the official puzzle file and record its SHA-256 before each experiment.
2. Treat the official evaluator/referee as the authority for instruction semantics, validity, and score.
3. Never assume that recursion, helper sharing, common-subexpression elimination, or a compact source representation reduces the scored instruction count. Establish this from evaluator semantics first.
4. Preserve exact source, version, dataset, license, and derivation lineage for every candidate row.
5. Do not execute untrusted Kaggle notebooks merely to inspect them. Perform static source and dependency review first.
6. A candidate is promotable only after serialization and exact replay of all 1,000 scored puzzles, with no missing, extra, invalid, or altered rows.
7. Keep local verified score, external public candidate score, and official leaderboard rank distinct.
8. No Kaggle submission without explicit user approval.

## 3. Five research laboratories

### Lab A — Cross-puzzle structure discovery

**Question:** Are the 1,000 puzzles instances of a much smaller number of computational families?

Build per-puzzle fingerprints from information permitted by the task and evaluator: input/output structure, target characteristics, current program operation histograms, dependency-graph motifs, repeated subexpressions, and proven algebraic invariants.

Cluster puzzles using multiple representations rather than a single raw numeric distance. Test whether clusters predict useful solver choice or reusable transformations on held-out puzzles.

**Success criterion:** A discovered family or feature predicts a measurable reduction in exact instruction cost on held-out puzzles, not merely attractive visual clusters.

### Lab B — Algebraic compression and equivalence discovery

**Question:** Can existing programs be transformed into shorter equivalent programs without changing their behavior under the evaluator?

Construct a rewrite system from the exact instruction semantics. Candidate transformations include constant folding, identity elimination, operation composition, inverse cancellation, common-subexpression factoring, and domain-specific identities—but only where each identity is valid for the evaluator's integer ranges, overflow behavior, division/modulo rules, and edge cases.

For every rewrite:
- State preconditions explicitly.
- Prove equivalence algebraically or exhaustively over a formally bounded domain.
- Preserve a machine-checkable transformation trace.
- Measure instruction-count change after compiling/evaluating with the official rules.

**Success criterion:** Rewrites produce shorter, exact programs on a held-out set, with no semantic counterexamples.

### Lab C — Reverse synthesis

**Question:** Can target-directed reasoning reduce the search space?

Start from required outputs and derive feasible predecessor states under each instruction. Use interval, congruence, divisibility, and range constraints to prune impossible predecessors. Combine backward frontiers with forward reachable-state summaries at a meet-in-the-middle boundary.

Avoid uncontrolled state explosion by canonicalizing equivalent states and recording dominance only when that is sound.

**Success criterion:** Better best-known instruction costs per unit compute than the existing forward or backward baselines on matched puzzles.

### Lab D — Evolutionary computational ecology

**Question:** Can distinct program families exchange useful structures and escape local minima?

Maintain a population of valid programs and structural fragments. Apply semantics-preserving mutations, recombination, instruction substitutions, and targeted resynthesis. Use exact cost and validity as selection criteria; heuristic scores may guide exploration but cannot certify candidates.

Prevent genetic drift and duplicate work with canonical program hashes, novelty measures, diversity constraints, and deterministic seeds.

**Success criterion:** Reproducible improvements on a fixed benchmark set beyond existing search baselines, with compute budgets reported.

### Lab E — Global portfolio optimization

**Question:** Can the best collection be assembled from complementary candidate sources and solvers?

For each puzzle, maintain a candidate bank containing the incumbent and every independently verified candidate. Compute the per-puzzle lower envelope as an exploratory bound. Then build the best feasible portfolio from candidates whose provenance and licenses have been cleared.

If the official scoring model permits cross-program sharing or other global effects, model those effects explicitly; otherwise do not assume that source-level reuse changes the score.

**Success criterion:** A fully provenance-cleared 1,000-row portfolio with a strictly lower exact referee score than the incumbent.

## 4. Experiment protocol

Each experiment must record:

- Experiment ID, hypothesis, author/source, commit, and deterministic seed.
- Pinned puzzle-file hash and evaluator version/hash.
- Candidate input hashes and all upstream source/dataset versions.
- Compute budget, runtime, and search parameters.
- Number of puzzles attempted, solved, invalid, and improved.
- Total exact instruction score and per-puzzle deltas.
- Serialized output hash and exact replay report.
- License/provenance status and unresolved risks.

Use a fixed development/validation split for method selection. Keep a final untouched evaluation set to reduce overfitting to the known puzzle collection. All final candidate rows must nevertheless pass the full official 1,000-puzzle replay.

## 5. Milestones (targets, not predictions)

| Milestone | Required evidence |
|---|---|
| 130,974 → 125,000 | Full exact replay and auditable source lineage |
| 125,000 → 120,000 | At least one distinct method contributes verified gains |
| 120,000 → 115,000 | Cross-puzzle structure or algebraic rewrite gains generalize |
| 115,000 → 110,000 | Multiple independent methods combine without regressions |
| 110,000 → 105,000 | Broad gains survive held-out evaluation |
| 105,000 → 100,000 | Fully audited, independently replayed 100K candidate |

Milestones are checkpoints for deciding whether to continue, pivot, or retire a hypothesis. They are not assumed additive contributions from the five labs.

## 6. Immediate execution order

1. Finish inspecting the latest authenticated Kaggle source/output archive and its pull-status logs.
2. Pin and document the exact evaluator semantics, including arithmetic edge cases and what the scorer counts.
3. Reproduce the 130,974 incumbent from its frozen CSV and pinned puzzle file.
4. Complete static provenance/license audits for the stronger public candidates (Ishan, Ozertuu, Muhakabartay, Avazaku).
5. Build a per-puzzle candidate matrix and source-attribution map; do not merge uncleared rows into a distributable candidate.
6. Establish matched baselines for each lab before running new search.
7. Implement the smallest falsifiable experiment first: puzzle fingerprints plus held-out solver/candidate performance analysis.
8. Promote only exact, licensed, fully replayed improvements.

## 7. Current known position

The project record reports a 130,974 exact-replay incumbent. Previously replayed external candidates include Ishan Karnick (130,859), Ozertuu (130,914), and Muhakabartay (130,939), each with 1,000 valid rows. These are external candidate results, not yet a provenance-cleared replacement portfolio.

The latest authenticated source bundle was successfully created by GitHub Actions run 45119872278 (artifact 14793690376; SHA-256 `e683a582c69beeb4e1f3df4405d8b30d5fbb8f7ed6b372dbc8bdab15a994a33e`). Its contents still require inspection and replay. A data-analysis availability limit currently prevents that archive inspection; no substitute execution path should be used to bypass that limit.

## 8. Decision principle

We are not optimizing for an impressive-looking notebook, a speculative score, or a leaderboard claim. We are optimizing for the shortest valid, reproducible, provenance-cleared candidate that the official referee accepts. The 100K target is the north star; evidence decides every step.
