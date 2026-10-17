"""Exercise the read-only crash helper against a fake installation and Saved tree."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
HELPER = ROOT / 'scripts/reference/game-crash/Collect Resonance Crash.ps1'
PWSH = shutil.which('pwsh') or (str(Path('/tmp/ffr-pwsh/pwsh')) if Path('/tmp/ffr-pwsh/pwsh').is_file() else None)


@unittest.skipUnless(PWSH, 'PowerShell is required for the crash collector tests.')
class GameCrashCollectorTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.game = self.root / "Game & user's folder"
        self.binary = self.game / 'FFRS/Binaries/Win64'
        self.binary.mkdir(parents=True)
        self.local = self.root / 'Local AppData'
        self.local.mkdir()
        self.output = self.root / 'Downloads/FFR Mod'
        self.env = dict(os.environ, USERPROFILE=str(self.root), LOCALAPPDATA=str(self.local),
                        XDG_CACHE_HOME=str(self.root / 'cache'), XDG_CONFIG_HOME=str(self.root / 'config'),
                        XDG_DATA_HOME=str(self.root / 'data'))

    def write(self, path, text):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
        return path

    def run_helper(self, *, output=None, engine=None, success=True):
        args = [PWSH, '-NoLogo', '-NoProfile', '-File', str(HELPER), '-GamePath', str(self.game),
                '-OutputRoot', str(output or self.output), '-NoPrompt']
        if engine:
            args += ['-EnginePath', str(engine)]
        result = subprocess.run(args, capture_output=True, text=True, env=self.env, timeout=30)
        self.assertEqual(result.returncode, 0 if success else 1, result.stdout + result.stderr)
        return result

    def archive(self):
        path, = self.output.glob('*.zip')
        return zipfile.ZipFile(path)

    def digest_tree(self, root):
        return {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
                for p in root.rglob('*') if p.is_file()}

    def test_collects_crash_stacks_and_logs_without_changing_or_exporting_game_content(self):
        for saved in (self.game / 'FFRS/Saved', self.local / 'FFRS/Saved'):
            self.write(saved / 'Crashes/UECC-fixture/CrashContext.runtime-xml', '<ErrorMessage>Fatal access violation</ErrorMessage>')
            self.write(saved / 'Crashes/UECC-fixture/Diagnostics.txt', 'native stack')
            self.write(saved / 'Crashes/UECC-fixture/FFRS.log', 'crash log')
            self.write(saved / 'Crashes/UECC-fixture/minidump.dmp', 'private memory')
            self.write(saved / 'SaveGames/player.sav', 'private save')
            self.write(saved / 'Logs/FFRS.log', 'Fatal native function')
        self.write(self.binary / 'ue4ss/UE4SS.log', 'UE4SS access violation stack')
        self.write(self.binary / 'ue4ss/Mods/OtherMod/secret.txt', 'other mod private config')
        self.write(self.binary / 'ue4ss/Mods/OtherMod/enabled.txt', '')
        self.write(self.binary / 'ue4ss/Mods/FFRStudioFieldLeader/Scripts/main.lua', 'runtime fixture')
        self.write(self.binary / 'ue4ss/Mods/FFRStudioFieldLeader/Scripts/config.lua', 'private roster')
        self.write(self.binary / 'ue4ss/Mods/mods.txt', 'OtherMod : 1')
        self.write(self.binary / 'ue4ss/UE4SS.dll', 'native DLL')
        self.write(self.game / 'FFRS/Content/Paks/~mods/Studio.utoc', 'game content')
        before_game, before_local = self.digest_tree(self.game), self.digest_tree(self.local)
        self.run_helper()
        self.assertEqual(before_game, self.digest_tree(self.game))
        self.assertEqual(before_local, self.digest_tree(self.local))
        with self.archive() as z:
            report = json.loads(z.read('report.json').decode('utf-8-sig'))
            self.assertEqual(report['errors'], [])
            self.assertEqual(report['crashFolders'], 2)
            self.assertEqual(report['pakInventory'][0]['name'], 'Studio.utoc')
            self.assertTrue(next(m for m in report['mods'] if m['name'] == 'OtherMod')['enabledMarker'])
            names = z.namelist()
            self.assertEqual(sum(n.endswith('CrashContext.runtime-xml') for n in names), 2)
            self.assertTrue(any(b'UE4SS access violation stack' in z.read(n) for n in names))
            self.assertFalse(any(n.endswith(('.sav', '.dmp', '.dll', '.utoc', '.lua', 'secret.txt')) for n in names))

    def test_only_recent_reports_and_logs_are_read_and_large_logs_are_bounded(self):
        saved = self.local / 'FFRS/Saved'
        for i in range(5):
            p = self.write(saved / f'Crashes/UECC-{i}/CrashContext.runtime-xml', str(i))
            os.utime(p.parent, (1000 + i, 1000 + i))
            p = self.write(saved / f'Logs/FFRS-{i}.log', 'x' * (4194304 + 12) + f'TAIL-{i}')
            os.utime(p, (1000 + i, 1000 + i))
        self.run_helper()
        with self.archive() as z:
            report = json.loads(z.read('report.json').decode('utf-8-sig'))
            self.assertEqual(report['errors'], [])
            self.assertEqual(report['crashFolders'], 3)
            names = z.namelist()
            self.assertTrue(any('UECC-2/' in n for n in names))
            self.assertFalse(any('UECC-0/' in n or 'UECC-1/' in n for n in names))
            logs = [n for n in names if '/logs/' in n]
            self.assertEqual(len(logs), 2)
            for name in logs:
                data = z.read(name)
                self.assertEqual(len(data), 4194304)
                self.assertIn(data[-6:], (b'TAIL-3', b'TAIL-4'))
            self.assertEqual(sum(r['tailOnly'] for r in report['files']), 2)

    def test_missing_crash_folder_is_reported_and_does_not_require_a_loader(self):
        result = self.run_helper()
        self.assertIn('No Unreal crash folder', result.stdout)
        with self.archive() as z:
            self.assertEqual(z.namelist(), ['report.json'])
            report = json.loads(z.read('report.json').decode('utf-8-sig'))
            self.assertEqual(report['crashFolders'], 0)
            self.assertEqual(report['files'], [])
            self.assertTrue(all(not r['exists'] for r in report['runtime']))

    def test_engine_settings_are_allowlisted_and_config_is_only_used_for_game_detection(self):
        engine = self.root / 'Studio engine'
        self.write(engine / 'tools/make_vision_mod.py', '# fixture')
        self.write(engine / 'config.json', '{"secret": "do not collect"}')
        self.write(engine / 'mods/EstherTsukiko/testing.json', '{"surviveAtOne": true}')
        self.write(engine / 'mods/EstherTsukiko/ability-modes.json', '{"useNativeRepairs": true}')
        self.write(engine / 'mods/EstherTsukiko/units.json', '{"private roster": true}')
        self.run_helper(engine=engine)
        with self.archive() as z:
            self.assertTrue(any(n.endswith('testing.json') for n in z.namelist()))
            self.assertTrue(any(n.endswith('ability-modes.json') for n in z.namelist()))
            self.assertFalse(any(n.endswith(('config.json', 'units.json')) for n in z.namelist()))

    def test_output_inside_game_is_rejected_before_writing(self):
        output = self.game / 'Do not create'
        self.run_helper(output=output, success=False)
        self.assertFalse(output.exists())

    @unittest.skipIf(os.name == 'nt', 'Creating a Windows symlink requires extra privileges.')
    def test_linked_crash_report_is_not_followed(self):
        saved = self.local / 'FFRS/Saved'
        folder = saved / 'Crashes/UECC-fixture'
        folder.mkdir(parents=True)
        private = self.write(self.root / 'private.txt', 'do not collect')
        (folder / 'CrashContext.runtime-xml').symlink_to(private)
        self.run_helper()
        with self.archive() as z:
            report = json.loads(z.read('report.json').decode('utf-8-sig'))
            self.assertTrue(report['errors'])
            self.assertEqual(z.namelist(), ['report.json'])


if __name__ == '__main__':
    unittest.main()
