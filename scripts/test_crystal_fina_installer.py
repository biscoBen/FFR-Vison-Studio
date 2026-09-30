import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

HERE = Path(__file__).resolve().parent
loader = importlib.util.spec_from_file_location('installer', HERE.parent / 'assets/crystal_fina/engine/install_crystalfina.py')
installer = importlib.util.module_from_spec(loader)
loader.loader.exec_module(installer)
ORIGINAL = r'''import os, json
def main():
    install = True
    patch = {"legacyRoot": LEGACY.replace("\\", "/"), "outRoot": OUT.replace("\\", "/"), "tables": list(tables.values()), "objects": objects, "clones": clones}
    pp = os.path.join(BUILD, "patch.json")
    json.dump(patch, open(pp, "w"), indent=1)
    if os.path.isdir(OUT):
        import shutil; shutil.rmtree(OUT)
    generate_sprites()
    stage("Packing the mod" + (" and installing it" if install else ""))
    cmd = ffrenv.py(os.path.join(ROOT, "tools", "build_mod.py"), OUT, ffrenv.MOD_NAME) + (["--install"] if install else [])
    subprocess.run(cmd)
if __name__ == "__main__":
    main()
'''.replace('\n', '\r\n').encode('utf-8')


class InstallerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='crystalfina-test-', dir=HERE)
        self.root = Path(self.tmp.name)
        self.engine = self.root / 'Engine with spaces'
        self.p = installer.paths(self.engine)
        self.p['builder'].parent.mkdir(parents=True)
        self.p['builder'].write_bytes(ORIGINAL)
        self.roster = self.engine / 'mods/units.json'
        self.roster.parent.mkdir()
        self.roster.write_bytes(b'untouched roster')
        self.payload = self.root / 'payload'
        self.payload.mkdir()
        self.file_data = {'_ffr_crystalfina.py': b'def prepare(*args): pass\ndef copy_material(*args): pass\n',
                          'material/FFRS/Content/BP/Material.uasset': b'fake material fixture',
                          'material/FFRS/Content/BP/Material.uexp': b'fake export fixture'}
        for rel, value in self.file_data.items():
            p = self.payload / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(value)
        self.manifest = self.payload / 'manifest.json'
        self.write_manifest()

    def write_manifest(self):
        self.manifest.write_text(json.dumps({'schema': 1, 'files': {r: installer.digest(v) for r, v in self.file_data.items()}}), encoding='utf-8')

    def tearDown(self):
        self.assertEqual(self.roster.read_bytes(), b'untouched roster')
        self.tmp.cleanup()

    def apply(self):
        return installer.apply(self.engine, self.payload)

    def test_apply_restore_exact_and_idempotent(self):
        self.assertEqual(installer.inspect(self.engine)['status'], 'not-installed')
        self.apply()
        built = self.p['builder'].read_bytes()
        self.assertEqual(built.count(installer.MARKER.encode()), 2)
        self.assertIn(b'\r\n    import _ffr_crystalfina\r\n', built)
        self.assertLess(built.index(b'.prepare('), built.index(b'json.dump('))
        self.assertLess(built.index(b'shutil.rmtree'), built.index(b'.copy_material('))
        self.assertLess(built.index(b'.copy_material('), built.index(b'stage("Packing'))
        state = self.p['state'].read_bytes()
        self.assertFalse(self.apply()['changed'])
        self.assertEqual(self.p['state'].read_bytes(), state)
        self.assertEqual(installer.inspect(self.engine)['status'], 'active')
        installer.restore(self.engine)
        self.assertEqual(self.p['builder'].read_bytes(), ORIGINAL)
        self.assertFalse(self.p['helper'].exists())
        self.assertFalse((self.engine / '.ffr-crystalfina/material/FFRS/Content/BP/Material.uasset').exists())
        self.assertFalse(installer.restore(self.engine)['changed'])
        self.apply()
        self.assertEqual(self.p['builder'].read_bytes(), built)

    def test_updated_developer_file_reapplies_and_restores_new_version(self):
        self.apply()
        updated = ORIGINAL + b'# Developer v16\r\n'
        self.p['builder'].write_bytes(updated)
        self.apply()
        self.assertIn(b'Developer v16', self.p['builder'].read_bytes())
        self.assertEqual(len(list(self.p['backup_dir'].glob('*.original.py'))), 2)
        installer.restore(self.engine)
        self.assertEqual(self.p['builder'].read_bytes(), updated)

    def test_supported_engine_versions_and_required_serializer(self):
        for relative in ('tools/ffrenv.py', 'tools/devui/ffbe_catalog.py', 'bin/ffr-dt.exe'):
            path = self.engine / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b'layout fixture')
        version = self.engine / 'VERSION'
        for tag in ('1.0.0.15', '1.0.0.16', '1.1.0.0'):
            version.write_text(tag)
            installer.validate_engine(self.engine)
        for tag in ('1.0.0.14', '2.0.0.15', 'unknown'):
            version.write_text(tag)
            with self.assertRaises(installer.PatchError):
                installer.validate_engine(self.engine)
        version.write_text('1.0.0.15')
        (self.engine / 'bin/ffr-dt.exe').unlink()
        with self.assertRaisesRegex(installer.PatchError, 'missing bin/ffr-dt.exe'):
            installer.validate_engine(self.engine)

    def test_restore_after_update_never_downgrades(self):
        self.apply()
        updated = ORIGINAL + b'# Developer v16\r\n'
        self.p['builder'].write_bytes(updated)
        installer.restore(self.engine)
        self.assertEqual(self.p['builder'].read_bytes(), updated)

    def test_external_builder_edit_refuses_both_operations(self):
        self.apply()
        edited = self.p['builder'].read_bytes() + b'# personal edits\n'
        self.p['builder'].write_bytes(edited)
        for op in (self.apply, lambda: installer.restore(self.engine)):
            with self.assertRaises(installer.PatchError):
                op()
            self.assertEqual(self.p['builder'].read_bytes(), edited)

    def test_changed_upstream_shape_refused_without_writes(self):
        edited = ORIGINAL.replace(b'list(tables.values())', b'new_table_layout()')
        self.p['builder'].write_bytes(edited)
        with self.assertRaises(installer.PatchError):
            self.apply()
        self.assertEqual(self.p['builder'].read_bytes(), edited)
        self.assertFalse(self.p['state'].exists())

    def test_unowned_helper_refused(self):
        self.p['helper'].write_bytes(b'# unknown helper')
        with self.assertRaises(installer.PatchError):
            self.apply()
        self.assertEqual(self.p['builder'].read_bytes(), ORIGINAL)

    def test_managed_material_edits_refused(self):
        self.apply()
        material = self.engine / '.ffr-crystalfina/material/FFRS/Content/BP/Material.uasset'
        material.write_bytes(b'custom edit')
        self.assertEqual(installer.inspect(self.engine)['status'], 'payload-missing-or-modified')
        for op in (self.apply, lambda: installer.restore(self.engine)):
            with self.assertRaises(installer.PatchError):
                op()
        self.assertEqual(material.read_bytes(), b'custom edit')

    def test_missing_managed_file_repaired(self):
        self.apply()
        self.p['helper'].unlink()
        self.apply()
        self.assertEqual(installer.inspect(self.engine)['status'], 'active')

    def test_payload_corruption_refused(self):
        (self.payload / '_ffr_crystalfina.py').write_bytes(b'bad')
        with self.assertRaises(installer.PatchError):
            self.apply()
        self.assertEqual(self.p['builder'].read_bytes(), ORIGINAL)

    def test_manifest_traversal_refused(self):
        data = json.loads(self.manifest.read_text())
        data['files']['../outside.py'] = '0' * 64
        self.manifest.write_text(json.dumps(data))
        with self.assertRaises(installer.PatchError):
            self.apply()

    def test_failure_rolls_back_payload_state_and_builder(self):
        write = installer.atomic_write
        def fail_builder(path, data):
            if path == self.p['builder'] and installer.MARKER.encode() in data:
                raise OSError('Simulated sharing violation')
            return write(path, data)
        with mock.patch.object(installer, 'atomic_write', side_effect=fail_builder):
            with self.assertRaises(OSError):
                self.apply()
        self.assertEqual(self.p['builder'].read_bytes(), ORIGINAL)
        self.assertFalse(self.p['helper'].exists())
        self.assertFalse(self.p['state'].exists())

    def test_corrupt_backup_refuses_restore(self):
        result = self.apply()
        Path(result['backup']).write_bytes(b'corrupt')
        with self.assertRaises(installer.PatchError):
            installer.restore(self.engine)
        self.assertEqual(installer.inspect(self.engine)['status'], 'active')

    def test_concurrent_developer_update_is_not_overwritten(self):
        transact = installer.transact
        updated = ORIGINAL + b'# Concurrent upstream update\n'
        def update_before_write(changes, expected=None):
            self.p['builder'].write_bytes(updated)
            return transact(changes, expected)
        with mock.patch.object(installer, 'transact', side_effect=update_before_write):
            with self.assertRaises(installer.PatchError):
                self.apply()
        self.assertEqual(self.p['builder'].read_bytes(), updated)
        self.assertFalse(self.p['helper'].exists())

    def test_real_build15_source_supported(self):
        source = HERE / 'fixtures/crystal_fina/make_vision_mod.py'
        if not source.exists():
            self.skipTest('Local official engine fixture unavailable')
        raw = source.read_bytes()
        if installer.MARKER.encode() in raw:
            self.skipTest('Integration fixture already patched')
        built = installer.hook_builder(raw)
        self.assertEqual(built.count(installer.MARKER.encode()), 2)


if __name__ == '__main__':
    unittest.main(verbosity=2)
