# OOP to DOD / PWP Transformation

Use this module when the requested result is a DOD/PWP redesign of an object-based subsystem. Apply it to the selected scope; a question about one field does not require a whole-system rewrite. Use [Workflow](../workflow.md) for implementation, verification and reporting.

Decisions: [responsibility versus representation](#decision-tree-responsibility-versus-representation), [domain ownership](#decision-tree-replace-domain-object-ownership), [completion](#decision-tree-declare-the-transformation-result).

## Mandatory target derivation order

After the [mandatory system-wide as-is C4](00-structural-analysis.md#mandatory-c4-as-is-preflight) has exposed current layers and wiring, establish required outputs, errors, ordering, input bounds, external interfaces, authority checks and resource lifetimes. Current architecture is evidence, never the target template.

Derive the target strictly in this order:

1. Required observable operations and effects.
2. Exact data read/written by each operation.
3. Multiplicity, traversal, ordering and access/mutation patterns.
4. Physical layout/data path: direct/streamed access, AoS/SoA, hot/cold split, sparse storage, IDs/ranges and scratch as justified.
5. Retained versus transient data; owners and lifetimes.
6. Mutation, synchronization and invalidation model.
7. Required correctness, external protocol and semantic boundaries.
8. Only then explicit passes/functions and module/type organization.

Do not name proposed Services, Repositories, DTOs, Mappers, Managers, Controllers, Factories, ViewModels or architectural interfaces before step 8. Do not carry a current element into the target unless its responsibility and separate form are independently required by the derived operation/data path. Otherwise restart from step 1.

For a structural transformation, produce [to-be C4 L2/L3 and affected L4](00-structural-analysis.md#c4-coverage-gate) only after deriving the operations/data/layout; use it to verify removal of old dependency edges, not to relabel old boxes.

Choose AoS/SoA and mutable/frozen state by real access, not fashion. Prefer root-owned stores and typed IDs/offsets/ranges for retained internal relationships; local borrows and external resource handles have distinct lifetime contracts. DOD does not mandate SoA or freezing.

### Invalid candidate gate

Treat these as **INVALID target candidates**, not merely cleanup smells: Entity → DTO → ViewModel or Row → Domain → DTO chains without independent semantics; Controller → Service → Repository delegation; pass-through managers/facades; one-implementation architectural interfaces; owned projections justified only by clean boundaries; or new layers before physical access/layout derivation.

Only a separately established external, semantic, lifetime or correctness requirement can justify a specific extra boundary. Name that requirement, its direct-data alternative and why the alternative fails. Renaming an old mechanism, existing callers or testability alone never proves necessity.

## Decision tree: responsibility versus representation

```text
What observable result/invariant does this old element provide?
  UNKNOWN -> trace callers and effects; do not conclude KEEP or REMOVE yet.
  NONE -> remove it after checking remaining consumers.
  KNOWN -> assign that responsibility to a target operation or data owner.
Does preserving that responsibility require this particular separate representation?
  NO -> merge/replace the element; preserve its computation/check at the required point.
  UNKNOWN -> construct the direct function/pass + owned-data alternative and compare.
  YES -> name the external constraint or demonstrate the alternative's violation.
Is the only evidence an existing caller, class name, injected dependency or test mock?
  YES -> insufficient: inspect the caller's required result; adapt internal callers.
Does a concrete alternative preserve behavior but its cost remain unknown?
  YES -> MEASURE the disputed cost; current architecture is not thereby proven necessary.
```

For a retained object mechanism, record only: the affected data/resource, the exact requirement, the simpler alternative, and the specific violation or matched cost evidence. “Handles validation”, “thread safe”, “used by two services” and “easier to test” do not establish why a separate object/lock/trait is needed. Relabeling an old mechanism as a new decision supplies no evidence.

### Example: validation survives, the service chain disappears

Current: `Controller → ValidationService → CommandDto → ExecutorService`, with an internal JSON encode/decode between the last two. The services have one implementation and no state or external compatibility obligation. Required behavior: reject duplicate wire keys and malformed IDs, then execute a typed command.

Target: `decode_and_admit(bytes) → AdmittedCommand → execute(command, &mut State)`. Wire checks stay in decoding; typed admission runs once. Remove the two delegation objects, redundant DTO and internal JSON round-trip. Update internal callers. Do not retain `ValidationService` merely because validation is required. Keep an externally fixed API adapter only at that external boundary if the contract requires it.

## Decision tree: replace domain object ownership

```text
Are retained relationships between domain entities, or to an external resource?
  EXTERNAL RESOURCE -> isolate its lifetime/address/thread contract at its owner.
  DOMAIN ENTITIES -> construct root-owned stores with typed relationships.
Is the domain frozen after build?
  YES -> flatten child buffers into arrays/ranges; release build-only maps.
  NO -> specify insert/update/delete/move operations and valid handle resolution.
Does required parallel work mutate this domain?
  NO -> one mutable owner or shared immutable snapshot; no per-entity locks.
  YES -> test disjoint ownership, partitioned passes or explicit ownership transfer.
Does the alternative violate a required observable concurrency/lifetime contract?
  UNKNOWN -> establish that contract; do not infer it from current Arc/Mutex usage.
  NO -> implement the data-owner alternative and remove superseded object sharing.
  YES -> isolate the necessary shared resource/operation; show why the constraint
         applies there. It does not justify a pointer graph across the whole domain.
```

Use [PWP decision details](compiler/profile/50-pwp-retained-state.md) for ranges, stale handles, derived fields and builder lifetime. A pointer exception at one boundary does not exempt unrelated retained records from this analysis.

### Example: frozen dependency graph with native cancellation

Current: `HashMap<Name, Arc<Mutex<Node>>>`; each node owns `Vec<Arc<Mutex<Node>>>` dependencies and calls `dependency.run()` recursively. Build completes before execution; nodes are immutable afterward; one request owns execution results. The native library separately requires a stable cancellation handle.

Target:

```text
Graph owner: nodes: [NodeRow], dependency_ids: [NodeId], names: NamePool
NodeRow: name_id: NameId, dependencies: Range, payload: Value
Request owner: results[], visit/order scratch
Resource owner: native cancellation handle
build/admit -> resolve dependency IDs -> freeze -> dependency-ordered evaluate -> emit
```

Preserve dependency order, duplicate/unknown-name errors and cycle behavior required by the input contract. Remove per-node locks/reference counts and nested owning dependency vectors. Release the build name map unless runtime name queries require an index. Keep the native handle's actual address/lifetime protocol at the resource owner. Report that exception explicitly; it is not a reason to keep `Arc<Mutex<Node>>`.

## Decision tree: declare the transformation result

```text
Are target operations, stores, owners and relationships concrete?
  NO -> design incomplete; a list of smells or renamed classes is not a target.
Does every required behavior map to a target operation/boundary?
  NO -> correctness gap; complete the mapping before replacement.
Do old delegation objects, duplicate stores or internal owning links remain in scope?
  YES -> have their specific necessity tests passed?
          NO -> transformation incomplete; remove/replace them or name the blocker.
          YES -> report the precise remaining constraint and its scope.
Has only a subset of the requested subsystem been transformed?
  YES -> report PARTIAL with the remaining operations/stores; do not claim full conversion.
Does the requested structural result and affected behavior verification pass?
  YES -> report the structural conversion; claim speed/memory only with matched evidence.
```

For an analysis-only task, the deliverable is the concrete target plus the old-to-target removal/replacement map, with unverified claims named. For implementation, verify the actual diff: which objects, stores, nested links and dispatch layers disappeared, and which target passes/stores replaced them. If the input already has the target organization, show that mapping and report that no structural conversion was needed; do not manufacture changes.

Inspect nested retained fields as well as top-level types. Putting the old owning object graph behind a field named `payload` or `state` does not satisfy the PWP relationship check. Distinguish logical ID-based relationships from physical storage claims: packed bytes, cache behavior and a relocatable serialized image each require their own layout/encoding evidence.

### Example: a partial conversion

Replacing `Vec<Arc<Node>>` edges with `NodeId` while retaining `Arc<Mutex<Node>>` per entity and the controller/service delegation chain fixes one relationship. If the task requested conversion of the whole subsystem, this is PARTIAL. Complete ownership and operation restructuring or identify the specific blocking requirement. A passing test suite alone does not establish DOD/PWP conversion.
