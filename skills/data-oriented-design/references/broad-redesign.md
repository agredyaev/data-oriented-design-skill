# Broad Redesign: Existing Repo → Flat Target → Tune

Use this route for repository/module redesign, especially over-abstracted OOP code. This file owns the broad sequence. Other references are detail blocks selected by a gate below; do not compose another workflow around it.

The goal is not cleaner classes. Reconstruct the required computation, synthesize a smaller data-oriented target, implement it directly, delete superseded architecture, then tune measured costs.

## Required end state

A broad redesign is not complete until all applicable conditions hold:

- current input→output computation and retained state are understood;
- target passes/read-write sets are synthesized without old class boundaries;
- build-only, canonical retained, derived, and request-local data are separated;
- every surviving/new abstraction has a current responsibility;
- every retained representation/index has an owner, lifetime, and consumer;
- superseded internal production paths/state are deleted;
- no old/new shadow architecture or synchronization bridge remains;
- correctness gates pass;
- performance claims have matched evidence;
- 512 techniques are used only when the byte/frontend gate selects them.

Do not stop at `Class -> Row + IDs`. That can be an intermediate step, not the broad result.

## Stage 1 — Reconstruct current system

Trace the affected path from external input to required output. Do not infer the real design from class names.

For each operation record:

```text
operation
input/output concrete types
iterated set / multiplicity
retained state read
retained state written
parse/hash/lookup/copy/allocation/lock/dispatch/boundary work
```

For each retained structure record owner, lifetime, authority, mutation, relationship form, and consumers.

Inventory mechanisms that create code/state:

```text
service/manager/repository/factory/provider
trait/interface + implementations
DTO/conversion layer
wrapper/adapter/facade
registry/event bus
cache/index
shared mutable owner / Arc<Mutex<_>>
dynamic dispatch
persistent representation
full-input pass
serialization/protocol boundary
```

Unknown facts stay `UNKNOWN`. Inspect callers/lifetimes before removal.

## Stage 2 — Synthesize required work with the old architecture erased

Keep external contracts and correctness boundaries. Mentally discard internal services/classes/managers/DTOs and write the smallest computation that produces the required output.

Build a pass/access matrix:

| Pass | Iterates | Reads | Writes/produces | Lifetime |
| --- | --- | --- | --- | --- |
| admit | input | source bytes | admitted values | build/request |
| resolve | raw relations | admitted IDs, lookup | typed relations | build |
| schedule | active IDs | status, relation ranges | ready IDs | pass-local |
| execute | ready IDs | actions | output | request |

Rules:

1. A pass exists only for required transformation, ordering, correctness, or measured locality.
2. A pass names concrete input/output data, not "service", "manager", or "processor".
3. If the pass graph reproduces the old service call graph, redo it from the contract.
4. Merge producer→consumer stages when no independent consumer/boundary requires the intermediate.
5. Do not add an abstraction to make the old architecture easier to migrate.

Example slop input:

```text
Controller -> IService -> ServiceImpl -> Repository
           -> Mapper -> RuntimeModel -> SchedulerModel -> Executor
```

Possible required work:

```text
admit(input) -> names[], raw_edges[]
resolve(names[], raw_edges[]) -> dependency_ids[]
schedule(status[], dependency_ids[]) -> ready_ids[]
execute(ready_ids[], actions[]) -> output
```

Choose storage from these access patterns next.

## Stage 3 — Build the flat DOD/PWP state

Partition state by lifetime:

```text
admission/build-only
retained canonical/frozen
derived/index
pass/request-local scratch
output
```

Derive layout from the pass/access matrix:

- whole-record consumption together → AoS may be correct;
- stable field subsets → test SoA or hot/cold split;
- variable relations → flat side arrays + offsets/ranges when mutation permits;
- long-lived domain relationships → typed IDs/offsets when one owner can preserve lifetime;
- deterministic fields → derive when exact inputs survive and read budget permits;
- builder maps/AST/growth machinery → remove after last consumer;
- temporary queues/visited sets/buffers → local scratch unless reuse is measured and lifecycle explicit;
- repeated identity parse/normalize → admit/resolve once and propagate typed identity;
- shared mutable state → localize/partition unless a real concurrent invariant requires it.

Use [PWP retained-state decisions](engineering/compiler/profile/50-pwp-retained-state.md) when ownership/lifetime/derived-state details decide the branch. Use [Data shape](engineering/01-data-shape.md) for AoS/SoA/relations.

### Reject pointerless OOP

This is not sufficient by itself:

```rust
struct ModelRow {
    name: NameId,
    status: Status,
    action: Action,
    dependencies: Range<u32>,
}
struct Runtime { models: Vec<ModelRow> }
```

If scheduling reads `status + dependencies` and execution reads `actions`, derive data groups from those access sets:

```rust
struct Runtime {
    names: Vec<NameId>,
    status: Vec<Status>,
    actions: Vec<Action>,
    dependency_offsets: Vec<u32>,
    dependency_ids: Vec<ModelId>,
}
```

This layout is selected only when the access matrix supports it.

## Stage 4 — Abstraction veto

Every new or surviving nontrivial abstraction must pass:

```text
Does it protect an external/wire/FFI boundary,
correctness/authority boundary,
ownership/lifetime boundary,
required current polymorphism,
or independent oracle?
  YES -> KEEP only that responsibility.
  NO
    |
    |-- Can plain data + a direct function express the work?
    |     YES -> REMOVE/REJECT abstraction.
    |     NO
    |
    '-- Another concrete current responsibility?
          UNKNOWN -> inspect consumers.
          NO -> REMOVE/REJECT.
          YES -> name it.
```

Additional gates:

