---
name: data-oriented-design
description: Recognize data layout problems in code, propose concrete AoS/SoA, flat-array, and handle-based redesigns, then check time, space, and behavior across languages.
---

# Data-Oriented Design

Code shape can justify a concrete redesign candidate before profiling. Object count alone does not justify SoA: identify the loop, fields it touches, and update pattern. Measurements decide whether to adopt the candidate.

**Build** creates or updates retained data. **Query** reads it. **Canonical** data defines identity and output order. `N` is rows, `M` another input count, `Q` queries, `U` updates, and `K` returned rows. Examples are hypothetical; derived counts are not benchmark results. Bytes use decimal units.

## Run one layout experiment

1. Read the container and its loops. Start with code that repeatedly traverses a retained collection, then rank candidates by row count, width, call count, or a known budget/profile. A single 20-row startup scan is not a layout problem.
2. Write the code signature and target shape from the table below. Draw both layouts, name the fields each pass reads, and note insert/delete/reorder behavior. Propose the shape even if no measurements exist; label its benefit `UNVERIFIED`.
3. Calculate old and proposed retained bytes, build/query/update complexity, and extra space. State identity, order, error, and serialization invariants. For an implementation, change one layout property per patch.
4. Compare old and new behavior and costs on the same workload. Adopt only when the target budget is met without breaking another stated budget. In a review, specify the missing measurement.

| Code signature | Candidate end state | Rule |
| --- | --- | --- |
| Loop over thousands of AoS rows reads only `row.key` | Dense `keys[i]`; other fields stay together as `payloads[i]` | DOD-006 |
| AoS row repeats alignment padding `N` times | Separate columns by alignment when reordering cannot remove padding | DOD-014, DOD-006 |
| Parent rows each own a child array | One child array; each parent stores `(offset, length)` | DOD-007 |
| Long-lived pointers to movable or reused rows | One row owner; checked typed IDs outside it | DOD-005 |
| Rows own duplicate variable-length strings | One byte pool; rows store `(offset, length)` IDs | DOD-022 |
| Each row stores multiple independent boolean fields | One explicitly defined bit mask, if the aligned row shrinks | DOD-023 |
| Optional payload reserved in every row | Core rows plus present-only side storage | DOD-015 |
| Hot loop starts with `if not active: continue` | Active row partition, or active IDs when rows cannot move | DOD-020 |
| Repeated `N × M` scan or key search | Grouped rows or an index, including maintenance cost | DOD-003, DOD-021 |

## Diagnose the work

### DOD-001 — Trace the data lifetime
- **Symptom:** A review targets a row layout without knowing who builds, owns, reads, updates, or emits the rows.
- **Action:** Trace input → validation → retained rows → repeated passes → output. Mark build-only data and canonical identity/order.
- **Check:** Each proposed deletion or reordering has a named consumer and output invariant.
- **Example:** A name map resolves input references during build; queries use numeric IDs. Drop the map after build only if no runtime name lookup or diagnostic needs it.

### DOD-002 — Finish diagnosis with a target layout
- **Symptom:** A review identifies a wide row or repeated loop, perhaps calculates `rows × row bytes`, then stops without a representation change or a decision to keep the current one.
- **Action:** Match the code signature to a rule below and draw the exact new layout or algorithm. Calculate old and proposed total bytes and build/query/update costs when inputs are known. Missing measurements prevent acceptance, not a specific candidate.
- **Check:** End with `old → proposed` representation, projected target cost, budget if stated, preserved behavior, and acceptance measurement. A byte count or rule ID alone does not complete this rule.
- **Example:** Hypothetical memory case:
  - **Before:** `1,000,000 × 64 B = 64 MB` of rows exceeds a `48 MB` retained-data budget. Each row contains `32 B` of core fields and a `32 B` optional payload present on `2%` of rows.
  - **Change:** Keep `32 B` core rows. Put present payloads in a sorted side array of `8 B` ID + `32 B` payload per entry (DOD-015).
  - **Projected cost:** `1,000,000 × 32 B + 20,000 × 40 B = 32.8 MB` of raw arrays before capacity and allocator overhead. For `P=20,000` present rows, a worst-case `O(P log P)` sort builds the side array. Binary search takes `O(log P)`. Sorted insertion takes `O(P)`; inline lookup took `O(1)`.
  - **Decision:** `FINDING`: the current `64 MB` raw rows exceed the `48 MB` budget. The side-array proposal is `UNVERIFIED` until actual retained bytes meet `48 MB`, lookup/update latency meets its budget, and behavior stays equivalent. Splitting one scanned `8 B` field (DOD-006) changes scan access but leaves the `64 MB` raw field total unchanged, so it cannot solve this memory budget by itself.

