# DOD / YAGNI Engineering Rules

Use this file as a router. The detailed rules are split by concern so only the relevant blocks need to be loaded after task classification.

## Core direction

1. **Flatten runtime data before adding object structure.** Prefer explicit data layouts over graphs of heap objects, wrappers, callbacks, and shared mutable objects when the workload can be represented directly.
2. **Use one canonical representation.** Additional structures should be indexes, ranges, views, side tables, or scratch with a concrete consumer and lifetime—not second authorities.
3. **Prefer dense typed identity when the domain allows it.** Stable bounded entities are usually cheaper to traverse as typed IDs into contiguous arrays than as pointer-linked objects or repeated string keys.
4. **Prefer contiguous, address-independent data and explicit passes.** Arrays, slices, ranges, offsets, typed IDs, and flat adjacency make iteration, mutation, ownership, and cost visible. For frozen bounded domains, prefer records whose relationships do not depend on raw memory addresses when the contract allows it. Use SoA, CSR, bitsets, or dense indexes only when the access pattern and bounds justify them.
5. **Use CPU work to avoid unnecessary retained memory when the trade-off is favorable.** Cheap deterministic recomputation can be better than loading, invalidating, and synchronizing stored derived state; decide from the access pattern and budget.
6. **Derive instead of retain when derivation is deterministic and cheap enough.** Do not store a field, projection, normalized value, or expanded intermediate merely because it can be stored. Keep the canonical inputs and calculate the value at use time when this reduces retained state without violating a latency budget or snapshot semantics.
7. **Admit once and propagate typed data.** Avoid repeated parsing, normalization, hashing, serialization round-trips, and string reconstruction when a validated typed representation already exists.
8. **Keep temporary work temporary.** Build-time maps, parser structures, lookup tables, and request scratch may be appropriate; do not let them become permanent runtime state without a concrete runtime consumer.
9. **Remove abstraction that owns no responsibility.** Pass-through wrappers, redundant DTO conversions, one-implementation traits, mode-heavy generic executors, DI containers, speculative registries, services, and caches require a current concrete responsibility.
10. **Correctness overrides simplification.** Authorization, wire validation, transaction and authority checks, migrations, recovery semantics, determinism, and independent test oracles are not removable merely because they look duplicated.
11. **Remove structure before tuning structure.** When equivalent behavior permits it, prefer eliminating an object, wrapper, retained representation, pass, state transition, synchronization point, or round-trip over making that mechanism slightly cheaper.
12. **Measure material optimization claims.** A simpler representation may be selected from code evidence; a runtime or memory improvement is accepted only with the evidence required by the workload and stated budget.
13. **Escalate when local tuning does not move the target.** If local metrics improve without a material end-to-end effect, return to the structural map and challenge representation, ownership, passes, state transitions, and boundaries before continuing micro-tuning.

## Foundational transformation checklist

Before adding abstractions, test whether the current representation can be simplified as follows:

| Current shape | Candidate flat shape |
| --- | --- |
| domain-object pointer/reference | typed ID, handle, offset, or dense index |
| per-object child list | one flat child array plus `offset/length` or offsets table |
| repeated owned strings | one byte pool plus interned offset/ID |
| boolean/state stored in every row | out-of-band column, partition, bitset, or encoded tag when justified |
| AoS where hot passes read only a subset | SoA or hot/cold split |
| sparse optional payload in every row | present-only side array or sparse map keyed by typed ID |
| subclass/object polymorphism | tag/encoding plus common columns and present-only variant payloads |
| stored deterministic projection | derive from canonical state when the cost fits the budget |
| build-time map/AST retained at runtime | freeze to arrays/IDs/ranges and discard build structures |
| repeated lookup/parse/normalize | resolve/admit once and propagate the typed result |

These are candidates, not mandatory target shapes. Select them from identity density, access pattern, mutation pattern, lifetime, bounds, and measured cost.

## Store or derive

Default to **derive** when all of these hold:

- the value is a deterministic function of retained canonical data;
- the required inputs remain available for the value's lifetime;
- derivation cost fits the read-path budget;
- the value does not need independent snapshot/history semantics;
- removing the stored copy reduces state, invalidation, synchronization, or update work.

Keep the value **stored** when at least one of these holds:

- it is authoritative rather than derived;
- an external wire, ABI, persistence, or compatibility contract requires it;
- derivation would violate a measured latency or resource budget;
- required derivation inputs are intentionally discarded;
- the value must preserve historical/snapshot state independently of its current inputs.

Do not store and derive the same semantic value as two mutable authorities.

## Load rules by problem

For non-trivial architecture/performance work, follow [Workflow](workflow.md) and use [Structural analysis](engineering/00-structural-analysis.md) for typed maps, structural alternatives, allocation-shape analysis, and escalation after ineffective tuning. For a focused question, load only the matching block below.

| Problem class | Read |
| --- | --- |
| Broad structural redesign or a shared cause across hotspots | [Structural analysis](engineering/00-structural-analysis.md) |
| Object graphs, dense arrays, typed IDs, contiguous storage, flat adjacency, builder→runtime shape | [Data shape](engineering/01-data-shape.md) |
| Canonical state, derive-vs-store, repeated normalization/parsing, duplicated representations | [Canonical and derived data](engineering/02-canonical-and-derived.md) |
| Repeated scans, clones, allocations, intermediate caching, operation-local reuse | [Hot-path work](engineering/03-hot-path-work.md) |
| Shared ownership, locks, reference counting, pointer-centric runtime graphs, FFI/thread handles | [Ownership and concurrency](engineering/04-ownership-and-concurrency.md) |
| Wrappers, traits, DTO layers, generic frameworks, caches, services, cleanup and YAGNI | [YAGNI and cleanup](engineering/05-yagni-and-cleanup.md) |
| Authorization, transaction authority, migrations, recovery, wire checks, independent oracles | [Correctness boundaries](engineering/06-correctness-boundaries.md) |
| Performance claims, red flags, decision table, review checklist, acceptance criteria | [Measurement and review](engineering/07-measurement-and-review.md) |
| Concrete Rust transformations | [Examples](engineering/08-examples.md) |
| Compiler/tokenizer/parser/IR pipeline | [Compiler DOD router](engineering/09-wide-pointerless-compiler.md) |

Start with the primary block. Load another only when a finding crosses its boundary. Do not use the examples as authority over a repository-specific contract.

