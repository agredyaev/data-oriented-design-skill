# Data-Oriented Design Skill

A language-independent guide for diagnosing data-oriented performance problems and selecting a measured redesign.

The skill uses progressive disclosure. `SKILL.md` routes each task to the required workflow and rule blocks. The performance methodology uses this staged method:

- freeze the workload;
- test scaling;
- find the hotspot;
- classify the bottleneck;
- record the access pattern;
- select the smallest targeted transformation;
- write a falsifiable prediction;
- validate the predicted physical metric;
- validate phase time, total time, memory, and correctness.

It covers AoS, SoA, AoSoA, typed IDs, flat relations, side storage, string and canonical-value interning, access-order changes, packing, indexing, serialization, allocation lifetime, and concurrency.

Each rule `DOD-001` through `DOD-033` has its own decision tree. The skill also contains one global diagnostic decision tree.

The writing rules use Simplified Technical English style: active voice, short procedural sentences, stable terminology, and explicit conditions. The skill does not claim certified ASD-STE100 compliance.

Skill router: `skills/data-oriented-design/SKILL.md`.\n\nDetailed material:\n\n- workflow: `skills/data-oriented-design/references/workflow.md`;\n- performance methodology and `DOD-001` through `DOD-033`: `skills/data-oriented-design/references/performance-methodology.md`;\n- engineering router: `skills/data-oriented-design/references/dod-yagni-engineering-rules.md`;\n- structural analysis: `skills/data-oriented-design/references/engineering/00-structural-analysis.md`;\n- focused engineering blocks: `skills/data-oriented-design/references/engineering/`.

To install in Codex, copy `skills/data-oriented-design` into `~/.codex/skills/`.
To install in Claude Code, copy the same directory into `~/.claude/skills/` or a project's `.claude/skills/`, then invoke `/data-oriented-design`.
For claude.ai, put `data-oriented-design/` at the top of a ZIP and upload it in Customize > Skills.

Rule IDs `DOD-001` through `DOD-023` remain stable. New rules `DOD-024` through `DOD-033` extend the quality gate without renumbering existing rules.
