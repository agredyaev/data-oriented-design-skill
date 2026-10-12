# Measurement and Review

# 9. Measurement Rules

## Rule MEASURE-01 — A material layout/hot-path change requires evidence

For significant representation or hot-path changes compare on the same representative workload:

- output equivalence;
- allocation count;
- peak working set;
- operation latency.

Do not invent benchmark requirements for trivial edits.

Do not add complexity for an optimization that has no measured value.

---

## Rule MEASURE-02 — LOC reduction is not permission to weaken the product

Do not reduce source size by:

- removing validation;
- deleting failure handling;
- hiding code in macros;
- moving product behavior into tooling;
- compressing SQL into opaque strings;
- weakening diagnostics;
- deleting tests that expose defects;
- merging semantically distinct operations.

---
# 10. Review Heuristics

When reviewing Rust code, flag the following for investigation.

## Strong red flags

```text
Arc<Mutex<T>> used for ordinary domain entities
HashMap<Id, Arc<Mutex<T>>>
Vec<Arc<T>> in a stable bounded domain
Rc<RefCell<T>> runtime object graphs
Box<T> per entity in hot traversal
global Mutex/RwLock domain state
repeated serde_json round-trips
same input parsed multiple times
full canonical state copied into multiple runtime structures
clone/to_vec/to_string in dominant loops
generic executor with many mode flags
DI/service locator/container
traits with one implementation and no real boundary
new global cache without measurement
new durable store/source of truth
```

## Review, but do not automatically reject

```text
Arc<T> for immutable cross-thread ownership
Arc<foreign_interrupt_handle>
Mutex around a genuinely concurrent external handle
HashMap during build/admission
ASTs during parser/compiler phases
AoS layouts
small local Vec allocations outside hot paths
small crate-local helper functions
operation-specific duplicated guards protecting different invariants
```

---
# 11. Practical Decision Table

| Situation | Default decision |
|---|---|
| Stable bounded entities referenced by each other | Typed IDs + contiguous storage |
| Immutable data after startup/freeze | Owned frozen structure + shared references/slices |
| Multiple threads only read immutable state | Shared immutable ownership; `Arc<T>` only if ownership requires it |
| Concurrent mutation of one real shared resource | Lock may be justified |
| Ordinary domain entities wrapped in `Arc<Mutex<_>>` | Redesign ownership first |
| Temporary compiler lookup | `HashMap` is acceptable |
| Frozen runtime still contains temporary parser maps | Require concrete justification |
| Graph traversal over stable adjacency | Consider CSR/ranges |
| Tiny records always consumed whole | AoS is fine |
| Hot pass touches one field across many entities | Consider SoA |
| Same input parsed twice | Propagate admitted typed result |
| Internal typed value serialized then reparsed | Remove internal round-trip where wire semantics are not needed |
| Small repeated low-level operation | Local helper |
| Similar high-level operations with different invariants | Keep separate |
| Cache proposed without profiling/requirement | Reject |
| Optimization increases complexity with no measurement | Reject |
| Shared FFI interrupt handle uses `Arc` | Accept if required by boundary |

---
# 13. Cleanup Review Checklist

Before accepting a cleanup change, answer:

### Data

- What is the dominant iteration?
- Are entities addressed by typed IDs where appropriate?
- Is hot data contiguous where appropriate?
- Is there more than one canonical copy?
- Is stable input reparsed or renormalized?
- Are temporary build structures leaking into frozen runtime state?

### Ownership

- Who owns each allocation?
- Why is `Arc` required?
- Why is `Mutex`/`RwLock` required?
- Could immutable data be borrowed instead?
- Is shared mutation real or merely compensating for unclear ownership?

### Processing

- Is execution expressed as explicit passes?
- Are loops deterministic where required?
- Are repeated scans avoidable through existing ranges/indexes?
- Are clones/copies occurring in dominant loops?
- Is request-local scratch reusable?

### Abstraction

