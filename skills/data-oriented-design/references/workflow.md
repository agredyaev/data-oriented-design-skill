# Data-Oriented Design Workflow

Use this skill as an execution procedure. Do not start from a preferred pattern such as SoA, CSR, typed IDs, caching, or a particular ownership model. Start from the operation, its contract, its data, and the work it performs.

Correctness and required behavior take precedence over cleanup and performance. A smaller implementation is preferred only when it preserves the contract. A faster or smaller implementation is accepted only when the relevant cost is measured on a matched workload.

## Terms

- **Build**: creates, admits, parses, indexes, or updates retained data.
- **Query**: reads or traverses retained data.
- **Canonical state**: the authoritative representation for identity and required output semantics.
- **Material optimization**: a change to retained representation, hot-path algorithm, allocation strategy, or ownership model intended to reduce runtime or memory cost.
- **Finding**: a demonstrated defect, unnecessary mechanism, or budget violation supported by code, tests, measurements, or explicit contract evidence.
- **Hypothesis**: a plausible issue that lacks evidence required for a finding.

Use `N` for rows or entities, `M` for another input count, `Q` for queries, `U` for updates, and `K` for returned rows. Derived counts are estimates unless measured. Do not present estimates as benchmark results.

# Execution workflow

Run the phases in order. A phase may be short, but do not skip its required output.

## Phase 0 — Classify the task

Identify every applicable class:

| Class | Typical signals | Primary rules |
| --- | --- | --- |
| Layout / retained memory | wide rows, padding, optional payloads, pointer-heavy collections, sparse fields | Performance methodology `DOD-005`–`DOD-009`, `DOD-014`–`DOD-017`, `DOD-022`–`DOD-023` |
| Hot path / repeated work | dominant scans, nested scans, repeated lookup, rebuild, parse, clone, serialization | Performance methodology `DOD-003`, `DOD-010`, `DOD-018`–`DOD-033` as applicable; engineering DATA/PERF rules |
| Ownership / concurrency | `Arc`, `Mutex`, `RwLock`, `Rc<RefCell<_>>`, shared mutable graphs, unclear owner | reference PTR/DATA rules |
| Abstraction / YAGNI | pass-through wrappers, one-implementation traits, mode-heavy helpers, DI, registries, speculative services or caches | reference YAGNI/AP rules |
| Correctness-sensitive cleanup | authorization, wire validation, transactions, claims, leases, epochs, fences, migrations, recovery, independent oracles | reference SAFE rules |
| Performance claim | proposed latency, allocation, memory, throughput, or scaling improvement | Performance methodology `DOD-012`, `DOD-030`, `DOD-031`; engineering MEASURE rules |

A task may belong to more than one class. Do not reduce a mixed problem to the easiest class.

**Required output:** the classified classes, code paths in scope, and engineering rule blocks selected from the router.

## Phase 1 — Establish the contract

Before proposing a change, record what must remain true.

Capture, when applicable:

- accepted inputs and bounds;
- identity and equality rules;
- output values and ordering;
- error and diagnostic behavior;
- authorization and security checks;
- transaction and isolation semantics;
- claim, lease, epoch, fence, readiness, and finalization semantics;
- wire-format, ABI, persistence, and migration compatibility;
- failure, retry, cancellation, and recovery behavior;
- determinism requirements;
- concurrency and thread-safety requirements;
- resource limits or explicit performance budgets.

If a required value is unknown, write `UNKNOWN`. Do not invent a bound, workload, call count, or budget.

**Stop condition:** if the proposed change could alter an unknown correctness contract, do not implement that part until the contract is recovered from code, tests, specification, or user-provided requirements. Continue with independent findings that do not depend on the unknown.

**Required output:** contract, known bounds, and unknowns.

## Phase 2 — Draw the structure and trace data/work

Before proposing any optimization, draw an ASCII structural map of the current design. The map must make objects, ownership, mutable/shared state, boundaries, and dominant data movement visible.

At minimum show:

```text
[caller]
   |
   v
[layer / object]
   |
   v
[canonical state]
   |
   +--> [index / view]
   +--> [derived state]
   |
   v
[dominant pass]
   |
   v
[output]
```

For every important node or edge, annotate both the kind of work and known scale:

```text
count | bytes | calls | allocations | pointer/ID hops
copy | lookup | hash | parse | normalize | serialize | lock |
atomic refcount | IPC | syscall | state transition | ownership transfer
```

