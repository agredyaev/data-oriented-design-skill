---
name: data-oriented-design
description: Design or review data-oriented runtime layouts across languages when hot loops or large collections matter. Check Big O time/space, memory, dense IDs, SoA/AoS, and graph storage.
---

# Data-Oriented Design

Choose the representation from the work the program actually does. Apply this skill when data layout or ownership affects a significant path. Honor the project's correctness, compatibility, and observable ordering requirements. Examples illustrate decisions; use the active workload and contract.

## Inspect before changing layout

- DOD-001: Trace data from admission/build through retained runtime state to its consumers and output boundary.
  Example: parse records, validate them, retain compact rows, run queries, then serialize output.
- DOD-002: Prioritize collections by live footprint and time in repeated passes. Identify element count and size (including padding), fields read/written, identity domain, mutation frequency, lifetime, and allocation ownership. For new designs, use documented bounds and expected operations; for refactors, measure or estimate current bytes, allocations, and time on a representative workload. Label estimates.
  Example: one million 64-byte rows use about 64 MB before allocation overhead, while a repeated pass reads one 8-byte field.
- DOD-003: Name input sizes, output size, and operation frequency. Compare build, update, and query time/space complexity, including nested scans and lookup costs; distinguish expected from worst-case bounds. Address costly asymptotics before layout tuning, using actual scale. Big O alone does not prove a bottleneck.
  Example: Q exact-key queries over N rows cost O(QN) by scanning; sorting once and binary-searching costs O(N log N + Q log N), excluding output.
- DOD-004: If the path is small or cold and no concrete cost is shown, keep the simpler representation unless the project contract requires a specific layout.
  Example: keep a map of 20 settings loaded once.

## Choose a representation

- DOD-005: Keep external stable identity separate from compact, typed runtime indices. Check bounds when creating or decoding indices. Define canonical ordering where output or hashes must be deterministic.
  Example: map an external UUID to a checked 32-bit slot; serialize in the contract's stable order.
- DOD-006: Prefer contiguous rows and slices for sequential traversal. Use AoS when passes need whole rows; split hot/cold fields or use SoA when repeated passes touch only a subset. Do not force either layout everywhere.
  Example: whole-row validation favors AoS; a repeated sum over one column may favor SoA.
- DOD-007: Use ranges for contiguous ownership, CSR or offsets plus flat arrays for stable sparse adjacency, sorted vectors for small sparse sets, and bitsets only when dense repeated set operations justify them. Avoid one heap allocation per retained element.
  Example: offsets [0,2,2,5] plus five flat targets encode adjacency for three nodes without three child vectors.
- DOD-008: Temporary maps and flexible builders are fine at admission. For read-mostly snapshots, freeze validated data and drop build-only state. Keep one authority for identity and order; use lookup maps as side indexes when arrays are canonical. Intern strings when repeated long-lived or hot comparisons justify it; avoid formatting names in hot loops when IDs suffice.
  Example: a builder map resolves names, while the frozen row array owns order; retain the map only if runtime name lookup needs it.
- DOD-009: Narrow integers or pack variants only with a proven bound or distribution, checked overflow behavior, and a measured decode trade-off.
  Example: use a 16-bit index only when its checked maximum is at most 65,535 and measured footprint gain justifies decode overhead.
- DOD-010: Prefer explicit passes and operation-local bounded scratch. Shared caches, pointer-linked object graphs, per-element locks, and dynamic dispatch in hot loops need a demonstrated reason.
  Example: keep traversal marks in a request-local array when only one edit needs them.

## Verify the change

- DOD-011: Preserve identity, ordering, bounds, stale-handle rejection, side-table updates, serialization, and other applicable product invariants with focused behavioral checks. Do not weaken validation, authorization, recovery, diagnostics, or wire compatibility for a layout change.
  Example: after deleting a row and reusing its slot, an old generation-tagged handle must fail rather than select the new row.
- DOD-012: For a material refactor, derive before/after time and space complexity with named variables and assumptions. Measure the target cost and material trade-offs (footprint, allocations, latency) on matched representative inputs, stating warm/cold state; for new designs, check documented bounds or budgets. Report regressions and trade-offs. Revert performance-only complexity without demonstrated benefit.
  Example: AoS to SoA remains O(N); claim a gain only when matched latency and memory measurements support it.
- DOD-013: In reviews, rank findings by impact. For each, cite applicable rule IDs and show path and scale, current/proposed complexity, layout change, correctness constraint, and evidence. Label estimates; if none, state the inspected scope and missing measurements. Style alone is not a finding.

## Illustrative review outcomes

The numbers show the reporting shape, not evidence for another project.

- Finding (DOD-003, DOD-007): `load` rescans `M=20,000` records for each of `D=200` owners: `O(DM)` time; a representative profile attributes 40% of load time to this loop. Group by checked dense owner ID once: `O(D+M)` time and `O(D+M)` extra space. Preserve per-owner order and duplicate errors; compare matched load time and peak memory before accepting the change.
- No finding (DOD-003, DOD-004): `report(id)` sorts `E=50,000` edges once in `O(E log E)` time, then answers each query in `O(log E+k)` time for `k` returned edges. Measured p95 is 0.2 ms against a 1 ms budget; keep the layout.
