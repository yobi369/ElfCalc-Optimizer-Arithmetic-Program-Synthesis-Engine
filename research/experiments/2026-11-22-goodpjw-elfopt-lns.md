# GoodPJW C++ LNS pilot — 22 November 2026

## Source and build

The single-file `elfopt.cpp` engine was retrieved from GoodPJW DAG-LNS Programs v151 (Apache-2.0 for its own optimizer code; see [attribution](../upstream/goodpjw-v151-recombine-ATTRIBUTION.md)) and compiled locally with g++ 14.2.0:

```bash
g++ -std=c++17 -O3 -march=native -DNDEBUG -o elfopt elfopt.cpp
```

Local binary SHA-256: `bae370761b0a2153aa78089e1d0b6e674e9725e943baba95ce69f6527a3ce4bb`.

## Initial hard-puzzle pilot

The engine was run against the 16 highest instruction-count puzzles from the frozen 131,052 candidate, using a 2-second internal search budget per puzzle and a fixed seed/configuration.

- 16 puzzles completed.
- 0 strict instruction improvements.
- The reported accepted local-search moves were not strict score reductions.
- A separate longer attempt on `scored_0051` also found no strict improvement.

This is only a small pilot; it does not establish that the engine cannot improve other puzzles or that longer/more diverse searches will fail.

## Full-dataset experiment

The GitHub Actions workflow [experiment-elfopt-lns-full.yml](../../.github/workflows/experiment-elfopt-lns-full.yml) now runs two configurations across all 1,000 puzzles. Each puzzle/configuration has a hard subprocess timeout, and any returned program must pass a local exact replay before it can replace the baseline. The final merged submission is independently audited again.

No result is claimed until that workflow completes and its artifact report is inspected.
