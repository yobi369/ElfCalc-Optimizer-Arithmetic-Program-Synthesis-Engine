# Public candidate and licensing audit — 22 November 2026

This audit separates candidate quality from permission to reuse. A lower public score is not automatically a reusable source.

| Public source | Version | Reported/replayed total | License / provenance | Decision |
|---|---:|---:|---|---|
| Juan-Severiano checkpoint | pinned 132515 | 132,515 | Apache-2.0; original upstream notice preserved | Used: 640 rows |
| Ishan Karnick frontier | 18 | 131,053 | Apache-2.0; embedded Alex Chilton programs retain CC0-1.0; per-row `sources.csv` | Used: 360 rows |
| Alex Chilton Rudolph | 195 | 131,053 | CC0-1.0 | Included in the Ishan v18 source lineage; no additional rows selected directly |
| Asterios Panoras programs and experiments | 297 | 131,904 | Apache-2.0; per-row source field | Audited; no strict per-puzzle improvement over the Juan + Ishan merge |
| GoodPJW DAG-LNS portfolio | 151 | 131,050 | Apache-2.0 for own code and shortened programs; inherited program rows retain original terms | Candidate CSV not adopted because row-level lineage is not sufficiently exposed; optimizer code is used with attribution |
| Pardheev validated programs | 126 | 131,025 | Kaggle metadata says “Other (specified in description)”; the downloaded description does not state usable terms | Excluded from submission candidate |
| Ozertuu verified programs | 463 | 131,029 | Kaggle metadata reports unknown license | Excluded from submission candidate |
| Kindasomethin exact portfolio checkpoints | 33 | 132,018 | “Other (specified in description)”; mixed upstream Apache-2.0, CC0, and outputs without separate licenses | Excluded from submission candidate |
| Hanif Noer Rofiq peephole programs | 32 | 132,641 | Apache-2.0 | Audited; no shorter per-puzzle rows selected |
| Kmmmvs improver programs | 3 | 136,057 | Apache-2.0 | Audited; no shorter per-puzzle rows selected |
| Konbu17 programs | 11 | 142,940 | Apache-2.0 | Audited; no shorter per-puzzle rows selected |
| Thisray two-step dictionary submission | 1 | 174,827 | CC0-1.0 | Audited; no shorter per-puzzle rows selected |

## Important comparisons

- The clean 131,052 candidate is a two-source per-puzzle minimum: 640 rows from Juan-Severiano 132515 and 360 from Ishan v18.
- The Kindasomethin v33 `row_attribution.csv` contains a per-puzzle instruction-count table for its 132,018 candidate. Comparing those 1,000 lengths against our 131,052 candidate found **zero puzzles** where Kindasomethin's program was shorter. Its program data was not imported because the dataset documents mixed licensing and does not relicense inherited programs.
- The GoodPJW v151 public portfolio totals 131,050, two instructions below our clean candidate. Its dataset description states that inherited program data retains the original source terms, but its downloaded portfolio CSV does not expose enough per-row lineage to clear those three marginal gains. We therefore keep it as a comparison, not as part of the submission candidate.
- Pardheev (131,025) and Ozertuu (131,029) are numerically stronger public candidates, but their downloaded license metadata is respectively unspecified and unknown. Neither was used.
- The CLIST snapshot observed on 22 November listed 126,659 as the leading public score. The 131,052 candidate remains 4,393 instructions above that third-party snapshot; Kaggle is authoritative.

All candidate pools were replayed locally where a complete submission file was available. “Audited” does not mean that every source was adopted. Preserve the individual upstream notices and licenses before reusing any source.
