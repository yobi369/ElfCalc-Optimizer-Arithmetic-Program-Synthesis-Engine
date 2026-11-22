# GoodPJW kick-enabled LNS retest at 130,974

Date: 2026-11-22

## Baseline and validation

- Baseline score: **130,974**
- Exact replay before search: 1,000 / 1,000 valid
- Candidate SHA-256: `90f68edb0ebef9c7f2c1839dbc0935cabc13066c60f3de989e0320d49b5d2f36`

## Experiment

Recompiled the Apache-2.0 GoodPJW `elfopt.cpp` optimizer and tested kick-enabled variants on the 100 highest-instruction puzzles. Each puzzle received two four-second runs:

1. seed 2, group 3, orders 3, kicks 2, kick slack 2
2. seed 3, group 4, orders 4, kicks 2, kick slack 2

The exact referee validated every returned candidate before it could be retained.

## Result

- Puzzles searched: 100
- Optimizer configurations: 2 per puzzle
- Improved puzzles: **0**
- Net instruction gain: **0**
- Resulting score: **130,974**

The incumbent was not modified by the experiment. No Kaggle submission was made.

## Interpretation

Kick-enabled LNS did not improve the current best on the 100 hardest puzzles at this budget. This is a bounded negative result, not proof that all LNS configurations or all 1,000 puzzles are exhausted. Keep 130,974 as the verified incumbent and prioritize a genuinely different search family or newly discovered candidate source over repeating these same parameter families.