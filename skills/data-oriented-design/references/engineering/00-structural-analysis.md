# Structural Analysis

Read this block before local performance tuning or architecture cleanup.

The purpose is to expose the current state shape before optimizing implementation details. The primary question is not "how can this object be faster?" but "does this object, relationship, stored value, pass, or boundary need to exist?"

## 1. Draw the current state shape

Start with one ASCII map that shows the root owner and retained state.

Example:

```text
State
  |
  +-- models: HashMap<Name, Arc<Model>>
  |      |
  |      +-- Model
  |            |
  |            +-- dependencies: Vec<Arc<Model>>
  |
  +-- runtime_cache: Mutex<...>
  |
  +-- work_registry: HashMap<Id, Work>
```

Then draw the dominant execution path separately:

```text
input
  |
  v
parse
  |
  v
lookup
  |
  v
object dispatch
  |
  v
shared state
  |
  v
serialize
  |
  v
output
```

Annotate important nodes and edges with both work type and known scale:

```text
count
bytes
calls
allocations
pointer/ID hops
copy
lookup
hash
parse
normalize
serialize
lock
atomic refcount
IPC
syscall
state transition
ownership transfer
```

Use `?` for unknown quantities. The absence of a measurement is information; do not erase the edge or cost category.

Do not omit an edge because it is hidden behind a wrapper, callback, trait, helper, runtime, framework, or protocol layer.

## 2. Draw the candidate flat shape

For each object-heavy map, attempt a representation with explicit top-level ownership.

Example:

```text
State
  |
  +-- models[]
  +-- dependency_offsets[]
  +-- dependency_ids[]
  +-- string_bytes[]
  +-- indexes[]
```

Relationships become values:

```text
ModelId -> models[id]

dependencies(id):
    dependency_ids[
        dependency_offsets[id]
        ..
        dependency_offsets[id + 1]
    ]
```

This mirrors the source pattern in which a root state owns backing storage while records refer to other data through compact handles, offsets, ranges, or IDs rather than per-object ownership.

The target is not "zero pointers everywhere." The target is to remove pointer identity, nested allocation, and ownership edges from ordinary retained domain relationships when those properties are not required by the contract.

## 3. Count allocation shape

Do not count only payload bytes. Count independent allocations and ownership nodes.

Example:

```text
before
------
N entity allocations
N child-vector allocations
S string allocations
M Arc control blocks
L lock objects

after
-----
entities[]
children[]
string_bytes[]
indexes[]
```

Record:

- number of independent allocations;
- allocator metadata and capacity overhead where relevant;
- number of pointer/reference hops in the dominant pass;
- number of atomic reference-count operations;
- number of locks or shared-mutation points;
- number of containers that require separate destruction or invalidation.

A flat representation can be valuable even when the sum of field widths is similar because it changes allocation count, locality, traversal, and ownership complexity.

## 4. Challenge every retained field

For each stored field ask:

> Is this authoritative state, or a deterministic function of authoritative state?

If it is derived, compare storing it with recomputing it.

```text
stored:
Token {
    start
    end
    line
    column
}

candidate:
Token {
    start
    kind
}

source[]
line_starts[]

end    = derive(start, kind)
line   = derive(line_starts, start)
column = derive(line_starts, start)
```

Prefer derive-over-store when recomputation fits the read-path budget and removes retained bytes, invalidation, synchronization, or update bookkeeping.

Keep the value stored when it has independent snapshot/history semantics, a compatibility contract requires it, required inputs will be discarded, or measured recomputation violates the budget.

## 5. Challenge every relationship

For each relationship ask in order:

1. Does identity need to be a memory address?
2. Can the relationship be a typed ID or handle?
3. Can nested collections become one flat array plus offset/length or offsets?
4. Can repeated strings become one byte pool plus interned handles?
5. Can sparse payload move to side storage?
6. Can membership encode state out of band instead of a field in every row?
7. Can variant behavior become tags plus explicit passes instead of object polymorphism?
8. Can a map used during construction disappear after freeze?

Do not apply these mechanically. Mutation pattern, stable identity, bounds, output order, concurrency, ABI/wire contracts, and workload decide whether the transformation is valid.

## 6. Challenge every layer and boundary

For each wrapper, service, registry, callback chain, process hop, protocol call, or state machine transition ask:

- What concrete contract responsibility does it own?
- Could its caller work directly with the underlying canonical data?
- Could several calls become one batch?
- Could several state transitions become one explicit pass?
- Could temporary coordination state become local scratch?
- Could a runtime object exist only during build/admission?

If removal preserves the contract, prefer removing the mechanism to optimizing its implementation.

## 7. Compare structural alternatives before micro-tuning

Before changing a local mechanism, write at least these alternatives when applicable:

```text
A. keep current representation and tune implementation
B. flatten ownership / replace pointers with IDs
C. remove duplicated or derived state
D. collapse passes / calls / round-trips
E. move temporary structures to build/request scope
```

Estimate for each:

- recurring work removed;
- retained state removed;
- new state introduced;
- new invariants introduced;
- build/update cost;
- query/traversal cost;
- expected effect on the end-to-end target.

Do not choose A merely because it requires the smallest code edit.

## 8. Escalate when local tuning fails

Track:

```text
local physical metric
        |
        v
component / phase wall
        |
        v
end-to-end target
```

A local improvement is not a system improvement.

If a local change improves allocations, lookup cost, lock time, or a component microbenchmark but does not materially move the end-to-end target, re-rank the system.

If two consecutive local changes on the same representation fail to move the end-to-end target beyond noise or toward the stated budget:

1. stop tuning that representation;
2. redraw the ASCII structure;
3. identify the next removable object, state copy, pass, transition, boundary, or round-trip;
4. produce a structural candidate before another micro-optimization.

Continue local tuning only when evidence still shows that component is a material contributor.

## 9. Required structural output

Before implementation, record:

```text
CURRENT ASCII MAP
...

CANDIDATE ASCII MAP
...

REMOVED
- objects:
- allocations:
- retained fields:
- passes:
- lookups:
- locks:
- round-trips:

ADDED
- arrays/indexes:
- build work:
- update work:
- invariants:

STORE -> DERIVE
- ...

POINTER/OBJECT -> ID/RANGE
- ...

EXPECTED TARGET EFFECT
- local:
- phase:
- end-to-end:

EVIDENCE NEEDED
- ...
```

If there is no plausible structural simplification, state why and then proceed to local layout or hot-path tuning.
