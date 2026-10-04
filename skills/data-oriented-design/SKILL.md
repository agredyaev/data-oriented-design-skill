---
name: data-oriented-design
description: Use when reviewing memory or runtime costs of retained collections in code. Propose concrete AoS/SoA, flat-array, cache, and ID-based redesigns; check time, space, and behavior across languages.
---

# Data-Oriented Design

Find the expensive work before you change data layout. Measure the work, access pattern, bottleneck, and end-to-end result. Use DOD only after evidence identifies a physical cost.

**Build** creates or updates retained data. **Query** reads it. **Canonical** data defines identity and output order. `N` is rows, `M` another input count, `Q` queries, `U` updates, and `K` returned rows. Examples are hypothetical. Derived counts are not benchmark results. Bytes use decimal units.

## Language rules

Use these rules for all skill output.

- Use active voice.
- Use the imperative for procedures.
- Put one instruction in each procedural sentence.
- Use the same term with the same meaning.
- Avoid vague pronouns.
- Avoid unnecessary synonyms.
- Keep procedural sentences at 20 words or fewer.
- Keep descriptive sentences at 25 words or fewer.
- Keep paragraphs at six sentences or fewer.
- Keep noun clusters to three words when practical.
- Prefer simple present for descriptions.
- Do not use passive voice in procedures.
- Put conditions before the instruction when this improves clarity.
- Use vertical lists for three or more related items.
- Keep code terms unchanged when the code defines the term.

These rules use the style of Simplified Technical English. They do not claim certified ASD-STE100 compliance.

## Core model

Use this model to reason about cost:

```text
Total cost ≈
logical work
× visits per item
× physical cost per visit
+ allocation cost
+ synchronization cost
+ I/O cost
```

Optimize in this order:

1. Remove unnecessary work.
2. Remove repeated work.
3. Reduce the physical cost per visit.
4. Improve access order and locality.
5. Improve data ownership and parallel scaling.
6. Validate the predicted cause.

## Run one performance experiment

1. Freeze the workload and benchmark conditions.
2. Test scaling with `N`, `2N`, and `4N`.
3. Find the phase and operation that dominate wall time.
4. Classify the bottleneck before you select a DOD change.
5. Record the access pattern for the hot operation.
6. Select the smallest change that targets the measured cause.
7. Write a falsifiable prediction before implementation.
8. Measure the predicted physical metric after the change.
9. Measure phase time, total time, memory, and correctness.

Use the same input for the before and after runs. Run enough repetitions to expose noise. Separate cold, warm, and incremental workloads when they have different behavior.

### Workload contract

Record these values before each experiment:

```text
input
input distribution
build mode
feature flags
thread count
machine
CPU affinity, if used
compiler flags
cache state
output validation
repetition count
```

Use a workload matrix when scale or distribution changes the access pattern:

| Dimension | Suggested cases |
| --- | --- |
| Scale | small, medium, production, stress |
| Cardinality | low, normal, high |
| Cache state | cold, warm |
| Change size | full, incremental |
| Relation width | short, normal, long-tail |

### Scaling gate

Count logical operations as well as wall time.

Record, when applicable:

```text
rows visited
edges visited
lookups
hash operations
comparisons
copies
bytes copied
allocations
passes
```

If work grows faster than the required result, fix the algorithm first. Do not use layout work to hide avoidable work.

### Bottleneck classes

Classify the hot operation before you select a transformation.

| Class | Typical evidence |
| --- | --- |
| Algorithmic | excess operations, poor scaling, repeated work |
| Memory | cache misses, bandwidth, dependent loads, TLB walks, store pressure |
| Core | expensive arithmetic, hashing, divides, dependency chains |
| Front end | instruction-cache or decode pressure |
| Branch | high miss rate or bad speculation |
| Allocation | malloc/free, realloc, copies, fragmentation |
| Synchronization | locks, atomics, false sharing, contention |
| I/O | filesystem, serialization, syscalls |

### Access profile

Record these properties for the hot operation:

| Property | Question |
| --- | --- |
| Count | How many items does the operation visit? |
| Visits | How many times does it visit each item? |
| Reads | Which fields does it read? |
| Writes | Which fields does it write? |
| Order | Is access sequential, clustered, or random? |
| Indirection | How many dependent loads occur? |
| Collections | Does each row own variable-size data? |
| Cardinality | How many values are unique? |
| Optionality | How often is each optional field present? |
| Lifetime | How long does each allocation stay live? |
| Reuse | When does the operation use the same data again? |
| Ownership | Which thread reads or changes the data? |

Use static access amplification only as a screening metric:

```text
static access amplification =
physical record width
/
logically required field width
```

Do not treat this ratio as measured memory traffic. Cache lines, prefetch, reuse, TLB behavior, and stores can change the real cost.

## Global decision tree

