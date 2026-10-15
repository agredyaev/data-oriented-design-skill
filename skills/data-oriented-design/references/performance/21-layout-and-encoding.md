# Layout, Side Storage, and Encoding

### DOD-006 decision tree

```text
Does a hot operation use only a subset of fields?
 |-- NO
 |    |
 |    '-- Does repeated row padding breach a memory budget?
 |           |-- NO -> Keep AoS.
 |           '-- YES -> Test field reorder first. Then test a split if padding remains.
 '-- YES
      |
      |-- Does measured full-row work dominate the target workload?
      |      |-- YES -> Keep AoS as the baseline.
      |      '-- NO
      |
      |-- Is the hot access a sequential field-subset scan?
      |      |-- NO -> Test a hot/cold split. Keep AoS if random object access wins.
      |      '-- YES
      |
      |-- Does pure SoA create page, TLB, or multi-column working-set cost?
             |-- NO -> Test SoA.
             '-- YES -> Test AoSoA and benchmark the chunk size.
```

### DOD-006 — Choose AoS, SoA, or AoSoA from the access pattern
- **Symptom:** A repeated loop over `N` AoS rows reads one field. Or each row carries padding that field reordering cannot remove.
- **Action:** Keep AoS when full-row access dominates. Use SoA for sequential field-subset scans. Test AoSoA when pure SoA increases page or TLB pressure. Keep fields consumed together in one group. Update aligned columns together.
- **Check:** Compare total bytes, hot-pass time, full-row time, page and TLB behavior, and update cost. Benchmark AoSoA chunk size. A scan split alone does not remove field bytes.
- **Example:** For 10,000 rows of `{score: 8 B, payload: 56 B}`, a score loop walks a 640 KB row region. `scores[i]: 8 B` plus `payloads[i]: 56 B` makes that loop walk an 80 KB column; raw fields still total 640 KB. The same split works for a flag-only pass: `flags[i]` holds each boolean beside `payloads[i]`, while the pass reads only `flags[]`. If false rows dominate and rows may move, DOD-020 can encode the flag as active/inactive array membership. A separate row `{link: 8 B, tag: 1 B}` can occupy 16 B with 8 B alignment: 160 KB for 10,000 rows. `links[]` plus `tags[]` uses 90 KB of raw elements before capacity. The AoS and column-only scans remain O(N); an active partition under DOD-020 visits A active rows. Time gains are `UNVERIFIED`.

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

### DOD-009 — Narrow fields only with enforced bounds
- **Symptom:** A retained row uses a wider integer than its declared maximum requires.
- **Action:** Select a narrower representation only if a declared maximum covers every valid value and sentinel. Validate before conversion and define overflow behavior. Measure retained bytes and conversion/decode time before accepting the change.
- **Check:** Test the largest accepted value, first rejected value, sentinel, and serialized compatibility.
- **Example:** A 16-bit unsigned slot holds `0..65,535`. Use it only if the declared capacity and reserved values fit; otherwise keep a wider slot.

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

### DOD-014 — Measure padding before packing
- **Symptom:** A row in a retained collection measures wider than the sum of its fields because alignment inserts padding.
- **Action:** Inspect field offsets. Reorder private fields or derive a flag when another field determines it. If padding still repeats per row, compare columns under DOD-006. Change one layout property per comparison.
- **Check:** Report old/new row bytes and `row count × row bytes`. Preserve externally fixed serialized or binary layouts. Where the runtime does not expose field offsets, measure retained allocation instead.
- **Example:** With 8 B alignment, `[bool, 8 B ID, 4 B count, 2 B tag, bool]` can occupy 24 B; reordering the same fields can occupy 16 B. Verify both sizes in the target build.

### DOD-015 decision tree

```text
Does every row reserve an optional payload?
 |-- NO -> N/A.
 '-- YES
      |
      |-- Is new core + side index + present payload smaller than the old inline layout?
      |      |-- NO -> Keep inline.
      |      '-- YES
      |
      |-- Do measured side lookup and update costs meet their budgets?
             |-- NO -> Keep inline.
             '-- YES -> Use present-only side storage.
```

