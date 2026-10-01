"""Offline regression tests; all mutations are limited to temporary fixtures."""
import copy
import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile
import types
import unittest
from unittest import mock

from verify_crystal_fina_bundle import verify

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
PAYLOAD = HERE.parent / 'assets/crystal_fina/engine/payload'
HELPER_SOURCE = (PAYLOAD / '_ffr_crystalfina.py').read_bytes()
helper = types.ModuleType('_ffr_crystalfina')
exec(compile(HELPER_SOURCE, str(PAYLOAD / '_ffr_crystalfina.py'), 'exec'), helper.__dict__)
REAL_PATCH = json.loads((HERE / 'fixtures/crystal_fina/roster_recipe.json').read_text(encoding='utf-8'))


class FreshBuildMaterialTests(unittest.TestCase):
    def test_shipped_bundle_manifest_matches_every_file(self):
        self.assertEqual(verify(), 16)

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='ffr-fina-helper-', dir=HERE)
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / 'engine'
        self.root.mkdir()
        self.private = self.root / helper.STATE
        self.private.mkdir()
        (self.root / 'tools').mkdir()
        (self.root / 'tools/_ffr_crystalfina.py').write_bytes(HELPER_SOURCE)
        self.hashes = {'_ffr_crystalfina.py': hashlib.sha256(HELPER_SOURCE).hexdigest()}
        for relative in helper.MATERIAL_FILES:
            target = self.private / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(PAYLOAD / relative, target)
            self.hashes[relative] = hashlib.sha256(target.read_bytes()).hexdigest()
        self.manifest = {'schema': 1, 'files': self.hashes}
        self.save_manifest()
        self.patch = copy.deepcopy(REAL_PATCH)
        self.out = self.root / 'build/visions_mod/assets'
        self.patch['outRoot'] = str(self.out)
        self.table = next(t for t in self.patch['tables'] if t.get('asset') == helper.TABLE)
        self.units = []
        for row in self.table['add']:
            uid = row['set']['ID']
            self.units.append({'id': uid, 'jp': row['row'], 'ffbe': {'source': 'CUSTOM' if uid == helper.VISION_ID else 'FFBE', 'id': helper.SPRITE_ID if uid == helper.VISION_ID else str(uid)}})
        self.fina = next(u for u in self.units if u['id'] == helper.VISION_ID)
        self.fina_row = next(r for r in self.table['add'] if r['set']['ID'] == helper.VISION_ID)

    def save_manifest(self):
        (self.private / 'manifest.json').write_text(json.dumps(self.manifest), encoding='utf-8')

    def grow_roster(self, count):
        used = {u['id'] for u in self.units}
        uid = 13500
        while len(self.units) < count:
            if uid not in used:
                name = 'Fixture Vision ' + str(uid)
                unit = {'id': uid, 'jp': name, 'ffbe': {'source': 'FFBE', 'id': str(uid)}}
                row = copy.deepcopy(self.table['add'][0])
                row['row'] = name
                for key, value in list(row['set'].items()):
                    row['set'][key] = value.replace('13500', str(uid)) if isinstance(value, str) else uid if key == 'ID' else value
                row['set']['untouchedFixtureField'] = {'nested': [uid, True, None]}
                self.units.append(unit)
                self.table['add'].append(row)
                used.add(uid)
            uid += 1

    def assert_prepare_rejected_without_mutation(self, message):
        before = copy.deepcopy(self.patch)
        with self.assertRaisesRegex(RuntimeError, message):
            helper.prepare(self.patch, self.units, self.root)
        self.assertEqual(before, self.patch)

    def test_four_unit_build_changes_only_finas_two_fields(self):
        self.grow_roster(4)
        expected = copy.deepcopy(self.patch)
        table = next(t for t in expected['tables'] if t.get('asset') == helper.TABLE)
        row = next(r for r in table['add'] if r['set']['ID'] == helper.VISION_ID)
        row['set']['animationAssetList[0].isVisionCharacter'] = False
        row['set']['animationAssetList[0].Material'] = helper.MATERIAL
        units_before = copy.deepcopy(self.units)
        helper.prepare(self.patch, self.units, self.root)
        self.assertEqual(expected, self.patch)
        self.assertEqual(units_before, self.units)

    def test_sixteen_unit_build_preserves_every_other_row_and_table(self):
        self.grow_roster(16)
        before = copy.deepcopy(self.patch)
        helper.prepare(self.patch, self.units, self.root)
        self.assertEqual(16, len(self.table['add']))
        actual = copy.deepcopy(self.patch)
        row = next(r for t in actual['tables'] if t.get('asset') == helper.TABLE for r in t['add'] if r['set']['ID'] == helper.VISION_ID)
        row['set'].pop('animationAssetList[0].Material')
        row['set'].pop('animationAssetList[0].isVisionCharacter')
        self.assertEqual(before, actual)

    def test_missing_fina_is_noop_even_without_patch_installation(self):
        units = [u for u in self.units if u['id'] != helper.VISION_ID]
        before = copy.deepcopy(self.patch)
        shutil.rmtree(self.private)
        helper.prepare(self.patch, units, self.root)
        helper.copy_material(self.root, self.out, units)
        self.assertEqual(before, self.patch)
        self.assertFalse(self.out.exists())

    def test_allocated_vision_id_receives_its_own_material(self):
        self.fina['id'] = 13514
        self.fina_row['set']['ID'] = 13514
        for key in ('animationAssetList[0].Ss6Project', 'animationAssetList[0].textureBaseColor'):
            self.fina_row['set'][key] = self.fina_row['set'][key].replace('13503', '13514')
        helper.prepare(self.patch, self.units, self.root)
        self.assertEqual(self.fina_row['set']['animationAssetList[0].Material'], helper.MATERIAL.replace('13503', '13514'))

    def test_lower_id_original_receives_transparency_without_permitting_low_custom_ids(self):
        self.fina['id'] = 13024
        self.fina_row['set']['ID'] = 13024
        for key in ('animationAssetList[0].Ss6Project', 'animationAssetList[0].textureBaseColor'):
            self.fina_row['set'][key] = self.fina_row['set'][key].replace('13503', '13024')
        self.assert_prepare_rejected_without_mutation('invalid game ID')
        self.fina['donor'] = 13024
        self.fina['native'] = {'version': 1, 'id': 13024, 'baseline': {'id': 13024}}
        helper.prepare(self.patch, self.units, self.root)
        self.assertEqual(self.fina_row['set']['animationAssetList[0].Material'], helper.MATERIAL.replace('13503', '13024'))
        self.assertIs(self.fina_row['set']['animationAssetList[0].isVisionCharacter'], False)
        self.fina['native']['baseline']['id'] = 13503
        self.assert_prepare_rejected_without_mutation('invalid game ID')

    def test_noncustom_source_fails_closed(self):
        self.fina['ffbe']['source'] = 'FFBE'
        self.assert_prepare_rejected_without_mutation('no longer a custom source')

    def test_duplicate_custom_sprite_fails_closed(self):
        second = copy.deepcopy(self.fina)
        second['id'] = 13514
        self.units.append(second)
        self.assert_prepare_rejected_without_mutation('multiple visions')

    def test_duplicate_id_fails_closed(self):
        self.units.append({'id': helper.VISION_ID, 'jp': 'Different unit', 'ffbe': {'id': '999'}})
        self.assert_prepare_rejected_without_mutation('duplicate vision ID')

    def test_base_sprite_id_is_supported(self):
        self.fina['ffbe']['base'] = self.fina['ffbe'].pop('id')
        helper.prepare(self.patch, self.units, self.root)
        self.assertEqual(helper.MATERIAL, self.fina_row['set']['animationAssetList[0].Material'])

    def test_mismatched_table_identity_fails_closed(self):
        self.fina_row['row'] = 'Unrelated Vision'
        self.assert_prepare_rejected_without_mutation('does not belong')

    def test_mismatched_sprite_or_texture_path_fails_closed(self):
        for field in ('animationAssetList[0].Ss6Project', 'animationAssetList[0].textureBaseColor'):
            with self.subTest(field=field):
                saved = self.fina_row['set'][field]
                self.fina_row['set'][field] = '/Game/Unrelated'
                self.assert_prepare_rejected_without_mutation('sprite/texture paths changed')
                self.fina_row['set'][field] = saved

    def test_missing_any_roster_row_fails_closed(self):
        self.table['add'].remove(next(r for r in self.table['add'] if r['set']['ID'] != helper.VISION_ID))
        self.assert_prepare_rejected_without_mutation('missing or duplicates vision')

    def test_duplicate_roster_row_fails_closed(self):
        self.table['add'].append(copy.deepcopy(self.table['add'][0]))
        self.assert_prepare_rejected_without_mutation('missing or duplicates vision')

    def test_missing_fina_row_fails_closed(self):
        self.table['add'].remove(self.fina_row)
        self.assert_prepare_rejected_without_mutation('missing or duplicates vision')

    def test_missing_and_duplicate_battle_tables_fail_closed(self):
        original = copy.deepcopy(self.patch['tables'])
        self.patch['tables'] = [t for t in original if t.get('asset') != helper.TABLE]
        self.assert_prepare_rejected_without_mutation('expected one freshly generated battle asset table')
        self.patch['tables'] = original + [copy.deepcopy(self.table)]
        self.assert_prepare_rejected_without_mutation('expected one freshly generated battle asset table')

    def test_output_layout_change_fails_closed(self):
        self.patch['outRoot'] = str(self.root / 'unexpected-output')
        self.assert_prepare_rejected_without_mutation('output location changed')
        with self.assertRaisesRegex(RuntimeError, 'output location changed'):
            helper.copy_material(self.root, self.root / 'unexpected-output', self.units)

    def test_copy_material_matches_hashes_and_never_copies_a_data_table(self):
        table_path = self.out / (helper.TABLE + '.uasset')
        table_path.parent.mkdir(parents=True)
        table_path.write_bytes(b'CURRENT COMPLETE ROSTER TABLE: must remain untouched')
        before = table_path.read_bytes()
        helper.copy_material(self.root, self.out, self.units)
        expected_files = {helper.TABLE + '.uasset'}
        for rel in helper.MATERIAL_FILES:
            output_rel = rel.removeprefix('material/')
            expected_files.add(output_rel)
            self.assertEqual(self.hashes[rel], hashlib.sha256((self.out / output_rel).read_bytes()).hexdigest())
        self.assertEqual(before, table_path.read_bytes())
        self.assertEqual(expected_files, {p.relative_to(self.out).as_posix() for p in self.out.rglob('*') if p.is_file()})
        helper.copy_material(self.root, self.out, self.units)  # identical output is safe
        self.assertEqual(before, table_path.read_bytes())

    def test_material_checksum_mismatch_fails_before_any_copy(self):
        (self.private / helper.MATERIAL_FILES[-1]).write_bytes(b'corrupt')
        self.assert_prepare_rejected_without_mutation('checksum mismatch')
        with self.assertRaisesRegex(RuntimeError, 'checksum mismatch'):
            helper.copy_material(self.root, self.out, self.units)
        self.assertFalse(self.out.exists())

    def test_helper_checksum_mismatch_fails_closed(self):
        (self.root / 'tools/_ffr_crystalfina.py').write_bytes(b'changed helper')
        self.assert_prepare_rejected_without_mutation('helper changed')

    def test_manifest_cannot_authorize_a_stale_data_table(self):
        self.hashes['material/' + helper.TABLE + '.uasset'] = '0' * 64
        self.save_manifest()
        self.assert_prepare_rejected_without_mutation('unsupported material manifest')

    def test_existing_different_material_fails_before_overwriting_anything(self):
        conflict = self.out / helper.MATERIAL_FILES[-1].removeprefix('material/')
        conflict.parent.mkdir(parents=True)
        conflict.write_bytes(b'different material')
        with self.assertRaisesRegex(RuntimeError, 'another asset already uses'):
            helper.copy_material(self.root, self.out, self.units)
        self.assertEqual(b'different material', conflict.read_bytes())
        self.assertFalse((self.out / helper.MATERIAL_FILES[0].removeprefix('material/')).exists())

    def test_each_old_overlay_component_blocks_prepare(self):
        game = self.root.parent / 'game'
        mods = game / 'FFRS/Content/Paks/~mods'
        mods.mkdir(parents=True)
        (self.root / 'config.json').write_text(json.dumps({'gameRoot': str(game)}), encoding='utf-8')
        for ext in ('.utoc', '.ucas', '.pak'):
            with self.subTest(ext=ext):
                old = mods / ('zzz_CrystalFina_AlphaFlagTest_999_P' + ext)
                old.write_bytes(b'old overlay marker')
                self.assert_prepare_rejected_without_mutation('old AlphaFlagTest_999_P overlay is still installed')
                old.unlink()

    def serializer(self, root, arguments):
        operation, source, output = arguments
        output = Path(output)
        if operation == 'tojson':
            view = self.serialized if source.endswith('13514.uasset') else json.loads((HERE / 'fixtures/crystal_fina/material.json').read_text())
            output.write_text(json.dumps(view), encoding='utf-8')
        else:
            self.serialized = json.loads(Path(source).read_text())
            output.write_bytes(b'serializer output fixture')
            output.with_suffix('.uexp').write_bytes((self.private / helper.MATERIAL_FILES[1]).read_bytes())

    def test_collision_material_retargets_texture_import_without_changing_shader_data(self):
        original = json.loads((HERE / 'fixtures/crystal_fina/material.json').read_text())
        with mock.patch.object(helper, 'run_asset_tool', side_effect=self.serializer):
            result = helper.retarget_material(self.root, helper.materials(self.root), 13514)
        helper.verify_material_view(self.serialized, 13514)
        self.assertEqual(original['Exports'][0]['Data'], self.serialized['Exports'][0]['Data'])
        self.assertEqual(original['Exports'][0]['Extras'], self.serialized['Exports'][0]['Extras'])
        self.assertEqual(result[0][1], helper.ASSET.replace('13503', '13514') + '.uasset')
        self.assertEqual(result[1][0].read_bytes(), (self.private / helper.MATERIAL_FILES[1]).read_bytes())

    def test_serializer_must_preserve_cooked_payload(self):
        def corrupt(root, arguments):
            self.serializer(root, arguments)
            if arguments[0] == 'fromjson':
                Path(arguments[2]).with_suffix('.uexp').write_bytes(b'changed shader')
        with mock.patch.object(helper, 'run_asset_tool', side_effect=corrupt):
            with self.assertRaisesRegex(RuntimeError, 'cooked material export payload'):
                helper.retarget_material(self.root, helper.materials(self.root), 13514)

    def test_serializer_must_target_the_allocated_texture(self):
        def wrong_texture(root, arguments):
            self.serializer(root, arguments)
            if arguments[0] == 'fromjson':
                for item in self.serialized['Imports']:
                    if item['ClassName'] == 'Texture2D': item['OuterIndex'] = -999
        with mock.patch.object(helper, 'run_asset_tool', side_effect=wrong_texture):
            with self.assertRaisesRegex(RuntimeError, 'texture import'):
                helper.retarget_material(self.root, helper.materials(self.root), 13514)


if __name__ == '__main__':
    unittest.main(verbosity=2)
