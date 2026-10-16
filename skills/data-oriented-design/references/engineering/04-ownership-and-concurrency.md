# Ownership and Concurrency

Use this block to decide whether sharing, reference counting, stable addresses, or synchronization have a concrete responsibility. `Arc`, `Mutex`, references, and pointers are mechanisms, not automatic defects.

**Scope:** in focused work this block may preserve an existing mechanism. In broad redesign it returns only the lifetime/concurrency/FFI requirement; [Broad redesign](../broad-redesign.md#stage-4--responsibility-transfer-and-abstraction-veto) must re-derive the target mechanism from scratch.

## Decision tree: shared ownership

```text
Is the value retained beyond one local operation?
  NO -> KEEP ordinary borrowing/local ownership if it satisfies the lifetime.
  YES
    |
    |-- Does an FFI/ABI/native API require a stable pointer or reference-counted handle?
    |     YES -> focused: KEEP that handle; broad: record the stable-handle requirement and re-derive the target carrier.
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

Focused work may keep `Arc<Manifest>` when spawned tasks genuinely need independently cloned ownership. Broad redesign records that lifetime requirement and re-derives the target ownership.

## Decision tree: `Mutex` / shared mutation

```text
Is the protected state mutated concurrently by multiple execution contexts?
  NO -> REMOVE the lock; freeze or localize the state.
  UNKNOWN -> inspect writers and lifetimes before changing it.
  YES
    |
    |-- Is it one real shared resource whose invariant spans those writers?
    |     YES -> synchronization semantics are required; focused may KEEP, broad must choose the smallest target synchronization/ownership mechanism.
    |     NO
    |
    |-- Can mutable ownership be partitioned/localized without changing semantics?
          YES -> TEST local ownership/sharding; include merge/order costs.
          NO -> focused may KEEP; broad re-derives the smallest synchronization design that preserves the invariant.
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

## Pointer-topology handoff

A long-lived domain pointer graph whose question is "pointer or typed ID/range?" belongs to [PWP retained-state decisions](compiler/profile/50-pwp-retained-state.md). This block owns whether shared ownership, locking, or a foreign/native handle is required; it does not repeat the pointer-topology decision.

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