When a quantity is unknown, mark it `?`; do not omit it merely because it has not been measured.

Also draw object/ownership structure separately when the runtime is object-heavy:

```text
Runtime
  |
  +--> Arc<ObjectA>
  |       |
  |       +--> Mutex<ObjectB>
  |               |
  |               +--> Vec<Arc<ObjectC>>
  |
  +--> Cache
```

The purpose is not documentation aesthetics. The map is a diagnostic tool for asking whether objects, wrappers, mutable authorities, and boundaries can disappear.

Trace the path from input to output:

`input → validation/admission → canonical state → indexes/views/scratch → dominant passes → output`

For each retained structure or dominant operation, record:

- who creates it;
- who owns each allocation;
- lifetime;
- mutable versus immutable phases;
- canonical versus derived data;
- identity representation;
- fields read and written by each dominant pass;
- iteration order;
- number of entities and edges where known;
- build frequency;
- query frequency;
- update frequency;
- allocations and copies in the path;
- parsing, normalization, hashing, serialization, and lookup steps;
- synchronization and cross-thread ownership;
- FFI or external-library handles;
- temporary structures that survive past their useful phase.

Prefer evidence from code, tests, profiles, allocation traces, benchmarks, and explicit repository contracts. Source inspection may establish unnecessary work or duplication without a profiler; it does not establish a speedup.

**Required output:** ASCII structural map, data-flow and ownership map, dominant iteration, boundary annotations, and known scale.

## Phase 3 — Diagnose and record findings

Inspect the current path before designing replacements.

Check at least the applicable categories:

1. repeated full scans or nested scans;
2. pointer chasing or heap-per-entity storage;
3. repeated parsing, normalization, hashing, or serialization;
4. clones, `to_vec`, `to_string`, or buffer allocation in dominant loops;
5. more than one authoritative copy of the same state;
6. build-time maps or AST structures retained into frozen runtime without a consumer;
7. shared mutable domain state used to compensate for unclear ownership;
8. global caches or registries without measured or contractual need;
9. pass-through wrappers and redundant DTO conversions;
10. one-implementation traits or generic frameworks without a boundary responsibility;
11. mode-heavy helpers combining operations with different invariants;
12. correctness checks that look duplicated but protect distinct invariants;
13. stored fields, projections, normalized values, or expanded intermediates that are deterministic and cheap enough to derive from canonical retained data.

Assign one status to each inspected issue:

- `FINDING` — evidence demonstrates the defect, unnecessary mechanism, or budget violation.
- `UNVERIFIED` — a concrete hypothesis exists, but required evidence is missing. For a DOD/layout finding, include the provisional `before → after` design required by `DOD-013` and name the missing measurement or bound.
- `NO FINDING` — the condition was checked and is acceptable.
- `N/A` — the rule does not apply; state why.

Do not hide a supported finding because the fix is invasive, conflicts with a preferred design, or shows no expected performance gain.

### Structural challenge

Before ranking or micro-tuning, answer these questions against the Phase 2 ASCII map:

1. Can this object disappear entirely?
2. Can this pointer/reference relationship become a typed ID?
3. Can this object graph become dense arrays plus IDs, offsets, or ranges?
4. Can this wrapper/layer disappear because it owns no contract responsibility?
5. Can this second representation become an index/view over canonical state instead of another copy?
6. Can this stored field or projection be derived from retained canonical data?
7. Can shared/global mutable state become operation-local scratch or immutable runtime state?
8. Can this runtime structure exist only during build/admission and be discarded at freeze?
9. Can repeated parse/normalize/hash work become admit once → typed value → propagate?
10. Can repeated lookup become resolve once → typed/dense ID?
11. Can multiple calls, passes, state transitions, IPC hops, or protocol round-trips be collapsed into one batch or pass?
12. Can hidden object choreography/callback dispatch become explicit sequential passes over data?

For every `yes`, produce a candidate that removes the mechanism rather than merely optimizing its implementation. Prefer elimination of objects, states, passes, boundaries, and retained representations over tuning them in place when behavior can remain equivalent.

**Required output:** findings with rule IDs, code locations, evidence, status, and structural-challenge answers for the dominant path.

## Phase 4 — Rank by leverage

Rank findings in this order unless the repository has a stronger explicit priority:

