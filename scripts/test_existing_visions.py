import ast
import contextlib
import copy
import importlib.util
import json
import os
import glob
import io
from pathlib import Path
import tempfile
import sys
import unittest
from types import SimpleNamespace
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m


native = module('native', ROOT / 'assets/existing_visions/payload/_ffr_existingvisions.py')
animation = module('animation', ROOT / 'assets/existing_visions/payload/_ffr_animation_repair.py')
installer = module('native_installer', ROOT / 'assets/existing_visions/install_existing_visions.py')
fina_installer = module('fina_installer', ROOT / 'assets/crystal_fina/engine/install_crystalfina.py')


# The published catalogue has these 26 IDs. All row contents below are explicit
# synthetic test fixtures, never substituted for extracted game data.
CATALOG_IDS = (13017, 13024, 13027, 13033, 13045, 13051, 13062, 13080, 13060,
               13100, 13101, 13102, 13103, 13105, 13108, 13110, 13116, 13118,
               13120, 13123, 13124, 13125, 13127, 13128, 13130, 13113)


def fixture(vid=13110):
    empty = lambda n: [{'parameterType': 'None', 'params': [-1, -1]} for _ in range(n)]
    tables = {
        native.UNIT: {'Cloud': {'ID': 13110, 'SaveId': 13110, 'LevelParamId': 10112, 'FaceIconId': 13110,
                              'ElementResistanceList': {}, **{f: 50 for f in native.FIELDS}, 'untouched': {'progression': True}}},
        native.VISION: {'Cloud': {'ID': 13110, 'SortId': 1, 'buyingPrice': 0, 'Name': 'Cloud', 'Description': 'Original Cloud',
                                 'CommandId': 202, 'finishBlowSkill': 440110, 'attackType': 'Physic', 'roles': ['eUnitRole::Attacker']}},
        native.BATTLE: {'Cloud': {'ID': 13110, 'animationAssetList': [{'Ss6Project': '/Game/Chara/summon/summon13110/summon13110',
                                                                   'Material': 'original material', 'isVisionCharacter': True}]}},
        'Skill/DT_CommandSkillData': {'Cloud command': {'ID': 202, 'unitIdToUseSkill': 13110, 'Name': 'Cloud skills'}},
        'Skill/DT_MasterSkillData': {'Cloud master': {'ID': 500, 'VisionId': 13110, 'Name': 'Spirit of Cloud'}},
        'Skill/DT_SkillData': {'Braver': {'ID': 446000}, 'Climhazzard': {'ID': 440110}},
        'Asset/Skill/DT_SkillAsset': {}, 'Asset/Skill/CDT_SkillAsset_Demo': {}, 'Battle/Sequencer/DT_BtlHitEffectData': {},
        native.AWAKENING: {f'Aw{i}': {'ID': 13110, 'Level': i, 'masteryPoint': i, 'detailData': empty(8)} for i in range(4)},
        native.SYNCHRO: {f'Mr{i}': {'ID': 13110, 'Level': i, 'masteryPoint': i * 111, 'detailData': empty(5)} for i in range(10)},
    }
    tables[native.AWAKENING]['Aw0']['detailData'][0] = {'parameterType': 'ActiveSkill', 'params': [446000, -1]}
    tables[native.SYNCHRO]['Mr1']['detailData'][0] = {'parameterType': 'BaseParameter', 'params': [1, 50]}
    if vid != 13110:
        for values in tables.values():
            for row in values.values():
                for field in ('ID', 'VisionId', 'SaveId', 'FaceIconId', 'unitIdToUseSkill'):
                    if row.get(field) == 13110: row[field] = vid
        tables[native.VISION]['Cloud']['CommandId'] = 30000 + vid
        tables['Skill/DT_CommandSkillData']['Cloud command']['ID'] = 30000 + vid
        tables['Skill/DT_MasterSkillData']['Cloud master']['ID'] = vid * 100
        tables[native.BATTLE]['Cloud']['animationAssetList'][0]['Ss6Project'] = f'/Game/Chara/summon/summon{vid}/summon{vid}'
    rows = lambda rel: copy.deepcopy(tables[rel])
    spec = native.snapshot(vid, rows, {'visions': [{'id': vid, 'name': 'Fixture vision'}]})
    return tables, rows, spec


