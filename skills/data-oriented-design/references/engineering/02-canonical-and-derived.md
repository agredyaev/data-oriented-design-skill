# Canonical and Derived Data

# 4. Canonical Data and Representation Rules

## Rule DATA-01 — Keep one canonical representation

Avoid multiple mutable or independently authoritative copies of the same domain state.

Suspicious patterns include:

```text
Manifest
ManifestRuntime
ManifestCache
ManifestLookup
ManifestGraph
```

when each duplicates the same information.

Prefer one canonical representation plus indexes, ranges, or views.

### Better

```rust
struct Manifest {
    models: Vec<Model>,
    model_by_name: FrozenNameIndex,
}
```

```rust
struct ModelView<'a> {
    manifest: &'a Manifest,
    id: ModelId,
}
```

---

## Rule DATA-02 — Do not recalculate stable identity repeatedly

If an identity, digest, normalized name, or mapping has already been admitted and is stable, propagate the typed/admitted form.

Do not repeatedly:

- hash the same canonical data;
- parse the same identifier;
- normalize the same token;
- rebuild the same lookup;
- reconstruct the same graph identity.

---

## Rule DATA-03 — Do not serialize and immediately deserialize internal typed data

### Bad

```text
Typed result
    ↓
JSON Value
    ↓
bytes
    ↓
JSON parse
    ↓
validation
    ↓
Typed-ish use
```

Prefer a reusable validation path for typed/internal values while retaining original-wire validation where wire-level properties matter.

Example: duplicate JSON keys can only be checked reliably at the original wire-decoding boundary, so do not remove that external-byte check merely to eliminate an internal round-trip.

---

## Rule DATA-04 — Preserve admitted typed projections

If parsing/admission has already produced a valid typed representation, downstream code should consume that representation whenever the contract permits.

### Bad

```rust
validate_relation_name(raw)?;
let parts = parse_relation_name(raw)?;
validate_relation_name_again(&parts)?;
```

### Better

```rust
let admitted = admit_relation_name(raw)?;
execute_with_relation(admitted)?;
```

---

## Rule DATA-05 — Avoid repeated full-document reparsing

A known bad pattern is retaining a complete JSON document only to repeatedly reparse it for each work item.

Prefer:

```text
authenticated immutable decision
        ↓
bounded typed execution projection
        ↓
execution
```

Do not use this optimization to remove live authority checks. Immutable decision reuse and live claim/lease/fence validation are separate responsibilities.

---

## Source-aligned computation rule — Prefer cheap recomputation over retained derived state

Memory traffic and retained state are costs. When a value is a deterministic function of canonical data, compare retaining it with recomputing it.

Prefer recomputation when:

- the derivation is cheap relative to the memory traffic or lookup it replaces;
- reads do not require historical snapshot semantics;
- canonical inputs are already resident for the operation;
- retaining the value would add bytes to every row or require another allocation/index;
- stored copies would require invalidation, synchronization, or update bookkeeping.

Examples:

```text
stored:
row.start
row.end
row.line
row.column

candidate:
row.start
row.kind
source bytes + lexical context for variable-width tokens
line_starts[]

fixed-width kind: end = start + fixed_width(kind)
variable-width kind: rescan retained source with the required lexical context
line/byte-column: find preceding line start, then subtract
```

`start` and `kind` alone cannot recover a variable-width token's end. If source/context is discarded, or rescanning breaches the read budget, retain the endpoint. User-visible character columns may need Unicode/tab handling rather than byte subtraction. Use [DOD-017](../performance/21-layout-and-encoding.md#dod-017-decision-tree) for exact derivation and lifetime checks.

and:

```text
stored:
normalized_name
parsed_name
name_hash

candidate:
admitted typed name
+ derive/render only at the boundary that needs text
```

Do not recompute blindly. Keep a derived value when measured recomputation violates the read-path budget, when required inputs are intentionally discarded, or when the stored value has independent temporal or compatibility semantics.

The design question is:

> Is this value state, or is it a function of state?

If it is only a function of canonical state, storing it requires an explicit cost or semantic justification.