1. correctness or security defect;
2. removable process/API/protocol boundary, pass, state transition, or round-trip that materially contributes to the target;
3. repeated asymptotic work or unbounded resource growth;
4. repeated parsing, serialization, allocation, copying, or lookup on a dominant path;
5. unclear canonical ownership or unnecessary shared mutation;
6. duplicated or cheaply derivable retained state with unjustified lifetime;
7. representation/layout inefficiency;
8. abstraction or cleanup issues outside dominant paths.

Within the same class, prefer the change that removes more recurring work with less new state and fewer invariants. Prefer removing an object, representation, pass, state transition, synchronization point, or boundary over making that mechanism slightly cheaper when both preserve the contract.

Do not optimize a path that already satisfies its stated budget merely because a different representation is possible. Do not rank a micro-optimization above a structural simplification that removes the entire cost source.

**Required output:** ordered candidate list and the reason for the order.

## Phase 5 — Design one explicit change

For the highest-priority candidate, write the design before editing code.

Required fields:

- **Before:** current representation or execution path, including the relevant ASCII fragment.
- **After:** exact proposed representation or execution path, including the candidate ASCII fragment.
- **Removed work/state:** what disappears.
- **Added work/state:** what is introduced.
- **Ownership:** canonical owner and lifetime after the change.
- **Identity:** IDs, indexes, handles, or keys after the change.
- **Complexity:** build, query, update, output, and extra-space costs where applicable.
- **Bounds:** capacities, integer widths, sentinel values, overflow behavior.
- **Mutation effects:** insert, delete, reorder, compaction, slot reuse, invalidation.
- **Concurrency effects:** synchronization, thread ownership, cancellation, FFI handles.
- **Preserved invariants:** exact contract items from Phase 1.
- **Evidence needed:** tests and measurements required for acceptance.

Use these defaults only when the access pattern supports them:

- typed dense IDs instead of pointer identity;
- contiguous storage instead of per-entity heap allocation;
- ranges or flat adjacency for stable sequential traversal;
- explicit passes instead of hidden object choreography;
- immutable/frozen runtime state after build;
- operation-local scratch instead of shared caches;
- one canonical state plus indexes, ranges, or views;
- admitted typed values propagated instead of reparsed text;
- deterministic cheap projections derived from canonical retained data instead of stored as redundant mutable state;
- borrowing or consuming instead of cloning.

Do not force SoA, CSR, bitsets, dense indexes, interning, caches, or narrower integer widths without matching bounds and access patterns.

**Stop condition:** reject the candidate before implementation if it weakens a required invariant, introduces speculative infrastructure, or has no concrete responsibility for newly added state or abstraction.

For performance or architecture work, include at least one structural alternative from `00-structural-analysis.md` and explain why the selected design removes more recurring work/state or why no structural simplification is valid.

**Required output:** one concrete `before → after` design and the rejected structural alternatives with reasons.

## Phase 6 — Establish the baseline

Before a material implementation change:

1. run the relevant correctness tests;
2. record the current result;
3. identify the representative workload;
4. record existing latency, allocations, retained/peak memory, or update cost when the change claims to improve them;
5. record build mode, relevant environment, input size, repetitions, and cold/warm state for performance comparisons.

If no performance claim is made and the change is behavior-only or trivial, do not invent a benchmark requirement.

If a benchmark cannot be run, keep the performance benefit `UNVERIFIED`. A projected complexity improvement may justify investigation but not a measured-speed claim.

**Required output:** baseline evidence or an explicit list of unavailable measurements.

## Phase 7 — Implement narrowly

Change one dominant mechanism at a time so the result can be attributed and reverted.

During implementation:

- preserve the Phase 1 contract;
- keep canonical ownership explicit;
- keep temporary data local to its required lifetime;
- remove superseded state instead of leaving both implementations authoritative;
- do not add compatibility wrappers unless compatibility requires them;
- do not add a cache to avoid fixing ownership or repeated parsing;
- do not merge semantically different operations to reduce LOC;
- do not remove migration, wire, authority, recovery, or independent-oracle checks as duplication;
- keep foreign-library synchronization or reference counting when the boundary requires it.

Do not perform unrelated style cleanup in the same change unless needed for correctness or compilation.

**Required output:** implemented delta linked to the Phase 5 design.

## Phase 8 — Verify

Run verification in this order:

