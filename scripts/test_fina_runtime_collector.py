"""Run the standalone Fina collector against isolated full-game/Studio fixtures."""
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
HELPER = ROOT / 'scripts/reference/crystal-fina-battle/Collect Fina Runtime Diagnostics.ps1'
PWSH = shutil.which('pwsh')


class FinaRuntimeDownloadTests(unittest.TestCase):
    def test_standalone_zip_matches_the_collector_sources(self):
        folder = HELPER.parent
        names = ['Collect Fina Runtime Diagnostics.cmd', 'Collect Fina Runtime Diagnostics.ps1',
                 'Runtime Diagnostics README.txt']
        with zipfile.ZipFile(folder / 'Crystal-Fina-Full-Game-Diagnostics.zip') as archive:
            self.assertEqual(archive.namelist(), names)
            self.assertIsNone(archive.testzip())
            for name in names:
                self.assertEqual(archive.read(name).decode('utf-8').replace('\r\n', '\n'),
                                 (folder / name).read_text(encoding='utf-8'))


@unittest.skipUnless(PWSH, 'PowerShell is required for Fina collector checks.')
class FinaRuntimeCollectorTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.game = self.root / 'Steam/steamapps/common/FINAL FANTASY RESONANCE'
        self.binary = self.game / 'FFRS/Binaries/Win64'
        self.binary.mkdir(parents=True)
        self.engine = self.root / 'Desktop/Sephira-Studio-Test/Studio Test Data/FFR Vision Studio/engine'
        self.write(self.engine / 'tools/make_vision_mod.py', '# engine fixture')
        self.write(self.engine / 'config.json', json.dumps({'gameRoot': str(self.game), 'private': 'do not export'}))
        self.output = self.root / 'results'
        self.env = dict(os.environ, USERPROFILE=str(self.root), LOCALAPPDATA=str(self.root / 'Local'),
                        XDG_CACHE_HOME=str(self.root / 'cache'), XDG_CONFIG_HOME=str(self.root / 'config'),
                        XDG_DATA_HOME=str(self.root / 'data'))
        # Keep discovery isolated from a developer's actual Steam installation.
        self.env['ProgramFiles(x86)'] = str(self.root / 'Program Files (x86)')

    def write(self, path, value):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(value)
        return path

    def run_helper(self, *args, success=True):
        result = subprocess.run([PWSH, '-NoLogo', '-NoProfile', '-File', str(HELPER),
                                 '-OutputRoot', str(self.output), '-NoPrompt', *args],
                                capture_output=True, text=True, env=self.env, timeout=30)
        self.assertEqual(result.returncode, 0 if success else 1, result.stdout + result.stderr)
        return result

    def archive(self):
        path, = self.output.glob('*.zip')
        return zipfile.ZipFile(path)

    def digest_tree(self, path):
        return {str(p.relative_to(path)): hashlib.sha256(p.read_bytes()).hexdigest()
                for p in path.rglob('*') if p.is_file()}

    def test_desktop_studio_selects_full_game_and_collects_only_runtime_files(self):
        self.write(self.binary / 'ue4ss/UE4SS.log', 'FFR Fina runtime error fixture')
        self.write(self.binary / 'ue4ss/Mods/FFRStudioFieldLeader/Scripts/config.lua', 'fina config fixture')
        self.write(self.binary / 'ue4ss/UE4SS.dll', 'hash only')
        self.write(self.game / 'FFRS/Saved/SaveGames/player.sav', 'do not export')
        self.write(self.engine / 'mods/EstherTsukiko/units.json', 'private roster')
        key = os.path.normcase(str(self.game.resolve()))
        ledger = 'game-installs/' + hashlib.sha256(key.encode()).hexdigest() + '/field-leader-state.json'
        self.write(self.engine / ledger, '{"selected": true}')
        self.write(self.engine / 'field-leader-state.json', '{"oldDemo": true}')
        self.write(self.engine / 'build/crystal-fina-battle/runtime.json', '{"fina": true}')
        before_game, before_engine = self.digest_tree(self.game), self.digest_tree(self.engine)
        result = self.run_helper()
        self.assertIn('Full game: ', result.stdout)
        self.assertEqual(before_game, self.digest_tree(self.game))
        self.assertEqual(before_engine, self.digest_tree(self.engine))
        with self.archive() as z:
            report = json.loads(z.read('report.json').decode('utf-8-sig'))
            self.assertEqual(report['gameEdition'], 'full')
            self.assertTrue(os.path.samefile(report['game'], self.game))
            self.assertTrue(os.path.samefile(report['engine'], self.engine))
            self.assertEqual(report['errors'], [])
            self.assertEqual(z.read('engine/' + ledger), b'{"selected": true}')
            self.assertNotIn('engine/field-leader-state.json', z.namelist())
            self.assertTrue(any(n.endswith('runtime.json') for n in z.namelist()))
            self.assertIn(b'FFR Fina runtime error fixture', z.read('fina-log-summary.txt'))
            self.assertFalse(any(n.endswith(('.sav', '.dll', 'units.json', 'config.json')) for n in z.namelist()))

    def test_demo_setting_is_ignored_in_favor_of_full_game_steam_library(self):
        demo = self.root / 'FINAL FANTASY RESONANCE DEMO'
        (demo / 'FFRS/Binaries/Win64').mkdir(parents=True)
        self.write(self.engine / 'config.json', json.dumps({'gameRoot': str(demo)}))
        library = self.root / "Second library & player's folder"
        full_game = library / 'steamapps/common/FINAL FANTASY RESONANCE'
        (full_game / 'FFRS/Binaries/Win64').mkdir(parents=True)
        vdf_path = str(library).replace('\\', '\\\\')
        self.write(Path(self.env['ProgramFiles(x86)']) / 'Steam/steamapps/libraryfolders.vdf',
                   '"libraryfolders" { "0" { "path" "' + vdf_path + '" } }')
        self.run_helper()
        with self.archive() as z:
            report = json.loads(z.read('report.json').decode('utf-8-sig'))
            self.assertTrue(os.path.samefile(report['game'], full_game))

    def test_explicit_demo_is_rejected_before_creating_output(self):
        demo = self.root / 'FINAL FANTASY RESONANCE DEMO'
        (demo / 'FFRS/Binaries/Win64').mkdir(parents=True)
        result = self.run_helper('-GamePath', str(demo), success=False)
        self.assertIn('not the demo', result.stdout)
        self.assertFalse(self.output.exists())

    def test_explicit_paths_support_other_studio_locations_and_legacy_record(self):
        other = self.root / "Other & user's Studio/engine"
        self.write(other / 'tools/make_vision_mod.py', '# engine fixture')
        self.write(other / 'field-leader-state.json', '{"legacy": true}')
        self.run_helper('-GamePath', str(self.binary), '-EnginePath', str(other.parent))
        with self.archive() as z:
            self.assertEqual(z.read('engine/field-leader-state.json'), b'{"legacy": true}')
            report = json.loads(z.read('report.json').decode('utf-8-sig'))
            self.assertTrue(os.path.samefile(report['game'], self.game))
            self.assertTrue(os.path.samefile(report['engine'], other))

    def test_output_inside_game_is_rejected_without_writing(self):
        self.output = self.game / 'do not create'
        self.run_helper(success=False)
        self.assertFalse(self.output.exists())


if __name__ == '__main__':
    unittest.main()
