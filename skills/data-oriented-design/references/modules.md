# Module Composition

Select capabilities by the requested result. Modules are independent instructions with information dependencies, not mandatory phases. Inputs/results may be code, supplied evidence, or inline notes; they do not require new documents or schemas.

## Module contracts

| Module | Use for | Minimum inputs | Result | Instructions |
| --- | --- | --- | --- | --- |
| Contract | clarify required behavior | task, consumers, external boundaries | required input/output, invariants, bounds, unknowns | [Contract](workflow.md#1-fix-the-contract) |
| Application reconstruction | broad repo/app topology and redesign-route discovery | repository/code/deployables | C4-like topology, paths, responsibility ledger, route portfolio, global target | [Whole application](application-reconstruction.md) |
| Process/data map | understand one route's transformations/state | affected code or supplied design | typed operations, owners, lifetimes, consumers, known counts | [Mapping](engineering/00-structural-analysis.md) |
| Necessity | decide whether an element should exist | element, contract/consumer, ownership/lifetime | focused: KEEP/REMOVE/etc.; broad: extract requirement only, never preserve/recreate internal mechanism | [Element test](workflow.md#3-apply-the-element-necessity-test) |
| Data representation | choose identity, relations, storage | contract, access/mutation pattern, bounds/lifetime | candidate types/trade-offs | [Data shape](engineering/01-data-shape.md), [Canonical state](engineering/02-canonical-and-derived.md) |
| Ownership | evaluate sharing/synchronization | owners, lifetimes, concurrent access, FFI boundaries | ownership/lock/handle decision | [Ownership](engineering/04-ownership-and-concurrency.md) |
| Work elimination | remove repeated operations/layers | operations, consumers, frequency, required boundaries | eliminated/merged work and preserved behavior | [Hot-path](engineering/03-hot-path-work.md), [YAGNI](engineering/05-yagni-and-cleanup.md) |
| Pipeline materialization | batch boundary work, compile apply-ready plans, narrow before wide materialization, shrink persisted intermediates | path bounds, keys, snapshot/order semantics, future consumers | batched/resolved/apply-ready or late-materialized representation | [Pipeline materialization](engineering/11-pipeline-materialization.md) |
| Performance diagnosis | identify cause before optimization | target, workload, baseline/profile or access to measure | bottleneck/hypothesis/selected rule family | [Diagnosis](performance/00-diagnosis.md) |
| Experiment | evaluate a cost claim | candidate/hypothesis, baseline, workload, acceptance rule | matched evidence + verdict | [Measurement](performance/01-measurement.md), [Acceptance](performance/10-foundation.md) |
| Correctness | assess a proposed/implemented change | contract, diff/design, tests/oracle | preserved/violated invariants + missing verification | [Correctness](engineering/06-correctness-boundaries.md) |
| Implementation | execute an accepted decision | scoped contract, concrete decision, affected code | changed code + verification | [Implementation](workflow.md#6-implement-one-structural-decision-at-a-time), [Verification](workflow.md#7-verify-proportionally) |
| PWP retained state | pointers, children, builder lifetime | owners/lifetimes, mutation, consumers, contract | focused keep/replace; broad single-owner/phase-owned target shape | [PWP decisions](engineering/compiler/profile/50-pwp-retained-state.md) |
| General SIMD | already-selected identity/layout feeding regular hot loops, gather/scatter, tails | identity/layout result, loop semantics; profile/budget for speed | SIMD/backend decision + acceptance gates | [General SIMD](engineering/10-simd-and-dense-processing.md) |
| 512-byte / lexical profile | batch/masks/compaction/lookup | grammar, source lifetime, backend targets; cost evidence for speed claims | selected technique + parity gates | [512 profile](engineering/compiler/25-pwp-512-profile.md) |
| Compiler specialization | compiler-specific decision | relevant pipeline/lexical/state/validation inputs | selected compiler-block result | [Compiler router](engineering/09-wide-pointerless-compiler.md) |

## Decision ownership

One decision has one detailed owner. Routers may classify and delegate; they must not restate the owner's decision tree.

| Decision | Detailed owner |
| --- | --- |
| whole-application topology / route portfolio | [Whole-application reconstruction](application-reconstruction.md) |
| broad replacement sequence / anti-slop gates | [Broad redesign](broad-redesign.md) |
| scoped structural sequence / verification / reporting | [Workflow](workflow.md) |
| structural pointer→ID, flat children, builder→frozen | [PWP retained state](engineering/compiler/profile/50-pwp-retained-state.md) |
| canonical authority, store-vs-derive, admit/resolve once | [Canonical and derived](engineering/02-canonical-and-derived.md) |
| boundary batching, compile-to-apply, late materialization, persisted history projection | [Pipeline materialization](engineering/11-pipeline-materialization.md) |
| performance typed IDs / flat relations | [Identity rules](performance/20-identity-and-relations.md) and DOD-019 where lookup-in-scan is the cause |
| AoS/SoA/AoSoA, field width, packing/encoding | [Layout and encoding](performance/21-layout-and-encoding.md) |
| vector backend, lane independence, gather/scatter, tails | [General SIMD](engineering/10-simd-and-dense-processing.md) |
| compiler lexical/parser-facing representation | [Wide frontend](engineering/compiler/20-wide-frontend.md) |
| explicit logical 512-byte lexical mechanics | [PWP/512 router](engineering/compiler/25-pwp-512-profile.md) |
| repeated profiler optimization cycle | [Profiler route](#profiler-route) |

## Composition rules

1. Select the smallest module set that produces the requested result.
2. Check minimum inputs. Reuse matching evidence; inspect or measure only missing inputs.
3. Carry results forward with the same scope, version, identity, workload, and units. Recheck only when a dependency changes or validity is uncertain.
4. An unresolved prerequisite blocks only dependent decisions. Continue independent work and label the affected result `UNKNOWN` or `UNVERIFIED`.
5. Before changing a mechanism whose necessity is unresolved, apply Necessity. Before broad repo/application redesign, reconstruct the whole application and route portfolio; then establish route-level typed process/data.
6. Implementation requires affected-behavior verification. A runtime/memory/scaling claim requires Experiment. Analysis-only modules require neither implementation nor benchmark unless their decision depends on measured cost.
7. Stop when the requested result and applicable gates are satisfied. Use [Workflow reporting](workflow.md#proportional-result-format).

## Choose and switch routes

Choose from the question and evidence. Do not run Diagnosis merely because a performance route exists.

| Situation | Start | Next |
| --- | --- | --- |
| broad repo/module redesign or OOP/slop cleanup | [Broad redesign](broad-redesign.md) | whole-app map → route portfolio → global target → per-route flat redesign → direct replacement → tune |
| broad compiler/frontend redesign | [Broad redesign](broad-redesign.md) | map required passes first; specialize compiler/512 only when selected |
| performance target with missing/unreliable profile | Diagnosis | establish baseline/attribution → selected rule family |
| trusted profile or supplied measured cause | profiler route | rank measured costs → inspect selected path → matching rule/module |
| supplied claim to verify | Experiment + Correctness | add Diagnosis only if causal evidence is missing |
| one focused question/candidate | individual module | consume minimum inputs and stop |
| evidence insufficient to choose | smallest missing-input module | inspect/measure the disputed fact; do not invent a ranking |

### Structural route

Use this for scoped structural work; broad replacement uses [Broad redesign](broad-redesign.md).

`Contract → Process/data map → Necessity → selected representation/ownership/work module → candidate comparison → Implementation/Correctness → Experiment only for claimed cost results.`

A measurement can occur earlier whenever a branch explicitly says `MEASURE`.

### Compiler structural route

`Contract → affected Process/data map → Compiler DOD → Pipeline elimination → one specialization for the first accepted structural candidate → Validation.`

Do not separately load the generic structural router and every compiler block. The compiler router owns specialization selection.

### Profiler route

A profile is usable only when workload, build, metric, scope, and measurement method match the target. A CPU-sample profile alone does not attribute blocked wall time or retained memory.

1. Fix target, representative workload, conditions, and acceptance rule. Obtain a baseline only if it is missing.
2. Rank costs by measured contribution to the target. Keep CPU samples, elapsed time, allocations, memory, and waits distinct.
3. Select the largest supported actionable cause within contract/scope. If attribution cannot distinguish candidates, run a bounded diagnostic experiment.
4. Inspect only that path, its contract/consumers, access pattern, and mechanism necessity. Select the matching rule/module. Form one concrete candidate and falsifiable prediction.
5. Implement one causal change, verify behavior, repeat matched measurement, then reprofile and rerank.
6. Stop when the target passes or no supported in-scope change remains.

**Switch profiler → structural** when cost crosses stages/owners, duplicate work/state explains several hotspots, or two consecutive local changes on the same representation fail the declared target acceptance rule.

**Switch structural → profiler** when competing designs depend on unknown cost, the structural candidate leaves the target unmet, or measurement identifies another dominant cause.

After changed evidence invalidates an assumption, revisit only dependent decisions. There is no mandatory restart.

## Example routes

| Request | Composition | Stop condition |
| --- | --- | --- |
| “Does this lock have a responsibility?” | Ownership; Necessity only if responsibility is unclear | focused keep/change; broad extract concurrency invariant, then eliminate shared mutable domain ownership |
| “Map this path; do not redesign it” | Process/data map | affected typed map + known counts |
| “Find duplicated state” | Canonical state + Necessity | authorities/consumers identified |
| “Verify this claimed speedup” | Experiment + Correctness; Diagnosis only if attribution is missing | supported result class or explicit missing evidence |
| “Latency is high; no profile yet” | Diagnosis | attributable cause or named missing evidence |
| “This profile shows hash lookup is 28% of target phase” | profiler route → matching lookup/identity rule | one causal candidate + matched result |
| “Use PWP for this frozen graph; there is no lexer” | PWP retained state | justified pointer/ID/range decision |
| “Simplify this compiler pipeline” | compiler structural route | pipeline candidate + validation requirements |
| “Simplify this full pipeline and implement it” | [Broad redesign](broad-redesign.md) | old path deleted; contract preserved; claimed result supported |

## Extend a capability

Add/refine a focused reference only when a recurring decision needs instructions not already covered. Route it directly from this map or the entry router. Declare only real information dependencies. Reuse existing contract, correctness, measurement, and reporting rules; do not create a registration framework.
