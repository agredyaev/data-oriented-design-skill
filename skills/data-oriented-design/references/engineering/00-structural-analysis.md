# Structural Analysis

Use this block before detailed DOD rules for any non-trivial performance or architecture problem.

The required direction is:

```text
current process
    ↓
current data types and ownership
    ↓
count steps and transformations
    ↓
identify removable work/state
    ↓
design a simpler process for the same contract
    ↓
choose flatter data structures
    ↓
only then apply detailed DOD rules
```

Do not begin by optimizing an existing class, container, lock, cache, or loop. First decide whether that mechanism belongs in the target design.

## 1. State the exact contract

Write the externally observable task in one sentence:

```text
INPUT → REQUIRED OUTPUT
```

Then list only behavior that must remain invariant:

- accepted inputs and bounds;
- output values and ordering;
- identity semantics;
- error behavior;
- authorization/security checks;
- persistence/wire/ABI compatibility;
- transaction/recovery semantics;
- concurrency requirements;
- explicit latency/memory/throughput budgets.

Unknown requirements are `UNKNOWN`. Do not infer them.

## 2. Build the current process map with data types

Draw the end-to-end process from input to output. Every node must name:

1. the operation;
2. the input data type;
3. the output data type;
4. retained state read or written;
5. multiplicity/call count when known.

Use this format:

```text
[1] parse
    in:  &[u8]
    out: Ast
    work: allocate nodes
        |
        v
[2] resolve
    in:  Ast
    out: Vec<ResolvedObject>
    read: HashMap<String, ObjectId>
        |
        v
[3] build runtime
    in:  Vec<ResolvedObject>
    out: Runtime
    write: Vec<Arc<Mutex<Object>>>
        |
        v
[4] execute
    in:  Request
    read: Runtime
    out: Response
```

Do not write generic boxes such as "service", "manager", or "processing" without the concrete operation and data type.

For each edge annotate applicable costs:

```text
copy
clone
allocate
parse
normalize
hash
lookup
serialize
lock
atomic refcount
IPC
syscall
state transition
ownership transfer
```

Also annotate known quantities:

```text
N items
M edges
K calls
B bytes
A allocations
? = unknown
```

## 3. Build the current retained-data map

Draw the root owner and every retained structure used by the dominant path.

Example:

```text
Runtime
  |
  +-- models: HashMap<String, Arc<Model>>
  |      |
  |      +-- Model
  |            +-- dependencies: Vec<Arc<Model>>
  |            +-- flags: Vec<bool>
  |
  +-- cache: Mutex<HashMap<Key, Value>>
```

For every retained structure record:

- owner;
- lifetime;
- mutable or frozen;
- canonical or derived;
- element count;
- bytes if known;
- number of independent allocations;
- relationship representation: pointer / ID / offset / range / key;
- dominant readers and writers.

## 4. Count the current process

Count the process before proposing a new design.

At minimum record:

```text
process steps:
full passes:
lookups:
parses:
serializations:
copies/clones:
allocations:
locks/atomic refcounts:
IPC/protocol round-trips:
retained representations of the same semantic data:
```

Use actual counts when available. Use symbolic counts such as `N`, `M`, `Q` when they depend on input size.

This count is the structural baseline.

## 5. Identify removable work and state

Inspect the process map from top to bottom. For every node, edge, and retained structure ask these questions in order.

### Process

1. Can this step disappear while preserving the contract?
2. Can two adjacent steps become one pass?
3. Can several calls or round-trips become one batch?
4. Can parse/normalize/resolve happen once instead of repeatedly?
5. Can a lookup be replaced by an ID resolved earlier?
6. Can temporary coordination state become local variables or scratch?

### State

1. Is this representation canonical or a copy of canonical data?
2. Can this stored value be derived from canonical state?
3. Can this build-time structure be discarded after freeze?
4. Can sparse/optional data move out of every row?
5. Does this cache solve measured repeated work, or hide a poor ownership/process design?

### Relationships

1. Does identity require a memory address?
2. Can a pointer/reference become a typed ID?
3. Can nested containers become one flat array plus offsets/ranges?
4. Can repeated strings become one byte pool plus IDs/offsets?
5. Can object polymorphism become tags plus explicit passes?

