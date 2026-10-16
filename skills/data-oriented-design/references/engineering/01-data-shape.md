# Data Shape and Computation

Use this block after identifying the affected passes and their read/write sets. Choose retained shape from access, identity, mutation, and lifetime; do not preserve entity boundaries by default. A flat layout is a candidate, not a goal.

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

If one immutable snapshot owns every model and the relevant passes read names/status/relations separately, test:

```rust
struct ModelId(u32);

struct GraphData {
    name_ids: Vec<NameId>,
    status: Vec<Status>,
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

Before:

```rust
struct Parent {
    children: Vec<ChildId>,
}
```

Candidate after freeze:

```rust
struct Relations {
    child_offsets: Vec<u32>,
    child_ids: Vec<ChildId>,
}
```

`[[A,B], [], [C]]` becomes `child_ids=[A,B,C]`, `child_offsets=[0,2,2,3]`. Parent order is preserved. Do not claim O(1) append to parent 0 after freezing.

## Decision tree: AoS, SoA, or hot/cold split

```text
What access pattern does the dominant repeated pass use?
  sequential stable subset -> TEST SoA or hot/cold split.
  sequential most/all fields -> AoS and SoA are BOTH candidates;
      compare padding, stream count, SIMD/encoding, and neighboring passes.
  random access needing many fields -> KEEP AoS/hot-record as baseline.
Does pure SoA increase page/TLB or multi-column working-set cost?
  YES -> TEST AoSoA/chunking or grouped columns.
Does the candidate force record reconstruction/scatter in the hot loop?
  YES -> REJECT that split unless measurement supports the trade-off.
```

### Example: status scan

Before:

```rust
struct WorkItem {
    status: Status,
    payload: Payload,
    diagnostics: Diagnostics,
}
```

Candidate when the repeated pass reads only status:

```rust
struct WorkItems {
    status: Vec<Status>,
    cold: Vec<ColdWorkItem>,
}
```

If every hot operation immediately needs the whole work item, keep AoS.

## Decision tree: builder versus frozen state

```text
Does a build-time map/AST/growable buffer have a consumer after freeze?
  NO -> REMOVE it after its last consumer.
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

Before:

```rust
struct Builder {
    rows: Vec<ModelRow>,
    by_name: HashMap<String, ModelId>,
}
```

Candidate when runtime never resolves names:

```rust
struct FrozenModels {
    rows: Vec<ModelRow>,
}
```

Keep `by_name` if the runtime API still accepts names and must resolve them.

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

Before:

```rust
engine.process(input)?; // internally parses, resolves, mutates, dispatches
```

Candidate when these are real dependencies:

```rust
let admitted = admit(input)?;
let resolved = resolve(&admitted, &catalog)?;
let actions = build_actions(&resolved)?;
compute_readiness(&actions, &mut readiness)?;
```

Do not split one cohesive operation merely to create more stages.

## Guardrails

- Do not erase semantic ID domains merely because their storage width matches.
- Do not force `Vec`, SoA, CSR, bitsets, or dense IDs where bounds/access patterns do not fit.
- Do not call a flatter shape faster without matched evidence.
- Use [PWP retained-state decisions](compiler/profile/50-pwp-retained-state.md) for detailed pointer/lifetime cases.
- Use [performance layout rules](../performance/21-layout-and-encoding.md) when a cost target selects field layout or encoding.
