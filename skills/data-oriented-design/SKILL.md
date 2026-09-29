---
name: data-oriented-design
description: Review or design high-count runtime collections and repeated passes across languages. Diagnose asymptotic cost, bytes per element, allocation and access patterns; choose layouts only with workload and correctness evidence.
---

# Data-Oriented Design

Use this skill for a collection with many live elements, a repeated pass, or a measured memory or latency problem. Optimize the operation, not the name of a data structure. A map, pointer, object, or branch is not a finding by itself.

Terms: **build** creates or updates retained data; **query** reads it; **hot** means a top measured cost or an operation that exceeds its stated budget; **canonical** means the representation that defines identity and observable order. `N` is rows, `E` relations, `Q` queries, `U` updates, and `K` returned rows. All bytes below are decimal and illustrative unless measured in the target program.

## Diagnose the work

### DOD-001 — Trace the data lifetime
- **Symptom:** A review targets a row layout without knowing who builds, owns, reads, updates, or emits the rows.
- **Action:** Trace input → validation → retained state → each repeated pass → output. Mark build-only structures and the source of canonical identity and order.
- **Check:** Each proposed deletion or reordering has a named consumer and output invariant.
- **Example:** A name map resolves input references during build; queries use numeric IDs. Drop the map after build only if no runtime name lookup or diagnostic needs it.

### DOD-002 — Rank collections by actual cost
- **Symptom:** A tiny object attracts layout work while a million-row array dominates memory.
- **Action:** Record live count, actual element size including alignment, auxiliary allocations, bytes retained, fields touched per pass, pass count, and lifetime. Rank by total bytes and measured time. For a new system, label bounds as assumptions.
- **Check:** `retained bytes = count × element size + side storage + allocation overhead`; do not present this estimate as measured process memory.
- **Example:** `1,000,000 × 64 B = 64 MB` for the rows alone; if a scan reads only one 8 B field, investigate that scan before rearranging 20 configuration entries.

### DOD-003 — Calculate time and space complexity
- **Symptom:** A nested scan, repeated sort, or copy grows faster than the workload.
- **Action:** Name input sizes and calls. Derive build, query, update, output, and peak-extra-space costs separately; include `K` when outputting `K` results. State expected versus worst-case lookup when they differ. If projected calls exceed a stated budget, change the algorithm before tuning cache layout.
- **Check:** The proposed complexity accounts for index construction and maintenance, not only the fast lookup.
- **Example:** `Q` exact-key scans over `N` unsorted rows cost `O(QN)` time and `O(1)` extra space; a worst-case `O(N log N)` comparison sort followed by binary search costs `O(N log N + Q log N)` time, plus sort space determined by the algorithm. Returning `K` rows adds `Ω(K)` work.

### DOD-004 — Leave cheap paths simple
- **Symptom:** A new layout adds side indexes or synchronization to a path with no budget or scale problem.
- **Action:** Keep the current representation until a profile, size estimate, asymptotic bound, or explicit contract identifies a cost it solves.
- **Check:** State the triggering count, frequency, or budget; without one, report `NO FINDING`.
- **Example:** A map of 20 settings read at startup once does not justify a dense-ID migration.

## Shape retained data

### DOD-005 — Use checked IDs for retained identity
- **Symptom:** Every row owns a heap object and long-lived links to movable rows.
- **Action:** Let one owner keep rows in arrays; use typed indices or handles outside that owner. Check type/domain, range, liveness, and generation on lookup when slots can be reused. Keep direct references short-lived across relocation or deletion.
- **Check:** Delete row A, reuse its slot for B, then verify A's old handle cannot resolve to B. Define generation-wrap behavior before relying on a finite counter.
- **Example:** An external UUID resolves once to a checked row ID; a generation-tagged handle rejects access after the row is removed and its slot reused.

### DOD-006 — Lay out fields for the consuming pass
- **Symptom:** A repeated pass loads whole records to read one or two fields.
- **Action:** Keep array-of-structs (AoS) when passes use whole rows. For field-subset passes, split the searched/scanned fields into dense columns (SoA) or a hot/cold split; keep fields consumed together adjacent.
- **Check:** Measure the complete pass and any extra lookup or update cost. A split that slows whole-row consumers may lose overall.
- **Example:** Binary-search a compact timestamp column, then fetch one complete payload row at the matching index; the search reads timestamps without pulling every payload.

### DOD-007 — Flatten stable relations
- **Symptom:** Each parent owns a separately allocated child list and traversal is sequential.
- **Action:** Use `[start, end)` ranges for contiguous children; use offsets plus one flat target array (compressed sparse row, CSR) for stable sparse adjacency. Use a sorted list for sparse members. For repeated dense set operations, compare bitset storage `ceil(universe size / 8)` bytes per set with the list's bytes and operation costs.
- **Check:** Include build/update cost, memory for offsets, duplicate/order semantics, and empty parents.
- **Example:** Offsets `[0,2,2,5]` and five targets encode three parents; parent 1 has the empty slice `[2,2)`.

