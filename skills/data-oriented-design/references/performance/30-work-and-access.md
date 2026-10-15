# Work, Reuse, and Access Rules

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
      |-- Does measured saved query time exceed cache build and invalidation cost?
             |-- NO -> Recompute locally.
             '-- YES -> Cache with explicit invalidation.
```

### DOD-010 — Keep passes and scratch local
- **Symptom:** A pass allocates per row, writes shared mutable marks, or retains a cache for data used by one request.
- **Action:** Reuse operation-local scratch. Size queues for their maximum occupancy; size ID-indexed marks for the validated ID domain, or use explicit sparse/remapped storage. Include initialization/reset and concurrent request memory. Compute a derived value inside the request when it is used only there. Add a retained cache only when measured savings exceed build and invalidation cost within the memory budget.
- **Check:** Count allocations per operation, scratch peak, concurrent behavior, and cache invalidation paths.
- **Example:** Visiting only ID 999,999 still requires 1,000,000 entries in `visited[id]`, not one entry. If that exceeds the request budget, test sparse marks or a remapping; include their lookup/reset costs. Local marks need no shared lock.

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

### DOD-018 — Skip unchanged or repeated work
- **Symptom:** A no-op update still parses, rebuilds, serializes, or converts IDs to strings and back.
- **Action:** Check a trusted version or verified content identity before parsing, rebuilding, or serializing. Carry validated typed IDs through internal stages and render strings at the output boundary.
- **Check:** Hash collisions or stale metadata cannot authorize skipping required validation; compare changed, unchanged, and malformed inputs.
- **Example:** If source bytes and required metadata match the retained snapshot, skip reparse and staging; a changed source still follows the full validation path.

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

### DOD-019 — Remove random lookup from a sequential scan
- **Symptom:** A pass over `N` rows performs a map lookup or pointer chase for every row to fetch stable companion data.
- **Action:** Resolve companions into parallel arrays or stable dense IDs during build, then scan them by index. Keep the map for queries that ask for arbitrary keys.
- **Check:** Measure lookup count and the extra bytes/update work; verify companion arrays stay aligned after insert, delete, and reorder.
- **Example:** Replace `N` string-key lookups per ranking pass with `N` indexed reads from a parallel weight array.

### DOD-020 decision tree

```text
Does a repeated pass skip inactive rows?
 |-- NO -> N/A.
 '-- YES
      |
      |-- Is new build + transition cost + scan cost lower than the old measured total?
      |      |-- NO -> Keep the flag scan.
      |      '-- YES
      |
      |-- May rows move?
             |-- YES -> Test active/inactive partitions.
             '-- NO -> Test an active-ID list.
```

### DOD-020 — Partition active rows when scans repay transitions
- **Symptom:** A repeated loop skips inactive rows before doing work for most rows.
- **Action:** Keep active and inactive rows in separate dense arrays. Let array membership encode the flag. Scan only the active array. When external references exist, maintain `ID → (partition, slot)`; if rows cannot move, keep active IDs instead. Compare measured `T_new_build + U × T_new_transition + Q × T_new_scan` with `T_old_build + U × T_old_transition + Q × T_old_scan` on the same workload. Include ID-map and order-maintenance time.
- **Check:** Measure scanned rows, state-transition moves, total row bytes, and full-pass latency. Preserve stable IDs, output order, and concurrent update behavior. Swap removal moves O(1) rows but changes order; count ID-map maintenance separately. Order-preserving moves can cost O(N).
- **Example:** With 1,000,000 rows and 10,000 active rows, the active partition visits 10,000 rows and needs no per-row active check. Each state transition moves a row and fixes its ID mapping. An active-ID list visits 10,000 IDs but then fetches their rows. Compare both against the 1,000,000-row scan; counts alone do not prove speed.

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

### DOD-021 — Price an index across its lifetime
- **Symptom:** Exact or range queries repeatedly scan the same rows, while an index would add build and update work.
- **Action:** Compare `B + Q × L_new + U × M_new` with `Q × L_old` for the same workload. Here `B` is index build time, `L` is lookup time, and `M` is extra maintenance time per update. Compare index bytes with the memory budget.
- **Check:** Measure build, lookup, and update time. Report break-even query count or `UNVERIFIED` when times are missing. Keep output order independent of index order.
- **Example:** With no updates and fixed `L_old > L_new`, the index repays build time only when `Q > B / (L_old - L_new)`.

### DOD-024 decision tree

```text
Which measured symptom applies? Evaluate each applicable branch separately.
 |-- Repeated passes over the same data
 |      '-- Can fusion preserve dependencies, errors, effects and order?
 |             |-- YES -> Test fusion; include register/code-size costs.
 |             '-- NO -> Keep the required pass boundary.
 |-- One hot loop contains rare/cold work
 |      '-- Can cold work be deferred without changing effects, errors or order?
 |             |-- YES -> Test fission; include queues and the extra traversal.
 |             '-- NO -> Keep the required execution order.
 '-- Neither -> N/A.
