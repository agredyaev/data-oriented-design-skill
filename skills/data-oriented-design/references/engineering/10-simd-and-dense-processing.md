# Dense IDs and General SIMD

Use this block for general hot loops over arrays, columns, dense slots, active-ID lists, or regular numeric/state data. It is not the PWP/512 frontend profile.

A dense-ID rewrite can be a structural simplification when it removes repeated lookup or pointer traversal. A SIMD speed claim requires a representative workload and matched measurement. Keep identity, layout, and execution backend as separate decisions.

## Decision tree: dense identity to direct indexing

```text
Does the hot path address retained data by string/key/pointer/map lookup?
  NO -> keep the simpler current addressing unless another requirement changes it.
  YES
    |
    |-- Can admission/build map each live internal entity to a bounded slot 0..N-1?
    |     NO -> KEEP sparse/stable identity; do not allocate an array by max external ID.
    |     YES
    |
    |-- Does that slot remain valid for the consumer/pass lifetime?
    |     NO -> use stable ID -> slot resolution, generations, or remapping at the boundary.
    |     YES
    |
    |-- Can companion data be stored/aligned by the same slot?
          NO -> dense ID alone does not remove the lookup.
          YES -> TEST direct arrays indexed by slot.
                 Keep external/name lookup only at boundaries that still accept those identities.
```

A **dense ordinal** is an internal slot in a bounded contiguous domain `[0, N)`. An integer-valued external ID is not dense merely because its type is `u32`. A pool byte offset is also not automatically a dense ordinal. Do not allocate an array by max external ID.

### Example: resolve once, then index

Before:

```rust
for model in &models {
    let status = status_by_name.get(&model.name).unwrap();
    let deps = dep_count_by_name.get(&model.name).unwrap();
    if *status == READY && *deps == 0 {
        ready.push(model.name.clone());
    }
}
```

Candidate after build assigns `ModelId(slot)` and aligns columns by slot:

```rust
struct Runtime {
    status: Vec<u8>,
    dep_count: Vec<u16>,
}

for slot in 0..runtime.status.len() {
    if runtime.status[slot] == READY && runtime.dep_count[slot] == 0 {
        ready.push(ModelId(slot as u32));
    }
}
```

Keep `name -> ModelId` only if a runtime boundary still accepts names. Counterexample: external IDs `{4, 900_000_000}` do not justify an array of length 900,000,001; remap them to dense slots or keep sparse lookup.

## Decision tree: choose layout for a vector candidate

```text
What access pattern does the repeated pass use?
  sequential subset of stable fields
      -> TEST SoA or a hot/cold split.
  sequential most/all fields
      -> AoS and SoA are BOTH candidates.
         Compare padding, number of streams, vector loads, encoding, and other passes.
  random lookup needing many fields together
      -> AoS/hot-record is a baseline; split only with measured benefit.
Are several columns always consumed together in bounded vector blocks?
  YES -> TEST grouped columns or AoSoA/chunking.
Does pure SoA create page/TLB or too-many-stream cost?
  YES -> TEST AoSoA/chunk size.
Would the proposed layout require reconstructing/scattering whole records in the hot loop?
  YES -> REJECT that layout for this pass unless measurement proves the trade-off.
```

Full-row logical use does **not** imply AoS. `x[i], y[i], z[i]` is still direct access to one logical item when the columns are aligned by the same dense slot.

### Example: full logical item, still SoA-friendly

```rust
for i in 0..x.len() {
    out[i] = x[i] * scale + y[i] - z[i];
}
```

All three fields are used, but the loop has three unit-stride streams and no per-row padding. Keep SoA if this and neighboring passes benefit. If random queries repeatedly need twenty fields of one item, an AoS/hot-record candidate may reduce independent cache-line/page touches. Measure the disputed case.

## Decision tree: scalar loop to SIMD candidate

```text
Is this loop material to a measured target or explicit throughput budget?
  NO -> KEEP scalar/simple code; do not add SIMD complexity for fashion.
  YES
    |
    |-- Are iterations independent?
    |     NO -> Is the dependency a reduction with explicitly acceptable semantics?
    |             NO -> REJECT straightforward lane SIMD.
    |             YES -> TEST a validated vector reduction.
    |     YES
    |
    |-- Are reads/writes unit-stride or direct-indexed by dense slots?
    |     YES -> continue.
    |     NO -> use the gather/scatter tree before choosing SIMD.
    |
    |-- Can per-item control flow become lane masks without changing side effects/order?
    |     NO -> KEEP scalar or split homogeneous cases first.
    |     YES
    |
    |-- Do field widths and encodings preserve every valid value/sentinel/overflow rule?
          NO -> keep wider lanes/representation.
          YES -> TEST vector backend against the scalar reference.
```

