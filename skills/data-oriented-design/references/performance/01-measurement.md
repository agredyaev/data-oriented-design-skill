# Performance Measurement and Reporting

Use this block for matched benchmark mechanics and result classification. Measure only the claimed target plus costs/guardrails that can change the adoption decision.

## Workload contract

Before comparing candidates, keep the relevant conditions matched:

```text
input and distribution
build/version
feature flags
thread count
machine
compiler flags
cache state
output validation
repetition count
acceptance rule
```

Separate cold, warm, full, and incremental workloads when they represent different product behavior.

## Measurement rules

- Use identical before/after inputs and conditions.
- Declare the acceptance rule before implementation.
- Use repeated runs and report median plus variation/uncertainty.
- Interleave A/B runs when machine drift can matter.
- Measure the physical metric predicted by the hypothesis and the declared target.
- Measure only affected construction/update/lifetime guardrails; state why omitted costs cannot affect acceptance.
- Separate phase time from end-to-end time.
- Measure reads and writes when layout/packing changes them.
- Check PMU multiplexing/time-running values when hardware counters are used.
- Do not infer speed from Big O, row width, fewer allocations, or cache intuition alone.

## Falsifiable hypothesis

Write this before implementation when a cost claim selects the change:

```text
HOTSPOT
<operation/state and measured contribution to the target>

EVIDENCE
<measurement that identifies the cost>

HYPOTHESIS
<physical/logical cause>

CHANGE
<smallest transformation that removes the cause>

PREDICTION
<metric that must move and direction>

TARGET
<declared acceptance rule>

GUARDRAILS
<required limits that may be affected>

CORRECTNESS
<behavior that must remain true>
```

If the predicted causal metric does not move, reject that performance hypothesis even when another local metric changes.

## Reads, writes, allocation, and lifetime

Record only dimensions changed by the candidate, for example:

```text
bytes read / written
copies or memcpy bytes
packing/producer stores
allocation count / allocated bytes
reallocated bytes
retained bytes
peak live bytes
build/update cost
```

A smaller consumer read path can lose end-to-end if packing/build writes rise. A retained-memory win can be valid with unchanged latency when the latency guardrail still passes.

## Layout choices

Choose AoS, SoA, or AoSoA from measured access behavior.

- Keep AoS when most fields are consumed together.
- Test SoA for repeated sequential field-subset scans.
- Test AoSoA when pure SoA increases page/TLB or multi-column working-set cost.
- Benchmark chunk size when AoSoA is selected.
- Reject a split that reconstructs full rows inside the hot loop and loses the intended access benefit.

## Access-order choices

When measured reuse/access order is the cause:

- fuse passes only when dependencies, errors, effects, and order permit it;
- split cold work only when deferral preserves semantics;
- block only when the bounded working set fits the intended cache level;
- cluster/reorder only when computation order may change safely;
- include sort/reorder/restoration cost.

## Concurrency gate

Before sharding or adding thread-local state, measure a scaling curve such as:

```text
threads | wall/throughput
1
2
4
8
16
```

Classify the supported cause: serial fraction, lock/atomic contention, false sharing, bandwidth saturation, load imbalance, scheduler overhead, or NUMA. Sharding is not a remedy for bandwidth saturation.

## Result classes

Choose adoption precedence first:

```text
required correctness violated
  -> REJECT

required budget/guardrail violated
  -> REGRESSION; reject adoption

required acceptance evidence missing
  -> UNVERIFIED

declared target passes
  -> accept only that supported result class

declared target does not pass
  -> TARGET UNMET; keep only for a separately justified measured benefit
     or named structural simplification
```

Supported result classes:

- **PERFORMANCE WIN** — declared time/throughput target passes; name phase or end-to-end scope.
- **MEMORY WIN** — declared retained bytes, peak bytes, or artifact-size target passes.
- **SCALABILITY WIN** — declared workload-scaling criterion passes over the tested range.
- **PARALLEL WIN** — declared thread-scaling criterion passes.
- **STRUCTURAL SIMPLIFICATION** — named representation/pass/state/invariant was removed with behavior verified; no cost claim implied.
- **NO EFFECT** — compared target metrics remain within measurement uncertainty.
- **REGRESSION** — required budget fails or a meaningful worsening violates the adoption rule.
- **TARGET UNMET** — narrower benefit may exist, but the declared target still fails.
- **UNVERIFIED** — evidence needed for acceptance is missing.

### Examples

| Before → after | Contract | Verdict |
| --- | --- | --- |
| retained 200 → 140 MB; latency 10 → 10 ms | retained ≤150 MB; latency ≤11 ms | MEMORY WIN; no speed claim |
| retained 200 → 140 MB; latency 10 → 14 ms | same limits | REGRESSION; reject adoption |
| phase 8 → 4 ms; total 100 → 99 ms within ±3 ms | total ≤90 ms | phase benefit only; TARGET UNMET |
| wrapper/state removed; behavior tests pass; no timing run | structural simplification only | STRUCTURAL SIMPLIFICATION |

Name statistically supported worsening even when it remains inside a guardrail if it matters to the trade-off.
