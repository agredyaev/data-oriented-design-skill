#!/usr/bin/env python3
from pathlib import Path
import re
import sys

ROOT = Path("skills/data-oriented-design")
SKILL = ROOT / "SKILL.md"
PERFORMANCE = ROOT / "references/performance-methodology.md"
WORKFLOW = ROOT / "references/workflow.md"
ENGINEERING_ROUTER = ROOT / "references/dod-yagni-engineering-rules.md"
README = Path("README.md")

errors = []

for path in [SKILL, PERFORMANCE, WORKFLOW, ENGINEERING_ROUTER, README]:
    if not path.is_file():
        errors.append(f"Missing required file: {path}")

if errors:
    print("Skill validation failed:")
    for error in errors:
        print(f"- {error}")
    sys.exit(1)

skill = SKILL.read_text(encoding="utf-8")
performance = PERFORMANCE.read_text(encoding="utf-8")
workflow = WORKFLOW.read_text(encoding="utf-8")
readme = README.read_text(encoding="utf-8")

frontmatter = re.match(r"^---\n(.*?)\n---", skill, re.S)
if not frontmatter:
    errors.append("Missing YAML frontmatter")
else:
    fm = frontmatter.group(1)
    if "name: data-oriented-design" not in fm:
        errors.append("Unexpected skill name")
    for term in ["data layout", "memory", "hot paths", "ownership"]:
        if term.lower() not in fm.lower():
            errors.append(f"Frontmatter description does not cover: {term}")

for section in [
    "## Required load order",
    "## Routing",
    "## Non-negotiable rules",
    "## Required result",
]:
    if section not in skill:
        errors.append(f"SKILL router missing section: {section}")

required_paths = [
    "references/workflow.md",
    "references/dod-yagni-engineering-rules.md",
    "references/performance-methodology.md",
    "references/engineering/00-structural-analysis.md",
    "references/engineering/01-data-shape.md",
    "references/engineering/02-canonical-and-derived.md",
    "references/engineering/03-hot-path-work.md",
    "references/engineering/04-ownership-and-concurrency.md",
    "references/engineering/05-yagni-and-cleanup.md",
    "references/engineering/06-correctness-boundaries.md",
    "references/engineering/07-measurement-and-review.md",
    "references/engineering/08-examples.md",
]
for target in required_paths:
    if not (ROOT / target).is_file():
        errors.append(f"Routed file does not exist: {target}")

for target in [
    "references/workflow.md",
    "references/dod-yagni-engineering-rules.md",
    "references/performance-methodology.md",
    "references/engineering/00-structural-analysis.md",
]:
    if target not in skill:
        errors.append(f"SKILL router does not reference: {target}")

expected = [f"DOD-{i:03d}" for i in range(1, 34)]
definitions = re.findall(r"^### (DOD-\d{3}) — ", performance, re.M)
trees = re.findall(r"^### (DOD-\d{3}) decision tree$", performance, re.M)

for label, actual in [("definition", definitions), ("decision tree", trees)]:
    for rule_id in expected:
        count = actual.count(rule_id)
        if count != 1:
            errors.append(f"{rule_id}: expected exactly one {label}, found {count}")
    extras = sorted(set(actual) - set(expected))
    if extras:
        errors.append(f"Unexpected {label} IDs: {', '.join(extras)}")

required_performance_sections = [
    "## Language rules",
    "## Core model",
    "## Global decision tree",
    "## Transformation map",
    "## Decision trees for every rule",
    "## Diagnose the work",
    "## Prove and report",
    "## Quality gate for this skill's output",
]
for section in required_performance_sections:
    if section not in performance:
        errors.append(f"Performance methodology missing section: {section}")

tree_start = performance.find("## Decision trees for every rule")
tree_end = performance.find("## Diagnose the work")
if tree_start == -1 or tree_end == -1 or tree_end <= tree_start:
    errors.append("Cannot locate the decision-tree block")
else:
    tree_text = performance[tree_start:tree_end]
    for pattern in [
        r"\breused enough\b",
        r"\bsparse enough\b",
        r"\brare enough\b",
        r"\bmuch smaller\b",
        r"\bmost consumers\b",
        r"\bbest measured\b",
    ]:
        if re.search(pattern, tree_text, re.I):
            errors.append(f"Vague decision-tree predicate found: {pattern}")

if "Repeated string/value storage -> DOD-022" in performance:
    errors.append("DOD-022 must not route non-string canonical values")

gstart = performance.find("## Global decision tree")
gend = performance.find("## Transformation map")
global_tree = performance[gstart:gend] if gstart >= 0 and gend > gstart else ""
for term in ["CORE", "FRONT END", "BRANCH", "I/O"]:
    if term not in global_tree:
        errors.append(f"Global decision tree does not route bottleneck class: {term}")

for phrase in [
    "ASCII structural map",
    "Can this object disappear entirely?",
    "Can this stored field or projection be derived",
    "two consecutive local optimizations",
]:
    if phrase not in workflow:
        errors.append(f"Workflow missing structural requirement: {phrase}")

structural = (ROOT / "references/engineering/00-structural-analysis.md").read_text(encoding="utf-8")
for phrase in [
    "Draw the current state shape",
    "Draw the candidate flat shape",
    "Count allocation shape",
    "Challenge every retained field",
    "Challenge every relationship",
    "Escalate when local tuning fails",
]:
    if phrase not in structural:
        errors.append(f"Structural analysis missing section: {phrase}")

for path in ROOT.rglob("*.md"):
    md = path.read_text(encoding="utf-8")
    if len(re.findall(r"^\x60\x60\x60", md, re.M)) % 2:
        errors.append(f"Unbalanced fenced code blocks: {path}")

if "DOD-033" not in readme:
    errors.append("README does not document DOD-033")
if "DOD-023" not in readme or "remain stable" not in readme:
    errors.append("README does not preserve the original stable-ID contract")

if errors:
    print("Skill validation failed:")
    for error in errors:
        print(f"- {error}")
    sys.exit(1)

print("Skill validation passed.")
print(f"Definitions: {len(definitions)}")
print(f"Decision trees: {len(trees)}")
print("Router references: OK")
