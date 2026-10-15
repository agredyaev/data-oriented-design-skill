#!/usr/bin/env python3
from pathlib import Path
import re
import sys

ROOT = Path("skills/data-oriented-design")
SKILL = ROOT / "SKILL.md"
WORKFLOW = ROOT / "references/workflow.md"
PERFORMANCE_ROUTER = ROOT / "references/performance-methodology.md"
PERFORMANCE_DIR = ROOT / "references/performance"
ENGINEERING_ROUTER = ROOT / "references/dod-yagni-engineering-rules.md"
STRUCTURAL = ROOT / "references/engineering/00-structural-analysis.md"
COMPILER_MODULE = ROOT / "references/engineering/09-wide-pointerless-compiler.md"
COMPILER_DIR = ROOT / "references/engineering/compiler"
COMPILER_PIPELINE = COMPILER_DIR / "10-pipeline-elimination.md"
COMPILER_FRONTEND = COMPILER_DIR / "20-wide-frontend.md"
COMPILER_STATE = COMPILER_DIR / "30-pointerless-state.md"
COMPILER_VALIDATION = COMPILER_DIR / "40-validation.md"
README = Path("README.md")

errors = []

required_files = [
    SKILL,
    WORKFLOW,
    PERFORMANCE_ROUTER,
    ENGINEERING_ROUTER,
    STRUCTURAL,
    COMPILER_MODULE,
    COMPILER_PIPELINE,
    COMPILER_FRONTEND,
    COMPILER_STATE,
    COMPILER_VALIDATION,
    PERFORMANCE_DIR / "00-diagnosis.md",
    PERFORMANCE_DIR / "01-measurement.md",
    PERFORMANCE_DIR / "10-foundation.md",
    PERFORMANCE_DIR / "20-identity-and-relations.md",
    PERFORMANCE_DIR / "21-layout-and-encoding.md",
    PERFORMANCE_DIR / "30-work-and-access.md",
    PERFORMANCE_DIR / "40-concurrency.md",
    README,
]
for path in required_files:
    if not path.is_file():
        errors.append(f"Missing required file: {path}")

if errors:
    print("Skill validation failed:")
    for error in errors:
        print(f"- {error}")
    sys.exit(1)

skill = SKILL.read_text(encoding="utf-8")
workflow = WORKFLOW.read_text(encoding="utf-8")
performance_router = PERFORMANCE_ROUTER.read_text(encoding="utf-8")
structural = STRUCTURAL.read_text(encoding="utf-8")
compiler_module = COMPILER_MODULE.read_text(encoding="utf-8")
compiler_pipeline = COMPILER_PIPELINE.read_text(encoding="utf-8")
compiler_frontend = COMPILER_FRONTEND.read_text(encoding="utf-8")
compiler_state = COMPILER_STATE.read_text(encoding="utf-8")
compiler_validation = COMPILER_VALIDATION.read_text(encoding="utf-8")
readme = README.read_text(encoding="utf-8")

# Router must remain small and selective.
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
    "## Choose the task mode",
    "## Engineering routing",
    "## Performance routing",
    "## Primary top-down algorithm",
    "## Non-negotiable rules",
    "## Completion",
]:
    if section not in skill:
        errors.append(f"SKILL router missing section: {section}")

if SKILL.stat().st_size > 6500:
    errors.append(f"SKILL router is too large: {SKILL.stat().st_size} bytes")
if PERFORMANCE_ROUTER.stat().st_size > 5000:
    errors.append(
        f"Performance router is too large: {PERFORMANCE_ROUTER.stat().st_size} bytes"
    )
if "Start with at most three references" not in skill:
    errors.append("SKILL router does not cap initial reference loading")
if "for every task" in skill.lower():
    errors.append("SKILL router contains a blanket load-for-every-task rule")
if re.search(r"^### DOD-\d{3}", performance_router, re.M):
    errors.append("Performance router contains detailed DOD rules instead of routing")

# Workflow must remain executable rather than bureaucratic.
for phrase in [
    "## 1. Fix the contract",
    "## 2. Draw the current process and data",
    "## 3. Apply the element-necessity test",
    "## 4. Design the replacement from the contract",
    "## 5. Compare current and candidate",
    "## 6. Implement one structural decision at a time",
    "## 7. Verify proportionally",
    "every added element has a concrete responsibility",
]:
    if phrase not in workflow:
        errors.append(f"Workflow missing executable rule: {phrase}")

