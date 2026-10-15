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

## 3. Apply the element-necessity test

Every element on the current process/data map must have a concrete reason to exist.

An **element** is any:

- process step;
- object or wrapper;
- retained structure;
- cache/index/view;
- stored field;
- pointer/reference relationship;
- lock/shared-mutation point;
- protocol/API/IPC boundary;
- parser/normalizer/serializer;
- abstraction layer or trait.

For each relevant element ask:

| Question to establish from contract/code | If no responsibility is found after inspection |
| --- | --- |
| Which contract requirement or current consumer requires it? | candidate to remove |
| Why must it be a separate step/layer rather than merged with an adjacent step? | candidate to inline/merge |
| Why must it be retained rather than derived or local scratch? | candidate to derive/localize |
| Why must the relationship use pointer/key identity rather than a typed ID/offset/range? | candidate to flatten |
| Why must this transformation happen more than once? | candidate to move earlier and reuse |
| Why must this state be mutable/shared? | candidate to freeze or localize |
| What measured or semantic requirement justifies the added state/complexity? | candidate to remove |

Allowed decisions:

```text
KEEP       concrete contract/consumer requires it
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

Do not require documentation for elements already obvious from the code and contract. Record only decisions that affect the design.

## 4. Design the replacement from the contract

Create a candidate before changing the old object model. Keep the current process when no justified simplification exists.

For a performance task, establish the baseline and measured bottleneck before selecting a transformation. Use [Performance diagnosis](performance/00-diagnosis.md) when the cause is unknown. Missing evidence permits a concrete candidate marked `UNVERIFIED`, but never an invented performance finding.

Create a candidate that preserves the contract and targets a named recurring cost or unnecessary structure. An index can add state to remove repeated search; count its build, update, memory and identity costs. A simpler-looking map alone does not establish a faster candidate.

```text
CURRENT
A → B → C → D → E → output

CANDIDATE
A → C → E → output
```

Name concrete data types in both maps.

For retained data, prefer the simplest representation that supports the candidate process:

```text
State
  +-- rows[]
  +-- offsets[]
  +-- ids[]
  +-- side_data[]
  +-- indexes[]
```

Use detailed DOD rules to refine the candidate, in either execution route.

The candidate is valid only if every new element also passes the element-necessity test.

## 5. Compare current and candidate

Compare only metrics relevant to the task.

For a structural delta, compare current/candidate steps, passes, retained representations/bytes, allocations, pointer/key lookups, parse/normalize operations, copies, locks/refcounts and protocol round-trips. Include only changed or disputed counts.

Use `?` when unknown.

Reject candidates that violate the contract or a required budget. Compare remaining candidates on the declared target, including lifetime costs. If evidence cannot distinguish them, retain the current design or measure the disputed cost. For structural simplification, name the eliminated responsibility-free element and any new invariants; do not infer speed from counts.

Do not prefer a design merely because it changes fewer lines.

## 6. Implement one structural decision at a time

Implement one justified candidate first: the measured cause selected by the profiler route, or the structural removal whose consumers and replacement are established. Resolve required dependencies first. Implementation may be an experiment; adoption waits for verification.

During implementation:

- keep one canonical authority;
- remove superseded state instead of retaining both paths;
- keep temporary work local;
- preserve required validation/security/recovery boundaries;
- do not add compatibility wrappers, caches, registries, or traits without a current requirement;
- do not perform unrelated cleanup.

If implementation exposes a wrong assumption in the candidate map, update the map and design before continuing.

## 7. Verify proportionally

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

If two consecutive local changes on the same representation fail the declared target acceptance rule, stop micro-tuning and revisit the affected current/candidate process maps.

## Completion rule

Apply these gates to the selected scope. Analysis-only work completes with its conclusion, supporting evidence, and relevant unknowns; it does not require implementation or a benchmark. An implementation or accepted redesign is complete when:

- the required contract still holds;
- every added element has a concrete responsibility;
- removed elements have no remaining required consumer;
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
