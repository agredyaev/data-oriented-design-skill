#!/usr/bin/env python3
from pathlib import Path
import re
import sys

SKILL = Path("skills/data-oriented-design/SKILL.md")
README = Path("README.md")

text = SKILL.read_text(encoding="utf-8")
readme = README.read_text(encoding="utf-8")
errors = []

expected = [f"DOD-{i:03d}" for i in range(1, 34)]
definitions = re.findall(r"^### (DOD-\d{3}) — ", text, re.M)
trees = re.findall(r"^### (DOD-\d{3}) decision tree$", text, re.M)

for label, actual in [("definition", definitions), ("decision tree", trees)]:
    for rule_id in expected:
        count = actual.count(rule_id)
        if count != 1:
            errors.append(f"{rule_id}: expected exactly one {label}, found {count}")
    extras = sorted(set(actual) - set(expected))
    if extras:
        errors.append(f"Unexpected {label} IDs: {', '.join(extras)}")

if len(re.findall(r"^```", text, re.M)) % 2:
    errors.append("Unbalanced fenced code blocks")

required_sections = [
    "## Language rules",
    "## Core model",
    "## Global decision tree",
    "## Transformation map",
    "## Decision trees for every rule",
    "## Diagnose the work",
    "## Prove and report",
    "## Quality gate for this skill's output",
]
for section in required_sections:
    if section not in text:
        errors.append(f"Missing required section: {section}")

frontmatter = re.match(r"^---\n(.*?)\n---", text, re.S)
if not frontmatter:
    errors.append("Missing YAML frontmatter")
else:
    fm = frontmatter.group(1)
    if "name: data-oriented-design" not in fm:
        errors.append("Unexpected skill name")
    for term in ["CPU", "memory", "wall-clock", "access order", "ownership"]:
        if term.lower() not in fm.lower():
            errors.append(f"Frontmatter description does not cover: {term}")

tree_start = text.find("## Decision trees for every rule")
tree_end = text.find("## Diagnose the work")
if tree_start == -1 or tree_end == -1 or tree_end <= tree_start:
    errors.append("Cannot locate the decision-tree block")
else:
    tree_text = text[tree_start:tree_end]
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

if "Repeated string/value storage -> DOD-022" in text:
    errors.append("DOD-022 must not route non-string canonical values")

gstart = text.find("## Global decision tree")
gend = text.find("## Transformation map")
global_tree = text[gstart:gend] if gstart >= 0 and gend > gstart else ''
for term in ["CORE", "FRONT END", "BRANCH", "I/O"]:
    if term not in global_tree:
        errors.append(f"Global decision tree does not route bottleneck class: {term}")

if "DOD-033" not in readme:
    errors.append("README does not document DOD-033")
if "DOD-023` remain stable" not in readme:
    errors.append("README does not preserve the original stable-ID contract")

if errors:
    print("Skill validation failed:")
    for error in errors:
        print(f"- {error}")
    sys.exit(1)

print("Skill validation passed.")
print(f"Definitions: {len(definitions)}")
print(f"Decision trees: {len(trees)}")
