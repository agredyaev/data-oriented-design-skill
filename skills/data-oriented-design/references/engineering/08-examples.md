# Examples

# 12. Rust Examples

## 12.1 Shared object graph → typed IDs

### Avoid

```rust
struct Node {
    name: String,
    edges: Vec<Arc<Node>>,
}
```

### Prefer

```rust
#[repr(transparent)]
#[derive(Clone, Copy)]
struct NodeId(u32);

struct Graph {
    names: Vec<StringId>,
    offsets: Vec<u32>,
    targets: Vec<NodeId>,
}
```

---

## 12.2 Shared mutable manifest → frozen manifest

### Avoid

```rust
struct Runtime {
    manifest: Arc<Mutex<Manifest>>,
}
```

### Prefer

```rust
struct Runtime {
    manifest: Manifest,
}

impl Runtime {
    fn manifest(&self) -> &Manifest {
        &self.manifest
    }
}
```

or, when ownership really spans threads:

```rust
struct Runtime {
    manifest: Arc<Manifest>,
}
```

with no lock when the manifest is immutable.

---

## 12.3 Reparse → admit once

### Avoid

```rust
validate_identifier(raw)?;
let id = parse_identifier(raw)?;
```

### Prefer

```rust
let id = admit_identifier(raw)?;
```

where admission returns the validated typed result.

---

## 12.4 Copy → borrow

### Avoid

```rust
fn process(values: Vec<Value>) -> Result<()> {
    ...
}

process(existing_values.clone())?;
```

### Prefer

```rust
fn process(values: &[Value]) -> Result<()> {
    ...
}

process(&existing_values)?;
```

when ownership transfer is unnecessary.

---

## 12.5 Global cache → request scratch

### Avoid

```rust
struct Engine {
    cache: Arc<Mutex<HashMap<NodeId, Vec<NodeId>>>>,
}
```

### Prefer

```rust
struct TraversalScratch {
    queue: Vec<NodeId>,
    visited: Vec<u32>,
}

fn traverse(
    graph: &Graph,
    scratch: &mut TraversalScratch,
) {
    scratch.queue.clear();
    // ...
}
```

---

## 12.6 Generic mode-heavy helper → explicit operations

### Avoid

```rust
fn execute(
    mode: MutationMode,
    history: bool,
    bootstrap: bool,
    reconcile: bool,
) -> Result<()> {
    ...
}
```

### Prefer

```rust
fn execute_full(...) -> Result<()> { ... }
fn execute_incremental(...) -> Result<()> { ... }
fn execute_scd2(...) -> Result<()> { ... }
```

with a small shared helper only for mechanics that are truly identical.

---