- What concrete responsibility does each wrapper/trait/layer provide?
- Is a helper removing a real shared rule or merely reducing LOC?
- Does a generic abstraction introduce mode flags?
- Is a framework replacing only a few local functions?
- Is extensibility required now, or only hypothetical?

### Safety

- Were authorization checks preserved?
- Were claim/lease/epoch/fence checks preserved?
- Were transaction boundaries preserved?
- Were failure and recovery semantics preserved?
- Were wire-level checks preserved?
- Were upgrade paths preserved?
- Were independent test oracles preserved?

### Evidence

- Does the change preserve output?
- Are regression tests present for behavior-sensitive changes?
- For material hot-path/layout changes, were allocations, memory, and latency measured?
- Was complexity added without demonstrated benefit?

---
# 14. Scope and Exceptions

This document consolidates DOD and YAGNI guidance for implementation, review, and cleanup work across repositories.

## Covered rules

The policy covers:

- YAGNI-first implementation;
- no speculative runtime services, stores, sources of truth, generic backends, plugin systems, dependency-injection frameworks, or caches;
- dense typed IDs;
- contiguous arrays;
- ranges;
- CSR where appropriate;
- bounded side tables;
- explicit passes;
- reusable request-local scratch;
- builder/runtime representation separation;
- removal of repeated parsing;
- removal of unnecessary clones;
- removal of pass-through wrappers and redundant DTO conversions;
- avoiding second copies of canonical graphs/state;
- measurement for material hot-path/layout changes;
- preserving correctness, security, diagnostics, recovery, and tests;
- not forcing every record into SoA;
- not forcing every relation into CSR;
- not forcing every sparse set into a bitset;
- preservation of valid foreign interrupt/thread-safety boundaries;
- avoiding generic frameworks that merge semantically different operations.

## Important qualification: `Arc<Mutex<T>>`

These rules do **not** prohibit every use of `Arc`, `Mutex`, or `Arc<Mutex<T>>`.

Apply this distinction:

> Pointer-centric shared mutable domain graphs are contrary to the desired DOD direction and should be treated as a strong design smell. Reference-counted or synchronized handles remain valid where a concrete concurrency, lifetime, FFI, cancellation, or external-library boundary requires them.

Use **"avoid / require justification"**, not **"globally forbidden."**

## Evidence and scope

The guidance incorporates:

- operating priorities;
- YAGNI removal rules;
- DOD rules;
- measurement and verification requirements;
- demonstrated duplication and repeated transformations;
- parser/rendering/allocation findings;
- application dispatch duplication;
- native helper guidance;
- cases where apparent duplication must be preserved;
- explicit foreign interrupt-handle exceptions.

Examples are contextual and do not establish additional product requirements. Apply repository-specific architecture policies and external contracts separately.
---
# 15. Short Policy Version

For code review, the policy can be reduced to:

1. **Data first, objects second.**
2. **Dense typed IDs over pointer identity.**
3. **Contiguous storage over heap-per-entity layouts where the workload fits.**
4. **Explicit passes over hidden object choreography.**
5. **Immutable/frozen runtime state where possible.**
6. **`Arc<Mutex<_>>` for domain state requires a concrete concurrency/FFI justification.**
7. **Temporary maps/ASTs are fine before freeze; do not retain them without need.**
8. **Do not force SoA/CSR/bitsets where the workload does not justify them.**
9. **Parse/admit once; propagate typed results.**
10. **Avoid internal serialization round-trips.**
11. **Borrow or consume before cloning.**
12. **Use request-local scratch before global caches.**
13. **One canonical state; indexes/views instead of copies.**
14. **Small local helpers before generic frameworks.**
15. **Do not merge semantically different operations to reduce LOC.**
16. **No speculative services, stores, DI, plugins, backends, or caches.**
17. **Never remove correctness boundaries as “duplication.”**
18. **Measure material optimization work.**
19. **Preserve deterministic behavior and explicit resource bounds.**
20. **Prefer measurable simplicity over abstraction.**
