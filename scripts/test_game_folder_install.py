"""Switch PC installations without mixing runtime ownership or pak backups."""
import ast
import copy
import gzip
import hashlib
import json
import os
from pathlib import Path
import shutil
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock

from test_existing_visions import ROOT, installer
import _ffr_field_leader as leader
import _ffr_deck_sync as sync

PAYLOAD = {'schema': 1, 'files': {
    'enabled.txt': '', 'Scripts/config.lua': 'return {}', 'Scripts/main.lua': 'full-game runtime fixture'}}


def working_loader(game):
    for i, name in enumerate(sync.LOADER_FILES):
        path = game / name; path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(('loader fixture ' + str(i)).encode())
    signature = game / (sync.BINARY + 'ue4ss/UE4SS_Signatures/FakeSignature.lua')
    signature.parent.mkdir(parents=True); signature.write_text('fixture signature')
    other = game / (sync.BINARY + 'ue4ss/Mods/OtherMod/Scripts/main.lua')
    other.parent.mkdir(parents=True); other.write_text('do not transfer this mod')


def files(root):
    return {p.relative_to(root).as_posix(): p.read_bytes() for p in root.rglob('*') if p.is_file()}


class GameFolderInstallTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name); self.root = self.base / 'engine'
        self.demo = self.base / 'demo'; self.full = self.base / 'full'
        self.demo.mkdir(); self.full.mkdir(); self.root.mkdir()
        working_loader(self.demo)
        leader.deploy(leader.install_plan(self.root, self.demo, PAYLOAD))
        # Reproduce the released legacy ledger, before loader ownership existed.
        legacy = self.root / leader.STATE
        record = json.loads(legacy.read_bytes()); record.pop('loader', None)
        legacy.write_text(json.dumps(record))

    def test_switching_keeps_demo_ledger_and_loader_and_isolates_restores(self):
        before = files(self.demo); legacy = (self.root / leader.STATE).read_bytes()
        plan = leader.install_plan(self.root, self.full, PAYLOAD)
        self.assertFalse(files(self.full))  # Preflight does not change the game.
        self.assertNotEqual(plan['state'], self.root / leader.STATE)
        leader.deploy(plan, self.root / 'backups/same-stamp')
        self.assertEqual(files(self.demo), before)
        self.assertEqual((self.root / leader.STATE).read_bytes(), legacy)
        for name in sync.LOADER_FILES:
            self.assertEqual((self.full / name).read_bytes(), (self.demo / name).read_bytes())
        signature = sync.BINARY + 'ue4ss/UE4SS_Signatures/FakeSignature.lua'
        self.assertEqual((self.full / signature).read_text(), 'fixture signature')
        self.assertFalse((self.full / (sync.BINARY + 'ue4ss/Mods/OtherMod')).exists())
        full_record = json.loads(plan['state'].read_bytes())
        self.assertEqual(len(full_record['loader']), len(sync.LOADER_FILES) + 1)
        leader.deploy(leader.restore_plan(self.root, self.full))
        self.assertFalse(files(self.full))
        self.assertEqual(files(self.demo), before)
        self.assertEqual(leader.install_plan(self.root, self.demo, PAYLOAD)['state'], self.root / leader.STATE)

    def test_existing_loader_in_new_game_is_preserved_and_never_claimed(self):
        working_loader(self.full)
        dll = self.full / sync.LOADER_FILES[0]; dll.write_bytes(b'different existing full-game loader')
        before = files(self.full)
        leader.deploy(leader.install_plan(self.root, self.full, PAYLOAD))
        leader.deploy(leader.restore_plan(self.root, self.full))
        self.assertEqual(files(self.full), before)

    def test_different_partial_loader_blocks_copy_before_any_changes(self):
        dll = self.full / sync.LOADER_FILES[0]; dll.parent.mkdir(parents=True)
        dll.write_bytes(b'keep this different proxy')
        before = files(self.base)
        with self.assertRaisesRegex(RuntimeError, 'Preserving a different runtime loader'):
            leader.install_plan(self.root, self.full, PAYLOAD)
        self.assertEqual(files(self.base), before)

    def test_disable_on_new_game_needs_no_loader_and_keeps_demo_enabled(self):
        before = files(self.demo)
        leader.deploy(leader.install_plan(self.root, self.full, {'schema': 1, 'files': {}}))
        self.assertFalse(files(self.full))
        self.assertEqual(files(self.demo), before)

    def test_failed_state_write_removes_new_loader_and_runtime_and_preserves_demo(self):
        before = files(self.demo); legacy = (self.root / leader.STATE).read_bytes()
        plan = leader.install_plan(self.root, self.full, PAYLOAD)
        atomic = leader.atomic
        def failing(path, raw):
            if path == plan['state']: raise OSError('fixture state write failed')
            atomic(path, raw)
        with mock.patch.object(leader, 'atomic', side_effect=failing):
            with self.assertRaisesRegex(OSError, 'fixture state write failed'): leader.deploy(plan)
        self.assertFalse(files(self.full))
        self.assertFalse(plan['state'].exists())
        self.assertEqual(files(self.demo), before)
        self.assertEqual((self.root / leader.STATE).read_bytes(), legacy)

    def test_loader_changed_after_preflight_is_preserved(self):
        plan = leader.install_plan(self.root, self.full, PAYLOAD)
        path = self.full / sync.LOADER_FILES[0]; path.parent.mkdir(parents=True)
        path.write_bytes(b'installed after preflight')
        with self.assertRaisesRegex(RuntimeError, 'loader changed during installation'): leader.deploy(plan)
        self.assertEqual(files(self.full), {sync.LOADER_FILES[0]: b'installed after preflight'})

    def test_copied_loader_edit_blocks_restore_without_deleting_anything(self):
        leader.deploy(leader.install_plan(self.root, self.full, PAYLOAD))
        (self.full / sync.LOADER_FILES[0]).write_bytes(b'user-edited loader')
        before = files(self.full)
        with self.assertRaisesRegex(RuntimeError, 'Preserving an edited Studio loader'):
            leader.restore_plan(self.root, self.full)
        self.assertEqual(files(self.full), before)

    def test_runtime_backups_cannot_cross_game_folders(self):
        leader.deploy(leader.install_plan(self.root, self.full, PAYLOAD), self.root / 'backups/stamp')
        path = leader.runtime_backup(self.root, self.full, 'stamp')
        value = json.loads(path.read_bytes()); value['game'] = str(self.demo)
        path.write_text(json.dumps(value))
        before = files(self.full)
        with self.assertRaisesRegex(RuntimeError, 'another game folder'):
            leader.restore_plan(self.root, self.full, 'stamp')
        self.assertEqual(files(self.full), before)

    def test_real_server_install_and_restore_keep_legacy_demo_and_full_game_backups_separate(self):
        # Unmodified source from the checksum-pinned engine 1.0.0.15; no game assets.
        raw = gzip.decompress((ROOT / 'scripts/fixtures/existing_visions/server.py.gz').read_bytes())
        self.assertEqual(hashlib.sha256(raw).hexdigest(), '258b3269e51dddc49ef4ef0d37ce3caa7f9b2704f53443b8d0a35747ad61044f')
        hooked = ast.parse(installer.hook_server(raw))
        names = {'_game_state', '_save_game_state', '_game_root', 'install_files', 'restore_game', 'game_files'}
        methods = [n for n in hooked.body if isinstance(n, ast.FunctionDef) and n.name in names]
        self.assertEqual(len(methods), len(names))
        selected = [self.full]
        mod_names = [Path(p).name for p in sync.PAKS]
        for i, name in enumerate(mod_names):
            source = self.root / 'build/out' / name; source.parent.mkdir(parents=True, exist_ok=True)
            source.write_bytes(('new mod ' + str(i)).encode())
        full_old = self.full / sync.PAKS[0]; full_old.parent.mkdir(parents=True)
        full_old.write_bytes(b'full game previous pak')
        untouched = full_old.parent / 'someone-else.pak'; untouched.write_bytes(b'keep unrelated mod')
        demo_mod = self.demo / sync.PAKS[0]; demo_mod.parent.mkdir(parents=True)
        demo_mod.write_bytes(b'demo mod')
        old_backup = self.root / 'backups/same-stamp' / mod_names[0]
        old_backup.parent.mkdir(parents=True); old_backup.write_bytes(b'demo original pak')
        state = {'placed': [sync.PAKS[0]], 'original': {sync.PAKS[0]: 'same-stamp/' + mod_names[0]},
                 'createdModsDir': False, 'installs': [{'game': str(self.demo), 'time': 'same-stamp'}]}
        legacy = self.root / 'game_state.json'; legacy.write_text(json.dumps(state))
        stage = self.root / leader.STAGE; stage.parent.mkdir(parents=True, exist_ok=True)
        stage.write_text(json.dumps(PAYLOAD))
        previous = files(self.demo); legacy_bytes = legacy.read_bytes()
        env = {'ROOT': str(self.root), 'GAME_STATE': str(legacy), 'BACKUPS': str(self.root / 'backups'),
               'MOD_FILES': mod_names, 'MODS_REL': 'FFRS/Content/Paks/~mods',
               'os': os, 'json': json, 'time': SimpleNamespace(strftime=lambda _: 'same-stamp'),
               'game_running': lambda: False, 'game_paks': lambda: str(selected[0] / 'FFRS/Content/Paks'),
               'ffrenv': SimpleNamespace(detect_game=lambda: str(selected[0])),
               '_ffr_launch': SimpleNamespace(guard=lambda *a, **k: None), '_ffr_field_leader': leader}
        exec(compile(ast.Module(body=methods, type_ignores=[]), 'pinned_install_server', 'exec'), env)
        original_copy = shutil.copy2
        def select_demo_during_copy(source, target, *args, **kwargs):
            result = original_copy(source, target, *args, **kwargs)
            if Path(target) == self.full / sync.PAKS[-1]: selected[0] = self.demo
            return result
        with mock.patch.object(shutil, 'copy2', side_effect=select_demo_during_copy):
            self.assertEqual(env['install_files']()['files'], 3)
        self.assertEqual(selected[0], self.demo)
        self.assertEqual(files(self.demo), previous)
        self.assertEqual(legacy.read_bytes(), legacy_bytes)
        self.assertEqual(old_backup.read_bytes(), b'demo original pak')
        selected[0] = self.full
        current = env['game_files']()
        self.assertEqual(current['record']['installs'][-1]['game'], str(self.full))
        self.assertEqual([v['id'] for v in current['backups']], ['same-stamp'])
        actual_backup = Path(leader.backup_root(self.root, self.full)) / 'same-stamp' / mod_names[0]
        self.assertEqual(actual_backup.read_bytes(), b'full game previous pak')
        # A repeated installation compares actual bytes and retains the prior
        # complete backup rather than replacing it with this same build.
        snapshot=files(self.full)
        result=env['install_files']()
        self.assertEqual(result['reused'],3)
        self.assertEqual(files(self.full),snapshot)
        self.assertEqual(actual_backup.read_bytes(), b'full game previous pak')
        env['restore_game']()
        self.assertEqual(full_old.read_bytes(), b'full game previous pak')
        self.assertEqual(untouched.read_bytes(), b'keep unrelated mod')
        self.assertFalse((self.full / sync.PAKS[1]).exists())
        self.assertFalse((self.full / sync.LOADER_FILES[0]).exists())
        self.assertEqual(files(self.demo), previous)
        selected[0] = self.demo
        self.assertEqual(env['game_files']()['record'], state)
        env['restore_game']()
        self.assertEqual(demo_mod.read_bytes(), b'demo original pak')
        self.assertEqual(full_old.read_bytes(), b'full game previous pak')


if __name__ == '__main__': unittest.main()
