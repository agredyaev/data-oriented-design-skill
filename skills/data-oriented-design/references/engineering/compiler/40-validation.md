# Compiler Redesign Validation

Use this block before accepting a compiler/frontend architecture change or a claimed performance improvement.

## Decision tree

```text
START
  |
  |-- Does required semantic behavior match?
  |      |-- NO -> REJECT.
  |      |-- NOT VERIFIED -> VERIFY before acceptance.
  |      '-- YES
  |
  |-- Does the optimization depend on repeated workload shape?
  |      |-- YES -> does representative data demonstrate that repetition?
  |      |             |-- UNKNOWN -> MEASURE representativeness.
  |      |             |-- NO -> REJECT specialization.
  |      |             '-- YES -> continue.
  |      '-- NO -> continue.
  |
  |-- Is a cost improvement claimed?
  |      |-- NO -> verify a named representation/pass/invariant was removed,
  |      |        account for new obligations and required budgets; accept only
  |      |        that structural result. Do not require a speedup.
  |      '-- YES -> declare target metric, causal prediction and guardrails.
  |
  |-- Is matched evidence available for the cause, target and affected guardrails?
  |      |-- NO -> UNVERIFIED; obtain evidence before cost acceptance.
  |      '-- YES
  |
  |-- Did the predicted causal metric pass its acceptance rule?
  |      |-- NO -> REJECT the performance hypothesis.
  |      '-- YES
  |
  |-- Did all required guardrails pass?
  |      |-- NO -> REJECT adoption, even if the primary metric improved.
  |      '-- YES
  |
  '-- Did the declared target pass (memory, phase, end-to-end, or scaling)?
         |-- NO -> TARGET UNMET; report any narrower supported benefit.
         '-- YES -> ACCEPT for that metric if added state/invariants have
                    a named responsibility, lifecycle and budget.
```

### Example: a valid memory result

Suppose the target is retained compiler state ≤150 MB and compile time ≤110 ms. Matched runs show 200 →140 MB and 100 →102 ms; correctness passes. This is a memory win if uncertainty still satisfies both limits, with a reported time trade-off. At 120 ms, reject adoption even though memory improved. A 4 ms lexer gain alone does not establish an end-to-end win.

## 1. Reject benchmark-only architecture

If an optimization exploits repeated synthetic structure, require evidence that the same repetition exists in representative workloads.

Do not retain templates, caches, bypasses, or special paths whose benefit comes from the benchmark generator rather than the product workload.

## 2. Measure stages independently

Record phase time for the relevant compiler stages, for example:

```text
source admission
lexical classification
token extraction
parsing / IR emission
dependency construction
semantic evaluation
lineage
freeze / packing
serialization
```

Do not accept "looks data-oriented" as evidence.

A storage reduction with unchanged wall time is a memory/storage win, not a CPU win.

## 3. Write a falsifiable prediction

Before implementation, state:

```text
OBSERVATION
measured hotspot/cost

CAUSE
physical or logical mechanism believed responsible

CHANGE
smallest transformation that removes that mechanism

PREDICTION
metric(s) that must move

TARGET
retained/peak bytes, phase/end-to-end time, throughput or scaling criterion

GUARDRAILS
required limits that must still pass

INVARIANTS
semantic behavior that must remain unchanged
```

If the predicted physical metric does not move, the performance hypothesis is false even when some other local metric improves.

## 4. Compare semantic outputs, not internal shape

Choose the semantic boundary that defines correctness.

Possible invariants:

```text
same accepted inputs
same rejected inputs
same relation/entity count
same expression count
same row/output count
same dependencies
same value lineage
same row lineage
same canonical hashes when contractual
same observable ordering
same error class/diagnostic contract when contractual
```

Instruction numbers, node addresses, traversal order, or internal packing need not match unless they are externally observable or persisted.

A legacy implementation can serve temporarily as an independent oracle.

## 5. Fail closed

A direct or specialized parser must not guess on unsupported syntax or semantics.

Required behavior:

```text
unsupported / unknown input
    ↓
explicit parse / unsupported / semantic error
```

Never convert unsupported syntax into silently different semantics for speed.

If the existing accepted-input contract includes that syntax, rejecting it is also a regression. Implement it or route it to a correct required fallback; an explicit error is acceptable only where the contract permits rejection.

## 6. Keep an optimization only for a named result

Classify the outcome:

```text
performance win
memory/storage win
scalability win
architecture simplification
no effect
regression
```

Decision:

```text
correctness failed
    -> reject

required budget/guardrail failed
    -> reject adoption, even if another metric improved

correctness passed + target improved
    -> keep only when guardrails pass and every added representation/invariant has a named responsibility and stays within its declared budget

correctness passed + target unchanged
    -> keep only for a separate measured benefit
       or a structural simplification that removes a named representation, pass, allocation class, or invariant

new representation/layer added
    -> require the declared acceptance rule to cover
       its construction, lifetime, maintenance, and added invariants
```

Do not call a storage win a speed win.

## 7. Execution and reporting

Use [Module composition](../../modules.md#choose-and-switch-routes) for route selection and [Workflow](../../workflow.md#proportional-result-format) for proportional reporting. This file adds compiler-specific correctness and measurement gates, not a second workflow.

## 8. Generic target architecture

A valid target can look like:

```text
source bytes
    ↓
classification / tokenization
    ↓
compact parser contract
    ↓
parser with local scratch
    ↓
semantic IR in dense indexed storage
    ↓
semantic passes over required columns
    ↓
canonical result
```

Optional wide classification, mask algebra, batch compaction, SoA, CSR, interning, and pass fusion are mechanisms. They are not mandatory stages.

Central invariant:

> Every persistent representation and every full pass needs a named semantic consumer or a measured cost justification.

