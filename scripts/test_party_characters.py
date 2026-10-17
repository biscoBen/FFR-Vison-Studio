"""Party-only replacements: identity, exact hard references and output isolation."""
import copy
import ast
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
import sys
from types import SimpleNamespace
from unittest import mock
from test_existing_visions import ROOT, party, animation, installer, fina_installer


def battle_rows():
    result = {}
    for id, jp, en, pack in party.CHARACTERS:
        path = f'/Game/Chara/unit/{pack}/{pack}'
        result[jp] = {'ID': id, 'animationAssetList': [{'isVisionCharacter': False, 'Ss6Project': path,
            'Material': '/Game/BP/Map/Unit/Material/CharaPBR/M_Ss_Component_PBRBattle',
            'textureBaseColor': path + '_tex', 'textureNormal': path + '_normal', 'textureMetallicRoughness': path + '_mreo'}],
            'shadowScale': 1.0, 'Footstep': 'Common'}
    return result


def original_view(selected=()):
    """Synthetic runtime soft-reference layout, matching DT_BtlUnitAsset."""
    values = battle_rows(); names = ['None', '0', 'ID', 'animationAssetList', 'isVisionCharacter', 'Ss6Project',
        'textureBaseColor', 'textureNormal', 'textureMetallicRoughness', 'Material', 'UNIT_ASSET_DATA',
        'UNIT_ANIMATION_ASSET_DATA', '/Script/Engine', '/Script/CoreUObject', 'Package', 'Class', 'DataTable', 'DT_BtlUnitAsset']
    for u in selected:
        for path, value in party.asset_updates(u).items(): values[u['jp']]['animationAssetList'][0][path.split('.')[-1]] = value
    table = []
    for jp, row in values.items():
        props = []
        for field, value in row['animationAssetList'][0].items():
            if isinstance(value, bool):
                props.append({'$type': 'UAssetAPI.PropertyTypes.Objects.BoolPropertyData, UAssetAPI', 'Name': field, 'Value': value})
                continue
            leaf = value.rsplit('/', 1)[-1]; names.extend([value, leaf])
            props.append({'$type': 'UAssetAPI.PropertyTypes.Objects.SoftObjectPropertyData, UAssetAPI', 'Name': field,
                'Value': {'$type': 'UAssetAPI.PropertyTypes.Objects.FSoftObjectPath, UAssetAPI',
                    'AssetPath': {'$type': 'UAssetAPI.PropertyTypes.Objects.FTopLevelAssetPath, UAssetAPI',
                        'PackageName': value, 'AssetName': leaf}, 'SubPathString': None}})
        names.append(jp)
        table.append({'$type': 'UAssetAPI.PropertyTypes.Structs.StructPropertyData, UAssetAPI',
            'Name': jp, 'StructType': 'UNIT_ASSET_DATA', 'Value': [
                {'$type': 'UAssetAPI.PropertyTypes.Objects.IntPropertyData, UAssetAPI', 'Name': 'ID', 'Value': row['ID']},
                {'$type': 'UAssetAPI.PropertyTypes.Objects.ArrayPropertyData, UAssetAPI', 'Name': 'animationAssetList',
                    'ArrayType': 'StructProperty', 'Value': [
                        {'$type': 'UAssetAPI.PropertyTypes.Structs.StructPropertyData, UAssetAPI',
                            'Name': '0', 'StructType': 'UNIT_ANIMATION_ASSET_DATA', 'Value': props}]}]})
    imports = [
        {'$type': 'UAssetAPI.Import, UAssetAPI', 'ObjectName': '/Script/Engine', 'OuterIndex': 0,
         'ClassName': 'Package', 'ClassPackage': '/Script/CoreUObject', 'PackageName': None, 'bImportOptional': False},
        {'$type': 'UAssetAPI.Import, UAssetAPI', 'ObjectName': 'DataTable', 'OuterIndex': -1,
         'ClassName': 'Class', 'ClassPackage': '/Script/CoreUObject', 'PackageName': None, 'bImportOptional': False}]
    return {'NameMap': list(dict.fromkeys(names)), 'Imports': imports,
        'Exports': [{'$type': 'UAssetAPI.ExportTypes.DataTableExport, UAssetAPI', 'ObjectName': 'DT_BtlUnitAsset',
            'ClassIndex': -2, 'Data': [], 'Table': {'$type': 'UAssetAPI.ExportTypes.UDataTable, UAssetAPI', 'Data': table}}]}


