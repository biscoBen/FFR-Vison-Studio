import copy
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import stat
import sys
import tempfile
import unittest
from unittest import mock
import urllib.error
import zipfile

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location('deck_sync', ROOT / 'assets/existing_visions/payload/_ffr_deck_sync.py')
sync = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sync)


class Vault:
    def __init__(self):
        self.values = {}
    def get(self, repo):
        return self.values.get(repo)
    def put(self, repo, token):
        self.values[repo] = token
        return True


class FakeGitHub:
    private_repo = True
    owner = 'tester'
    push = True
    calls = []
    uploaded = b''
    def __init__(self, token):
        if not token:
            raise sync.SyncError('Missing token')
    def private(self, repo, publishing=False):
        return sync.GitHub.private(self, repo, publishing)
    def api(self, path, method='GET', body=None):
        self.calls.append((path, method, body))
        if path == '/user':
            return {'login': 'tester'}
        if path == '/repos/tester/private-mods':
            return {'full_name': 'tester/private-mods', 'private': self.private_repo,
                    'owner': {'login': self.owner}, 'permissions': {'push': self.push}, 'default_branch': 'main'}
        if method == 'POST':
            return {'id': 12}
        return None
    def request(self, path, method='GET', stream=None, size=None):
        self.uploaded = stream.read()
        self.calls.append((path, method, size))
        return io.BytesIO(json.dumps({'digest': 'sha256:' + hashlib.sha256(self.uploaded).hexdigest()}).encode())


def fixture(base, cycling=False):
    root, game = base / 'engine', base / 'pc-game'
    for name in sync.PAKS:
        path = root / 'build/out' / Path(name).name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(('synthetic built ' + name).encode())
    marker = game / sync.MARKER
    marker.parent.mkdir(parents=True, exist_ok=True)
    marker.write_bytes(b'explicit synthetic game version fixture')
    leader = {'schema': 1, 'files': {'enabled.txt': '', 'Scripts/main.lua': 'synthetic code', 'Scripts/config.lua': 'synthetic config'} if cycling else {}}
    sync.json_write(root / 'build/field-leader/payload.json', leader)
    if cycling:
        for name in sync.REQUIRED_LOADER:
            path = game / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(('synthetic loader ' + name).encode())
    env = {'ROOT': str(root), 'MOD_FILES': [Path(x).name for x in sync.PAKS], 'ENGINE_VERSION': 'fixture',
           'ffrenv': mock.Mock(game_root=lambda: str(game))}
    sync.capture(env)
    archive = base / 'mod.zip'
    manifest = sync.make_package(env, archive)
    staging = base / 'staging'
    sync.validate_package(archive, staging)
    deck = base / 'deck-game'
    path = deck / sync.MARKER
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(marker.read_bytes())
    return root, game, env, archive, manifest, staging, deck


class SyncTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        FakeGitHub.private_repo, FakeGitHub.owner, FakeGitHub.push, FakeGitHub.calls = True, 'tester', True, []

    def test_uploads_off_and_destination_empty_on_new_install(self):
        self.assertEqual(sync.settings(self.base), {'schema': 1, 'enabled': False, 'repository': ''})
        with self.assertRaisesRegex(sync.SyncError, 'off'):
            sync.publish({'ROOT': self.base}, github=mock.Mock(side_effect=AssertionError('Network called')))
        self.assertEqual(list(self.base.iterdir()), [])

    def test_settings_never_store_token_and_destinations_are_independent(self):
        vault = Vault()
        a, b = self.base / 'a', self.base / 'b'
        token = 'github_pat_' + 'A' * 25
        sync.configure(a, True, 'tester/private-mods', token, github=FakeGitHub, credentials=vault)
        self.assertNotIn(token, (a / sync.SETTINGS).read_text())
        self.assertFalse(sync.settings(b)['enabled'])
        self.assertNotEqual(sync.CredentialStore(a)._name('tester/private-mods'), sync.CredentialStore(b)._name('tester/private-mods'))

    def test_reject_public_and_another_users_repository_before_upload(self):
        for key, value in [('private_repo', False), ('owner', 'someone-else'), ('push', False)]:
            with self.subTest(key=key):
                setattr(FakeGitHub, key, value)
                with self.assertRaises(sync.SyncError):
                    sync.configure(self.base, True, 'tester/private-mods', 'github_pat_' + 'a' * 25, github=FakeGitHub, credentials=Vault())
                self.assertFalse((self.base / sync.SETTINGS).exists())
                setattr(FakeGitHub, key, {'private_repo': True, 'owner': 'tester', 'push': True}[key])
        for repo in ('biscoBen/FFR-Vison-Studio', 'bad/../../x', 'https://github.com/a/b', 'a/b?query', 'a/..'):
            with self.assertRaises(sync.SyncError):
                sync.repository(repo)

    def test_disabling_never_contacts_github(self):
        sync.configure(self.base, False, '', github=mock.Mock(side_effect=AssertionError('Network')))
        self.assertFalse(sync.settings(self.base)['enabled'])

    def test_corrupt_settings_do_not_enable_or_upload(self):
        (self.base / sync.SETTINGS).write_text('{bad json')
        with self.assertRaises(sync.SyncError):
            sync.settings(self.base)
        sync.json_write(self.base / sync.SETTINGS, {'schema': 1, 'enabled': True, 'repository': 'tester/private-mods', 'token': 'secret'})
        with self.assertRaises(sync.SyncError):
            sync.settings(self.base)

    def test_package_is_only_finished_mod_not_config_saves_or_credentials(self):
        root, game, env, archive, manifest, _, _ = fixture(self.base)
        (root / 'config.json').write_text('SECRET PC PATH')
        (root / 'my-save.sav').write_text('SAVE')
        (root / sync.SETTINGS).write_text('SECRET SETTINGS')
        sync.make_package(env, archive)
        with zipfile.ZipFile(archive) as bundle:
            self.assertEqual(set(bundle.namelist()), {'manifest.json', *('files/' + x for x in sync.PAKS)})
            self.assertNotIn(str(root), bundle.read('manifest.json').decode())
        self.assertEqual(set(manifest['files']), set(sync.PAKS))

    def test_cycling_package_has_working_loader_and_exact_scripts(self):
        *_, manifest, staging, deck = fixture(self.base, cycling=True)
        self.assertTrue(set(sync.LEADER_FILES + sync.REQUIRED_LOADER).issubset(manifest['files']))
        result = sync.install(self.base / 'state', deck, staging, manifest, 'tester/private-mods', running=lambda: False)
        self.assertTrue(result['cycling'])
        self.assertEqual((deck / sync.LEADER / 'Scripts/main.lua').read_text(), 'synthetic code')

    def test_changed_output_failed_build_and_new_game_block_publish(self):
        root, game, env, archive, *_ = fixture(self.base)
        output = root / 'build/out' / Path(sync.PAKS[0]).name
        output.write_bytes(b'new failed build output')
        with self.assertRaisesRegex(sync.SyncError, 'changed'):
            sync.make_package(env, archive)
        sync.begin_build(root)
        with self.assertRaisesRegex(sync.SyncError, 'Build successfully'):
            sync.make_package(env, archive)
        sync.capture(env)
        (game / sync.MARKER).write_bytes(b'game updated')
        with self.assertRaisesRegex(sync.SyncError, 'game.*runtime changed'):
            sync.make_package(env, archive)

    def test_runtime_change_and_missing_loader_block_publish(self):
        root, game, env, archive, *_ = fixture(self.base, cycling=True)
        (game / sync.REQUIRED_LOADER[0]).write_bytes(b'changed loader')
        with self.assertRaisesRegex(sync.SyncError, 'changed'):
            sync.make_package(env, archive)
        (game / sync.REQUIRED_LOADER[0]).unlink()
        with self.assertRaisesRegex(sync.SyncError, 'working UE4SS'):
            sync.capture(env)

    def test_draft_upload_verified_before_publication(self):
        root, _, env, *_ = fixture(self.base)
        vault = Vault()
        sync.configure(root, True, 'tester/private-mods', 'github_pat_' + 'a' * 25, github=FakeGitHub, credentials=vault)
        result = sync.publish(env, github=FakeGitHub, credentials=vault)
        self.assertEqual(result['result'], 'ok')
        create = next(x for x in FakeGitHub.calls if x[1] == 'POST' and isinstance(x[2], dict))
        self.assertTrue(create[2]['draft'])
        self.assertFalse(next(x for x in FakeGitHub.calls if x[1] == 'PATCH')[2]['draft'])

    def test_bad_upload_never_publishes_and_cleans_its_draft(self):
        root, _, env, *_ = fixture(self.base)
        vault = Vault()
        sync.configure(root, True, 'tester/private-mods', 'github_pat_' + 'a' * 25, github=FakeGitHub, credentials=vault)
        class BadUpload(FakeGitHub):
            def request(self, *args, **kwargs):
                return io.BytesIO(b'{"digest":"sha256:bad"}')
        with self.assertRaisesRegex(sync.SyncError, 'checksum'):
            sync.publish(env, github=BadUpload, credentials=vault)
        self.assertFalse(any(x[1] == 'PATCH' for x in FakeGitHub.calls))
        self.assertTrue(any(x[1] == 'DELETE' for x in FakeGitHub.calls))

    def mutate_zip(self, source, edit):
        target = self.base / 'bad.zip'
        with zipfile.ZipFile(source) as original, zipfile.ZipFile(target, 'w') as out:
            entries = [(info, original.read(info)) for info in original.infolist()]
            edit(entries)
            for info, data in entries:
                out.writestr(info, data)
        return target

    def test_zip_traversal_links_duplicates_unlisted_paths_and_bad_checksum_rejected(self):
        _, _, _, archive, *_ = fixture(self.base)
        def symlink(entries):
            info, data = entries[0]
            info.external_attr = (stat.S_IFLNK | 0o777) << 16
        edits = [lambda e: e.append(('../escape', b'bad')),
                 lambda e: e.append(('files/FFRS/save.sav', b'bad')),
                 lambda e: e.append(e[0]), symlink,
                 lambda e: e.__setitem__(0, (e[0][0], b'bad checksum'))]
        for edit in edits:
            with self.subTest(edit=edit):
                with self.assertRaises(sync.SyncError):
                    sync.validate_package(self.mutate_zip(archive, edit), self.base / 'invalid-stage')
        self.assertFalse((self.base / 'escape').exists())

    def test_manifest_unsupported_file_and_incomplete_runtime_rejected(self):
        _, _, _, archive, *_ = fixture(self.base, cycling=True)
        def edit(entries):
            entries[:] = [(info, data) for info, data in entries if info.filename != 'files/' + sync.REQUIRED_LOADER[0]]
            for i, (info, data) in enumerate(entries):
                if info.filename == 'manifest.json':
                    value = json.loads(data)
                    del value['files'][sync.REQUIRED_LOADER[0]]
                    entries[i] = info, json.dumps(value).encode()
        with self.assertRaisesRegex(sync.SyncError, 'incomplete'):
            sync.validate_package(self.mutate_zip(archive, edit), self.base / 'bad-stage')

    def test_game_mismatch_running_game_and_staging_mutation_do_not_touch_game(self):
        _, _, _, _, manifest, stage, game = fixture(self.base)
        state = self.base / 'state'
        with self.assertRaisesRegex(sync.SyncError, 'Close Resonance'):
            sync.install(state, game, stage, manifest, 'tester/private-mods', running=lambda: True)
        (game / sync.MARKER).write_bytes(b'wrong version')
        with self.assertRaisesRegex(sync.SyncError, 'version differs'):
            sync.install(state, game, stage, manifest, 'tester/private-mods', running=lambda: False)
        (game / sync.MARKER).write_bytes(b'explicit synthetic game version fixture')
        (stage / sync.PAKS[0]).write_bytes(b'changed')
        with self.assertRaisesRegex(sync.SyncError, 'staged package changed'):
            sync.install(state, game, stage, manifest, 'tester/private-mods', running=lambda: False)
        self.assertFalse((game / sync.PAKS[0]).exists())

    def test_install_preserves_other_mods_restore_originals_and_repeated_restore(self):
        _, _, _, _, manifest, stage, game = fixture(self.base)
        original = game / sync.PAKS[0]
        original.parent.mkdir(parents=True)
        original.write_bytes(b'old pak')
        other = original.parent / 'someone_else.pak'
        other.write_bytes(b'other mod')
        state = self.base / 'state'
        sync.install(state, game, stage, manifest, 'tester/private-mods', running=lambda: False)
        self.assertNotEqual(original.read_bytes(), b'old pak')
        self.assertTrue(sync.restore(state, running=lambda: False))
        self.assertEqual(original.read_bytes(), b'old pak')
        self.assertFalse((game / sync.PAKS[1]).exists())
        self.assertEqual(other.read_bytes(), b'other mod')
        self.assertFalse(sync.restore(state, running=lambda: False))

    def test_changing_game_folder_requires_restore_then_allows_the_new_folder(self):
        _, _, _, _, manifest, stage, first = fixture(self.base)
        second = self.base / 'game-on-another-drive'
        marker = second / sync.MARKER
        marker.parent.mkdir(parents=True)
        marker.write_bytes((first / sync.MARKER).read_bytes())
        state = self.base / 'state'
        sync.install(state, first, stage, manifest, 'tester/private-mods', running=lambda: False)
        with self.assertRaisesRegex(sync.SyncError, 'Restore it before switching'):
            sync.install(state, second, stage, manifest, 'tester/private-mods', running=lambda: False)
        self.assertTrue(sync.restore(state, running=lambda: False))
        sync.install(state, second, stage, manifest, 'tester/private-mods', running=lambda: False)
        self.assertFalse((first / sync.PAKS[0]).exists())
        self.assertTrue((second / sync.PAKS[0]).exists())
        self.assertTrue(sync.restore(state, running=lambda: False))
        self.assertFalse((second / sync.PAKS[0]).exists())

    def test_disabling_cycle_removes_owned_loader_scripts_and_keeps_other_mods(self):
        _, _, _, _, first, stage, game = fixture(self.base, cycling=True)
        state = self.base / 'state'
        sync.install(state, game, stage, first, 'tester/private-mods', running=lambda: False)
        second = copy.deepcopy(first)
        second['files'] = {k: v for k, v in first['files'].items() if k in sync.PAKS}
        other = game / sync.BINARY / 'ue4ss/Mods/OtherMod/enabled.txt'
        other.parent.mkdir(parents=True)
        other.write_bytes(b'')
        sync.install(state, game, stage, second, 'tester/private-mods', running=lambda: False)
        self.assertFalse((game / sync.LEADER_FILES[0]).exists())
        self.assertFalse((game / sync.REQUIRED_LOADER[0]).exists())
        self.assertTrue(other.exists())

    def test_unowned_runtime_conflicts_and_changed_owned_files_are_preserved(self):
        _, _, _, _, manifest, stage, game = fixture(self.base, cycling=True)
        loader = game / sync.REQUIRED_LOADER[0]
        loader.parent.mkdir(parents=True)
        loader.write_bytes(b'another loader')
        state = self.base / 'state'
        with self.assertRaisesRegex(sync.SyncError, 'existing runtime'):
            sync.install(state, game, stage, manifest, 'tester/private-mods', running=lambda: False)
        self.assertEqual(loader.read_bytes(), b'another loader')
        loader.unlink()
        sync.install(state, game, stage, manifest, 'tester/private-mods', running=lambda: False)
        (game / sync.PAKS[0]).write_bytes(b'user edit')
        with self.assertRaisesRegex(sync.SyncError, 'changed outside'):
            sync.restore(state, running=lambda: False)
        self.assertEqual((game / sync.PAKS[0]).read_bytes(), b'user edit')

    def test_failed_copy_rolls_back_all_game_files_and_state(self):
        _, _, _, _, manifest, stage, game = fixture(self.base, cycling=True)
        state = self.base / 'state'
        original = game / sync.PAKS[0]
        original.parent.mkdir(parents=True)
        original.write_bytes(b'old')
        copying = sync.copy_atomic
        def fail(source, target):
            if Path(source).is_relative_to(stage) and str(target).endswith('.ucas'):
                raise OSError('fixture disk error')
            return copying(source, target)
        with mock.patch.object(sync, 'copy_atomic', side_effect=fail):
            with self.assertRaises(OSError):
                sync.install(state, game, stage, manifest, 'tester/private-mods', running=lambda: False)
        self.assertEqual(original.read_bytes(), b'old')
        self.assertFalse((game / sync.LEADER_FILES[0]).exists())
        self.assertFalse((game / sync.REQUIRED_LOADER[0]).exists())
        self.assertFalse((state / 'installed-state.json').exists())

    def test_failed_state_commit_rolls_back_previous_successful_install(self):
        _, _, _, _, manifest, stage, game = fixture(self.base)
        state = self.base / 'state'
        sync.install(state, game, stage, manifest, 'tester/private-mods', running=lambda: False)
        previous = (state / 'installed-state.json').read_bytes()
        modified = copy.deepcopy(manifest)
        (stage / sync.PAKS[0]).write_bytes(b'new successful build')
        modified['files'][sync.PAKS[0]] = {'sha256': sync.sha(stage / sync.PAKS[0]), 'size': 20}
        modified['files'][sync.PAKS[0]]['size'] = (stage / sync.PAKS[0]).stat().st_size
        old = (game / sync.PAKS[0]).read_bytes()
        writing = sync.json_write
        def fail_commit(path, value):
            if str(path).endswith('installed-state.json'):
                raise OSError('state commit failure')
            return writing(path, value)
        with mock.patch.object(sync, 'json_write', side_effect=fail_commit):
            with self.assertRaises(OSError):
                sync.install(state, game, stage, modified, 'tester/private-mods', running=lambda: False)
        self.assertEqual((game / sync.PAKS[0]).read_bytes(), old)
        self.assertEqual((state / 'installed-state.json').read_bytes(), previous)

    def test_interrupted_rollback_is_recovered_on_next_run(self):
        _, _, _, _, manifest, stage, game = fixture(self.base, cycling=True)
        state = self.base / 'state'
        original = game / sync.PAKS[2]
        original.parent.mkdir(parents=True)
        original.write_bytes(b'original pak')
        copying = sync.copy_atomic
        def interrupt(source, target):
            if Path(source).is_relative_to(stage) and str(target).endswith('.ucas'):
                raise OSError('interrupted install')
            if 'backups' in Path(source).parts and str(target).endswith('.pak'):
                raise OSError('interrupted rollback')
            return copying(source, target)
        with mock.patch.object(sync, 'copy_atomic', side_effect=interrupt):
            with self.assertRaises(OSError):
                sync.install(state, game, stage, manifest, 'tester/private-mods', running=lambda: False)
        self.assertTrue((state / 'install-journal.json').exists())
        self.assertTrue(sync.recover(state, running=lambda: False))
        self.assertEqual(original.read_bytes(), b'original pak')
        self.assertFalse((game / sync.LEADER_FILES[0]).exists())
        self.assertFalse((state / 'install-journal.json').exists())
        self.assertFalse((state / 'installed-state.json').exists())

    @unittest.skipIf(sys.platform == 'win32', 'Symlink fixture needs Unix')
    def test_linked_game_or_backup_paths_rejected(self):
        _, _, _, _, manifest, stage, game = fixture(self.base)
        linked = self.base / 'linked-game'
        linked.symlink_to(game, target_is_directory=True)
        # Calling checked directly preserves the link path for rejection.
        with self.assertRaisesRegex(sync.SyncError, 'links'):
            sync.checked(linked, sync.PAKS[0])
        mods = game / 'FFRS/Content/Paks/~mods'
        mods.symlink_to(self.base, target_is_directory=True)
        with self.assertRaisesRegex(sync.SyncError, 'links'):
            sync.install(self.base / 'state', game, stage, manifest, 'tester/private-mods', running=lambda: False)

    @unittest.skipIf(sys.platform == 'win32', 'Linux installer locking')
    def test_real_install_lock_excludes_concurrent_update(self):
        with sync.locked(self.base):
            with self.assertRaisesRegex(sync.SyncError, 'already running'):
                with sync.locked(self.base):
                    self.fail('lock acquired')
        with sync.locked(self.base):
            pass

    def test_authenticated_redirect_drops_token_and_refuses_other_hosts(self):
        client = sync.GitHub('github_pat_' + 'a' * 25)
        endpoint = 'https://api.github.com/repos/tester/private-mods/releases/assets/1'
        error = urllib.error.HTTPError(endpoint, 302, 'redirect', {'Location': 'https://release-assets.githubusercontent.com/file?secret=signed'}, None)
        client.opener = mock.Mock()
        client.opener.open.side_effect = [error, io.BytesIO(b'archive')]
        response = client.request('/repos/tester/private-mods/releases/assets/1', accept='application/octet-stream')
        self.assertEqual(response.read(), b'archive')
        signed = client.opener.open.call_args_list[1].args[0]
        self.assertIsNone(signed.get_header('Authorization'))
        error.headers['Location'] = 'https://example.com/steal'
        client.opener.open.side_effect = error
        with self.assertRaises(sync.SyncError) as captured:
            client.request('/repos/tester/private-mods/releases/assets/1', accept='application/octet-stream')
        self.assertNotIn('signed', str(captured.exception))
        self.assertNotIn(client.token, str(captured.exception))

    def test_download_checksum_failure_and_truncation(self):
        client = mock.Mock(request=lambda *a, **kw: io.BytesIO(b'bad bytes'))
        with self.assertRaises(sync.SyncError):
            sync.download(client, 'tester/private-mods', {'id': 1, 'size': 9}, '0' * 64, self.base / 'download.zip')
        with self.assertRaises(sync.SyncError):
            sync.download(client, 'tester/private-mods', {'id': 1, 'size': 100}, hashlib.sha256(b'bad bytes').hexdigest(), self.base / 'download.zip')

    def test_latest_selects_only_complete_private_channel_releases(self):
        digest = 'a' * 64
        metadata = {'schema': 1, 'channel': sync.CHANNEL, 'repository': 'tester/private-mods',
                    'packageId': 'b' * 32, 'sha256': digest, 'gameSha256': 'c' * 64}
        valid = {'id': 1, 'published_at': '2026-10-13', 'body': json.dumps(metadata),
                 'assets': [{'id': 1, 'name': 'Resonance-Mod.zip', 'size': 5, 'digest': 'sha256:' + digest}]}
        draft = {**valid, 'id': 2, 'draft': True}
        wrong = {**valid, 'id': 3, 'body': json.dumps({**metadata, 'repository': 'another/person'})}
        incomplete = {**valid, 'id': 4, 'assets': []}
        client = mock.Mock()
        client.api.return_value = [draft, wrong, incomplete, valid]
        self.assertEqual(sync.latest(client, 'tester/private-mods')[0]['id'], 1)

    def test_linux_credentials_never_fall_back_to_plaintext(self):
        with mock.patch.object(sync.sys, 'platform', 'linux'), mock.patch.object(sync.shutil, 'which', return_value=None):
            vault = sync.CredentialStore(self.base)
            self.assertIsNone(vault.get('tester/private-mods'))
            self.assertFalse(vault.put('tester/private-mods', 'github_pat_' + 'a' * 25))
        self.assertEqual(list(self.base.iterdir()), [])

    def test_kwallet_receives_token_only_on_stdin_and_forget_clears_it(self):
        saved = ''
        token = 'github_pat_' + 'a' * 25
        def query(command, **kwargs):
            nonlocal saved
            self.assertNotIn(token, command)
            self.assertEqual(command[-3:], ['--folder', 'FFR Studio', 'kdewallet'])
            if command[1] == '--write-password':
                saved = kwargs['input']
                return mock.Mock(returncode=0, stdout='')
            return mock.Mock(returncode=0, stdout=saved + '\n')
        with mock.patch.object(sync.sys, 'platform', 'linux'), mock.patch.object(sync.shutil, 'which', side_effect=lambda name: '/usr/bin/kwallet-query' if name == 'kwallet-query' else None), mock.patch.object(sync.subprocess, 'run', side_effect=query):
            vault = sync.CredentialStore(self.base)
            self.assertTrue(vault.put('tester/private-mods', token))
            self.assertEqual(vault.get('tester/private-mods'), token)
            vault.delete('tester/private-mods')
            self.assertIsNone(vault.get('tester/private-mods'))

    @unittest.skipUnless(sys.platform == 'win32', 'Real Windows Credential Manager')
    def test_real_windows_credentials_round_trip_and_forget(self):
        vault = sync.CredentialStore(self.base)
        repo = 'tester/private-mods'
        try:
            self.assertTrue(vault.put(repo, 'github_pat_' + 'a' * 25))
            self.assertEqual(vault.get(repo), 'github_pat_' + 'a' * 25)
        finally:
            vault.delete(repo)
        self.assertIsNone(vault.get(repo))


if __name__ == '__main__':
    unittest.main()
