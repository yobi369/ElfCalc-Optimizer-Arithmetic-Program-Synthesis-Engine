# ElfCalc Optimizer — Arithmetic Program Synthesis Engine

An independent, reproducible solver for Kaggle's **Santa 2026 — The Elf Calculator** competition.

The objective is to synthesize short arithmetic programs that produce every required target using only exact `+`, `-`, `*`, and `/` operations, while respecting the competition's register and value constraints.

## Project status

**Exact validator, reproducible baseline audit, and constructive solver implemented.** The solver searches a bounded shared-intermediate DAG pass, every feasible positional base from 2 through 32 (including shared-prefix orderings), precomputed signed-window widths 3 through 8, and streaming signed-window widths 9 through 14. Every candidate is checked with independent exact-arithmetic replay. The shared-DAG pass is a heuristic experiment; its full-dataset impact is not yet measured.

A full local run on the supplied scored dataset produced a 1,000-program candidate with **275,767 total instructions**. All 1,000 programs replayed successfully and covered every target; the longest program has 548 instructions. The official sample baseline has 1,490,379 instructions, so this candidate reduces the local instruction total by 1,214,612 (81.50%). On the 200 labeled practice puzzles, the same portfolio produced 55,946 instructions. These are locally measured candidate results, **not Kaggle leaderboard scores** and not claims of global optimality. The CSV candidate and its verification report are generated locally and are not committed with competition data.

## Restore competition datasets

Raw competition data is deliberately excluded from this public repository. Read [DATASETS.md](DATASETS.md) for the privacy rationale, current dataset fingerprints, and one-command retrieval instructions. After configuring Kaggle authentication, run:

```bash
bash scripts/fetch_kaggle_data.sh
```

The script restores the official puzzle and sample-submission files into the ignored local `data/` directory, so you do not need to attach those files to every coding session.

## Competitive reference checkpoint (22 November 2026)

A public Apache-2.0 reference checkpoint is available at **132,515 total instructions** across all 1,000 scored puzzles. It was previously accepted by Kaggle as submission 58675401. We retrieved the exact upstream artifact, verified both upstream SHA-256 fingerprints, and independently replayed all 1,000 programs against the supplied `puzzles.csv` in this project:

- Exact local replay: **1,000/1,000 valid and complete**, zero missing targets.
- Total: **132,515** instructions; median 118; minimum 2; maximum 277.
- CSV SHA-256: `d984166fee5681afc84382afda0d0eaf009922d88c192a9b8fa5dbc9dbbdc5d3`.
- Provenance and license: [THIRD_PARTY.md](THIRD_PARTY.md), [original upstream notice](research/upstream/132515-NOTICE.md), and [Apache-2.0](licenses/Apache-2.0.txt).

**Attribution:** this is an inherited public-reference merge, not a score independently achieved by this repository. Preserve all upstream credits. Our earlier independent constructive candidate scored 275,767; it remains a useful reproducible baseline for research, but it is not the strongest available candidate. Do not claim 132,515 as an original algorithmic result.

Submission and restoration steps are documented in [SUBMISSION.md](SUBMISSION.md).

The workflow [fetch-public-frontier.yml](.github/workflows/fetch-public-frontier.yml) retrieves the pinned upstream checkpoint, verifies its compressed and uncompressed hashes, and publishes a temporary GitHub Actions artifact. The raw Kaggle competition CSVs remain excluded from this public repository.

The current public standings snapshot checked on 22 November listed leading scores near 126,659. The 132,515 checkpoint is therefore a strong validated starting point, not a claim of first place. Future improvements must be measured per puzzle against this frozen baseline and independently replayed before replacing it.

The current dataset-level score floor and hardest-puzzle triage are documented in [the score-landscape report](research/score-landscape-2026-11-22.md). Reproduce the replay audit and per-puzzle breakdown with [analyze_score_landscape.py](scripts/analyze_score_landscape.py).

The latest clean local portfolio is **131,052 instructions**, assembled from the attributed Juan-Severiano 132,515 checkpoint and Ishan Karnick's Apache-2.0 frontier dataset v18. All 1,000 programs pass exact replay. See [the portfolio report](research/portfolio-131052.md), [source selection summary](research/portfolio-131052-sources.csv), and [reproducible merge script](scripts/merge_attributed_frontiers.py). This is a public-reference merge, not an original solver score or an official Kaggle submission.

The latest local attributed per-puzzle portfolio is **132,428 instructions**, independently replayed on all 1,000 puzzles. It is a minimum merge of the public 132,515 and 132,477 references, not an original solver score. See [portfolio report](research/portfolio-132428.md), [eight selected rows](research/portfolio-132428-improvements.csv), and preserved upstream notices under `research/upstream/`.

## Reproduce the baseline audit

Place the official files in `data/` (the directory is git-ignored), then run:

```bash
python scripts/audit_baseline.py
```

Or supply explicit paths:

```bash
python scripts/audit_baseline.py --puzzles data/puzzles.csv --submission data/sample_submission.csv
```