### DOD-015 — Move optional payloads out of every row
- **Symptom:** Every row reserves `B` bytes for an optional payload, but only `P` of `N` rows contain one.
- **Action:** Compare `N × old row bytes` with `N × new row bytes + side-table bytes`, including alignment and capacity. Move present payloads to a side table only when total bytes decrease. Require lookup and update time to meet their budgets.
- **Check:** Measure `P/N`, total bytes, access latency, and insert/delete/move consistency. Reserve an absent index and check it before side-array access. Keep the field inline if the side table breaches a budget.
- **Example:** `N=1,000` rows contain a 24 B core and a 16 B optional payload; `P=10` payloads are present. The old raw fields use `40 KB`. Replace them with `core[]:24 B × N`, `side_index[]:4 B × N`, and `side[]:{owner_id:4 B, payload:16 B} × P`: `24 KB + 4 KB + 0.2 KB = 28.2 KB` before capacity/alignment. Lookup uses one checked index, O(1); swap removal must repair the moved owner's side index.

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

### DOD-016 — Replace per-object variants with SoA encodings
- **Symptom:** A base object points to a separate subclass payload. Or a tagged union makes every row pay for its largest variant.
- **Action:** Count each variant. Put common fields in parallel columns. Let a tag encode both variant and mutually exclusive flags; reuse an `extra_index` field according to the tag. Put variant-only payloads in dense side arrays. If swap removal can move side rows, store each side row's owner ID. Update the moved owner's `extra_index`. Define a decode path for every tag before removing the old objects.
- **Check:** Compute `Σ(column capacity × element width) + Σ(side-array capacity × element width) + lookup bytes`, including alignment. Test every tag, side index, transition, invalid encoding, output order, and serialization. Compare full traversal and decode time with the old objects.
- **Example:** On a hypothetical runtime with 8 B alignment, `Actor {kind:1 B, x:4 B, y:4 B, extra_ptr:8 B}` occupies 24 B before subclass allocations. For 1,000,000 actors, use common columns `tag[]:1 B`, `x[]:4 B`, `y[]:4 B`, and `extra_index[]:4 B`. Tags are `BASIC`, `EQUIPPED_IDLE`, and `EQUIPPED_ARMED`. Only the 100,000 equipped actors have entries in `equipped[]:{owner_id:4 B, item_id:4 B}`. Raw elements total `1,000,000 × 13 B + 100,000 × 8 B = 13.8 MB` before capacity, versus at least `24 MB` of old base objects. The tag carries the armed flag; `extra_index[i]` names `equipped[]` only for equipped actors.

### DOD-017 decision tree

```text
Is a retained field fully derivable from retained input?
 |-- NO -> Keep it.
 '-- YES
      |
      |-- Does measured recompute cost meet the read-time budget?
      |      |-- NO -> Keep the field.
      |      '-- YES
      |
      '-- Does source lifetime cover every read?
             |-- NO -> Keep the field.
             '-- YES -> Test on-demand derivation.
```

### DOD-017 — Derive fields from retained input at use time
- **Symptom:** Each of `N` rows stores `end`, `line`, `column`, or another value determined by retained `start`, `kind`, and source data.
- **Action:** Write the exact derivation first. Keep only its required inputs in the row; derive the value at the consumer. For byte columns, use a sorted `line_starts[]`: binary-search the last start not after `token.start`, then subtract it. Derive `end = start + fixed_width(kind)` only for fixed-width kinds; scan source bytes for variable-width kinds.
- **Check:** Retain the source until the last derivation. Validate that source length and line offsets fit their integer fields. Test final line, empty input, multi-byte text, line endings, and each token kind. Compare saved row bytes and added per-read work; keep a stored value if repeated reads exceed its time budget.
- **Example:** `before: token = {kind:1 B, start:4 B, end:4 B, line:4 B, column:4 B}`. `after: token = {kind:1 B, start:4 B}` plus `source` and `line_starts[]`. With source length bounded to `2^32-1` bytes and `N=1,000,000`, removing the three 4 B fields removes `12 MB` of raw field bytes before row alignment; lookup is `O(log L)` for `L` lines, plus any source scan. Actual retained bytes and latency remain `UNVERIFIED`.

