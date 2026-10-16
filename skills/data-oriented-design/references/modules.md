# Module Composition

Select capabilities by the result requested. Modules are independent instructions with information dependencies, not mandatory phases. Inputs/results may be code, supplied evidence, or a few inline notes; they do not require new documents or schemas.

## Module contracts

| Module | Use for | Minimum inputs | Result | Instructions |
| --- | --- | --- | --- | --- |
| Contract | clarify required behavior | task, consumers, external boundaries | required input/output, invariants, bounds, unknowns | [Contract](workflow.md#1-fix-the-contract) |
| Process/data map | understand current transformations/state | affected code or a supplied design | typed operations, owners, lifetimes, consumers, known counts | [Mapping techniques](engineering/00-structural-analysis.md) |
| OOP → DOD/PWP | redesign object-based execution and retained state | behavior contract, access/mutation, owners/lifetimes, current path | target passes/stores/typed relationships and old-to-target replacement map | [Transformation](engineering/10-oop-to-dod.md) |
| Necessity | decide which element should exist | relevant element, contract/consumer, ownership/lifetime | KEEP/REMOVE/MERGE/DERIVE/LOCALIZE/FLATTEN/BATCH or MEASURE/UNKNOWN with reason | [Element test](workflow.md#4-apply-the-element-necessity-test) |
| Data representation | choose identity, relations, storage | relevant contract, access/mutation pattern, bounds/lifetime | candidate types and trade-offs; unknown costs remain unverified | [Data shape](engineering/01-data-shape.md), [Canonical state](engineering/02-canonical-and-derived.md) |
| Ownership | evaluate sharing and synchronization | owners, lifetimes, concurrent access, FFI boundaries | ownership decision; required locks/handles retained | [Ownership](engineering/04-ownership-and-concurrency.md) |
| Work elimination | remove repeated operations/layers | affected operations, consumers, frequency, required boundaries | proposed eliminated/merged work and preserved behavior | [Hot-path work](engineering/03-hot-path-work.md), [YAGNI](engineering/05-yagni-and-cleanup.md) |
| Performance diagnosis | identify a cause before optimization | target, workload, baseline/profile or access to measure | bottleneck, causal hypothesis, missing evidence, selected rule family | [Diagnosis](performance/00-diagnosis.md) |
| Experiment | evaluate a concrete cost claim | candidate/hypothesis, baseline, workload, acceptance rule | matched evidence and accepted/rejected/unverified claim | [Measurement](performance/01-measurement.md), [Acceptance](performance/10-foundation.md) |
| Correctness | assess a proposed/implemented change | affected contract, code/design diff, relevant tests/oracle | preserved/violated invariants and missing verification | [Correctness boundaries](engineering/06-correctness-boundaries.md) |
| Implementation | implement a justified candidate or experiment | scoped contract, concrete decision, affected code | changed code, superseded state removed, verification result | [Implementation](workflow.md#7-implement-one-structural-decision-at-a-time), [Verification](workflow.md#8-verify-proportionally) |
| PWP retained state | retained pointers, children, derived fields, builder lifetime | owners/lifetimes, mutation, consumers, affected contract | keep/replace decision and identity/lifetime checks | [PWP decisions](engineering/compiler/profile/50-pwp-retained-state.md) |
| 512-byte / lexical profile | selected batch contract or measured lexical cause | grammar, source lifetime, backend targets; cost evidence for speed claims | selected mask/compaction/lookup technique and parity gates | [512 profile](engineering/compiler/25-pwp-512-profile.md) |
| Compiler specialization | apply a compiler-specific decision | relevant pipeline, lexical, retained-state, or validation inputs | result of the selected compiler block | [Compiler router](engineering/09-wide-pointerless-compiler.md) |

## Composition rules

1. Apply the structural override before selecting modules. Otherwise use the smallest module set that produces the requested result; a focused ownership question does not require full redesign.
2. Check minimum inputs. Reuse matching code/evidence; inspect or obtain only missing inputs. Do not rerun a module merely to satisfy order.
3. Carry results forward with the same scope, version, identity, and units. Recheck evidence only when a dependency changes or validity is uncertain.
4. An unresolved prerequisite blocks only dependent decisions. Continue independent analysis and label the affected result `UNKNOWN` or `UNVERIFIED`.
5. Before changing a mechanism whose necessity is unresolved, apply Necessity. Before a broad redesign, establish the affected typed process/data. A focused layout or ownership question can use the relevant supplied fragment.
6. Implementation requires affected-behavior verification. A performance claim requires Experiment. Analysis-only modules require neither a code change nor a benchmark unless their decision depends on measured cost.
7. Stop when the requested result and applicable gates are satisfied. Use [Workflow reporting](workflow.md#proportional-result-format) for all compositions.

## Choose and switch routes

**Route priority:** for architecture redesign or structural cleanup with OOP/layer signals, derive a minimal operation-first DOD/PWP target before local YAGNI. Apply the structural override before choosing a focused cleanup module. Focused questions and profiler-led diagnosis remain scoped.

| Situation | Start | Next decision |
| --- | --- | --- |
| architecture redesign or structural cleanup with OOP/layer signals | structural route | derive operation/access/layout first; remove or justify old layers against the target |
| performance target but missing/unreliable profile | performance diagnosis | establish matched baseline and relevant attribution before choosing a transformation |
| trusted profile identifies target cost | profiler route | rank measured hotspots and iterate the most relevant actionable cause |
| one focused question or supplied candidate | individual module | consume its minimum inputs and stop with its result |
| evidence insufficient to choose | smallest missing-input module | inspect the affected path or measure; do not invent a ranking |

**Structural route:** Contract → current behavior/process/data evidence → physical operation/access/layout → element necessity → target operations/passes/owned representations → old-to-target comparison → Implementation/Correctness → Experiment when claiming a cost improvement. For object-based code, use [OOP → DOD/PWP](engineering/10-oop-to-dod.md); existing internal callers do not prescribe the target architecture. A measurement can occur anywhere a design choice requires it.

A profile is usable when its workload, build, metric, and scope match the target and the measurement method is checked. If they do not match, obtain the missing evidence. A CPU-sample profile alone does not attribute blocked wall time or retained memory.

**Profiler route:**

1. Fix the target, representative workload, conditions, and acceptance rule. Inspect the current profile; obtain a baseline if missing.
2. Rank costs by measured contribution to that target. Distinguish CPU samples, elapsed time, allocations, retained memory, and waits. Do not add overlapping inclusive costs or infer an end-to-end gain directly from a sample percentage.
3. Select the cause with the largest supported contribution to the unmet target that can be changed within the contract/scope. When attribution cannot distinguish candidates, run a bounded diagnostic experiment instead of guessing their rank. A lower-ranked cause can come first for a shared prerequisite or contract constraint; state that reason. Do not optimize unrelated top entries.
4. Inspect only the affected path, its contract/consumers, and access pattern. Check necessity locally. Select the matching module/rule, form a concrete candidate and falsifiable prediction, then implement one causal change and verify behavior.
5. Repeat matched measurement, validate the causal metric and declared target, and reprofile. Keep, reject, or narrow the claim using the acceptance evidence. Rerank from the new profile; do not continue using the old top list after the workload/cost distribution changes.
6. Stop when the target passes or no supported change remains in scope. Report unresolved cost/evidence explicitly.

**Switch profiler → structural** when the cost crosses stages/owners, duplicate work/state explains multiple hotspots, or two consecutive valid experiments on the same representation show no supported progress in the declared target metric. Expand the map only as far as needed to investigate that cause. Invalid/noisy measurements require measurement repair; they do not count as evidence against the representation.

Distinguish the overall completion target from per-experiment progress and required guardrails. Declare them before evaluating results. A confirmed target-metric improvement beyond uncertainty, with correctness and guardrails passing, is progress even if the overall target is not yet met. Reprofile and continue from the new baseline. A local causal metric changing without target progress does not count. Reject a causal hypothesis whose predicted mechanism fails; investigate an unexplained improvement before crediting it to that hypothesis.

Example: target ≤60 ms; matched results 100 →90 →80 ms with uncertainty ±1 ms and passing guardrails show two useful steps. Report the overall target unmet and continue reranking. Extraction 8 →4 →2 ms while total remains 100 ±3 ms shows no supported total-time progress; after those two valid experiments inspect the broader cause. This is a diagnostic switch, not permission to weaken correctness or a mandatory full restart.

**Switch structural → profiler** when competing designs depend on unknown cost, the structural candidate leaves the target unmet, or measurement identifies a different dominant cause. Use the measurement to choose the next module; do not complete irrelevant design work for sequence compliance.

After a change invalidates an earlier assumption, revisit only dependent decisions. There is no mandatory full restart.

## Example routes

| Request | Composition | Stop condition |
| --- | --- | --- |
| “Does this lock have a responsibility?” | Ownership; add Necessity if the boundary is unclear | justified keep/remove decision or named missing concurrency fact |
| “Map this path; do not redesign it” | Process/data map | affected typed map and known counts; no candidate required |
| “Find duplicated state” | Canonical-state part of Data representation + Necessity | authorities/consumers identified; duplication conclusions supported |
| “Verify this claimed speedup” | Experiment + Correctness; Diagnosis if causal evidence is missing | supported result class or explicit missing evidence; no forced rewrite |
| “Latency is high; no profile yet” | Diagnosis → baseline and wall-time attribution | cause or missing evidence; no inferred SoA/512 rewrite |
| “Use PWP for this frozen graph; there is no lexer” | PWP retained state → identity/lifetime checks | justified pointer/ID/range choice; no batch-width analysis |
| “Convert this object subsystem to DOD/PWP” | Contract/current evidence → physical operation/layout → Transformation target → necessity/removal map → Implementation + Correctness | target passes/owners/typed relationships implemented; remaining constraints scoped; performance claims measured |

## Extend a capability

Add or refine a focused reference when a recurring decision needs instructions not already covered. Add one row here with its trigger, minimum inputs, result, and direct instruction link. Route it directly from this map or SKILL.md so it is discoverable.

Declare only real information dependencies. Reuse existing contract, correctness, measurement, and reporting rules. Keep specialized decision criteria in the new block. Do not copy the full workflow, create mandatory empty outputs, or add a framework solely to register a module.
