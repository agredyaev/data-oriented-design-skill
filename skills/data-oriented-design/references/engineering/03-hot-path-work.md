# Hot-Path Work

# 5. Allocation and Hot-Path Rules

## Rule PERF-01 — Treat `clone()` in dominant loops as suspicious

These are not automatically wrong:

```rust
clone()
to_vec()
to_string()
```

but they should be reviewed when used inside dominant loops or recursive rendering.

Ask:

- Is the copy necessary?
- Can ownership be consumed?
- Can a slice/range/index be used?
- Can a buffer be reused?
- Can the work be emitted once instead of retained repeatedly?

---

## Rule PERF-02 — Do not cache expanded intermediate data without measurement

Bad candidate:

```rust
HashMap<ExprId, (String, Vec<Param>)>
```

when nested expressions cause repeated retention and cloning of increasingly large SQL fragments.

Possible alternatives, only after measurement:

- store compact structural information;
- reuse bounded buffers;
- perform a size pass followed by emission;
- cache only genuinely reusable compact data.

Measure before increasing complexity.

---

## Rule PERF-03 — Avoid repeated whole-collection scans when ownership ranges/indexes already exist

Example smell:

```rust
for item in all_models {
    if item.owner == current_owner {
        ...
    }
}
```

repeated for each owner.

Prefer an ownership range/index if the canonical representation already establishes stable grouping:

```rust
let range = manifest.model_range(owner);
for model in &manifest.models[range] {
    ...
}
```

Do not build a secondary index unless the access pattern justifies it.

---

## Rule PERF-04 — Reuse bounded operation-local fragments

If identical bounded fragments are rebuilt repeatedly inside the same transaction/request, prepare them once locally.

Do not turn this into a global cache unless there is an independent requirement.

---
