# 130,974 frontier — merge with full-dataset LNS result

## Result

**130,974 instructions**, 1,000/1,000 valid and complete, zero failures.

This is a per-puzzle minimum merge of:
- GoodPJW source-aware v72 frontier: 130,976 (independently replayed).
- GoodPJW full-dataset LNS output from run 45051994422: 131,045 (workflow replayed against the same official puzzle SHA).

The LNS run itself improved its 131,052 parent by 7 instructions across six puzzles. When compared row-by-row with v72, only two of its programs are shorter:
- `scored_0737`: 111 → 110 instructions (GoodPJW LNS seed1-g4-o4).
- `scored_0757`: 129 → 128 instructions (Juan-Severiano parent row selected in the LNS baseline).

The other 998 rows remain from v72. Net gain over 130,976: **2 instructions**.

## Hashes

| Artifact | SHA-256 |
|---|---|
| Official puzzles | `b0c70d849eca078a0e1cf9a4f7b47fd40b7435663f6f84de6725f84724500428` |
| v72 source-aware candidate | `f06d968ae8cd3eaf5d06739bd999a4b1d6c87ddf9a7697686a7827f333b4ae46` |
| LNS 131,045 bank | `9c8901bbea79a420b4b9e8f3fa0dc615e7cd2436d6220b621b639dfa207a8f81` |
| Merged 130,974 candidate | `90f68edb0ebef9c7f2c1839dbc0935cabc13066c60f3de989e0320d49b5d2f36` |

## Replay validation

Independent exact replay checked the full merged CSV:
- Exactly 1,000 unique IDs and official `id,program` schema.
- 48 registers, initialized reads, exact division, positive intermediate values, and per-puzzle value limits.
- Maximum 4,096 instructions and 131,072 serialized bytes per program.
- Every target reached.
- Result: **1,000 valid and complete; zero failures**.

## Provenance

The merged candidate is still mixed-source: 998 rows from GoodPJW's source-aware v72 frontier (which itself is mixed-source), plus two rows from the GoodPJW Apache-2.0 LNS/baseline bank. Full upstream per-row lineage remains incomplete. This is a local research artifact, not an official Kaggle submission; do not redistribute or submit until source attribution and competition rules have been reviewed.

## Next search

A separate higher-budget local LNS pass was already running from the v71 130,981 base when v72 was discovered. Its output will be merged against 130,974 and independently replayed. Targeted Atakan multiplier-frontier and interface-closure experiments are also planned for the highest-cost low-seed puzzles.


## Cross-check with the earlier Atakan full-dataset bank

Atakan full-dataset run 45052245963 produced 131,051 from a 131,052 parent (one instruction saved, one puzzle improved). Its output was independently compared with the 130,974 candidate. It was longer on 54 puzzles, equal on 946, and shorter on none. Therefore it does not change the 130,974 incumbent. The separate targeted Atakan search on the 200 highest-cost puzzles is still running.


## Targeted Atakan frontier search — no gain in first half

A separate local Atakan Apache-2.0 multiplier-frontier pass targeted the 200 highest-cost puzzles using two seeds. It was stopped after 208 of 400 puzzle/seed jobs completed: 207 no-improvement results and one timeout; no candidate was promoted. The earlier full-dataset Atakan output also had no rows shorter than 130,974. The current Wang Jakie seeded graph-search pass is being prioritized next.
