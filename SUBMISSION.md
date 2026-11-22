# Submission checkpoint — 130,974 instructions

## Current research incumbent

- Candidate: per-puzzle minimum merge of GoodPJW source-aware v72 (130,976) and GoodPJW full-dataset LNS output (131,045).
- Local verified file: `submission.csv` inside `santa-2026-130974-verified-candidate.zip`.
- Rows: 1,000.
- Exact schema: `id,program`.
- Total instructions: **130,974**.
- Independent exact replay: **1,000/1,000 valid and complete**, zero failures.
- Candidate SHA-256: `90f68edb0ebef9c7f2c1839dbc0935cabc13066c60f3de989e0320d49b5d2f36`.
- Official puzzle data SHA-256: `b0c70d849eca078a0e1cf9a4f7b47fd40b7435663f6f84de6725f84724500428`.

The merge uses 998 rows from the v72 source-aware candidate and two shorter rows from the separate LNS/baseline bank:
- `scored_0737`: 111 → 110 instructions (GoodPJW Apache-2.0 LNS).
- `scored_0757`: 129 → 128 instructions (Juan-Severiano checkpoint row selected in the LNS parent portfolio).

The full replay, hashes and merge details are recorded in [the 130,974 merge report](research/experiments/2026-11-22-goodpjw-130974-lns-merge.md).

## Provenance and clearance

This is a mixed-source public-reference frontier. The v72 base itself contains multiple upstream sources; two additional rows come from the LNS/baseline bank. The origin file identifies the immediate source of every row, but complete upstream author/license lineage for all v72 rows has not yet been established.

- Do not describe this as an original solver score.
- Do not redistribute the mixed-source CSV until row-level attribution and license review are complete.
- Check current Kaggle competition rules before deciding whether to submit a public-reference merge.
- No Kaggle submission has been made from this project session.

## Current competitive snapshot

Against the leaderboard values supplied in this research session:

| Position | Score | Gap above this candidate |
|---|---:|---:|
| 1st | 126,659 | 4,315 |
| 2nd | 126,660 | 4,314 |
| 3rd | 128,059 | 2,915 |
| 4th | 128,300 | 2,674 |
| Current research incumbent | **130,974** | — |

These are a user-provided snapshot, not a fresh official Kaggle confirmation. The live leaderboard may change.

## Historical checkpoints

- 131,047: GoodPJW LNS portfolio.
- 131,007: GoodPJW v155 frontier.
- 130,981: GoodPJW source-aware v71.
- 130,976: GoodPJW source-aware v72.
- 130,974: v72 plus two strictly shorter LNS/baseline rows; current research incumbent.

A separate higher-budget local LNS pass is still running from the v71 130,981 predecessor. Its output will be merged against 130,974 and promoted only if the complete result is strictly shorter and passes exact replay.

## Official submission procedure

Only after the competition rules and provenance are reviewed, and after explicit user authorization to submit, use:

```bash
kaggle competitions submit -c santa-2026 -f submission.csv -m "Exact replay-validated arithmetic program portfolio"
kaggle competitions submissions -c santa-2026
```

Never paste Kaggle credentials or API tokens into chat or commit them to this repository.
