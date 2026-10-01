import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

import yaml

from build_contract import documentation_only, required_checks_pass
from workflow_plan import requires_build

ROOT = Path(__file__).resolve().parent.parent


class UniqueKeyLoader(yaml.BaseLoader):
    def construct_mapping(self, node, deep=False):
        keys = [self.construct_object(key, deep=deep) for key, _ in node.value]
        if len(keys) != len(set(keys)):
            raise ValueError('Duplicate workflow mapping key')
        return super().construct_mapping(node, deep=deep)


class WorkflowPlanTests(unittest.TestCase):
    def test_only_the_two_root_documentation_files_skip_builds(self):
        self.assertTrue(documentation_only(['README.md', 'CHANGELOG.md']))
        self.assertTrue(documentation_only(['CHANGELOG.md']))
        for path in ['lib/main.dart', 'assets/image.png', 'pubspec.lock', 'pubspec.yaml',
                     'scripts/cloud_windows_build.py', '.github/workflows/windows.yml', 'AGENTS.md', 'lib/README.md']:
            with self.subTest(path=path):
                self.assertFalse(documentation_only(['README.md', path]))
        self.assertFalse(documentation_only([]))

    def test_real_git_diff_covers_multi_commit_docs_and_renames_into_code(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            def git(*args):
                return subprocess.check_output(['git', '-C', directory, *args], text=True).strip()
            git('init', '--initial-branch=fixture')
            git('config', 'user.name', 'Fixture')
            git('config', 'user.email', 'fixture@example.invalid')
            (root / 'README.md').write_text('before')
            git('add', '.'); git('commit', '-m', 'base')
            base = git('rev-parse', 'HEAD')
            (root / 'README.md').write_text('after')
            git('add', '.'); git('commit', '-m', 'readme')
            (root / 'CHANGELOG.md').write_text('release notes')
            git('add', '.'); git('commit', '-m', 'notes')
            with patch('workflow_plan.git', side_effect=git):
                self.assertFalse(requires_build('push', {'before': base}))
                self.assertFalse(requires_build('pull_request', {'pull_request': {'base': {'sha': base}}}))
                self.assertTrue(requires_build('workflow_dispatch', {}))
                (root / 'lib').mkdir()
                git('mv', 'README.md', 'lib/main.dart')
                git('commit', '-m', 'payload rename')
                self.assertTrue(requires_build('push', {'before': base}))

    def test_branch_creation_and_unknown_bases_build_conservatively(self):
        self.assertTrue(requires_build('push', {'before': '0' * 40}))
        self.assertTrue(requires_build('push', {}))

    def test_a_failure_cancelled_missing_or_skipped_required_job_blocks_the_gate(self):
        good = {'plan': 'success', 'validate': 'success', 'compile': 'success'}
        self.assertTrue(required_checks_pass(True, good))
        for job in good:
            for status in ['failure', 'cancelled', 'skipped', None]:
                with self.subTest(job=job, status=status):
                    self.assertFalse(required_checks_pass(True, {**good, job: status}))
        self.assertTrue(required_checks_pass(False, {'plan': 'success', 'validate': 'skipped', 'compile': 'skipped'}))
        self.assertFalse(required_checks_pass(False, {'plan': 'failure', 'validate': 'skipped', 'compile': 'skipped'}))

    def test_gate_process_fails_when_validation_fails_even_if_compilation_succeeded(self):
        needs = {'plan': {'result': 'success', 'outputs': {'build_required': 'true'}},
                 'validate': {'result': 'failure'}, 'compile': {'result': 'success'}}
        result = subprocess.run([os.sys.executable, str(ROOT / 'scripts/workflow_plan.py'), 'gate'],
                                env={**os.environ, 'JOB_RESULTS': json.dumps(needs)}, capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('Required jobs did not succeed', result.stderr)

    def test_workflow_publishes_only_after_the_always_completing_check_gate(self):
        workflow = yaml.load((ROOT / '.github/workflows/windows.yml').read_text(), Loader=UniqueKeyLoader)
        self.assertNotIn('paths-ignore', workflow['on']['push'])
        self.assertIn('workflow_dispatch', workflow['on'])
        jobs = workflow['jobs']
        self.assertEqual(jobs['windows']['needs'], ['plan', 'validate', 'compile'])
        self.assertIn('always()', jobs['windows']['if'])
        for name in ['compile', 'validate']:
            self.assertEqual(jobs[name]['needs'], 'plan')
            self.assertIn("build_required == 'true'", jobs[name]['if'])
            concurrency = jobs[name]['concurrency']
            self.assertIn("github.event_name == 'push'", concurrency['cancel-in-progress'])
            self.assertIn('github.run_id', concurrency['group'])
            setup, = [step for step in jobs[name]['steps'] if step.get('uses') == 'subosito/flutter-action@v2']
            self.assertEqual(setup['with']['flutter-version'], '3.47.6')
            self.assertEqual(setup['with']['cache'], 'true')
        for name in ['test-release', 'cloud-download']:
            self.assertEqual(jobs[name]['needs'], ['plan', 'windows'])
            self.assertIn("needs.windows.result == 'success'", jobs[name]['if'])
            self.assertIn("build_required == 'true'", jobs[name]['if'])
        self.assertEqual(jobs['test-release']['concurrency']['cancel-in-progress'], 'false')
        commands = '\n'.join(step.get('run', '') for step in jobs['validate']['steps'])
        for required in ['flutter analyze --no-pub', 'flutter test --no-pub', 'test_windows_bundled_startup.ps1',
                         'test_verified_engine_archive.ps1', 'test_studio_launcher.ps1', 'test_official_visions_import.ps1',
                         'unittest discover']:
            self.assertIn(required, commands)
        cache, = [step for step in jobs['validate']['steps'] if step.get('uses') == 'actions/cache@v4']
        self.assertEqual(cache['with']['key'], 'ffr-windows-engine-1.0.0.15-1c6e4d4b348b048404b6578bf10010c4caa873a5599d9dcbb9f64b00d299c41d')


if __name__ == '__main__':
    unittest.main()