### DOD-023 decision tree

```text
Do rows store several independent boolean fields?
 |-- NO -> N/A.
 '-- YES
      |
      |-- Does a mask shrink aligned size OR have a grouped-access benefit to test?
      |      |-- NO -> Keep explicit fields.
      |      '-- YES
      |
      |-- Do threads update different flags concurrently?
             |-- YES -> Measure contention before packing.
             '-- NO -> Test a named bit mask.
```

### DOD-023 — Pack independent row flags
- **Symptom:** Each of `N` rows stores separate boolean fields that are read or serialized as a group.
- **Action:** Assign a fixed bit position to each flag and store one integer mask. Replace field reads/writes with named bit tests and updates. Use this layout only when the aligned row shrinks or grouped flag access meets a stated budget.
- **Check:** Verify each flag combination, default value, and serialized meaning. Compare actual row bytes and flag-read/update time. If multiple threads update different flags in one mask, account for synchronization and contention.
- **Example:** In a runtime with 1 B booleans, eight flags occupy 8 B before padding; one 8-bit mask occupies 1 B. At `N=10,000`, raw flag bytes fall by `70 KB`, but aligned rows may save `0 B`. With unchanged row size, a frequent combined flag test can still justify an experiment; accept only its measured time benefit within update/synchronization budgets.

### DOD-027 decision tree

```text
Do the producer and repeated consumers need different layouts?
 |-- NO -> Use one representation.
 '-- YES
      |
      |-- Is packing deterministic and behavior-preserving?
      |      |-- NO -> Keep one representation.
      |      '-- YES
      |
      '-- Is packing cost lower than measured downstream savings?
             |-- NO -> Keep one representation.
             '-- YES -> Add one linear packing stage.
```

### DOD-027 — Separate producer and consumer layouts
- **Symptom:** The producer needs an easy-to-build shape, but repeated consumers need a different layout.
- **Action:** Add one deterministic linear packing stage when measured downstream savings repay its cost.
- **Check:** Measure producer cost, packing cost, writes, copies, consumer savings, and total wall time.
- **Example:** Parse into a simple builder form, pack once into dense columns, then scan those columns repeatedly.

### DOD-033 decision tree

```text
Does growth cause reallocations or copied bytes in a hot build path?
 |-- NO -> N/A.
 '-- YES
      |
      |-- Is exact output cardinality known before growth?
      |      |-- YES -> Validate byte-size arithmetic and memory limit, then reserve.
      |      '-- NO
      |
      |-- Is a safe upper bound known AND does reserving it fit peak/retained limits?
      |      |-- YES -> Test bounded reservation; count unused capacity.
      |      '-- NO -> Do not reserve the legal maximum merely because it is known.
      |
      '-- Does a measured estimate reduce total build cost within memory limits?
             |-- NO -> Keep checked dynamic growth.
             '-- YES -> Reserve from the estimate; permit checked growth beyond it.
```

### DOD-033 — Preallocate from known or measured cardinality
- **Symptom:** A hot build path repeatedly grows arrays and copies retained elements.
- **Action:** Validate cardinality-to-byte arithmetic and allocation limits before reservation. Reserve exact capacity when known and feasible. Otherwise test a bounded reservation or measured estimate against growth cost and memory limits. An estimate is not an accepted-input bound; keep checked growth or the contractual failure path.
- **Check:** Measure reallocations, copied bytes, unused capacity, peak bytes, and build time.
- **Example:** A legal upper bound of 1 billion 16 B entries would reserve 16 GB. With a 128 MB budget and typical output of 2,000 entries, reject that reservation. Test a measured small estimate with checked growth; do not reject valid larger outputs merely because they exceed the estimate.
