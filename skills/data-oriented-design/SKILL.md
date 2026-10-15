---
name: data-oriented-design
description: Use when analyzing or changing code for data layout, retained memory, hot paths, ownership or lifetime, repeated parsing or copying, shared mutable state, YAGNI cleanup, architecture simplification, or correctness-preserving refactoring.
---

# Data-Oriented Design

Use this file as the entry router. Select one module or compose several by task type. Do not read the whole skill tree by default.

For a partial task or a custom route, use the [module composition map](references/modules.md). Each module declares its inputs, result, and dependencies. Reuse valid existing evidence; execute only the missing work required for the selected result.

## Choose the task mode

| Task | First read | Add only when needed |
| --- | --- | --- |
| Explain or answer one focused DOD question | the single matching engineering block below | examples |
| Review a non-trivial design or code path | matching engineering block(s); add workflow + structural analysis for architecture/performance | correctness or measurement block |
| Implement or modify code | [workflow](references/workflow.md) + matching engineering block(s) | correctness or measurement block |
| Diagnose a performance problem or iterate profiler hotspots | [module composition](references/modules.md) + [performance diagnosis](references/performance/00-diagnosis.md) | matching rule pack; structural analysis for broad/shared causes or ineffective local tuning |
| Redesign object/data architecture | [workflow](references/workflow.md) + [structural analysis](references/engineering/00-structural-analysis.md) | matching data/ownership block; performance methodology for speed/memory claims |
| Cleanup/YAGNI review | [YAGNI and cleanup](references/engineering/05-yagni-and-cleanup.md) | workflow when code will change |
| Correctness-sensitive refactor | [correctness boundaries](references/engineering/06-correctness-boundaries.md) + [workflow](references/workflow.md) | matching ownership/data block |

Start with at most three references after this router. Load another file only when the current finding crosses its boundary.

## Engineering routing

| Signal | Read |
| --- | --- |
| PWP / programming without pointers, object graph, pointer-heavy model, nested containers, freeze/build boundary | [Data shape](references/engineering/01-data-shape.md) |
| Canonical state, duplicate representation, stored derived fields, repeated parse/normalize/hash | [Canonical and derived data](references/engineering/02-canonical-and-derived.md) |
| Repeated scans, clones, copies, allocations, hot-loop work, temporary caches | [Hot-path work](references/engineering/03-hot-path-work.md) |
| Shared ownership, locks, reference counting, FFI ownership | [Ownership and concurrency](references/engineering/04-ownership-and-concurrency.md) |
| Wrappers, traits, DTO layers, DI, registries, generic executors, speculative caches/services | [YAGNI and cleanup](references/engineering/05-yagni-and-cleanup.md) |
| Authorization, transactions, claims/leases/fences, migrations, recovery, wire checks | [Correctness boundaries](references/engineering/06-correctness-boundaries.md) |
| Benchmark validity, acceptance decision, review heuristics | [Measurement and review](references/engineering/07-measurement-and-review.md) |
| A concrete Rust transformation would clarify the design | [Examples](references/engineering/08-examples.md) |
| PWP / explicit 512-byte classification profile | [PWP and 512-byte profile](references/engineering/compiler/25-pwp-512-profile.md) |
| Compiler/tokenizer/parser/IR | [Compiler DOD](references/engineering/09-wide-pointerless-compiler.md) |

For compiler/frontend code, use [Compiler DOD](references/engineering/09-wide-pointerless-compiler.md) as the primary engineering route. Load generic engineering blocks only when that router sends the finding there.

Use [engineering rules index](references/dod-yagni-engineering-rules.md) only when the problem is mixed or the correct block is unclear.

## Performance routing

[Performance methodology](references/performance-methodology.md) is itself a router. It first sends the task to a compact diagnosis guide, then to one rule pack. Do not load all DOD-001–DOD-033 rules at once.

## Choose the execution route

For a broad redesign, use the structural route: contract → current typed process/data → necessity decisions → simpler candidate → verification.

For a measured performance task, use the profiler route: target/workload → rank measured costs → select a hotspot → test a causal change → reprofile and rerank. Use the [route selection and switching rules](references/modules.md#choose-and-switch-routes).

Use [workflow](references/workflow.md) as the default full-route composition and the shared completion/reporting contract. Individual modules can run independently when their inputs are available; do not force the full route for a scoped task. Use [structural analysis](references/engineering/00-structural-analysis.md) for map notation, counting, and candidate-design techniques. A selected rule pack refines a concrete candidate. A profiler task needs only the affected path until evidence calls for broader structural analysis.

## Non-negotiable rules

- Establish the contract before changing representation, ownership, or boundaries.
- Before a structural redesign, establish the affected typed process and retained data; reuse valid existing maps. A scoped module needs only its declared inputs.
- Check whether the selected mechanism is necessary before tuning it; every added representation needs a named consumer and lifetime.
- Preserve required authorization, wire, migration, recovery, ordering, and independent-oracle boundaries.
- Accept performance claims only from matched evidence; after two local misses, return to structural analysis.
- Report regressions, unknowns, missing measurements, and rejected candidates.

## Completion

For review or implementation work, use the gates and proportional output format in [workflow](references/workflow.md). State only the result supported by evidence: structural simplification, memory reduction, phase improvement, or end-to-end improvement.

