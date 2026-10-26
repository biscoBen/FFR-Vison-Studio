"""Save collection is byte-exact and does not touch the source save or roster."""
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
FOLDER = ROOT / 'scripts/reference/vision-save'
PWSH = os.environ.get('FFR_TEST_PWSH') or shutil.which('pwsh')


class PackageTests(unittest.TestCase):
    def test_download_matches_sources(self):
        with zipfile.ZipFile(FOLDER / 'Vision-Save-Check.zip') as archive:
            self.assertEqual(set(archive.namelist()), {'Collect Vision Save Check.cmd', 'Collect Vision Save Check.ps1', 'README.txt'})
            for name in archive.namelist():
                self.assertEqual(archive.read(name).decode().replace('\r\n', '\n'), (FOLDER / name).read_text())


@unittest.skipUnless(PWSH, 'PowerShell required')
class CollectorTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.saves = self.root / "User's Local/FFRS/Saved/SaveGames"
        self.saves.mkdir(parents=True)
        self.studio = self.root / "Studio & user's folder"
        self.roster = self.studio / 'engine/mods/EstherTsukiko/units.json'
        self.roster.parent.mkdir(parents=True)
        self.roster.write_bytes(b'[{"id":13500,"en":"Crystal Fina"}]')
        self.first = self.saves / 'SAVE00.sav'
        self.first.write_bytes(b'GVAS\0' + bytes(range(256)))
        self.output = self.root / 'results'
        self.env = dict(os.environ, LOCALAPPDATA=str(self.root / "User's Local"), USERPROFILE=str(self.root),
                        XDG_CACHE_HOME=str(self.root / 'cache'), XDG_CONFIG_HOME=str(self.root / 'config'),
                        XDG_DATA_HOME=str(self.root / 'data'))

    def run_helper(self, *args):
        return subprocess.run([PWSH, '-NoLogo', '-NoProfile', '-File', str(FOLDER / 'Collect Vision Save Check.ps1'),
                               '-StudioPath', str(self.studio), '-OutputRoot', str(self.output), '-NoPrompt', *args],
                              env=self.env, capture_output=True, text=True, timeout=30)

    def test_automatic_discovery_copies_saves_and_roster_without_other_files(self):
        nested = self.saves / 'Profile'; nested.mkdir()
        (nested / 'auto.sav').write_bytes(b'opaque automatic save')
        (nested / 'account.ini').write_text('not for collection')
        before = {p: (p.read_bytes(), p.stat().st_mtime_ns) for p in (self.first, nested / 'auto.sav', self.roster)}
        result = self.run_helper()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        with zipfile.ZipFile(next(self.output.glob('*.zip'))) as archive:
            names = {n.replace('\\', '/'): n for n in archive.namelist()}
            report = json.loads(archive.read(names['report.json']).decode('utf-8-sig'))
            self.assertEqual(report['saveCount'], 2)
            for entry in report['files']:
                raw = archive.read(names[entry['file']])
                self.assertEqual(hashlib.sha256(raw).hexdigest(), entry['sha256'])
            self.assertEqual(archive.read(names['roster/units.json']), self.roster.read_bytes())
            self.assertEqual({archive.read(n) for k, n in names.items() if k.startswith('saves/')}, {v[0] for p, v in before.items() if p != self.roster})
            self.assertFalse(any(n.endswith('.ini') for n in names))
        self.assertEqual({p: (p.read_bytes(), p.stat().st_mtime_ns) for p in before}, before)

    def test_explicit_single_slot_and_missing_save_do_not_claim_an_audit(self):
        (self.saves / 'other.sav').write_bytes(b'other slot')
        result = self.run_helper('-SavePath', str(self.first))
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        with zipfile.ZipFile(next(self.output.glob('*.zip'))) as archive:
            self.assertEqual(len([n for n in archive.namelist() if n.replace('\\', '/').startswith('saves/')]), 1)
        result = self.run_helper('-SavePath', str(self.root / 'missing.sav'))
        self.assertEqual(result.returncode, 1)
        self.assertIn('No save files found', result.stdout)

    def test_refuses_output_under_sources(self):
        self.output = self.saves / 'results'
        result = self.run_helper()
        self.assertEqual(result.returncode, 1)
        self.assertFalse(self.output.exists())


if __name__ == '__main__':
    unittest.main()
