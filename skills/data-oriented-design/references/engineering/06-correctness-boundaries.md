# Correctness Boundaries

Use this block before removing checks, migrations, wire validation, recovery logic, or duplicated implementations. Similar code is removable only when it protects the same invariant at the same authority/time boundary.

## Decision tree: repeated authority checks

```text
Do two checks observe the same authority at the same logical moment?
  NO -> KEEP both; they protect different authority windows.
  UNKNOWN -> inspect when authority can change.
  YES
    |
    '-- Can one check dominate every mutation/finalization path?
          NO -> KEEP the required checks.
          YES -> TEST MERGE only if races/isolation semantics remain identical.
```

### Example: claim and fence

```rust
claim.check_live()?;
apply_changes()?;
fence.check_current()?;
finalize()?;
```

The second check is not duplicate work when another actor can invalidate authority after `apply_changes()`. One early `validate_transaction()?` would weaken the protocol.

## Decision tree: similar validations

```text
Do the checks reject different invalid states?
  YES -> KEEP them as distinct invariants.
  UNKNOWN -> enumerate each failure condition before deduplicating.
  NO
    |
    '-- Would one shared primitive preserve the same diagnostics and failure point?
          YES -> MERGE only the identical mechanic.
          NO -> KEEP separate checks.
```

### Example: SCD2 invariants

```rust
check_source_uniqueness(rows)?;
check_current_row_uniqueness(history)?;
check_monotonic_change_time(rows)?;
check_history_validity(history)?;
```

Do not replace these with a vague `validate_scd2()` implementation that obscures which invariant failed. A small shared comparison helper is fine when the checks remain independently visible.

## Decision tree: old or duplicate implementation

```text
Is the code used by a supported upgrade path, recovery path, or independent oracle?
  YES -> KEEP it; name that responsibility.
  UNKNOWN -> inspect supported versions/tests before deletion.
  NO -> REMOVE it if no current consumer remains.
Does an oracle share implementation with the code under test after cleanup?
  YES -> REJECT that consolidation; independence was the responsibility.
```

### Example: migration and oracle

```rust
fn migrate_v3_to_v4(db: &mut Db) -> Result<()> { ... }

#[test]
fn optimized_matches_reference() {
    assert_eq!(optimized(input), reference(input));
}
```

A migration remains required while v3 is a supported upgrade source. `reference()` may intentionally duplicate logic so it can detect defects in `optimized()`.

## Decision tree: wire bytes versus typed state

```text
Does a validation rule depend on the original bytes/framing/order?
  YES -> KEEP byte-level validation at admission.
  NO -> typed state may replace repeated internal parsing.
Has the byte-level rule already been established before typed admission?
  YES -> REMOVE later serialize/reparse copies unless another wire boundary exists.
```

### Example: duplicate JSON keys

```rust
let admitted = parse_json_rejecting_duplicate_keys(raw)?;
execute(admitted)?;
```

Do not replace the first line with ordinary typed deserialization if duplicate keys must be rejected. After admission, avoid serializing `admitted` back to JSON solely to call an internal component.

## Guardrails

- Upgrade migrations are not dead code while their source version remains supported.
- Independent test oracles must remain independent enough to expose the same implementation defect.
- Wire/framing/truncation/version checks that depend on original bytes cannot be reconstructed from a lossy typed representation.
- Correctness boundaries override YAGNI cleanup and local performance wins.
