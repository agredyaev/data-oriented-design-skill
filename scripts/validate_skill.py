#!/usr/bin/env python3
"""Check skill structure, local navigation, rule registry, and reference reachability."""
import argparse
from collections import Counter
from pathlib import Path
import re
import unicodedata
from urllib.parse import unquote, urlsplit

SKILL_PATH = Path('skills/data-oriented-design')
REQUIRED = (
    'SKILL.md', 'references/workflow.md', 'references/modules.md',
    'references/dod-yagni-engineering-rules.md',
    'references/engineering/00-structural-analysis.md',
    'references/engineering/09-wide-pointerless-compiler.md',
    'references/performance-methodology.md',
)
# Limits keep the always-loaded router small and stop rule packs becoming routers.
LIMITS = {'SKILL.md': 6500, 'references/workflow.md': 10000,
          'references/performance-methodology.md': 5000,
          'references/engineering/09-wide-pointerless-compiler.md': 5000}
GENERAL_DECISION_BLOCKS = (
    'references/engineering/01-data-shape.md',
    'references/engineering/02-canonical-and-derived.md',
    'references/engineering/03-hot-path-work.md',
    'references/engineering/04-ownership-and-concurrency.md',
    'references/engineering/05-yagni-and-cleanup.md',
    'references/engineering/07-measurement-and-review.md',
)


def prose(text):
    """Exclude examples inside fenced code from navigation checks."""
    lines = []
    fence = None
    for line in text.splitlines():
        marker = re.match(r'^\s*(`{3,}|~{3,})', line)
        if marker:
            token = marker.group(1)
            if fence is None:
                fence = token
            elif token[0] == fence[0] and len(token) >= len(fence):
                fence = None
            continue
        if fence is None:
            lines.append(line)
    return '\n'.join(lines), fence is not None


def anchors(text):
    result = set()
    seen = Counter()
    for title in re.findall(r'^#{1,6}\s+(.+?)\s*#*$', text, re.M):
        title = title.lower().replace('`', '')
        slug = ''.join(c for c in title if c in '-_ ' or
                       unicodedata.category(c)[0] in 'LN').replace(' ', '-')
        suffix = f'-{seen[slug]}' if seen[slug] else ''
        seen[slug] += 1
        result.add(slug + suffix)
    return result


def local_targets(text):
    # Relative inline Markdown links, including anchors.
    targets = re.findall(r'\]\(([^\s)]+)(?:\s+"[^"]*")?\)', text)
    # Routers also use literal file paths in table cells and sentences.
    for literal in re.findall(r'`([^`\n]+)`', text):
        if re.fullmatch(r'[\w./-]+\.md(?:#[\w-]+)?', literal):
            targets.append(literal)
    return sorted(set(targets))


def decision_sections(text):
    return re.findall(
        r'(^## Decision tree:[^\n]*\n[\s\S]*?)(?=^## |\Z)',
        text, re.M,
    )


