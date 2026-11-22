# New source lead: backward frontier rewrite

Date: 2026-11-22

## Discovery

A public Kaggle notebook was identified:

- Author: avazaku
- Kernel: `avazaku/elf-calc-shared-helpers-chain-resynthesis`
- Title: **Elf Calc | Backward Frontier Rewrite**
- Reported public score: **130,963**
- Reported best version: V26
- License shown on Kaggle: Apache 2.0
- Reported method description: shared-helper chains and backward frontier resynthesis

Public listing:
https://www.kaggle.com/code/avazaku/elf-calc-shared-helpers-chain-resynthesis

This is five instructions below our independently replayed 130,974 candidate and is a materially different search family from the Wang Jakie graph-search and GoodPJW LNS variants recently tested.

## Retrieval status

The authenticated GitHub Actions source-fetch workflow was updated to pull both the notebook source and its output:
- `avazaku/elf-calc-shared-helpers-chain-resynthesis`

The workflow uses the existing repository secret `KAGGLE_API_TOKEN`. The notebook source and output have **not yet been retrieved or audited** in this report. Do not assume its reported score can be reproduced until the exact notebook version, inputs, outputs, and replay are independently checked.

## Planned audit

1. Retrieve the notebook source and output through the authenticated workflow.
2. Inspect the notebook source statically; do not execute untrusted notebook code.
3. Identify all input artifacts and exact version lineage.
4. Verify the stated Apache-2.0 license and any third-party source/data notices.
5. Reproduce its candidate output if possible, then exact-replay all 1,000 programs against the pinned puzzle file.
6. Compare row by row with the 130,974 incumbent and promote only strictly shorter, valid rows with auditable provenance.

No Kaggle submission was made.