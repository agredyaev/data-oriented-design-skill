# DOD / YAGNI Engineering Fallback Index

Use this file only when the primary engineering block is unclear or the finding spans several concerns. It is an index, not a second workflow.

## First classify the decision

```text
What must be decided?
  retained identity / object graph / storage shape
      -> Data shape
  canonical authority / duplicate state / derive-vs-store / repeated admission
      -> Canonical and derived data
  repeated scans / copies / allocations / scratch / cache
      -> Hot-path work
  shared ownership / locks / reference counting / FFI handle
      -> Ownership and concurrency
  wrapper / trait / DTO / framework / service / speculative infrastructure
      -> YAGNI and cleanup
  authorization / transaction / migration / recovery / wire / oracle boundary
      -> Correctness boundaries
  required evidence / acceptance verdict
      -> Measurement and review
  compiler/tokenizer/parser/IR
      -> Compiler DOD router
```

| Decision | Read |
| --- | --- |
| identity, graph, flat relation, AoS/SoA, builder→frozen | [Data shape](engineering/01-data-shape.md) |
| canonical/derived state, repeated parse/normalize/hash | [Canonical and derived](engineering/02-canonical-and-derived.md) |
| repeated work, copy/allocation, local scratch/cache | [Hot-path work](engineering/03-hot-path-work.md) |
| sharing, locks, FFI/stable-address ownership | [Ownership](engineering/04-ownership-and-concurrency.md) |
| abstractions, wrappers, DTOs, frameworks, speculative infrastructure | [YAGNI](engineering/05-yagni-and-cleanup.md) |
| safety/correctness boundaries | [Correctness](engineering/06-correctness-boundaries.md) |
| evidence and result acceptance | [Measurement and review](engineering/07-measurement-and-review.md) |
| compiler/frontend | [Compiler DOD](engineering/09-wide-pointerless-compiler.md) |

## Shared priority

When several mechanisms apply, prefer this decision order unless the contract or measurement gives a stronger reason:

```text
remove responsibility-free element
    ↓
remove repeated transformation/pass
    ↓
localize temporary state
    ↓
choose retained identity/relations
    ↓
choose hot/cold layout or encoding
    ↓
micro-optimize the remaining required work
```

This order does not authorize removal. Every branch must still preserve required consumers, lifetimes, correctness boundaries, and budgets.

## Cross-cutting rules

- One semantic fact should have one mutable authority. Indexes/views need a named consumer and update/rebuild rule.
- Typed IDs/offsets/ranges are preferred only when ownership, lifetime, and validity checks make them correct.
- Derive deterministic values only while exact inputs/version survive and read cost fits the budget.
- Temporary build/request state should end at its last consumer unless a runtime consumer justifies retention.
- Do not add caches, services, registries, DI, or generic executors to avoid fixing ownership/data flow.
- Correctness boundaries override cleanup.
- Structural simplification can be accepted from code + behavior evidence. Runtime/memory/scaling claims require the matching evidence.

For broad redesigns, use [Workflow](workflow.md) and [Structural analysis](engineering/00-structural-analysis.md). For profiler-led work, use [Module composition](modules.md#choose-and-switch-routes) and [Performance methodology](performance-methodology.md).
