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


    def test_trusted_profiler_route_cannot_force_diagnosis(self):
        path = self.skill / 'SKILL.md'
        text = path.read_text()
        line = next(line for line in text.splitlines()
                    if 'Trusted profiler hotspot or supplied measured cause' in line)
        changed = line.replace(
            '[performance methodology](references/performance-methodology.md)',
            '[performance diagnosis](references/performance/00-diagnosis.md)',
        )
        path.write_text(text.replace(line, changed))
        self.assert_invalid('Trusted profiler route must not force Diagnosis')

    def test_general_engineering_block_requires_decision_tree(self):
        path = self.skill / 'references/engineering/04-ownership-and-concurrency.md'
        path.write_text(path.read_text().replace('## Decision tree:', '## Advice:'))
        self.assert_invalid('General engineering block has no decision trees')

    def test_general_decision_tree_requires_example(self):
        path = self.skill / 'references/engineering/03-hot-path-work.md'
        path.write_text(path.read_text().replace('### Example:', '### Illustration:', 1))
        self.assert_invalid('General decision tree lacks a worked example')

    def test_measurement_block_rejects_output_style_policy(self):
        path = self.skill / 'references/performance/01-measurement.md'
        path.write_text(path.read_text() + '\n## Language rules\n- Use passive voice.\n')
        self.assert_invalid('Performance measurement must not contain output-style language rules')

    def test_module_routes_require_compiler_redesign_entry(self):
        path = self.skill / 'references/modules.md'
        path.write_text(path.read_text().replace(
            'broad compiler/frontend redesign', 'compiler work', 1))
        self.assert_invalid('Module routes must include broad compiler/frontend redesign')


    def test_correctness_block_requires_decision_trees(self):
        path = self.skill / 'references/engineering/06-correctness-boundaries.md'
        path.write_text(path.read_text().replace('## Decision tree:', '## Advice:'))
        self.assert_invalid('General engineering block has no decision trees')

    def test_general_block_requires_concrete_code_example(self):
        path = self.skill / 'references/engineering/04-ownership-and-concurrency.md'
        text = path.read_text()
        path.write_text(text.replace('rust', 'text'))
        self.assert_invalid('General engineering block lacks a concrete code example')

    def test_compiler_redesign_does_not_force_structural_first(self):
        path = self.skill / 'references/engineering/09-wide-pointerless-compiler.md'
        text = path.read_text()
        old = '1. use the typed contract/process/data map required by the workflow;'
        new = '1. read [Structural analysis](00-structural-analysis.md);'
        path.write_text(text.replace(old, new))
        self.assert_invalid('Broad compiler route must not force Structural analysis before Pipeline elimination')

    def test_repeated_pass_signature_routes_to_dod_024(self):
        path = self.skill / 'references/performance/00-diagnosis.md'
        text = path.read_text()
        path.write_text(text.replace(
            '| Several full passes use the same data | Fuse, split, or block the passes when semantics allow | DOD-024, DOD-025 |',
            '| Several full passes use the same data | Fuse or block the passes when semantics allow | DOD-003, DOD-010 |',
        ))
        self.assert_invalid('Repeated-pass code signature must route to DOD-024')


    def test_pwp_retained_state_requires_code_example(self):
        path = self.skill / 'references/engineering/compiler/profile/50-pwp-retained-state.md'
        path.write_text(path.read_text().replace('rust', 'text'))
        self.assert_invalid('PWP retained-state block requires a concrete Rust code example')


    def test_broad_redesign_route_is_dedicated(self):
        path = self.skill / 'SKILL.md'
        text = path.read_text()
        line = next(line for line in text.splitlines()
                    if 'Broad repo/module redesign or OOP cleanup' in line)
        path.write_text(text.replace(
            line,
            line.replace('[broad redesign](references/broad-redesign.md)',
                         '[workflow](references/workflow.md)'),
        ))
        self.assert_invalid('Broad repo redesign must start from the dedicated broad-redesign route')

    def test_broad_redesign_requires_anti_slop_gate(self):
        path = self.skill / 'references/broad-redesign.md'
        path.write_text(path.read_text().replace(
            '## Stage 5 — Anti-slop gate before coding',
            '## Stage 5 — Candidate review',
        ))
        self.assert_invalid('Broad redesign missing executable gate')

    def test_broad_redesign_rejects_shadow_architecture(self):
        path = self.skill / 'references/broad-redesign.md'
        path.write_text(path.read_text().replace(
            'Do not create a shadow architecture beside the old one.',
            'A shadow architecture is acceptable during migration.',
        ))
        self.assert_invalid('Broad redesign missing anti-slop invariant')

    def test_broad_redesign_requires_pwp_gate(self):
        path = self.skill / 'references/broad-redesign.md'
        path.write_text(path.read_text().replace(
            'engineering/compiler/profile/50-pwp-retained-state.md',
            'engineering/01-data-shape.md',
        ))
        self.assert_invalid('Broad redesign must integrate the PWP retained-state gate')

    def test_broad_redesign_requires_conditional_512_gate(self):
        path = self.skill / 'references/broad-redesign.md'
        path.write_text(path.read_text().replace(
            '512 is a specialized wide-frontend technique, not a general DOD target.',
            '512 is the default batching target.',
        ))
        self.assert_invalid('Broad redesign missing anti-slop invariant')


    def test_general_simd_requires_dense_id_route(self):
        path = self.skill / 'references/engineering/10-simd-and-dense-processing.md'
        text = path.read_text()
        path.write_text(text.replace('## Dense-ID → SIMD route', '## SIMD notes'))
        self.assert_invalid('General SIMD block missing dense-ID to SIMD route')

    def test_general_simd_rejects_sparse_external_id_array(self):
        path = self.skill / 'references/engineering/10-simd-and-dense-processing.md'
        text = path.read_text()
        path.write_text(text.replace(
            'Do not allocate an array by max external ID.',
            'External integer IDs can directly size arrays.',
        ))
        self.assert_invalid('General SIMD block missing invariant')

    def test_general_simd_keeps_scalar_reference(self):
        path = self.skill / 'references/engineering/10-simd-and-dense-processing.md'
        text = path.read_text()
        path.write_text(text.replace(
            'Keep the scalar semantics/reference available',
            'Delete scalar semantics after vectorization',
        ))
        self.assert_invalid('General SIMD block missing invariant')

    def test_general_simd_requires_five_trees(self):
        path = self.skill / 'references/engineering/10-simd-and-dense-processing.md'
        text = path.read_text()
        path.write_text(text.replace(
            '## Decision tree: gather/scatter or change the data flow',
            '## Gather/scatter notes',
        ))
        self.assert_invalid('General SIMD block requires five executable decision trees')

if __name__ == '__main__':
    unittest.main()