if WORKFLOW.stat().st_size > 9000:
    errors.append(f"Workflow is too large: {WORKFLOW.stat().st_size} bytes")
if "Required output:" in workflow:
    errors.append("Workflow contains per-phase Required output bureaucracy")
if re.search(r"^## Phase \d", workflow, re.M):
    errors.append("Workflow reverted to phase-heavy structure")
for decision in ["KEEP", "REMOVE", "MERGE", "DERIVE", "LOCALIZE", "FLATTEN", "BATCH", "MEASURE"]:
    if decision not in workflow:
        errors.append(f"Element-necessity decision is missing: {decision}")

# All directly routed files must exist.
skill_links = re.findall(r"\((references/[^)]+\.md)\)", skill)
for target in skill_links:
    if not (ROOT / target).is_file():
        errors.append(f"SKILL routed file does not exist: {target}")

perf_links = re.findall(r"\((performance/[^)]+\.md)\)", performance_router)
for target in perf_links:
    if not (ROOT / "references" / target).is_file():
        errors.append(f"Performance routed file does not exist: {target}")

# DOD-001..033 must exist exactly once as a decision tree and once as a definition
# across routed packs.
rule_pack_paths = sorted(PERFORMANCE_DIR.glob("*.md"))
performance_content = "\n".join(p.read_text(encoding="utf-8") for p in rule_pack_paths)
expected = [f"DOD-{i:03d}" for i in range(1, 34)]
definitions = re.findall(r"^### (DOD-\d{3}) — ", performance_content, re.M)
trees = re.findall(r"^### (DOD-\d{3}) decision tree$", performance_content, re.M)

for label, actual in [("definition", definitions), ("decision tree", trees)]:
    for rule_id in expected:
        count = actual.count(rule_id)
        if count != 1:
            errors.append(f"{rule_id}: expected exactly one {label}, found {count}")
    extras = sorted(set(actual) - set(expected))
    if extras:
        errors.append(f"Unexpected {label} IDs: {', '.join(extras)}")

# Preserve the performance methodology sections from main.
diagnosis = (PERFORMANCE_DIR / "00-diagnosis.md").read_text(encoding="utf-8")
measurement = (PERFORMANCE_DIR / "01-measurement.md").read_text(encoding="utf-8")
foundation = (PERFORMANCE_DIR / "10-foundation.md").read_text(encoding="utf-8")
methodology_text = diagnosis + "\n" + measurement + "\n" + foundation
for section in [
    "## Language rules",
    "## Core model",
    "## Run one performance experiment",
    "## Global decision tree",
    "## Transformation map",
    "## Layout choices",
    "## Access-order choices",
    "## Reads, writes, and lifetime",
    "## Concurrency gate",
    "## Measurement rules",
    "## Falsifiable hypothesis",
    "## Result classes",
    "## Code signatures",
    "## Quality gate for this skill's output",
]:
    if section not in methodology_text:
        errors.append(f"Performance methodology missing section: {section}")

for pattern in [
    r"\breused enough\b",
    r"\bsparse enough\b",
    r"\brare enough\b",
    r"\bmuch smaller\b",
    r"\bmost consumers\b",
    r"\bbest measured\b",
]:
    if re.search(pattern, performance_content, re.I):
        errors.append(f"Vague decision-tree predicate found: {pattern}")

if "Repeated string/value storage -> DOD-022" in performance_content:
    errors.append("DOD-022 must not route non-string canonical values")

gstart = diagnosis.find("## Global decision tree")
gend = diagnosis.find("## Transformation map")
global_tree = diagnosis[gstart:gend] if gstart >= 0 and gend > gstart else ""
for term in ["CORE", "FRONT END", "BRANCH", "I/O"]:
    if term not in global_tree:
        errors.append(f"Global decision tree does not route bottleneck class: {term}")

# Structural route must be top-down and typed.
for phrase in [
    "State the exact contract",
    "Build the current process map with data types",
    "Build the current retained-data map",
    "Count the current process",
    "Identify removable work and state",
    "Design the new process from the contract",
    "Design the new retained representation",
    "Compare current and candidate structurally",
    "Only now select detailed rules",
]:
    if phrase not in structural:
        errors.append(f"Structural analysis missing section: {phrase}")