def validate(repo):
    root = (repo / SKILL_PATH).resolve()
    errors = []
    for relative in REQUIRED:
        if not (root / relative).is_file():
            errors.append(f'Missing required file: {relative}')
    if not root.is_dir():
        return errors
    documents = {p.resolve(): p.read_text(encoding='utf-8')
                 for p in root.rglob('*.md')}
    entry = root / 'SKILL.md'
    if entry not in documents:
        return errors
    fm = re.match(r'^---\n(.*?)\n---(?:\n|$)', documents[entry], re.S)
    if not fm:
        errors.append('Missing YAML frontmatter')
    else:
        # This skill uses only two scalar keys; reject unexpected metadata.
        keys = re.findall(r'^([\w-]+):', fm.group(1), re.M)
        if Counter(keys) != Counter(['name', 'description']):
            errors.append('Frontmatter requires exactly name and description')
        if not re.search(r'^name: data-oriented-design$', fm.group(1), re.M):
            errors.append('Unexpected skill name')
        if not re.search(r'^description: \S.+', fm.group(1), re.M):
            errors.append('Missing nonempty description')
    for relative, limit in LIMITS.items():
        path = root / relative
        if path.is_file() and path.stat().st_size > limit:
            errors.append(f'File exceeds {limit} byte budget: {relative}')
    graph = {p: set() for p in documents}
    clean = {}
    for path, text in documents.items():
        clean[path], unbalanced = prose(text)
        if unbalanced:
            errors.append(f'Unbalanced fenced code blocks: {path.relative_to(root)}')
    # Inspect README navigation too, but do not treat it as a skill entry point.
    readme = repo / 'README.md'
    sources = dict(clean)
    if readme.is_file():
        sources[readme.resolve()] = prose(readme.read_text(encoding='utf-8'))[0]
    for path, text in sources.items():
        for target in local_targets(text):
            parts = urlsplit(target)
            if parts.scheme or parts.netloc:
                continue
            dest = (path.parent / unquote(parts.path)).resolve() if parts.path else path
            if not dest.is_relative_to(root) and path in documents:
                errors.append(f'Route escapes skill: {path.relative_to(root)} -> {target}')
                continue
            if not dest.is_file():
                errors.append(f'Broken local route: {path.name} -> {target}')
                continue
            if parts.fragment and dest in clean and unquote(parts.fragment) not in anchors(clean[dest]):
                errors.append(f'Broken heading anchor: {path.name} -> {target}')
            if path in graph and dest in documents:
                graph[path].add(dest)
    reached = set()
    pending = [entry]
    while pending:
        current = pending.pop()
        if current not in reached:
            reached.add(current)
            pending.extend(graph.get(current, ()))
    for path in sorted(set(documents) - reached):
        errors.append(f'Unreachable reference from SKILL.md: {path.relative_to(root)}')
    packs = {p: text for p, text in documents.items()
             if p.parent == root / 'references/performance'}
    content = '\n'.join(packs.values())
    expected = {f'DOD-{i:03d}' for i in range(1, 34)}
    for label, pattern in (
        ('definition', r'^### (DOD-\d{3}) — '),
        ('decision tree', r'^### (DOD-\d{3}) decision tree$'),
    ):
        counts = Counter(re.findall(pattern, content, re.M))
        for rule in sorted(expected | counts.keys()):
            if counts[rule] != (1 if rule in expected else 0):
                errors.append(f'{rule}: expected {1 if rule in expected else 0} {label}, found {counts[rule]}')
    # A registry heading alone does not preserve the methodology: each rule
    # needs an actionable body and a nonempty decision tree.
    definitions = re.findall(
        r'^### (DOD-\d{3}) — [^\n]+\n([\s\S]*?)(?=^### |^## |\Z)',
        content, re.M,
    )
    for rule, body in definitions:
        for field in ('Symptom', 'Action', 'Check', 'Example'):
            if not re.search(r'\*\*' + field + r':\*\*[ \t]+\S', body):
                errors.append(f'{rule}: missing nonempty {field} field')
    trees = re.findall(
        r'^### (DOD-\d{3}) decision tree\n([\s\S]*?)(?=^### |^## |\Z)',
        content, re.M,
    )
    for rule, body in trees:
        fenced = re.search(r'^```[^\n]*\n(.*?)^```', body, re.M | re.S)
        if not fenced or not fenced.group(1).strip():
            errors.append(f'{rule}: missing nonempty decision tree body')
    for path, text in documents.items():
        for rule in sorted(set(re.findall(r'\bDOD-\d{3}\b', text)) - expected):
            errors.append(f'Unknown rule ID in {path.relative_to(root)}: {rule}')
    router = documents[entry]
    if re.search(r'^\d+\. ', router, re.M):
        errors.append('SKILL.md must route to the workflow, not duplicate its numbered sequence')
    if 'Start with at most three references' not in router:
        errors.append('Missing initial reference loading cap')
    trusted_row = next(
        (line for line in router.splitlines()
         if 'Trusted profiler hotspot or supplied measured cause' in line),
        '',
    )
    if not trusted_row:
        errors.append('Missing trusted-profile direct route')
    elif 'performance/00-diagnosis.md' in trusted_row:
        errors.append('Trusted profiler route must not force Diagnosis')
    modules_path = root / 'references/modules.md'
    if modules_path in documents:
        modules = documents[modules_path]
        if 'broad compiler/frontend redesign' not in modules:
            errors.append('Module routes must include broad compiler/frontend redesign')
        if 'trusted profile or supplied measured cause' not in modules:
            errors.append('Module routes must include trusted-profile direct routing')
    measurement = root / 'references/performance/01-measurement.md'
    if measurement in documents and re.search(
        r'^## Language rules$', documents[measurement], re.M
    ):
        errors.append('Performance measurement must not contain output-style language rules')
    for relative in GENERAL_DECISION_BLOCKS:
        path = root / relative
        if path not in documents:
            continue
        sections = decision_sections(documents[path])
        if not sections:
            errors.append(f'General engineering block has no decision trees: {relative}')
            continue
        for section in sections:
            title = section.splitlines()[0]
            body = re.search(r'^\x60\x60\x60[^\n]*\n(.*?)^\x60\x60\x60', section, re.M | re.S)
            if not body or not body.group(1).strip():
                errors.append(f'General decision tree is empty: {relative}: {title}')
            if not re.search(r'^### Example:', section, re.M):
                errors.append(f'General decision tree lacks a worked example: {relative}: {title}')
    structural = root / 'references/engineering/00-structural-analysis.md'
    if structural in documents and re.search(r'^## (?:\d+\.|Required output)', documents[structural], re.M):
        errors.append('Structural analysis must provide techniques, not a second workflow/report')
    compiler_router = root / 'references/engineering/09-wide-pointerless-compiler.md'
    if compiler_router in graph:
        blocks = {p for p in graph[compiler_router] if p.parent == root / 'references/engineering/compiler'}
        required_blocks = {root / 'references/engineering/compiler' / name for name in (
            '10-pipeline-elimination.md', '20-wide-frontend.md',
            '30-pointerless-state.md', '40-validation.md',
        )}
        if not required_blocks.issubset(blocks):
            errors.append('Compiler router must reach its core blocks')
        for block in blocks:
            if documents[block].count('## Decision tree') != 1:
                errors.append(f'Compiler block requires one primary decision tree: {block.name}')
    profile_dir = root / 'references/engineering/compiler/profile'
    for block in sorted(profile_dir.glob('*.md')):
        text = documents[block.resolve()]
        decisions = re.split(r'(?=^## Decision tree:)', text, flags=re.M)[1:]
        if not decisions:
            errors.append(f'Decision block has no decision trees: {block.name}')
        for decision in decisions:
            title = decision.splitlines()[0]
            body = re.search(r'^```[^\n]*\n(.*?)^```', decision, re.M | re.S)
            if not body or not body.group(1).strip():
                errors.append(f'Decision block has empty tree: {block.name}: {title}')
            if not re.search(r'^### Example:', decision, re.M):
                errors.append(f'Decision tree lacks a worked example: {block.name}: {title}')
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo-root', type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    errors = validate(args.repo_root.resolve())
    if errors:
        print('Skill validation failed:')
        print('\n'.join(f'- {error}' for error in errors))
        return 1
    print('Skill validation passed: local routes/anchors, reachable references, 33 definitions and decision trees, router budgets.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
