# Performance Methodology

Use this file as a router. Load the smallest performance block that answers the diagnosed problem.

## Start here

For a performance task, read [Performance diagnosis](performance/00-diagnosis.md) first. It contains the core cost model, workload/scaling gates, bottleneck classification, global decision tree, transformation map, and code signatures.

Read [Performance measurement and reporting](performance/01-measurement.md) when establishing a benchmark, making a performance claim, evaluating concurrency, or reporting a result.

After diagnosis, load only the rule pack that contains the selected rule IDs:

| Rule family | Rule IDs | Read |
| --- | --- | --- |
| Diagnosis, budgets, correctness, evidence, measurement validity, outside-DOD stop | DOD-001–004, 011–013, 030–031 | [Foundation, evidence, and acceptance](performance/10-foundation.md) |
| Pointer identity, handles, flat relations, string/canonical-value interning | DOD-005, 007–008, 022, 028 | [Identity, handles, and flat relations](performance/20-identity-and-relations.md) |
| AoS/SoA/AoSoA, compact fields, side storage, variants, derived fields, packing | DOD-006, 009, 014–017, 023, 027, 033 | [Layout, side storage, and encoding](performance/21-layout-and-encoding.md) |
| Scratch, repeated work, random lookup, active partitions, indexes, pass fusion/fission, blocking, clustering, serialization | DOD-010, 018–021, 024–026, 032 | [Work, reuse, and access](performance/30-work-and-access.md) |
| Thread scaling, sharding, ownership partitioning | DOD-029 | [Concurrency and scaling](performance/40-concurrency.md) |

## Loading rule

Do not load all rule packs by default. Use `00-diagnosis.md` to select a rule family, then open the relevant pack. Load another pack only when the finding crosses that boundary.

For a structural redesign, read `../engineering/00-structural-analysis.md` before selecting a layout rule. Structural elimination takes priority over tuning a mechanism that can be removed.

The complete rule set remains DOD-001 through DOD-033. Each rule keeps one decision tree and one rule definition in the routed packs.