```text
START
 |
 |-- Does N -> 2N cause more than expected work?
 |      |-- YES -> Fix algorithmic work or repeated visits.
 |      '-- NO
 |
 |-- Is one phase responsible for meaningful wall time?
 |      |-- NO -> Stop. The candidate cannot move the target KPI.
 |      '-- YES
 |
 |-- What limits the hot operation?
 |      |-- Too many operations -> DOD-003, DOD-018, DOD-021
 |      |-- Too many full passes -> fuse, cache, or remove a pass
 |      |-- Wide scan -> DOD-006, DOD-014, DOD-015, DOD-023
 |      |-- Random dependent loads -> DOD-005, DOD-008, DOD-019
 |      |-- Variable child allocations -> DOD-007
 |      |-- Repeated string/value storage -> DOD-022
 |      |-- Realloc/copy traffic -> preallocate and use DOD-010
 |      |-- Rare derived data -> DOD-017
 |      |-- Mostly inactive rows -> DOD-020
 |      |-- Repeated search -> DOD-021
 |      '-- Synchronization -> local ownership, sharding, partitioning
 |
 |-- Write a prediction for one physical metric.
 |-- Implement the smallest change.
 |-- Did the predicted metric improve?
 |      |-- NO -> Reject the performance hypothesis.
 |      '-- YES
 |
 |-- Did the target phase improve beyond noise?
 |      |-- NO -> Classify as memory/structure win only, if applicable.
 |      '-- YES
 |
 '-- Did end-to-end KPI and correctness pass?
        |-- NO -> Reject or narrow the change.
        '-- YES -> Adopt.
```

## Transformation map

| Measured cause | Candidate change | Main rules |
| --- | --- | --- |
| Avoidable logical work | prune, index, incremental update | DOD-003, DOD-018, DOD-021 |
| Repeated full passes | remove, fuse, cache | DOD-003, DOD-010, DOD-018 |
| Wide AoS scan | SoA, hot/cold split, AoSoA | DOD-006, DOD-014 |
| Pointer chasing | dense owner plus typed IDs | DOD-005, DOD-008, DOD-019 |
| Per-row child allocation | side array plus range | DOD-007 |
| Repeated string keys | string pool plus typed ID | DOD-022 |
| Sparse optional payload | present-only side storage | DOD-015 |
| Wide variant rows | common columns plus side payloads | DOD-016 |
| Rare derived fields | recompute from retained source | DOD-017 |
| Mostly inactive rows | active partition or active IDs | DOD-020 |
| Repeated key search | index with lifetime cost | DOD-021 |
| Many independent flags | packed mask | DOD-023 |
| Reallocation and copy | preallocate or reuse scratch | DOD-010 |
| Poor temporal locality | fusion, blocking, clustering | DOD-003, DOD-006, DOD-010 |
| Shared mutable state | local ownership, sharding | DOD-010, DOD-012 |

## Layout choices

Choose between AoS, SoA, and AoSoA from the measured access pattern.

- Keep AoS when most fields are used together.
- Test SoA for sequential field-subset scans.
- Test AoSoA when pure SoA increases page or TLB pressure.
- Benchmark the chunk size for AoSoA.
- Do not rebuild full rows inside a hot SoA loop.

## Access-order choices

Layout is only one part of DOD.

Test these changes when locality or visit count is the problem:

- Fuse passes when they use the same data and preserve semantics.
- Split a pass when rare cold work pollutes the hot path.
- Block work when a smaller working set can stay in cache.
- Cluster work when a key causes random access.
- Include sort or reorder cost in the result.

## Reads, writes, and lifetime

Measure reads and writes.

Record:

```text
bytes read
bytes written
copies
memcpy bytes
producer stores
packing stores
allocation count
allocated bytes
reallocated bytes
peak live bytes
```

A smaller read path can still lose end-to-end when build or packing writes increase.

## Concurrency gate

Build a scaling curve before you add sharding:

```text
threads | wall
1
2
4
8
16
```

If scaling stops, classify the cause:

```text
serial fraction
lock contention
atomic contention
false sharing
memory bandwidth saturation
load imbalance
scheduler overhead
NUMA
```

Use thread-local storage, sharding, or cache-line isolation only after evidence supports the cause.

## Measurement rules

- Use repeated runs.
- Report median and variation.
- Keep before and after conditions equal.
- Interleave A/B runs when machine drift can matter.
- Separate cold and warm workloads.
- Measure PMU events in small related groups.
- Check PMU multiplexing and time-running values.
- Do not infer speed from Big O or row width alone.

## Falsifiable hypothesis

Write this block before implementation:

```text
HOTSPOT
<operation and share of target time>

EVIDENCE
<measurement that identifies the cost>

HYPOTHESIS
<physical cause>

CHANGE
<smallest proposed transformation>

PREDICTION
<metric that must move and direction>

CORRECTNESS
<invariants that must remain true>
```

If the predicted physical metric does not move, reject the performance hypothesis.

## Result classes

Use one result class:

- **PERFORMANCE WIN** — target wall time improves, and the causal metric supports the hypothesis.
- **MEMORY WIN** — memory or artifact size improves, but wall time does not.
- **SCALABILITY WIN** — larger workloads improve more than small workloads.
- **PARALLEL WIN** — thread scaling improves.
- **NO EFFECT** — target metrics stay within noise.
- **REGRESSION** — a target budget becomes worse.

## Code signatures

