---
name: data-oriented-design
description: Use when analyzing or changing code for data layout, retained memory, hot paths, ownership or lifetime, repeated parsing or copying, shared mutable state, YAGNI cleanup, architecture simplification, or correctness-preserving refactoring.
---

# Data-Oriented Design

Use progressive disclosure. This file routes the task; detailed procedure and rules live in `references/`.

## Required load order

1. Read [workflow](references/workflow.md) for every task.
2. Read [engineering rules router](references/dod-yagni-engineering-rules.md) for every task.
3. For performance, data-model, ownership, or architecture work, read [structural analysis](references/engineering/00-structural-analysis.md) before proposing changes.
4. Read every additional engineering block selected by the engineering router.
5. Read [performance methodology and DOD rules](references/performance-methodology.md) when the task includes performance diagnosis, retained layout, memory, hot paths, IDs, indexes, derived fields, scaling, measurement, or a material performance claim.
6. Load [examples](references/engineering/08-examples.md) only when a concrete transformation example is useful.

Do not load unrelated references merely because they exist.

## Routing

| Task signal | Read |
| --- | --- |
| Object graph, pointer-heavy model, nested containers, freeze/build boundary | [Data shape](references/engineering/01-data-shape.md) |
| Canonical state, duplicated representation, stored derived fields, repeated parse/normalize/hash | [Canonical and derived data](references/engineering/02-canonical-and-derived.md) |
| Repeated scans, clone/copy/allocation, hot-loop work, intermediate caching | [Hot-path work](references/engineering/03-hot-path-work.md) |
| `Arc`, `Mutex`, `RwLock`, reference counting, shared mutation, FFI ownership | [Ownership and concurrency](references/engineering/04-ownership-and-concurrency.md) |
| Wrappers, traits, DTO layers, DI, registries, generic executors, speculative caches/services | [YAGNI and cleanup](references/engineering/05-yagni-and-cleanup.md) |
| Authorization, transactions, claims/leases/fences, migrations, recovery, wire checks | [Correctness boundaries](references/engineering/06-correctness-boundaries.md) |
| Benchmark or performance claim, acceptance decision, review heuristics | [Measurement and review](references/engineering/07-measurement-and-review.md) |

Mixed problems require every applicable block.

## Non-negotiable rules

- Establish the contract before changing representation or ownership.
- Draw the current structure in ASCII before material optimization or architecture cleanup.
- Prefer removing objects, states, passes, boundaries, round-trips, and retained representations before tuning them in place.
- Prefer one canonical state; additional structures need a concrete consumer and lifetime.
- Prefer dense typed IDs, offsets, ranges, and contiguous storage when the domain and access pattern support them.
- Treat stored deterministic values as candidates for derivation; retain them only with a semantic or measured cost justification.
- Admit/parse/normalize once and propagate typed results where the contract permits.
- Preserve authorization, wire validation, migrations, recovery, independent test oracles, and distinct authority checks.
- Do not claim performance from Big O, row width, or a microbenchmark alone.
- If two consecutive local changes on the same representation do not materially move the end-to-end target, stop micro-tuning and return to structural analysis.
- Report supported failures, regressions, unknowns, missing measurements, and rejected candidates. Do not replace them with a favorable summary.

## Required result

Follow the output format and acceptance gates in [workflow](references/workflow.md). A material optimization is complete only when required correctness gates pass and the claimed end-to-end improvement is supported by matched evidence.
