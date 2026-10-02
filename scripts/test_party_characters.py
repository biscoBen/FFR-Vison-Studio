"""Party-only replacements: identity, exact hard references and output isolation."""
import copy
import ast
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from types import SimpleNamespace
from unittest import mock
from test_existing_visions import ROOT, party, animation, installer, fina_installer


def original_view():
    imports = []; rows = []; names = ['/Script/CoreUObject', '/Script/Engine', '/Script/SpriteStudio6',
                                       'Package', 'Texture2D', 'Ss6Project', 'Material', 'Ss6Project',
                                       'textureBaseColor', 'textureNormal', 'textureMetallicRoughness', 'BTL_PLAYABLE_UNIT_ASSET']
    def reference(path, kind):
        start = len(imports); leaf = path.rsplit('/', 1)[1]
        imports.extend([{'$type': 'UAssetAPI.Import, UAssetAPI', 'ObjectName': path,
                         'ClassPackage': '/Script/CoreUObject', 'ClassName': 'Package', 'OuterIndex': 0,
                         'PackageName': None, 'bImportOptional': False},
                        {'$type': 'UAssetAPI.Import, UAssetAPI', 'ObjectName': leaf,
                         'ClassPackage': '/Script/Engine' if kind != 'Ss6Project' else '/Script/SpriteStudio6',
                         'ClassName': kind, 'OuterIndex': -start-1, 'PackageName': None, 'bImportOptional': False}])
        names.extend([path, leaf]); return -start-2
    common = reference('/Game/Material/Battle', 'Material')
    for id, jp, en, pack in party.CHARACTERS:
        props = []
        for field, suffix, kind in [('Ss6Project', '', 'Ss6Project'), ('textureBaseColor', '_tex', 'Texture2D'),
                                    ('textureNormal', '_normal', 'Texture2D'), ('textureMetallicRoughness', '_mreo', 'Texture2D')]:
            props.append({'$type': 'UAssetAPI.PropertyTypes.Objects.ObjectPropertyData, UAssetAPI',
                          'Name': field, 'Value': reference(f'/Game/Chara/unit/{pack}/{pack}{suffix}', kind)})
        props.append({'$type': 'UAssetAPI.PropertyTypes.Objects.ObjectPropertyData, UAssetAPI', 'Name': 'Material', 'Value': common})
        names.append(jp)
        rows.append({'$type': 'UAssetAPI.PropertyTypes.Structs.StructPropertyData, UAssetAPI',
                     'Name': jp, 'StructType': 'BTL_PLAYABLE_UNIT_ASSET', 'Value': props})
    # The real serializer resolves export ancestry through the DataTable class.
    class_start = len(imports)
    imports.extend([{'$type': 'UAssetAPI.Import, UAssetAPI', 'ObjectName': '/Script/Engine',
                     'OuterIndex': 0, 'ClassName': 'Package', 'ClassPackage': '/Script/CoreUObject',
                     'PackageName': None, 'bImportOptional': False},
                    {'$type': 'UAssetAPI.Import, UAssetAPI', 'ObjectName': 'DataTable',
                     'OuterIndex': -class_start-1, 'ClassName': 'Class', 'ClassPackage': '/Script/CoreUObject',
                     'PackageName': None, 'bImportOptional': False}])
    names.extend(['DT_BtlPlayableUnitAsset', 'DataTable', 'Class'])
    return {'NameMap': list(dict.fromkeys(names)), 'Imports': imports,
            'Exports': [{'$type': 'UAssetAPI.ExportTypes.DataTableExport, UAssetAPI',
                         'ObjectName': 'DT_BtlPlayableUnitAsset', 'ClassIndex': -class_start-2, 'Data': [],
                         'Table': {'$type': 'UAssetAPI.ExportTypes.UDataTable, UAssetAPI', 'Data': rows},
                         'SerializationBeforeSerializationDependencies': []}]}


def unit(id=1001, form='401001207'):
    c = party.identity(id)
    return {'key': f'party_{id}', 'id': id, 'jp': c[1], 'en': c[2],
            'party': {'version': 1, 'id': id}, 'ffbe': {'id': form, 'dir': 'units/ffbe/a2'}}


