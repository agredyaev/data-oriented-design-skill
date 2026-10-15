# Canonical and Derived Data

Use this block to decide which representation is authoritative, which values should be derived, and where parsing/normalization should happen.

## Decision tree: one authority versus duplicate state

```text
Do two retained structures encode the same semantic facts?
  NO -> KEEP both if each has a distinct responsibility.
  YES
    |
    |-- Is one explicitly an index/view/projection derived from the other?
    |     YES -> KEEP only if its consumer, rebuild/update rule, and lifetime are named.
    |     NO
    |
    |-- Do both accept independent mutation?
          YES -> REMOVE/MERGE the competing authority after choosing one canonical source.
          NO -> remove the redundant retained copy unless a consumer/budget justifies it.
```

### Example: graph copies

`ManifestGraph + RuntimeGraph + SchedulerGraph` is suspicious when all retain the same edges. Keep one canonical edge store and narrow indexes/views unless each graph has an independent semantic responsibility.

## Decision tree: store or derive

```text
Is the value authoritative or independently historical/snapshot state?
  YES -> KEEP it.
Is there an exact deterministic derivation from retained canonical inputs?
  NO -> KEEP it.
Will every required input/version survive until the last read?
  NO -> KEEP the value or preserve those inputs/version.
Does derivation meet the read-path budget?
  UNKNOWN -> MEASURE.
  NO -> KEEP the stored value.
  YES -> candidate: DERIVE at use.
Does removal also eliminate invalidation/synchronization/update work?
  YES -> include those removed costs in the comparison.
```

### Example: token end

`end = start + fixed_width(kind)` can be derived when the source contract makes width fixed. A variable-width token cannot be reconstructed from `start + kind` alone; keep enough source/context or retain the endpoint.

## Decision tree: parse/admit once

```text
Has raw input already been validated/normalized into a typed value?
  NO -> perform admission at the required boundary.
  YES
    |
    |-- Does a later consumer require the original bytes/text semantics?
    |     YES -> keep the original boundary data it needs.
    |     NO -> KEEP the admitted typed value and pass it downstream.
Does a later stage parse/normalize/hash the same identity again?
  YES -> REMOVE the repeated work unless validity/version changed.
```

### Example: identifier

Prefer:

```rust
let id = admit_relation_name(raw)?;
execute(id)?;
```

over validate → parse → normalize → hash the same name again in every downstream stage.

## Decision tree: internal serialization round-trip

```text
Does typed internal data serialize and immediately deserialize before use?
  NO -> no finding.
  YES
    |
    |-- Is the byte-level boundary itself required for wire/compatibility/security semantics?
    |     YES -> KEEP validation at that boundary.
    |     NO -> pass the typed representation directly.
```

### Example: JSON validation

Do not delete duplicate-key detection performed on original JSON bytes. But once that boundary produced trusted typed data, do not convert it back to JSON and parse it again only to call another internal component.

## Guardrails

- A cache/index is not a second authority when canonical ownership and rebuild/update rules are explicit.
- Recompute only from inputs whose lifetime and version match the required value.
- Live claim/lease/fence checks are not removable snapshots.
- For exact derived-field cost gates, use [DOD-017](../performance/21-layout-and-encoding.md#dod-017-decision-tree).
