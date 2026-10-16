# Broad Redesign: Existing Repo → Flat Target → Tune

Use this route for repository/module redesign, especially over-abstracted OOP code. This file owns the broad sequence. Other references are detail blocks selected by a gate below; do not compose another workflow around it.

The goal is not cleaner classes. **Existing internal architecture has zero preservation value.** Reconstruct the required computation from external contracts and required invariants, synthesize a new DOD/PWP target, implement it directly, delete superseded architecture, then tune measured costs.

## Stage 0 — Reconstruct the whole application

For broad repository/application redesign, first use [Whole-application reconstruction](application-reconstruction.md). Build the current topology, end-to-end execution/data paths, state/lifetime/authority map, responsibility ledger, redesign route portfolio, and one global target architecture.

Do this before judging local mechanisms. The current code is evidence of responsibilities, not the target design.

Hard rules:

- **No current mechanism receives KEEP status during reconstruction.** Current internal mechanisms are witnesses to requirements, not target candidates.
- Extract the required responsibility from `Arc`, `Mutex`, traits, services, wrappers, security seams, caches, and DTOs; do not preserve the mechanism by default.
- Build one global target architecture before implementing any route.
- Apply the classifier below to each discovered route. It chooses route scope; it does not decide which current mechanisms survive.

## Route classifier: focused fix or broad redesign

Do not classify from names such as `Service`, `Manager`, `Repository`, `Factory`, `Arc`, or `Mutex`. Match only code-level signatures.

| ID | Match only when all conditions hold |
| --- | --- |
| S1 PASS_THROUGH_LAYER | an internal method adds no state transition, validation, boundary, or error translation and only forwards arguments/result to one next internal call |
| S2 SINGLE_IMPL_INTERFACE | an internal trait/interface has one production implementation and no external plugin, independent oracle, or actual generic requirement |
| S3 FIELD_COPY_REPRESENTATION | two retained internal types represent the same identity/version; conversion is field-copy or lossless projection; no independent authority/history/boundary requires both |
| S4 TRANSIENT_INTERMEDIATE | A→B→C; B has no consumer except producing C and adds no validation, authority, wire, ordering, or recovery boundary |
| S5 REPEATED_IDENTITY_WORK | the same admitted identity/version is parsed, normalized, hashed, or key-looked-up again downstream |
| S6 ROOT_DOMINATES_OWNERSHIP | one root outlives every consumer, yet retained domain relations use reference counting/pointers; no stable-address or independent-lifetime contract exists |
| S7 SERIALIZED_SHARED_MUTATION | a lock protects domain state although code proves one executor is the only writer or all writes finish before freeze |
| S8 PHASE_LEAKED_STATE | a field/map/buffer is written in one phase and has no read after that phase, or is copied into longer-lived state only for convenience |
| S9 PASS_FIELD_SPLIT | two recurring passes iterate the same entity collection but read different stable field sets, and no recurring pass requires the whole entity |
| S10 MODE_RECONSTRUCTION | one generic executor takes mode/boolean switches whose branches recreate distinct operations or invariants |
| S11 CLOSED_WORLD_DISPATCH | all production implementations are known at build time; no runtime/plugin/ABI implementation loading exists; selection comes from a closed tag/config; callers need behavior selection rather than open extension |

For every match, record exact code locations and the fact satisfying each condition. No evidence → no match. The classifier chooses focused versus broad scope only; **it never grants KEEP status to the matched current mechanism.**

### Route decision

```text
Can the selected mechanism be removed/replaced by changing it and direct callers
WITHOUT:
  adapter/wrapper between old and new internal forms,
  duplicate canonical state,
  synchronization between old and new representations,
  changing neighboring retained-data ownership/lifetime,
  or changing two or more adjacent pipeline stages?
  YES -> focused route.
  NO  -> BROAD REDESIGN.

Would a proposed local fix add an adapter, duplicate retained state,
or compatibility service solely to preserve the current internal architecture?
  YES -> BROAD REDESIGN immediately.

Do two or more matched signatures share the same retained state or adjacent stages,
so fixing one necessarily changes the other?
  YES -> BROAD REDESIGN.

Are several matches independent and removable without those effects?
  YES -> keep them focused; count alone does not justify broad scope.
```

### Worked classification

```text
Controller -> IService -> ServiceImpl -> Repository interface
           -> RepositoryImpl -> DomainModel -> Mapper
           -> RuntimeModel -> Scheduler
```

