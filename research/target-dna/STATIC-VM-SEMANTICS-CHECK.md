# Target DNA — static VM semantics check

**Review date:** 2026-11-23  
**Review type:** Static source inspection only; no candidate execution or score analysis  
**Files reviewed:** src/elfcalc/machine.py, src/elfcalc/puzzle.py, src/elfcalc/validation.py

## Confirmed in the repository implementation

- The machine has 48 registers, a 4,096-instruction ceiling, and a 131,072-byte serialized-program ceiling.
- Supported operators are addition, subtraction, multiplication, and division.
- Initial values and computed results must be positive integers.
- Division uses integer divmod and rejects non-zero remainder.
- The optional per-puzzle value limit is checked for initial values and every computed result.
- The VM reads both source-register values before assigning the destination. Therefore a destination may alias a source register, provided the source was initialized.
- The machine tracks every value ever observed in a persistent seen_values set. A target remains covered even if its register is later overwritten.
- The puzzle model requires unique, increasing positive targets and exposes missing_targets as targets absent from the initial values.
- The local validator replays the complete instruction sequence and checks instruction count, serialized byte size, arithmetic validity, and target coverage.

## Consequences for Target DNA

1. The graph state is a set of values ever produced plus the currently live register assignment. These are different objects and must not be conflated.
2. A DAG recipe may reuse a value only while a register holding it remains live, or after recomputing it. The optimizer must model this cost.
3. Since target coverage persists after overwrite, a target-producing register can be reused as a destination immediately after its value has been recorded.
4. In-place operations are legal under this local VM because operands are read before the destination write. The instruction scheduler should exploit this where safe.
5. A mathematical recipe graph is not yet a valid register program. It must be scheduled, allocated to 48 registers, serialized, and replayed.
6. Positive subtraction requires lhs > rhs. Exact division requires a nonzero divisor and zero remainder. Every generated edge must encode these preconditions.

## Important scope limitation

This review establishes behavior in the repository's local implementation. It does not independently establish that this implementation is byte-for-byte or semantically identical to the current official Kaggle evaluator. Before competition submission, compare against the official evaluator and replay the final serialized artifact there.

## What was not done

- No authenticated archive was opened.
- No puzzle target set was decomposed.
- No new synthesis program was executed.
- No score improvement is claimed.
