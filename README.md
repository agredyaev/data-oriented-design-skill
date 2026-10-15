# Data-Oriented Design Skill

A language-independent skill for diagnosing data-oriented performance problems and designing simpler, measurable architectures.

The skill uses progressive disclosure. `SKILL.md` routes each task to the smallest relevant workflow or rule block instead of loading the full methodology.

## Core workflow

For non-trivial architecture or performance work:

1. define the contract;
2. draw the current typed process and retained data;
3. count passes, lookups, parsing, copies, allocations, synchronization, and duplicate state;
4. remove unnecessary work or representations before tuning them;
5. design a simpler candidate from the contract;
6. select the relevant DOD rules;
7. validate correctness and the claimed physical/performance effect.

The performance methodology covers workload definition, scaling checks, hotspot diagnosis, access patterns, falsifiable hypotheses, matched benchmarks, and causal acceptance.

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

A compiler-specific module also covers wide classification, compact token streams, pointerless parsing, direct IR emission, intermediate-representation elimination, and canonical production paths.

## Files

- Skill router: `skills/data-oriented-design/SKILL.md`
- Workflow: `skills/data-oriented-design/references/workflow.md`
- Performance router: `skills/data-oriented-design/references/performance-methodology.md`
- Engineering router: `skills/data-oriented-design/references/dod-yagni-engineering-rules.md`
- Structural analysis: `skills/data-oriented-design/references/engineering/00-structural-analysis.md`
- Wide/pointerless compiler module: `skills/data-oriented-design/references/engineering/09-wide-pointerless-compiler.md`
- Focused engineering blocks: `skills/data-oriented-design/references/engineering/`
- Performance rule packs: `skills/data-oriented-design/references/performance/`

## Rule IDs

Each performance rule `DOD-001` through `DOD-033` has one decision tree and one rule definition.

Rule IDs `DOD-001` through `DOD-023` remain stable. Rules `DOD-024` through `DOD-033` extend the methodology without renumbering the original set.

## Installation

For Codex, copy `skills/data-oriented-design` into `~/.codex/skills/`.

For Claude Code, copy the same directory into `~/.claude/skills/` or a project's `.claude/skills/`, then invoke `/data-oriented-design`.

For claude.ai, place `data-oriented-design/` at the top level of a ZIP and upload it in Customize > Skills.
