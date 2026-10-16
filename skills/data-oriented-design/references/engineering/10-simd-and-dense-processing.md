# General SIMD Backend

Use this block only after the hot operation is known and identity/layout prerequisites are either already established or routed to their owners. This block owns vector execution: lane independence, gather/scatter, masks, backend width, tails, and SIMD-specific acceptance. It does not own dense-ID creation, AoS/SoA selection, or field narrowing.

A SIMD speed claim requires a representative workload and matched measurement. SIMD does not imply a 512-byte logical batch.

## Decision tree: establish SIMD prerequisites

```text
Does the hot loop already use unit-stride arrays or direct indexing by a bounded dense slot?
  YES -> continue to vectorability.
  NO
    |
    |-- Is the blocker pointer/string/key identity?
    |     YES -> route to DOD-005/DOD-008 or PWP for a structural-only decision; return here only if direct indexing results.
    |
    |-- Is the blocker one random companion lookup per sequential row?
    |     YES -> route to DOD-019; return here only if lookup removal succeeds.
    |
    |-- Is the blocker an active/sparse iteration set?
          YES -> route to DOD-020/026 as applicable.
          NO  -> dense-ID SIMD route is not established; use gather/scatter tree or keep scalar.
```

A **dense ordinal** is an internal slot in bounded `[0,N)`; an external integer or string-pool byte offset is not dense by type alone. Do not allocate an array by max external ID.

### Example: identity first, SIMD second

```rust
// Not yet a SIMD-layout decision:
for row in &rows {
    let weight = weight_by_name[&row.name];
    consume(weight);
}
```

First route the lookup to [identity/access rules](../performance/20-identity-and-relations.md) or [DOD-019](../performance/30-work-and-access.md). Only a resulting bounded slot such as `weights[slot]` is a dense/direct prerequisite for this block.

## Decision tree: check vector-layout readiness

```text
Has AoS/SoA/AoSoA/packing already been selected from the pass access pattern?
  NO -> route to DOD-006/layout-and-encoding; do not choose layout here.
  YES
    |
    |-- Does the selected layout expose contiguous/unit-stride lane loads for the hot fields?
    |     YES -> continue to vectorability.
    |     NO -> use gather/scatter tree.
    |
    '-- Would vector execution require reconstructing/scattering records every iteration?
          YES -> reject this SIMD candidate unless matched measurement pays for that work.
          NO -> continue.
```

### Example: full logical item does not decide layout here

```rust
for i in 0..x.len() {
    out[i] = x[i] * scale + y[i] - z[i];
}
```

Whether these aligned columns should be SoA, grouped columns, AoSoA, or an AoS record is owned by [DOD-006](../performance/21-layout-and-encoding.md). This block starts after that layout decision.

## Decision tree: scalar loop to SIMD candidate

```text
Is this loop material to a measured target or explicit throughput budget?
  NO -> KEEP scalar/simple code.
  YES
    |
    |-- Are iterations independent?
    |     NO -> Is it a reduction with explicitly acceptable reassociation/determinism?
    |             NO -> REJECT straightforward lane SIMD.
    |             YES -> TEST a validated vector reduction.
    |     YES
    |
    |-- Can per-item control flow become lane masks without changing observable side effects/order?
    |     NO -> KEEP scalar or split homogeneous cases first.
    |     YES
    |
    '-- Does a candidate narrow fields solely to fit more lanes?
          YES -> DOD-009 must establish bounds/sentinels first; otherwise REJECT.
          NO  -> TEST vector backend against scalar semantics.
```

Keep the scalar semantics/reference available even when production uses SIMD.

### Example: dense scheduler predicate

```rust
for slot in 0..status.len() {
    if status[slot] == READY && dep_count[slot] == 0 {
        ready.push(ModelId(slot as u32));
    }
}
```

Candidate backend:

```text
load status lanes
load dep_count lanes
ready_mask = (status == READY) AND (dep_count == 0)
compact selected lane indices
emit base_slot + lane_index in required order
```

## Decision tree: gather/scatter or change data flow

```text
Does the hot loop read/write values[ids[k]] with non-contiguous ids?
  NO -> use contiguous vectorability tree.
  YES
    |
    |-- Can the existing identity/access owner align companion data to the iterated slot?
    |     YES -> change data flow there, then return to contiguous SIMD.
    |     NO
    |
    |-- Can DOD-026 legally cluster/reorder work?
    |     YES -> test clustering there, then re-evaluate.
    |     NO
    |
    '-- Is hardware gather/scatter measured cheaper than scalar access on the target backend?
          NO/UNKNOWN -> KEEP scalar or MEASURE one bounded gather candidate.
          YES -> TEST gather/scatter with bounds, duplicate-index, and ordering semantics.
```

Scatter needs an additional correctness check: two lanes writing the same slot can change results or create a race.

### Example: do not vectorize around an avoidable lookup

```rust
for id in active_ids {
    score += weight_by_id.get(id).unwrap() * values[id.slot()];
}
```

Do not retain the map and add a gather merely to call the loop SIMD. First ask DOD-019/026 whether the access can become direct or clustered.

## Decision tree: backend, tails, and acceptance

```text
Is machine lane width an external/logical contract?
  NO -> keep it an implementation detail.
  YES -> preserve the contract while allowing multiple machine backends.
Can the final partial block avoid out-of-bounds access?
  scalar remainder -> valid.
  backend-safe masked load/store -> valid.
  readable padding explicitly guaranteed by contract -> valid.
  otherwise -> REJECT.
Does scalar/vector output match edge cases and required ordering?
  NO -> REJECT.
Does matched measurement pass the local prediction and declared target/guardrails?
  NO -> REJECT the performance claim/candidate.
  YES -> ACCEPT only the measured claim.
```

Do not over-read merely because invalid lanes will later be masked.

### Example: safe tail

For `N=10` with an 8-lane backend, process `0..8` as one vector block and `8..10` with a scalar remainder unless a validated masked load is available. Never read `8..16` from a ten-element allocation.

## Dense-ID → SIMD route

The chain is explicit but each decision keeps its owner:

```text
external/pointer/key identity
  -> PWP or DOD-005/DOD-008/DOD-019
bounded dense internal slot
  -> DOD-006/DOD-009 layout and encoding
direct/unit-stride hot pass
  -> General SIMD vectorability
scalar semantic reference
  -> vector backend + safe tail
matched benchmark
  -> reprofile/rerank
```

Stop at any stage that already solves the target. Do not add SIMD merely because dense IDs made it possible.

For byte classification, lexical masks, token streams, or an explicit logical 512-byte contract, use the [PWP/512 profile](compiler/25-pwp-512-profile.md); 512 mechanics are not owned here.
