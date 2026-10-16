# PWP Retained-State Decisions

Apply these trees to general retained state; no tokenizer or 512-byte batch is required.

## Decision tree: pointer versus typed identity

```text
Is the relationship local borrowed scratch that ends with the operation?
  YES -> KEEP the local reference if it satisfies lifetime rules.
  NO -> does an FFI/ABI/stable-address contract require a pointer?
          YES -> KEEP the required pointer/handle; name that contract.
Do entities require independently managed lifetimes outside one owning domain?
  YES -> preserve the ownership/lifetime boundary; do not replace it with an invalid slot.
  NO -> candidate: root-owned rows + typed ID/offset/range.
Can deletion reuse a slot while an old ID remains live?
  YES -> use checked generations or another stale-ID rejection scheme.
Can compaction move rows?
  YES -> remap relationships or resolve stable IDs through a maintained slot map.
Are bounds, wrong-domain IDs, and stale IDs checked at admission/resolution?
  NO -> REJECT the pointer replacement until those invariants are implemented.
```

### Example: domain graph and native handle

Before:

```rust
struct Node {
    children: Vec<Arc<Node>>,
}
```

Candidate when one frozen graph owns every node and addresses are not observable:

```rust
struct NodeId(u32);

struct NodeRow {
    children: Range<u32>,
}

struct Graph {
    nodes: Vec<NodeRow>,
    child_ids: Vec<NodeId>,
}
```

Deleting one node is not supported in this frozen contract, so a generation field has no current responsibility.

Counterexample:

```rust
struct NativeNode {
    handle: Arc<NativeHandle>, // native API retains stable identity across calls
}
```

Keep stable-address/reference-counted storage for that boundary.

## Decision tree: nested children versus flat ranges

```text
Are child lists frozen, or replaced only by a bounded rebuild?
  YES -> candidate: one children[] plus offsets/ranges.
  NO -> does the contract require O(1) append to any parent's existing list?
          YES -> KEEP an append-friendly representation.
          NO -> compare update/rebuild cost with the declared workload and budget.
Is per-parent order required?
  YES -> build flat ranges in that same order.
Do range endpoints fit the selected integer width for every valid input?
  NO -> keep a wider field or reject oversized input by the existing contract.
```

### Example: flatten child buffers

Before:

```rust
struct Parent {
    children: Vec<ChildId>,
}
```

Candidate after freeze:

```rust
struct Relations {
    child_offsets: Vec<u32>,
    child_ids: Vec<ChildId>,
}
```

For `[[A,B],[],[C]]`, store `child_ids=[A,B,C]` and `child_offsets=[0,2,2,3]`. Appending `D` to parent 0 is not O(1) in this frozen layout; retain another representation if that operation is contractual.

## Derived-field handoff

Store-vs-derive and canonical-authority decisions are owned by [Canonical and derived data](../../02-canonical-and-derived.md). Do not repeat that tree here. After it selects the retained fields, return here only if pointer/child/builder lifetime remains unresolved.

## Decision tree: builder, frozen state, and scratch lifetime

```text
Does the retained map/AST/buffer have a consumer after build/freeze/pass ends?
  NO -> REMOVE it after its last consumer; do not copy it into runtime state.
  YES -> does the consumer need the full structure or only a projection/index?
          full structure -> KEEP it.
          projection/index -> keep only the required result.
Is temporary scratch reused by another operation/request?
  YES -> define reset, ownership, concurrent access, and stale-generation behavior.
Is an exact-size freeze/packing pass proposed only to remove unused capacity?
  YES -> include conversion copies, peak bytes, and future growth needs.
Does the full trade-off meet the declared budget?
  UNKNOWN -> MEASURE; Vec itself is not a defect.
  NO -> KEEP current storage.
```

### Example: retain the right name lookup

Before:

```rust
struct Builder {
    nodes: Vec<NodeRow>,
    by_name: HashMap<String, NodeId>,
}
```

Candidate when every post-freeze consumer already uses IDs:

```rust
struct FrozenGraph {
    nodes: Vec<NodeRow>,
}
```

Remove the build map after its last consumer. If a runtime API still resolves incoming names, retain that lookup index; dropping it would remove behavior.

For request scratch `visited[]`, clearing only the queue is insufficient if marks survive. Clear marks or use a checked generation scheme; verify generation wrap, concurrent requests, and stale IDs.

Use [Ownership](../../04-ownership-and-concurrency.md), [Data shape](../../01-data-shape.md), and [Correctness boundaries](../../06-correctness-boundaries.md) when the decision crosses those boundaries. Use [Compiler validation](../40-validation.md) for compiler acceptance. A flatter representation alone does not prove lower runtime.
