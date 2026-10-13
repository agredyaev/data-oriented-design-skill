# Concurrency and Scaling Rules

### DOD-029 decision tree

```text
Does throughput stop scaling as thread count rises?
 |-- NO -> Keep the current ownership model.
 '-- YES
      |
      |-- Do measurements show lock, atomic, false-sharing, imbalance, bandwidth, or NUMA cost?
      |      |-- NO -> Do not add sharding.
      |      '-- YES
      |
      '-- Can ownership partition the mutable state?
             |-- YES -> Test thread-local state or sharding.
             '-- NO -> Test work partitioning or another synchronization design.
```

### DOD-029 — Partition mutable state only after a scaling diagnosis
- **Symptom:** More threads stop improving throughput.
- **Action:** Measure the scaling limit before you add thread-local state, sharding, or cache-line isolation.
- **Check:** Classify lock, atomic, false-sharing, imbalance, bandwidth, scheduler, and NUMA costs.
- **Example:** Shard a mutable pool only after measurements show shared-map contention.
