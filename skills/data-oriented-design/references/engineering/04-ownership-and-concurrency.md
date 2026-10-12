# Ownership and Concurrency

# 3. `Arc`, `Mutex`, `Rc`, and Pointer-Centric Runtime State

## Rule PTR-01 — `Arc<Mutex<T>>` is a design smell, not a blanket ban

The source policy does **not** support the rule:

> "`Arc<Mutex<T>>` is always forbidden."

The correct rule is:

> Do not model ordinary domain/runtime state as a pointer-centric graph of shared mutable objects unless a real concurrency, ownership, or foreign-library boundary requires it.

Treat this as suspicious:

```rust
Arc<Mutex<T>>
```

and require a concrete justification.

Treat this as strongly suspicious:

```rust
Arc<Mutex<HashMap<Id, Arc<Mutex<Node>>>>>
```

or:

```rust
struct Runtime {
    planner: Arc<Mutex<Planner>>,
    manifest: Arc<Mutex<Manifest>>,
    graph: Arc<Mutex<Graph>>,
    state: Arc<Mutex<State>>,
}
```

This often indicates that the data ownership and execution flow were never made explicit.

---

## Rule PTR-02 — `Mutex` must protect real concurrent mutation

Do not add a lock merely because several components want mutable access.

### Bad

```rust
struct Engine {
    manifest: Mutex<Manifest>,
}
```

when the manifest becomes immutable after startup.

### Better

```rust
struct Engine {
    manifest: Manifest,
}
```

and:

```rust
fn execute(engine: &Engine, request: &Request) -> Result<Response>
```

If immutable state is shared between threads, an `Arc<T>` may be justified depending on process/thread ownership. The lock is not.

---

## Rule PTR-03 — References and slices are not pointer-centric domain graphs

These are normal Rust tools:

```rust
&T
&mut T
&[T]
&mut [T]
```

Using references does not violate DOD.

The problem is a runtime domain model whose topology, ownership, and access pattern are primarily represented by recursively shared heap objects.

---

## Rule PTR-04 — Foreign-library/thread-safety handles are valid exceptions

Do not remove a reference-counted handle merely because it contains `Arc`.

A legitimate example is an interrupt/cancellation handle required by a foreign or native library for cross-thread cancellation.

Example:

```rust
struct NativeCancellation {
    interrupt: Arc<NativeInterruptHandle>,
}
```

This is different from:

```rust
struct Model {
    state: Arc<Mutex<ModelState>>,
}
```

The first expresses an actual external concurrency boundary.  
The second may simply hide poor ownership.

---
