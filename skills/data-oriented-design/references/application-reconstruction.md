# Whole-Application Reconstruction

Use this block only for broad repository/application redesign. It runs before local redesign decisions. Its purpose is to reconstruct what the application does, where responsibilities live, and which connected paths should become redesign routes.

This is C4-like, not a documentation exercise. Build the map from code, manifests, process entrypoints, dependency edges, protocols, and retained state. The output exists only to drive a new target architecture.

## Current topology map

Start at deployable/process boundaries, then descend only far enough to explain computation and state.

Record:

| Level | Record |
| --- | --- |
| external system | user/service/data source and protocol |
| deployable/container | process/browser/CLI/job/library loaded independently |
| subsystem/component | code region with one runtime/build responsibility |
| code owner | crate/module/package only when it helps locate implementation |

Use one ASCII map:

```text
[Author/User]
     |
     v
[Build CLI] ---> [Sealed Artifact]
                    |       |
                    v       v
               [Web Host] [Gateway]
                    |       |
                    v       v
                [Browser] [Backend]
```

Do not infer containers from folders alone. A crate/package is not automatically an architectural boundary, and several crates in one process may be one container.

For every connection name the concrete contract: file bytes, JSON, typed call, message, Arrow stream, FFI handle, database protocol, etc.

## End-to-end execution and data paths

List the externally meaningful paths before judging local mechanisms.

For each path record:

```text
PATH P<n>: <trigger> -> <observable result>

stage
concrete input
concrete output
state read/written
identity form
parse/hash/lookup/copy/allocation/lock/dispatch work
frequency/multiplicity
boundary or same-process call
```

Example:

```text
P1 BUILD
source bytes
 -> parse
 -> validate
 -> resolve identities
 -> freeze
 -> artifact bytes

P2 REQUEST
HTTP bytes
 -> authorize
 -> direct lookup
 -> execute
 -> validated output bytes
```

Overlay data movement on topology. If the same semantic fact is represented as a string, object, DTO, ID, map key, and wire field across one path, show each transition.

## State, lifetime, and authority map

For every retained state group record:

| State | Owner | Created | Last consumer | Mutation | Authority | Relationship |
| --- | --- | --- | --- | --- | --- | --- |
| build lookup | compiler pass | admission | resolve | mutable | derived | key -> slot |
| frozen runtime | process root | boot | shutdown | immutable | canonical | slot/range |
| request scratch | request | request | response | local | none | temporary |

Mark state that crosses a phase even though its last real consumer is earlier.

Do not decide representation yet. This map establishes what must survive, not how the target should store it.

## Responsibility extraction

Separate **what must remain true** from **how the current code happens to enforce it**.

For every nontrivial current mechanism write:

| Current mechanism | Observed purpose | Required responsibility/invariant | Target carrier | Old mechanism |
| --- | --- | --- | --- | --- |
| `Arc<Mutex<State>>` | shared mutation | terminal state applied once | UNKNOWN until target ownership is designed | undecided |
| trait + implementations | backend selection | one of supported backends executes request | UNKNOWN | undecided |
| auth wrapper | access decision | authorization occurs before protected action | UNKNOWN | undecided |

Rules:

1. **No current mechanism receives KEEP status during reconstruction.**
2. A current mechanism can prove that a responsibility exists; it cannot prove that the same mechanism belongs in the target.
3. Record security, ordering, concurrency, lifetime, recovery, wire, FFI, and independent-oracle responsibilities explicitly.
4. If the responsibility disappears when the system is redesigned, prove why the underlying contract disappeared; do not silently drop it.
5. `UNKNOWN` is valid until target ownership/data flow is synthesized.

Example:

```text
CURRENT
Arc<Mutex<Model>>
  observed because scheduler and workers can reach Model

RESPONSIBILITY
updates must not race and consumers must see one coherent version

TARGET QUESTION
can one scheduler own mutation and publish frozen arrays?

YES -> responsibility preserved; Arc + Mutex deleted.
NO  -> choose the smallest synchronization mechanism that satisfies the
       remaining target concurrency model.
```

This is a quality gate against losing semantics, not a preservation gate for the old architecture.

## Redesign route portfolio

Partition the application by **connected data/state/lifetime changes**, not by files or crates.

Two findings belong to one route when changing one necessarily changes the other's canonical state, ownership, protocol, or adjacent stages. Independent paths become separate routes even when they live in the same module.

For each route write:

| Route | Current path | Target direction | Delete/replace | Code delta | Performance hypothesis | Depends on |
| --- | --- | --- | --- | --- | --- | --- |
| R1 | parse -> validate -> reparse | compile -> frozen artifact -> load | second parse/validator/runtime IR | count concrete types/functions/files; LOC only if counted | remove passes/allocations; UNVERIFIED until measured | none |
| R2 | names -> maps -> names | admit once -> dense slots -> direct arrays | internal map/string identity | mechanism counts | fewer comparisons/allocations; measure hot path | R1 schema |

### Route decision tree

```text
Does the change cross canonical state, ownership/lifetime,
a protocol boundary, or two adjacent stages?
  YES -> one broad redesign route.
  NO
    |
    |-- Can old mechanism + direct callers change without adapter,
    |   duplicate state, or neighboring redesign?
    |     YES -> focused route.
    |     NO  -> broad route.

Do several candidate routes create or mutate the same target authority?
  YES -> merge them or redesign the target ownership.
  NO  -> keep them independently implementable.
```

Code reduction is estimated from concrete mechanism removal:

```text
current -> target:
production crates/modules
retained representations
traits/dynamic-dispatch points
maps/indexes
locks/shared owners
conversions/adapters
full passes
protocols/serializations
production types/functions
```

Approximate LOC may be reported only after naming files/types to add and delete. Do not invent a percentage from architectural taste.

Performance prediction must name eliminated work and frequency:

```text
remove parse O(bytes) once per boot
remove map lookup O(log N) per query transition
remove allocation per request
replace pointer traversal with contiguous slot access
```

These are hypotheses. Runtime improvement remains `UNVERIFIED` until matched measurement.

## Global target architecture

Before implementing any route, draw one target topology and place every route into it.

```text
               BUILD
source -> parse/validate/resolve -> FROZEN ARTIFACT
                                  /           \
                                 v             v
                              runtime A     runtime B
                                 |             |
                           direct data      boundary I/O
```

The target must answer:

- which deployables/containers remain;
- where mutable ownership lives;
- where data freezes;
- which identities are external versus internal;
- which representation is canonical at each lifetime;
- which boundaries serialize;
- which responsibilities cross boundaries;
- which routes delete old mechanisms rather than wrap them.

Prefer subsystem boundaries that match real process/security/lifetime boundaries. Do not preserve a crate/service/interface boundary merely because it exists today.

## Reconstruction gate

Do not start route implementation until all hold:

- every production subsystem is mapped to target, deletion, or an unchanged external boundary;
- every externally meaningful path has a current and target route;
- every required responsibility has a named target carrier or is explicitly `UNKNOWN`;
- no current mechanism is marked KEEP merely because it currently carries a required responsibility;
- each target canonical state has one authority/owner;
- route outputs compose into one global target architecture;
- no route requires a permanent old↔new adapter, dual canonical state, or synchronization bridge;
- code-reduction estimates name concrete mechanisms;
- performance estimates name removed work and remain `UNVERIFIED` until measured.

After this gate, apply the broad route to each route in dependency order.
