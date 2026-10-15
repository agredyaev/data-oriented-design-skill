# Pointerless Compiler State

Use this block when long-lived compiler state contains pointer graphs, nested containers, individually owned strings, repeated logical identity, wide hot records, or builder state that survives after construction.

The rule is not "no pointers". The rule is: persistent semantic identity and topology should use the simplest representation that satisfies ownership/access requirements and the declared cost budget. If cost is unknown, use `MEASURE`.

## Decision tree

```text
START
  |
  |-- Is the relationship long-lived semantic state?
  |      |-- NO -> local pointers/references are allowed; stop.
  |      '-- YES
  |
  |-- Does the target require independent lifetime or stable address identity?
  |      |-- YES -> keep pointer/object ownership; name the requirement.
  |      '-- NO -> use a typed ID, offset, or range.
  |
  |-- Does each row own a variable child/list allocation?
  |      |-- YES -> test one flat side array + ranges/CSR.
  |      '-- NO
  |
  |-- Are many strings individually allocated?
  |      |-- YES -> test byte pooling; add interning only if canonical identity/dedup is required or measured to improve the target.
  |      '-- NO
  |
  |-- Is logical identity normalized/hashed/resolved more than once?
  |      |-- YES -> resolve once and propagate typed identity, unless matched measurement shows recomputation has lower total cost.
  |      '-- NO
  |
  |-- Does frozen state retain builder capacity/maps/mutation machinery?
  |      |-- YES -> freeze/pack to exact immutable storage.
  |      '-- NO
  |
  |-- Do hot passes read only a subset of wide state?
         |-- YES -> test SoA or hot/cold side storage.
         '-- NO -> keep the simpler layout.
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
Does the value need independent lifetime/ownership?
  |-- NO -> dense root-owned storage + typed ID.
  '-- YES
       |
       |-- Is stable address identity required?
              |-- YES -> pointer/object ownership is valid.
              '-- NO -> prefer dense storage + typed ID.
```

State the specific requirement when a long-lived pointer remains.

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

## 5. Resolve logical identity once when propagation is cheaper

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

Exception: intentional recomputation is valid when the retained representation would cost more memory, lifetime complexity, or synchronization than resolving again.

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