- One internal implementation behind a trait/interface is rejected unless an external contract, real generic requirement, or independent oracle requires it.
- A cache/index needs a repeated consumer plus build/update/invalidation/lifetime rules.
- An adapter used only for old-internal-model ↔ new-internal-model is temporary and cannot survive completion.
- "clean architecture", testability alone, future backends, consistency, extensibility, or possible reuse are not sufficient.
- Zero-cost semantic types such as distinct typed IDs are allowed when they enforce a real invariant.

Treat `Service`, `Manager`, `Repository`, `Factory`, `Provider`, `Strategy`, `Context`, `Coordinator`, `Registry`, `Adapter`, `Facade`, `Builder`, `Box<dyn _>`, and `Arc<Mutex<_>>` as review signals, not automatic defects. They must pass the tree.

Use [YAGNI and cleanup](engineering/05-yagni-and-cleanup.md) for detail.

## Stage 5 — Anti-slop gate before coding

Do not write production code until target passes, storage, and deletion plan are concrete.

Compare current → target mechanism counts where relevant:

```text
full passes
persistent representations
object/pointer ownership layers
traits/dynamic-dispatch points
wrappers/adapters/DTO conversions
caches/indexes
shared mutable containers
serialization/protocol boundaries
per-entity allocations
```

Before implementation name:

```text
ADD: exact target data types/functions/passes
CHANGE: exact callers/boundaries
DELETE: old types/services/wrappers/state/paths made obsolete
KEEP: unavoidable boundaries with reason
```

Reject before coding when:

- candidate is mostly additive and leaves old internal architecture intact;
- new services/interfaces/wrappers only organize the rewrite;
- duplicate canonical old/new state remains;
- permanent synchronization between old/new models is required;
- no obsolete mechanisms can be named for deletion;
- increased architectural mechanisms lack contract requirement or measured cause.

Line count is not the sole metric, but a broad redesign that mostly adds production code without deleting obsolete mechanisms has failed this gate.

## Stage 6 — Implement vertical replacement slices

Lock the end-state design before broad code generation. Implement direct target code, not scaffolding for hypothetical variants.

For each slice:

1. choose one input→output path or retained-state responsibility;
2. implement target plain data/functions;
3. move the real caller directly to the target;
4. delete superseded internal path/state in the same slice;
5. run affected correctness tests;
6. continue only when duplicate authority is gone.

Do not create a shadow architecture beside the old one. Do not add an internal compatibility layer merely to avoid changing callers.

If a temporary bridge is unavoidable for intermediate compilation, mark it temporary, route no new behavior through it, and delete it before completion. A broad redesign cannot finish with migration adapters, dual state, or two production paths.

Extract helpers only from concrete duplicated target mechanics; do not pre-build frameworks.

## Stage 7 — Profile and tune

When performance is in scope, measure the current representative workload before replacement when feasible. After the structural target passes behavior checks, measure/profile the new design again: the dominant cost may have moved.

Use [Performance diagnosis](performance/00-diagnosis.md) when attribution is missing. With a trustworthy profile, go directly to the selected rule family.

Tune in this order unless evidence selects otherwise:

```text
remove unnecessary work/state
remove repeated passes/parse/resolve
reduce data touched / improve layout
improve locality/access order
remove allocation/copy churn
reduce branch/classification cost
batch/vectorize
partition concurrency
```

For each change:

```text
hotspot/evidence -> hypothesis -> smallest causal change
-> correctness -> matched measurement -> reprofile/rerank
```

Do not infer end-to-end speed from fewer allocations, smaller structs, or a faster microbenchmark. After two consecutive changes on one representation fail the target, return to structural design instead of generating more tuning code.

## Stage 8 — 512 gate

512 is a specialized wide-frontend technique, not a general DOD target.

```text
Does the selected hot operation process source bytes for
classification, lexical boundaries, mask/event extraction,
operator/keyword lookup, or token-stream construction?
  NO -> do not use the 512 profile.
  YES
    |
    |-- Are grammar/boundary/carry/tail semantics known?
    |     NO -> establish them first.
    |     YES
    |
    '-- Does task/evidence justify a wide logical batch?
          NO -> keep simpler width/path.
          YES -> evaluate PWP/512 profile.
```

Use [PWP / 512 Decision Router](engineering/compiler/25-pwp-512-profile.md). A selected 512-byte contract is logical source width with 8×u64 masks where applicable; it does not require AVX-512.

After a 512 change, verify parity, measure the predicted local metric, then remeasure the declared target and reprofile.

## Completion gate

Return `NOT DONE` when any applicable item fails:

- target passes/storage are still organized around old classes without access justification;
- a surviving/new abstraction lacks a named current responsibility;
- duplicate old/new canonical state remains;
- an internal migration adapter/shadow production path remains;
- build-only state survives without a runtime consumer;
- temporary state became retained/global without evidence;
- superseded code is still reachable in production;
- required correctness boundaries/tests fail;
- claimed performance result lacks matched evidence;
- 512 was selected without the byte/frontend gate.

A successful redesign is a small set of explicit passes over necessary data plus unavoidable boundaries. If it needs the old service/class hierarchy to explain it, it is not finished.

## Compact result

Report only:

1. **Current** — typed pipeline, retained-state/mechanism inventory, measured costs if available.
2. **Target** — exact passes, access matrix, flat state, unavoidable boundaries.
3. **Delete / Keep** — obsolete mechanisms; retained abstractions with one-line responsibility.
4. **Implementation delta** — direct slices/tests; no shadow architecture.
5. **Performance** — baseline/profile, causal changes, matched results; 512 decision when applicable.
6. **Unknowns** — only facts blocking a decision.
