# Attributed portfolio checkpoint: 132,428 instructions

Date: 22 November 2026

## Result

A new local candidate was assembled by taking the shorter independently replay-valid program for each puzzle from two public, attributed reference portfolios.

| Measure | Result |
|---|---:|
| Scored puzzles | 1,000 |
| Total instructions | **132,428** |
| Valid and complete | 1,000 / 1,000 |
| Invalid or incomplete | 0 |
| Median program length | 118 |
| 90th percentile | 221 |
| Shortest / longest | 2 / 277 |
| Rows selected from Juan-Severiano 132,515 | 992 |
| Rows selected from Hansen0223 132,477 | 8 |
| Savings vs Juan-Severiano 132,515 | 87 |
| Savings vs Hansen0223 132,477 | 49 |

Candidate SHA-256:

`24040cef5722894c278ce0c8a420a3d9168a3366af2327f79b4b8194b4c3835f`

Puzzle file SHA-256:

`b0c70d849eca078a0e1cf9a4f7b47fd40b7435663f6f84de6725f84724500428`

## How the portfolio was built

**Parent A — Juan-Severiano public checkpoint**

- Score: 132,515
- CSV SHA-256: `d984166fee5681afc84382afda0d0eaf009922d88c192a9b8fa5dbc9dbbdc5d3`
- Its source and contributor credits are preserved in [the original notice](upstream/132515-NOTICE.md).

**Parent B — Hansen0223 portfolio**

- Reconstructed score: 132,477
- CSV SHA-256: `208c1f7e839b893f103db0261bb06353fa5810b3a6544d18681a1e5ad7224be9`
- Reconstructed from the pinned Hansen public-assisted base, Asterios Panoras dataset v196, and notebook script version 372207578.
- Both downloaded inputs were checked against the upstream SHA-256 values. The reconstructed CSV matched the upstream manifest's exact score and SHA-256.
- The pinned manifest is [here](upstream/hansen-132477-portfolio.json). The upstream notices and Apache-2.0 text are preserved alongside it.

**Merge rule**

For every puzzle, both parent programs were independently replayed against the exact official puzzle inputs. The shorter valid program was selected; ties retain Parent A. The resulting CSV was serialized with the exact `id,program` schema and replayed again after serialization.

The eight rows selected from Parent B are listed in [the improvement provenance table](portfolio-132428-improvements.csv). Full row-level provenance is maintained with the private candidate artifacts.

## Interpretation and limitations

This is a **per-puzzle minimum merge of existing public reference work**, not a new independently invented solver and not an official Kaggle score. The upstream author credits and notices are retained. Do not present 132,428 as an original algorithmic result.

A CLIST standings snapshot observed on 22 November listed 126,659 as the leading score. The current local candidate is therefore 5,769 instructions above that snapshot. This is a third-party, time-sensitive standings source; Kaggle remains authoritative.

The requested 6,000–8,000 range is below the problem's mathematical lower bound. Even the elementary count of targets absent from starting registers is 26,898. Hansen0223's repository reports a stronger combined puzzle-level lower bound of 37,987; that external certificate set has not yet been independently rechecked here.

## Next optimization work

1. Treat 132,428 as the frozen local baseline.
2. Acquire and hash newer public program releases, preserving each release's license and attribution.
3. Merge the new sources per puzzle, but accept only strict replay-valid improvements.
4. Run targeted arithmetic-graph, cut-and-rebuild, and register-scheduling experiments on hard puzzles.
5. Recompute the complete 1,000-puzzle score and hash after every accepted change.
6. Verify the current Kaggle rules before any submission using third-party programs.

## Submission status

Prepared and locally replay-validated. **Not submitted to Kaggle.**
