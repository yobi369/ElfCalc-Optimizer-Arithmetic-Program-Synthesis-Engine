# Authenticated Kaggle solver-source audit — 2026-11-22

## Retrieval result

The authenticated Kaggle source workflow completed successfully (GitHub Actions run 45054563235; artifact 14766074382). Kaggle authentication was confirmed by successful private/API-backed kernel pulls. The bundle SHA-256 is recorded by GitHub as `f6ced23158c729bcbaf006159ad8700e501921e4e6de5f5de3fbcf8d610681e7`.

Retrieved public notebooks:
- `goodpjw2008/santa-2026-source-aware-frontier-lb-130-984`
- `goodpjw2008/santa-2026-lns-cp-sat-recombine-lb-132-256`
- `atakanaldemir/santa-2026-joint-recipes-for-large-puzzles`
- `pablodiegoo/santa-2026-deterministic-atlas-solver`
- `royalacecat/elf-calculator-residual-cut-search`
- `mizeroluckygall/elf-calculator-best-of-public-merge-polish`
- `alexchilton/rudolph-the-red-nosed-register-allocator`
- `ozertuu/santa-2026-starter-notebook`

Two restricted notebook pulls (Pratham Jain and Roman Rozen slugs) returned 403 and were skipped. The workflow now records per-source success/restriction and continues. It was further updated to download GoodPJW's attached `santa-2026-dag-lns-programs` dataset, because the source-aware notebook's newest per-puzzle programs are attached data and must be audited/replayed separately.

## Highest-value algorithmic findings

1. **Source-aware frontier extraction (GoodPJW).** The notebook explicitly harvests programs from notebook source and attached datasets, not only public `submission.csv` outputs. It parses candidate programs as data, exact-replays them, and retains the shortest valid program per puzzle. Its current notebook title reports 130,984, but this number is not accepted as our candidate until the attached program dataset is retrieved, every row is replayed against our pinned official puzzle data, and the exact total is independently recomputed.
2. **Atlas-driven real-machine optimizer (Pablo Diego).** The notebook describes a deterministic C++20 engine with puzzle-family/target structural features; backward quotient/remainder beam search; square-peeling and dependency reversal; depth-5/6 table-joined cone rebuilding; live-frontier and pull-JIT lowering; 48-register topological scheduling/annealing; multi-bank DAG rewrites; cross-trace hypergraph recombination; shared-helper/fan-out scaffold exchange; and bounded target rebuilding. This is the strongest architecture to study for our next independent optimizer, but the notebook's claimed imported source licenses must be checked per source before copying code or redistributing programs.
3. **Deep cone synthesis (Ozertuu).** The notebook describes Miller–Rabin plus Pollard–Rho factorization of target offsets, large meet-in-the-middle tables, congruence-aware backward beam search, and Belady-style register scheduling. Potentially useful for hard target rebuilds; no performance claim is adopted without local tests.
4. **Register allocation and ruin/recreate (Alex Chilton).** The solver uses backward reduction over a two-step dictionary and farthest-next-use eviction (Belady), then performs target/pair ruin-and-recreate. Its own notebook describes substantial gains from target-order portfolio diversity and allocator-aware recompilation. The mechanism credits Tony Li and konbu17; treat those upstream attributions as required.
5. **Window/suffix polishing (Mizeroluckygall).** Uses window optimizer and suffix rebuilder credited to Nilanjan Saha, plus a reroute pass credited to Tony Li. This overlaps with known optimizer work; compare against our existing GoodPJW LNS before adopting.
6. **Residual cut search (RoyalAceCat).** Searches cuts in an arithmetic program, joins candidate expressions and schedules verified replacements under 48-register constraints. The notebook's own reported public-bank score is materially worse than our incumbent, so use it for ideas, not as a candidate bank.

## Immediate experiment plan

- Retrieve and pin the current GoodPJW dataset version and source metadata.
- Extract all candidate CSVs / embedded program banks without executing third-party notebook code.
- Build a row-level provenance manifest (dataset/kernel/version, original author, license evidence, file hash, puzzle ID, instruction count).
- Exact-replay every candidate with the repository verifier; independently recompute total score.
- Compare the best source-aware candidate row-by-row against our 131,007 verified incumbent.
- Only then run controlled local improvements: source-aware merge, Atlas-style multi-bank recombination, register-pressure-aware rematerialization, and bounded cone rebuilds on the hardest residual puzzles.
- Keep the incumbent unchanged unless a full 1,000/1,000 exact replay passes and the total is strictly lower.

## Important distinctions

- GoodPJW's notebook headline 130,984 is a reported notebook result, not yet an independently verified submission in this repository.
- A notebook's Kaggle visibility does not automatically license reuse of its code or its input programs. Dataset and source licenses must be checked independently; mixed-source outputs need row-level attribution.
- No Kaggle submission has been made by this project.