| Code signature | Candidate end state | Rule |
| --- | --- | --- |
| Repeated loop over `N` AoS rows reads only `row.key` | Dense `keys[i]`; keep related payload fields together | DOD-006 |
| AoS row repeats alignment padding `N` times | Reorder fields, or split columns when padding remains | DOD-014, DOD-006 |
| Parent rows each own a child array | One child array; each parent stores `(offset, length)` | DOD-007 |
| Long-lived pointers refer to movable rows | One row owner; checked typed IDs outside it | DOD-005 |
| Rows retain repeated string keys | Intern bytes once; store bounded `StringId` values | DOD-022 |
| Build resolves names, but rows retain string links | Resolve once to typed row IDs | DOD-008 |
| Every row stores a derivable value | Keep the source inputs; derive the value on demand | DOD-017 |
| A pass reads only `row.flag` | Use a flag column or bitset after measurement | DOD-006, DOD-023 |
| Every row pays for the largest variant | Common columns plus present-only payload arrays | DOD-016 |
| Optional payload is reserved in every row | Core rows plus present-only side storage | DOD-015 |
| A repeated loop skips inactive rows | Active partition or active IDs | DOD-020 |
| Repeated `N × M` scan or key search | Grouped rows or an index with maintenance cost | DOD-003, DOD-021 |
| Repeated queries recompute one result | Cache or incrementally maintain the result | DOD-003, DOD-010 |
| Several full passes use the same data | Fuse or block the passes when semantics allow | DOD-003, DOD-010 |
| Pure SoA causes page or TLB pressure | Use bounded SoA chunks inside an AoSoA layout | DOD-006 |

## Decision trees for every rule

### DOD-001 decision tree

```text
Do you know who builds, owns, reads, updates, and emits the data?
 |-- NO -> Trace the full lifetime.
 '-- YES
      |
      |-- Does each proposed deletion have a named last consumer?
      |      |-- NO -> Keep the data.
      |      '-- YES -> Record the release point.
      |
      '-- Does reordering preserve canonical identity and output order?
             |-- NO -> Keep canonical order or add an order index.
             '-- YES -> Continue.
```

### DOD-002 decision tree

```text
Did the review find a repeated cost or a budget breach?
 |-- NO -> NO FINDING.
 '-- YES
      |
      |-- Is there a concrete before -> after representation?
      |      |-- NO -> Add one.
      |      '-- YES
      |
      |-- Are target costs and invariants stated?
      |      |-- NO -> Add them.
      |      '-- YES -> FINDING or UNVERIFIED.
```

### DOD-003 decision tree

```text
Does work scale with N, M, Q, or U?
 |-- NO -> Measure fixed overhead instead.
 '-- YES
      |
      |-- Is avoidable work larger than layout cost?
      |      |-- YES -> Change the algorithm first.
      |      '-- NO
      |
      |-- Do repeated passes touch the same data?
      |      |-- YES -> Test fusion, caching, or incrementality.
      |      '-- NO -> Calculate build, query, update, and space costs.
```

### DOD-004 decision tree

```text
Does the current path exceed a stated budget?
 |-- NO -> Keep it. Report NO FINDING.
 '-- YES
      |
      |-- Is the budget based on worst-case valid input?
      |      |-- NO -> Add the missing bound.
      |      '-- YES -> Evaluate a replacement.
```

### DOD-005 decision tree

```text
Do retained rows use pointers or one allocation per node?
 |-- NO -> N/A.
 '-- YES
      |
      |-- Does profiling show pointer, cache, TLB, or memory cost?
      |      |-- NO -> UNVERIFIED.
      |      '-- YES
      |
      |-- Can one owner address every row by a bounded slot?
      |      |-- NO -> Keep pointers or use another stable handle.
      |      '-- YES -> Test typed IDs.
```

### DOD-006 decision tree

```text
Does a hot pass read only a field subset?
 |-- NO
 |    '-- Do repeated rows waste alignment padding?
 |           |-- NO -> Keep AoS.
 |           '-- YES -> Test reorder or split columns.
 '-- YES
      |
      |-- Is access sequential?
      |      |-- YES -> Test SoA.
      |      '-- NO -> Test hot/cold split or AoSoA.
      |
      '-- Do most consumers need full rows?
             |-- YES -> Keep AoS or use AoSoA.
             '-- NO -> Keep the best measured split.
```

### DOD-007 decision tree

```text
Does each parent own a separate child allocation?
 |-- NO -> N/A.
 '-- YES
      |
      |-- Is child traversal mostly sequential and stable?
      |      |-- NO -> Keep a dynamic structure.
      |      '-- YES
      |
      |-- Do arbitrary parent appends need O(1)?
             |-- YES -> Use another append-friendly representation.
             '-- NO -> Test one child array plus ranges.
```

### DOD-008 decision tree

```text
Does runtime traversal resolve internal links from strings?
 |-- NO -> N/A.
 '-- YES
      |
      |-- Can build validate and resolve the name once?
      |      |-- NO -> Keep runtime lookup.
      |      '-- YES
      |
      '-- Are names still required for output?
             |-- YES -> Keep names at the output boundary.
             '-- NO -> Retain only typed IDs.
```

### DOD-009 decision tree

```text
Can a field use fewer bits?
 |-- NO -> N/A.
 '-- YES
      |
      |-- Is the maximum valid value enforced?
      |      |-- NO -> Do not narrow.
      |      '-- YES
      |
      |-- Do sentinels also fit?
             |-- NO -> Keep the wider field.
             '-- YES -> Measure size and conversion cost.
```

### DOD-010 decision tree

```text
Does a pass allocate or retain temporary state?
 |-- NO -> N/A.
 '-- YES
      |
      |-- Is the state needed after the operation?
      |      |-- NO -> Use local reusable scratch.
      |      '-- YES
      |
      |-- Is the same result reused enough to repay retention?
             |-- NO -> Recompute locally.
             '-- YES -> Cache with explicit invalidation.
```

### DOD-011 decision tree

