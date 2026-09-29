---
name: data-oriented-design
description: Redesign the retained row type with the highest live count or a pass selected by profile or budget. Produce old/new layout, time and space costs, and validation across languages.
---

# Data-Oriented Design

A map, pointer, object, or branch alone is not a finding.

**Build** creates or updates retained data. **Query** reads it. **Canonical** data defines identity and output order. `N` is rows, `M` another input count, `Q` queries, `U` updates, and `K` returned rows. Examples are hypothetical; derived counts are not benchmark results. Bytes use decimal units.

## Run one layout experiment

1. Follow a budget breach or profiled pass; otherwise start with the highest-count retained row type. Record live rows, row bytes, total bytes, and calls per workload. Without a budget or profile, label the experiment exploratory.
2. Draw the current row and its consumers: field widths, padding, optional-field occupancy, fields read per pass, and update frequency. Choose one change from the rules below that reduces the observed bytes or repeated accesses.
3. Show the proposed layout and calculate its total bytes plus build, query, and update cost. State the identity, order, error, and serialization behavior it must preserve. For an implementation, change one layout property per patch.
4. If implementing, compare old and new behavior and costs on the same workload. Keep the change only if it meets the target budget without breaking another stated budget. In a review, name the measurements still required to accept the proposal.

| Observed cost | First rule to test |
| --- | --- |
| Repeated `N × M` work or searches | DOD-003, DOD-021 |
| Padding or redundant boolean per row | DOD-014, DOD-017 |
| Heap object or pointer per row | DOD-005 |
| Pass reads only some row fields | DOD-006 |
| Optional payload in every row | DOD-015 |
| Every variant pays for the largest one | DOD-016 |

## Diagnose the work

### DOD-001 — Trace the data lifetime
- **Symptom:** A review targets a row layout without knowing who builds, owns, reads, updates, or emits the rows.
- **Action:** Trace input → validation → retained rows → repeated passes → output. Mark build-only data and canonical identity/order.
- **Check:** Each proposed deletion or reordering has a named consumer and output invariant.
- **Example:** A name map resolves input references during build; queries use numeric IDs. Drop the map after build only if no runtime name lookup or diagnostic needs it.

### DOD-002 — Turn the measured cost into a proposed layout
- **Symptom:** A report calculates `rows × row bytes` or ranks passes, then stops without a representation change or a decision to keep the current one.
- **Action:** Identify the bytes or repeated accesses behind the selected cost. Choose one matching rule below and draw the exact new layout or algorithm. Calculate old and proposed total bytes and build/query/update costs. If fields, occupancy, or measurements are missing, state which one blocks the decision.
- **Check:** End with `old → proposed` representation, projected target cost, budget if stated, preserved behavior, and acceptance measurement. A byte count or rule ID alone does not complete this rule.
- **Example:** Hypothetical memory case:
  - **Before:** `1,000,000 × 64 B = 64 MB` of rows exceeds a `48 MB` retained-data budget. Each row contains `32 B` of core fields and a `32 B` optional payload present on `2%` of rows.
  - **Change:** Keep `32 B` core rows. Put present payloads in a sorted side array of `8 B` ID + `32 B` payload per entry (DOD-015).
  - **Projected cost:** `1,000,000 × 32 B + 20,000 × 40 B = 32.8 MB` of raw arrays before capacity and allocator overhead. For `P=20,000` present rows, a worst-case `O(P log P)` sort builds the side array. Binary search takes `O(log P)`. Sorted insertion takes `O(P)`; inline lookup took `O(1)`.
  - **Decision:** `FINDING`: the current `64 MB` raw rows exceed the `48 MB` budget. The side-array proposal is `UNVERIFIED` until actual retained bytes meet `48 MB`, lookup/update latency meets its budget, and behavior stays equivalent. Splitting one scanned `8 B` field (DOD-006) changes scan access but removes none of the `64 B` per row, so it cannot solve this memory budget by itself.

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

### DOD-005 — Use checked IDs for retained identity
- **Symptom:** Every row owns a heap object and long-lived links to movable rows.
- **Action:** Let one owner keep rows in arrays; use typed indices or handles outside that owner. Check type/domain, range, liveness, and generation on lookup when slots can be reused. Keep direct references short-lived across relocation or deletion.
- **Check:** Delete row A, reuse its slot for B, then verify A's old handle cannot resolve to B. Define generation-wrap behavior before relying on a finite counter.
- **Example:** An external UUID resolves once to a checked row ID; a generation-tagged handle rejects access after the row is removed and its slot reused.

