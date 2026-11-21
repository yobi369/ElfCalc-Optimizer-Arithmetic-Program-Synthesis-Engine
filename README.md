# ElfCalc Optimizer — Arithmetic Program Synthesis Engine

An independent, reproducible solver for Kaggle's **Santa 2026 — The Elf Calculator** competition.

The objective is to synthesize short arithmetic programs that produce every required target using only exact `+`, `-`, `*`, and `/` operations, while respecting the competition's register and value constraints.

## Project status

**Exact validator, reproducible baseline audit, and constructive solver implemented.** The solver searches a bounded shared-intermediate DAG pass, every feasible positional base from 2 through 32 (including shared-prefix orderings), precomputed signed-window widths 3 through 8, and streaming signed-window widths 9 through 14. Every candidate is checked with independent exact-arithmetic replay. The shared-DAG pass is a heuristic experiment; its full-dataset impact is not yet measured.

A full local run on the supplied scored dataset produced a 1,000-program candidate with **275,767 total instructions**. All 1,000 programs replayed successfully and covered every target; the longest program has 548 instructions. The official sample baseline has 1,490,379 instructions, so this candidate reduces the local instruction total by 1,214,612 (81.50%). On the 200 labeled practice puzzles, the same portfolio produced 55,946 instructions. These are locally measured candidate results, **not Kaggle leaderboard scores** and not claims of global optimality. The CSV candidate and its verification report are generated locally and are not committed with competition data.

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
