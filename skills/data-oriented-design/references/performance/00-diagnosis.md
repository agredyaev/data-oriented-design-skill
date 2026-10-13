# Performance Diagnosis

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

Use the same input for the before and after runs. Declare an acceptance rule before implementation. Use repeated runs to estimate uncertainty. Separate cold, warm, and incremental workloads when they have different behavior.

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
acceptance rule
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

Classify the hot operation before you select a transformation. Use DOD-031 when the measured cause has no DOD path.

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
 |-- Does N -> 2N cause more work than the required result explains?
 |      |-- YES -> Fix algorithmic work or repeated visits. Use DOD-003 or DOD-018.
 |      '-- NO
 |
 |-- Can the hot phase move the required end-to-end KPI?
 |      |-- NO -> Stop. Amdahl's law limits the possible gain.
 |      '-- YES
 |
 |-- What limits the hot operation?
 |      |
 |      |-- ALGORITHMIC
 |      |     |-- Repeated search -> DOD-021
 |      |     |-- Unchanged input repeats work -> DOD-018
 |      |     '-- Repeated passes -> DOD-024
 |      |
 |      |-- MEMORY
 |      |     |-- Wide field-subset scan -> DOD-006, DOD-014, DOD-015, DOD-023
 |      |     |-- Random dependent loads -> DOD-005, DOD-008, DOD-019
 |      |     |-- Variable child allocations -> DOD-007
 |      |     |-- Repeated strings -> DOD-022
 |      |     |-- Repeated canonical values -> DOD-028
 |      |     |-- Realloc/copy traffic -> DOD-033
 |      |     |-- Rare derived data -> DOD-017
 |      |     |-- Poor temporal locality -> DOD-024, DOD-025, DOD-026
 |      |     '-- Producer/consumer layout conflict -> DOD-027
 |      |
 |      |-- CORE
 |      |     |-- Repeated hashing/comparison of canonical values -> DOD-022 or DOD-028
 |      |     '-- Other arithmetic/core cost -> OUTSIDE DOD. Optimize the computation.
 |      |
 |      |-- FRONT END
 |      |     |-- Cold variant work inflates the hot path -> DOD-024
 |      |     '-- Other decode/I-cache cost -> OUTSIDE DOD.
 |      |
 |      |-- BRANCH
 |      |     |-- Rare/cold cases share the hot loop -> DOD-020 or DOD-024
 |      |     '-- Other speculation cost -> OUTSIDE DOD.
 |      |
 |      |-- ALLOCATION
 |      |     |-- Per-row temporary allocation -> DOD-010
 |      |     '-- Growth/reallocation -> DOD-033
 |      |
 |      |-- SYNCHRONIZATION
 |      |     '-- Diagnose the scaling limit -> DOD-029
 |      |
 |      '-- I/O
 |            |-- Text parsing or serialization dominates -> DOD-032
 |            '-- External device/service latency dominates -> OUTSIDE DOD.
 |
 |-- Write one falsifiable prediction.
 |-- Implement the smallest targeted change.
 |-- Validate the measurement method with DOD-030.
 |-- Did the predicted physical metric pass the declared acceptance rule?
 |      |-- NO -> Reject the performance hypothesis.
 |      '-- YES
 |
 |-- Did the target phase pass the declared acceptance rule?
 |      |-- NO -> Classify the result without claiming a performance win.
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
| Repeated full passes | remove, fuse, split, or cache | DOD-024 |
| Wide AoS scan | AoS, SoA, hot/cold split, or AoSoA | DOD-006, DOD-014 |
| Pointer chasing | dense owner plus typed IDs | DOD-005, DOD-008, DOD-019 |
| Per-row child allocation | side array plus range | DOD-007 |
| Repeated string keys | string pool plus typed ID | DOD-022 |
| Repeated canonical values | canonical pool plus typed ID | DOD-028 |
| Sparse optional payload | present-only side storage | DOD-015 |
| Wide variant rows | common columns plus side payloads | DOD-016 |
| Rare derived fields | recompute from retained source | DOD-017 |
| Mostly inactive rows | active partition or active IDs | DOD-020 |
| Repeated key search | index with lifetime cost | DOD-021 |
| Many independent flags | packed mask | DOD-023 |
| Growth and reallocation | reserve capacity or size exactly | DOD-033 |
| Poor temporal locality | fusion, fission, blocking, clustering | DOD-024, DOD-025, DOD-026 |
| Producer/consumer layout conflict | one measured packing stage | DOD-027 |
| Shared mutable state | local ownership, sharding, partitioning | DOD-029 |
| Text cache/serialization overhead | compact machine-oriented format | DOD-032 |
| Measurement uncertainty | validate benchmark and PMU evidence | DOD-012, DOD-030 |

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

