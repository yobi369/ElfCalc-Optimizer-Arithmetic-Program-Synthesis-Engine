# GoodPJW DAG-LNS Programs v151 — optimizer attribution

- Dataset: https://www.kaggle.com/datasets/goodpjw2008/santa-2026-dag-lns-programs
- Author: goodpjw2008
- Version: 151 (retrieved 22 November 2026)
- Declared dataset license: Apache-2.0, with the dataset description explicitly stating that inherited program data retains the original source terms.
- Dataset archive SHA-256: `581586ddc71414c3370ddc238fed1a24c94581d845d961ca178aaf0551842fa8`

The CP-SAT experiment workflow retrieves the upstream `elf.py` exact arithmetic helper and `recombine.py` DAG/recipe recombination implementation from this version. The code is used as a research optimizer against the separately attributed 131,052 baseline and licensed candidate banks.

**Important scope:** the 131,052 submission candidate does not select any rows from GoodPJW v151's `our_programs.csv` or `public_frontier.csv`. The GoodPJW public portfolio was inspected as a comparison, but its mixed source lineage was not included in the clean candidate. The workflow uses the GoodPJW optimizer code, not its mixed-license candidate programs.

The GoodPJW dataset description states that Apache-2.0 applies to its own code and programs its search shortened, while every other inherited program keeps the terms of the public notebook or dataset it came from. Preserve the dataset's original credits and do not assume the entire mixed program pool is Apache-2.0.