```

### DOD-024 — Fuse or split passes from measured reuse
- **Symptom:** Several passes revisit the same data, or one hot loop contains rare cold work.
- **Action:** Test fusion when passes can share hot data. Test fission when rare work pollutes the hot path.
- **Check:** Preserve dependencies, errors, order, and output. Measure visits, cache behavior, phase time, and total time.
- **Example:** Three independent scans can test fusion. A single loop updating scores and formatting rare diagnostics can test fission only if formatting may be deferred. If the first diagnostic must abort before later score updates, preserve that boundary. Include queued diagnostic IDs and the second pass in the comparison.

### DOD-025 decision tree

```text
Does the operation reuse data after the working set leaves cache?
 |-- NO -> N/A.
 '-- YES
      |
      |-- Can one block fit the target cache level with required companion data?
      |      |-- NO -> Keep the current schedule.
      |      '-- YES
      |
      '-- Does block overhead stay within the phase budget?
             |-- NO -> Keep the current schedule.
             '-- YES -> Test blocking or tiling.
```

### DOD-025 — Block work to bound the working set
- **Symptom:** Reused data leaves the target cache before the next consumer uses it.
- **Action:** Process bounded blocks that include all companion data for the local work.
- **Check:** Measure block overhead, cache behavior, TLB behavior, phase time, and total time.
- **Example:** Process rows in 256-row blocks only after a benchmark shows that this block size wins.

### DOD-026 decision tree

```text
Does a key cause random access to stable companion data?
 |-- NO -> N/A.
 '-- YES
      |
      |-- May computation reorder while preserving dependencies, errors and effects?
      |      |-- NO -> Keep computation order; an output index cannot repair it.
      |      '-- YES
      |
      |-- Must emitted results retain canonical order?
      |      |-- YES -> Include an order index and restoration cost.
      |      '-- NO -> No restoration required.
      |
      '-- Is grouping + restoration cheaper than the saved random-access cost?
             |-- NO -> Keep the current order.
             '-- YES -> Test clustering or reordering.
```

### DOD-026 — Cluster work to remove random access
- **Symptom:** A stable key causes repeated random access to companion data.
- **Action:** Group work by the key when the order can change safely.
- **Check:** Include sort or reorder cost. Preserve canonical output with a separate order index when required.
- **Example:** Independent pure calculations can group by `parent_id` and restore input order with original indices. Ordered account withdrawals cannot reorder if earlier withdrawals affect later success; sorting their output cannot restore the original behavior.

### DOD-032 decision tree

```text
Does text parsing, formatting, or serialization dominate the target path?
 |-- NO -> N/A.
 '-- YES
      |
      |-- Is the format internal or cache-only?
      |      |-- NO -> Preserve the external contract.
      |      '-- YES
      |
      '-- Can a compact binary format avoid parsing or copies within its budget?
             |-- NO -> Keep the current format.
             '-- YES -> Test the machine-oriented format.
```

### DOD-032 — Use a machine-oriented internal serialization format
- **Symptom:** Internal cache or build paths spend meaningful time parsing, formatting, or copying text metadata.
- **Action:** Test a compact binary format only for internal or versioned data.
- **Check:** Preserve external contracts. Measure file bytes, parse time, copy bytes, cache-hit time, and compatibility behavior.
- **Example:** Replace an internal text cache record with a versioned binary record when parsing dominates cache-hit time.
