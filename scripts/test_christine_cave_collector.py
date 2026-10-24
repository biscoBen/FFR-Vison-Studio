"""Scoped native cave/music collection without prepare-game or installed mods."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile

from restore_reference_chunks import restore

ROOT = Path(__file__).resolve().parents[1]
FOLDER = ROOT / 'scripts/reference/christine-cave'
SCRIPT = FOLDER / 'Collect Christine Cave Reference.ps1'
PWSH = shutil.which('pwsh')
NAMES = [SCRIPT.name, 'Collect Christine Cave Reference.cmd', 'Read me.txt']


class DownloadTests(unittest.TestCase):
    def test_standalone_archive_matches_reviewed_sources(self):
        with zipfile.ZipFile(FOLDER / 'Christine-Cave-Reference.zip') as bundle:
            self.assertEqual(bundle.namelist(), NAMES)
            self.assertIsNone(bundle.testzip())
            for name in NAMES:
                self.assertEqual(bundle.read(name).decode('utf-8').replace('\r\n', '\n'),
                                 (FOLDER / name).read_text())


@unittest.skipUnless(PWSH and sys.platform != 'win32', 'PowerShell plus POSIX executable fixture required.')
class CollectorTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.engine = self.root / "Studio & user's directory/engine"
        self.game = self.root / "Full game & user's directory"
        self.paks = self.game / 'FFRS/Content/Paks'
        self.output = self.root / 'results'
        self.fixture = self.root / 'fixtures'
        self.level = 'FFRS/Content/Map/Dng/01Gra/01Gra_44/Dng_01Gra_44_PL.umap'
        self.music = 'FFRS/Content/Sound/Cri/Bgm/BGM_PP/BGM_PP_DUNGEON_CAVE1_Cue.uasset'
        self.write(self.fixture / self.level, b'native cave geometry')
        self.write(self.fixture / self.music, b'native cave music cue')
        self.write(self.fixture / 'FFRS/Content/BP/Map/Gimmick/BP_MapGimmick_EventTrigger.uasset', b'blueprint')
        for name in ('global.utoc', 'global.ucas', 'FFRS-Windows.utoc', 'FFRS-Windows.ucas',
                     'FFRS-Windows.pak', 'FFRS-Windows_1_P.utoc', 'FFRS-Windows_1_P.ucas'):
            self.write(self.paks / name, name.encode())
        self.write(self.paks / '~mods/unrelated.pak', b'private installed mod')
        self.write(self.paks / 'unrelated.utoc', b'private extra container')
        self.write(self.game / 'FFRS/Saved/SaveGames/private.sav', b'private save')
        self.write(self.engine / 'config.json', json.dumps({'gameRoot': str(self.game), 'secret': 'private'}).encode())
        self.write(self.engine / 'extracted/Mappings.usmap', b'mappings fixture')
        self.ret = self.engine / 'tools/retoc/retoc.exe'
        self.env = dict(os.environ, USERPROFILE=str(self.root),
                        XDG_CONFIG_HOME=str(self.root / 'config'), XDG_CACHE_HOME=str(self.root / 'cache'),
                        XDG_DATA_HOME=str(self.root / 'data'))
        self.set_retoc()

    def write(self, path, value):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(value)

    def set_retoc(self, failure=False):
        source = f'''#!{sys.executable}
import pathlib, shutil, sys
args=sys.argv[1:]
assert args[:2]==['to-legacy','--no-shaders']
filters=args[3:-2:2]
assert len(filters)==3
assert filters[-1]=='FFRS/Content/Sound/Cri/Bgm/BGM_PP/'
view=pathlib.Path(args[-2])
assert sorted(p.name for p in view.iterdir())=={sorted(p.name for p in self.paks.iterdir() if p.is_file() and p.name != 'unrelated.utoc')!r}
assert all(p.stat().st_ino == (pathlib.Path({str(self.paks)!r})/p.name).stat().st_ino for p in view.iterdir())
source=pathlib.Path({str(self.fixture)!r})
for p in source.rglob('*'):
 if p.is_file() and any(f in p.relative_to(source).as_posix() for f in filters):
  out=pathlib.Path(args[-1])/p.relative_to(source)
  out.parent.mkdir(parents=True,exist_ok=True)
  shutil.copyfile(p,out)
print('info: : Extracted 0 (398 failed)' if {failure!r} else 'info: : Extracted 3 (0 failed)')
'''
        self.write(self.ret, source.encode())
        self.ret.chmod(0o755)

    def digest(self, folder):
        return {p.relative_to(folder).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                for p in folder.rglob('*') if p.is_file()}

    def run_helper(self, success=True, *extra):
        before = self.digest(self.game), self.digest(self.engine)
        p = subprocess.run([PWSH, '-NoProfile', '-File', str(SCRIPT), '-EnginePath', str(self.engine),
                            '-OutputRoot', str(self.output), *extra], env=self.env,
                           text=True, capture_output=True, timeout=60)
        self.assertEqual(p.returncode, 0 if success else 1, p.stdout + p.stderr)
        self.assertEqual(before, (self.digest(self.game), self.digest(self.engine)))
        self.assertEqual(list((self.game / 'FFRS/Content').glob('StudioCaveReference-*')), [])
        return p

    def merged(self):
        destination = self.root / 'restored'
        archives = sorted(self.output.glob('*.zip'))
        self.assertTrue(archives)
        for archive in archives:
            self.assertLess(archive.stat().st_size, 25*1024*1024)
            with zipfile.ZipFile(archive) as z:
                self.assertIsNone(z.testzip())
                z.extractall(destination)
        restore(destination)
        return destination

    def test_collects_cave_music_and_global_patch_dependencies_without_prepare_or_mods(self):
        self.run_helper()
        dest = self.merged()
        self.assertEqual((dest / 'legacy' / self.level).read_bytes(), b'native cave geometry')
        self.assertEqual((dest / 'legacy' / self.music).read_bytes(), b'native cave music cue')
        report = json.loads((dest / 'reference.json').read_text(encoding='utf-8-sig'))
        self.assertEqual(report['musicCue'], 'BGM_PP_DUNGEON_CAVE1')
        self.assertTrue(any(c['name']=='global.utoc' for c in report['containers']))
        self.assertTrue(any(c['name']=='FFRS-Windows_1_P.utoc' for c in report['containers']))
        self.assertFalse(any(p.suffix in ('.pak','.ucas','.utoc','.sav') or p.name=='config.json' for p in dest.rglob('*')))
        self.assertNotIn('private', (dest / 'reference.json').read_text())

    def test_reports_failed_conversion_even_with_zero_exit_and_creates_no_success_zip(self):
        self.set_retoc(failure=True)
        p = self.run_helper(False)
        self.assertIn('Cave extraction failed', p.stdout)
        self.assertEqual(list(self.output.glob('*.zip')), [])

    def test_missing_level_or_mappings_creates_no_success_zip(self):
        (self.fixture / self.level).unlink()
        p = self.run_helper(False)
        self.assertIn('expected secret-cave level', p.stdout)
        self.write(self.fixture / self.level, b'cave')
        (self.engine / 'extracted/Mappings.usmap').unlink()
        p = self.run_helper(False)
        self.assertIn('mappings were not found', p.stdout)
        self.assertEqual(list(self.output.glob('*.zip')), [])

    def test_rejects_demo_before_extraction(self):
        p = self.run_helper(False, '-GamePath', str(self.root / 'FINAL FANTASY RESONANCE DEMO'))
        self.assertIn('still points to the demo', p.stdout)
        self.assertFalse(self.output.exists())

    def test_large_native_member_splits_and_restores_exactly(self):
        value = os.urandom(23*1024*1024)
        member = self.level.replace('_PL.umap', '_BG.uexp')
        self.write(self.fixture / member, value)
        self.run_helper()
        dest = self.merged()
        self.assertEqual((dest / 'legacy' / member).read_bytes(), value)
        self.assertGreaterEqual(len(list(self.output.glob('*.zip'))), 2)


if __name__ == '__main__':
    unittest.main()
