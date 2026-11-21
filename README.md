# ElfCalc Optimizer — Arithmetic Program Synthesis Engine

An independent, reproducible solver for Kaggle's **Santa 2026 — The Elf Calculator** competition.

The objective is to synthesize short arithmetic programs that produce every required target using only exact `+`, `-`, `*`, and `/` operations, while respecting the competition's register and value constraints.

## Project status

**Foundation and baseline-ingestion stage — no optimized score claimed.** The repository now contains an exact-arithmetic machine, puzzle parser, independent program validator, and an adapter for the official `id,program` submission CSV. The supplied sample submission has been replayed against all 1,000 scored puzzles outside the repository: all 1,000 programs were valid and complete. The baseline contains 1,490,379 instructions in total (median 1,593 per puzzle). This is a verified local replay result, not a Kaggle leaderboard score.

## Engineering principles

- Exact integer arithmetic only; never use floating point for validation.
- Enforce the 48-register machine and every official puzzle/program limit.
- Validate every candidate by replaying it from the original initial state.
- Keep solver heuristics separate from the trusted interpreter.
- Record dataset hashes, solver version, per-puzzle instruction counts, and reproducible experiment settings.
- Never report a score or leaderboard result that has not been confirmed by Kaggle.

## Architecture

| Component | Responsibility |
| --- | --- |
| `src/elfcalc/machine.py` | Deterministic exact-arithmetic virtual machine |
| `src/elfcalc/puzzle.py` | Puzzle model and official puzzle CSV parsing |
| `src/elfcalc/validation.py` | Independent replay validation and official instruction-row conversion |
| `src/elfcalc/submission.py` | Official submission CSV loading and writing |
| `src/elfcalc/construct.py` | Planned constructive solver |
| `src/elfcalc/optimize.py` | Planned search and instruction-count reduction |
| `tests/` | Unit, parser, and regression tests |
| `experiments/` | Reproducible optimization experiments |

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

To be selected after reviewing the competition rules and any third-party solver code used. No third-party implementation is included in this bootstrap.
