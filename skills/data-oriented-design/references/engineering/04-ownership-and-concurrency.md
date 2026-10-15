# Ownership and Concurrency

Use this block to decide whether sharing, reference counting, stable addresses, or synchronization have a concrete responsibility. `Arc`, `Mutex`, references, and pointers are mechanisms, not automatic defects.

## Decision tree: shared ownership

```text
Is the value retained beyond one local operation?
  NO -> KEEP ordinary borrowing/local ownership if it satisfies the lifetime.
  YES
    |
    |-- Does an FFI/ABI/native API require a stable pointer or reference-counted handle?
    |     YES -> KEEP that handle; name the boundary.
    |     NO
    |
    |-- Do multiple owners genuinely outlive one common root owner?
    |     YES -> shared ownership may be required; define release semantics.
    |     NO -> root-own the data and borrow/resolve through that owner.
```

### Example: immutable manifest

If an engine owns a manifest for the whole process and workers only read it, prefer direct ownership plus borrows. Use `Arc<Manifest>` only when thread/task ownership genuinely requires an independently cloned owner handle.

## Decision tree: `Mutex` / shared mutation

```text
Is the protected state mutated concurrently by multiple execution contexts?
  NO -> REMOVE the lock; freeze or localize the state.
  UNKNOWN -> inspect writers and lifetimes before changing it.
  YES
    |
    |-- Is it one real shared resource whose invariant spans those writers?
    |     YES -> KEEP synchronization required by that invariant.
    |     NO
    |
    |-- Can mutable ownership be partitioned/localized without changing semantics?
          YES -> TEST local ownership/sharding; include merge/order costs.
          NO -> KEEP a synchronization design that preserves the shared invariant.
```

### Example: `Arc<Mutex<Model>>`

A graph of `Arc<Mutex<Model>>` is not justified because several functions want `&mut Model`. If one scheduler owns all model state, test indexed/root-owned mutation. Keep a lock when independent threads truly mutate the same contractual resource.

## Decision tree: pointer graph versus typed identity

```text
Does a long-lived relationship encode domain topology through object pointers?
  NO -> no pointer-graph finding.
  YES
    |
    |-- Is stable address identity observable/contractual?
    |     YES -> KEEP it.
    |     NO
    |
    |-- Can one owner preserve every target lifetime?
          NO -> preserve independent ownership.
          YES -> TEST typed IDs/offsets/ranges with bounds/stale-ID checks.
```

### Example: frozen graph

A snapshot-scoped immutable graph can often replace `Vec<Arc<Node>>` edges with `NodeId`. A plugin retaining a node after snapshot destruction cannot use a naked snapshot index without another lifetime protocol.

## Decision tree: foreign/native handle

```text
Does a foreign library define the handle's sharing/thread-safety contract?
  YES -> preserve that contract even if it uses Arc/Mutex internally.
  NO -> evaluate it under the ordinary ownership trees above.
```

### Example: cancellation

`Arc<NativeInterruptHandle>` can be correct when a native library requires a cloneable cross-thread cancellation handle. Do not rewrite it merely to satisfy a pointer-free aesthetic.

## Guardrails

- `&T`, `&mut T`, `&[T]`, and `&mut [T]` are normal local access tools.
- Shared immutable ownership and shared mutable ownership are different decisions.
- Sharding does not solve bandwidth saturation; use [concurrency diagnosis](../performance/40-concurrency.md) for a scaling claim.