class PartyCharacterTests(unittest.TestCase):
    def test_saved_roster_loader_keeps_party_specs_sparse_and_converts_vision_skills(self):
        source = (ROOT / 'scripts/fixtures/crystal_fina/make_vision_mod.py').read_bytes()
        patched = installer.hook_builder(fina_installer.hook_builder(source))
        loader = next(n for n in ast.parse(patched).body if isinstance(n, ast.FunctionDef) and n.name == 'load_units')
        rows = lambda rel: {c[1]: {'Ss6Project': c[3]} for c in party.CHARACTERS}
        originals = [party.snapshot(c[0], rows) for c in party.CHARACTERS]
        replacements = [unit(c[0]) for c in party.CHARACTERS]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'units.json'
            env = {'os': __import__('os'), 'json': json, 'SPEC_JSON': str(path), 'UNITS': []}
            exec(compile(ast.Module(body=[loader], type_ignores=[]), 'installed_roster_loader', 'exec'), env)
            for selected in (originals, replacements):
                vision = {'id': 13501, 'skills': {'446100': {'en': 'Custom'}}}
                saved = [*selected, vision]; path.write_text(json.dumps(saved))
                loaded = env['load_units']()
                self.assertEqual(loaded[:-1], selected)
                self.assertEqual(loaded[-1]['skills'], {446100: {'en': 'Custom'}})
                actual, others = party.split(loaded, rows)
                self.assertEqual(actual, selected); self.assertEqual(others, [loaded[-1]])
                self.assertEqual(json.loads(path.read_text()), saved)

    def test_original_party_portraits_cover_all_eight_with_verified_png_bytes(self):
        root = ROOT / 'assets/party_portraits'
        manifest = json.loads((root / 'manifest.json').read_bytes())
        self.assertEqual({(p['characterId'], p['characterName']) for p in manifest['portraits']},
                         {(c[0], c[2]) for c in party.CHARACTERS})
        for p in manifest['portraits']:
            data = (root / p['file']).read_bytes()
            self.assertEqual(hashlib.sha256(data).hexdigest(), p['sha256'])
            self.assertTrue(data.startswith(b'\x89PNG\r\n\x1a\n'))

    def test_all_eight_originals_keep_identity_and_do_not_enter_vision_builder(self):
        rows = lambda rel: {c[1]: {'Ss6Project': c[3]} for c in party.CHARACTERS}
        catalog = [party.snapshot(c[0], rows) for c in party.CHARACTERS]
        added = {'id': 13501, 'key': 'a2'}; native = {'id': 13110, 'native': {}}
        before = copy.deepcopy(catalog)
        selected, others = party.split([added, *catalog, native], rows)
        self.assertEqual(selected, before); self.assertEqual(others, [added, native])
        self.assertTrue(all('stats' not in u and 'awakening' not in u for u in selected))
        with self.assertRaises(ValueError): party.split([catalog[0], copy.deepcopy(catalog[0])], rows)

    def test_invalid_identity_paths_and_unsupported_edits_fail_before_build(self):
        for field, value in [('key', 'a2'), ('id', 13110), ('en', 'A2'), ('stats', {'Attack': 999})]:
            u = unit(); u[field] = value
            with self.subTest(field=field), self.assertRaises(ValueError): party.validate(u)
        for path in ('../x', 'units/../outside', '/tmp/sprites', 'units/dir/../../x', 'units/C:/x'):
            u = unit(); u['ffbe']['dir'] = path
            with self.subTest(path=path), self.assertRaises(ValueError): party.validate(u)

    def test_private_references_preserve_native_pack_names_and_all_other_rows(self):
        original = original_view(); before = copy.deepcopy(original)
        for c in party.CHARACTERS:
            chosen = unit(c[0]); edited = party.table_view(original, [chosen]); party.check_table(original, edited, [chosen])
            self.assertEqual(edited['Exports'], original['Exports'])
            expected = f'/Game/Chara/StudioParty/party{c[0]}/{c[3]}'
            self.assertTrue(any(i['ObjectName'] == expected for i in edited['Imports']))
            self.assertEqual(sum(a != b for a, b in zip(edited['Imports'], original['Imports'])), 4)
        all_units = [unit(c[0]) for c in party.CHARACTERS]
        party.check_table(original, party.table_view(original, all_units), all_units)
        self.assertEqual(original, before)

    def test_crystal_fina_material_is_assigned_only_to_selected_row(self):
        original = original_view(); chosen = unit(form=party.FINA)
        edited = party.table_view(original, [chosen]); party.check_table(original, edited, [chosen])
        a, b = original['Exports'][0]['Table']['Data'], edited['Exports'][0]['Table']['Data']
        self.assertEqual(a[1:], b[1:]); self.assertNotEqual(a[0], b[0])
        material = next(p for p in b[0]['Value'] if p['Name'] == 'Material')['Value']
        self.assertEqual(edited['Imports'][-material-1]['ObjectName'], 'M_StudioParty1001')
        self.assertEqual(edited['Imports'][-material-1]['ClassName'], 'Material')

    def test_verifier_rejects_other_rows_and_wrong_hard_reference_paths(self):
        original = original_view(); chosen = unit(); edited = party.table_view(original, [chosen])
        wrong = copy.deepcopy(edited); wrong['Imports'][0]['ObjectName'] = '/Wrong'
        with self.assertRaises(ValueError): party.check_table(original, wrong, [chosen])
        wrong = copy.deepcopy(edited); wrong['Exports'][0]['Table']['Data'][1]['Value'][0]['Value'] = 0
        with self.assertRaises(ValueError): party.check_table(original, wrong, [chosen])

    def test_mixture_has_separate_hold_and_return_without_extra_hits(self):
        spec = {'animations': [{'name': 'attack_B', 'frameCount': 6,
                                'parts': {'part_0': {'Cell': [[0, 'a'], [2, 'b'], [5, 'c']]}}}]}
        party.party_motions(spec)
        hold, reverse = spec['animations'][1:]
        self.assertEqual(hold['parts']['part_0']['Cell'], [[0, 'c']])
        self.assertEqual(reverse['parts']['part_0']['Cell'], [[0, 'c'], [1, 'b'], [4, 'a']])
        self.assertEqual(hold['frameCount'], 1); self.assertEqual(reverse['frameCount'], 6)
        party.party_motions(spec); self.assertEqual(len(spec['animations']), 3)

    def test_generator_only_emits_private_battle_assets(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); u = unit(); calls = []
            templates = root / 'legacy/FFRS/Content/Chara/summon/summon13110'
            templates.mkdir(parents=True)
            for suffix in ('', '_tex', '_normal', '_mreo'):
                for ext in ('.uasset', '.uexp'): (templates / ('summon13110' + suffix + ext)).write_bytes(b'fixture')
            def run(args):
                calls.append(args)
                if '_ffr_build_sprites.py' in args[0]:
                    battle = root / 'build/sprites/party_1001/battle'; battle.mkdir(parents=True)
                    (battle / 'spec.json').write_text(json.dumps({'pixelSize': [32, 32], 'animations': []}))
            env = {'ROOT': str(root), 'LEGACY': str(root / 'legacy'), 'OUT': str(root / 'out'),
                   'FFRDT': ['real-tool'], 'USMAP': 'fixture.usmap', 'run': run,
                   'ffrenv': SimpleNamespace(py=lambda *args: list(args))}
            with mock.patch.dict('sys.modules', {'_ffr_animation_repair': animation}), mock.patch.object(animation, 'repair_unit'):
                party.generate(u, env)
            self.assertIn('--battle-only', calls[0]); self.assertEqual(len(calls), 5)
            spec = json.loads((root / 'build/sprites/party_1001/battle/spec.json').read_bytes())
            self.assertEqual(spec['animePackName'], 'unit0010')
            self.assertTrue(all('StudioParty/party1001' in str(args) for args in calls[1:]))
            self.assertTrue(all('/Chara/menu/' not in str(args) and '/Chara/unit/' not in str(args) for args in calls))


if __name__ == '__main__': unittest.main()
