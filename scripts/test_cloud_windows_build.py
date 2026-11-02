import unittest
import base64
import hashlib
from types import SimpleNamespace
from pathlib import Path
import tempfile
from unittest.mock import patch
import zipfile

from cloud_windows_build import BuildError, build, download_cloud_release, extract_verified_zip, github_environment, matching_run


class BuildSelectionTests(unittest.TestCase):
    def test_joined_failed_run_stops_instead_of_dispatching_another_build(self):
        active = {'id': 9, 'head_branch': "Sephira's-Update", 'head_sha': 'wanted',
                  'workflow_id': 42, 'path': '.github/workflows/windows.yml',
                  'display_title': 'ffr-windows-v1 build=15 cloud=false', 'event': 'push',
                  'status': 'in_progress', 'conclusion': None, 'html_url': 'https://example.test/run/9'}
        args = SimpleNamespace(build=15, ref="Sephira's-Update", enable_actions=False,
                               cloud_download=False, force_rebuild=False, timeout=60)
        for conclusion in ('failure', 'cancelled', 'timed_out'):
            with self.subTest(conclusion=conclusion):
                def api(path, **kwargs):
                    if path.startswith('git/ref/heads/'): return {'object': {'sha': 'wanted'}}
                    if path == 'actions/workflows/windows.yml': return {'id': 42, 'state': 'active'}
                    if path.startswith('contents/'): return {'sha': 'workflow', 'content': base64.b64encode(b'ffr-windows-v1').decode()}
                    if path.startswith('actions/workflows/windows.yml/runs?'): return {'workflow_runs': [active]}
                    if path == 'actions/runs/9': return dict(active, status='completed', conclusion=conclusion)
                    self.fail('Unexpected API request: ' + path)
                with patch('cloud_windows_build.api', side_effect=api) as requests, \
                        patch('cloud_windows_build.subprocess.check_output', side_effect=['other-branch', 'wanted']), \
                        patch('cloud_windows_build.time.sleep'):
                    with self.assertRaisesRegex(BuildError, 'Build finished with ' + conclusion): build(args)
                    self.assertFalse(any('dispatches' in call.args[0] for call in requests.call_args_list))

    def test_selects_only_new_runs_for_the_requested_branch_and_commit(self):
        runs = [
            {"id": 1, "head_branch": "Sephira's-Update", "head_sha": "wanted", "event": "workflow_dispatch"},
            {"id": 2, "head_branch": "master", "head_sha": "wanted", "event": "workflow_dispatch"},
            {"id": 3, "head_branch": "Sephira's-Update", "head_sha": "old", "event": "workflow_dispatch"},
            {"id": 4, "head_branch": "Sephira's-Update", "head_sha": "wanted", "event": "push"},
            {"id": 5, "head_branch": "Sephira's-Update", "head_sha": "wanted", "event": "workflow_dispatch"},
        ]
        selected = matching_run(runs, branch="Sephira's-Update", commit="wanted", previous_ids={1})
        self.assertEqual(selected["id"], 5)

    def test_no_matching_run_is_not_treated_as_a_success(self):
        self.assertIsNone(matching_run(
            [{"id": 1, "head_branch": "master", "head_sha": "wanted", "event": "workflow_dispatch"}],
            branch="Sephira's-Update", commit="wanted", previous_ids=set(),
        ))

    def test_build_binding_does_not_mutate_the_existing_authentication(self):
        with patch.dict("os.environ", {"GH_TOKEN": "existing-test-binding", "FFR_GITHUB_ACTIONS_TOKEN": "scoped-test-binding"}, clear=True):
            environment = github_environment()
            self.assertEqual(environment["GH_TOKEN"], "scoped-test-binding")
            import os
            self.assertEqual(os.environ["GH_TOKEN"], "existing-test-binding")

    def test_download_checksum_is_required_before_extraction(self):
        with tempfile.TemporaryDirectory() as directory:
            archive = Path(directory) / "build.zip"
            destination = Path(directory) / "extracted"
            with zipfile.ZipFile(archive, "w") as bundle:
                bundle.writestr("FFR Vision Studio.exe", b"test executable")
            with self.assertRaisesRegex(BuildError, 'SHA256 digest'):
                extract_verified_zip(archive, destination, "sha256:" + "0" * 64)
            self.assertFalse(destination.exists())
            digest = "sha256:" + hashlib.sha256(archive.read_bytes()).hexdigest()
            extract_verified_zip(archive, destination, digest)
            self.assertEqual((destination / "FFR Vision Studio.exe").read_bytes(), b"test executable")

    def test_download_cannot_write_outside_destination(self):
        with tempfile.TemporaryDirectory() as directory:
            archive = Path(directory) / "build.zip"
            with zipfile.ZipFile(archive, "w") as bundle:
                bundle.writestr("../unexpected.txt", b"unsafe path")
            digest = "sha256:" + hashlib.sha256(archive.read_bytes()).hexdigest()
            with self.assertRaisesRegex(BuildError, 'outside its destination'):
                extract_verified_zip(archive, Path(directory) / "extracted", digest)
            self.assertFalse((Path(directory) / "unexpected.txt").exists())

    def test_download_copy_for_another_commit_is_rejected(self):
        release = {'id': 7, 'draft': True, 'tag_name': 'cloud-test-5',
                   'target_commitish': 'old', 'body': '{}'}
        with patch('cloud_windows_build.api', side_effect=[[release], release]), \
                patch('cloud_windows_build.gh') as github:
            with self.assertRaisesRegex(BuildError, 'does not match'):
                download_cloud_release(
                    {'id': 5, 'head_sha': 'wanted', 'head_branch': "Sephira's-Update"},
                    {'id': 4}, Path('/unused-test-destination'),
                )
            github.assert_not_called()


if __name__ == "__main__":
    unittest.main()