# Compiler methodology must stay routed, modular, and selective.
if "references/engineering/09-wide-pointerless-compiler.md" not in skill:
    errors.append("Compiler router is not routed from SKILL.md")
if "engineering/09-wide-pointerless-compiler.md" not in ENGINEERING_ROUTER.read_text(encoding="utf-8"):
    errors.append("Compiler router is not routed from engineering router")
if "09-wide-pointerless-compiler.md" not in readme:
    errors.append("README does not document compiler router")

if COMPILER_MODULE.stat().st_size > 5000:
    errors.append(f"Compiler router is too large: {COMPILER_MODULE.stat().st_size} bytes")

compiler_router_links = re.findall(r"\((compiler/[^)]+\.md)\)", compiler_module)
expected_compiler_links = {
    "compiler/10-pipeline-elimination.md",
    "compiler/20-wide-frontend.md",
    "compiler/30-pointerless-state.md",
    "compiler/40-validation.md",
}
if set(compiler_router_links) != expected_compiler_links:
    errors.append(
        "Compiler router links do not match the four focused blocks: "
        + ", ".join(sorted(set(compiler_router_links)))
    )
for target in compiler_router_links:
    if not (ROOT / "references/engineering" / target).is_file():
        errors.append(f"Compiler routed file does not exist: {target}")

compiler_blocks = {
    "pipeline": compiler_pipeline,
    "frontend": compiler_frontend,
    "state": compiler_state,
    "validation": compiler_validation,
}
for name, text in compiler_blocks.items():
    path = {
        "pipeline": COMPILER_PIPELINE,
        "frontend": COMPILER_FRONTEND,
        "state": COMPILER_STATE,
        "validation": COMPILER_VALIDATION,
    }[name]
    if path.stat().st_size > 7500:
        errors.append(f"Compiler block is too large: {path} ({path.stat().st_size} bytes)")
    if "## Decision tree" not in text:
        errors.append(f"Compiler block lacks one primary decision tree: {path}")
    if text.count("## Decision tree") != 1:
        errors.append(f"Compiler block must have exactly one primary decision tree: {path}")

for phrase in [
    "## Choose one primary block",
    "Start with one block",
    "## Decision language",
    "choose `MEASURE`",
    "Do not use a lower-level block to justify a higher-level stage",
]:
    if phrase not in compiler_module:
        errors.append(f"Compiler router missing cognitive-load rule: {phrase}")

compiler_combined = "\n".join(
    [compiler_pipeline, compiler_frontend, compiler_state, compiler_validation]
)
for phrase in [
    "remove stage",
    "Does R add information required downstream?",
    "wide classification",
    "start_mask",
    "batch/SWAR/vector compaction",
    "tags[]",
    "extents[]",
    "token_ix",
    "byte_cursor",
    "typed ID",
    "offsets[]",
    "string_bytes[]",
    "builder",
    "frozen",
    "hot from cold",
    "benchmark-only",
    "semantic outputs",
    "Fail closed",
    "falsifiable prediction",
]:
    if phrase not in compiler_combined:
        errors.append(f"Compiler methodology coverage missing: {phrase}")

for pattern in [
    r"\bmaterially\b",
    r"\bwhen justified\b",
    r"\bcheaper\b",
    r"\blarge enough\b",
    r"\bworth it\b",
    r"\bbest measured\b",
]:
    if re.search(pattern, compiler_combined, re.I):
        errors.append(f"Vague compiler decision predicate found: {pattern}")

for forbidden in [
    "MeshIR",
    "MeshSema",
    "CanonicalMesh",
    "model_ranges[]",
    "model_roots[]",
    "Duck Mesh",
    "821 ms",
    "3.6×",
]:
    if forbidden in compiler_module or forbidden in compiler_combined:
        errors.append(f"Compiler methodology contains project-specific detail: {forbidden}")

# Markdown fences must remain balanced.
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
print(f"SKILL router bytes: {SKILL.stat().st_size}")
print(f"Workflow bytes: {WORKFLOW.stat().st_size}")
print(f"Performance router bytes: {PERFORMANCE_ROUTER.stat().st_size}")
print("Initial reference cap: 3")