```text
Does the change alter layout, identity, order, or mutation behavior?
 |-- NO -> Run normal product tests.
 '-- YES
      |
      |-- Is there an independent behavior oracle?
      |      |-- NO -> Add one before acceptance.
      |      '-- YES
      |
      '-- Do stale IDs, errors, order, and serialization match?
             |-- NO -> Reject.
             '-- YES -> Continue to performance acceptance.
```

### DOD-012 decision tree

```text
Do before and after use the same workload?
 |-- NO -> Benchmark is invalid.
 '-- YES
      |
      |-- Are repetitions and variation reported?
      |      |-- NO -> Repeat the benchmark.
      |      '-- YES
      |
      |-- Are build, query, update, memory, and wall costs measured?
      |      |-- NO -> Complete the trade-off.
      |      '-- YES
      |
      '-- Does the predicted metric move with the target KPI?
             |-- NO -> Reject the performance hypothesis.
             '-- YES -> Accept if correctness also passes.
```

### DOD-013 decision tree

```text
Can a reader reproduce the finding?
 |-- NO -> Add location, counts, costs, and evidence.
 '-- YES
      |
      |-- Is the before -> after design explicit?
      |      |-- NO -> Add it.
      |      '-- YES
      |
      '-- Is the acceptance measurement named?
             |-- NO -> Mark UNVERIFIED and name it.
             '-- YES -> Report the result class.
```

### DOD-014 decision tree

```text
Is row size larger than the field sum?
 |-- NO -> N/A.
 '-- YES
      |
      |-- Can private fields be reordered safely?
      |      |-- YES -> Test reorder first.
      |      '-- NO
      |
      |-- Does padding repeat across many retained rows?
             |-- NO -> Keep layout.
             '-- YES -> Test DOD-006 column split.
```

### DOD-015 decision tree

```text
Does every row reserve a large optional payload?
 |-- NO -> N/A.
 '-- YES
      |
      |-- Is presence sparse enough to save total bytes?
      |      |-- NO -> Keep inline.
      |      '-- YES
      |
      |-- Does side lookup meet its read and update budgets?
             |-- NO -> Keep inline.
             '-- YES -> Use present-only side storage.
```

### DOD-016 decision tree

```text
Does every row pay for the largest variant or subclass pointer?
 |-- NO -> N/A.
 '-- YES
      |
      |-- Are common fields shared across variants?
      |      |-- NO -> Keep separate variant owners.
      |      '-- YES
      |
      |-- Are rare payloads sparse?
             |-- NO -> Test compact tagged rows.
             '-- YES -> Test common columns plus side payloads.
```

### DOD-017 decision tree

```text
Is a retained field fully derivable from retained input?
 |-- NO -> Keep it.
 '-- YES
      |
      |-- Is the field read rarely enough to repay recompute?
      |      |-- NO -> Keep it.
      |      '-- YES
      |
      '-- Does source lifetime cover every read?
             |-- NO -> Keep the field.
             '-- YES -> Test on-demand derivation.
```

### DOD-018 decision tree

```text
Does an unchanged input trigger parse, rebuild, or serialization?
 |-- NO -> N/A.
 '-- YES
      |
      |-- Is there a trusted identity or version check?
      |      |-- NO -> Add safe change detection first.
      |      '-- YES
      |
      '-- Can the check skip work without skipping validation?
             |-- NO -> Keep full work.
             '-- YES -> Skip unchanged work.
```

### DOD-019 decision tree

```text
Does a sequential scan perform one random lookup per row?
 |-- NO -> N/A.
 '-- YES
      |
      |-- Is companion data stable for the scan lifetime?
      |      |-- NO -> Keep the lookup.
      |      '-- YES
      |
      '-- Can build align companion data by row ID?
             |-- NO -> Use a stable dense ID.
             '-- YES -> Scan the companion array directly.
```

### DOD-020 decision tree

```text
Does a repeated pass skip many inactive rows?
 |-- NO -> N/A.
 '-- YES
      |
      |-- Are state transitions rare enough to repay moves?
      |      |-- NO -> Keep the flag scan.
      |      '-- YES
      |
      |-- May rows move?
             |-- YES -> Test active/inactive partitions.
             '-- NO -> Test an active-ID list.
```

### DOD-021 decision tree

```text
Do repeated exact or range queries scan the same rows?
 |-- NO -> N/A.
 '-- YES
      |
      |-- Does index build plus maintenance fit the workload?
      |      |-- NO -> Keep the scan.
      |      '-- YES
      |
      '-- Is Q above the measured break-even point?
             |-- NO -> Keep the scan.
             '-- YES -> Add the index.
```

### DOD-022 decision tree

```text
Do retained rows repeat string keys or hash the same bytes?
 |-- NO -> N/A.
 '-- YES
      |
      |-- Is unique_count much smaller than occurrence_count?
      |      |-- NO -> Measure before interning.
      |      '-- YES
      |
      |-- Can one owned pool keep stable string identity?
             |-- NO -> Keep strings.
             '-- YES -> Test StringId plus byte pool.
```

### DOD-023 decision tree

```text
Do rows store several independent boolean fields?
 |-- NO -> N/A.
 '-- YES
      |
      |-- Does a mask reduce the final aligned row size?
      |      |-- NO -> Keep explicit fields.
      |      '-- YES
      |
      |-- Do threads update different flags concurrently?
             |-- YES -> Measure contention before packing.
             '-- NO -> Test a named bit mask.
```

## Diagnose the work

