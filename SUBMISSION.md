# Submission checkpoint — 132,515 instructions

## Candidate status

- File: `elfcalc_submission_132515.csv`
- Rows: 1,000
- Exact schema: `id,program`
- Total instruction count: **132,515**
- Local independent replay: **1,000/1,000 valid and complete**
- Candidate SHA-256: `d984166fee5681afc84382afda0d0eaf009922d88c192a9b8fa5dbc9dbbdc5d3`
- Puzzle data SHA-256: `b0c70d849eca078a0e1cf9a4f7b47fd40b7435663f6f84de6725f84724500428`

This is an inherited Apache-2.0 public-reference merge, not an original result from this repository. Its upstream author reports that Kaggle accepted the same checkpoint as submission 58675401 with score 132,515. Preserve all attribution in [THIRD_PARTY.md](THIRD_PARTY.md) and [research/upstream/132515-NOTICE.md](research/upstream/132515-NOTICE.md).

## Restore the candidate

The public repository does not store the raw competition data or generated submission. Retrieve the checkpoint through the GitHub Actions workflow:

1. Open Actions → **Retrieve attributed public frontier checkpoint**.
2. Download the artifact named `attributed-frontier-132515`.
3. Extract `132515.csv` and rename it to `submission.csv`.
4. Verify its SHA-256 against the value above.

The same exact CSV and report are also preserved in the owner's private ChatGPT Library under `Kaggle Competitions/Santa 2026 - Elf Calculator`.

## Submit through the Kaggle CLI

After joining the competition and accepting its rules, place the candidate file at `submission.csv` and run:

```bash
kaggle competitions submit -c santa-2026 -f submission.csv -m "Attributed Apache-2.0 reference checkpoint; independently replay-validated"
```

Then inspect the result:

```bash
kaggle competitions submissions -c santa-2026
```

Do not place Kaggle credentials or API tokens in this repository or in chat. The command submits to Kaggle; local replay alone does not constitute a Kaggle submission.

## Before submission

The owner should review the competition's current rules and attribution requirements. The public leaderboard snapshot checked on 22 November 2026 showed scores near 126,659, so 132,515 is a strong verified checkpoint but is not first place. Continue optimizing against this frozen candidate and only replace it with a strictly shorter, fully replay-validated CSV.
