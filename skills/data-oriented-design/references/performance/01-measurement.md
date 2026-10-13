# Performance Measurement and Reporting

## Language rules

Apply these rules to generated review output. Do not rewrite code identifiers or quoted source text.

- Use the same word for the same thing every time.
- Use approved common words when possible.
- Do not omit articles or determiners such as `the`, `a`, `an`, and `this`.
- Use active voice for procedures.
- Use the imperative for instructions.
- Put one instruction in each procedural sentence.
- Put one topic in each paragraph.
- Use vertical lists for complex text.
- Keep procedural sentences at 20 words or fewer.
- Keep descriptive sentences at 25 words or fewer.
- Keep noun clusters to three words when practical.
- Use simple present, simple past, or simple future for descriptions.
- Use infinitives when they make an instruction clearer.
- Do not use progressive verb forms.
- Do not use perfect verb forms.
- Do not use passive voice in procedures.
- Use an `-ing` form only in an established technical name or code identifier.
- Put a condition before an instruction when this improves clarity.

These rules follow the supplied Simplified Technical English style. They do not claim certified ASD-STE100 dictionary compliance.

## Layout choices

Choose between AoS, SoA, and AoSoA from the measured access pattern.

- Keep AoS when most fields are used together.
- Test SoA for sequential field-subset scans.
- Test AoSoA when pure SoA increases page or TLB pressure.
- Benchmark the chunk size for AoSoA.
- Do not rebuild full rows inside a hot SoA loop.

## Access-order choices

Layout is only one part of DOD.

Test these changes when locality or visit count is the problem:

- Fuse passes when they use the same data and preserve semantics.
- Split a pass when rare cold work pollutes the hot path.
- Block work when a smaller working set can stay in cache.
- Cluster work when a key causes random access.
- Include sort or reorder cost in the result.

## Reads, writes, and lifetime

Measure reads and writes.

Record:

```text
bytes read
bytes written
copies
memcpy bytes
producer stores
packing stores
allocation count
allocated bytes
reallocated bytes
peak live bytes
```

A smaller read path can still lose end-to-end when build or packing writes increase.

## Concurrency gate

Build a scaling curve before you add sharding:

```text
threads | wall
1
2
4
8
16
```

If scaling stops, classify the cause:

```text
serial fraction
lock contention
atomic contention
false sharing
memory bandwidth saturation
load imbalance
scheduler overhead
NUMA
```

Use thread-local storage, sharding, or cache-line isolation only after evidence supports the cause.

## Measurement rules

- Use repeated runs.
- Report median and variation.
- Keep before and after conditions equal.
- Interleave A/B runs when machine drift can matter.
- Separate cold and warm workloads.
- Measure PMU events in small related groups.
- Check PMU multiplexing and time-running values.
- Do not infer speed from Big O or row width alone.

## Falsifiable hypothesis

Write this block before implementation:

```text
HOTSPOT
<operation and share of target time>

EVIDENCE
<measurement that identifies the cost>

HYPOTHESIS
<physical cause>

CHANGE
<smallest proposed transformation>

PREDICTION
<metric that must move and direction>

CORRECTNESS
<invariants that must remain true>
```

If the predicted physical metric does not move, reject the performance hypothesis.

## Result classes

Use one result class:

- **PERFORMANCE WIN** — target wall time improves, and the causal metric supports the hypothesis.
- **MEMORY WIN** — memory or artifact size improves, but wall time does not.
- **SCALABILITY WIN** — larger workloads improve more than small workloads.
- **PARALLEL WIN** — thread scaling improves.
- **NO EFFECT** — target metrics stay within noise.
- **REGRESSION** — a target budget becomes worse.