### DOD-001 — Trace the data lifetime
- **Symptom:** A review targets a row layout without knowing who builds, owns, reads, updates, or emits the rows.
- **Action:** Trace input → validation → retained rows → repeated passes → output. Mark build-only data and canonical identity/order.
- **Check:** Each proposed deletion or reordering has a named consumer and output invariant.
- **Example:** Input bytes → parse tree → canonical rows → score pass → ordered output. Once score and output use only rows plus the order index, release the parse tree.

### DOD-002 — Finish diagnosis with a target layout
- **Symptom:** A review identifies `N` retained rows of `W` bytes each or a repeated loop, then stops without a representation change or a decision to keep the current one.
- **Action:** Match the code signature to a rule below and draw the exact new layout or algorithm. Calculate old and proposed total bytes and build/query/update costs when inputs are known. Missing measurements prevent acceptance, not a specific candidate.
- **Check:** End with `old → proposed` representation, projected target cost, budget if stated, preserved behavior, and acceptance measurement. A byte count or rule ID alone does not complete this rule.
- **Example:** Hypothetical memory case:
  - **Before:** `1,000,000 × 64 B = 64 MB` of rows exceeds a `48 MB` retained-data budget. Each row contains `32 B` of core fields and a `32 B` optional payload present on `2%` of rows.
  - **Change:** Keep `32 B` core rows. Put present payloads in a sorted side array of `8 B` ID + `32 B` payload per entry (DOD-015).
  - **Projected cost:** `1,000,000 × 32 B + 20,000 × 40 B = 32.8 MB` of raw arrays before capacity and allocator overhead. For `P=20,000` present rows, building core rows and sorting the side array costs `O(N + P log P)` with a worst-case `O(P log P)` comparison sort. Binary search takes `O(log P)`. Sorted insertion takes `O(P)`; inline lookup took `O(1)`.
  - **Decision:** `FINDING`: the current `64 MB` raw rows exceed the `48 MB` budget. The side-array proposal is `UNVERIFIED` until actual retained bytes meet `48 MB`, lookup/update latency meets its budget, and behavior stays equivalent. Splitting one scanned `8 B` field (DOD-006) changes scan access but leaves the `64 MB` raw field total unchanged, so it cannot solve this memory budget by itself.

### DOD-003 — Calculate time and space complexity
- **Symptom:** A pass scans `N × M` pairs, sorts `N` rows, or recomputes the same result on every query.
- **Action:** Name input sizes and call counts. Derive build, query, update, output, and peak extra-space costs separately. Include `K` when producing `K` results. Distinguish expected from worst-case lookup when they differ. If projected calls exceed a stated budget, change the algorithm before tuning field layout.
- **Check:** Include index construction, cache build, invalidation, and update work in the proposed complexity.
- **Example:** `Q` exact-key scans of `N` rows cost `O(QN)` time and `O(1)` extra space. Sort a separate `(key, row_id)` index in worst-case `O(N log N)` time, then use binary search for `O(log N)` per query while canonical rows keep their order. The index needs `O(N)` space; sorted insertion costs `O(N)` per update. Producing `K` rows adds `Ω(K)` work.
  - **Cached result:** `Q` reachability checks from one root in a fixed graph of `N` nodes and `E` edges cost `O(Q(N+E))` if each check traverses the graph. Build `reachable[id]` once in `O(N+E)` time and `O(N)` space; then each membership check is `O(1)`, for `O(N+E+Q)` total time. Invalidate on graph mutation. If `R` graph versions receive queries, rebuilding costs `O(R(N+E)+Q)`; when `R≈Q`, caching does not improve asymptotic time.
  - **Incremental result:** `Q` reads of the sum of `N` fixed-width integers cost `O(QN)` if each read scans all rows. Store one total: build `O(N)`, adjust it from old/new values in `O(1)` per mutation, and read it in `O(1)`. Aggregate work becomes `O(N+U+Q)` with `O(1)` extra space, excluding row mutation costs. Prove the total cannot overflow and route every mutation through the update.

### DOD-004 — Leave paths within budget unchanged
- **Symptom:** A review proposes an index or cache for a collection whose access count and size already fit the stated budget.
- **Action:** Keep the current representation when its worst-case work fits the budget. Include index-build and cache-maintenance work before proposing either addition.
- **Check:** Record element count, call count, and budget. If any value needed to decide is absent, mark the proposal `UNVERIFIED`.
- **Example:** A 20-row linear scan run once at startup makes at most 20 comparisons. A new index adds build work to that single query. Report `NO FINDING` when the scan meets the startup budget.

## Shape retained data

### DOD-005 — Replace retained row pointers with checked IDs
- **Symptom:** Rows retain pointer links or use one heap allocation per node; link width and pointer traversal recur across `N` rows.
- **Action:** Put rows in one owner array and store typed slot IDs in links. Choose a narrower ID only under a validated capacity bound (DOD-009). If deleted slots can be reused, add a generation; if rows are compacted, preserve or remap every live ID. Resolve IDs through the owner, and do not retain direct references across owner relocation.
- **Check:** Compare actual row width, allocations, and traversal time. Reject wrong-domain, out-of-range, deleted, and stale IDs; define generation-wrap behavior if slots are reused.
- **Example:** On a machine with 8 B pointers, `next: pointer` in 10,000 rows uses 80 KB of raw link fields. With at most `2^32-1` slots and no reuse, `next: checked 4 B NodeId` uses 40 KB before row padding. If slots are reused, `NodeId(slot, generation)` rejects a deleted node's old ID; recalculate its width.

