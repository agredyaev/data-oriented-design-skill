# Data Shape and Computation

## 1. Governing Principle

Prefer the **smallest explicit implementation** that preserves required behavior, data integrity, authorization, recoverability, compatibility, determinism, and resource bounds.

Data-Oriented Design (DOD) is the primary implementation bias where it matches the workload. YAGNI applies aggressively: do not introduce infrastructure, abstraction, caching, indirection, or generic frameworks without a demonstrated requirement.

A cleanup is successful only if it does at least one of the following:

- closes required behavior or a correctness defect;
- removes demonstrated duplication;
- removes unnecessary state or representation;
- reduces avoidable work or allocation;
- strengthens a meaningful behavioral test.

Style-only churn is not progress.

---
# 2. Core DOD Rules

## Rule DOD-01 — Design around the dominant iteration

For each relevant path, identify:

1. the dominant iteration;
2. the fields read and written;
3. the identity domain;
4. the lifetime of the data;
5. allocation ownership.

Choose the representation from that access pattern rather than from an object model.

Prefer, when appropriate:

```rust
Vec<T>
&[T]
&mut [T]
Range<usize>
typed dense IDs
CSR / offsets + flat arrays
bounded side tables
request-local scratch buffers
explicit processing passes
```

Avoid designing runtime state as a graph of individually allocated objects unless the workload genuinely requires it.

### Bad

```rust
struct Model {
    id: ModelId,
    dependencies: Vec<Arc<Mutex<Model>>>,
}

struct Runtime {
    models: HashMap<ModelId, Arc<Mutex<Model>>>,
}
```

Problems:

- pointer chasing;
- atomic reference-count traffic;
- lock traffic;
- fragmented allocation;
- unclear ownership;
- poor cache locality;
- hidden execution order.

### Better

```rust
#[repr(transparent)]
struct ModelId(u32);

struct ModelGraph {
    dependency_offsets: Vec<u32>,
    dependency_ids: Vec<ModelId>,
}
```

```rust
for model_idx in 0..model_count {
    let begin = graph.dependency_offsets[model_idx] as usize;
    let end = graph.dependency_offsets[model_idx + 1] as usize;

    for dependency in &graph.dependency_ids[begin..end] {
        process_dependency(*dependency);
    }
}
```

---

## Rule DOD-02 — Prefer dense typed IDs over pointer identity

Domain relationships should normally use explicit typed IDs rather than object pointers.

### Bad

```rust
struct Edge {
    from: Arc<Model>,
    to: Arc<Model>,
}
```

or:

```rust
struct Edge {
    from: String,
    to: String,
}
```

### Better

```rust
#[repr(transparent)]
struct ModelId(u32);

struct Edge {
    from: ModelId,
    to: ModelId,
}
```

Do not erase semantic distinctions merely because multiple IDs use the same storage width.

### Bad

```rust
type Id = u32;
```

used for models, strings, snapshots, versions, and work items.

### Better

```rust
struct ModelId(u32);
struct StringId(u32);
struct SnapshotId(u32);
struct WorkId(u32);
```

Storage may be identical; semantic domains are not.

---

## Rule DOD-03 — Prefer contiguous storage over heap-per-object layouts

Prefer:

```rust
Vec<Node>
Vec<ModelId>
Vec<u32>
Box<[T]>
```

over:

```rust
Vec<Box<Node>>
Vec<Arc<Node>>
LinkedList<Node>
HashMap<Id, Arc<Node>>
```

when the domain is bounded or naturally enumerable.

The goal is not "`Vec` everywhere"; the goal is to match the representation to the traversal and lifetime.

---

## Rule DOD-04 — Use explicit passes instead of object choreography

Prefer visible processing stages.

### Bad

```rust
world.update();
```

where the call triggers callbacks, shared mutable state, nested dispatch, and hidden allocations.

### Better

```rust
admit_requests(input, &mut admitted)?;
resolve_models(manifest, &mut admitted)?;
build_actions(manifest, &admitted, &mut actions)?;
compute_readiness(&actions, &mut ready)?;
```

Explicit passes make the following visible and testable:

- ordering;
- allocation;
- mutation;
- error propagation;
- determinism;
- ownership;
- data dependencies.

---

## Rule DOD-05 — Builder and runtime representations may differ