Every `yes` is a candidate removal or flattening.

## 6. Design the new process from the contract, not from the old classes

Create a second process map that solves the same contract with the smallest explicit sequence of transformations.

Do not preserve an old layer merely because the current code has it.

Required form:

```text
CURRENT
[1] A -> B
[2] B -> C
[3] C -> D
[4] D -> E
[5] E -> output

CANDIDATE
[1] A -> C
[2] C -> E
[3] E -> output
```

For the candidate, name exact data types again.

Example:

```text
[1] admit
    in:  &[u8]
    out: BuildState

[2] freeze
    in:  BuildState
    out: Runtime {
        models: Vec<ModelRow>,
        dependency_offsets: Vec<u32>,
        dependency_ids: Vec<ModelId>,
        string_bytes: Vec<u8>,
    }

[3] execute
    in:  Request
    read: Runtime
    out: Response
```

The candidate must explicitly show which old steps no longer exist.

## 7. Design the new retained representation

Prefer a root-owned flat representation when the domain permits it.

Typical target:

```text
Runtime
  |
  +-- entities[]
  +-- edge_offsets[]
  +-- edge_ids[]
  +-- string_bytes[]
  +-- optional_payloads[]
  +-- indexes[]
```

Typical record:

```text
EntityRow {
    name: StringId,
    edges: Range,
    tag: EntityKind,
}
```

Use:

- typed IDs for stable bounded identity;
- contiguous arrays for frequently traversed data;
- offsets/ranges for one-to-many relations;
- side arrays for sparse or optional payload;
- tags/encodings instead of per-object subtype allocation;
- one canonical state plus indexes/views;
- derived values instead of stored copies when recomputation fits the budget;
- operation-local scratch for temporary work.

Do not force any of these when mutation, ABI, concurrency, lifetime, or measured workload makes another representation better.

## 8. Compare current and candidate structurally

Produce this table before implementation:

| Metric | Current | Candidate | Delta |
| --- | ---: | ---: | ---: |
| process steps | | | |
| full passes | | | |
| retained canonical representations | | | |
| derived retained copies | | | |
| independent allocations | | | |
| pointer/reference hops on dominant path | | | |
| lookups | | | |
| parse/normalize operations | | | |
| copies/clones | | | |
| locks/refcount operations | | | |
| IPC/protocol round-trips | | | |
| retained bytes | | | |

If a value is unknown, write `?`. Do not invent an improvement.

A structural candidate is preferred when it preserves the contract and removes steps, state, relationships, or recurring work without introducing more expensive invariants elsewhere.

## 9. Only now select detailed rules

After the candidate process and data model exist, use the detailed DOD/YAGNI rule packs to answer implementation questions:

- exact ID width and bounds;
- AoS vs SoA vs AoSoA;
- packing and padding;
- indexing;
- sparse side storage;
- pass fusion/fission;
- blocking/clustering;
- concurrency partitioning;
- benchmark design;
- correctness gates.

Detailed rules refine the new design. They do not substitute for creating it.

## 10. Reject ineffective local tuning

Track:

```text
local metric
    ↓
component wall time
    ↓
end-to-end target
```

If a local optimization improves only the first level and does not materially improve the end-to-end target, do not treat it as success.

If two consecutive local changes on the same representation fail to move the end-to-end target:

1. stop tuning that representation;
2. return to Sections 2–8;
3. redraw the current process;
4. produce another structural candidate;
5. continue local tuning only if evidence still identifies that component as material.

## Required output

Before implementation or a final architecture recommendation, provide:

```text
CONTRACT
...

CURRENT PROCESS
[typed ASCII process map]

CURRENT DATA
[typed ASCII retained-data map]

CURRENT COUNTS
steps:
passes:
allocations:
lookups:
copies:
locks:
round-trips:
retained representations:

REMOVABLE
- ...

CANDIDATE PROCESS
[typed ASCII process map]

CANDIDATE DATA
[flat retained-data map]

STRUCTURAL DELTA
[comparison table]

DETAILED RULES NEEDED NEXT
- DOD-...
- engineering/...

EVIDENCE REQUIRED
- ...
```
