---
name: data-oriented-design
description: Use for OOP-to-DOD/PWP redesign, data layout, retained memory, hot paths, ownership or lifetime, repeated parsing or copying, shared mutable state, YAGNI cleanup, architecture simplification, or correctness-preserving refactoring.
---

# Data-Oriented Design

Route by task scope, load only needed references, and reuse valid evidence.

## Primary goal

**DOD (Data-Oriented Design):** Derive the implementation from required operations, data access/mutation and physical layout—not object hierarchies.

**PWP (Programming Without Pointers):** Prefer explicitly owned retained data with typed IDs, offsets and ranges over pointer-linked domain graphs. Local borrows and necessary lifetime, stable-address or FFI handles remain valid.

For architecture or structural cleanup, derive a **DOD/PWP target from computations and physical data access**, not from existing OOP layers. Prefer minimal explicit passes, data shaped for real operations, clear ownership/lifetimes and typed IDs/offsets/ranges for retained internal relationships. Remove unnecessary Service/Repository/DTO/Mapper/Manager layers, object graphs and owned copies. Preserve independently required correctness and external boundaries.

## Mandatory DOD preflight

Before proposing a target for architecture, redesign, structural cleanup, data-model, ownership or performance-change work, establish in order: **required operation → exact reads/writes → multiplicity/access pattern → physical data path/layout → retained state → ownership/lifetime/correctness boundaries**. Do not propose target types, layers or abstractions before these facts. Mark missing facts `UNKNOWN`; resolve those blocking a target choice.

Current layers are evidence, never target-design primitives. If a target starts from old architecture boxes, restart from operations and data. Focused fixes/questions and profiler diagnosis stay scoped.

### Structural-route override

**Apply this before selecting a task-mode row or an Engineering routing row.** Architecture redesign always uses the structural route. For architecture/structural cleanup, Controller → Service → Repository delegation, DTO/Mapper/ViewModel hops, DI service graphs, domain-object graphs, per-entity heap ownership, one-implementation architectural traits or repeated DTO/transport conversions also force [Transformation](references/engineering/10-oop-to-dod.md) + [workflow](references/workflow.md) + [Data shape](references/engineering/01-data-shape.md). Do **not** accept YAGNI-only cleanup. Use YAGNI only after deriving the target. Focused local fixes/questions and profiler diagnosis remain scoped until they require a structural target.

## Choose the task mode

| Task | First read | Add only when needed |
| --- | --- | --- |
| Architecture redesign or structural cleanup with OOP/layer signals | [Transformation](references/engineering/10-oop-to-dod.md) + [workflow](references/workflow.md) + [Data shape](references/engineering/01-data-shape.md) | correctness or measurement for disputed decisions |
| Performance diagnosis or profiler hotspots | [module composition](references/modules.md) + [performance diagnosis](references/performance/00-diagnosis.md) | selected rule pack; structural route for shared causes |
| Correctness-sensitive refactor | [correctness boundaries](references/engineering/06-correctness-boundaries.md) + [workflow](references/workflow.md) | matching ownership/data block |
| Scoped implementation without structural redesign | matching engineering block + [workflow verification](references/workflow.md#8-verify-proportionally) | only missing contract/ownership inputs |
| Focused question or supplied design candidate | matching engineering block | correctness/measurement when needed |
| Local YAGNI cleanup **only after structural override check** | [YAGNI and cleanup](references/engineering/05-yagni-and-cleanup.md) | workflow if code changes |

Requested scope takes precedence: a focused compiler/performance question stays focused. A performance complaint without a trustworthy profile starts with Diagnosis; an explicit redesign starts with the structural route. For mixed work, use [route selection](references/modules.md#choose-and-switch-routes).

Start with at most three references after this router. Load more for missing inputs or necessary correctness checks.

## Engineering routing

| Signal | Read |
| --- | --- |
| General data model, identity, object graph or container choice | [Data shape](references/engineering/01-data-shape.md) |
| Canonical state, duplicate representation, stored derived fields, repeated parse/normalize/hash | [Canonical and derived data](references/engineering/02-canonical-and-derived.md) |
| Repeated scans, clones, copies, allocations, hot-loop work, temporary caches | [Hot-path work](references/engineering/03-hot-path-work.md) |
| Shared ownership, locks, reference counting, FFI ownership | [Ownership and concurrency](references/engineering/04-ownership-and-concurrency.md) |
| Authorization, transactions, claims/leases/fences, migrations, recovery, wire checks | [Correctness boundaries](references/engineering/06-correctness-boundaries.md) |
| Benchmark validity, acceptance decision, review heuristics | [Measurement and review](references/engineering/07-measurement-and-review.md) |
| A concrete Rust transformation would clarify the design | [Examples](references/engineering/08-examples.md) |
| PWP / programming without pointers: retained ownership, flattening, derived fields, builder lifetime | [PWP decisions](references/engineering/compiler/profile/50-pwp-retained-state.md) |
| Explicit 512-byte profile, masks, compaction, compact lexical lookup | [512-byte profile router](references/engineering/compiler/25-pwp-512-profile.md) |
| Compiler/tokenizer/parser/IR | [Compiler DOD](references/engineering/09-wide-pointerless-compiler.md) |
| Local wrappers, traits, DTO/DI cleanup **after structural override** | [YAGNI and cleanup](references/engineering/05-yagni-and-cleanup.md) |

For compiler/frontend code, use [Compiler DOD](references/engineering/09-wide-pointerless-compiler.md) unless the focused PWP/512 route above already selects the needed block. Do not visit both routers for the same decision.

Use [engineering rules index](references/dod-yagni-engineering-rules.md) only when the problem is mixed or the correct block is unclear.

## Performance routing

[Performance methodology](references/performance-methodology.md) routes diagnosis to one rule pack. Do not load all 33 rules at once.

## Read decisions consistently

`UNKNOWN` is a missing fact, not NO: inspect or measure it; continue independent work. `MEASURE` requests cost evidence; `UNVERIFIED` labels a claim lacking evidence. `TEST`/`candidate` require verification before adoption. `KEEP`/`REJECT` ends that candidate branch, not independent analysis.

Examples are illustrative, not measurements of the user's code. Compare construction, updates, reads and lifetime costs; a local win cannot override a required budget.

## Non-negotiable rules

- Apply the [preflight](#mandatory-dod-preflight) before structural target design; required behavior does not justify its old layer.
- Apply the [representation budget](references/engineering/02-canonical-and-derived.md#representation-budget) to new owned state, and test a mechanism's necessity before tuning it.
- Preserve required authorization, wire, migration, recovery, ordering, and independent-oracle boundaries.
- Accept performance claims only from matched evidence; use the [progress and switching rule](references/modules.md#choose-and-switch-routes).
- Report regressions, unknowns, missing measurements, and rejected candidates.

## Completion

For review or implementation work, use the gates and proportional output format in [workflow](references/workflow.md). State only the result supported by evidence: structural simplification, memory reduction, phase improvement, or end-to-end improvement.

