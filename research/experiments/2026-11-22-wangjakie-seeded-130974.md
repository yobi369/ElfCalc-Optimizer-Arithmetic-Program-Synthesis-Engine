# Wang Jakie seeded graph-search pass on 130,974

## Objective

Test whether the Apache-2.0 Wang Jakie arithmetic graph-search strategies can shorten the current 130,974 portfolio by reusing near-length alternative programs as crossover seeds.

## Pinned starting bank

- Candidate total: 130,974.
- Official puzzle SHA-256: `b0c70d849eca078a0e1cf9a4f7b47fd40b7435663f6f84de6725f84724500428`.
- Candidate CSV: `90f68edb0ebef9c7f2c1839dbc0935cabc13066c60f3de989e0320d49b5d2f36`.
- Extra candidate seed banks: GoodPJW v72 (130,976), Ozertuu starter output (130,979), Alex Chilton Rudolph output (130,979), and GoodPJW LNS output (131,045).
- Source: Wang Jakie's public graph-search strategies from the GoodPJW DAG-LNS dataset; `NOTICE.md` identifies Apache-2.0 and records the seeded-variant changes.

## Current run

- Strategy: `anneal_seeded`.
- Focus set: 200 highest-instruction-count puzzles.
- Rounds: 700.
- Worker processes: 3.
- Batch size: 4.
- Seed: 20261124.
- Extra seed banks: four per puzzle maximum; slack up to 3 instructions.
- Candidate outputs are replayed by the upstream driver and will be independently replayed again before promotion.

## Promotion criteria

No change to the 130,974 incumbent unless the complete 1,000-row candidate is strictly shorter and passes the independent exact replay audit. Preserve origin metadata and Apache-2.0 notices. No Kaggle submission without explicit user authorization.

## Follow-on strategies

If the first pass yields gains, test `incremental_seeded` and `compact_rotate` on the updated focus set with fresh seeds. Do not assume any strategy is beneficial until measured against the pinned incumbent.