### DOD-008 — Separate flexible build state from frozen runtime state
- **Symptom:** Runtime retains maps, parsed trees, and temporary strings used only to construct a read-mostly snapshot.
- **Action:** Validate references and bounds in a builder, choose canonical row order, freeze rows and indexes, then drop build-only data. Retain a lookup map only for runtime lookups that exist.
- **Check:** Input order, hash iteration, and thread scheduling must not alter serialized order or content hashes when the contract requires determinism.
- **Example:** Resolve names through a builder map, sort canonical rows by stable key, construct adjacency offsets, then discard the builder map.

### DOD-009 — Narrow fields only with enforced bounds
- **Symptom:** A high-count row uses a wide integer although the product has a smaller hard maximum.
- **Action:** Select the narrowest representation that holds every valid value and sentinel; validate before conversion and define overflow behavior. Count conversion/decode cost before packing.
- **Check:** Test the largest accepted value, first rejected value, sentinel, and serialized compatibility.
- **Example:** A 16-bit unsigned slot can address indices `0..65,535` only if all reserved values and future capacity fit; otherwise keep a wider slot.

### DOD-010 — Keep passes and scratch local
- **Symptom:** A pass allocates per row, writes shared mutable marks, or adds a cache just to avoid one cheap traversal.
- **Action:** Use one explicit pass over owned arrays and reuse bounded operation-local scratch. Recompute cheap derived data when cache invalidation and retained memory cost more than the work saved.
- **Check:** Count allocations per operation, scratch peak, concurrent behavior, and cache invalidation paths.
- **Example:** A graph query uses a request-local visited array indexed by dense ID; no per-node allocation or shared lock is needed for the marks.

### DOD-014 — Measure padding before packing
- **Symptom:** A frequently retained row contains isolated booleans, small fields between wide fields, or unexpectedly high `sizeof`/record size.
- **Action:** Inspect actual layout and field alignment. Reorder private fields, derive constant booleans from existing state, or move genuinely sparse flags to side storage; change one property at a time.
- **Check:** Report old/new bytes per row and total retained bytes. Preserve serialized or binary interface layout if externally fixed; a language runtime may not expose or guarantee a packed layout.
- **Example:** With 8 B alignment, `[bool, 8 B ID, 4 B count, 2 B tag, bool]` can occupy 24 B; reordering the same fields can occupy 16 B. Verify both sizes in the target build.

### DOD-015 — Put rare payloads where they are used
- **Symptom:** Every row reserves a large optional field used by few rows.
- **Action:** Store a compact key or absence marker in the common row and put present payloads in a side table if `N × old row bytes > N × new row bytes + side-table bytes`. Include alignment and capacity in both sizes. Compare lookup and update time separately.
- **Check:** Measure occupancy, total bytes, access latency, and insert/delete/move consistency. Keep inline when most rows have the value or hot passes read it.
- **Example:** If only 2% of records carry a 32 B diagnostic, compare `N × 32 B` inline with actual side-table bytes and the cost of diagnostic lookups.

### DOD-016 — Encode variants by observed frequency
- **Symptom:** Every tagged row pays for its largest variant, or each variant lives in a separate heap object.
- **Action:** Count each variant. Put common fixed fields in a compact row and rare variable payloads in a flat auxiliary area keyed by offset/ID. Reuse tag states for mutually exclusive facts only when every state remains distinguishable.
- **Check:** Compute `sum(count_variant × encoded_size_variant) + auxiliary bytes`; test encode/decode round trips and invalid tags. Do not pack without a measured net gain.
- **Example:** A common two-field event stays inline; a rare event stores an offset to four extra fields instead of making every event reserve those four fields.

### DOD-017 — Remove repeatable derived fields
- **Symptom:** Every hot row stores a value exactly derivable from other retained fields or a stable class tag.
- **Action:** Derive it at read time or store it once per class when derivation is cheap and the saved bytes matter. Keep it when derivation is expensive or a measured read path needs it cached.
- **Check:** Prove derivation for every variant and boundary case; include extra compute time in the benchmark.
- **Example:** Store line-start offsets once and derive a token's line/column for diagnostics instead of keeping line and column in every token read by the parser.

### DOD-018 — Skip unchanged or repeated work
- **Symptom:** A no-op update still parses, rebuilds, serializes, or converts IDs to strings and back.
- **Action:** Test a trusted version or verified content identity before expensive work; carry validated typed IDs through internal stages and render strings at the output boundary.
- **Check:** Hash collisions or stale metadata cannot authorize skipping required validation; compare changed, unchanged, and malformed inputs.
- **Example:** If source bytes and required metadata match the retained snapshot, skip reparse and staging; a changed source still follows the full validation path.

