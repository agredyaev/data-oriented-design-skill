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

Before when no independent owner is required:

```rust
struct Engine {
    manifest: Arc<Manifest>,
}
```

Candidate:

```rust
struct Engine {
    manifest: Manifest,
}

fn execute(engine: &Engine, request: &Request) -> Result<Response> { ... }
```

Keep `Arc<Manifest>` when spawned tasks genuinely need independently cloned ownership.

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

Before:

```rust
struct Runtime {
    models: HashMap<ModelId, Arc<Mutex<Model>>>,
}
```

Candidate when one scheduler owns mutation:

```rust
struct Runtime {
    models: Vec<Model>,
}

fn update(rt: &mut Runtime, id: ModelId) {
    let model = &mut rt.models[id.0 as usize];
    // mutate under the scheduler's exclusive ownership
}
```

Keep a lock when independent threads truly mutate the same contractual resource.

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

Before:

```rust
struct Node {
    edges: Vec<Arc<Node>>,
}
```

Candidate for one snapshot-owned graph:

```rust
struct NodeId(u32);
struct Node { edges: Range<u32> }
struct Graph { nodes: Vec<Node>, edge_ids: Vec<NodeId> }
```

A plugin retaining a node after snapshot destruction cannot use a naked snapshot index without another lifetime protocol.

## Decision tree: foreign/native handle

```text
Does a foreign library define the handle's sharing/thread-safety contract?
  YES -> preserve that contract even if it uses Arc/Mutex internally.
  NO -> evaluate it under the ordinary ownership trees above.
```

### Example: cancellation

```rust
struct NativeCancellation {
    interrupt: Arc<NativeInterruptHandle>,
}
```

Keep this when the native API requires a cloneable cross-thread handle. Do not rewrite it merely to satisfy a pointer-free aesthetic.

## Guardrails

- `&T`, `&mut T`, `&[T]`, and `&mut [T]` are normal local access tools.
- Shared immutable ownership and shared mutable ownership are different decisions.
- Sharding does not solve bandwidth saturation; use [concurrency diagnosis](../performance/40-concurrency.md) for a scaling claim.
