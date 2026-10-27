"""Fresh-PC installation choices, real bundled core and owned rollback."""
import ast
import gzip
import hashlib
import json
import os
from pathlib import Path
import struct
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock
import zipfile

from test_existing_visions import ROOT, installer
from test_game_folder_install import PAYLOAD, files, working_loader
import _ffr_field_leader as leader
import _ffr_runtime_loader as runtime
import _ffr_deck_sync as sync


class RuntimeLoaderTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / 'engine'; self.root.mkdir()
        self.game = Path(self.temp.name) / 'game'; self.game.mkdir()

    def test_official_bundle_checksum_license_settings_and_64bit_binaries(self):
        path = ROOT / 'assets/existing_visions/payload/ue4ss_runtime.zip'
        self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), runtime.ARCHIVE_SHA256)
        with zipfile.ZipFile(path) as bundle:
            self.assertIn(b'Permission is hereby granted', bundle.read('ue4ss/LICENSE'))
            settings = bundle.read('ue4ss/UE4SS-settings.ini')
            self.assertIn(b'ConsoleEnabled = 0', settings)
            for name in runtime.CORE[:2]:
                data = bundle.read(name)
                self.assertEqual(data[:2], b'MZ')
                pe = struct.unpack_from('<I', data, 60)[0]
                self.assertEqual(data[pe:pe+4], b'PE\0\0')
                self.assertEqual(struct.unpack_from('<H', data, pe+4)[0], 0x8664)

    def test_bootstrap_is_opt_in_owned_and_removable_without_touching_other_mods(self):
        other = self.game / (sync.BINARY + 'ue4ss/Mods/OtherMod/Scripts/main.lua')
        other.parent.mkdir(parents=True); other.write_text('keep me')
        original = files(self.game)
        runtime.save_choice(self.root, self.game, 'install')
        plan = leader.install_plan(self.root, self.game, PAYLOAD)
        self.assertEqual(files(self.game), original)
        self.assertEqual(set(plan['loaderOwned']), {sync.BINARY + n for n in runtime.CORE})
        leader.deploy(plan)
        self.assertEqual((self.game / leader.REL / 'Scripts/main.lua').read_text(), PAYLOAD['files']['Scripts/main.lua'])
        self.assertEqual(set(files(self.game)), set(original) | set(plan['loaderOwned']) | set(sync.LEADER_FILES))
        self.assertTrue(runtime.status(self.root, self.game, [{'synchro': [[['PassiveSkill',1960,-1]]]}])['ready'])
        leader.deploy(leader.restore_plan(self.root, self.game))
        self.assertEqual(files(self.game), original)

    def test_existing_loader_is_preserved_and_never_claimed(self):
        working_loader(self.game); original = files(self.game)
        runtime.save_choice(self.root, self.game, 'install')
        plan = leader.install_plan(self.root, self.game, PAYLOAD)
        self.assertFalse(plan['loaderChanges']); self.assertFalse(plan['loaderOwned'])
        leader.deploy(plan); leader.deploy(leader.restore_plan(self.root, self.game))
        self.assertEqual(files(self.game), original)

    def test_choice_is_scoped_to_game_and_skip_can_later_enable_unchanged_build(self):
        other = self.game.with_name('another-game')
        runtime.save_choice(self.root, self.game, 'install')
        self.assertEqual(runtime.choice(self.root, other), 'skip')
        runtime.save_choice(self.root, self.game, 'skip')
        stage = self.root / leader.STAGE; stage.parent.mkdir(parents=True); stage.write_text(json.dumps(PAYLOAD))
        leader.deploy(leader.install_plan(self.root, self.game), log=lambda _: None)
        self.assertFalse(files(self.game))
        self.assertEqual(json.loads(stage.read_bytes()), PAYLOAD)
        state = runtime.status(self.root, self.game, [], last_build=True)
        self.assertTrue(state['required']); self.assertFalse(state['ready'])
        runtime.save_choice(self.root, self.game, 'install')
        leader.deploy(leader.install_plan(self.root, self.game))
        self.assertTrue((self.game / leader.REL / 'enabled.txt').exists())

    def test_corrupt_bundle_conflicts_and_failed_state_write_preserve_game(self):
        runtime.save_choice(self.root, self.game, 'install')
        with mock.patch.object(runtime, 'ARCHIVE_SHA256', '0'*64):
            with self.assertRaisesRegex(ValueError, 'checksum'): leader.install_plan(self.root, self.game, PAYLOAD)
        self.assertFalse(files(self.game))
        proxy = self.game / sync.LOADER_FILES[0]; proxy.parent.mkdir(parents=True); proxy.write_bytes(b'different proxy')
        with self.assertRaisesRegex(RuntimeError, 'Preserving a different runtime loader'):
            leader.install_plan(self.root, self.game, PAYLOAD)
        self.assertEqual(proxy.read_bytes(), b'different proxy'); proxy.unlink()
        plan = leader.install_plan(self.root, self.game, PAYLOAD); atomic = leader.atomic
        def fail(path, raw):
            if path == plan['state']: raise OSError('disk full')
            atomic(path, raw)
        with mock.patch.object(leader, 'atomic', side_effect=fail):
            with self.assertRaisesRegex(OSError, 'disk full'): leader.deploy(plan)
        self.assertFalse(files(self.game)); self.assertFalse(plan['state'].exists())

    def test_real_pinned_server_installs_assets_without_loader_then_enables_last_build(self):
        raw = gzip.decompress((ROOT / 'scripts/fixtures/existing_visions/server.py.gz').read_bytes())
        tree = ast.parse(installer.hook_server(raw))
        names = {'_game_state','_save_game_state','_game_root','install_files','restore_game'}
        methods = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in names]
        for name in sync.PAKS:
            path = self.root / 'build/out' / Path(name).name
            path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(b'compiled asset fixture')
        stage = self.root / leader.STAGE; stage.parent.mkdir(parents=True); stage.write_text(json.dumps(PAYLOAD))
        env = {'ROOT': str(self.root), 'GAME_STATE': str(self.root/'game_state.json'), 'BACKUPS': str(self.root/'backups'),
               'MOD_FILES': [Path(p).name for p in sync.PAKS], 'MODS_REL': 'FFRS/Content/Paks/~mods',
               'os': os, 'json': json, 'time': SimpleNamespace(strftime=lambda _: 'first'),
               'game_running': lambda: False, 'game_paks': lambda: str(self.game/'FFRS/Content/Paks'),
               'ffrenv': SimpleNamespace(detect_game=lambda: str(self.game)),
               '_ffr_launch': SimpleNamespace(guard=lambda *a, **k: None), '_ffr_field_leader': leader}
        exec(compile(ast.Module(body=methods, type_ignores=[]), 'pinned_server', 'exec'), env)
        log = []
        self.assertEqual(env['install_files'](log=log.append)['files'], 3)
        self.assertTrue(any(runtime.SKIPPED == line for line in log))
        self.assertEqual(set(files(self.game)), set(sync.PAKS))
        runtime.save_choice(self.root, self.game, 'install')
        self.assertEqual(env['install_files'](log=log.append)['reused'], 3)
        self.assertTrue((self.game / leader.REL / 'enabled.txt').exists())
        env['restore_game']()
        self.assertFalse(files(self.game))

    def test_api_rejects_stale_game_invalid_choices_and_choices_during_build(self):
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        state = {'running': False}
        app = FastAPI()
        runtime.register(app, {'ROOT': self.root, 'ffrenv': SimpleNamespace(game_root=lambda: str(self.game)),
                               'load_spec': lambda: [], 'state': state})
        with TestClient(app) as client:
            self.assertFalse(client.get('/api/runtime/status').json()['required'])
            self.assertEqual(client.post('/api/runtime/choice', json={'game': 'other', 'choice': 'install'}).status_code, 409)
            self.assertEqual(client.post('/api/runtime/choice', json={'game': str(self.game), 'choice': 'bad'}).status_code, 422)
            proxy = self.game / sync.LOADER_FILES[0]; proxy.parent.mkdir(parents=True); proxy.write_bytes(b'keep other proxy')
            self.assertEqual(client.post('/api/runtime/choice', json={'game': str(self.game), 'choice': 'install'}).status_code, 422)
            self.assertEqual(proxy.read_bytes(), b'keep other proxy')
            self.assertFalse(runtime.choice_path(self.root, self.game).exists()); proxy.unlink()
            self.assertEqual(client.post('/api/runtime/choice', json={'game': str(self.game), 'choice': 'install'}).status_code, 200)
            state['running'] = True
            self.assertEqual(client.post('/api/runtime/choice', json={'game': str(self.game), 'choice': 'skip'}).status_code, 409)
            self.assertEqual(runtime.choice(self.root, self.game), 'install')


if __name__ == '__main__': unittest.main()
