# Foundation, Evidence, and Acceptance

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
      '-- Does reordering preserve identity, dependencies, errors and effects?
             |-- NO -> Keep required order/identity; an output index cannot repair these.
             '-- YES -> Preserve required emission order separately; see DOD-026.
```

### DOD-001 — Trace the data lifetime
- **Symptom:** A review targets a row layout without knowing who builds, owns, reads, updates, or emits the rows.
- **Action:** Trace input → validation → retained rows → repeated passes → output. Mark build-only data and canonical identity/order.
- **Check:** Each proposed deletion or reordering has a named consumer and output invariant.
- **Example:** Input bytes → parse tree → canonical rows → score pass → ordered output. Once score and output use only rows plus the order index, release the parse tree.

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

### DOD-002 — Finish diagnosis with a target layout
- **Symptom:** A review finds a repeated loop or `N` retained rows of `W` bytes each. The review stops without a representation decision.
- **Action:** Match the code signature to a rule below and draw the exact new layout or algorithm. Calculate old and proposed total bytes and build/query/update costs when inputs are known. Missing measurements prevent acceptance, not a specific candidate.
- **Check:** End with `old → proposed` representation, projected target cost, budget if stated, preserved behavior, and acceptance measurement. A byte count or rule ID alone does not complete this rule.
- **Example:** Hypothetical memory case:
  - **Before:** `1,000,000 × 64 B = 64 MB` of rows exceeds a `48 MB` retained-data budget. Each row contains `32 B` of core fields and a `32 B` optional payload present on `2%` of rows.
  - **Change:** Keep `32 B` core rows. Put present payloads in a sorted side array of `8 B` ID + `32 B` payload per entry (DOD-015).
  - **Projected cost:** `1,000,000 × 32 B + 20,000 × 40 B = 32.8 MB` of raw arrays before capacity and allocator overhead. For `P=20,000` present rows, building core rows and sorting the side array costs `O(N + P log P)` with a worst-case `O(P log P)` comparison sort. Binary search takes `O(log P)`. Sorted insertion takes `O(P)`; inline lookup took `O(1)`.
  - **Decision:** `FINDING`: the current `64 MB` raw rows exceed the `48 MB` budget. The side-array proposal is `UNVERIFIED` until actual retained bytes meet `48 MB`, lookup/update latency meets its budget, and behavior stays equivalent. Splitting one scanned `8 B` field (DOD-006) changes scan access but leaves the `64 MB` raw field total unchanged, so it cannot solve this memory budget by itself.

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

### DOD-003 — Calculate time and space complexity
- **Symptom:** A pass scans `N × M` pairs, sorts `N` rows, or recomputes the same result on every query.
- **Action:** Name input sizes and call counts. Derive build, query, update, output, and peak extra-space costs separately. Include `K` when producing `K` results. Distinguish expected from worst-case lookup when they differ. If projected calls exceed a stated budget, change the algorithm before tuning field layout.
- **Check:** Include index construction, cache build, invalidation, and update work in the proposed complexity.
- **Example:** `Q` exact-key scans of `N` rows cost `O(QN)` time and `O(1)` extra space. Sort a separate `(key, row_id)` index in worst-case `O(N log N)` time, then use binary search for `O(log N)` per query while canonical rows keep their order. The index needs `O(N)` space; sorted insertion costs `O(N)` per update. Producing `K` rows adds `Ω(K)` work.
  - **Cached result:** `Q` reachability checks from one root in a fixed graph of `N` nodes and `E` edges cost `O(Q(N+E))` if each check traverses the graph. Build `reachable[id]` once in `O(N+E)` time and `O(N)` space; then each membership check is `O(1)`, for `O(N+E+Q)` total time. Invalidate on graph mutation. If `R` graph versions receive queries, rebuilding costs `O(R(N+E)+Q)`; when `R≈Q`, caching does not improve asymptotic time.
  - **Incremental result:** `Q` reads of the sum of `N` fixed-width integers cost `O(QN)` if each read scans all rows. Store one total: build `O(N)`, adjust it from old/new values in `O(1)` per mutation, and read it in `O(1)`. Aggregate work becomes `O(N+U+Q)` with `O(1)` extra space, excluding row mutation costs. Prove the total cannot overflow and route every mutation through the update.

### DOD-004 decision tree

```text
Does the path fail a declared target or required budget?
 |-- NO -> Keep it for this cost task. Report NO FINDING.
 '-- YES
      |
      |-- Are the target population and acceptance rule explicit?
      |      |-- NO -> Specify them; do not invent a threshold.
      |      '-- YES -> Evaluate a replacement; preserve hard bounds on all valid inputs.
```

### DOD-004 — Leave paths within budget unchanged
- **Symptom:** A review proposes an index or cache for a collection whose access count and size already fit the stated budget.
- **Action:** Keep the current representation when it meets the declared target and required budgets. A hard capacity bound covers all valid inputs; a percentile latency target needs the declared workload distribution. Do not substitute one for the other. Include index-build and cache-maintenance work before proposing either addition.
- **Check:** Record element count, call count, and budget. If any value needed to decide is absent, mark the proposal `UNVERIFIED`.
- **Example:** A 20-row linear scan run once at startup makes at most 20 comparisons. A new index adds build work to that single query. Report `NO FINDING` when the scan meets the startup budget.

### DOD-011 decision tree

```text
Does the change alter layout, identity, order, or mutation behavior?
 |-- NO -> Run normal product tests.
 '-- YES
      |
      |-- Do existing tests or an independent oracle cover affected behavior?
      |      |-- NO -> Add the missing verification before acceptance.
      |      '-- YES
      |
      '-- Do stale IDs, errors, order, and serialization match?
             |-- NO -> Reject.
             '-- YES -> Continue to performance acceptance.
