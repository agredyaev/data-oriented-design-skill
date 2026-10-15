---
name: data-oriented-design
description: Use when analyzing or changing code for data layout, retained memory, hot paths, ownership or lifetime, repeated parsing or copying, shared mutable state, YAGNI cleanup, architecture simplification, or correctness-preserving refactoring.
---

# Data-Oriented Design

Use this file as the entry router. Select one module or compose several by task type. Do not read the whole skill tree by default.

Reuse valid existing evidence; execute only missing work. For a custom composition, use the [module contracts](references/modules.md#module-contracts).

## Choose the task mode

| Task | First read | Add only when needed |
| --- | --- | --- |
| Explain or answer one focused DOD question | the single matching engineering block below | examples |
| Review one design choice or supplied candidate | matching engineering block | correctness or measurement when the conclusion depends on them |
| Implement a scoped change | matching engineering block + [workflow verification](references/workflow.md#7-verify-proportionally) | only missing contract/ownership inputs; no mandatory full redesign |
| Diagnose a performance problem or iterate profiler hotspots | [module composition](references/modules.md) + [performance diagnosis](references/performance/00-diagnosis.md) | matching rule pack; structural analysis for broad/shared causes or ineffective local tuning |
| Redesign object/data architecture | [workflow](references/workflow.md) + [structural analysis](references/engineering/00-structural-analysis.md) | matching data/ownership block; performance methodology for speed/memory claims |
| Cleanup/YAGNI review | [YAGNI and cleanup](references/engineering/05-yagni-and-cleanup.md) | workflow when code will change |
| Correctness-sensitive refactor | [correctness boundaries](references/engineering/06-correctness-boundaries.md) + [workflow](references/workflow.md) | matching ownership/data block |

Requested scope takes precedence: a focused compiler/performance question stays focused. A performance complaint without a trustworthy profile starts with Diagnosis; an explicit redesign starts with the structural route. For mixed work, use [route selection](references/modules.md#choose-and-switch-routes).

Start with at most three references after this router. This is an initial reading budget, not a limit on necessary correctness checks. Load another file only for a missing input or a crossed boundary.

## Engineering routing

| Signal | Read |
| --- | --- |
| General data model, identity, object graph or container choice | [Data shape](references/engineering/01-data-shape.md) |
| Canonical state, duplicate representation, stored derived fields, repeated parse/normalize/hash | [Canonical and derived data](references/engineering/02-canonical-and-derived.md) |
| Repeated scans, clones, copies, allocations, hot-loop work, temporary caches | [Hot-path work](references/engineering/03-hot-path-work.md) |
| Shared ownership, locks, reference counting, FFI ownership | [Ownership and concurrency](references/engineering/04-ownership-and-concurrency.md) |
| Wrappers, traits, DTO layers, DI, registries, generic executors, speculative caches/services | [YAGNI and cleanup](references/engineering/05-yagni-and-cleanup.md) |
| Authorization, transactions, claims/leases/fences, migrations, recovery, wire checks | [Correctness boundaries](references/engineering/06-correctness-boundaries.md) |
| Benchmark validity, acceptance decision, review heuristics | [Measurement and review](references/engineering/07-measurement-and-review.md) |
| A concrete Rust transformation would clarify the design | [Examples](references/engineering/08-examples.md) |
| PWP / programming without pointers: retained ownership, flattening, derived fields, builder lifetime | [PWP decisions](references/engineering/compiler/profile/50-pwp-retained-state.md) |
| Explicit 512-byte profile, masks, compaction, compact lexical lookup | [512-byte profile router](references/engineering/compiler/25-pwp-512-profile.md) |
| Compiler/tokenizer/parser/IR | [Compiler DOD](references/engineering/09-wide-pointerless-compiler.md) |

For compiler/frontend code, use [Compiler DOD](references/engineering/09-wide-pointerless-compiler.md) unless the focused PWP/512 route above already selects the needed block. Do not visit both routers for the same decision.

Use [engineering rules index](references/dod-yagni-engineering-rules.md) only when the problem is mixed or the correct block is unclear.

## Performance routing

[Performance methodology](references/performance-methodology.md) routes diagnosis to one rule pack. Do not load all 33 rules at once.

## Choose the execution route

Use [module composition](references/modules.md#choose-and-switch-routes) for routes/switching and [workflow](references/workflow.md) for full redesign or shared verification/reporting.

## Read decisions consistently

`UNKNOWN` is a missing fact, not NO: inspect or measure it; continue independent work. `MEASURE` requests cost evidence; `UNVERIFIED` labels a claim lacking evidence. `TEST`/`candidate` require verification before adoption. `KEEP`/`REJECT` ends that candidate branch, not independent analysis.

Examples are illustrative, not measurements of the user's code. Compare construction, updates, reads and lifetime costs; a local win cannot override a required budget.

## Non-negotiable rules

- Establish the contract before changing representation, ownership, or boundaries.
- Before a structural redesign, establish the affected typed process and retained data; reuse valid existing maps. A scoped module needs only its declared inputs.
- Check whether the selected mechanism is necessary before tuning it; every added representation needs a named consumer and lifetime.
- Preserve required authorization, wire, migration, recovery, ordering, and independent-oracle boundaries.
- Accept performance claims only from matched evidence; after two consecutive local changes on the same representation fail the declared target acceptance rule, revisit the affected structure.
- Report regressions, unknowns, missing measurements, and rejected candidates.

## Completion

For review or implementation work, use the gates and proportional output format in [workflow](references/workflow.md). State only the result supported by evidence: structural simplification, memory reduction, phase improvement, or end-to-end improvement.

