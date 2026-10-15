---
name: data-oriented-design
description: Use when analyzing or changing code for data layout, retained memory, hot paths, ownership or lifetime, repeated parsing or copying, shared mutable state, YAGNI cleanup, architecture simplification, or correctness-preserving refactoring.
---

# Data-Oriented Design

Use this file as the only entry router. Load references by task type. Do not read the whole skill tree by default.

## Choose the task mode

| Task | First read | Add only when needed |
| --- | --- | --- |
| Explain or answer one focused DOD question | the single matching engineering block below | examples |
| Review a non-trivial design or code path | matching engineering block(s); add structural analysis for architecture/performance | workflow only if the review proceeds to implementation or formal acceptance |
| Implement or modify code | [workflow](references/workflow.md) + matching engineering block(s) | correctness or measurement block |
| Diagnose a performance problem | [structural analysis](references/engineering/00-structural-analysis.md) | performance methodology after the current/candidate process maps exist |
| Redesign object/data architecture | [structural analysis](references/engineering/00-structural-analysis.md) + matching data/ownership block | performance methodology when claiming speed/memory improvement |
| Cleanup/YAGNI review | [YAGNI and cleanup](references/engineering/05-yagni-and-cleanup.md) | workflow when code will change |
| Correctness-sensitive refactor | [correctness boundaries](references/engineering/06-correctness-boundaries.md) + [workflow](references/workflow.md) | matching ownership/data block |

Start with at most three references after this router. Load another file only when the current finding crosses its boundary.

## Engineering routing

| Signal | Read |
| --- | --- |
| Object graph, pointer-heavy model, nested containers, freeze/build boundary | [Data shape](references/engineering/01-data-shape.md) |
| Canonical state, duplicate representation, stored derived fields, repeated parse/normalize/hash | [Canonical and derived data](references/engineering/02-canonical-and-derived.md) |
| Repeated scans, clones, copies, allocations, hot-loop work, temporary caches | [Hot-path work](references/engineering/03-hot-path-work.md) |
| Shared ownership, locks, reference counting, FFI ownership | [Ownership and concurrency](references/engineering/04-ownership-and-concurrency.md) |
| Wrappers, traits, DTO layers, DI, registries, generic executors, speculative caches/services | [YAGNI and cleanup](references/engineering/05-yagni-and-cleanup.md) |
| Authorization, transactions, claims/leases/fences, migrations, recovery, wire checks | [Correctness boundaries](references/engineering/06-correctness-boundaries.md) |
| Benchmark validity, acceptance decision, review heuristics | [Measurement and review](references/engineering/07-measurement-and-review.md) |
| A concrete Rust transformation would clarify the design | [Examples](references/engineering/08-examples.md) |
| Compiler/parser/tokenizer/IR lowering | [Wide compiler](references/engineering/09-wide-pointerless-compiler.md) |

Use [engineering rules index](references/dod-yagni-engineering-rules.md) only when the problem is mixed or the correct block is unclear.

## Performance routing

[Performance methodology](references/performance-methodology.md) is itself a router. It first sends the task to a compact diagnosis guide, then to one rule pack. Do not load all DOD-001–DOD-033 rules at once.

## Primary top-down algorithm

For every non-trivial architecture or performance task:

1. State the contract as `INPUT → REQUIRED OUTPUT` plus behavior that must not change.
2. Draw the current typed process: each step names its operation, input type, output type, retained state touched, and known multiplicity.
3. Draw the current retained data: root owner, concrete containers/records, relationships, lifetime, and canonical versus derived state.
4. Count the current work: steps, passes, lookups, parse/normalize operations, copies/clones, allocations, locks/refcounts, round-trips, and duplicate retained representations.
5. Mark elements that can be removed, merged, derived, localized, flattened, or batched while preserving the contract.
6. Design a new typed process from the contract rather than from the old classes. The candidate must solve the same task with fewer explicit steps or less retained state.
7. Design the candidate data model. Prefer one canonical root-owned representation with arrays, typed IDs, offsets/ranges, side storage, tags, and derived values where valid.
8. Compare current and candidate structurally using the same counts. Unknown values stay `?`.
9. Only then load detailed DOD rule packs to refine widths, layout, indexing, blocking, concurrency, and measurement.
10. Measure the stated target. A local improvement is not an end-to-end result.

The preferred candidate is the simplest design that preserves the contract and removes the most recurring work/state without adding more expensive invariants.

## Non-negotiable rules

- Establish the contract before changing representation or ownership.
- For material performance or architecture work, draw the current structure in ASCII.
- Prefer removing objects, states, passes, boundaries, round-trips, and retained representations before tuning them.
- Prefer one canonical state. Give every additional index, view, cache, or side structure a concrete consumer and lifetime.
- Prefer dense typed IDs, offsets, ranges, and contiguous storage when the domain and access pattern support them.
- Treat deterministic stored values as derive candidates. Keep them only for semantic or measured-cost reasons.
- Admit, parse, normalize, or resolve once when the validated typed result can be propagated.
- Preserve authorization, wire validation, migrations, recovery, independent test oracles, and distinct authority checks.
- Do not claim performance from complexity, row width, or a microbenchmark alone.
- If two consecutive local changes do not materially move the end-to-end target, stop micro-tuning and return to structural analysis.
- Report failures, regressions, unknowns, missing measurements, and rejected candidates.

## Completion

For review or implementation work, use the gates and output format in [workflow](references/workflow.md). A material optimization is complete only when correctness passes and the claimed end-to-end improvement has matched evidence.
