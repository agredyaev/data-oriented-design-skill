# Data-Oriented Design Workflow

Use [Module composition](modules.md) for scoped modules or profiler execution. The steps below describe a full structural redesign; verification/reporting apply to any route. Reuse evidence, execute missing prerequisites only, and do not claim skipped verification passed.

For a local fix with no representation, ownership, or boundary change, state affected behavior, make the fix, and verify it. No process map is required.

## 1. Fix the contract

Write the task as:

```text
INPUT → REQUIRED OUTPUT
```

Record only requirements that constrain the design:

- output values and ordering;
- identity rules;
- errors;
- security/authorization;
- persistence/wire/ABI compatibility;
- transaction/recovery semantics;
- concurrency requirements;
- explicit resource or performance budgets.

Unknown requirements are `UNKNOWN`. Do not invent them.

## 2. Draw the current process and data

Map only the affected input-to-output process using a typed table or Mermaid. For notation and counting examples, use [Mapping techniques](engineering/00-structural-analysis.md).

Each operation needs input/output types, read/write state, and known call count. Annotate relevant items, bytes, allocations, lookups, parse/normalize/copy/serialize work, locks/refcounts, IPC/syscalls and state transitions. Do not invent unknown counts.

For each retained structure identify:

- owner;
- lifetime;
- mutable or frozen;
- canonical or derived;
- relationship form: pointer / ID / offset / range / key;
- current consumers.

Do not map unrelated parts of the repository.

## 3. Derive the physical operation shape

Before examining whether old abstractions survive, derive a physical data path for each relevant recurring operation:

- exact fields/bytes read and written; item counts, frequency and traversal/order;
- hot fields used together, cold fields skipped, retained versus request-local data;
- parsing, hashing, lookup, copying, allocation and synchronization work;
- direct access or no intermediate representation where possible; otherwise justify streaming, AoS, SoA, hot/cold split, sparse side storage, typed IDs, offsets/ranges or scratch arrays from the access/mutation pattern.

Do not introduce target structs, services, repositories, DTOs, mappers or domain objects in this step. The result is an **operation/data/layout path**, not an architecture diagram.

**Gate:** If the access pattern and plausible physical layout are not established, do not design the target. Resolve blocking `UNKNOWN` facts. If a proposed target begins with current layers, return here.

## 4. Apply the element-necessity test

Existing elements have **no presumption of survival**. Test whether the *target operation* needs their responsibility, not whether a current wrapper performs useful work. If the work moves into a target pass/store, REMOVE or MERGE the wrapper and preserve the required behavior there.

Every element on the current process/data map must have a concrete reason to exist.

An **element** is a step, object/wrapper, retained structure, cache/index/view, field, pointer relationship, lock, protocol boundary, parser/serializer, layer or trait.

For each relevant element ask:

| Question to establish from contract/code | If no responsibility is found after inspection |
| --- | --- |
| Which required behavior needs its result, and which consumer observes that result? | candidate to remove |
| Why must it be a separate step/layer rather than merged with an adjacent step? | candidate to inline/merge |
| Why must it be retained rather than derived or local scratch? | candidate to derive/localize |
| Why must the relationship use pointer/key identity rather than a typed ID/offset/range? | candidate to flatten |
| Why must this transformation happen more than once? | candidate to move earlier and reuse |
| Why must this state be mutable/shared? | candidate to freeze or localize |
| What measured or semantic requirement justifies the added state/complexity? | candidate to remove |

Allowed decisions:

```text
KEEP       concrete requirement needs this form; simpler alternative fails a named check
REMOVE     no current responsibility
MERGE      separate step/layer adds no required boundary
DERIVE     deterministic value does not need retained authority
LOCALIZE   temporary state does not need global/shared lifetime
FLATTEN    object/pointer graph can become IDs/arrays/ranges
BATCH      repeated calls/transitions can become one operation
MEASURE    necessity depends on an unresolved cost
UNKNOWN    required consumer/semantic fact is not yet established
```

Absence of evidence is not evidence of no consumer. For `UNKNOWN`, inspect callers, persistence and lifetime before removal. `DERIVE` requires exact inputs and their lifetime; `FLATTEN` requires preserved identity and mutation semantics. These are candidates until their correctness and applicable cost gates pass.

For a full redesign, first extract responsibilities here; finalize KEEP/replace decisions only against the target in step 5. A current internal caller proves use, not necessity of the representation. Preserve required computations/checks and adapt internal callers to the target.

Do not require documentation for elements already obvious from the code and contract. Record only decisions that affect the design.

## 5. Design the replacement from the contract