### DOD-006 — Lay out fields for the consuming pass
- **Symptom:** A repeated pass loads whole records to read one or two fields.
- **Action:** Keep array-of-structs (AoS) when passes use whole rows. When a measured pass reads only some fields, move those fields into parallel columns (structure-of-arrays, SoA). Keep fields consumed together adjacent.
- **Check:** Measure the complete pass, whole-row consumers, and added update work before accepting a split.
- **Example:** Binary-search a timestamp column, then fetch one payload row at the matching index. Search steps read timestamps without loading every payload.

### DOD-007 — Flatten stable relations
- **Symptom:** Each parent owns a separately allocated child list and traversal is sequential.
- **Action:** Use `[start, end)` ranges for contiguous children; use offsets and flat targets (compressed sparse row, CSR) for stable sparse adjacency. For repeated dense set operations, compare bitset bytes `ceil(universe size / 8)` per set plus metadata with a sorted list's bytes and operation costs.
- **Check:** Include build/update cost, memory for offsets, duplicate/order semantics, and empty parents.
- **Example:** Offsets `[0,2,2,5]` and five targets encode three parents; parent 1 has the empty slice `[2,2)`.

### DOD-008 — Separate flexible build state from frozen runtime state
- **Symptom:** Runtime retains maps, parsed trees, and temporary strings after the last consumer of those build artifacts finishes.
- **Action:** Validate references, duplicate policy, and bounds in a builder. Choose canonical row order, freeze rows and indexes, then drop build-only data. Retain a lookup map only for runtime lookups that exist.
- **Check:** Input order, hash iteration, and thread scheduling must not alter serialized order or content hashes when the contract requires determinism.
- **Example:** Resolve names through a builder map, sort canonical rows by stable key, construct adjacency offsets, then discard the builder map.

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
- **Action:** Inspect field offsets. Reorder private fields or derive a flag when another field determines it. Change one layout property per comparison.
- **Check:** Report old/new row bytes and `row count × row bytes`. Preserve externally fixed serialized or binary layouts. Where the runtime does not expose field offsets, measure retained allocation instead.
- **Example:** With 8 B alignment, `[bool, 8 B ID, 4 B count, 2 B tag, bool]` can occupy 24 B; reordering the same fields can occupy 16 B. Verify both sizes in the target build.

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

### DOD-020 — Preselect work only when skips repay maintenance
- **Symptom:** A repeated pass visits inactive rows and branches past them on every call.
- **Action:** Build an active-ID list when `list build + updates + active scans < full scans` over the observed calls. Keep the full scan if the list costs more to maintain.
- **Check:** Count skipped fraction, list rebuild/update work, and total pass latency; branch prediction alone is not proof.
- **Example:** With 1,000,000 rows and 10,000 active IDs, compare a 1,000,000-row scan with a 10,000-ID scan plus list maintenance. The counts alone do not establish which is faster.

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
- **Symptom:** A review says “use SoA” or “optimize this” without a loop, scale, or proof.
- **Action:** Report rule ID, code location and operation, input counts, current layout/cost, proposed layout/cost, preserved invariant, and evidence. Use `FINDING`, `UNVERIFIED`, `NO FINDING`, or `N/A` for each considered rule. `UNVERIFIED` means that the proposed benefit lacks measurements or bounds needed to decide.
- **Check:** A reader can reproduce the calculation or measurement and decide whether to implement the change. Never invent profile percentages or latency.
- **Example:** `Illustrative UNVERIFIED DOD-003/DOD-007: load loops over M=20,000 records for each of D=200 owners (4,000,000 comparisons; O(DM)). Two-pass grouping by checked dense owner ID costs O(D+M) time and extra space. Preserve per-owner order and duplicate errors. Matched load time and peak bytes: not measured.`

## Quality gate for this skill's output

Apply IDs tied to inspected operations. `FINDING` names the current and proposed layout or algorithm, target cost, budget if stated, invariant, and acceptance measurement. `NO FINDING` means the inspected path meets its budget or has no demonstrated cost problem. If a candidate fails while the cost problem remains, report the unresolved breach and next candidate. `UNVERIFIED` names the missing field distribution, profile, byte count, or workload bound. Calculate build, query, update, and extra-space complexity. Never infer latency from Big O or row width.
