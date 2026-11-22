# Submission checkpoint — 131,052 instructions

## Current candidate

- File in the verified artifact: `submission.csv`
- Rows: 1,000
- Exact schema: `id,program`
- Total instruction count: **131,052**
- Local exact replay: **1,000/1,000 valid and complete**
- Candidate SHA-256: `1902b48b488380c9282a2537ad0279cc7f6c0d159f19360b019501fe0401ccef`
- Puzzle data SHA-256: `b0c70d849eca078a0e1cf9a4f7b47fd40b7435663f6f84de6725f84724500428`

This is a per-puzzle minimum merge of two attributed public references, not an original solver result:

- 640 rows from Juan-Severiano's Apache-2.0 checkpoint (132,515 total).
- 360 rows from Ishan Karnick's frontier dataset v18 (131,053 total), with per-row source credits retained.

The merge saves 1,463 instructions versus the Juan-Severiano parent and one instruction versus the Ishan parent. Preserve [the Juan-Severiano notice](research/upstream/132515-NOTICE.md), [Ishan v18 credits](research/upstream/ishan-v18-CREDITS.md), [Ishan v18 manifest](research/upstream/ishan-v18-MANIFEST.md), and [the portfolio report](research/portfolio-131052.md).

## Rebuild the exact candidate

The submission CSV is not committed to the public repository. It can be regenerated from pinned public inputs:

1. Open GitHub Actions.
2. Run **Rebuild and verify 131052 portfolio** (or use its latest successful run).
3. Download the artifact `santa-2026-131052-verified-submission`.
4. Extract `submission.csv`.
5. Verify its SHA-256 against the value above.

The workflow verifies the compressed parent archives, puzzle data hash, and parent candidate hashes; replays both parents and the merged output; then runs the repository's independent full-submission audit. The latest successful artifact is also stored in the owner's private ChatGPT Library under `Kaggle Competitions/Santa 2026 - Elf Calculator`.

## Submit through the Kaggle CLI

Only after joining the competition and reviewing/accepting its current rules, place the extracted file at `submission.csv` and run:

```bash
kaggle competitions submit -c santa-2026 -f submission.csv -m "Attributed per-puzzle minimum of Apache-2.0/CC0 public references; exact replay-validated"
```

Then inspect the result:

```bash
kaggle competitions submissions -c santa-2026
```

Do not place Kaggle credentials or API tokens in this repository or in chat. A local replay audit is not a Kaggle submission; no submission has been made from this project session.

## Current competitive position

A third-party CLIST snapshot observed on 22 November 2026 listed 126,659 as the leading score. This candidate is 4,393 instructions above that snapshot. The Kaggle leaderboard is authoritative and may have changed.

The older 132,515 public checkpoint remains documented as a parent and fallback. Replace the current candidate only with a strictly shorter complete CSV that passes the same exact replay audit.
