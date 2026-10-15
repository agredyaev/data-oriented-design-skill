# Data Shape and Computation

Use this block to choose the shape of retained data. Start from the affected contract, dominant access pattern, identity domain, mutation pattern, and lifetime. A flat layout is a candidate, not a goal by itself.

## Decision tree: retained relationship and identity

```text
Is the relationship only local borrowed scratch?
  YES -> KEEP a normal reference/slice if it is simplest.
  NO
    |
    |-- Does ABI/FFI/stable-address identity require an address?
    |     YES -> KEEP the required pointer/handle; name the contract.
    |     NO
    |
    |-- Do related entities require independently managed lifetimes?
    |     YES -> preserve that ownership boundary.
    |     NO
    |
    '-- Can one owner keep all entities alive for every consumer?
          NO -> KEEP independent ownership or design an explicit lifetime protocol.
          YES -> TEST root-owned storage + typed IDs/offsets/ranges.
                    Check bounds, stale IDs, deletion/reuse, and compaction.
```

### Example: frozen model graph

Before:

```rust
struct Model {
    dependencies: Vec<Arc<Model>>,
}
```

If one immutable snapshot owns every model and addresses are not observable, test:

```rust
struct ModelId(u32);

struct Graph {
    models: Vec<ModelRow>,
    dependency_offsets: Vec<u32>,
    dependency_ids: Vec<ModelId>,
}
```

Reject the replacement if a consumer can retain a model beyond the snapshot lifetime or requires stable addresses.

## Decision tree: nested variable-size children

```text
Does each parent own a separate child allocation?
  NO -> KEEP the simpler current relation unless another requirement changes it.
  YES
    |
    |-- Are child lists stable/frozen or rebuilt as a bounded unit?
    |     YES -> TEST one flat children[] + offsets/ranges.
    |     NO
    |
    |-- Does the contract require cheap arbitrary append/remove per parent?
          YES -> KEEP an append/update-friendly representation.
          NO -> compare flat rebuild/update cost with the workload; MEASURE if disputed.
```

### Example: flat ranges

`[[A,B], [], [C]]` can become `children=[A,B,C]`, `offsets=[0,2,2,3]`. Parent order is preserved. Do not claim O(1) append to parent 0 after freezing.

## Decision tree: AoS, SoA, or hot/cold split

```text
What does the dominant repeated pass read?
  most fields together -> KEEP AoS unless padding/memory budget says otherwise.
  a stable subset sequentially
      -> TEST SoA or a hot/cold split.
  random whole-record access
      -> KEEP AoS as baseline; a split needs measured benefit.
Does pure SoA increase page/TLB or multi-column working-set cost?
  YES -> TEST AoSoA/chunking.
Does the candidate force full-record reconstruction in the hot loop?
  YES -> REJECT that split.
```

### Example: status scan

If a scheduler repeatedly scans only `status` across one million work items, test `statuses[]` separate from cold payload. If every hot operation immediately needs the whole work item, keep AoS.

## Decision tree: builder versus frozen state

```text
Does a build-time map/AST/growable buffer have a consumer after freeze?
  NO -> RELEASE it at its last consumer.
  YES
    |
    |-- Does runtime need the full builder structure?
    |     YES -> KEEP it.
    |     NO -> retain only the required projection/index.
Is an exact-size packing/freeze pass proposed only for compactness?
  YES -> include conversion copies, peak bytes, and future growth.
          MEASURE when cost determines adoption.
```

### Example: build lookup

A `HashMap<String, ModelId>` used only while resolving edges should disappear after freeze. Keep it if the runtime API still accepts names and must resolve them.

## Decision tree: explicit passes

```text
Does an object method hide callbacks/shared mutation/nested dispatch?
  NO -> no DOD finding from indirection alone.
  YES
    |
    |-- Can required ordering and state transitions be written as bounded typed passes?
          NO -> KEEP the boundary that encodes the required semantics.
          YES -> TEST explicit passes with named inputs/outputs and owners.
```

### Example: make work visible

Prefer explicit operations such as `admit -> resolve -> build_actions -> compute_readiness` when they expose real dependencies. Do not split one cohesive operation merely to create more stages.

## Guardrails

- Do not erase semantic ID domains merely because their storage width matches.
- Do not force `Vec`, SoA, CSR, bitsets, or dense IDs where bounds/access patterns do not fit.
- Do not call a flatter shape faster without matched evidence.
- Use [PWP retained-state decisions](compiler/profile/50-pwp-retained-state.md) for detailed pointer/lifetime cases.
- Use [performance layout rules](../performance/21-layout-and-encoding.md) when a cost target selects field layout or encoding.