### DOD-006 — Choose AoS, SoA, or AoSoA from the access pattern
- **Symptom:** A repeated loop over `N` AoS rows reads one field, or each row carries alignment padding that field reordering cannot remove.
- **Action:** Keep AoS when full-row access dominates. Use SoA for sequential field-subset scans. Test AoSoA when pure SoA increases page or TLB pressure. Keep fields consumed together in one group. Update aligned columns together.
- **Check:** Compare total bytes, hot-pass time, full-row time, page and TLB behavior, and update cost. Benchmark AoSoA chunk size. A scan split alone does not remove field bytes.
- **Example:** For 10,000 rows of `{score: 8 B, payload: 56 B}`, a score loop walks a 640 KB row region. `scores[i]: 8 B` plus `payloads[i]: 56 B` makes that loop walk an 80 KB column; raw fields still total 640 KB. The same split works for a flag-only pass: `flags[i]` holds each boolean beside `payloads[i]`, while the pass reads only `flags[]`. If false rows dominate and rows may move, DOD-020 can encode the flag as active/inactive array membership. A separate row `{link: 8 B, tag: 1 B}` can occupy 16 B with 8 B alignment: 160 KB for 10,000 rows. `links[]` plus `tags[]` uses 90 KB of raw elements before capacity. The AoS and column-only scans remain O(N); an active partition under DOD-020 visits A active rows. Time gains are `UNVERIFIED`.

### DOD-007 — Flatten stable relations
- **Symptom:** Each parent owns a separately allocated child list and traversal is sequential.
- **Action:** Append children to one owner array, and put `(offset, length)` in each parent. As an alternative for fixed adjacency lists, store `N+1` offsets instead of `(offset, length)` per parent. Rebuild or use another representation when arbitrary per-parent append must take O(1) time.
- **Check:** Include child order, empty parents, offset overflow, allocation count, and rebuild/update cost. Do not claim O(1) append to an arbitrary middle range.
- **Example:** `before: parents[i].children = separate_array`; `after: children = [a,b,c]; ranges = [(0,2),(2,0),(2,1)]`. Parent 1 reads `children[2:2]`; one array owns all children. Sequential traversal stays O(total children).

### DOD-008 — Resolve external strings to internal IDs at build time
- **Symptom:** Relations retain names and each runtime traversal searches a string-key map for the target row.
- **Action:** Validate names and duplicates at build time. Assign typed dense IDs and store them in relations. Keep names for output or diagnostics. Retain the string lookup only for runtime name queries or inserts. If rows move, update an ID-to-slot map or remap stored IDs.
- **Check:** Preserve unknown-name errors, duplicate-name policy, output order, and spelling. Count build lookups, retained bytes, and runtime traversal, including name and ID-to-slot maps.
- **Example:** `before: edge.target = "cat"; visit(edge) => map[edge.target]`. `after: edge.target = EntityId(7); visit(edge) => owner.resolve(edge.target)`. Retain `names[7] = "cat"` only for output. An ID-to-slot map keeps `EntityId(7)` stable as rows move. For `E` edges visited `Q` times, resolve names once per edge during build instead of `Q × E` runtime lookups.

### DOD-022 — Replace retained string keys with integer IDs
- **Symptom:** Rows or indexes retain owned or borrowed string keys, and internal operations repeatedly hash or compare their bytes.
- **Action:** Store each distinct string once in an owned byte pool with its length. Intern incoming bytes to a typed unsigned `StringId` containing the pool offset. Use that ID in rows or as the key of internal maps, wherever string keys were retained; resolve a temporary byte view only when text content is needed. Keep the string-to-ID table while new strings or external string lookups are accepted.
- **Check:** Strings equivalent under the declared equality policy receive one ID; non-equivalent strings remain distinct despite hash collisions. Validate offset width, length encoding, and pool lifetime; keep offsets stable or remap IDs if the pool is compacted. Count pool bytes, IDs, retained lookup tables and maps, and allocations; compare build and runtime lookup costs. Persist the pool alongside IDs or remap IDs on load. Pool offsets are not dense ordinals: compact direct arrays require a separate dense ID mapping.
- **Example:** `before: string_key_map["cat"] = value; row.name = owned_string("cat")`. `after: id = intern("cat"); integer_key_map[id] = value; row.name = id`. If the pool entry for `cat` starts at byte offset 37, repeated uses of `cat` share `StringId(37)`; `integer_key_map` uses integer keys rather than string bytes. A 32-bit offset is valid only while pool size and reserved values fit its declared range.

### DOD-009 — Narrow fields only with enforced bounds
- **Symptom:** A retained row uses a wider integer than its declared maximum requires.
- **Action:** Select a narrower representation only if a declared maximum covers every valid value and sentinel. Validate before conversion and define overflow behavior. Measure retained bytes and conversion/decode time before accepting the change.
- **Check:** Test the largest accepted value, first rejected value, sentinel, and serialized compatibility.
- **Example:** A 16-bit unsigned slot holds `0..65,535`. Use it only if the declared capacity and reserved values fit; otherwise keep a wider slot.

### DOD-010 — Keep passes and scratch local
- **Symptom:** A pass allocates per row, writes shared mutable marks, or retains a cache for data used by one request.
- **Action:** Reuse operation-local scratch sized to the maximum visited rows. Compute a derived value inside the request when it is used only there. Add a retained cache only if measured saved time covers its build and invalidation cost and its bytes fit the memory budget.
- **Check:** Count allocations per operation, scratch peak, concurrent behavior, and cache invalidation paths.
- **Example:** A graph query uses a request-local visited array indexed by dense ID; no per-node allocation or shared lock is needed for the marks.

