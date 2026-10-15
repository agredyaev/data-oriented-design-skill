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
  |-- Was a physical/logical cause and acceptance rule declared before implementation?
  |      |-- NO -> classify as architecture experiment; do not claim causal speedup.
  |      '-- YES
  |
  |-- Did the predicted causal metric pass its acceptance rule?
  |      |-- NO -> REJECT the performance hypothesis.
  |      '-- YES
  |
  |-- Did the target phase pass its acceptance rule?
  |      |-- NO -> classify result without phase-speed claim.
  |      '-- YES
  |
  |-- Was end-to-end improvement part of the goal?
         |-- NO -> classify the proven phase/result only.
         '-- YES
              |
              |-- Did end-to-end KPI pass its acceptance rule?
                     |-- NO -> do not claim end-to-end win.
                     '-- YES -> ACCEPT if all added state/invariants have named responsibility and budget.
```

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
phase/end-to-end metric that must improve

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

correctness passed + target improved
    -> keep if every added representation/invariant has a named responsibility and stays within its declared budget

correctness passed + target unchanged
    -> keep only for a separate measured benefit
       or a structural simplification that removes a named representation, pass, allocation class, or invariant

new representation/layer added
    -> require the declared acceptance rule to cover
       its construction, lifetime, maintenance, and added invariants
```

Do not call a storage win a speed win.

## 7. Complete redesign sequence

```text
state contract
  ↓
draw complete typed pipeline
  ↓
list persistent representations
  ↓
remove/fuse representations that add no required information
  ↓
replace unjustified long-lived pointer/key topology
  ↓
pool/resolve identity when required or selected by measurement
  ↓
inspect hot lexical scan
  ↓
test wide classification only when profiling selects lexical scanning
  ↓
test batch event extraction only when profiling selects extraction
  ↓
remove staging tree when it has no independent consumer
  ↓
remove superseded production path
  ↓
semantic correctness gate
  ↓
representative measurement gate
  ↓
keep only added structure with a named responsibility and passed budget
```

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