Build-time convenience structures are allowed.

Examples that may be valid before freeze:

```rust
HashMap
BTreeMap
String
parser AST nodes
temporary lookup tables
temporary ownership graphs
```

They are not automatically DOD violations.

The important boundary is **freeze**.

### Example

Build-time:

```rust
struct ManifestBuilder {
    models: HashMap<String, ModelBuilder>,
}
```

Frozen runtime:

```rust
struct Manifest {
    model_names: Vec<StringId>,
    model_offsets: Vec<u32>,
    dependencies: Vec<ModelId>,
}
```

Temporary parser/build structures should not survive into frozen runtime state without a concrete reason.

---

## Rule DOD-06 — Do not force SoA everywhere

Struct-of-Arrays is not a universal rule.

Use Array-of-Structs when the dominant loop uses the record as a unit.

### Good AoS

```rust
struct WorkItem {
    model: ModelId,
    partition: PartitionId,
    mode: Mode,
}

struct WorkQueue {
    items: Vec<WorkItem>,
}
```

If every hot loop reads all three fields, this may be the correct layout.

Use SoA when hot passes touch only a subset of fields.

### Possible SoA

```rust
struct WorkState {
    statuses: Vec<Status>,
    attempts: Vec<u16>,
    owners: Vec<WorkerId>,
}
```

if the scheduler repeatedly scans `statuses` without needing the other fields.

Do not mechanically convert every small struct into SoA.

---

## Rule DOD-07 — Do not force CSR, bitsets, or dense indexes where they do not fit

CSR is appropriate for stable graph-like adjacency traversal.

It is not mandatory for every relation.

Likewise:

- not every sparse set should become a bitset;
- not every mapping should become a dense array;
- not every collection should use integer indexing.

Use these structures only where identity density, lifetime, access pattern, and bounds justify them.

---

## Rule DOD-08 — Reuse scratch locally, not through global shared caches

Prefer request-local or operation-local scratch:

```rust
struct Scratch {
    queue: Vec<NodeId>,
    marks: Vec<u32>,
}
```

Reuse explicitly:

```rust
scratch.queue.clear();
scratch.marks.fill(0);
```

Avoid introducing global/shared caches such as:

```rust
Arc<Mutex<HashMap<RequestKey, CachedResult>>>
```

unless there is an existing requirement and demonstrated benefit.

When reusable scratch or generation-indexed storage is introduced, test:

- reset correctness;
- generation rollover;
- stale-index rejection;
- capacity overflow;
- empty input;
- disconnected input;
- deterministic ordering;
- simultaneously live requests where applicable.

---

## Source-aligned structural rule — Prefer pointer-free frozen records

When a runtime domain is bounded, enumerable, or naturally frozen, test whether the retained records can be address-independent:

- the top-level owner may own arrays, byte pools, maps, or other storage;
- records inside those stores should prefer values, typed IDs, offsets, lengths, ranges, tags, and compact handles over owning pointers or per-record heap containers;
- relationships should resolve through the owning state rather than through object pointers when this preserves required semantics;
- moving or reallocating the backing stores should not require rewriting internal relationships when IDs/offsets are defined independently of raw addresses.

A useful target shape is:

```text
State
  +-- entities[]
  +-- child_items[]
  +-- string_bytes[]
  +-- indexes[]

Entity {
  name: StringId
  children: Range
}
```

instead of:

```text
State
  +-- Entity*
       +-- String*
       +-- Vec<Child*>
```

This is not a ban on pointers. Borrowed references, FFI handles, externally owned resources, and genuinely concurrent shared ownership may require them. The question is whether pointer identity and per-object ownership are part of the domain contract or merely an implementation habit.

### Relocatability check

For frozen or snapshot-like state, ask:

> Could the retained representation be moved to another address without fixing up every relationship?

A `yes` is not mandatory, but inability to relocate because domain records contain raw internal pointers is a reason to examine the representation.

### Allocation-shape check

Count allocations by structure, not only total bytes. A representation that changes:

```text
N entities
+ M nested vectors
+ S owned strings
```

into:

```text
entities[]
children[]
string_bytes[]
indexes[]
```

may remove allocator metadata, pointer chasing, deallocation loops, and ownership complexity even when raw payload bytes are similar.