### DOD-014 — Measure padding before packing
- **Symptom:** A row in a retained collection measures wider than the sum of its fields because alignment inserts padding.
- **Action:** Inspect field offsets. Reorder private fields or derive a flag when another field determines it. If padding still repeats per row, compare columns under DOD-006. Change one layout property per comparison.
- **Check:** Report old/new row bytes and `row count × row bytes`. Preserve externally fixed serialized or binary layouts. Where the runtime does not expose field offsets, measure retained allocation instead.
- **Example:** With 8 B alignment, `[bool, 8 B ID, 4 B count, 2 B tag, bool]` can occupy 24 B; reordering the same fields can occupy 16 B. Verify both sizes in the target build.

### DOD-023 — Pack independent row flags
- **Symptom:** Each of `N` rows stores separate boolean fields that are read or serialized as a group.
- **Action:** Assign a fixed bit position to each flag and store one integer mask. Replace field reads/writes with named bit tests and updates. Use this layout only when the aligned row shrinks or grouped flag access meets a stated budget.
- **Check:** Verify each flag combination, default value, and serialized meaning. Compare actual row bytes and flag-read/update time. If multiple threads update different flags in one mask, account for synchronization and contention.
- **Example:** In a runtime with 1 B booleans, eight flags occupy 8 B before padding; one 8-bit mask occupies 1 B before padding. An `N=10,000` row array saves up to `70 KB` in raw flag bytes, but may save `0 B` after row alignment; measure the final row size.

### DOD-015 — Move optional payloads out of every row
- **Symptom:** Every row reserves `B` bytes for an optional payload, but only `P` of `N` rows contain one.
- **Action:** Compare `N × old row bytes` with `N × new row bytes + side-table bytes`, including alignment and capacity. Move present payloads to a side table only if the byte saving and measured lookup/update time meet the stated budgets.
- **Check:** Measure `P/N`, total bytes, access latency, and insert/delete/move consistency. Reserve an absent index and check it before side-array access. Keep the field inline if the side table breaches a budget.
- **Example:** `N=1,000` rows contain a 24 B core and a 16 B optional payload; `P=10` payloads are present. The old raw fields use `40 KB`. Replace them with `core[]:24 B × N`, `side_index[]:4 B × N`, and `side[]:{owner_id:4 B, payload:16 B} × P`: `24 KB + 4 KB + 0.2 KB = 28.2 KB` before capacity/alignment. Lookup uses one checked index, O(1); swap removal must repair the moved owner's side index.

### DOD-016 — Replace per-object variants with SoA encodings
- **Symptom:** A base object points to separately allocated subclass payloads, or a tagged union makes every row pay for its largest variant.
- **Action:** Count each variant. Put common fields in parallel columns. Let a tag encode both variant and mutually exclusive flags; reuse an `extra_index` field according to the tag. Put variant-only payloads in dense side arrays. If side rows can be removed by swapping, store each side row's owner ID so the moved row's `extra_index` can be updated. Define a decode path for every tag before removing the old objects.
- **Check:** Compute `Σ(column capacity × element width) + Σ(side-array capacity × element width) + lookup bytes`, including alignment. Test every tag, side index, transition, invalid encoding, output order, and serialization. Compare full traversal and decode time with the old objects.
- **Example:** On a hypothetical runtime with 8 B alignment, `Actor {kind:1 B, x:4 B, y:4 B, extra_ptr:8 B}` occupies 24 B before subclass allocations. For 1,000,000 actors, use common columns `tag[]:1 B`, `x[]:4 B`, `y[]:4 B`, and `extra_index[]:4 B`. Tags are `BASIC`, `EQUIPPED_IDLE`, and `EQUIPPED_ARMED`. Only the 100,000 equipped actors have entries in `equipped[]:{owner_id:4 B, item_id:4 B}`. Raw elements total `1,000,000 × 13 B + 100,000 × 8 B = 13.8 MB` before capacity, versus at least `24 MB` of old base objects. The tag carries the armed flag; `extra_index[i]` names `equipped[]` only for equipped actors.

### DOD-017 — Derive fields from retained input at use time
- **Symptom:** Each of `N` rows stores `end`, `line`, `column`, or another value determined by retained `start`, `kind`, and source data.
- **Action:** Write the exact derivation first. Keep only its required inputs in the row; derive the value at the consumer. For byte columns, use a sorted `line_starts[]`: binary-search the last start not after `token.start`, then subtract it. Derive `end = start + fixed_width(kind)` only for fixed-width kinds; scan source bytes for variable-width kinds.
- **Check:** Retain the source until the last derivation. Validate that source length and line offsets fit their integer fields. Test final line, empty input, multi-byte text, line endings, and each token kind. Compare saved row bytes and added per-read work; keep a stored value if repeated reads exceed its time budget.
- **Example:** `before: token = {kind:1 B, start:4 B, end:4 B, line:4 B, column:4 B}`. `after: token = {kind:1 B, start:4 B}` plus `source` and `line_starts[]`. With source length bounded to `2^32-1` bytes and `N=1,000,000`, removing the three 4 B fields removes `12 MB` of raw field bytes before row alignment; lookup is `O(log L)` for `L` lines, plus any source scan. Actual retained bytes and latency remain `UNVERIFIED`.

