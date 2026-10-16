# Data Shape Router

Use this file after the affected passes and read/write sets are known. It classifies the representation question and delegates it to one detailed owner. It does not duplicate pointer, builder, derive, or AoS/SoA decision trees.

## Decision tree: select the data-shape owner

```text
What must be decided?
  retained pointer/reference, child containers, builder→frozen lifetime
      -> PWP retained-state decisions.
  canonical copy, stored derived field, repeated parse/normalize/resolve
      -> Canonical and derived data.
  AoS / SoA / AoSoA / field width / side payload / packing
      -> Layout and encoding rules; cost claims remain UNVERIFIED until measured.
  entity-shaped candidate versus pass-shaped data
      -> Structural analysis pass/access synthesis.
  dense/direct-index loop already selected and vector backend is the remaining question
      -> General SIMD.
No branch matches
      -> return to the process/data map; do not invent a representation.
```

### Example: frozen scheduler data

Current code:

```rust
struct Model {
    dependencies: Vec<Arc<Model>>,
    status: Status,
    action: Action,
    cached_end: u32,
}
```

Do not redesign this file by file. Route the questions:

- pointer/children/lifetime → [PWP retained state](compiler/profile/50-pwp-retained-state.md);
- whether `cached_end` should exist → [Canonical and derived](02-canonical-and-derived.md);
- whether `status[]`, `actions[]`, or grouped records fit the passes → [DOD-006 and layout rules](../performance/21-layout-and-encoding.md);
- whether the candidate still mirrors the old `Model` entity → [Structural analysis](00-structural-analysis.md);
- only after dense direct indexing/layout are established, vector execution → [General SIMD](10-simd-and-dense-processing.md).

A router result is the selected owner, not a second representation decision.

## Stop rule

Load only the selected owner. Do not read PWP, layout, canonical, structural, and SIMD blocks together unless the finding actually crosses those boundaries.
