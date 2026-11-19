# ElfCalc Optimizer — Arithmetic Program Synthesis Engine

An independent, reproducible solver for Kaggle's **Santa 2026 — The Elf Calculator** competition.

The objective is to synthesize short arithmetic programs that produce every required target using only exact `+`, `-`, `*`, and `/` operations, while respecting the competition's register and value constraints.

## Project status

**Bootstrap stage — no competition score claimed yet.** This repository was created for Brian Mutunga's independent implementation. The first milestone is a trustworthy exact-arithmetic execution and validation core; optimization comes only after the interpreter is tested against the official specification and sample data.

## Engineering principles

- Exact integer arithmetic only; never use floating point for validation.
- Enforce the 48-register machine and every official puzzle/program limit.
- Validate every candidate by replaying it from the original initial state.
- Keep solver heuristics separate from the trusted interpreter.
- Record dataset hashes, solver version, per-puzzle instruction counts, and reproducible experiment settings.
- Never report a score or leaderboard result that has not been confirmed by Kaggle.

## Planned architecture

| Component | Responsibility |
| --- | --- |
| `src/elfcalc/machine.py` | Deterministic exact-arithmetic virtual machine |
| `src/elfcalc/validation.py` | Program, register, target, and constraint validation |
| `src/elfcalc/construct.py` | Initial constructive solver |
| `src/elfcalc/optimize.py` | Local search and instruction-count reduction |
| `src/elfcalc/io.py` | Competition CSV/JSON input and output |
| `tests/` | Unit, property-style, and regression tests |
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

The email invitation lists **21 January 2027** as the entry deadline. The currently indexed competition schedule lists **28 January 2027** as the competition close; verify the authoritative Kaggle page before relying on either date.

## License

To be selected after reviewing the competition rules and any third-party solver code used. No third-party implementation is included in this bootstrap.
