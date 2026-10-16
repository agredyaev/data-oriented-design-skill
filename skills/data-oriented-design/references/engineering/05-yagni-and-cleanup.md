# YAGNI and Cleanup

# 6. YAGNI Rules

## Rule YAGNI-01 — No speculative infrastructure

Do not introduce new:

- runtime services;
- durable stores;
- sources of truth;
- generic backends;
- plugin systems;
- dependency-injection frameworks;
- caches;
- event buses;
- registries;
- abstraction layers;

without an existing requirement and demonstrated need.

---

## Rule YAGNI-02 — A useful responsibility does not justify a separate abstraction

Identify the required computation/invariant, then apply the [responsibility-versus-representation decision](10-oop-to-dod.md#decision-tree-responsibility-versus-representation). Compare the current layer, object or trait with a direct function/pass over explicitly owned data.

A separate abstraction survives only when the simpler target fails a named semantic, lifetime, external or correctness constraint, or a supported cost requirement. Otherwise preserve its work in the target and MERGE/REMOVE its wrapper. Existing callers, "clean architecture", future extensibility, test mocks and reduced LOC do not prove necessity.

---

## Rule YAGNI-03 — Prefer small local helpers over frameworks

If three modules repeat identifier quoting:

### Good

```rust
fn quote_identifier(input: &str) -> Result<String>
```

inside the owning crate.

### Bad

Creating:

```text
GenericNativeExecutionFramework
  + execution traits
  + mode enums
  + backend abstraction
  + dependency injection
```

to remove a few duplicated local functions.

---

## Rule YAGNI-04 — Do not unify unlike operations merely to reduce LOC

Similar syntax does not imply shared semantics.

Do not combine operations if the resulting helper requires:

```rust
fn execute(
    mode: Mode,
    use_history: bool,
    enforce_current: bool,
    bootstrap: bool,
    recovery: bool,
    ...
)
```

A helper with many mode flags often means unrelated behavior was forced together.

---

## Rule YAGNI-05 — Do not create generic graph frameworks for semantically different graphs

Model graphs, work graphs, and base/candidate mappings may share low-level representation concepts but have:

- different identities;
- different lifetimes;
- different invariants;
- different consumers.

Do not merge them into a generic graph framework solely because their storage looks similar.

---

## Rule YAGNI-06 — Do not add a cache to avoid solving an ownership problem

A cache is not a substitute for:

- a canonical representation;
- a stable typed ID;
- correct lifetime design;
- request-local scratch;
- an explicit index;
- a better processing pass.

---
# 7. Cleanup Anti-Patterns

The following are priority cleanup candidates when demonstrated in production paths.

## AP-01 — Pass-through wrappers

### Bad

```rust
fn plan(input: Input) -> Result<Plan> {
    self.inner.plan(input)
}
```

when the wrapper owns no:

- validation;
- translation;
- lifetime;
- error;
- authorization;
- transaction;
- compatibility responsibility.

---

## AP-02 — Redundant DTO conversion

### Bad

```text
DomainType
 -> InternalDto
 -> TransportLikeDto
 -> DomainType2
```

inside one process with no real boundary.

Prefer one canonical type plus narrow projections where necessary.

---

## AP-03 — Repeated parsing

Examples:

- SQL parsed twice in one compilation path;
- relation names validated then reparsed;
- retained Plan/Work JSON reparsed for each work item;
- source metadata repeatedly decoded.

---

## AP-04 — Unnecessary clones

Examples:

```rust
let copied = value.clone();
let bytes = data.to_vec();
let owned = name.to_string();
```

inside repeated loops when the callee could borrow or consume.

---

## AP-05 — Second copies of canonical graph/state

Examples:

```text
canonical graph
+ runtime graph
+ scheduler graph
+ lookup graph
```

with duplicated edges/state and no independent semantic responsibility.

Prefer indexes/projections/ranges over full copies.

---

## AP-06 — Global shared mutable state

Strong smell:

```rust
lazy_static! {
    static ref STATE: Mutex<HashMap<...>> = ...;
}
```

or globally shared caches used to coordinate ordinary domain execution.

Prefer explicit ownership passed through the execution boundary.

---

## AP-07 — Trait/object indirection with one implementation and no boundary responsibility

### Suspicious

```rust
trait PlannerBackend {
    fn plan(&self, ...);
}

struct DefaultPlanner;
```

when there is one required planner and no concrete external, runtime or independent-oracle boundary requiring substitution. A test mock alone does not justify the trait.

Do not add polymorphism "in case we need another implementation."

---

## AP-08 — Dependency injection frameworks

Prefer explicit construction:

```rust
let owners = ApplicationOwners {
    planner,
    scheduler,
    executor,
    catalog,
};
```

over a service container or registration framework.

A new DI framework is specifically contrary to the cleanup direction.

---

## AP-09 — Generic executor controlled by mode flags

### Bad

```rust
execute_mutation(
    MutationMode::Scd2,
    true,
    false,
    Bootstrap::No,
    ...
)
```

Prefer operation-specific explicit code sharing only genuinely common low-level mechanics.

---

## AP-10 — Rebuilding identical transaction-local data

Examples:

- collision-safe action names;
- quoted identifiers;
- key fragments;
- normalized names;
- bounded parameter projections.

Prepare once per transaction/request when safe.

---
