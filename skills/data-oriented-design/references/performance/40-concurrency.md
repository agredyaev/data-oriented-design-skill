# Concurrency and Scaling Rules

### DOD-029 decision tree

```text
Does throughput stop scaling as thread count rises?
 |-- NO -> Keep the current ownership model.
 '-- YES
      |
      '-- Which cause is supported by the scaling measurements?
             |-- Lock/atomic contention -> Can mutable ownership partition safely?
             |      |-- YES -> Test local state or sharding, including merge costs.
             |      '-- NO -> Test a synchronization design preserving shared invariants.
             |-- False sharing -> Test cache-line isolation or ownership separation.
             |-- Load imbalance -> Test scheduling/partition sizes, including overhead.
             |-- Bandwidth saturation -> Reduce bytes/visits; sharding alone adds no bandwidth.
             |-- NUMA -> Test placement and local access; include migration/replication costs.
             |-- Serial fraction -> Inspect the serial dependency before parallelizing.
             |-- Scheduler overhead -> Test task granularity or fewer workers.
             '-- Unknown -> Diagnose first; do not prescribe sharding.
```

### DOD-029 — Partition mutable state only after a scaling diagnosis
- **Symptom:** More threads stop improving throughput.
- **Action:** Measure the scaling limit before you add thread-local state, sharding, or cache-line isolation.
- **Check:** Classify lock, atomic, false-sharing, imbalance, bandwidth, scheduler, and NUMA costs.
- **Example:** Shared-map lock waits rising with thread count support a sharding experiment. A read-only scan already saturating memory bandwidth does not: test fewer bytes/visits or fewer workers. Recheck throughput and latency at the required thread counts.
