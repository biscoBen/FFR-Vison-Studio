"""Real supplied bytes, local game ownership, independent switching and rollback."""
import ast
import gzip
import hashlib
import json
import os
from pathlib import Path
import tempfile
import time
from types import SimpleNamespace
import unittest
from unittest import mock

from test_existing_visions import ROOT, installer
import _ffr_deck_sync as sync
import _ffr_minimap as radar
import _ffr_field_leader as leader


class TreasureRadarTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / 'engine'; self.root.mkdir()
        self.game = Path(self.temp.name) / 'game'
        marker = self.game / sync.MARKER; marker.parent.mkdir(parents=True); marker.write_bytes(b'game marker fixture')

    def snapshot(self):
        return {p.relative_to(self.game).as_posix(): p.read_bytes() for p in self.game.rglob('*') if p.is_file()}

    def test_original_bundle_has_exact_reviewed_package_hashes_and_no_executables(self):
        files = radar.bundle()
        self.assertEqual(sum(map(len, files.values())), 24658)
        self.assertEqual(set(files), {radar.NAME + ext for ext in ('.pak', '.ucas', '.utoc')})
        for name, raw in files.items(): self.assertEqual(hashlib.sha256(raw).hexdigest(), radar.HASHES[name])
        with mock.patch.dict(radar.HASHES, {radar.NAME + '.pak': '0'*64}):
            with self.assertRaisesRegex(ValueError, 'checksum'): radar.bundle()

    def test_switch_adds_radar_and_counter_then_removes_them_and_preserves_other_mods(self):
        other = self.game / (radar.PAKS + '~mods/another-mod.pak'); other.parent.mkdir(); other.write_bytes(b'keep')
        before = self.snapshot()
        value = radar.plan(self.root, self.game, True)
        self.assertEqual(self.snapshot(), before)
        radar.deploy(value)
        self.assertTrue(radar.status(self.game)['enabled'])
        self.assertEqual(len(radar.owned(self.root, self.game)['files']), 6)
        self.assertTrue(radar.status(self.game)['counterEnabled'])
        for name, raw in radar.bundle().items(): self.assertEqual((self.game / (radar.PAKS + '~mods/' + name)).read_bytes(), raw)
        radar.deploy(radar.plan(self.root, self.game, False))
        self.assertFalse(radar.status(self.game)['enabled']); self.assertEqual(self.snapshot(), before)

    def test_root_manual_install_is_detected_not_duplicated_and_not_claimed_on_restore(self):
        for name, raw in radar.bundle().items(): (self.game / radar.PAKS / name).write_bytes(raw)
        before = self.snapshot(); self.assertTrue(radar.status(self.game)['enabled'])
        self.assertFalse(radar.status(self.game)['counterEnabled'])
        radar.deploy(radar.plan(self.root, self.game, True))
        self.assertTrue(radar.status(self.game)['counterEnabled'])
        self.assertEqual(set(radar.owned(self.root, self.game)['files']),
                         {radar.PAKS + n for n in radar.COUNTER_HASHES})
        radar.deploy(radar.plan(self.root, self.game))
        self.assertEqual(self.snapshot(), before)
        # Explicitly switching OFF removes this exact known manually installed package too.
        radar.deploy(radar.plan(self.root, self.game, False))
        self.assertFalse(radar.status(self.game)['enabled'])

    def test_complete_partial_install_and_restore_only_the_files_studio_added(self):
        name, raw = next(iter(radar.bundle().items())); path = self.game / radar.PAKS / name; path.write_bytes(raw)
        before = self.snapshot(); self.assertTrue(radar.status(self.game)['partial'])
        radar.deploy(radar.plan(self.root, self.game, True))
        self.assertTrue(radar.status(self.game)['enabled'])
        self.assertEqual(len(radar.owned(self.root, self.game)['files']), 5)
        radar.deploy(radar.plan(self.root, self.game))
        self.assertEqual(self.snapshot(), before)

    def test_edited_package_preserved_and_conflict_detected_in_both_supported_folders(self):
        for folder in (radar.PAKS, radar.PAKS + '~mods/'):
            path = self.game / (folder + radar.NAME + '.pak'); path.parent.mkdir(exist_ok=True); path.write_bytes(b'other revision')
            before = self.snapshot()
            self.assertTrue(radar.status(self.game)['conflict'])
            for enabled in (True, False):
                with self.assertRaisesRegex(ValueError, 'Preserving'): radar.plan(self.root, self.game, enabled)
            self.assertEqual(self.snapshot(), before); path.unlink()
        radar.deploy(radar.plan(self.root, self.game, True))
        path = self.game / (radar.PAKS + '~mods/' + radar.NAME + '.pak'); path.write_bytes(b'edited after install')
        before = self.snapshot()
        with self.assertRaisesRegex(ValueError, 'Preserving'): radar.plan(self.root, self.game)
        self.assertEqual(self.snapshot(), before)

    def test_failed_ledger_write_rolls_back_all_three_files(self):
        before = self.snapshot(); value = radar.plan(self.root, self.game, True); atomic = sync.atomic
        def fail(path, raw):
            if path == value['state']: raise OSError('fixture disk failure')
            atomic(path, raw)
        with mock.patch.object(sync, 'atomic', side_effect=fail):
            with self.assertRaisesRegex(OSError, 'disk failure'): radar.deploy(value)
        self.assertEqual(self.snapshot(), before); self.assertFalse(value['state'].exists())

    def test_counter_hashes_and_edited_counter_are_preserved(self):
        counter = radar.counter_bundle()
        self.assertEqual(set(counter), set(radar.COUNTER_HASHES))
        for name, raw in counter.items():
            self.assertEqual(hashlib.sha256(raw).hexdigest(), radar.COUNTER_HASHES[name])
        radar.deploy(radar.plan(self.root, self.game, True))
        path = self.game / (radar.PAKS + '~mods/' + radar.COUNTER_NAME + '.ucas')
        path.write_bytes(b'other counter mod')
        before = self.snapshot()
        self.assertTrue(radar.status(self.game)['conflict'])
        for enabled in (None, False, True):
            with self.assertRaisesRegex(ValueError, 'Preserving'): radar.plan(self.root, self.game, enabled)
        self.assertEqual(self.snapshot(), before)

    def test_other_pc_folder_and_files_changed_after_preflight_remain_untouched(self):
        radar.deploy(radar.plan(self.root, self.game, True)); before = self.snapshot()
        other = self.game.with_name('second-game'); (other / sync.MARKER).parent.mkdir(parents=True)
        (other / sync.MARKER).write_bytes(b'second marker')
        radar.deploy(radar.plan(self.root, other))
        self.assertEqual(self.snapshot(), before)
        value = radar.plan(self.root, self.game, False)
        path = self.game / next(iter(value['changes'])); path.write_bytes(b'changed during operation')
        current = self.snapshot()
        with self.assertRaisesRegex(ValueError, 'changed during'): radar.deploy(value)
        self.assertEqual(self.snapshot(), current)

    def test_api_blocks_running_game_builds_and_stale_game_selection(self):
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        state = {'running': False}; running = [False]
        app = FastAPI(); radar.register(app, {'ROOT': self.root, 'state': state,
            'ffrenv': SimpleNamespace(game_root=lambda: str(self.game)), 'game_running': lambda: running[0]})
        with TestClient(app) as client:
            self.assertFalse(client.get('/api/minimap-treasure').json()['enabled'])
            def put(**kwargs): return client.put('/api/minimap-treasure', json={'game': str(self.game), 'enabled': True, **kwargs})
            before = self.snapshot(); self.assertEqual(put(game='old-game').status_code, 422)
            self.assertEqual(put(enabled=1).status_code, 422)
            running[0] = True; self.assertEqual(put().status_code, 422); running[0] = False
            state['running'] = True; self.assertEqual(put().status_code, 422); state['running'] = False
            self.assertEqual(self.snapshot(), before)
            self.assertTrue(put().json()['enabled'])
            self.assertFalse(put(enabled=False).json()['enabled'])

    def test_pinned_server_original_game_restore_removes_studio_radar_without_a_vision_mod(self):
        raw = gzip.decompress((ROOT / 'scripts/fixtures/existing_visions/server.py.gz').read_bytes())
        tree = ast.parse(installer.hook_server(raw))
        methods = [n for n in tree.body if isinstance(n, ast.FunctionDef)
                   and n.name in ('_game_state','_save_game_state','_game_root','restore_game')]
        radar.deploy(radar.plan(self.root, self.game, True))
        before = self.snapshot()
        env = {'ROOT': str(self.root), 'GAME_STATE': str(self.root/'game_state.json'), 'BACKUPS': str(self.root/'backups'),
            'MOD_FILES': [Path(p).name for p in sync.PAKS], 'MODS_REL': 'FFRS/Content/Paks/~mods', 'os': os, 'json': json, 'time': time,
            'game_running': lambda: False, 'game_paks': lambda: str(self.game / radar.PAKS),
            'ffrenv': SimpleNamespace(detect_game=lambda: str(self.game)), '_ffr_field_leader': leader}
        exec(compile(ast.Module(body=methods, type_ignores=[]), 'pinned_server', 'exec'), env)
        env['restore_game']()
        self.assertEqual(self.snapshot(), {sync.MARKER: before[sync.MARKER]})
        self.assertFalse(radar.ledger(self.root,self.game).exists())


if __name__ == '__main__': unittest.main()
