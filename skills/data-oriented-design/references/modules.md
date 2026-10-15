# Module Composition

Select capabilities by the result requested. Modules are independent instructions with information dependencies, not mandatory phases. Inputs/results may be code, supplied evidence, or a few inline notes; they do not require new documents or schemas.

## Module contracts

| Module | Use for | Minimum inputs | Result | Instructions |
| --- | --- | --- | --- | --- |
| Contract | clarify required behavior | task, consumers, external boundaries | required input/output, invariants, bounds, unknowns | [Contract](workflow.md#1-fix-the-contract) |
| Process/data map | understand current transformations/state | affected code or a supplied design | typed operations, owners, lifetimes, consumers, known counts | [Mapping techniques](engineering/00-structural-analysis.md) |
| Necessity | decide which element should exist | relevant element, contract/consumer, ownership/lifetime | KEEP/REMOVE/MERGE/DERIVE/LOCALIZE/FLATTEN/BATCH/MEASURE with reason | [Element test](workflow.md#3-apply-the-element-necessity-test) |
| Data representation | choose identity, relations, storage | relevant contract, access/mutation pattern, bounds/lifetime | candidate types and trade-offs; unknown costs remain unverified | [Data shape](engineering/01-data-shape.md), [Canonical state](engineering/02-canonical-and-derived.md) |
| Ownership | evaluate sharing and synchronization | owners, lifetimes, concurrent access, FFI boundaries | ownership decision; required locks/handles retained | [Ownership](engineering/04-ownership-and-concurrency.md) |
| Work elimination | remove repeated operations/layers | affected operations, consumers, frequency, required boundaries | proposed eliminated/merged work and preserved behavior | [Hot-path work](engineering/03-hot-path-work.md), [YAGNI](engineering/05-yagni-and-cleanup.md) |
| Performance diagnosis | identify a cause before optimization | target, workload, baseline/profile or access to measure | bottleneck, causal hypothesis, missing evidence, selected rule family | [Diagnosis](performance/00-diagnosis.md) |
| Experiment | evaluate a concrete cost claim | candidate/hypothesis, baseline, workload, acceptance rule | matched evidence and accepted/rejected/unverified claim | [Measurement](performance/01-measurement.md), [Acceptance](performance/10-foundation.md) |
| Correctness | assess a proposed/implemented change | affected contract, code/design diff, relevant tests/oracle | preserved/violated invariants and missing verification | [Correctness boundaries](engineering/06-correctness-boundaries.md) |
| Implementation | execute an accepted decision | scoped contract, concrete decision, affected code | changed code, superseded state removed, verification result | [Implementation](workflow.md#6-implement-one-structural-decision-at-a-time), [Verification](workflow.md#7-verify-proportionally) |
| PWP / 512-byte profile | selected 512-byte contract or measured lexical cause | grammar, source lifetime, backend targets; cost evidence for speed claims | selected mask/compaction/lookup technique and parity gates | [PWP/512 profile](engineering/compiler/25-pwp-512-profile.md) |
| Compiler specialization | apply a compiler-specific decision | relevant pipeline, lexical, retained-state, or validation inputs | result of the selected compiler block | [Compiler router](engineering/09-wide-pointerless-compiler.md) |

## Composition rules

1. Select the smallest module set that produces the requested result. “Analyze ownership” selects Ownership, not the entire redesign route.
2. Check minimum inputs. Reuse matching code/evidence; inspect or obtain only missing inputs. Do not rerun a module merely to satisfy order.
3. Carry results forward with the same scope, version, identity, and units. Recheck evidence only when a dependency changes or validity is uncertain.
4. An unresolved prerequisite blocks only dependent decisions. Continue independent analysis and label the affected result `UNKNOWN` or `UNVERIFIED`.
5. Before changing a mechanism whose necessity is unresolved, apply Necessity. Before a broad redesign, establish the affected typed process/data. A focused layout or ownership question can use the relevant supplied fragment.
6. Implementation requires affected-behavior verification. A performance claim requires Experiment. Analysis-only modules require neither a code change nor a benchmark unless their decision depends on measured cost.
7. Stop when the requested result and applicable gates are satisfied. Use [Workflow reporting](workflow.md#proportional-result-format) for all compositions.

## Choose and switch routes

Select from the question and available evidence. Neither route takes precedence universally.

| Situation | Start | Next decision |
| --- | --- | --- |
| broad redesign, unclear state/ownership, no trusted cost attribution | structural route | map current contract/process/data, remove unnecessary elements, compare a candidate |
| trusted profile identifies target cost | profiler route | rank measured hotspots and iterate the most relevant actionable cause |
| one focused question or supplied candidate | individual module | consume its minimum inputs and stop with its result |
| evidence insufficient to choose | smallest missing-input module | inspect the affected path or measure; do not invent a ranking |

**Structural route:** Contract → Process/data map → Necessity → selected representation/ownership/work modules → candidate comparison → Implementation/Correctness → Experiment when claiming a cost improvement. A measurement can occur anywhere a design choice requires it.

**Profiler route:**

1. Fix the target, representative workload, conditions, and acceptance rule. Inspect the current profile; obtain a baseline if missing.
2. Rank costs by measured contribution to that target. Distinguish CPU samples, elapsed time, allocations, retained memory, and waits. Do not add overlapping inclusive costs or infer an end-to-end gain directly from a sample percentage.
3. Select the highest-impact actionable cause supported by evidence. A lower-ranked cause can come first when a shared prerequisite, contract constraint, or bounded experiment justifies it; state that reason. Do not optimize unrelated top entries.
4. Inspect only the affected path, its contract/consumers, and access pattern. Check necessity locally. Select the matching module/rule, form a concrete candidate and falsifiable prediction, then implement one causal change and verify behavior.
5. Repeat matched measurement, validate the causal metric and declared target, and reprofile. Keep, reject, or narrow the claim using the acceptance evidence. Rerank from the new profile; do not continue using the old top list after the workload/cost distribution changes.
6. Stop when the target passes or no supported change remains in scope. Report unresolved cost/evidence explicitly.

**Switch profiler → structural** when the cost crosses stages/owners, duplicate work/state explains multiple hotspots, or two consecutive local changes on the same representation fail the declared target acceptance rule. Expand the map only as far as needed to investigate that cause.

**Switch structural → profiler** when competing designs depend on unknown cost, the structural candidate leaves the target unmet, or measurement identifies a different dominant cause. Use the measurement to choose the next module; do not complete irrelevant design work for sequence compliance.

After a change invalidates an earlier assumption, revisit only dependent decisions. There is no mandatory full restart.

## Example routes

| Request | Composition | Stop condition |
| --- | --- | --- |
| “Does this lock have a responsibility?” | Ownership; add Necessity if the boundary is unclear | justified keep/remove decision or named missing concurrency fact |
| “Map this path; do not redesign it” | Process/data map | affected typed map and known counts; no candidate required |
| “Find duplicated state” | Canonical-state part of Data representation + Necessity | authorities/consumers identified; duplication conclusions supported |
| “Verify this claimed speedup” | Experiment + Correctness; Diagnosis if causal evidence is missing | supported result class or explicit missing evidence; no forced rewrite |
| “Simplify this full pipeline and implement it” | Contract → Map → Necessity → candidate modules → Implementation + Correctness; Experiment for cost claims | affected contract preserved and claimed result supported |

## Extend a capability

Add or refine a focused reference when a recurring decision needs instructions not already covered. Add one row here with its trigger, minimum inputs, result, and direct instruction link. Route it directly from this map or SKILL.md so it is discoverable.

Declare only real information dependencies. Reuse existing contract, correctness, measurement, and reporting rules. Keep specialized decision criteria in the new block. Do not copy the full workflow, create mandatory empty outputs, or add a framework solely to register a module.