```

### DOD-011 — Preserve behavior through layout changes
- **Symptom:** A smaller layout has no test for identity, ordering, invalid input, or mutations.
- **Action:** Compare old and new behavior with an independent oracle or existing product tests. Cover IDs, bounds, stale handles, duplicate policy, order, side-table updates, errors, serialization, and authorization where applicable.
- **Check:** The same inputs produce the same required outputs and failures; performance never excuses weaker validation or recovery.
- **Example:** After deleting and reusing a slot, the stale handle fails; after reordering rows, serialized results remain in canonical order.

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
      |-- Are the target and affected build/query/update/memory/wall guardrails measured?
      |      |-- NO -> Complete the trade-off.
      |      '-- YES
      |
      '-- Do the predicted metric and target KPI pass the predeclared acceptance rule?
             |-- NO -> Reject the performance hypothesis.
             '-- YES -> Accept only if correctness and required guardrails also pass.
```

### DOD-012 — Measure the whole trade-off
- **Symptom:** A layout change is accepted from byte arithmetic or a microbenchmark alone.
- **Action:** Use identical before/after input. Measure the claimed metric and affected lifetime trade-offs: phase/total time, allocations, retained/peak bytes, reads/writes and build/update cost as relevant. State why an omitted cost cannot affect acceptance. Report repetitions, variation, cold/warm state and thread count. When using PMU evidence, measure related events in small groups and check multiplexing.
- **Check:** Preserve correctness first. Confirm the predicted physical metric before you claim a performance win. Report producer, consumer, packing, update, and maintenance costs.
- **Example:** An AoS→SoA split remains `O(N)` for a scan; claim a speed gain only after matched scan and whole-workload measurements.

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

### DOD-013 — Make each review finding actionable
- **Symptom:** A review says “use SoA” or “make this faster” without a loop, scale, or proof.
- **Action:** For an actionable finding, identify the code location, operation, workload/baseline, cause, before → after transformation, preserved behavior, and acceptance evidence. For a performance finding, also state the hypothesis, predicted physical metric, observed result, and verdict. Attach the applicable rule ID. Use the proportional report in [Workflow](../workflow.md); do not produce a disposition for every considered rule unless the user requests a coverage audit.
- **Check:** A reader can reproduce the calculation or measurement and decide whether to implement the change. Never invent profile percentages or latency.
- **Example:** `Illustrative UNVERIFIED DOD-003/DOD-007: load loops over M=20,000 records for each of D=200 owners (4,000,000 comparisons; O(DM)). Two-pass grouping by checked dense owner ID costs O(D+M) time and extra space. Preserve per-owner order and duplicate errors. Matched load time and peak bytes: not measured.`

### DOD-030 decision tree

```text
Does the experiment depend on timing or PMU evidence?
 |-- NO -> Use the applicable functional rule.
 '-- YES
      |
      |-- Was the acceptance rule declared before implementation?
      |      |-- NO -> Declare it and rerun.
      |      '-- YES
      |
      |-- Are before/after workloads identical and repeated?
      |      |-- NO -> Benchmark is invalid.
      |      '-- YES
      |
      |-- Is PMU evidence used?
      |      |-- NO -> Use the matched timing evidence; no counters are required.
      |      '-- YES
      |
      |-- Are PMU event groups free from harmful multiplexing?
             |-- NO -> Split the event groups and rerun.
             '-- YES -> Use the evidence.
```

### DOD-030 — Validate benchmark and PMU evidence
- **Symptom:** A performance claim depends on noisy timing or hardware counters.
- **Action:** Declare the acceptance rule before implementation. Repeat matched A/B workloads. Split PMU groups when multiplexing affects evidence.
- **Check:** Report the acceptance rule, repetitions, variation, cache state, event groups, and PMU time-running values.
- **Example:** Reject a 1% timing change when the declared uncertainty rule cannot distinguish the result from baseline variation.

### DOD-031 decision tree

```text
Is the dominant bottleneck outside data representation, access order, lifetime, or ownership?
 |-- NO -> Use the matching DOD rule.
 '-- YES
      |
      |-- Can a DOD change remove the measured cause directly?
      |      |-- YES -> Use the matching DOD rule and state the cause.
      |      '-- NO -> Report OUTSIDE DOD and stop proposing layout changes.
```

### DOD-031 — Stop DOD when the measured cause is outside DOD
- **Symptom:** The hotspot is core, front-end, branch, device, or service bound without a data-path cause.
- **Action:** Report `OUTSIDE DOD`. Do not propose a layout change without direct evidence.
- **Check:** Name the measured bottleneck and the missing DOD causal link.
- **Example:** A compute-heavy divide loop stays a computation problem when data layout does not cause the stalls.

## Quality gate for this skill's output

Use [Workflow reporting](../workflow.md#proportional-result-format) as the only reporting contract. A concrete performance proposal without measurements is `UNVERIFIED`; give its before → after design and the missing acceptance evidence. Never infer speed from Big O or row width alone. Include construction, maintenance, and space costs when they change the decision. If a candidate fails, leave the original budget breach open.