Use the physical data path from step 3 to derive explicit passes/owned stores; only now name target types and modules. For object-based code, apply [OOP → DOD/PWP](engineering/10-oop-to-dod.md).

For a cost claim, establish baseline and cause through [Diagnosis](performance/00-diagnosis.md). Without measurements, a concrete proposal remains `UNVERIFIED`.

Create a candidate that preserves the contract and targets a named recurring cost or unnecessary structure. An index can add state to remove repeated search; count its build, update, memory and identity costs. A simpler-looking map alone does not establish a faster candidate.

Name types, reads/writes, owners and lifetimes. Mark old elements removed, merged, replaced or required by a demonstrated constraint.

Refine with selected DOD rules. Every new element also needs the necessity test.

## 6. Compare current and candidate

Compare only metrics relevant to the task.

For a structural delta, compare current/candidate steps, passes, retained representations/bytes, allocations, pointer/key lookups, parse/normalize operations, copies, locks/refcounts and protocol round-trips. Include only changed or disputed counts.

Use `?` when unknown.

Reject contract/guardrail violations. Compare the target and lifetime costs; measure disputed costs. For structural simplification, name removed elements, where their required responsibilities move, and new invariants. Counts alone do not prove speed.

Do not prefer a design merely because it changes fewer lines.

## 7. Implement one structural decision at a time

Implement one justified candidate first: the measured cause selected by the profiler route, or the structural removal whose consumers and replacement are established. Resolve required dependencies first. Implementation may be an experiment; adoption waits for verification.

During implementation:

- keep one canonical authority;
- remove superseded state instead of retaining both paths;
- keep temporary work local;
- preserve required validation/security/recovery boundaries;
- do not add compatibility wrappers, caches, registries, or traits without a current requirement;
- do not perform unrelated cleanup.

If implementation exposes a wrong assumption in the candidate map, update the map and design before continuing.

## 8. Verify proportionally

Always verify affected behavior.

Add only the evidence required by the claim:

| Claim | Required evidence |
| --- | --- |
| behavior preserved | relevant tests/code evidence |
| retained or peak memory reduced | matched evidence for that specific metric and lifecycle point |
| allocations reduced | allocation evidence |
| phase latency/throughput improved | matched benchmark of that phase; include new work moved outside it |
| end-to-end latency/throughput improved | matched end-to-end benchmark |
| scaling improved | multi-load or multi-thread scaling evidence |
| abstraction/state removed | code/structure inspection plus tests |

A local microbenchmark does not prove an end-to-end improvement.

Use [progress and switching](modules.md#choose-and-switch-routes) to distinguish a useful intermediate improvement from a failed experiment or completed target.

## Completion rule

Apply these gates to the selected scope. Analysis-only work completes with its conclusion, supporting evidence, and relevant unknowns; it does not require implementation or a benchmark. An implementation or accepted redesign is complete when:

- the required contract still holds;
- every added element has a concrete responsibility;
- removed elements have no remaining required consumer;
- a requested OOP → DOD/PWP conversion implements the target operations, owners and relationships; name partial scope or blockers explicitly;
- new construction, update, lifetime and identity obligations are accounted for;
- any performance claim has matched evidence;
- remaining unknowns are stated explicitly.

## Proportional result format

For a local fix, report the change, affected behavior, verification, and any unresolved issue. No structural report is required.

For a full architecture/performance redesign, use one compact report:

1. **Contract** — required behavior and relevant bounds.
2. **Current → candidate** — typed process/data maps; combine them when this remains readable.
3. **Decisions and delta** — only changed or disputed elements, relevant counts, and trade-offs.
4. **Verification and result** — behavior evidence; matched measurements for the claimed metric.
5. **Unknowns** — missing evidence, rejected candidates, or remaining defects that affect the decision.

Use `FINDING` for a supported issue/result, `UNVERIFIED` for an unsupported claim, `NO FINDING` when the inspected scope yields no supported issue, or `OUTSIDE DOD` when the cause needs another method. Name the scope and next diagnostic action for the latter; it does not mean the user's problem is solved. Attach rule IDs only when they explain a decision. Removing a named unnecessary layer may be accepted as structural simplification from code and behavior evidence.

Do not enumerate every considered rule, report `N/A` rows, repeat the same map in multiple sections, or create a separate artifact unless the task requires one. Include build/query/update/space costs only where the candidate changes them. Unknown values stay `?` or `UNKNOWN`.

For a scoped module, report its decision/result, evidence, and blocking unknowns; reuse existing maps by reference. Do not fill sections belonging to modules that were not selected. State when correctness or performance acceptance remains pending.

For a formal rule-coverage audit explicitly requested by the user, include the requested per-rule dispositions.
