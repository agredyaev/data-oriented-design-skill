#!/usr/bin/env python3
"""Mutation checks for the failures the skill navigation validator must catch."""
from pathlib import Path
import shutil
import tempfile
import unittest

from validate_skill import SKILL_PATH, validate

REPO = Path(__file__).resolve().parents[1]


class ValidateSkillTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.repo = Path(self.temp.name)
        shutil.copytree(REPO / SKILL_PATH, self.repo / SKILL_PATH)
        shutil.copy2(REPO / 'README.md', self.repo / 'README.md')
        self.skill = self.repo / SKILL_PATH

    def append(self, relative, value):
        path = self.skill / relative
        path.write_text(path.read_text() + '\n' + value + '\n')

    def assert_invalid(self, message):
        errors = validate(self.repo)
        self.assertTrue(any(message in error for error in errors), errors)

    def test_current_skill(self):
        self.assertEqual(validate(self.repo), [])

    def test_missing_dod_definition(self):
        path = self.skill / 'SKILL.md'
        path.write_text(path.read_text().replace('**DOD (Data-Oriented Design):**',
                                                '**Unexplained acronym:**', 1))
        self.assert_invalid('Primary DOD/PWP definitions, preflight and structural override')

    def test_missing_pwp_definition(self):
        path = self.skill / 'SKILL.md'
        path.write_text(path.read_text().replace('**PWP (Programming Without Pointers):**',
                                                '**Unexplained acronym:**', 1))
        self.assert_invalid('Primary DOD/PWP definitions, preflight and structural override')

    def test_c4_first_reference(self):
        path = self.skill / 'SKILL.md'
        path.write_text(path.read_text().replace('**C4 procedure first**', 'optional C4', 1))
        self.assert_invalid('C4 must be first within reference loading cap')

    def test_c4_coverage_gate(self):
        path = self.skill / 'references/engineering/00-structural-analysis.md'
        path.write_text(path.read_text().replace('### C4 coverage gate', '### Informal review', 1))
        self.assert_invalid('Missing mandatory C4 definition: ### C4 coverage gate')

    def test_affected_candidate_must_override_focused_route(self):
        path = self.skill / 'references/modules.md'
        path.write_text(path.read_text().replace('If C4 flags structural candidates on the affected path', 'If preferred', 1))
        self.assert_invalid('Affected-path structural candidates must override focused routing')

    def test_to_be_c4_required(self):
        path = self.skill / 'references/workflow.md'
        path.write_text(path.read_text().replace('to-be C4 L2/L3', 'revised diagram'))
        self.assert_invalid('Structural redesign must include to-be C4')

    def test_missing_c4_gate(self):
        path = self.skill / 'SKILL.md'
        path.write_text(path.read_text().replace('**Gate 0 — draw as-is C4', '**Optional C4', 1))
        self.assert_invalid('Mandatory C4 Gate 0')

    def test_missing_c4_level(self):
        path = self.skill / 'references/engineering/00-structural-analysis.md'
        path.write_text(path.read_text().replace('**L3', '**Part of system', 1))
        self.assert_invalid('Missing mandatory C4 definition: **L3')

    def test_workflow_skips_c4(self):
        path = self.skill / 'references/workflow.md'
        path.write_text(path.read_text().replace('## 2. Draw the as-is C4 system and current process/data',
                                                '## 2. Draw affected process', 1))
        self.assert_invalid('Workflow step 2 must draw C4')

    def test_module_skips_c4(self):
        path = self.skill / 'references/modules.md'
        path.write_text(path.read_text().replace('Before selecting any module for repository-code work',
                                                'Optional for module work', 1))
        self.assert_invalid('C4 must precede focused module routing')

    def test_missing_mandatory_preflight(self):
        path = self.skill / 'SKILL.md'
        path.write_text(path.read_text().replace('## Mandatory DOD preflight',
                                                '## Optional design advice', 1))
        self.assert_invalid('Primary DOD/PWP definitions, preflight and structural override')

    def test_missing_structural_override(self):
        path = self.skill / 'SKILL.md'
        path.write_text(path.read_text().replace('### Structural-route override',
                                                '### Local cleanup', 1))
        self.assert_invalid('Primary DOD/PWP definitions, preflight and structural override')

    def test_yagni_precedes_structural_route(self):
        path = self.skill / 'SKILL.md'
        text = path.read_text()
        first = text.index('| Architecture redesign or structural cleanup with OOP/layer signals |')
        last = text.index('| Local YAGNI cleanup **only after structural override check** |')
        lines = text.splitlines(keepends=True)
        first_idx = next(i for i, line in enumerate(lines) if line.startswith('| Architecture redesign or structural cleanup with OOP/layer signals |'))
        last_idx = next(i for i, line in enumerate(lines) if line.startswith('| Local YAGNI cleanup **only after structural override check** |'))
        lines[first_idx], lines[last_idx] = lines[last_idx], lines[first_idx]
        path.write_text(''.join(lines))
        self.assert_invalid('Structural DOD route must precede local YAGNI')

    def test_physical_step_removed(self):
        path = self.skill / 'references/workflow.md'
        path.write_text(path.read_text().replace('## 3. Derive the physical operation shape',
                                                '## 3. Skip data analysis', 1))
        self.assert_invalid('Workflow must derive physical operation shape')

    def test_broken_nested_markdown_link(self):
        self.append('references/engineering/09-wide-pointerless-compiler.md',
                    '[wrong](../../performance/00-diagnosis.md)')
        self.assert_invalid('Broken local route')

    def test_broken_literal_route(self):
        self.append('references/modules.md', '`engineering/missing.md`')
        self.assert_invalid('Broken local route')

    def test_invalid_anchor(self):
        self.append('references/modules.md', '[step](workflow.md#missing-step)')
        self.assert_invalid('Broken heading anchor')

    def test_orphan_reference(self):
        (self.skill / 'references/orphan.md').write_text('# Orphan\n')
        self.assert_invalid('Unreachable reference')

    def test_missing_definition(self):
        path = self.skill / 'references/performance/10-foundation.md'
        path.write_text(path.read_text().replace('### DOD-001 — ', '### Removed — '))
        self.assert_invalid('DOD-001: expected 1 definition, found 0')

    def test_duplicate_tree(self):
        self.append('references/performance/10-foundation.md', '### DOD-001 decision tree')
        self.assert_invalid('DOD-001: expected 1 decision tree, found 2')

    def test_rule_action_cannot_disappear(self):
        path = self.skill / 'references/performance/10-foundation.md'
        path.write_text(path.read_text().replace('- **Action:**', '- **Removed:**', 1))
        self.assert_invalid('DOD-001: missing nonempty Action field')

    def test_empty_rule_action(self):
        path = self.skill / 'references/performance/10-foundation.md'
        text = path.read_text()
        start = text.index('- **Action:**')
        end = text.index('\n', start)
        path.write_text(text[:start] + '- **Action:**' + text[end:])
        self.assert_invalid('DOD-001: missing nonempty Action field')

    def test_empty_tree_cannot_pass_on_heading_alone(self):
        path = self.skill / 'references/performance/10-foundation.md'
        text = path.read_text()
        start = text.index('```text') + len('```text\n')
        end = text.index('```', start)
        path.write_text(text[:start] + text[end:])
        self.assert_invalid('DOD-001: missing nonempty decision tree body')

    def test_profile_tree_requires_a_worked_example(self):
        path = self.skill / 'references/engineering/compiler/profile/10-batch-and-classification.md'
        path.write_text(path.read_text().replace('### Example:', '### Illustration:', 1))
        self.assert_invalid('Decision tree lacks a worked example')

    def test_profile_requires_decision_trees(self):
        path = self.skill / 'references/engineering/compiler/profile/10-batch-and-classification.md'
        path.write_text(path.read_text().replace('## Decision tree:', '## General advice:'))
        self.assert_invalid('Decision block has no decision trees')

    def test_profile_tree_cannot_be_empty(self):
        path = self.skill / 'references/engineering/compiler/profile/10-batch-and-classification.md'
        text = path.read_text()
        start = text.index('```text') + len('```text\n')
        end = text.index('```', start)
        path.write_text(text[:start] + text[end:])
        self.assert_invalid('Decision block has empty tree')

    def test_external_links_and_fenced_examples_are_not_local_routes(self):
        self.append('references/modules.md', '[docs](https://example.org/manual.md)\n'
                    '```text\n[illustration](nonexistent.md)\n`also-not-a-route.md`\n```')
        self.assertEqual(validate(self.repo), [])

    def test_route_escape(self):
        self.append('references/modules.md', '[outside](../../../README.md)')
        self.assert_invalid('Route escapes skill')

    def test_unbalanced_fence(self):
        self.append('references/modules.md', '```text\nunfinished')
        self.assert_invalid('Unbalanced fenced code blocks')

    def test_missing_module_map(self):
        (self.skill / 'references/modules.md').unlink()
        self.assert_invalid('Missing required file: references/modules.md')


if __name__ == '__main__':
    unittest.main()