If inspection proves: one production `IService` implementation (S2), `ServiceImpl::run` only forwards (S1), `DomainModel -> RuntimeModel` is a retained field-copy (S3), and one scheduler is the only writer behind a lock (S7), then S3 and S7 share the same retained state and ownership. Route: **BROAD REDESIGN**.

Counterexample: `HTTP handler -> AuthorizationBoundary -> domain function`. Authorization is a distinct security responsibility, so S1 does not match. Record authorization timing/authority as a required responsibility; the target may still replace the wrapper with a direct boundary function or another simpler carrier.

Closed-world example: `trait LanguagePack` with only build-time-known packs selected by a persisted closed tag matches S11; target candidate is enum/direct dispatch. Do not match S11 when third-party/runtime implementations, ABI plugins, or another genuinely open implementation contract can appear.

## Required end state

A broad redesign is not complete until all applicable conditions hold:

- current input→output computation and retained state are understood;
- target passes/read-write sets are synthesized without old class boundaries;
- build-only, canonical retained, derived, and request-local data are separated;
- every required responsibility is carried by explicit target data/passes/ownership or an unchanged external boundary; old internal mechanisms do not survive;
- every retained representation/index has an owner, lifetime, and consumer;
- superseded internal production paths/state are deleted;
- no old/new shadow architecture or synchronization bridge remains;
- correctness gates pass;
- performance claims have matched evidence;
- 512 techniques are used only when the byte/frontend gate selects them.

Do not stop at `Class -> Row + IDs`. That can be an intermediate step, not the broad result. The final target must be explainable without referring to the old class/service/repository/interface hierarchy; if a target element exists because "the old system had X", redesign is incomplete.

## Stage 1 — Reconstruct the selected route

Use the route selected in Stage 0 and trace it from route input to required output. Do not infer the real design from class names. Whole-application topology is already established; this stage adds route-level concrete types and work.

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

When the route contains per-element boundary calls, known keys resolved one by one, source-index/input-back-reference plans, wide-before-select loading, or persisted temporary graphs, use [Pipeline materialization](engineering/11-pipeline-materialization.md).

## Stage 2 — Synthesize required work with the old architecture erased

Keep external contracts and proven correctness invariants. Treat every current internal service/class/manager/repository/trait/DTO/ownership mechanism as unavailable while synthesizing the target. Write the smallest computation that produces the required output.

Build a pass/access matrix:

| Pass | Iterates | Reads | Writes/produces | Lifetime |
| --- | --- | --- | --- | --- |
| admit | input | source bytes | admitted values | build/request |
| resolve | raw relations | admitted IDs, lookup | typed relations | build |
| schedule | active IDs | status, relation ranges | ready IDs | pass-local |
| execute | ready IDs | actions | output | request |

Default target shape:

```text
concrete data
+ direct functions/passes
+ explicit owner
+ explicit lifetime
+ explicit external boundary I/O
```

Internal architecture beyond this default is not an alternative target. If a requirement appears to need shared mutable domain ownership, dynamic-dispatch hierarchy, service/repository indirection, or an internal adapter graph, redesign ownership, phase boundaries, data placement, or dispatch until that need disappears. Only an immutable external protocol/ABI/native constraint may remain at the boundary.

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

- sequential use of most/all fields does not force AoS; compare AoS and aligned SoA/grouped layouts from padding, stream count, encoding, other passes, and measured cache/TLB behavior;
- stable field subsets → test SoA or hot/cold split;
- variable relations → flat side arrays + offsets/ranges when mutation permits;
- long-lived domain relationships → typed IDs/offsets when one owner can preserve lifetime;
- deterministic fields → derive when exact inputs survive and read budget permits;
- builder maps/AST/growth machinery → remove after last consumer;
- temporary queues/visited sets/buffers → local scratch unless reuse is measured and lifecycle explicit;
- repeated identity parse/normalize → admit/resolve once and propagate typed identity;
- shared mutable state → localize/partition unless a real concurrent invariant requires it.

Use [PWP retained-state decisions](engineering/compiler/profile/50-pwp-retained-state.md) for pointer/child/builder lifetime decisions, [Canonical and derived](engineering/02-canonical-and-derived.md) for store/derive authority, and [Data shape](engineering/01-data-shape.md) to route layout questions. Use [General SIMD](engineering/10-simd-and-dense-processing.md) only after identity/layout are selected and a non-512 vector candidate remains.

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

## Stage 4 — Responsibility transfer and internal-architecture prohibition

For every old mechanism, transfer only the required responsibility into the target design. **Preserve the responsibility, never the internal mechanism.**