### DOD-019 — Remove random lookup from a sequential scan
- **Symptom:** A pass over `N` rows performs a map lookup or pointer chase for every row to fetch stable companion data.
- **Action:** Resolve companions into parallel arrays or stable dense IDs during build, then scan them by index. Keep the map at admission or for genuinely random queries.
- **Check:** Measure lookup count and the extra bytes/update work; verify companion arrays stay aligned after insert, delete, and reorder.
- **Example:** Replace `N` string-key lookups per ranking pass with `N` indexed reads from a parallel weight array.

### DOD-020 — Preselect work only when skips repay maintenance
- **Symptom:** Every repeated pass branches over many rows that never participate.
- **Action:** Build a compact active-ID list if its build/update cost plus active-row scans beats full scans. Preserve full scans when active membership changes often or most rows participate.
- **Check:** Count skipped fraction, list rebuild/update work, and total pass latency; branch prediction alone is not proof.
- **Example:** A pass over 1,000,000 rows with 10,000 active rows may scan 10,000 IDs, but only after measuring list upkeep and indexed access.

### DOD-021 — Price an index across its lifetime
- **Symptom:** Repeated exact/range queries scan the same retained rows, or a proposed index speeds queries while making updates expensive.
- **Action:** Compare `B + Q × L_new + U × M_new` with `Q × L_old`, where `B` is index build cost, `L` lookup cost, and `M` extra per-update maintenance cost for the same workload. Include index bytes. Use sorted arrays for read-mostly range/exact lookup, maps for frequent keyed mutation when justified by update cost.
- **Check:** Benchmark build, query, and update phases separately and together; report the break-even query count or say it is unknown. Keep canonical output order independent of index order.
- **Example:** Sorting `N` rows once for `Q` exact queries changes time from `O(QN)` scans to `O(N log N + Q log N)` searches, but frequent inserts may erase the gain.

## Prove and report

### DOD-011 — Preserve behavior through layout changes
- **Symptom:** A smaller layout has no test for identity, ordering, invalid input, or mutations.
- **Action:** Compare old and new behavior with an independent oracle or existing product tests. Cover IDs, bounds, stale handles, duplicate policy, order, side-table updates, errors, serialization, and authorization where applicable.
- **Check:** The same inputs produce the same required outputs and failures; performance never excuses weaker validation or recovery.
- **Example:** After deleting and reusing a slot, the stale handle fails; after reordering rows, serialized results remain in canonical order.

### DOD-012 — Measure the whole trade-off
- **Symptom:** A layout change is accepted from byte arithmetic or a microbenchmark alone.
- **Action:** On identical before/after input covering the observed distribution and any relevant upper bound, record operation latency, allocations, retained/peak bytes, and build/update cost. State hardware, build mode, corpus size, repetitions, and cold/warm state. Separate estimates from measurements.
- **Check:** Preserve correctness first. Report latency and bytes saved beside added build, update, and maintenance costs; retain the change only if the stated workload or budget favors that trade-off.
- **Example:** An AoS→SoA split remains `O(N)` for a scan; claim a speed gain only after matched scan and whole-workload measurements.

### DOD-013 — Make each review finding actionable
- **Symptom:** A review says “use SoA” or “optimize this” without a loop, scale, or proof.
- **Action:** Report rule ID, code location/operation, symptom, input counts, current cost, proposed change and cost, preserved invariant, and evidence. Use `FINDING`, `UNVERIFIED`, `NO FINDING`, or `N/A` for each considered rule; `UNVERIFIED` means a plausible issue lacks required measurements or bounds.
- **Check:** A reader can reproduce the calculation or measurement and decide whether to implement the change. Never invent profile percentages or latency.
- **Example:** `UNVERIFIED DOD-003/DOD-007: load loops over M=20,000 records for each of D=200 owners (4,000,000 comparisons; O(DM)). Two-pass grouping by checked dense owner ID costs O(D+M) time and extra space. Preserve per-owner order and duplicate errors. Need matched load time and peak bytes before changing.`

## Quality gate for this skill's output

Apply only relevant IDs. Mark `N/A` with a short reason; do not force a layout change. A `FINDING` needs an observable symptom, a specific operation, scale or bound, an implementable fix, the correctness constraint, and a way to validate the benefit. Mark missing profile, size, or workload evidence `UNVERIFIED`. Mark an inspected path with no supported issue `NO FINDING`. Calculate Big O for every proposed algorithmic change, including build/update and extra space; do not use Big O as a latency measurement. Do not claim a speedup from fewer bytes alone. End with the highest-impact findings and the measurements needed to resolve unverified ones.
