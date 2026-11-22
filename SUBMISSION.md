# Submission checkpoint — 131,047 instructions

## Current candidate

- File in the verified artifact: `submission.csv`
- Rows: 1,000
- Exact schema: `id,program`
- Total instruction count: **131,047**
- Local exact replay: **1,000/1,000 valid and complete**
- Candidate SHA-256: `fada061b2aba1ba8dfbd0ed27083ec080f99238295c5fd08c5d2ee9703c4597a`
- Puzzle data SHA-256: `b0c70d849eca078a0e1cf9a4f7b47fd40b7435663f6f84de6725f84724500428`

This is an attributed public-reference portfolio, not an original solver result. It is based on the per-puzzle minimum merge of two attributed public references, then five puzzle programs were shortened by GoodPJW's Apache-2.0 LNS optimizer:

- 640 rows from Juan-Severiano's Apache-2.0 checkpoint (132,515 total).
- 360 rows from Ishan Karnick's frontier dataset v18 (131,053 total), with per-row source credits retained.

The parent merge saves 1,463 instructions versus the Juan-Severiano checkpoint and one instruction versus the Ishan v18 frontier. The LNS pass then saves five additional instructions on five distinct puzzles. Preserve [the Juan-Severiano notice](research/upstream/132515-NOTICE.md), [Ishan v18 credits](research/upstream/ishan-v18-CREDITS.md), [Ishan v18 manifest](research/upstream/ishan-v18-MANIFEST.md), [the parent portfolio report](research/portfolio-131052.md), and [the full-dataset LNS experiment report](research/experiments/2026-11-22-goodpjw-elfopt-lns-full-dataset.md).

## Rebuild the exact candidate

The submission CSV is not committed to the public repository. It can be regenerated from pinned public inputs:

1. Open GitHub Actions.
2. Run **Rebuild and verify 131052 portfolio (parent), then run the full-dataset LNS workflow** (or use its latest successful run).
3. Download the artifact `santa-2026-131052-verified-submission`.
4. Extract `submission.csv`.
5. Verify its SHA-256 against the value above.

The parent workflow verifies the compressed parent archives, puzzle data hash, and parent candidate hashes; replays both parents and the merged output. The LNS workflow independently replays each accepted improvement and the final serialized candidate. The verified 131047 artifact from run 45048175847 is available in that GitHub Actions run's artifact store for its retention period. A local copy was generated for this working session; it has not been uploaded to the Library. The latest successful artifact is also stored in the owner's private ChatGPT Library under `Kaggle Competitions/Santa 2026 - Elf Calculator`.

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
