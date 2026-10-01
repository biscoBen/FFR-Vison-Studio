import argparse
import base64
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from build_contract import PROVENANCE, request_identity, run_title
from cloud_windows_build import (BuildError, InvalidArtifact, build, check_bundle, compatible_run,
                                download_run, published_release, select_reusable_run, verified_artifact)

BRANCH = "Sephira's-Update"
COMMIT = 'a' * 40
REQUEST = dict(branch=BRANCH, commit=COMMIT, workflow_id=7, build=15, cloud_download=False)


def run(identity=10, **changes):
    return dict(id=identity, head_sha=COMMIT, head_branch=BRANCH, workflow_id=7,
                path='.github/workflows/windows.yml', event='push',
                display_title=run_title(15, False), status='completed', conclusion='success',
                html_url=f'https://github.com/example/actions/runs/{identity}', run_attempt=1, **changes)


class BuildReuseTests(unittest.TestCase):
    def test_only_exact_commit_workflow_branch_and_inputs_can_be_reused(self):
        candidate = run()
        self.assertTrue(compatible_run(candidate, **REQUEST))
        for changes in [dict(head_sha='b' * 40), dict(head_branch='master'), dict(workflow_id=8),
                        dict(path='other.yml'), dict(event='pull_request'),
                        dict(display_title=run_title(16, False)), dict(display_title=run_title(15, True)),
                        dict(display_title='legacy title with unknown inputs')]:
            with self.subTest(changes=changes):
                self.assertFalse(compatible_run({**candidate, **changes}, **REQUEST))

    def test_successful_verified_build_is_preferred_to_running_build(self):
        running = {**run(11), 'status': 'in_progress', 'conclusion': None}
        self.assertEqual(select_reusable_run([running, run()], REQUEST, lambda _: True)['id'], 10)

    def test_missing_expired_or_incompatible_artifacts_do_not_count_as_success(self):
        self.assertIsNone(select_reusable_run([run()], REQUEST, lambda _: False))
        self.assertIsNone(select_reusable_run([{**run(), 'conclusion': 'failure'}], REQUEST, lambda _: True))
        running = {**run(12), 'status': 'queued', 'conclusion': None}
        self.assertEqual(select_reusable_run([run(), running], REQUEST, lambda _: False)['id'], 12)

    def test_artifact_identity_expiry_and_checksum_are_required(self):
        good = {'id': 4, 'name': 'FFR-Vision-Studio-windows', 'expired': False, 'digest': 'sha256:' + '0' * 64,
                'workflow_run': {'id': 10, 'head_sha': COMMIT, 'head_branch': BRANCH}}
        for changes in [{}, {'expired': True}, {'digest': None}, {'workflow_run': {'id': 9, 'head_sha': COMMIT, 'head_branch': BRANCH}}]:
            with patch('cloud_windows_build.api', return_value={'artifacts': [{**good, **changes}]}):
                self.assertEqual(verified_artifact(run()) is not None, not changes)

    def test_downloaded_identity_cannot_be_relabeled_for_a_different_commit_or_inputs(self):
        expected = request_identity(COMMIT, BRANCH, 15, False, 'blob', 10)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'FFR Vision Studio.exe').write_bytes(b'executable')
            (root / 'flutter_windows.dll').write_bytes(b'runtime')
            for changes in [{'commit': 'b' * 40}, {'workflow_sha': 'other'}, {'build': 16}, {'cloud_download': True}, {}]:
                (root / PROVENANCE).write_text(json.dumps({**expected, **changes}))
                if changes:
                    with self.assertRaises(InvalidArtifact): check_bundle(root, expected)
                else:
                    self.assertEqual(check_bundle(root, expected).name, 'FFR Vision Studio.exe')

    def test_public_release_requires_exact_metadata_target_and_asset_digest(self):
        metadata = {'channel': 'sephira-test', 'repository': 'biscoBen/FFR-Vison-Studio',
                    'branch': BRANCH, 'commit': COMMIT, 'run_id': 10, 'build': 15}
        release = {'id': 3, 'tag_name': 'sephira-test-10', 'draft': False, 'prerelease': True,
                   'target_commitish': COMMIT, 'body': json.dumps(metadata),
                   'assets': [{'name': 'Sephira-Studio-Test.zip', 'digest': 'sha256:' + '0' * 64}]}
        for changes in [{}, {'target_commitish': 'b' * 40}, {'draft': True},
                        {'body': json.dumps({**metadata, 'build': 16})}, {'body': None}, {'assets': []}]:
            with self.subTest(changes=changes), patch('cloud_windows_build.api', return_value={**release, **changes}):
                self.assertEqual(published_release(run(), 15) is not None, not changes)

    def test_failed_required_jobs_cannot_deliver_an_artifact(self):
        jobs = [{'name': name, 'conclusion': 'failure' if name == 'validate' else 'success'}
                for name in ['plan', 'validate', 'compile', 'windows']]
        with patch('cloud_windows_build.api', return_value={'jobs': jobs}), \
             patch('cloud_windows_build.verified_artifact') as artifact:
            with self.assertRaisesRegex(InvalidArtifact, 'every required'):
                download_run(run(), argparse.Namespace(), 'blob', True)
            artifact.assert_not_called()

    def test_authenticated_release_fallback_preserves_identity_and_ignores_partial_artifact(self):
        expected = request_identity(COMMIT, BRANCH, 15, False, 'blob', 10)
        jobs = [{'name': name, 'conclusion': 'success'} for name in ['plan', 'validate', 'compile', 'windows']]
        def blocked(artifact, destination):
            (destination / PROVENANCE).write_text('partial artifact')
            raise BuildError('HTTP 403: Forbidden')
        def release_download(selected, release, destination, build_number):
            (destination / PROVENANCE).write_text(json.dumps(expected))
            (destination / 'FFR Vision Studio.exe').write_bytes(b'executable')
            (destination / 'flutter_windows.dll').write_bytes(b'runtime')
            return {'download_source': 'test-release', 'download_sha256': 'sha256:' + '0' * 64}
        with tempfile.TemporaryDirectory() as directory, \
             patch('cloud_windows_build.api', return_value={'jobs': jobs}), \
             patch('cloud_windows_build.verified_artifact', return_value={'id': 4}), \
             patch('cloud_windows_build.download_artifact', side_effect=blocked), \
             patch('cloud_windows_build.published_release', return_value=({}, {})), \
             patch('cloud_windows_build.download_published_release', side_effect=release_download):
            args = argparse.Namespace(output=Path(directory), ref=BRANCH, build=15, cloud_download=False)
            record = download_run(run(), args, 'blob', True)
            self.assertEqual(record['commit'], COMMIT)
            self.assertEqual(record['download_source'], 'test-release')
            self.assertEqual(record['run_id'], 10)
            self.assertTrue(record['reused_run'])
            self.assertTrue(Path(record['executable']).is_file())
            self.assertEqual(json.loads((Path(record['executable']).parent / PROVENANCE).read_text()), expected)

    def exercise_helper(self, candidate, *, available=True, force=False, reject_download=False):
        dispatched = []
        fresh = {**run(20), 'event': 'workflow_dispatch'}
        def fake_api(path, method='GET', body=None):
            if path.startswith('git/ref/'):
                return {'object': {'sha': COMMIT}}
            if path.startswith('contents/'):
                return {'sha': 'blob', 'content': base64.b64encode(b'run-name: ffr-windows-v1').decode()}
            if path == 'actions/workflows/windows.yml':
                return {'state': 'active', 'id': 7}
            if path.endswith('/dispatches'):
                dispatched.append(body); return None
            if path.startswith('actions/workflows/windows.yml/runs?'):
                return {'workflow_runs': [candidate, fresh] if dispatched else [candidate]}
            if path.startswith('actions/runs/'):
                return {**candidate, 'status': 'completed', 'conclusion': 'success'}
            self.fail(path)
        def git(command, **kwargs):
            return BRANCH if 'branch' in command else COMMIT if 'rev-parse' in command else ''
        def download(selected, *args, **kwargs):
            if reject_download and selected['id'] == candidate['id']:
                raise InvalidArtifact('Wrong compiled inputs')
            return {'run_id': selected['id'], 'reused_run': kwargs['reused']}
        args = argparse.Namespace(ref=BRANCH, build=15, enable_actions=False, cloud_download=False,
                                  force_rebuild=force, timeout=10, output=Path('/unused'))
        with patch('cloud_windows_build.api', side_effect=fake_api), \
             patch('cloud_windows_build.subprocess.check_output', side_effect=git), \
             patch('cloud_windows_build.verified_artifact', return_value={'id': 4} if available else None), \
             patch('cloud_windows_build.published_release', return_value=None), \
             patch('cloud_windows_build.download_run', side_effect=download), \
             patch('cloud_windows_build.time.sleep'):
            result = build(args)
        return result, dispatched

    def test_helper_joins_running_build_without_dispatching_another(self):
        result, dispatched = self.exercise_helper({**run(), 'status': 'in_progress', 'conclusion': None})
        self.assertEqual(result, {'run_id': 10, 'reused_run': True})
        self.assertEqual(dispatched, [])

    def test_helper_reuses_success_without_dispatch(self):
        result, dispatched = self.exercise_helper(run())
        self.assertTrue(result['reused_run'])
        self.assertEqual(dispatched, [])

    def test_missing_artifact_incompatible_input_or_explicit_force_dispatches_one_build(self):
        for candidate, available, force in [(run(), False, False),
                                            ({**run(), 'display_title': run_title(16, False)}, True, False),
                                            (run(), True, True)]:
            with self.subTest(candidate=candidate, available=available, force=force):
                result, dispatched = self.exercise_helper(candidate, available=available, force=force)
                self.assertEqual(result, {'run_id': 20, 'reused_run': False})
                self.assertEqual(len(dispatched), 1)
                self.assertEqual(dispatched[0]['inputs'], {'build': '15', 'cloud_download': 'false'})

    def test_incompatible_download_is_rejected_and_rebuilt_without_relabeling(self):
        result, dispatched = self.exercise_helper(run(), reject_download=True)
        self.assertEqual(result['run_id'], 20)
        self.assertEqual(len(dispatched), 1)


if __name__ == '__main__':
    unittest.main()
