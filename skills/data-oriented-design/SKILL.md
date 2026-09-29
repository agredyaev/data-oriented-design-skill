---
name: data-oriented-design
description: Recognize data layout problems in code, propose concrete AoS/SoA, flat-array, and handle-based redesigns, then check time, space, and behavior across languages.
---

# Data-Oriented Design

Inspect the retained array, the loop that reads it, and updates that move its rows. A matching access pattern can justify a replacement before profiling. Use retained bytes, pass latency, and update time to decide whether to adopt it.

**Build** creates or updates retained data. **Query** reads it. **Canonical** data defines identity and output order. `N` is rows, `M` another input count, `Q` queries, `U` updates, and `K` returned rows. Examples are hypothetical; derived counts are not benchmark results. Bytes use decimal units.

## Run one layout experiment

1. Read the container and its loops. Start with code that repeatedly traverses a retained collection, then rank candidates by row count, width, call count, or a known budget/profile. A 20-row startup scan needs no redesign when it meets its budget.
2. Write the code signature and target shape from the table below. Draw both layouts, name the fields each pass reads, and note insert/delete/reorder behavior. Propose the shape even if no measurements exist; label its benefit `UNVERIFIED`.
3. Calculate old and proposed retained bytes, build/query/update complexity, and extra space. State identity, order, error, and serialization invariants. For an implementation, change one layout property per patch.
4. Compare old and new behavior and costs on the same workload. Adopt only when the target budget is met without breaking another stated budget. In a review, specify the missing measurement.

| Code signature | Candidate end state | Rule |
| --- | --- | --- |
| Repeated loop over `N` AoS rows reads only `row.key` | Dense `keys[i]`; other fields stay together as `payloads[i]` | DOD-006 |
| AoS row repeats alignment padding `N` times | Separate columns by alignment when reordering cannot remove padding | DOD-014, DOD-006 |
| Parent rows each own a child array | One child array; each parent stores `(offset, length)` | DOD-007 |
| Long-lived pointers to movable or reused rows | One row owner; checked typed IDs outside it | DOD-005 |
| Rows or indexes retain string keys | Intern bytes once; store bounded integer `StringId` keys and one byte pool | DOD-022 |
| Build resolves names, but runtime rows still store string links | Resolve once to typed row IDs; keep names only for required output | DOD-008 |
| Every row stores line, column, or a value derivable from retained input | Keep source plus compact start/kind; derive the other value on demand | DOD-017 |
| A pass reads only `row.flag`, but rows cannot be partitioned | Parallel `flags[i]` column; test a bitset if only tests are needed | DOD-006 |
| Base object points to subclass payload, or every row pays for largest variant | Common SoA columns, tag encodings, and present-only payload arrays | DOD-016 |
| Each row stores multiple independent boolean fields | One explicitly defined bit mask, if the aligned row shrinks | DOD-023 |
| Optional payload reserved in every row | Core rows plus present-only side storage | DOD-015 |
| Repeated loop skips inactive rows before work | Active row partition, or active IDs when rows cannot move | DOD-020 |
| Repeated `N × M` scan or key search | Grouped rows or an index, including maintenance cost | DOD-003, DOD-021 |

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
- **Symptom:** A pass scans `N × M` pairs or sorts `N` rows on every query.
- **Action:** Name input sizes and call counts. Derive build, query, update, output, and peak extra-space costs separately. Include `K` when producing `K` results. Distinguish expected from worst-case lookup when they differ. If projected calls exceed a stated budget, change the algorithm before tuning field layout.
- **Check:** Include index construction and maintenance in the proposed complexity.
- **Example:** `Q` exact-key scans of `N` rows cost `O(QN)` time and `O(1)` extra space. Sort a separate `(key, row_id)` index in worst-case `O(N log N)` time, then use binary search for `O(log N)` per query while canonical rows keep their order. The index needs `O(N)` space; sorted insertion costs `O(N)` per update. Producing `K` rows adds `Ω(K)` work.

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
- **Symptom:** A repeated loop over `N` AoS rows reads one field, or each row carries alignment padding that field reordering cannot remove.
- **Action:** Put fields read together into dense columns; keep fields consumed together in payload rows. Separate differently aligned fields when this removes per-row padding. Access columns by the same index and update them together. Keep AoS if full-row access dominates or the split breaches its update budget.
- **Check:** Compare actual total bytes, the selected pass, full-row consumers, and insert/delete/reorder costs. Order-preserving insertion may move O(N) elements in every column; swap removal changes order. A scan split alone does not remove field bytes.
- **Example:** For 10,000 rows of `{score: 8 B, payload: 56 B}`, a score loop walks a 640 KB row region. `scores[i]: 8 B` plus `payloads[i]: 56 B` makes that loop walk an 80 KB column; raw fields still total 640 KB. The same split works for a flag-only pass: `flags[i]` holds each boolean beside `payloads[i]`, while the pass reads only `flags[]`. If false rows dominate and rows may move, DOD-020 can encode the flag as active/inactive array membership. A separate row `{link: 8 B, tag: 1 B}` can occupy 16 B with 8 B alignment: 160 KB for 10,000 rows. `links[]` plus `tags[]` uses 90 KB of raw elements before capacity. The AoS and column-only scans remain O(N); an active partition under DOD-020 visits A active rows. Time gains are `UNVERIFIED`.