### DOD-018 — Skip unchanged or repeated work
- **Symptom:** A no-op update still parses, rebuilds, serializes, or converts IDs to strings and back.
- **Action:** Check a trusted version or verified content identity before parsing, rebuilding, or serializing. Carry validated typed IDs through internal stages and render strings at the output boundary.
- **Check:** Hash collisions or stale metadata cannot authorize skipping required validation; compare changed, unchanged, and malformed inputs.
- **Example:** If source bytes and required metadata match the retained snapshot, skip reparse and staging; a changed source still follows the full validation path.

### DOD-019 — Remove random lookup from a sequential scan
- **Symptom:** A pass over `N` rows performs a map lookup or pointer chase for every row to fetch stable companion data.
- **Action:** Resolve companions into parallel arrays or stable dense IDs during build, then scan them by index. Keep the map for queries that ask for arbitrary keys.
- **Check:** Measure lookup count and the extra bytes/update work; verify companion arrays stay aligned after insert, delete, and reorder.
- **Example:** Replace `N` string-key lookups per ranking pass with `N` indexed reads from a parallel weight array.

### DOD-020 — Partition active rows when scans repay transitions
- **Symptom:** A repeated loop skips inactive rows before doing work for most rows.
- **Action:** Keep active and inactive rows in separate dense arrays; array membership encodes the flag, and the repeated pass visits only active rows. When external references exist, maintain `ID → (partition, slot)`; if rows cannot move, keep active IDs instead. Compare measured `T_new_build + U × T_new_transition + Q × T_new_scan` with `T_old_build + U × T_old_transition + Q × T_old_scan` on the same workload. Include ID-map and order-maintenance time.
- **Check:** Measure scanned rows, state-transition moves, total row bytes, and full-pass latency. Preserve stable IDs, output order, and concurrent update behavior. Swap removal moves O(1) rows but changes order; count ID-map maintenance separately. Order-preserving moves can cost O(N).
- **Example:** With 1,000,000 rows and 10,000 active rows, the active partition visits 10,000 rows and needs no per-row active check. Each state transition moves a row and fixes its ID mapping. An active-ID list visits 10,000 IDs but then fetches their rows. Compare both against the 1,000,000-row scan; counts alone do not prove speed.

### DOD-021 — Price an index across its lifetime
- **Symptom:** Exact or range queries repeatedly scan the same rows, while an index would add build and update work.
- **Action:** Compare `B + Q × L_new + U × M_new` with `Q × L_old` for the same workload. Here `B` is index build time, `L` is lookup time, and `M` is extra maintenance time per update. Compare index bytes with the memory budget.
- **Check:** Measure build, lookup, and update time. Report break-even query count or `UNVERIFIED` when times are missing. Keep output order independent of index order.
- **Example:** With no updates and fixed `L_old > L_new`, the index repays build time only when `Q > B / (L_old - L_new)`.

## Prove and report

### DOD-011 — Preserve behavior through layout changes
- **Symptom:** A smaller layout has no test for identity, ordering, invalid input, or mutations.
- **Action:** Compare old and new behavior with an independent oracle or existing product tests. Cover IDs, bounds, stale handles, duplicate policy, order, side-table updates, errors, serialization, and authorization where applicable.
- **Check:** The same inputs produce the same required outputs and failures; performance never excuses weaker validation or recovery.
- **Example:** After deleting and reusing a slot, the stale handle fails; after reordering rows, serialized results remain in canonical order.

### DOD-012 — Measure the whole trade-off
- **Symptom:** A layout change is accepted from byte arithmetic or a microbenchmark alone.
- **Action:** Use identical before/after input. Record phase time, total time, allocations, retained bytes, peak bytes, reads, writes, and build/update cost. Report repetitions, variation, cold/warm state, and thread count. Measure related PMU events in small groups. Check multiplexing.
- **Check:** Preserve correctness first. Confirm the predicted physical metric before you claim a performance win. Report producer, consumer, packing, update, and maintenance costs.
- **Example:** An AoS→SoA split remains `O(N)` for a scan; claim a speed gain only after matched scan and whole-workload measurements.

### DOD-013 — Make each review finding actionable
- **Symptom:** A review says “use SoA” or “make this faster” without a loop, scale, or proof.
- **Action:** Report rule ID, code location, operation, workload, baseline, root-cause evidence, hypothesis, transformation, prediction, invariants, result, and verdict. Use `FINDING`, `UNVERIFIED`, `NO FINDING`, or `N/A` for each considered rule.
- **Check:** A reader can reproduce the calculation or measurement and decide whether to implement the change. Never invent profile percentages or latency.
- **Example:** `Illustrative UNVERIFIED DOD-003/DOD-007: load loops over M=20,000 records for each of D=200 owners (4,000,000 comparisons; O(DM)). Two-pass grouping by checked dense owner ID costs O(D+M) time and extra space. Preserve per-owner order and duplicate errors. Matched load time and peak bytes: not measured.`

## Quality gate for this skill's output

For each inspected operation, report applicable rule IDs and `FINDING`, `UNVERIFIED`, `NO FINDING`, or `N/A`. Even `UNVERIFIED` gives a concrete `before → after` layout and names the missing measurement. Show build, query, update, and extra-space costs; never claim speed from Big O or row width alone. If a candidate fails, leave the original budget breach open.
