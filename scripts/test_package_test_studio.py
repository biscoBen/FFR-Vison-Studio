import json
from pathlib import Path
import tempfile
import unittest
import zipfile

from package_test_studio import package


class TestPackageTests(unittest.TestCase):
    def test_package_has_matching_metadata_and_complete_launcher(self):
        with tempfile.TemporaryDirectory() as directory:
            app = Path(directory) / 'app'
            app.mkdir()
            (app / 'FFR Vision Studio.exe').write_bytes(b'MZ fixture')
            (app / 'flutter_windows.dll').write_bytes(b'fixture runtime')
            output = Path(directory) / 'Sephira-Studio-Test.zip'
            metadata = package(app, output, 'a' * 40, 123)
            with zipfile.ZipFile(output) as archive:
                self.assertEqual(json.loads(archive.read('test-build.json')), metadata)
                for name in ['Start Studio Test.cmd', 'Launch Studio Test.ps1', 'Update Studio Test.ps1', 'Import Official Visions.ps1', 'App/FFR Vision Studio.exe']:
                    self.assertIn(name, archive.namelist())
                self.assertIn(b'\r\n', archive.read('Start Studio Test.cmd'))
                self.assertIn("Start Studio Test.sh", archive.namelist())
                self.assertIn("Studio Deck Launcher.py", archive.namelist())
                self.assertNotIn(b"\r\n", archive.read("Start Studio Test.sh"))
                self.assertEqual(archive.getinfo("Start Studio Test.sh").external_attr >> 16 & 0o777, 0o755)
                compile(archive.read("Studio Deck Launcher.py"), "packaged_deck_launcher", "exec")
                self.assertIn('Update my mod.sh', archive.namelist())
                self.assertNotIn(b'\r\n', archive.read('Update my mod.sh'))
                self.assertEqual(archive.getinfo('Update my mod.sh').external_attr >> 16 & 0o777, 0o755)
                self.assertEqual(archive.read('Deck Mod Sync.py'), (Path(__file__).resolve().parent.parent / 'assets/existing_visions/payload/_ffr_deck_sync.py').read_bytes())
                compile(archive.read('Deck Mod Sync.py'), 'standalone_deck_sync', 'exec')
                self.assertFalse(any(name.endswith(('deck-sync-settings.json', 'deck-settings.json')) for name in archive.namelist()))
                self.assertFalse(any(name.startswith('Studio Test Data/') for name in archive.namelist()))
            self.assertEqual(json.loads(output.with_suffix('.json').read_text()), metadata)
            with zipfile.ZipFile(output.parent / 'Resonance-Deck-Sync.zip') as deck:
                self.assertEqual(set(deck.namelist()), {'Update my mod.sh', 'Deck Mod Sync.py', 'Read me.txt', 'test-build.json'})
                self.assertEqual(json.loads(deck.read('test-build.json')), metadata)
                self.assertEqual(deck.read('Deck Mod Sync.py'), (Path(__file__).resolve().parent.parent / 'assets/existing_visions/payload/_ffr_deck_sync.py').read_bytes())
                self.assertEqual(deck.getinfo('Update my mod.sh').external_attr >> 16 & 0o777, 0o755)

    def test_master_cannot_be_packaged_as_a_branch_update(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'wrong.zip'
            with self.assertRaises(ValueError):
                package(Path(directory), output, 'a' * 40, 123, branch='master')
            self.assertFalse(output.exists())
