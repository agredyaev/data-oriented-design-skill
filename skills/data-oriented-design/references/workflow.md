# Data-Oriented Design Workflow

Use this workflow for implementation or formal review. It is intentionally short. Detailed rules live in the routed engineering and performance references.

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

For a non-trivial path, produce one typed ASCII process map:

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

Also draw the retained data owned by the path:

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

Do not modify the old object model in place first.

Create a candidate process that solves the same contract with fewer explicit operations and less retained state.

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

Use detailed DOD rules only after this candidate exists.

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

If two consecutive local changes on the same representation do not materially move the target metric, stop micro-tuning and return to the current/candidate process maps.

## Completion rule

A change is complete when:

- the required contract still holds;
- every added element has a concrete responsibility;
- removed elements have no remaining required consumer;
- the candidate process is no more complex than needed for the contract;
- any performance claim has matched evidence;
- remaining unknowns are stated explicitly.

## Compact result format

For a review or implementation, report only:

1. **Contract**
2. **Current typed process/data map**
3. **Element decisions** — only KEEP/REMOVE/MERGE/DERIVE/LOCALIZE/FLATTEN/BATCH/MEASURE decisions that matter
4. **Candidate typed process/data map**
5. **Structural delta**
6. **Verification**
7. **Remaining unknowns/findings**
