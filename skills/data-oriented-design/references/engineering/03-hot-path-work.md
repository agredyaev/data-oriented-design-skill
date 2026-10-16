# Hot-Path Work

Use this block when repeated work, copies, allocations, scans, scratch, or caches are the suspected mechanism. A speed claim still requires matched evidence.

If the shape is boundary-call-per-element, source-index/input-back-reference planning, wide-before-select loading, or persisted temporary computation state, route to [Pipeline materialization](11-pipeline-materialization.md) instead of treating it as generic loop tuning.

## Decision tree: clone/copy/allocation in a repeated path

```text
Does the repeated path clone/copy/allocate data?
  NO -> inspect another cause.
  YES
    |
    |-- Is ownership transfer required by the callee/lifetime?
    |     YES -> KEEP the required ownership; test a different representation only if justified.
    |     NO
    |
    |-- Can the callee borrow a slice/range/view or consume an existing owner?
    |     YES -> TEST borrow/consume and remove the copy.
    |     NO
    |
    '-- Is the allocation temporary and bounded per operation?
          YES -> TEST operation-local reusable scratch.
          NO -> inspect the retained-state responsibility before adding a cache.
```

### Example: clone to slice

Before:

```rust
for batch in batches {
    process(batch.values.clone())?;
}
```

Candidate when the callee does not retain ownership:

```rust
for batch in batches {
    process(&batch.values)?;
}
```

## Decision tree: repeated scans

```text
Does the same collection get scanned repeatedly for the same grouping/key?
  NO -> KEEP the scan unless its measured cost is independently material.
  YES
    |
    |-- Does canonical storage already provide a range/grouping?
    |     YES -> use that range; do not add another index.
    |     NO
    |
    |-- Can one build-time grouping/index serve repeated queries within its lifetime?
          NO -> KEEP scans.
          YES -> compare build + maintenance + bytes against saved query work.
                 MEASURE when the break-even is unknown.
```

### Example: owner ranges

Before:

```rust
for owner in owners {
    for model in &models {
        if model.owner == owner.id { process(model); }
    }
}
```

Candidate when canonical storage already groups models:

```rust
for owner in owners {
    for model in &models[model_range(owner.id)] {
        process(model);
    }
}
```

If the query happens once and no grouping exists, a new index may cost more than the scan.

## Decision tree: local scratch versus retained cache

```text
Is the intermediate used only inside one request/transaction/pass?
  YES -> LOCALIZE it; reuse bounded scratch if repeated allocation matters.
  NO
    |
    |-- Does unchanged input repeatedly request the same result?
    |     NO -> recompute from canonical data.
    |     YES
    |
    '-- Do measured saved query costs exceed cache build, invalidation,
        synchronization, and retained-memory cost?
          UNKNOWN -> MEASURE.
          NO -> REJECT the cache.
          YES -> TEST the smallest cache with explicit invalidation.
```

### Example: expression rendering

Bad first response:

```rust
static RENDERED: Mutex<HashMap<ExprId, (String, Vec<Param>)>> = ...;
```

Prefer operation-local scratch first:

```rust
let mut sql = String::with_capacity(estimated_len);
render(expr, &mut sql, &mut params)?;
```

Keep retained cache state only for demonstrated cross-operation reuse.

## Decision tree: repeated transaction-local fragments

```text
Is an identical bounded fragment rebuilt several times in one operation?
  NO -> no finding.
  YES
    |
    |-- Does preparing it once preserve ordering/version/authority semantics?
          NO -> KEEP separate construction.
          YES -> BATCH once locally and reuse it.
```

### Example: quoted identifiers

Before:

```rust
emit(quote_identifier(name)?);
log(quote_identifier(name)?);
bind(quote_identifier(name)?);
```

Candidate inside one transaction:

```rust
let quoted = quote_identifier(name)?;
emit(&quoted);
log(&quoted);
bind(&quoted);
```

Do not promote it to process-global state.

## Guardrails

- Do not infer end-to-end speed from removed calls or allocations alone.
- Do not retain expanded intermediate data without a named repeated consumer.
- If the measured cause is already known, use the matching [performance rule pack](../performance-methodology.md) rather than restarting diagnosis.
