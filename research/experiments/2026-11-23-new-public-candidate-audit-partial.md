# New public candidate outputs — partial audit

Date: 2026-11-23

## Frozen incumbent

- Score: **130,974**
- Exact replay: 1,000 / 1,000 valid
- Candidate SHA-256: `90f68edb0ebef9c7f2c1839dbc0935cabc13066c60f3de989e0320d49b5d2f36`
- Official puzzle SHA-256: `b0c70d849eca078a0e1cf9a4f7b47fd40b7435663f6f84de6725f84724500428`

## Newly retrieved candidate outputs

The authenticated Kaggle output archive from GitHub Actions run `45119643000` was downloaded and inspected. Each full 1,000-row candidate below was checked with the exact local `elf.py` replay against the pinned official `puzzles.csv`.

| Source output | Replayed score | Valid rows | Delta vs 130,974 |
|---|---:|---:|---:|
| `ishankarnick/santa-2026-frontier-programs-130-994` output | **130,859** | 1,000 / 1,000 | -115 |
| `ozertuu/santa-2026-starter-notebook` output | **130,914** | 1,000 / 1,000 | -60 |
| `muhakabartay/santa-2026-strict-verifier-public-merge-anatomy` output | **130,939** | 1,000 / 1,000 | -35 |
| `vigneshsankar1962/santa-2026-free-order-cp-sat-dag-optimizer` output | 131,007 | 1,000 / 1,000 | +33 |
| `vigneshsankar1962/santa-2026-132k-sota-frontier-synthesis-portfolio` output | 131,007 | 1,000 / 1,000 | +33 |
| `pablodiegoo/santa-2026-deterministic-atlas-solver` output | 131,946 | 1,000 / 1,000 | +972 |

The practice-only CSV is not part of the 1,000 scored puzzles and was excluded.

## What this establishes

Three public candidate CSVs are individually better than the incumbent under exact replay. This is a materially stronger lead than the previous bounded local search experiments.

The Ishan public dataset listing identifies `ishankarnick/santa-2026-frontier-programs` as Apache 2.0 and describes it as a best-valid-program-per-puzzle public merge plus graph-search polish. This is useful license evidence for that dataset, but the complete row-level lineage of the retrieved notebook output still needs audit.

The output archive does not by itself establish complete row-level provenance for all three stronger candidates. Do not promote or redistribute a merged candidate until source notebooks, attached datasets, license notices, and any copied third-party code have been reviewed.

## Pending work

1. Retrieve the corrected Avazaku notebook source using the canonical slug `avazaku/elf-calc-backward-frontier-rewrite`; an earlier slug was stale and returned 404.
2. Retrieve source notebooks and metadata for Ishan, Muhakabartay, and Vignesh. The authenticated workflow has been extended to request these sources.
3. Inspect upstream inputs and source notices; identify any restricted or unlicensed components.
4. Perform a per-puzzle merge of only cleared candidates with the 130,974 incumbent.
5. Independently replay all 1,000 rows after CSV serialization and compute the exact merged score and row-level origin map.

## Current status

The 130,974 candidate remains the project's verified incumbent. The 130,859 output is a verified external candidate, not yet the project's merged/provenance-cleared replacement. No Kaggle submission was made.