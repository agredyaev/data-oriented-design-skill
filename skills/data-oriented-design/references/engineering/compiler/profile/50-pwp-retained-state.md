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

Before: `Node { children: Vec<Arc<Node>> }`, one root owns a frozen enumerable graph; addresses are not observable. Candidate: `nodes: Vec<NodeRow>`, `child_ids: Vec<NodeId>`, ranges per parent. Traverse through the root owner. Deleting one node is not supported in this frozen contract, so a generation field has no current responsibility.

Counterexample: a native library stores a node's address across calls. Moving that node into a growable array breaks the contract. Keep stable-address storage for that boundary. Similarly, retain a reference-counted interrupt handle required for cross-thread cancellation.

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

Before: child vectors `[[A,B],[],[C]]`. Candidate: `children=[A,B,C]`, `offsets=[0,2,2,3]`. Parent 1 reads the empty range `[2,2)`; parent 2 reads `[2,3)`. Two nonempty child buffers can become one; the empty vector need not allocate. Payload bytes remain. Appending D to parent 0 is not O(1) in this frozen layout; retain another representation if that operation is contractual.

## Decision tree: store or derive a field

```text
Is the field authoritative or independently historical/snapshot state?
  YES -> KEEP it.
Is there an exact deterministic derivation from retained canonical inputs?
  NO -> KEEP it.
Will every input survive until the last read, with the required version?
  NO -> KEEP the field or preserve its inputs/version explicitly.
Does measured derivation meet the read budget, including repeated reads?
  NO -> KEEP the field.
  UNKNOWN -> MEASURE that trade-off; do not claim a speed/memory win.
  YES -> candidate: remove stored copy and derive at use.
Would removal eliminate invalidation/update/synchronization work?
  YES -> include those removed costs when comparing the candidate.
```

### Example: end position versus historical value

`end = start + length` can be derived when the canonical start/length stay live and checked addition fits the source bound. Remove only that duplicated end value; preserve externally required binary layout separately.

A historical price is not derived from the current price. Keep it even if the values happen to match today. Recomputing it from mutable present-day state changes the meaning.

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

Build uses `name -> NodeId` to resolve every edge. After freeze, all consumers use IDs and no name queries exist: release the build map. If a runtime API still resolves incoming names, retain that lookup index; dropping it would remove behavior.

For request scratch `visited[]`, clearing only the queue is insufficient if marks survive. Clear marks or use a checked generation scheme; verify generation wrap, concurrent requests, and stale IDs.

Use [Ownership](../../04-ownership-and-concurrency.md), [Data shape](../../01-data-shape.md), and [Correctness boundaries](../../06-correctness-boundaries.md) when the decision crosses those boundaries. Use [Compiler validation](../40-validation.md) for compiler acceptance. A flatter representation alone does not prove lower runtime.