Do not expose hardware lane width in the domain model. Keep the scalar semantics/reference available even when the production backend is vectorized. SIMD does not imply a 512-byte logical batch.

### Example: dense scheduler predicate

Scalar reference:

```rust
for slot in 0..status.len() {
    if status[slot] == READY && dep_count[slot] == 0 {
        ready.push(ModelId(slot as u32));
    }
}
```

Vector candidate:

```text
for each lane block:
    ready_mask = (load status == READY) AND (load dep_count == 0)
    compact lane indices selected by ready_mask
    emit base_slot + lane_index
tail -> validated masked load OR scalar remainder
```

The candidate preserves ascending slot order when the output contract requires it. If mask compaction becomes the new dominant cost, optimize or reject that mechanism based on measurement rather than assuming SIMD won.

## Decision tree: gather/scatter or change the data flow

```text
Does the hot loop read values[ids[k]] or write values[ids[k]]?
  NO -> use contiguous/direct-index SIMD tree.
  YES
    |
    |-- Are ids actually 0,1,2,... or one stable dense range?
    |     YES -> remove the index stream; use direct contiguous loads/stores.
    |     NO
    |
    |-- Can build/partition align the companion data to the iterated dense slot?
    |     YES -> TEST aligned parallel arrays before hardware gather.
    |     NO
    |
    |-- Can ids be clustered/reordered without changing observable order?
    |     YES -> TEST clustering/batching, then re-evaluate contiguous access.
    |     NO
    |
    '-- Is hardware gather/scatter supported and measured as cheaper than scalar access?
          NO/UNKNOWN -> KEEP scalar or MEASURE a bounded gather candidate.
          YES -> TEST gather/scatter with duplicate-index and fault/bounds semantics.
```

Scatter needs an additional correctness check: two lanes writing the same slot can change results or create a race. Reject unordered scatter when duplicate IDs, accumulation order, or exceptions are observable.

### Example: dense companion array before gather

Before:

```rust
for id in active_ids {
    score += weight_by_id.get(id).unwrap() * values[id.slot()];
}
```

If `ModelId.slot()` is the admitted dense slot, store `weights[slot]` and iterate a dense active partition when order permits:

```rust
for slot in active_start..active_end {
    score += weights[slot] * values[slot];
}
```

Do not keep a map lookup and then add SIMD gather on top of it. Remove the avoidable identity work first.

## Decision tree: backend, tails, narrowing, and acceptance

```text
Is vector width part of an external/logical contract?
  NO -> keep lane width/backend an implementation detail.
  YES -> preserve that contract while allowing multiple machine backends.
Can the final partial block be processed without out-of-bounds access?
  scalar remainder -> valid candidate
  masked load/store with backend-safe bounds -> valid candidate
  readable padding established by contract -> valid candidate
  otherwise -> REJECT
Does narrower encoding increase lane density?
  YES -> prove bounds, signedness, sentinels, overflow, and conversion cost first.
Does the operation use floating reduction/reassociation?
  YES -> preserve required determinism/error bounds or REJECT the changed semantics.
Do scalar and vector outputs match all edge cases?
  NO -> REJECT.
YES -> compare local metric and declared target; keep only the supported claim.
```

Alignment is a measurement/backend concern, not a reason to add padding automatically. Do not over-read merely because bytes will later be masked away.

### Example: safe tail and narrow lanes

For `N=10` with an 8-lane backend, process slots `0..8` as one vector block and slots `8..10` with a scalar remainder unless a validated masked load is available. Never load slots `8..16` from a 10-element allocation.

If `dep_count` is narrowed from `u32` to `u16`, admission must reject or represent values above 65,535 and preserve any sentinel. More lanes per vector is not evidence that the narrower encoding is correct or faster.

## Dense-ID → SIMD route

Use this route only when each arrow is supported:

```text
external/sparse identity
  -> admit/resolve once
dense internal slot [0,N)
  -> align hot companion fields by slot
direct indexed / unit-stride pass
  -> remove avoidable map/pointer work
SoA / grouped columns / AoSoA selected from access pattern
  -> establish independent lane semantics
scalar reference
  -> TEST SIMD backend
matched benchmark
  -> reprofile/rerank
```

Stop at any stage that already solves the target. Do not add SIMD merely because dense IDs made it possible.

For byte classification, lexical masks, token streams, or the selected logical 512-byte contract, use the [PWP/512 profile](compiler/25-pwp-512-profile.md) instead of treating 512 as a general SIMD width.