### DOD-007 — Flatten stable relations
- **Symptom:** Each parent owns a separately allocated child list and traversal is sequential.
- **Action:** Append children to one owner array, and put `(offset, length)` in each parent. As an alternative for fixed adjacency lists, store `N+1` offsets instead of `(offset, length)` per parent. Rebuild or use another representation when arbitrary per-parent append must take O(1) time.
- **Check:** Include child order, empty parents, offset overflow, allocation count, and rebuild/update cost. Do not claim O(1) append to an arbitrary middle range.
- **Example:** `before: parents[i].children = separate_array`; `after: children = [a,b,c]; ranges = [(0,2),(2,0),(2,1)]`. Parent 1 reads `children[2:2]`; one array owns all children. Sequential traversal stays O(total children).

### DOD-008 — Resolve external strings to internal IDs at build time
- **Symptom:** Relations retain names and each runtime traversal searches a string-key map for the target row.
- **Action:** Validate names and duplicates once during build, assign typed dense IDs, and store IDs in relations. Keep a name table only when output or diagnostics require names. Drop the builder map after the final string lookup; keep it if runtime accepts names or inserts rows.
- **Check:** Preserve unknown-name errors and the existing duplicate-name policy. Preserve canonical output order and name spelling. Compare build lookups, retained bytes, and runtime traversal; include the name table and any retained map in the byte count.
- **Example:** `before: edge.target = "cat"; visit(edge) => map[edge.target]`. `after: edge.target = EntityId(7); visit(edge) => owner.resolve(edge.target)`. Keep `names[7] = "cat"` only if output needs it. The ID stays stable if the physical row moves. For `E` edges visited `Q` times, name lookup moves from each of `Q × E` visits to the build of `E` edges.

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
- **Example:** On a hypothetical 8 B-aligned runtime, `Actor {kind:1 B, x:4 B, y:4 B, extra_ptr:8 B}` occupies 24 B before subclass allocations. For 1,000,000 actors with 100,000 equipped, replace it with `tag[]:1 B` (`BASIC`, `EQUIPPED_IDLE`, `EQUIPPED_ARMED`), `x[]:4 B`, `y[]:4 B`, `extra_index[]:4 B`, and `equipped[]:{owner_id:4 B, item_id:4 B}` for equipped actors only. Raw elements total `1,000,000 × 13 B + 100,000 × 8 B = 13.8 MB` before capacity, versus at least `24 MB` of old base objects. The tag carries the armed flag; `extra_index[i]` names `equipped[]` only for equipped actors.

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