```text
What exact externally observable requirement or correctness invariant
would be lost if the old mechanism disappeared?

  NONE -> DELETE it.
  UNKNOWN -> inspect consumers/authority/lifetime before coding.
  REQUIRED
    |
    '-- Re-express that requirement using:
          concrete data
          direct passes/functions
          one explicit owner per mutable state
          phase-local/build-local scratch
          immutable/frozen retained state
          typed IDs/ranges for relations
          closed direct/enum dispatch
          explicit external boundary I/O

        If this cannot be done yet:
          -> redesign ownership / phase split / data placement / work partitioning.
          -> do NOT fall back to the old internal mechanism family.
```

### Forbidden internal target mechanisms

A completed broad target must not contain these as domain/application architecture:

```text
Service / Manager / Repository / Provider / Coordinator
Factory / Facade / internal Adapter / Context object
internal trait/interface hierarchy or dyn dispatch
Arc/Rc ownership of domain state
Mutex/RwLock around domain state
retained pointer/object graph
registry/event bus used for internal indirection
cache used to compensate for inaccessible canonical state
DTO/conversion chains inside one process
shared mutable domain context
```

If any appears necessary, the redesign is **NOT DONE**. Return to Stage 2/3 and change ownership, lifetime, data placement, phase boundaries, or direct caller relationships.

Examples:

- `Arc<Mutex<T>>` reveals a concurrency requirement. Target response: assign mutation to one owner, partition state, or communicate immutable/owned messages. Shared mutable domain ownership is not an allowed broad-target fallback. Do not replace it with another shared-mutable domain wrapper.
- a trait with known implementations reveals behavior selection. Target response: closed enum/direct dispatch or separate concrete passes. Do not preserve internal dynamic dispatch.
- a repository/service layer reveals persistence/business work. Target response: direct typed boundary functions plus concrete computation passes. Do not recreate the layer under a new name.
- an authorization wrapper reveals an ordering/authority invariant. Target response: keep the check at the external boundary or direct operation entry; the wrapper object is deleted.

### External boundary exception

An **opaque external constraint** may expose a native/OS/FFI/plugin/wire handle with mandatory ownership or synchronization semantics. Preserve that external contract exactly, but isolate it at the boundary:

```text
external opaque handle/protocol
        |
        v
thin boundary function
        |
        v
owned DOD/PWP data
```

The exception does not permit `Arc<Mutex<DomainState>>`, internal service hierarchies, or dyn-dispatch architecture. If the external API itself returns a reference-counted/native handle, that handle remains boundary data; it must not determine internal domain ownership.

A rationale of "the old system had X", "this layer is conventional", "testability", "clean architecture", or "future flexibility" fails the gate.

Additional gates:

- Internal trait/interface hierarchies and dyn dispatch are not broad-target architecture. Closed implementations use direct/enum dispatch. A true external plugin/ABI contract remains only at the boundary and must not shape internal domain ownership.
- A cache/index needs a repeated consumer plus build/update/invalidation/lifetime rules and must not compensate for inaccessible canonical state.
- An adapter used only for old-internal-model ↔ new-internal-model is temporary and cannot survive completion.
- Zero-cost semantic types such as distinct typed IDs are allowed when they enforce a real invariant.

Use [YAGNI and cleanup](engineering/05-yagni-and-cleanup.md) only to extract responsibilities; broad-target mechanism policy is defined here.


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
RESPONSIBILITIES: invariants/lifetimes/security/concurrency carried into target
EXTERNAL EXCEPTIONS: only unavoidable protocol/ABI/native constraints isolated at the boundary
```

Also report current→target mechanism counts and a concrete code-size estimate from named files/types where possible. Performance estimates must name removed work and stay `UNVERIFIED` until measured.

Reject before coding when:

- candidate is mostly additive and leaves old internal architecture intact;
- new services/interfaces/wrappers only organize the rewrite;
- duplicate canonical old/new state remains;
- permanent synchronization between old/new models is required;
- no obsolete mechanisms can be named for deletion;
- increased architectural mechanisms lack contract requirement or measured cause;
- any forbidden internal target mechanism remains anywhere in the application/domain architecture.

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
batch/vectorize non-lexical work via [General SIMD](engineering/10-simd-and-dense-processing.md); byte/lexical work continues to Stage 8
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
- a forbidden internal target mechanism remains;
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
3. **Delete / External exceptions** — obsolete internal mechanisms; only unavoidable protocol/ABI/native constraints isolated at external boundaries.
4. **Implementation delta** — direct slices/tests; no shadow architecture.
5. **Performance** — baseline/profile, causal changes, matched results; 512 decision when applicable.
6. **Unknowns** — only facts blocking a decision.
