# YAGNI and Cleanup

Use this block to decide whether an abstraction, wrapper, framework, cache, service, registry, or generic layer has a current responsibility.

**Scope:** in focused work a supported result may preserve the existing mechanism. In broad redesign this block returns only the required responsibility/invariant. The broad target must express it with direct data/passes/ownership or an external boundary; it does not re-create an internal service/trait/wrapper mechanism.

## Decision tree: abstraction necessity

```text
For the layer/trait/wrapper/service, can you name a current responsibility for:
  ownership / lifetime / validation / authorization / transaction /
  compatibility / error translation / required polymorphism?
  YES -> preserve the responsibility. Focused work may keep the mechanism; broad redesign deletes the mechanism and expresses the responsibility in direct target data/passes/boundaries.
  NO
    |
    |-- Is the only reason future extensibility, "clean architecture",
    |   fewer lines, or possible future backends?
          YES -> REMOVE/MERGE the abstraction.
          NO/UNKNOWN -> inspect actual callers/consumers before deciding.
```

### Example: pass-through wrapper

```rust
fn plan(input: Input) -> Result<Plan> {
    self.inner.plan(input)
}
```

Remove the wrapper when it adds no validation, translation, lifetime, authorization, compatibility, or error responsibility.

## Decision tree: shared helper versus forced generic executor

```text
Do the operations share the same semantic rule/invariants?
  NO -> KEEP separate high-level operations.
  YES
    |
    |-- Can a small local helper express only the identical mechanics?
    |     YES -> extract that helper.
    |     NO
    |
    '-- Would unification require mode enums/boolean flags to recover differences?
          YES -> REJECT the generic executor.
          NO -> TEST the narrower shared abstraction.
```

### Example: mutation modes

Bad unification:

```rust
fn execute(
    mode: Mode,
    use_history: bool,
    bootstrap: bool,
    reconcile: bool,
 ) -> Result<()> { ... }
```

Prefer explicit operations and a small shared primitive:

```rust
fn apply_scd2(...) -> Result<()> { ... }
fn apply_full_replace(...) -> Result<()> { ... }
fn quote_identifier(...) -> Result<String> { ... }
```

## Decision tree: new cache/service/registry/framework

```text
Is there an existing requirement that cannot be met by current ownership/data flow?
  NO -> REJECT speculative infrastructure.
  YES
    |
    |-- Can a local helper/index/scratch/explicit owner solve the requirement?
    |     YES -> prefer the smaller mechanism.
    |     NO
    |
    '-- Does the proposed infrastructure have named consumers, lifetime,
        failure/invalidation rules, and required evidence?
          NO -> REJECT until those responsibilities exist.
          YES -> TEST it against the declared requirement/budget.
```

### Example: cache versus ownership

Bad first response:

```rust
static LOOKUP_CACHE: Mutex<HashMap<Key, Value>> = ...;
```

Candidate when the real problem is ownership:

```rust
struct Runtime {
    values: Vec<Value>,
    by_key: HashMap<Key, ValueId>,
}
```

Add retained cache state only for demonstrated repeated computation, not merely because canonical state is inconvenient to reach.

## Decision tree: apparent duplication

```text
Do two similar blocks protect different invariants, authorities, recovery points,
wire semantics, or an independent test oracle?
  YES -> preserve both invariants/authorities. Focused work may keep separate mechanisms; broad redesign expresses them directly in target passes/authorities without preserving the old layers.
  NO
    |
    |-- Is the repeated code a small identical mechanic?
          YES -> MERGE into a local helper.
          NO -> do not unify only to reduce LOC.
```

### Example: correctness boundary

```rust
claim.check_live()?;
apply_changes()?;
fence.check_current()?;
finalize()?;
```

Do not replace both checks with one early `validate_transaction()?` if authority may change between mutation and finalization.

## Decision tree: duplicate DTO/layer

```text
Does A -> B -> C inside one process cross a real boundary or add required information?
  YES -> preserve the boundary/information requirement. Focused work may keep the conversion; broad redesign keeps only a real serialization/protocol boundary and removes internal conversion layers.
  NO -> can producer/consumer share one canonical type or narrow projection?
          YES -> REMOVE/MERGE the redundant DTO layer.
          NO -> name the concrete reason before keeping it.
```

### Example: transport-like DTO

Before:

```rust
let dto1 = InternalDto::from(domain);
let dto2 = TransportLikeDto::from(dto1);
let value = DomainType2::try_from(dto2)?;
```

Candidate inside one process with no real boundary:

```rust
let value = project_required_fields(domain)?;
```

Focused work may keep a conversion when a real boundary or invariant requires it. Broad redesign may serialize only at a real external boundary; internal DTO/conversion chains are deleted.

## Guardrails

Never remove authorization, transaction/claim/lease/fence checks, upgrade migrations, wire-level validation, recovery semantics, or independent test oracles as "duplication". Use [Correctness boundaries](06-correctness-boundaries.md) when the responsibility is uncertain.