def unit(id=1001, form='401001207'):
    c = party.identity(id)
    return {'key': f'party_{id}', 'id': id, 'jp': c[1], 'en': c[2],
            'party': {'version': 1, 'id': id}, 'ffbe': {'id': form, 'dir': 'units/ffbe/a2'}}


def knockout_spec():
    """Distinct standing, wounded and fallen cells, with an animated fall."""
    return {'animations': [
        {'name': 'idle', 'fps': 60, 'frameCount': 12,
         'parts': {'part_0': {'Cell': [[0, 'standing']]}}},
        {'name': 'dying', 'fps': 60, 'frameCount': 4,
         'parts': {'part_0': {'Cell': [[0, 'kneeling']]}}},
        {'name': 'dead', 'fps': 60, 'frameCount': 9,
         'parts': {'part_0': {'Cell': [[0, 'falling'], [3, 'fallen']],
                              'Posx': [[0, -2.0]], 'Posy': [[0, 5.0]], 'Hide': [[0, 0.0]]}}}]}


class PartyCharacterTests(unittest.TestCase):
    def test_native_knockout_names_keep_fall_and_final_pose_without_changing_recovery(self):
        spec = knockout_spec(); original = copy.deepcopy(spec['animations'])
        party.party_motions(spec)
        motions = {a['name']: a for a in spec['animations']}
        for name in ('death', 'reverse_death'):
            clip = motions[name]
            self.assertEqual(clip['parts']['part_0']['Cell'], [[0, 'falling'], [3, 'fallen']])
            self.assertEqual(clip['parts']['part_0']['Posx'], [[0, -2.0]])
            self.assertEqual(clip['parts']['part_0']['Posy'], [[0, 5.0]])
            self.assertEqual((clip['fps'], clip['frameCount']), (60, 9))
        self.assertEqual(motions['reverse_dying']['parts']['part_0']['Cell'], [[0, 'kneeling']])
        self.assertEqual(spec['animations'][:3], original)  # idle still restores the standing pose.
        before = copy.deepcopy(spec); party.party_motions(spec); self.assertEqual(spec, before)
        motions['death']['parts']['part_0']['Cell'][-1][1] = 'edited'
        self.assertEqual(motions['dead']['parts']['part_0']['Cell'][-1][1], 'fallen')
        self.assertEqual(motions['reverse_death']['parts']['part_0']['Cell'][-1][1], 'fallen')

    def test_missing_source_motion_stops_generation_instead_of_adding_an_invalid_alias(self):
        for name in ('dead', 'dying'):
            spec = knockout_spec(); spec['animations'] = [a for a in spec['animations'] if a['name'] != name]
            with self.subTest(name=name), self.assertRaisesRegex(ValueError, name): party.party_motions(spec)

    def test_converter_uses_selected_or_base_knockout_artwork_with_native_party_names(self):
        from PIL import Image
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); tools = root / 'tools'; frames = tools / 'ffbe2ss6'; frames.mkdir(parents=True)
            for name in ('ffbe_frames.py', 'build_sprites.py'):
                shutil.copyfile(ROOT / 'scripts/fixtures/engine_motion' / name, frames / name)
            for name in ('_ffr_animation_repair.py', '_ffr_build_sprites.py', '_ffr_ability_modes.py'):
                shutil.copyfile(ROOT / 'assets/existing_visions/payload' / name, tools / name)
            main, base = root / 'main', root / 'base'
            for folder, form in ((main, '100030727'), (base, '100030717')):
                folder.mkdir(); Image.new('RGBA', (2, 1), (200, 0, 0, 255)).save(folder / f'unit_anime_{form}.png')
                (folder / f'unit_cgg_{form}.csv').write_text('0,1,0,0,0,0,100,0,0,0,1,1,0\n0,1,0,0,0,0,100,0,1,0,1,1,0\n')
                (folder / f'unit_idle_cgs_{form}.csv').write_text('0,0,0,12\n')
                (folder / f'unit_dying_cgs_{form}.csv').write_text('0,0,0,4\n')
                (folder / f'unit_dead_cgs_{form}.csv').write_text('1,-2,5,4\n')
            for base_fallback in (False, True):
                if base_fallback: (main / 'unit_dead_cgs_100030727.csv').unlink()
                output = root / str(base_fallback)
                args = [sys.executable, str(tools / '_ffr_build_sprites.py'), str(main), '100030727', '1002',
                        str(output), '--battle-only', '--base', str(base), '100030717']
                result = subprocess.run(args, capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                spec = json.loads((output / 'battle/spec.json').read_bytes()); party.party_motions(spec)
                motions = {a['name']: a for a in spec['animations']}
                for name in ('death', 'reverse_death'):
                    body = motions[name]['parts']['part_0']
                    self.assertEqual(body['Cell'], [[0, 'summon1002_b1' if base_fallback else 'summon1002_1']])
                    self.assertEqual(body['Posx'], [[0, -2.0]])
                    self.assertEqual(body['Posy'], [[0, -5.0]])
                    self.assertEqual(motions[name]['frameCount'], 4)
                self.assertEqual(motions['idle']['parts']['part_0']['Cell'], [[0, 'summon1002_0']])

    def test_native_voice_selection_for_all_64_pairs_changes_only_battle_label(self):
        original = {jp: {'ID': id, 'SaveId': id, 'BattleVoiceLabel': party.voice_label(id),
                         'FaceIconId': id, 'stats': {'Attack': 50}} for id, jp, _, _ in party.CHARACTERS}
        banks = {'VO_BTL_' + party.voice_label(id)[:-1]: {
            'CueSheetName': 'VO_BTL_' + party.voice_label(id),
            'pCueSheet': f'/Game/Sound/Cri/Voice/VO_BTL/VO_BTL_{party.voice_label(id)}/VO_BTL_{party.voice_label(id)}'}
            for id, _, _, _ in party.CHARACTERS}
        def rows(rel): return copy.deepcopy(banks if rel == party.VOICE_BANK_TABLE else original)
        for target, _, _, _ in party.CHARACTERS:
            for source, _, _, _ in party.CHARACTERS:
                with self.subTest(target=target, source=source):
                    chosen = unit(target); chosen.pop('ffbe'); chosen['battleVoice'] = source
                    before = copy.deepcopy(chosen); tables = {}
                    party.prepare(tables, [chosen], rows)
                    built = copy.deepcopy(original)
                    if source != target:
                        self.assertEqual(set(tables), {party.VOICE_TABLE})
                        self.assertEqual(tables[party.VOICE_TABLE]['add'], [])
                        self.assertEqual(tables[party.VOICE_TABLE]['set'],
                            [{'row': chosen['jp'], 'set': {'BattleVoiceLabel': party.voice_label(source)}}])
                        built[chosen['jp']]['BattleVoiceLabel'] = party.voice_label(source)
                    else: self.assertEqual(tables, {})
                    party.check_voice_rows(original, built, [chosen])
                    bad = copy.deepcopy(built); bad[chosen['jp']]['SaveId'] = 9999
                    with self.assertRaises(ValueError): party.check_voice_rows(original, bad, [chosen])
                    self.assertEqual(chosen, before)

    def test_voice_validation_and_missing_native_routes_stop_before_patching(self):
        for source in [None, True, 1002.0, '1002', 999, 1009, {}, []]:
            chosen = unit(); chosen['battleVoice'] = source
            with self.subTest(source=source), self.assertRaises(ValueError): party.validate(chosen)
        chosen = unit(1002); chosen.pop('ffbe'); chosen['battleVoice'] = 1008
        params = {jp: {'ID': id, 'BattleVoiceLabel': party.voice_label(id)} for id, jp, _, _ in party.CHARACTERS}
        for missing in ['label', 'bank']:
            def rows(rel):
                values = copy.deepcopy(params)
                if rel == party.VOICE_BANK_TABLE: return {}
                if missing == 'label': values[chosen['jp']]['BattleVoiceLabel'] = 'unexpected'
                return values
            tables = {}
            with self.assertRaisesRegex(ValueError, 'battle voice'): party.prepare(tables, [chosen], rows)
            self.assertEqual(tables, {})

    def test_verifier_accepts_only_the_saved_voice_override(self):
        chosen = unit(1002); chosen.pop('ffbe'); chosen['battleVoice'] = 1008
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); spec = root / 'mods/EstherTsukiko/units.json'; spec.parent.mkdir(parents=True)
            spec.write_text(json.dumps([chosen]))
            from test_existing_visions import native
            with mock.patch.dict(sys.modules, {'_ffr_animation_repair': animation}):
                expected = native.expected_edits(root)
            self.assertEqual(expected[(party.VOICE_TABLE, chosen['jp'])], {'BattleVoiceLabel': 'CHR0080'})
            original = {'ID': 1002, 'BattleVoiceLabel': 'CHR0020', 'SaveId': 1002}
            built = {**original, 'BattleVoiceLabel': 'CHR0080'}
            equivalent = lambda a, b: a == b
            self.assertTrue(native.expected_row_change(party.VOICE_TABLE, chosen['jp'], original, built, expected, equivalent))
            self.assertFalse(native.expected_row_change(party.VOICE_TABLE, chosen['jp'], original, {**built, 'SaveId': 1008}, expected, equivalent))

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

    def test_runtime_paths_preserve_all_existing_vision_operations_and_native_pack_names(self):
        original = battle_rows(); before = copy.deepcopy(original)
        for c in party.CHARACTERS:
            chosen = unit(c[0]); tables = {party.TABLE: {'asset': party.ASSET,
                'add': [{'row': 'A2', 'set': {'ID': 13501}}], 'set': [{'row': 'Cloud', 'set': {'shadowScale': 2.0}}]}}
            party.prepare(tables, [chosen], lambda rel: copy.deepcopy(original))
            self.assertEqual(tables[party.TABLE]['add'], [{'row': 'A2', 'set': {'ID': 13501}}])
            self.assertEqual(tables[party.TABLE]['set'][0], {'row': 'Cloud', 'set': {'shadowScale': 2.0}})
            self.assertEqual(len(tables[party.TABLE]['set']), 2)
            op = tables[party.TABLE]['set'][1]
            self.assertEqual(op['row'], c[1]); self.assertEqual(len(op['set']), 4)
            path = f'/Game/Chara/StudioParty/party{c[0]}/{c[3]}'
            self.assertEqual(op['set']['animationAssetList[0].Ss6Project'], path)
            built = copy.deepcopy(original)
            for field, value in op['set'].items(): built[c[1]]['animationAssetList'][0][field.split('.')[-1]] = value
            party.check_rows(original, built, [chosen])
            for key in original:
                if key != c[1]: self.assertEqual(built[key], original[key])
            self.assertNotIn(party.PLAYABLE_TABLE, tables)
        self.assertEqual(original, before)

    def test_crystal_fina_material_changes_only_selected_runtime_row(self):
        original = battle_rows(); chosen = unit(form=party.FINA); tables = {}
        party.prepare(tables, [chosen], lambda rel: copy.deepcopy(original))
        fields = tables[party.TABLE]['set'][0]['set']
        self.assertEqual(fields['animationAssetList[0].Material'], '/Game/BP/Map/Unit/Material/M_StudioParty1001')
        built = copy.deepcopy(original)
        for field, value in fields.items(): built[chosen['jp']]['animationAssetList'][0][field.split('.')[-1]] = value
        party.check_rows(original, built, [chosen])
        self.assertEqual(built['ラスウェル'], original['ラスウェル'])

    def test_verifier_rejects_wrong_paths_and_unrelated_party_properties(self):
        original = battle_rows(); chosen = unit(); fields = party.asset_updates(chosen); built = copy.deepcopy(original)
        for field, value in fields.items(): built[chosen['jp']]['animationAssetList'][0][field.split('.')[-1]] = value
        party.check_rows(original, built, [chosen])
        for field, value in [('ID', 999), ('shadowScale', 3.0)]:
            wrong = copy.deepcopy(built); wrong[chosen['jp']][field] = value
            with self.subTest(field=field), self.assertRaises(ValueError): party.check_rows(original, wrong, [chosen])
        wrong = copy.deepcopy(built); wrong[chosen['jp']]['animationAssetList'][0]['textureBaseColor'] = '/Wrong'
        with self.assertRaises(ValueError): party.check_rows(original, wrong, [chosen])
        wrong = copy.deepcopy(original); wrong[chosen['jp']]['ID'] = 13110
        with self.assertRaises(ValueError): party.prepare({}, [chosen], lambda rel: wrong)

    def test_mixture_has_separate_hold_and_return_without_extra_hits(self):
        spec = knockout_spec()
        spec['animations'].append({'name': 'attack_B', 'frameCount': 6,
                                  'parts': {'part_0': {'Cell': [[0, 'a'], [2, 'b'], [5, 'c']]}}})
        party.party_motions(spec)
        motions = {a['name']: a for a in spec['animations']}
        hold, reverse = motions['attack_B_pose'], motions['attack_B_reverse']
        self.assertEqual(hold['parts']['part_0']['Cell'], [[0, 'c']])
        self.assertEqual(reverse['parts']['part_0']['Cell'], [[0, 'c'], [1, 'b'], [4, 'a']])
        self.assertEqual(hold['frameCount'], 1); self.assertEqual(reverse['frameCount'], 6)
        party.party_motions(spec); self.assertEqual(len(spec['animations']), 9)

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
                    (battle / 'spec.json').write_text(json.dumps({'pixelSize': [2048.0, 2048.0], **knockout_spec()}))
            env = {'ROOT': str(root), 'LEGACY': str(root / 'legacy'), 'OUT': str(root / 'out'),
                   'FFRDT': ['real-tool'], 'USMAP': 'fixture.usmap', 'run': run,
                   'ffrenv': SimpleNamespace(py=lambda *args: list(args))}
            with mock.patch.dict('sys.modules', {'_ffr_animation_repair': animation}), mock.patch.object(animation, 'repair_unit'):
                party.generate(u, env)
            self.assertIn('--battle-only', calls[0]); self.assertEqual(len(calls), 5)
            spec = json.loads((root / 'build/sprites/party_1001/battle/spec.json').read_bytes())
            self.assertEqual(spec['animePackName'], 'unit0010')
            self.assertIn('death', [a['name'] for a in spec['animations']])
            self.assertTrue(all('StudioParty/party1001' in str(args) for args in calls[1:]))
            self.assertTrue(all('/Chara/menu/' not in str(args) and '/Chara/unit/' not in str(args) for args in calls))
            textures = [args for args in calls if 'make-texture' in args]
            self.assertEqual(len(textures), 3)
            self.assertTrue(all(args[4:6] == ['2048', '2048'] for args in textures))


if __name__ == '__main__': unittest.main()
