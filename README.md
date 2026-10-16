# Data-Oriented Design Skill

A language-independent skill for converting object-based subsystems to DOD/PWP and diagnosing data-oriented performance problems.

The skill uses progressive disclosure. The skill router routes each task to the smallest relevant workflow or rule block instead of loading the full methodology. The entry file is `skills/data-oriented-design/SKILL.md`.

## Core workflow

The [structural workflow](skills/data-oriented-design/references/workflow.md) follows: contract → current process/data map → **physical operation/access/layout** → element necessity → target passes/stores → comparison → implementation → verification. Architecture cleanup with OOP/layer signals cannot stop at YAGNI-only cleanup; the target is derived independently of current layers.

For profiler-led optimization, rank measured costs against the target, select an actionable cause, test one change, then reprofile and rerank. Switch to structural analysis for shared causes or ineffective local tuning. Individual modules can also run alone when their inputs are available.

The workflow owns the default full-route composition and proportional reporting format. The module composition map supports independent capabilities and custom routes with explicit inputs, outputs, and information dependencies. Structural analysis supplies mapping and candidate-design techniques. A local fix requires only affected-behavior verification; architecture work uses typed maps and relevant deltas. Rule-by-rule reports are reserved for explicitly requested coverage audits.

The performance methodology covers workload definition, scaling checks, hotspot diagnosis, access patterns, falsifiable hypotheses, matched benchmarks, and causal acceptance.

An OOP → DOD/PWP conversion produces explicit passes/functions, owned data stores and typed internal relationships. Naming an old object's responsibility does not justify keeping its architecture. The transformation module requires a concrete target, removal/replacement map, and scoped evidence for remaining mechanisms. Partial conversion is reported as partial; structural conversion alone does not establish a speedup.

## Coverage

The skill covers:

- AoS, SoA, and AoSoA;
- typed IDs and pointer-free frozen data;
- flat relations, ranges, CSR, and side storage;
- canonical and derived state;
- string and canonical-value interning;
- hot/cold splits and compact encodings;
- pass fusion, fission, blocking, and clustering;
- allocation lifetime and preallocation;
- serialization and indexing;
- concurrency ownership and sharding;
- YAGNI and architecture cleanup;
- correctness-preserving structural refactoring.

A compiler-specific module also covers wide classification, compact token streams, pointerless parsing, direct IR emission, intermediate-representation elimination, and canonical production paths. The PWP/512 router selects five independent decision blocks: batch/classification, compaction, lexical lookup, token streams/direct emission, and retained state. Each decision tree includes a worked example and rejection conditions.

## Files

- Skill router: `skills/data-oriented-design/SKILL.md`
- Module composition: `skills/data-oriented-design/references/modules.md`
- Workflow: `skills/data-oriented-design/references/workflow.md`
- Performance router: `skills/data-oriented-design/references/performance-methodology.md`
- Engineering router: `skills/data-oriented-design/references/dod-yagni-engineering-rules.md`
- Structural analysis: `skills/data-oriented-design/references/engineering/00-structural-analysis.md`
- OOP → DOD/PWP transformation: `skills/data-oriented-design/references/engineering/10-oop-to-dod.md`
- Compiler DOD router: `skills/data-oriented-design/references/engineering/09-wide-pointerless-compiler.md`
- Compiler pipeline elimination: `skills/data-oriented-design/references/engineering/compiler/10-pipeline-elimination.md`
- Wide frontend/tokenization: `skills/data-oriented-design/references/engineering/compiler/20-wide-frontend.md`
- Optional PWP / 512-byte profile: `skills/data-oriented-design/references/engineering/compiler/25-pwp-512-profile.md`
- Pointerless compiler state: `skills/data-oriented-design/references/engineering/compiler/30-pointerless-state.md`
- Compiler redesign validation: `skills/data-oriented-design/references/engineering/compiler/40-validation.md`
- Focused engineering blocks: `skills/data-oriented-design/references/engineering/`
- Performance rule packs: `skills/data-oriented-design/references/performance/`

## Rule IDs

Each performance rule `DOD-001` through `DOD-033` has one decision tree and one rule definition.

Rule IDs `DOD-001` through `DOD-023` remain stable. Rules `DOD-024` through `DOD-033` extend the methodology without renumbering the original set.

## Installation

For Codex, copy `skills/data-oriented-design` into `~/.codex/skills/`.

For Claude Code, copy the same directory into `~/.claude/skills/` or a project's `.claude/skills/`, then invoke `/data-oriented-design`.

For claude.ai, place `data-oriented-design/` at the top level of a ZIP and upload it in Customize > Skills.