The command checks that puzzle and submission IDs match, replays every instruction under the exact machine rules, and reports validity, target completeness, and instruction-count statistics. It exits with status 0 only when every program is valid and complete; it exits 1 for invalid/incomplete programs and 2 for input/schema errors.

## Generate a constructive candidate

Run the independent solver against the scored puzzles. The sample submission is used as a per-puzzle fallback, so the output will never be longer than the supplied fallback for a puzzle where the constructor succeeds:

```bash
python scripts/solve_constructive.py --puzzles data/puzzles.csv --fallback data/sample_submission.csv --output outputs/constructive.csv
python scripts/audit_baseline.py --puzzles data/puzzles.csv --submission outputs/constructive.csv
```

To experiment on the labeled practice set without a scored-puzzle fallback:

```bash
python scripts/solve_constructive.py --puzzles data/practice_puzzles.csv --fallback "" --output outputs/practice-constructive.csv --report outputs/practice-constructive-report.json
python scripts/audit_baseline.py --puzzles data/practice_puzzles.csv --submission outputs/practice-constructive.csv
```

The constructor portfolio compares a bounded shared-intermediate DAG pass, all feasible positive positional bases from 2 through 32 (with ordinary and shared-prefix target orderings), precomputed signed-window widths 3 through 8, and streaming signed-window widths 9 through 14. Wider windows synthesize digit constants lazily to avoid reserving a large register table. It uses exact integers, bounded intermediate values, direct target closure, difference/factor anchors, and a 48-register allocator. The next engineering stage is to improve shared-intermediate synthesis and optimize the weakest cases.


## Benchmark shared-intermediate DAG search

The DAG experiment is independently ablatable from the rest of the solver portfolio. Run it on practice data first:

```bash
python scripts/benchmark_shared_dag.py --puzzles data/practice_puzzles.csv --output outputs/shared-dag-practice.json
```

Then run the same comparison on the scored dataset:

```bash
python scripts/benchmark_shared_dag.py --puzzles data/puzzles.csv --output outputs/shared-dag-scored.json
```

The report compares the complete constructive portfolio with and without the DAG pass, records per-puzzle instruction counts and the dataset SHA-256, and independently replays both candidates. A DAG pass is retained only if it yields measurable aggregate improvement without validity regressions.

## Official constraints enforced

- 48 registers, indexed 0 through 47.
- At most 4,096 instructions per puzzle program.
- At most 131,072 UTF-8 bytes per program cell.
- Positive integer register values no greater than the puzzle's `value_limit`; puzzle limits are at most `10^18`.
- Exact division only; all source registers must be defined.
- Both source values are read before the destination register is overwritten.
- A target remains covered once it has appeared, even if its register is later overwritten.
- Submission CSV must contain exactly `id,program` in that order, with each puzzle ID exactly once.

## Engineering principles

- Exact integer arithmetic only; never use floating point for validation.
- Validate every candidate by replaying it from the original initial state.
- Keep solver heuristics separate from the trusted interpreter.
- Record dataset hashes, solver version, per-puzzle instruction counts, and reproducible experiment settings.
- Never report a score or leaderboard result that has not been confirmed by Kaggle.

## Architecture

| Component | Responsibility |
| --- | --- |
| `src/elfcalc/machine.py` | Deterministic exact-arithmetic virtual machine and shared limits |
| `src/elfcalc/puzzle.py` | Puzzle model and official puzzle CSV parsing |
| `src/elfcalc/validation.py` | Independent replay validation and official instruction-row conversion |
| `src/elfcalc/submission.py` | Official submission CSV loading and writing |
| `src/elfcalc/audit.py` | Reproducible full-submission replay and aggregate audit |
| `src/elfcalc/construct.py` | Shared-intermediate DAG, positive-radix, and signed-window constructive solver |
| `scripts/audit_baseline.py` | Command-line baseline/candidate audit |
| `scripts/solve_constructive.py` | Candidate generation with optional per-puzzle fallback |
| `tests/` | Unit, parser, audit, constraint, and solver regression tests |

## Development setup

Python 3.10+; the core is dependency-free.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
python -m unittest discover -s tests -v
```

The official competition data is not committed. After joining the competition and accepting its rules, download it with the Kaggle CLI:

```bash
kaggle competitions download -c santa-2026 -p data
```

Keep credentials, downloaded competition data, generated submissions, and experiment artifacts out of Git.

## Competition

- [Kaggle competition overview](https://www.kaggle.com/competitions/santa-2026/overview)
- [Competition data](https://www.kaggle.com/competitions/santa-2026/data)
- [Competition rules](https://www.kaggle.com/competitions/santa-2026/rules)

The email invitation lists **21 January 2027** as the entry deadline. The competition page's schedule is authoritative; verify it before relying on either date.

## License

To be selected after reviewing the competition rules and any third-party solver code used. The current constructor is independently implemented; no third-party implementation is vendored.



<!-- trigger latest pool v297 v18 -->
