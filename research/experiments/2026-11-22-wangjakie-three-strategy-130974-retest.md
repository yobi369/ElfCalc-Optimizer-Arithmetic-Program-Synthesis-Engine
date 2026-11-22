# Wang Jakie three-strategy retest at 130,974

Date: 2026-11-22

## Baseline

- Candidate score: **130,974**
- Exact replay: **1,000 / 1,000 valid**, zero failures
- Candidate SHA-256: `90f68edb0ebef9c7f2c1839dbc0935cabc13066c60f3de989e0320d49b5d2f36`
- Official puzzle source: pinned local `puzzles.csv`

## Search setup

Recovered the original Wang Jakie strategy sources and driver from the authenticated GoodPJW source archive. The source is attributed in `third_party/wangjakie/NOTICE.md` and is Apache-2.0. The seeded variants add extra near-length input programs to the candidate crossover pool; this modification is recorded in the NOTICE.

Each strategy searched the 200 puzzles with the highest current instruction counts, using the 130,974 incumbent and four validated historical candidate banks as inputs. All runs used 700 rounds per puzzle, three workers, and independent fixed seeds.

## Results

| Strategy | Puzzles | Rounds per puzzle | Improved puzzles | Net gain | Resulting score |
|---|---:|---:|---:|---:|---:|
| `anneal_seeded` | 200 | 700 | 0 | 0 | 130,974 |
| `incremental_seeded` | 200 | 700 | 0 | 0 | 130,974 |
| `compact_rotate` | 200 | 700 | 0 | 0 | 130,974 |

No candidate from these runs was promoted.

## Follow-up GoodPJW LNS retest

Recompiled the Apache-2.0 GoodPJW LNS optimizer and tested the two previously productive parameter families on the same top-200 focus set:
- seed 0, group 3, orders 3
- seed 1, group 4, orders 4

Each configuration received four seconds per puzzle. The search completed all 200 puzzles with **zero improvements**. The reporting script encountered a post-search bookkeeping NameError because no candidate had improved and the no-gain branch did not initialize its final score variable. This did not alter the incumbent file.

The incumbent was independently replayed again after the search:
- 1,000 / 1,000 valid
- score 130,974
- SHA-256 unchanged: `90f68edb0ebef9c7f2c1839dbc0935cabc13066c60f3de989e0320d49b5d2f36`

## Conclusion

These focused retests did not improve the incumbent. Do not infer that the strategies are globally exhausted: they covered only the 200 highest-cost puzzles, and the search budgets and parameter combinations were finite. Preserve 130,974 as the verified incumbent. No Kaggle submission was made.