### DOD-003 — Calculate time and space complexity
- **Symptom:** A pass scans `N × M` pairs or sorts `N` rows on every query.
- **Action:** Name input sizes and call counts. Derive build, query, update, output, and peak extra-space costs separately. Include `K` when producing `K` results. Distinguish expected from worst-case lookup when they differ. If projected calls exceed a stated budget, change the algorithm before tuning field layout.
- **Check:** Include index construction and maintenance in the proposed complexity.
- **Example:** `Q` exact-key scans of `N` rows cost `O(QN)` time and `O(1)` extra space. A worst-case `O(N log N)` comparison sort plus binary search costs `O(N log N + Q log N)` time. Extra space depends on the sort. Producing `K` rows adds `Ω(K)` work.

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

### DOD-006 — Split AoS for field-subset passes or repeated padding
- **Symptom:** A repeated loop over thousands of AoS rows reads one field, or each row carries alignment padding that field reordering cannot remove.
- **Action:** Put fields read together into dense columns; keep fields consumed together in payload rows. Separate differently aligned fields when this removes per-row padding. Access columns by the same index and update them together. Keep AoS if full-row access dominates or the split breaches its update budget.
- **Check:** Compare actual total bytes, the selected pass, full-row consumers, and insert/delete/reorder costs. Order-preserving insertion may move O(N) elements in every column; swap removal changes order. A scan split alone does not remove field bytes.
- **Example:** For 10,000 rows of `{score: 8 B, payload: 56 B}`, a score loop walks a 640 KB row region. `scores[i]: 8 B` plus `payloads[i]: 56 B` makes the score loop walk an 80 KB column; raw fields still total 640 KB. A separate row `{link: 8 B, tag: 1 B}` can occupy 16 B with 8 B alignment: 160 KB for 10,000 rows. `links[]` plus `tags[]` uses 90 KB of raw elements before capacity. Both scan layouts remain O(N); time gains are `UNVERIFIED`.

### DOD-007 — Flatten stable relations
- **Symptom:** Each parent owns a separately allocated child list and traversal is sequential.
- **Action:** Append children to one owner array, and put `(offset, length)` in each parent. Use `N+1` offsets for `N` fixed adjacency lists. Rebuild or use another representation if arbitrary per-parent appends must remain cheap.
- **Check:** Include child order, empty parents, offset overflow, allocation count, and rebuild/update cost. Do not claim O(1) append to an arbitrary middle range.
- **Example:** `before: parents[i].children = separate_array`; `after: children = [a,b,c]; ranges = [(0,2),(2,0),(2,1)]`. Parent 1 reads `children[2:2]`; one array owns all children. Sequential traversal stays O(total children).

### DOD-008 — Separate flexible build state from frozen runtime state
- **Symptom:** Runtime retains maps, parsed trees, and temporary strings after the last consumer of those build artifacts finishes.
- **Action:** Validate references, duplicate policy, and bounds in a builder. Choose canonical row order, freeze rows and indexes, then drop build-only data. Retain a lookup map only for runtime lookups that exist.
- **Check:** Input order, hash iteration, and thread scheduling must not alter serialized order or content hashes when the contract requires determinism.
- **Example:** Resolve names through a builder map, sort canonical rows by stable key, construct adjacency offsets, then discard the builder map.

