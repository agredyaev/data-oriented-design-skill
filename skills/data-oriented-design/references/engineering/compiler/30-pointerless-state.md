# Pointerless Compiler State Router

Use this file only to classify compiler-specific retained-state questions. General retained-state decisions have existing owners; this file must not restate their trees.

## Decision tree

```text
What compiler-state decision is blocking the design?
  pointer/reference topology, nested children, builder→frozen lifetime
      -> PWP retained-state decisions.
  duplicate/canonical state, stored derived field, repeated admission
      -> Canonical and derived data.
  performance pointer/flat-relation claim
      -> DOD-005/DOD-007/DOD-008 identity rules.
  string pooling/interning cost
      -> DOD-022.
  AoS/SoA/AoSoA, side storage, compact field/variant encoding
      -> Layout and encoding rules.
  repeated pass / fusion / blocking / clustering
      -> Pipeline elimination for stage necessity;
         measured remaining access cost -> DOD-024/025/026.
  none
      -> return to the compiler pipeline map; do not invent pointerless work.
```

### Example: compiler snapshot

```rust
struct Node {
    children: Vec<Arc<Node>>,
    cached_end: u32,
}
```

If one snapshot owns all nodes, route pointer/children lifetime to [PWP retained state](profile/50-pwp-retained-state.md). Route `cached_end` store-vs-derive to [Canonical and derived](../02-canonical-and-derived.md). If a measured hot pass later needs a different field layout, route that separately to [Layout and encoding](../../performance/21-layout-and-encoding.md). Do not solve all three questions in this router.

## Compiler-specific boundary checks

Before delegating, record compiler consumers that can invalidate a general simplification:

- plugin/FFI/stable-address lifetime;
- diagnostics/source-map/source-byte requirements;
- incremental compilation or snapshot/version lifetime;
- tooling that consumes syntax/IR independently;
- grammar/order/error semantics.

After the selected owner returns a candidate, use [Compiler validation](40-validation.md). For structural stage removal, use [Pipeline elimination](10-pipeline-elimination.md).

Detailed performance owners: [Identity and flat relations](../../performance/20-identity-and-relations.md) and [Work/access](../../performance/30-work-and-access.md).
