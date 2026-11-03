"""Large rollback history cleanup preserves originals, recent copies and user data."""
import json
import ast
import gzip
import os
from pathlib import Path
import shutil
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock

from test_existing_visions import ROOT
import _ffr_field_leader as leader
import _ffr_storage as storage


class BackupStorageTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / 'engine'; self.root.mkdir()
        self.game = Path(self.temp.name) / 'game'; self.game.mkdir()
        self.ledger = self.root / 'game_state.json'
        self.record = {'placed': [], 'original': {}, 'installs': []}
        self.save()

    def save(self):
        self.ledger.write_text(json.dumps(self.record))

    def add(self, day, recorded=True):
        stamp = f'20261102_{day:06d}'
        folder = self.root / 'backups' / stamp
        folder.mkdir(parents=True)
        for name in sorted(storage.FILES): (folder / name).write_bytes(b'previous package')
        if recorded:
            self.record['installs'].append({'game': str(self.game), 'backup': stamp})
            self.save()
        return folder

    def test_fifty_plus_copies_reclaim_only_old_recorded_packages_and_keep_restore_original(self):
        folders = [self.add(i) for i in range(60)]
        self.record['original'] = {'FFRS/Content/Paks/~mods/' + name: folders[0].name + '/' + name
                                   for name in storage.FILES}
        self.save()
        original = self.ledger.read_bytes()
        for name in ['mods/EstherTsukiko/units.json', 'build/out/current.ucas', 'extracted/rows/data.json', 'data/ffbe/custom.png']:
            p = self.root / name; p.parent.mkdir(parents=True, exist_ok=True); p.write_bytes(b'keep')
        before = {p: p.read_bytes() for p in self.root.rglob('*') if p.is_file() and 'backups' not in p.parts}
        plan = storage.plan(self.root, self.game)
        self.assertEqual(plan['removeCount'], 56)
        self.assertEqual(plan['originalCount'], 1)
        result = storage.prune(self.root, self.game, plan['token'])
        self.assertEqual(result['freedBytes'], 56 * 3 * len(b'previous package'))
        self.assertEqual([p.name for p in folders if p.exists()], [folders[0].name, *[p.name for p in folders[-3:]]])
        for p, raw in before.items(): self.assertEqual(p.read_bytes(), raw)
        self.assertEqual(self.ledger.read_bytes(), original)
        for reference in self.record['original'].values():
            self.assertEqual((self.root / 'backups' / reference).read_bytes(), b'previous package')

    def test_preview_does_not_change_files_or_enable_automatic_cleanup(self):
        for i in range(7): self.add(i)
        before = {p: p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
        self.assertFalse(storage.plan(self.root, self.game)['automatic'])
        self.assertFalse(storage.policy_path(self.root, self.game).exists())
        self.assertEqual(before, {p: p.read_bytes() for p in self.root.rglob('*') if p.is_file()})

    def test_unrecorded_partial_unknown_contents_and_non_timestamp_folders_are_kept(self):
        for i in range(7): self.add(i)
        partial = self.add(99, recorded=False)
        special = self.add(1_000)
        (special / 'personal.txt').write_text('keep')
        named = self.root / 'backups/user-named'; named.mkdir()
        (named / 'keep.txt').write_text('keep')
        plan = storage.plan(self.root, self.game)
        storage.prune(self.root, self.game, plan['token'])
        self.assertTrue(partial.exists()); self.assertTrue(special.exists()); self.assertTrue(named.exists())

    def test_stale_preview_or_new_original_reference_prevents_all_deletions(self):
        folders = [self.add(i) for i in range(7)]
        plan = storage.plan(self.root, self.game)
        next(folders[0].iterdir()).write_bytes(b'changed after preview')
        with self.assertRaisesRegex(ValueError, 'list changed'):
            storage.prune(self.root, self.game, plan['token'])
        self.assertTrue(all(p.exists() for p in folders))
        plan = storage.plan(self.root, self.game)
        self.record['original']['x'] = folders[0].name + '/' + next(iter(storage.FILES)); self.save()
        with self.assertRaisesRegex(ValueError, 'list changed'):
            storage.prune(self.root, self.game, plan['token'])

    def test_unreadable_or_unrecognized_original_reference_fails_closed(self):
        for i in range(7): self.add(i)
        for value in ['../outside/package.ucas', 'stamp/personal.txt', 1]:
            self.record['original'] = {'x': value}; self.save()
            with self.assertRaises(ValueError): storage.plan(self.root, self.game)
        self.assertEqual(len(list((self.root / 'backups').iterdir())), 7)

    def test_linked_backup_never_touches_outside_files(self):
        folders = [self.add(i) for i in range(7)]
        outside = self.game / 'keep'; outside.write_bytes(b'outside')
        target = folders[0] / next(iter(storage.FILES)); target.unlink()
        try: target.symlink_to(outside)
        except OSError: self.skipTest('symlink creation unavailable')
        plan = storage.plan(self.root, self.game)
        storage.prune(self.root, self.game, plan['token'])
        self.assertEqual(outside.read_bytes(), b'outside'); self.assertTrue(folders[0].exists())

    def test_other_game_scoped_ledger_and_backups_are_not_cleaned(self):
        for i in range(7): self.add(i)
        other = self.game.parent / 'other-game'; other.mkdir()
        scoped = Path(leader.game_state_path(self.root, other))
        scoped.write_text(json.dumps({'original': {}, 'installs': []}))
        marker = scoped.parent / 'backups/20261102_000001/keep'; marker.parent.mkdir(parents=True); marker.write_text('other game')
        plan = storage.plan(self.root, self.game)
        storage.prune(self.root, self.game, plan['token'])
        self.assertEqual(marker.read_text(), 'other game')

    def test_retention_only_runs_after_opt_in_and_cleanup_failure_does_not_fail_install(self):
        for i in range(7): self.add(i)
        storage.after_install(self.root, self.game, print)
        self.assertEqual(len(list((self.root / 'backups').iterdir())), 7)
        leader.atomic(storage.policy_path(self.root, self.game), b'{"schema":1,"automatic":true}')
        log = []; storage.after_install(self.root, self.game, log.append)
        self.assertEqual(len(list((self.root / 'backups').iterdir())), 3)
        self.assertIn('removed 4', log[0])
        with mock.patch.object(storage, 'prune', side_effect=OSError('locked backup')):
            storage.after_install(self.root, self.game, log.append)
        self.assertIn('did not complete', log[-1])

    def test_api_review_required_and_build_game_and_publish_busy_refuse_cleanup(self):
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        import _ffr_deck_sync as sync
        for i in range(7): self.add(i)
        state, running = {'running': False}, [False]
        app = FastAPI()
        storage.register(app, {'ROOT': self.root, 'ffrenv': SimpleNamespace(detect_game=lambda: str(self.game)),
                              'state': state, 'game_running': lambda: running[0]})
        with TestClient(app) as client:
            report = client.get('/api/storage/backups').json()
            body = {'token': report['token'], 'automatic': True}
            self.assertEqual(client.post('/api/storage/backups/cleanup', json={'automatic': True}).status_code, 409)
            state['running'] = True
            self.assertEqual(client.post('/api/storage/backups/cleanup', json=body).status_code, 409)
            state['running'] = False; running[0] = True
            self.assertEqual(client.post('/api/storage/backups/cleanup', json=body).status_code, 409)
            running[0] = False
            with mock.patch.dict(sync._publishing, {'running': True}):
                self.assertEqual(client.post('/api/storage/backups/cleanup', json=body).status_code, 409)
            response = client.post('/api/storage/backups/cleanup', json=body)
            self.assertEqual(response.status_code, 200, response.text)
            self.assertTrue(response.json()['automatic']); self.assertEqual(response.json()['removed'], 4)
            self.assertEqual(client.post('/api/storage/backups/cleanup', json=body).status_code, 409)

    def test_preflight_combines_copy_and_backup_on_same_volume_but_separates_drives(self):
        source = self.root / 'build/out'; source.mkdir(parents=True)
        destination = self.game / 'mods'; destination.mkdir()
        (source / 'mod').write_bytes(b'x' * 1000); (destination / 'mod').write_bytes(b'o' * 200)
        reserve = 64 * 1024**2
        with mock.patch.object(shutil, 'disk_usage', return_value=SimpleNamespace(free=reserve + 1100)):
            with self.assertRaisesRegex(RuntimeError, 'Install the last build'):
                storage.preflight(source, destination, self.root / 'backups', ['mod'])
            storage.preflight(source, destination, self.root / 'backups', ['mod'], unchanged=['mod'])
            separate = SimpleNamespace(name='nt', path=SimpleNamespace(splitdrive=lambda p: ('G:' if Path(p).is_relative_to(self.game.resolve()) else 'C:', p)))
            with mock.patch.object(storage, 'os', separate):
                storage.preflight(source, destination, self.root / 'backups', ['mod'])
        self.assertEqual((destination / 'mod').read_bytes(), b'o' * 200)
        self.assertFalse((self.root / 'backups').exists())

    def test_actual_pinned_installer_checks_space_before_writes_retains_backups_then_restores_original(self):
        from test_existing_visions import installer
        raw = gzip.decompress((ROOT / 'scripts/fixtures/existing_visions/server.py.gz').read_bytes())
        tree = ast.parse(installer.hook_server(raw))
        names = {'_game_state', '_save_game_state', '_game_root', 'install_files', 'restore_game'}
        methods = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in names]
        folders = [self.add(i) for i in range(7)]
        self.record['placed'] = ['FFRS/Content/Paks/~mods/' + name for name in storage.FILES]
        self.record['original'] = {'FFRS/Content/Paks/~mods/' + name: folders[0].name + '/' + name for name in storage.FILES}
        self.save()
        source = self.root / 'build/out'; source.mkdir(parents=True)
        destination = self.game / 'FFRS/Content/Paks/~mods'; destination.mkdir(parents=True)
        for name in storage.FILES:
            (source / name).write_bytes(b'new candidate')
            (destination / name).write_bytes(b'previous live package')
        stage = self.root / leader.STAGE; stage.parent.mkdir(parents=True)
        stage.write_text(json.dumps({'schema': 1, 'files': {}}))
        leader.atomic(storage.policy_path(self.root, self.game), b'{"schema":1,"automatic":true}')
        env = {'ROOT': str(self.root), 'MOD_FILES': sorted(storage.FILES), 'MODS_REL': 'FFRS/Content/Paks/~mods',
               'os': os, 'json': json, 'time': SimpleNamespace(strftime=lambda _: '20261102_000008'),
               'game_running': lambda: False, 'game_paks': lambda: str(destination.parent),
               'ffrenv': SimpleNamespace(detect_game=lambda: str(self.game)),
               '_ffr_launch': SimpleNamespace(guard=lambda *args, **kwargs: None),
               '_ffr_field_leader': leader, '_ffr_storage': storage}
        exec(compile(ast.Module(body=methods, type_ignores=[]), 'pinned_storage_server', 'exec'), env)
        before = {p: p.read_bytes() for p in self.root.parent.rglob('*') if p.is_file()}
        with mock.patch.object(shutil, 'disk_usage', return_value=SimpleNamespace(free=0)):
            with self.assertRaisesRegex(RuntimeError, 'Not enough free space'):
                env['install_files']()
        self.assertEqual(before, {p: p.read_bytes() for p in self.root.parent.rglob('*') if p.is_file()})
        log = []
        env['install_files'](log.append)
        self.assertTrue(any('Backup cleanup: removed 4' in line for line in log))
        self.assertEqual(len(list((self.root / 'backups').iterdir())), 4)
        env['restore_game']()
        for name in storage.FILES: self.assertEqual((destination / name).read_bytes(), b'previous package')


if __name__ == '__main__': unittest.main()