### DOD-022 — Pool retained strings behind offsets
- **Symptom:** Each of `N` rows separately allocates a name or keep long-lived slices into a buffer that may grow; repeated names are copied again.
- **Action:** Intern each distinct byte string into one owned byte array. Store a checked `(offset, length)` ID in rows; compare incoming bytes against pooled bytes in a build-time lookup table. Resolve a temporary slice only when needed. Drop the table after build if runtime neither inserts names nor looks them up.
- **Check:** Duplicate bytes receive the same ID; unequal bytes stay distinct even on hash collisions. Check offset/length overflow, encoding and equality policy, and lifetime across pool growth. Compare pool, IDs, lookup-table bytes, allocations, and lookup cost with the original.
- **Example:** `before: rows[i].name = separately_allocated_string`; `after: rows[i].name = StringId(offset, length); names = concatenated_unique_bytes`. Two rows named `Ada` share one `(offset, 3)` ID. Pool relocation changes addresses but not offsets.

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
- **Check:** Measure `P/N`, total bytes, access latency, and insert/delete/move consistency. Keep the field inline if the side table breaches a budget.
- **Example:** In the worked case, 20,000 side entries replace 1,000,000 inline payload slots. Accept the side array only after checking its lookup and insertion costs.

### DOD-016 — Encode variants by observed frequency
- **Symptom:** Every tagged row pays for its largest variant, or each variant lives in a separate heap object.
- **Action:** Count rows of each variant. Keep shared fields in rows and variant-only payloads in flat side storage keyed by offset or ID when total bytes and decode time meet budgets. Merge mutually exclusive states in one tag only if decoding stays unambiguous.
- **Check:** Compute `sum(count_variant × inline_bytes_variant) + auxiliary bytes`. Test encode/decode round trips and invalid tags. Compare total bytes and decode time before accepting the encoding.
- **Example:** Variant A uses two fields; B uses six. Keep A's two fields in each row and B's extra four in side storage. Compare total bytes with the original fixed-size row.

### DOD-017 — Remove repeatable derived fields
- **Symptom:** Every row in a profiled pass stores a value derivable from other retained fields or a class tag.
- **Action:** Compare old/new row bytes, including padding, and the storage of any shared index. Derive the value at read time when measured derivation time fits the read budget. Retain the field when it does not.
- **Check:** Prove derivation for every variant and boundary case; include extra compute time in the benchmark.
- **Example:** Store line-start offsets once and derive a token's line/column for diagnostics instead of keeping line and column in every token read by the parser.

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
- **Symptom:** A repeated loop starts with `if not active: continue` for most rows.
- **Action:** Keep active and inactive rows in separate dense arrays; array membership encodes the flag, and the hot loop visits only active rows. When external references exist, maintain `ID → (partition, slot)`; if rows cannot move, keep active IDs instead. Choose the layout only when `partition build + state transitions + active scans < full scans` for the workload.
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
- **Action:** On identical before/after input, record latency, allocations, retained/peak bytes, and build/update cost. Cover the observed distribution and maximum valid size when capacity drives the change. State hardware, build mode, corpus size, repetitions, and cold/warm state. Label estimates.
- **Check:** Preserve correctness first. Report latency and bytes saved beside added build, update, and maintenance costs; retain the change only if the stated workload or budget favors that trade-off.
- **Example:** An AoS→SoA split remains `O(N)` for a scan; claim a speed gain only after matched scan and whole-workload measurements.

### DOD-013 — Make each review finding actionable
- **Symptom:** A review says “use SoA” or “make this faster” without a loop, scale, or proof.
- **Action:** Report rule ID, code location and operation, input counts, current layout/cost, proposed layout/cost, preserved invariant, and evidence. Use `FINDING`, `UNVERIFIED`, `NO FINDING`, or `N/A` for each considered rule. `UNVERIFIED` still includes a concrete before/after design; it means that benefit lacks measurements or bounds needed to decide.
- **Check:** A reader can reproduce the calculation or measurement and decide whether to implement the change. Never invent profile percentages or latency.
- **Example:** `Illustrative UNVERIFIED DOD-003/DOD-007: load loops over M=20,000 records for each of D=200 owners (4,000,000 comparisons; O(DM)). Two-pass grouping by checked dense owner ID costs O(D+M) time and extra space. Preserve per-owner order and duplicate errors. Matched load time and peak bytes: not measured.`

## Quality gate for this skill's output

For each inspected operation, report applicable rule IDs and `FINDING`, `UNVERIFIED`, `NO FINDING`, or `N/A`. Even `UNVERIFIED` gives a concrete `before → after` layout and names the missing measurement. Show build, query, update, and extra-space costs; never claim speed from Big O or row width alone. If a candidate fails, leave the original budget breach open.
