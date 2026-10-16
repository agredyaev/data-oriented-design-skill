---
name: data-oriented-design
description: Use when analyzing or changing code for data layout, retained memory, hot paths, ownership or lifetime, repeated parsing or copying, shared mutable state, YAGNI cleanup, architecture simplification, or correctness-preserving refactoring.
---

# Data-Oriented Design

Select the smallest route that answers the request. Do not read the whole skill tree by default. Reuse valid evidence and execute only missing work. For custom compositions, use the [module contracts](references/modules.md#module-contracts).

## Choose the task mode

| Task | First read | Add only when needed |
| --- | --- | --- |
| Explain or review one focused DOD decision | the single matching engineering block below | correctness or measurement only when the decision depends on them |
| Implement a scoped change | matching engineering block + [workflow verification](references/workflow.md#7-verify-proportionally) | only missing contract/ownership inputs; no mandatory full redesign |
| Performance problem without a trustworthy profile | [module composition](references/modules.md) + [performance diagnosis](references/performance/00-diagnosis.md) | selected rule pack after diagnosis |
| Trusted profiler hotspot or supplied measured cause | [module composition](references/modules.md) + [performance methodology](references/performance-methodology.md) | the selected rule pack; do not repeat diagnosis only for sequence compliance |
| Broad repo/module redesign or OOP cleanup | [broad redesign](references/broad-redesign.md) | one detail block only when a gate selects it |
| Broad compiler/frontend redesign | [broad redesign](references/broad-redesign.md) | [Compiler DOD](references/engineering/09-wide-pointerless-compiler.md) after required passes are mapped |
| Cleanup/YAGNI review | [broad classifier](references/broad-redesign.md#entry-classifier-focused-fix-or-broad-redesign) | [YAGNI](references/engineering/05-yagni-and-cleanup.md) only if focused |
| Correctness-sensitive refactor | [correctness boundaries](references/engineering/06-correctness-boundaries.md) + [workflow](references/workflow.md) | matching ownership/data block |

Requested scope wins. Keep focused work focused. For mixed work, use [route selection](references/modules.md#choose-and-switch-routes).

Start with at most three references after this router. Load another only for a missing input or crossed boundary; correctness checks are not capped.

## Engineering routing

| Signal | Read |
| --- | --- |
| Data model, object graph, typed identity, contiguous/flat storage, builder→frozen shape | [Data shape](references/engineering/01-data-shape.md) |
| Canonical state, duplicate representation, stored derived fields, repeated parse/normalize/hash | [Canonical and derived data](references/engineering/02-canonical-and-derived.md) |
| Repeated scans, clones, copies, allocations, hot-loop work, scratch/cache choice | [Hot-path work](references/engineering/03-hot-path-work.md) |
| Shared ownership, locks, reference counting, FFI/stable-address ownership | [Ownership and concurrency](references/engineering/04-ownership-and-concurrency.md) |
| Wrappers, traits, DTO layers, DI, registries, generic executors, speculative caches/services | [YAGNI and cleanup](references/engineering/05-yagni-and-cleanup.md) |
| Authorization, transactions, claims/leases/fences, migrations, recovery, wire checks | [Correctness boundaries](references/engineering/06-correctness-boundaries.md) |
| Evidence needed to accept a structural, memory, phase, or end-to-end claim | [Measurement and review](references/engineering/07-measurement-and-review.md) |
| Concrete Rust transformation | [Examples](references/engineering/08-examples.md) |
| PWP retained ownership, flattening, builder lifetime | [PWP decisions](references/engineering/compiler/profile/50-pwp-retained-state.md) |
| Dense IDs, direct indexing, SIMD, gather/scatter, vector tails | [General SIMD](references/engineering/10-simd-and-dense-processing.md) |
| 512-byte lexical masks/compaction/lookup | [512 profile](references/engineering/compiler/25-pwp-512-profile.md) |
| Compiler/tokenizer/parser/IR | [Compiler DOD](references/engineering/09-wide-pointerless-compiler.md) |

For compiler/frontend code, use [Compiler DOD](references/engineering/09-wide-pointerless-compiler.md) unless a focused PWP/512 route already selected the block. Use the [engineering fallback index](references/dod-yagni-engineering-rules.md) only when the primary block is unclear.

## Performance routing

No/untrusted profile → Diagnosis. Trusted measured cause → [Performance methodology](references/performance-methodology.md) → matching rule pack. Claimed result → Experiment/Correctness; add Diagnosis only when attribution is missing.

## Decision language

Keep evidence state separate from design action.

Evidence state:

- `UNKNOWN` — a semantic/consumer/lifetime fact is missing.
- `MEASURE` — cost evidence is required to choose.
- `UNVERIFIED` — required evidence is missing.
- `MEASURED` / `WITHIN BUDGET` — named evidence/bound is established.

Design action:

- `KEEP`, `REMOVE`, `MERGE`, `DERIVE`, `LOCALIZE`, `FLATTEN`, `BATCH` — supported structural action.
- `TEST` / `candidate` — verify before adoption.
- `REJECT` — candidate fails contract, acceptance rule, or guardrail.

A decision can be structurally supported while a cost claim remains `UNVERIFIED`.

## Non-negotiable rules

- Establish the affected contract before changing representation, ownership, or boundaries.
- Broad redesign uses the dedicated route and deletes superseded internal architecture.
- Test mechanism necessity before tuning it. Every added representation needs a named consumer and lifetime.
- Preserve required authorization, wire, migration, recovery, ordering, and independent-oracle boundaries.
- Accept performance claims only from matched evidence. After two consecutive local changes on the same representation fail the declared target acceptance rule, revisit the affected structure.
- Report regressions, unknowns, missing measurements, and rejected candidates.

## Completion

Use the gates and proportional result format in [workflow](references/workflow.md). State only the result supported by evidence: structural simplification, memory reduction, phase improvement, end-to-end improvement, scalability improvement, or no supported change.