1. compile/type-check where applicable;
2. formatting/linting required by the repository;
3. focused tests for the changed path;
4. boundary and negative tests for affected invariants;
5. broader regression tests appropriate to the change;
6. matched performance measurement for a material optimization.

For representation and ID changes, include relevant cases such as:

- empty input;
- maximum valid size;
- first invalid size;
- duplicate identity;
- unknown identity;
- stale or reused slot;
- generation rollover if applicable;
- insert/delete/reorder;
- serialization round-trip or wire rejection where applicable;
- disconnected or degenerate graph;
- deterministic ordering;
- concurrent live operations where applicable.

Compare before and after on the same workload. Report both improvements and regressions.

### Escalation rule: stop micro-tuning when the target does not move

Track three levels when possible:

```text
local physical metric
    ↓
phase / component wall time
    ↓
end-to-end target metric
```

If a local change improves its own metric but the target end-to-end metric does not improve beyond measurement noise or toward the stated budget, do not keep tuning the same mechanism by default. Re-rank the system.

If two consecutive local optimizations on the same representation fail to produce a material end-to-end improvement, return to Phase 2 and redraw the structure. Re-examine:

- the canonical representation;
- object count and pointer graph;
- ownership and synchronization;
- retained derived state;
- number of passes and scans;
- state transitions;
- serialization/parsing boundaries;
- API/protocol/IPC round-trips;
- process boundaries;
- batching opportunities.

The next candidate should normally be structural: remove or collapse a representation, object layer, pass, state transition, or boundary. Continue local tuning only with evidence that the remaining component is still a material contributor to the target metric.

**Stop condition:** reject or revise the candidate if required behavior regresses, a stated resource budget is violated, the target metric does not move and the component is no longer material, or the new mechanism adds uncompensated complexity without the claimed benefit.

**Required output:** verification evidence and remaining gaps.

## Phase 9 — Decide and report

Use two independent status systems.

### Finding status

Use `FINDING`, `UNVERIFIED`, `NO FINDING`, or `N/A` for inspected rules.

### Change gates

For each proposed or implemented change, report:

| Gate | Status criteria |
| --- | --- |
| Contract | `PASS` only when affected requirements and unknowns are identified |
| Behavior and safety | `PASS` only when affected invariants have supporting tests or code evidence |
| Ownership and state | `PASS` only when canonical owner, lifetime, synchronization, and derived state are explicit |
| YAGNI and abstraction | `PASS` only when each added mechanism has a current concrete responsibility |
| Cost and bounds | `PASS` only when complexity, memory, capacity, and stated budgets are accounted for |
| Performance | `PASS` only when a material performance claim is supported by matched measurements; otherwise `NOT VERIFIED` or `N/A` |
| Verification | `PASS` only when required checks ran successfully and missing coverage is stated |

Allowed gate values:

- `PASS` — required evidence is present.
- `FAIL` — a requirement is violated; name it.
- `NOT VERIFIED` — required evidence is missing; name it.
- `N/A` — the gate does not apply; state why.

Lack of evidence is never `N/A`.

### Acceptance rules

- Correctness-sensitive change: accept only with Contract, Behavior and safety, Ownership and state, and Verification at `PASS`.
- Material optimization: additionally require Cost and bounds and Performance at `PASS`.
- Cleanup with no performance claim: Performance may be `N/A`; all affected correctness and ownership gates must still pass.
- A change with a `FAIL` gate is not accepted.
- A change with `NOT VERIFIED` may remain a proposal, but do not describe it as verified or complete.

## Output format

For review or implementation work, report in this order:

1. **Scope** — operation and files inspected.
2. **Contract** — preserved requirements, budgets, and unknowns.
3. **Current structure** — ASCII object/data-flow map with ownership, boundaries, edge work, dominant iteration, and scale.
4. **Findings** — rule ID, status, evidence, impact.
5. **Selected change** — current and candidate ASCII maps, explicit `before → after`, removed/added state and work, costs, invariants.
6. **Implementation** — files and mechanisms changed, if code was edited.
7. **Verification** — exact commands/tests/measurements and results.
8. **Gates** — status for each applicable gate.
9. **Decision** — accept, reject, or remain `UNVERIFIED`.
10. **Remaining findings** — unresolved issues in priority order.

Keep claims proportional to evidence. Report all supported failures, regressions, missing measurements, and rejected candidates. Do not replace them with a favorable summary.
