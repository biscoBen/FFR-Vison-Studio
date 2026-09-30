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
                for name in ['Start Studio Test.cmd', 'Launch Studio Test.ps1', 'Update Studio Test.ps1', 'App/FFR Vision Studio.exe']:
                    self.assertIn(name, archive.namelist())
                self.assertIn(b'\r\n', archive.read('Start Studio Test.cmd'))
                self.assertFalse(any(name.startswith('Studio Test Data/') for name in archive.namelist()))
            self.assertEqual(json.loads(output.with_suffix('.json').read_text()), metadata)

    def test_master_cannot_be_packaged_as_a_branch_update(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'wrong.zip'
            with self.assertRaises(ValueError):
                package(Path(directory), output, 'a' * 40, 123, branch='master')
            self.assertFalse(output.exists())
