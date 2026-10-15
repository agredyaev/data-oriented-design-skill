# Pointerless Compiler State

Use this block for long-lived compiler state.

Typical signals are pointer graphs, nested containers, per-string ownership, repeated identity resolution, wide hot records, or retained builder machinery.

The rule is not "no pointers". Use the simplest representation that satisfies ownership and access requirements.

Apply the declared cost budget. If cost is unknown, use `MEASURE`.

## Decision tree

```text
START
  |
  |-- Is this relationship retained semantic state?
  |      |-- UNKNOWN -> inspect lifetime/owner.
  |      |-- NO -> KEEP local pointers/references if simplest; stop this branch.
  |      '-- YES
  |
  |-- Does the contract require stable address identity?
  |      |-- UNKNOWN -> resolve contract before changing ownership.
  |      |-- YES -> KEEP pointer/object ownership; name the requirement.
  |      '-- NO -> Can the proposed owner preserve every object's required lifetime?
  |                    |-- UNKNOWN -> inspect owners/releases before flattening.
  |                    |-- NO -> KEEP independent ownership; do not force one arena.
  |                    '-- YES -> TEST typed IDs/offsets/ranges with checked validity.
  |
  |-- Does each retained row own a variable-size child allocation?
  |      |-- YES -> TEST flat side array + ranges/CSR.
  |      '-- NO -> continue.
  |
  |-- Is per-string ownership a measured cost or retained-memory budget issue?
  |      |-- UNKNOWN -> MEASURE.
  |      |-- YES -> TEST byte pooling; add interning only for required/measured canonical reuse.
  |      '-- NO -> continue.
  |
  |-- Is one logical identity normalized/hashed/resolved more than once?
  |      |-- YES -> PROPAGATE typed identity, unless matched measurement favors recomputation.
  |      '-- NO -> continue.
  |
  |-- Does frozen state retain growth/maps/mutation machinery with no consumer?
  |      |-- YES -> REMOVE it or FREEZE/PACK.
  |      '-- NO -> continue.
  |
  |-- Does a target hot pass fetch fields it does not use?
         |-- UNKNOWN -> MEASURE field access / traffic.
         |-- YES -> TEST SoA or hot/cold storage.
         '-- NO -> KEEP the simpler layout.
```

When cost is uncertain, mark the branch `MEASURE`.

## 1. Represent long-lived relationships with typed handles when possible

Prefer semantic references such as:

```text
InstIx
ExprIx
StringIx
RelationIx
ModelIx
ColumnIx
```

over graph topology based on:

```text
&Node
Box<Node>
Arc<Node>
Node*
```

when all related data belongs to one stable storage domain.

Pointers and references remain valid for local scratch, FFI, stable-address contracts, or genuinely independent ownership.

## 2. Require a reason for pointer identity

Use this test:

```text
Stable address required by a consumer/ABI?
  |-- YES -> Preserve address stability; a numeric ID alone cannot supply it.
  '-- NO -> Is root-owned lifetime sufficient for every consumer?
              |-- YES -> Test dense storage + typed ID; preserve deletion/move validity.
              '-- NO -> Preserve independent ownership, or design an explicit
                         ownership/handle protocol before changing representation.
```

State the specific requirement when a long-lived pointer remains.

For example, frozen nodes destroyed with one compiler snapshot can use snapshot-scoped IDs. A plugin retaining a node after snapshot release needs a valid lifetime protocol; replacing its `Arc<Node>` with a snapshot index would dangle. Use [PWP decisions](profile/50-pwp-retained-state.md) for mutation, generations and range examples.

## 3. Flatten nested variable-size relations

Candidate:

```text
offsets[]
values[]
```

with:

```text
values[offsets[row] .. offsets[row + 1]]
```

Use CSR/ranges when relations are stable enough that contiguous traversal and fewer allocations outweigh update cost.

Do not force CSR on mutation-heavy sparse structures without evidence.

## 4. Pool strings; intern only for a separate reason

Byte pooling targets allocation count and reference width:

```text
string_bytes[]
string_offsets[]
name_id[]
```

Interning additionally provides canonical equality/deduplication but adds lookup cost.

Choose:

```text
many owned strings, little reuse
    -> pool

many repeated canonical strings/values
    -> consider interning

nearly all unique + no equality benefit
    -> avoid interning unless another metric justifies it
```

## 5. Resolve logical identity once when propagation wins the declared trade-off

Prefer:

```text
source name
    ↓
resolve
    ↓
typed identity
    ├── dependency work
    ├── semantic work
    └── lineage/output work
```

Do not repeat normalize/hash/lookup solely because later stages use different wrappers.

Intentional recomputation is valid only when the contract permits it and matched evidence favors recomputation over retention.

Include memory, lifetime, and synchronization cost in that comparison.

Make that trade-off explicit.

## 6. Separate builder and frozen representations

Builder state may use:

```text
Vec<T>
maps
arenas
temporary pointers
growth capacity
```

Frozen state should retain only what its consumers need.

Decision:

```text
Size known at compile time?
  |-- YES -> fixed array when appropriate.
  '-- NO
       |
       |-- Exact size known before write?
       |      |-- YES -> exact allocation.
       |      '-- NO -> growable builder.
       |
       '-- After build, is growth still required?
              |-- YES -> keep growable form.
              '-- NO -> freeze/pack only if it removes unused state by contract or passes the declared cost acceptance rule.
```

Do not turn `Vec<T>` itself into a code smell. The smell is retained builder machinery with no post-build responsibility.

## 7. Separate hot from cold state

When a hot pass reads only a subset of a wide record, test:

```text
HOT
tags[]
types[]
ids[]
ranges[]

COLD
source spans[]
diagnostic text[]
rare metadata[]
```

Choose AoS, SoA, or AoSoA from the actual access pattern. Do not reconstruct full records inside the hot loop after splitting them.

## 8. Fuse semantic passes only when dependency order permits it

Use this test:

```text
Do passes visit the same items in the same order?
  |-- NO -> keep separate.
  '-- YES
       |
       |-- Does a later pass require a full prior result, fixpoint, or global barrier?
              |-- YES -> keep the boundary.
              '-- NO -> test fusion.
```

Preserve error ordering, fixpoint semantics, global barriers, and externally observable ordering.

## Related rules

For exact layout, ID width, interning, packing, side storage, or pass-fusion acceptance, load only the matching performance rule pack.
