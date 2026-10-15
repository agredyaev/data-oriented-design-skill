# YAGNI and Cleanup

Use this block to decide whether an abstraction, wrapper, framework, cache, service, registry, or generic layer has a current responsibility.

## Decision tree: abstraction necessity

```text
For the layer/trait/wrapper/service, can you name a current responsibility for:
  ownership / lifetime / validation / authorization / transaction /
  compatibility / error translation / required polymorphism?
  YES -> KEEP that responsibility; simplify only around it.
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

If a common `execute(mode, history, bootstrap, reconcile, ...)` needs flags to recreate distinct SCD2/full/incremental semantics, keep explicit operations and share only truly identical low-level mechanics.

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

Do not add a global cache because repeated code cannot reach canonical state conveniently. First repair ownership or add the smallest explicit index. Add retained cache state only for demonstrated repeated reuse.

## Decision tree: apparent duplication

```text
Do two similar blocks protect different invariants, authorities, recovery points,
wire semantics, or an independent test oracle?
  YES -> KEEP them separate.
  NO
    |
    |-- Is the repeated code a small identical mechanic?
          YES -> MERGE into a local helper.
          NO -> do not unify only to reduce LOC.
```

### Example: correctness boundary

A claim check before work and a fence check at finalization can look repetitive but protect different authority moments. Do not merge them into one generic validation call if that weakens the protocol.

## Decision tree: duplicate DTO/layer

```text
Does A -> B -> C inside one process cross a real boundary or add required information?
  YES -> KEEP the required conversion.
  NO -> can producer/consumer share one canonical type or narrow projection?
          YES -> REMOVE/MERGE the redundant DTO layer.
          NO -> name the concrete reason before keeping it.
```

### Example: transport-like DTO

`DomainType -> InternalDto -> TransportLikeDto -> DomainType2` has no value merely because the names describe architectural layers. Keep a conversion only when a real boundary or invariant requires it.

## Guardrails

Never remove authorization, transaction/claim/lease/fence checks, upgrade migrations, wire-level validation, recovery semantics, or independent test oracles as "duplication". Use [Correctness boundaries](06-correctness-boundaries.md) when the responsibility is uncertain.