def sprite_fixture(legacy, folder, vid):
    """Explicit file-presence fixtures; these are not game assets."""
    base = Path(legacy) / 'FFRS/Content' / folder / f'summon{vid}'
    base.parent.mkdir(parents=True, exist_ok=True)
    for suffix in ('.uasset', '.uexp'):
        base.with_suffix(suffix).write_bytes(b'explicit sprite extraction fixture')


class NativeVisionTests(unittest.TestCase):
    def test_all_26_missing_sprite_donors_are_extracted_once_and_cached_files_preserved(self):
        for vid in CATALOG_IDS:
            with self.subTest(vid=vid), tempfile.TemporaryDirectory() as temp:
                _, _, spec = fixture(vid); before = copy.deepcopy(spec); calls = []
                def extract(folder):
                    calls.append(folder); sprite_fixture(temp, folder, vid)
                native.ensure_sprite_templates(spec, temp, extract)
                self.assertEqual(calls, [f'Chara/summon/summon{vid}/', f'Chara/menu/summon{vid}/'])
                files = {p: p.read_bytes() for p in Path(temp).rglob('*') if p.is_file()}
                native.ensure_sprite_templates(spec, temp, extract)
                self.assertEqual(len(calls), 2); self.assertEqual(spec, before)
                self.assertEqual(files, {p: p.read_bytes() for p in files})

    def test_partial_or_empty_sprite_extraction_is_repaired_without_reextracting_complete_donors(self):
        for suffix, absent in (('.uexp', True), ('.uexp', False), ('.uasset', False)):
            with self.subTest(suffix=suffix, absent=absent), tempfile.TemporaryDirectory() as temp:
                _, _, spec = fixture(13045); calls = []
                for kind in ('summon', 'menu'): sprite_fixture(temp, f'Chara/{kind}/summon13045/', 13045)
                broken = Path(temp) / f'FFRS/Content/Chara/menu/summon13045/summon13045{suffix}'
                if absent: broken.unlink()
                else: broken.write_bytes(b'')
                def extract(folder):
                    calls.append(folder); sprite_fixture(temp, folder, 13045)
                native.ensure_sprite_templates(spec, temp, extract)
                self.assertEqual(calls, ['Chara/menu/summon13045/'])

    def test_failed_or_incomplete_extraction_stops_before_sprite_conversion(self):
        _, _, spec = fixture(13045); spec['en'] = 'Leah'
        with tempfile.TemporaryDirectory() as temp:
            extract = mock.Mock(side_effect=RuntimeError('game archives unavailable'))
            with self.assertRaisesRegex(RuntimeError, 'game archives unavailable'):
                native.ensure_sprite_templates(spec, temp, extract)
            extract.assert_called_once_with('Chara/summon/summon13045/')
            extract = mock.Mock()
            with self.assertRaisesRegex(RuntimeError, 'original summon sprite files for Leah'):
                native.ensure_sprite_templates(spec, temp, extract)
            extract.assert_called_once_with('Chara/summon/summon13045/')

    def test_catalog_route_lists_all_26_and_returns_each_original_without_changing_rows(self):
        game = {}; catalog = {'visions': []}
        for vid in CATALOG_IDS:
            tables, _, _ = fixture(vid)
            catalog['visions'].append({'id': vid, 'name': f'Fixture {vid}'})
            for rel, values in tables.items():
                game.setdefault(rel, {}).update({f'{vid}:{k}': row for k, row in values.items()})
        before = copy.deepcopy(game); routes = {}
        class App:
            def get(self, route):
                def add(func): routes[route] = func; return func
                return add
        class HTTPException(Exception):
            def __init__(self, status_code, detail): super().__init__(detail); self.status_code = status_code
        with tempfile.TemporaryDirectory() as root, mock.patch.dict('sys.modules', {
            'fastapi': SimpleNamespace(HTTPException=HTTPException),
            'fastapi.responses': SimpleNamespace(FileResponse=object),
        }):
            native.register(App(), {'ROOT': root, 'ffr_catalog': SimpleNamespace(load=lambda: catalog, rows=lambda rel: copy.deepcopy(game[rel]))})
            result = routes['/api/native/catalog']()
            self.assertEqual({u['id'] for u in result}, set(CATALOG_IDS)); self.assertEqual(len(result), 26)
            for vid in CATALOG_IDS:
                spec = routes['/api/native/vision/{vid}'](vid)
                self.assertEqual(spec['native']['id'], vid); self.assertEqual(spec['donor'], vid)
                patch = {}; native.prepare(patch, [], [spec], root, lambda rel: copy.deepcopy(game[rel]))
                self.assertEqual(patch, {})
        self.assertEqual(game, before)

    def test_all_nine_lower_ids_support_model_and_mr_edits_without_new_identity_rows(self):
        for vid in CATALOG_IDS[:9]:
            with self.subTest(vid=vid):
                game, rows, spec = fixture(vid); before = copy.deepcopy(game)
                spec['ffbe'] = {'id': '207000117', 'source': 'JP'}
                spec['synchro'][0].append(['PassiveSkill', 1234, 8])
                patch = {}; native.prepare(patch, [], [spec], '/unused', rows)
                self.assertEqual(set(patch), {native.BATTLE, native.SYNCHRO})
                self.assertTrue(all(not table['add'] for table in patch.values()))
                self.assertTrue(all(str(vid) in value for value in patch[native.BATTLE]['set'][0]['set'].values()))
                self.assertEqual(game, before)

    def test_nonvision_rows_and_nonpositive_ids_still_cannot_be_opened(self):
        _, rows, _ = fixture()
        for vid in (0, -1, True, 13024, 12001):
            with self.subTest(vid=vid), self.assertRaises(ValueError): native.snapshot(vid, rows, {'visions': []})

    def test_bundle_hashes_match(self):
        module('bundle', ROOT / 'scripts/verify_existing_visions_bundle.py').verify()

    def test_opening_original_creates_no_gameplay_or_sprite_patch(self):
        _, rows, spec = fixture(); tables = {}; objects = []
        native.prepare(tables, objects, [spec], '/unused', rows)
        self.assertEqual(tables, {}); self.assertEqual(objects, [])

    def test_sprite_only_changes_no_stats_progression_mastery_shop_or_skill_rows(self):
        original, rows, spec = fixture(); before = copy.deepcopy(original)
        spec['ffbe'] = {'id': '207000117', 'source': 'JP'}
        tables = {}; objects = []; native.prepare(tables, objects, [spec], '/unused', rows)
        self.assertEqual(set(tables), {native.BATTLE})
        row, = tables[native.BATTLE]['set']
        self.assertEqual(row['row'], 'Cloud'); self.assertNotIn('ID', row['set'])
        self.assertNotIn('Material', row['set']); self.assertNotIn('isVisionCharacter', row['set'])
        self.assertEqual(tables[native.BATTLE]['add'], [])
        self.assertTrue(all('13110' in value for value in row['set'].values()))
        self.assertEqual(objects[0]['mapAdd']['LayoutOverrideDataMap']['13110']['Scale'], 2.52)
        self.assertEqual(original, before)

    def test_edits_only_patch_selected_fields_and_keep_rank_points_and_save_ids(self):
        _, rows, spec = fixture(); spec['stats']['Attack'] = 99; spec['awakening'][1].append(['PassiveSkill', 1001])
        spec['synchro'][3].append(['BaseParameter', 8, 21]); spec['lb'] = 440260
        tables = {}; native.prepare(tables, [], [spec], '/unused', rows)
        self.assertEqual(tables[native.UNIT]['set'], [{'row': 'Cloud', 'set': {'Attack': 99}}])
        self.assertEqual(tables[native.VISION]['set'], [{'row': 'Cloud', 'set': {'finishBlowSkill': 440260}}])
        for rel in (native.AWAKENING, native.SYNCHRO):
            edit, = tables[rel]['set']; self.assertEqual(set(edit['set']), {'detailData'}); self.assertEqual(tables[rel]['add'], [])

    def test_native_layout_merges_with_other_added_visions(self):
        _, rows, spec = fixture(); spec['ffbe'] = {'id': '207000117', 'source': 'JP'}
        previous = {'13503': {'Scale': 2.7}}
        objects = [{'asset': 'FFRS/Content/UI/Unit/UIUnitSs/Data/DA_UIUnitSsLayout', 'mapAdd': {'LayoutOverrideDataMap': copy.deepcopy(previous)}}]
        native.prepare({}, objects, [spec], '/unused', rows)
        self.assertEqual(len(objects), 1)
        self.assertEqual(objects[0]['mapAdd']['LayoutOverrideDataMap']['13503'], previous['13503'])

    def test_originals_do_not_consume_added_unit_indices(self):
        _, rows, spec = fixture(); added = {'id': 13503, 'key': 'crystal_fina_2'}
        orig, extra = native.split([spec, added], rows)
        self.assertEqual(orig, [spec]); self.assertEqual(extra, [added])

    def test_rank_caps_identity_changes_duplicate_ids_and_native_skill_collisions_fail(self):
        _, rows, spec = fixture()
        for field, value in [('id', 13125), ('donor', 13125), ('lb_custom', {'from': 440110})]:
            changed = copy.deepcopy(spec); changed[field] = value
            with self.assertRaises(ValueError): native.validate(changed, rows)
        with self.assertRaises(ValueError): native.split([spec, spec], rows)
        spec['skills'] = {'446000': {'jp': 'A', 'from': 446000}}
        with self.assertRaises(ValueError): native.validate(spec, rows)
        spec['skills'] = {}; spec['synchro'][1] = [['BaseParameter', 1, 1]] * 6
        with self.assertRaises(ValueError): native.prepare({}, [], [spec], '/unused', rows)

    def test_free_native_skill_recipe_keeps_its_original_vision_id(self):
        _, rows, spec = fixture(); spec['skills']['446010'] = {'jp': 'Cloud_custom_fixture', 'from': 446000}
        native.validate(spec, rows)
        self.assertEqual(spec['id'], 13110)

    def test_native_skill_visual_collisions_are_rejected(self):
        game, rows, spec = fixture(); spec['skills']['446010'] = {'jp': 'Cloud_custom_fixture', 'from': 446000}
        for rel in ('Asset/Skill/DT_SkillAsset', 'Asset/Skill/CDT_SkillAsset_Demo', 'Battle/Sequencer/DT_BtlHitEffectData'):
            game[rel]['original effect'] = {'ID': 446011}
            with self.assertRaises(ValueError): native.validate(spec, rows)
            game[rel].clear()

    def test_passive_reward_second_parameter_survives_another_reward_edit(self):
        game, rows, _ = fixture()
        game[native.SYNCHRO]['Mr1']['detailData'][0] = {'parameterType': 'PassiveSkill', 'params': [1234, 8]}
        spec = native.snapshot(13110, rows, {'visions': []})
        self.assertEqual(spec['synchro'][1], [['PassiveSkill', 1234, 8]])
        spec['synchro'][1].append(['BaseParameter', 1, 77])
        tables = {}; native.prepare(tables, [], [spec], '/unused', rows)
        self.assertEqual(tables[native.SYNCHRO]['set'][0]['set']['detailData'][0]['params'], [1234, 8])

    def test_generated_native_source_compiles_and_keeps_custom_builder_and_fina_hooks(self):
        source = (ROOT / 'scripts/fixtures/crystal_fina/make_vision_mod.py').read_bytes()
        fina = fina_installer.hook_builder(source); patched = installer.hook_builder(fina)
        self.assertIn(b'_ffr_crystalfina.prepare(patch, UNITS, ROOT)', patched)
        self.assertIn(b'native_units, UNITS = _ffr_existingvisions.split(UNITS, rows)', patched)
        tree = ast.parse(patched); main, = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'main']
        self.assertTrue(any(isinstance(n, ast.For) and ast.unparse(n.iter) == 'UNITS' for n in main.body))
        self.assertIn(b'_native_skills(u)', patched); self.assertIn(b'generate_sprites(u)', patched)

    def test_normal_post_build_verifier_accepts_native_edits_but_rejects_unrelated_fields_and_missing_rows(self):
        game, _, spec = fixture(); spec['stats']['Attack'] = 99
        original = game[native.UNIT]
        changed = copy.deepcopy(original); changed['Cloud']['Attack'] = 99
        raw = (ROOT / 'scripts/fixtures/existing_visions/verify_mod.py').read_bytes()
        tree = ast.parse(installer.hook_verifier(raw))
        functions = [n for n in tree.body if isinstance(n, ast.FunctionDef)]
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); units = root / 'mods/EstherTsukiko/units.json'
            units.parent.mkdir(parents=True); units.write_text(json.dumps([spec, {'id': 13503}]))
            for rel, values in game.items():
                path = root / 'extracted/rows' / (rel + '.json'); path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(json.dumps({'rows': values}))
            for rel in ('UI/Skill/DT_CommandSkillIcon', 'UI/Skill/CDT_SkillIcon'):
                path = root / 'extracted/rows' / (rel + '.json'); path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(json.dumps({'rows': {'first': {'Tag': {'TagName': 'UI.Skill.Command.Icon.13104'}}, 'second': {'Tag': {'TagName': 'UI.Skill.Command.Icon.13106'}}}}))
            base = root / 'build/visions_mod/assets/FFRS/Content/Datatable'; asset = base / (native.UNIT + '.uasset')
            asset.parent.mkdir(parents=True); asset.write_bytes(b'explicit serializer fixture')
            def convert(args, **kwargs):
                Path(args[3]).write_text(json.dumps({'rows': changed}))
                return SimpleNamespace(returncode=0, stderr='')
            env = {'ROOT': str(root), 'BASE': str(base), 'TMP': str(root / 'verify'), 'os': os, 'json': json, 'sys': sys,
                   'glob': glob, 'subprocess': SimpleNamespace(run=convert), 'UNUSED_ICON_TAGS': [13104, 13106],
                   'ffrenv': SimpleNamespace(FFRDT=['fixture serializer'])}
            with mock.patch.dict('sys.modules', {'_ffr_existingvisions': native}):
                exec(compile(ast.Module(body=functions, type_ignores=[]), 'native_verifier_fixture', 'exec'), env)
                self.assertEqual(env['icon_rows']('UI/Skill/DT_CommandSkillIcon'), {'first'})
                for code, built in ((0, changed), (1, {**changed, 'Cloud': {**changed['Cloud'], 'SaveId': 999}}), (1, {})):
                    changed = built
                    with contextlib.redirect_stdout(io.StringIO()), self.assertRaises(SystemExit) as exit:
                        env['main']()
                    self.assertEqual(exit.exception.code, code)

    def test_native_verifier_checks_nested_sprite_and_mastery_fields(self):
        game, rows, spec = fixture(); spec['ffbe'] = {'id': '207000117'}
        spec['synchro'][0] = [['PassiveSkill', 1234, 8]]
        tables = {}; native.prepare(tables, [], [spec], '/unused', rows)
        edits = {(rel, entry['row']): entry['set'] for rel, table in tables.items() for entry in table['set']}
        row = copy.deepcopy(game[native.BATTLE]['Cloud'])
        for path, value in edits[(native.BATTLE, 'Cloud')].items(): row['animationAssetList'][0][path.split('.')[-1]] = value
        self.assertTrue(native.expected_row_change(native.BATTLE, 'Cloud', game[native.BATTLE]['Cloud'], row, edits, lambda a,b: a == b))
        row['animationAssetList'][0]['Material'] = 'unintended'
        self.assertFalse(native.expected_row_change(native.BATTLE, 'Cloud', game[native.BATTLE]['Cloud'], row, edits, lambda a,b: a == b))

    def test_full_native_only_builder_prepares_missing_leah_sprites_before_conversion_under_original_id(self):
        game, rows, spec = fixture(13045); spec['ffbe'] = {'id': '207000117', 'source': 'JP'}
        game['Shop/DT_ShopList'] = {'fixture shop': {'ItemList': [{'ItemId': 1001, 'MaxOrderNum': 99, 'PriceRatio': 1.0}]}}
        source = (ROOT / 'scripts/fixtures/crystal_fina/make_vision_mod.py').read_bytes()
        patched = installer.hook_builder(fina_installer.hook_builder(source)); tree = ast.parse(patched)
        main, = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'main']
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); build = root / 'build/visions_mod'; layout = build / 'check/da/DA_UIUnitSsLayout.json'
            layout.parent.mkdir(parents=True); layout.write_text(json.dumps({'Properties': {'LayoutOverrideDataMap': []}}))
            converted = []; extracted = []
            def extract(args):
                self.assertEqual(args[:3], [str(root / 'tools/extract_legacy.py'), '--filter', args[2]])
                extracted.append(args[2]); sprite_fixture(root / 'legacy', args[2], 13045)
            def generate(unit):
                self.assertEqual(extracted, ['Chara/summon/summon13045/', 'Chara/menu/summon13045/'])
                for kind in ('summon', 'menu'):
                    for suffix in ('.uasset', '.uexp'):
                        self.assertTrue((root / f'legacy/FFRS/Content/Chara/{kind}/summon13045/summon13045{suffix}').is_file())
                converted.append(unit['id'])
            env = {'UNITS': [spec], 'ROOT': str(root), 'BUILD': str(build), 'OUT': str(build / 'assets'), 'LEGACY': str(root / 'legacy'),
                   'DT': 'FFRS/Content/Datatable/', 'SHOP_ROW': 'fixture shop', 'FFRDT': ['fixture serializer'], 'USMAP': 'fixture.usmap',
                   'rows': lambda rel: copy.deepcopy(game.get(rel, {})), 'sys': SimpleNamespace(argv=['builder', '--no-install']),
                   'os': os, 'json': json, 'stage': lambda text: None, 'unique_skill_base': lambda vid: 445000+(vid-13100)*100,
                   'has_sequence': lambda sid: True, 'generate_sprites': generate, 'run': extract,
                   'subprocess': SimpleNamespace(run=lambda *a, **k: SimpleNamespace(returncode=0, stdout='', stderr='')),
                   'ffrenv': SimpleNamespace(py=lambda *a: list(a), MOD_NAME='fixture'),
                   'ffbe_audio': SimpleNamespace(banks=lambda a: [])}
            fina = SimpleNamespace(prepare=lambda *args: None, copy_material=lambda *args: None)
            with mock.patch.dict('sys.modules', {'_ffr_existingvisions': native, '_ffr_crystalfina': fina, '_ffr_animation_repair': animation}):
                exec(compile(ast.Module(body=[main], type_ignores=[]), 'native_builder_fixture', 'exec'), env)
                env['main']()
            result = json.loads((build / 'patch.json').read_text())
            self.assertEqual(converted, [13045]); self.assertEqual(env['UNITS'], [])
            self.assertTrue(all(not t['add'] for t in result['tables']))
            self.assertEqual(next(t for t in result['tables'] if t['asset'].endswith(native.BATTLE))['set'][0]['row'], 'Cloud')
            self.assertFalse(any('LevelParameter' in t['asset'] for t in result['tables']))


class NativeInstallerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.root = Path(self.temp.name)
        self.builder = self.root / installer.SOURCES[0]; self.builder.parent.mkdir(parents=True)
        self.builder.write_bytes(fina_installer.hook_builder((ROOT / 'scripts/fixtures/crystal_fina/make_vision_mod.py').read_bytes()))
        self.server = self.root / installer.SOURCES[1]; self.server.parent.mkdir(parents=True)
        self.server.write_bytes(b'from fastapi import FastAPI\napp = FastAPI()\ndef keep(): return "upstream"\n')
        self.verifier = self.root / installer.SOURCES[2]
        self.verifier.write_bytes((ROOT / 'scripts/fixtures/existing_visions/verify_mod.py').read_bytes())
        (self.root / 'VERSION').write_text('1.0.0.15')
        self.roster = self.root / 'units.json'; self.roster.write_text('user roster, untouched')
        self.original = {p: p.read_bytes() for p in (self.builder, self.server, self.verifier)}

    def tearDown(self):
        self.assertEqual(self.roster.read_text(), 'user roster, untouched'); self.temp.cleanup()

    def test_apply_restore_repeat_and_upstream_updates(self):
        installer.run(self.root, 'Apply'); first = self.builder.read_bytes()
        installer.run(self.root, 'Apply'); self.assertEqual(first, self.builder.read_bytes())
        installer.run(self.root, 'Restore')
        for p, raw in self.original.items(): self.assertEqual(p.read_bytes(), raw)
        self.builder.write_bytes(self.original[self.builder] + b'\n# new engine update\n')
        installer.run(self.root, 'Apply'); self.assertIn(b'new engine update', self.builder.read_bytes())
        installer.run(self.root, 'Restore'); self.assertIn(b'new engine update', self.builder.read_bytes())

    def test_external_source_and_helper_edits_are_preserved_and_refused(self):
        installer.run(self.root, 'Apply'); self.builder.write_bytes(self.builder.read_bytes() + b'\n# user edit\n')
        before = self.builder.read_bytes()
        for action in ('Apply', 'Restore'):
            with self.assertRaises(RuntimeError): installer.run(self.root, action)
            self.assertEqual(self.builder.read_bytes(), before)

    def test_unfamiliar_builder_leaves_all_sources_unchanged(self):
        self.builder.write_text('def main(): pass\n'); before = self.builder.read_bytes()
        with self.assertRaises(ValueError): installer.run(self.root, 'Apply')
        self.assertEqual(self.builder.read_bytes(), before); self.assertEqual(self.server.read_bytes(), self.original[self.server])

    def test_atomic_activation_rolls_back_an_interrupted_write(self):
        original_write = installer.write
        def fail(path, data):
            if path == self.server and installer.MARKER.encode() in data: raise OSError('fixture write failure')
            return original_write(path, data)
        with mock.patch.object(installer, 'write', side_effect=fail):
            with self.assertRaises(OSError): installer.run(self.root, 'Apply')
        for p, raw in self.original.items(): self.assertEqual(p.read_bytes(), raw)


if __name__ == '__main__': unittest.main()
