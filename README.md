# Data-Oriented Design Skill

A language-independent guide for diagnosing data-oriented performance problems and selecting a measured redesign.

The skill now uses a staged performance method:

- freeze the workload;
- test scaling;
- find the hotspot;
- classify the bottleneck;
- record the access pattern;
- select the smallest targeted transformation;
- write a falsifiable prediction;
- validate the predicted physical metric;
- validate phase time, total time, memory, and correctness.

It covers AoS, SoA, AoSoA, typed IDs, flat relations, side storage, interning, packed flags, recomputation, access-order changes, indexing, allocation lifetime, and concurrency.

Each stable rule `DOD-001` through `DOD-023` has its own decision tree. The skill also contains one global diagnostic decision tree.

The writing rules use Simplified Technical English style: active voice, short procedural sentences, stable terminology, and explicit conditions. The skill does not claim certified ASD-STE100 compliance.

Skill file: `skills/data-oriented-design/SKILL.md`.

To install in Codex, copy `skills/data-oriented-design` into `~/.codex/skills/`.
To install in Claude Code, copy the same directory into `~/.claude/skills/` or a project's `.claude/skills/`, then invoke `/data-oriented-design`.
For claude.ai, put `data-oriented-design/` at the top of a ZIP and upload it in Customize > Skills.

Rule IDs `DOD-001` through `DOD-023` are stable for quality gates.
