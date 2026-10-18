"""Optional installation, interrupted downloads and immutable publication contracts."""
import hashlib
import io
import json
from pathlib import Path
import sys
import tempfile
import threading
from types import SimpleNamespace
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'assets/existing_visions/payload'))
import _ffr_ffbe_download as download
import publish_ffbe_library as publisher


class Response(io.BytesIO):
    def __init__(self, data, status=200, headers=None):
        super().__init__(data)
        self.status = status
        self.headers = headers or {}


class InstallationTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.data = {'library-01.zip': b'source pack one', 'library-02.zip': b'source pack two'}
        self.manifest = {'schema': 1, 'revision': download.REVISION, 'files': {}, 'packs': [
            {'name': name, 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}
            for name, raw in self.data.items()]}
        self.requests = []

    def opener(self, request, timeout):
        self.requests.append(request)
        self.assertEqual(timeout, 20)
        self.assertTrue(request.full_url.startswith(download.BASE_URL))
        return Response(self.data[request.full_url.rsplit('/', 1)[1]])

    def install(self, opener=None, on_ready=None):
        return download.Installation(self.root, manifest=self.manifest,
                                     opener=opener or self.opener, on_ready=on_ready)

    def finish(self, installation):
        installation.start()
        installation.thread.join(5)
        self.assertFalse(installation.thread.is_alive())
        return installation.status()

    def partial(self, installation, data):
        path = installation.path(download.REVISION + '/library-01.zip.part')
        path.parent.mkdir(parents=True)
        path.write_bytes(data)
        return path

    def test_checking_missing_library_neither_downloads_nor_creates_directories(self):
        install = self.install()
        self.assertFalse(install.status()['ready'])
        self.assertEqual(install.status()['neededBytes'], sum(map(len, self.data.values())))
        self.assertEqual(self.requests, [])
        self.assertEqual(list(self.root.iterdir()), [])

    def test_explicit_download_commits_manifest_last_and_preserves_roster(self):
        state = self.root / 'mods/EstherTsukiko/units.json'
        state.parent.mkdir(parents=True)
        state.write_text('private roster')
        callbacks = []
        def opener(request, timeout):
            self.assertFalse((install.root / 'manifest.json').exists())
            return self.opener(request, timeout)
        install = self.install(opener, lambda: callbacks.append('ready'))
        self.assertTrue(self.finish(install)['ready'])
        self.assertEqual(len(self.requests), 2)
        self.assertEqual(callbacks, ['ready'])
        self.assertEqual(state.read_text(), 'private roster')
        self.assertEqual(json.loads((install.root / 'manifest.json').read_bytes()), self.manifest)
        # Opening a new Studio process / installing an app update reuses valid data.
        self.requests.clear()
        again = self.install()
        self.assertTrue(again.status()['ready'])
        self.assertTrue(again.start()['ready'])
        self.assertEqual(self.requests, [])
        self.assertIsNone(again.thread)

    def test_verified_packs_with_missing_manifest_need_no_network(self):
        install = self.install()
        self.assertTrue(self.finish(install)['ready'])
        (install.root / 'manifest.json').unlink()
        self.requests.clear()
        again = self.install()
        self.assertFalse(again.status()['ready'])
        self.assertEqual(again.status()['neededBytes'], 0)
        self.assertTrue(self.finish(again)['ready'])
        self.assertEqual(self.requests, [])

    def test_partial_download_resumes_only_with_exact_range(self):
        def opener(request, timeout):
            name = request.full_url.rsplit('/', 1)[1]
            if name == 'library-01.zip':
                self.assertEqual(request.get_header('Range'), 'bytes=5-')
                raw = self.data[name]
                return Response(raw[5:], 206, {'Content-Range': f'bytes 5-{len(raw)-1}/{len(raw)}'})
            return self.opener(request, timeout)
        install = self.install(opener)
        partial = self.partial(install, self.data['library-01.zip'][:5])
        self.assertTrue(self.finish(install)['ready'])
        self.assertFalse(partial.exists())

    def test_server_ignoring_range_restarts_instead_of_appending(self):
        install = self.install()
        self.partial(install, self.data['library-01.zip'][:5])
        self.assertTrue(self.finish(install)['ready'])
        self.assertEqual(self.requests[0].get_header('Range'), 'bytes=5-')
        self.assertEqual(install.path(download.REVISION + '/library-01.zip').read_bytes(), self.data['library-01.zip'])

    def test_invalid_range_or_checksum_never_publishes_library(self):
        for response in (lambda: Response(b'bad', 206, {'Content-Range': 'bytes 0-2/3'}),
                         lambda: Response(b'X' * len(self.data['library-01.zip']))):
            with self.subTest(response=response):
                install = self.install(lambda *a, **k: response())
                result = self.finish(install)
                self.assertEqual(result['state'], 'error')
                self.assertFalse(result['ready'])
                self.assertFalse((install.root / 'manifest.json').exists())

    def test_pause_retains_partial_and_duplicate_start_uses_same_worker(self):
        entered = threading.Event()
        release = threading.Event()
        raw = self.data['library-01.zip']
        class PausingResponse(Response):
            def read(response, size):
                if response.tell() == 0:
                    return super().read(5)
                entered.set()
                release.wait(3)
                return super().read(size)
        install = self.install(lambda *a, **k: PausingResponse(raw))
        install.start()
        self.assertTrue(entered.wait(3))
        worker = install.thread
        self.assertTrue(install.start()['running'])
        self.assertIs(worker, install.thread)
        install.cancel()
        release.set()
        worker.join(5)
        self.assertEqual(install.status()['state'], 'cancelled')
        self.assertFalse((install.root / 'manifest.json').exists())
        self.assertTrue(install.path(download.REVISION + '/library-01.zip.part').exists())
        install.opener = self.opener
        self.assertTrue(self.finish(install)['ready'])

    def test_corrupted_pack_is_repaired_without_redownloading_others(self):
        install = self.install()
        self.assertTrue(self.finish(install)['ready'])
        pack = install.path(download.REVISION + '/library-02.zip')
        pack.write_bytes(b'X' * len(self.data['library-02.zip']))
        self.requests.clear()
        again = self.install()
        self.assertEqual(again.status()['filesDone'], 1)
        self.assertTrue(self.finish(again)['ready'])
        self.assertEqual([r.full_url.rsplit('/', 1)[1] for r in self.requests], ['library-02.zip'])

    def test_untrusted_pack_name_and_linked_destination_are_rejected(self):
        self.manifest['packs'][0]['name'] = '../library-01.zip'
        with self.assertRaisesRegex(ValueError, 'metadata'):
            self.install()
        if sys.platform != 'win32':
            self.manifest['packs'][0]['name'] = 'library-01.zip'
            (self.root / 'library').symlink_to(self.root, target_is_directory=True)
            with self.assertRaisesRegex(ValueError, 'symbolic'):
                self.install().status()


class PublicationTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        directory = self.root / 'assets/ffbe_library'
        directory.mkdir(parents=True)
        raw = b'immutable source'
        self.pack = directory / 'library-01.zip'
        self.pack.write_bytes(raw)
        manifest = {'packs': [{'name': self.pack.name, 'bytes': len(raw),
                              'sha256': hashlib.sha256(raw).hexdigest()}]}
        (directory / 'manifest.json').write_text(json.dumps(manifest))
        self.release = {'assets': [{'name': p.name, 'state': 'uploaded', 'size': p.stat().st_size,
                                   'digest': 'sha256:' + hashlib.sha256(p.read_bytes()).hexdigest()}
                                  for p in directory.iterdir()]}

    def test_existing_data_release_is_reused_without_upload_or_overwrite(self):
        result = SimpleNamespace(returncode=0, stdout=json.dumps(self.release))
        with patch.object(publisher, 'ROOT', self.root), patch.object(publisher.subprocess, 'run', return_value=result), \
                patch.object(publisher, 'command', return_value=json.dumps(self.release)) as command:
            publisher.publish()
        self.assertTrue(all(c.args[0] == 'api' for c in command.call_args_list))

    def test_changed_remote_asset_fails_before_any_upload(self):
        self.release['assets'][0]['digest'] = 'sha256:' + '0' * 64
        result = SimpleNamespace(returncode=0, stdout=json.dumps(self.release))
        with patch.object(publisher, 'ROOT', self.root), patch.object(publisher.subprocess, 'run', return_value=result), \
                patch.object(publisher, 'command') as command:
            with self.assertRaisesRegex(RuntimeError, 'differs'):
                publisher.publish()
            command.assert_not_called()

    def test_local_source_corruption_cannot_be_published(self):
        self.pack.write_bytes(b'corruption')
        self.release['assets'] = [a for a in self.release['assets'] if a['name'] != self.pack.name]
        result = SimpleNamespace(returncode=0, stdout=json.dumps(self.release))
        with patch.object(publisher, 'ROOT', self.root), patch.object(publisher.subprocess, 'run', return_value=result), \
                patch.object(publisher, 'command') as command:
            with self.assertRaisesRegex(ValueError, 'changed'):
                publisher.publish()
            command.assert_not_called()


if __name__ == '__main__':
    unittest.main()
