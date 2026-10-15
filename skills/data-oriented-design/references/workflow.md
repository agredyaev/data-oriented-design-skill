# Data-Oriented Design Workflow

Use this file as the default full-route composition and the shared completion/reporting contract. Use [Module composition](modules.md) to select a single capability or assemble a different route. Focused explanations need only the relevant rule.

Choose structural or profiler-driven execution through [Module composition](modules.md#choose-and-switch-routes). Steps below describe a full structural redesign, not a universal order. Reuse matching inputs/evidence and execute only missing prerequisites. Analysis-only work stops with its selected conclusion. Do not claim skipped verification passed.

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

For a structural redesign, map only the affected input-to-output process. Use Mermaid when supported, or a compact typed table; use text diagrams when rendering is unavailable. Each operation must identify its input, output, state, and known call count. The following text illustrates the required information:

```text
[1] operation
    in:  TypeA
    out: TypeB
    read/write: StateX
        |
        v
[2] operation
    in:  TypeB
    out: TypeC
```

Annotate known costs on nodes or edges:

```text
calls
items
bytes
allocations
lookup
parse
normalize
copy/clone
serialize
lock/refcount
IPC/syscall
state transition
```

Also map the retained data owned by the path. A typed table or rendered diagram can carry the same information as this text example:

```text
RootState
  +-- container/type
  +-- container/type
  +-- relationship representation
```

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

| Question | If no |
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
```

Do not require documentation for elements already obvious from the code and contract. Record only decisions that affect the design.

## 4. Design the replacement from the contract

Create the candidate before changing the old object model. A candidate may keep the current process when code, contract, or measurement shows no justified simplification. Do not force a rewrite to satisfy the format.

For a performance task, establish the baseline and measured bottleneck before selecting a transformation. Use [Performance diagnosis](performance/00-diagnosis.md) when the cause is unknown. Missing evidence permits a concrete candidate marked `UNVERIFIED`, but never an invented performance finding.

Create a candidate process that solves the same contract with fewer explicit operations or less retained state, without adding more expensive invariants.

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

For architecture/performance work, use this structural delta:

| Metric | Current | Candidate |
| --- | ---: | ---: |
| process steps | | |
| full passes | | |
| retained representations | | |
| independent allocations | | |
| pointer/key lookups | | |
| parse/normalize operations | | |
| copies/clones | | |
| locks/refcount operations | | |
| IPC/protocol round-trips | | |
| retained bytes | | |

Use `?` when unknown.

Prefer the candidate that:

1. preserves the contract;
2. removes more recurring work/state;
3. adds fewer new invariants;
4. meets the stated budget.

Do not prefer a design merely because it changes fewer lines.

## 6. Implement one structural decision at a time

Implement the highest-leverage accepted decision first.

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
| memory reduced | matched retained/peak-memory evidence |
| allocations reduced | allocation evidence |
| latency/throughput improved | matched end-to-end benchmark |
| scaling improved | multi-load or multi-thread scaling evidence |
| abstraction/state removed | code/structure inspection plus tests |

A local microbenchmark does not prove an end-to-end improvement.

If two consecutive local changes on the same representation fail the declared target acceptance rule, stop micro-tuning and revisit the affected current/candidate process maps.

## Completion rule

Apply these gates to the selected scope. Analysis-only work completes with its conclusion, supporting evidence, and relevant unknowns; it does not require implementation or a benchmark. An implementation or accepted redesign is complete when:

- the required contract still holds;
- every added element has a concrete responsibility;
- removed elements have no remaining required consumer;
- the candidate process is no more complex than needed for the contract;
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

Use `FINDING`, `UNVERIFIED`, `NO FINDING`, or `OUTSIDE DOD` for conclusions. Attach rule IDs only when they explain a decision. An unmeasured speed/memory proposal is `UNVERIFIED`; removing a named unnecessary layer may be accepted as structural simplification from code and behavior evidence.

Do not enumerate every considered rule, report `N/A` rows, repeat the same map in multiple sections, or create a separate artifact unless the task requires one. Include build/query/update/space costs only where the candidate changes them. Unknown values stay `?` or `UNKNOWN`.

For a scoped module, report its decision/result, evidence, and blocking unknowns; reuse existing maps by reference. Do not fill sections belonging to modules that were not selected. State when correctness or performance acceptance remains pending.

For a formal rule-coverage audit explicitly requested by the user, include the requested per-rule dispositions.
