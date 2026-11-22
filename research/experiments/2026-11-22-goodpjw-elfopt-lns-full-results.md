# Full-dataset GoodPJW LNS result — 22 November 2026

## Run

- GitHub Actions run: `45048175847`
- Job: `137287231661`
- Conclusion: **success**
- Search step: completed
- Artifact: `santa-2026-elfopt-lns-full-dataset`
- Artifact SHA-256: `613ff8f39220262987e2b6bf992a1cb8fb921aa01892b9d48403ff731f7e7e9d`

## Result reported by the workflow

The two-configuration GoodPJW C++ register-aware LNS search ran across all 1,000 puzzles, with two configurations per puzzle:

- Baseline: **131,052** instructions
- Candidate: **131,047** instructions
- Reduction: **5** instructions
- Strictly improved puzzles: **5**
- Optimizer runs: **2,000**
- Status counts: 1,993 no-improvement; 7 improved
- Wall time: 1,798.27 seconds
- Workflow replay validation: **1,000/1,000 valid and complete; zero invalid or incomplete**

The five reported one-instruction reductions are:

- `scored_0161`
- `scored_0423`
- `scored_0626`
- `scored_0737`
- `scored_0778`

Candidate CSV SHA-256: `fada061b2aba1ba8dfbd0ed27083ec080f99238295c5fd08c5d2ee9703c4597a`.

## Interpretation

This is a real but small improvement. The LNS search explored 2,000 configurations and found seven improving runs, resulting in five distinct puzzles being shortened by one instruction each. This suggests the current neighborhood/search budget has reached a difficult plateau on the tested baseline; it does not establish a global optimum or a limit on further progress.

The candidate is **workflow-validated but pending a separate independent local replay and provenance review**. Until that audit is complete, retain 131,052 as the last independently audited candidate and do not describe 131,047 as a Kaggle leaderboard score. No Kaggle submission was made.

## Artifact contents

The uploaded artifact contains the candidate CSV, report, per-puzzle origins, per-run JSONL, baseline, binary hash, optimizer attribution, and Apache-2.0 license text. Preserve these files together when reviewing or redistributing the candidate.
