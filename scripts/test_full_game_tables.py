"""Production table routing, physical recipe verification, and demo regressions."""
import copy
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'assets/existing_visions/payload'))
import _ffr_game_tables as game_tables
import _ffr_launch as launch
import _ffr_testing as testing

BASE = 'Asset/Skill/DT_SkillAsset'
PROD = BASE + '_Prod'
COMPOSITE = 'Asset/Skill/CDT_SkillAsset_Prod'
DEMO = 'Asset/Skill/CDT_SkillAsset_Demo'


def save(root, rel, rows):
    target = root / 'extracted/rows' / (rel + '.json')
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps({'rows': rows}), encoding='utf-8')


def inventory(root, names):
    target = root / 'extracted/utoc_filelist.tsv'
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text('\n'.join('native\t../../../' + game_tables.PREFIX + p + '.uasset' for p in names))


def production(root):
    # Explicit independent fixture IDs/rows; no native game artwork is bundled.
    shared = {'ID': 400010, 'LevelSequence': '/Game/Shared', 'soundSequence': '/Game/SharedSound'}
    base = {'Shared': shared, 'BaseOnly': {'ID': 440111, 'LevelSequence': '/Game/Base'}}
    prod = {'Shared': copy.deepcopy(shared), 'ProductionOnly': {
        'ID': 500271, 'LevelSequence': '/Game/Needles', 'soundSequence': '/Game/NeedlesSound'}}
    original = {BASE: base, PROD: prod, COMPOSITE: {**base, **prod}}
    for rel, rows in original.items(): save(root, rel, rows)
    inventory(root, original)
    return original, game_tables.reader(root)


class FullGameTableTests(unittest.TestCase):
    def test_production_donor_is_cloned_in_registered_parent_and_composite_without_changing_sources(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); original, rows = production(root)
            before = {p: p.read_bytes() for p in root.rglob('*') if p.is_file()}
            tables = {rel: {'asset': game_tables.PREFIX + rel, 'add': [
                {'row': 'Custom', 'cloneFrom': 'ProductionOnly', 'set': {'ID': 898001}}], 'set': []}
                for rel in (BASE, DEMO)}
            game_tables.normalize(root, tables, rows)
            self.assertEqual(set(tables), {PROD, COMPOSITE})
            for rel, plan in tables.items():
                actual = copy.deepcopy(original[rel])
                actual['Custom'] = testing.apply_fields(actual['ProductionOnly'], {'ID': 898001})
                testing.check_rows(original[rel], actual, plan)
                self.assertEqual(actual['Custom']['soundSequence'], '/Game/NeedlesSound')
                actual['Shared']['ID'] = 99
                with self.assertRaises(ValueError): testing.check_rows(original[rel], actual, plan)
            self.assertEqual(before, {p: p.read_bytes() for p in before})

    def test_shared_parent_remains_available_and_shared_edits_reach_both_parents(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); original, rows = production(root)
            tables = {BASE: {'asset': game_tables.PREFIX + BASE, 'add': [
                {'row': 'CustomBase', 'cloneFrom': 'BaseOnly', 'set': {'ID': 898011}}],
                'set': [{'row': 'Shared', 'set': {'soundSequence': '/Game/EditedSound'}}]}}
            rows.normalize(tables)
            self.assertEqual([e['row'] for e in tables[BASE]['add']], ['CustomBase'])
            self.assertEqual(tables[PROD]['add'], [])
            self.assertEqual(tables[PROD]['set'], tables[BASE]['set'])
            self.assertEqual(set(rows(BASE)), set(original[COMPOSITE]))

    def test_official_inventory_rejects_stale_demo_cache_and_follows_game_changes_in_same_process(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); _, rows = production(root)
            save(root, DEMO, {'StaleDemo': {'ID': 9}})
            self.assertNotIn('StaleDemo', rows(DEMO))
            inventory(root, [BASE, DEMO])
            self.assertEqual(rows(DEMO), {'StaleDemo': {'ID': 9}})
            self.assertEqual(set(rows(BASE)), {'Shared', 'BaseOnly'})

    def test_duplicate_parent_conflicts_follow_composite_instead_of_assumed_load_order(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); original, rows = production(root)
            original[PROD]['Shared']['soundSequence'] = '/Game/ProductionSound'
            save(root, PROD, original[PROD])
            # The composite can select either parent; patch precisely its owner.
            for selected in (BASE, PROD):
                with self.subTest(selected=selected):
                    combined = {**original[BASE], **original[PROD], 'Shared': original[selected]['Shared']}
                    save(root, COMPOSITE, combined)
                    self.assertEqual(rows(BASE)['Shared'], original[selected]['Shared'])
                    plan = {BASE: {'add': [], 'set': [{'row': 'Shared', 'set': {'ID': 400020}}]}}
                    rows.normalize(plan)
                    self.assertEqual(set(plan), {selected})
            save(root, COMPOSITE, {'Shared': {'ID': 999}})
            with self.assertRaisesRegex(ValueError, 'disagree'): rows(BASE)

    def test_demo_plans_and_rows_remain_exact_without_production_assets(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); save(root, BASE, {'Demo': {'ID': 1}})
            save(root, DEMO, {'Demo': {'ID': 1}})
            rows = game_tables.reader(root)
            tables = {BASE: {'asset': game_tables.PREFIX + BASE, 'add': [], 'set': []}}
            before = copy.deepcopy(tables)
            rows.normalize(tables)
            self.assertEqual(tables, before)
            self.assertEqual(rows(DEMO), {'Demo': {'ID': 1}})

    def test_full_game_practice_and_grants_verify_against_physical_production_tables(self):
        from test_native_testing import practice_game
        native, _, unit = practice_game()
        unit['testAcquire'] = True
        for rel in list(native):
            if rel.endswith('_Demo'): native[rel[:-5] + '_Prod'] = native.pop(rel)
        # Split the chapter and stage donors into their production parents.
        for rel in (testing.EVENT, testing.STAGE):
            native[rel + '_Prod'] = native[rel]
            native[rel] = {}
        original = copy.deepcopy(native)
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            for rel, values in native.items(): save(root, rel, values)
            inventory(root, native)
            config = root / testing.CONFIG; config.parent.mkdir(parents=True)
            config.write_text(json.dumps({'schema': 1, 'maxMr': False, 'practiceBattle': True}))
            operations = testing.verification_operations(root, [unit], game_tables.reader(root))
            self.assertFalse(any(rel.endswith('_Demo') for rel in operations))
            self.assertIn(testing.EVENT + '_Prod', operations)
            self.assertIn(testing.STAGE + '_Prod', operations)
            self.assertNotIn(testing.STAGE, operations)
            for rel, operation in operations.items():
                built = copy.deepcopy(native[rel])
                for entry in operation['add']:
                    built[entry['row']] = testing.apply_fields(built[entry['cloneFrom']], entry['set'])
                for entry in operation['set']:
                    built[entry['row']] = testing.apply_fields(built[entry['row']], entry['set'])
                testing.check_rows(native[rel], built, operation)
            self.assertEqual(native, original)

    def test_catalog_refreshes_previously_prepared_full_game_routes_without_rewriting_saved_files(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); _, _ = production(root)
            cached = {'skills': [{'id': 500270, 'name': 'Needles', 'seq': [], 'seqPath': None}]}
            catalog = SimpleNamespace(rows=lambda rel: json.loads(
                (root / 'extracted/rows' / (rel + '.json')).read_text())['rows'], load=lambda: cached)
            game_tables.install_catalog(catalog, root)
            game_tables.install_catalog(catalog, root)
            fresh = catalog.load()
            self.assertEqual(fresh['skills'][0]['seq'], [1])
            self.assertEqual(fresh['skills'][0]['seqPath'], '/Game/Needles')
            self.assertEqual(cached['skills'][0]['seq'], [])

    def test_report_covers_production_routes_and_does_not_count_parent_duplicates_as_changes(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); original, _ = production(root)
            save(root, 'Skill/DT_SkillData', {'Needles': {'ID': 500270}})
            result = launch.summarize(root, {'sha256': 'fixture'})
            self.assertEqual(result['skills']['500270']['routes'], [original[PROD]['ProductionOnly']])
            duplicate = copy.deepcopy(result)
            duplicate['skills']['500270']['routes'] *= 2
            self.assertEqual(launch.compare(duplicate, result)['skills'], {})

    def test_old_optional_ffbe_needles_setting_defers_to_new_native_routes(self):
        import _ffr_ffbe_needles as needles
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); _, rows = production(root)
            config = root / testing.CONFIG; config.parent.mkdir(parents=True)
            config.write_text(json.dumps({'schema': 1, 'maxMr': False, 'ffbeNeedles': True}))
            previous = config.read_bytes(); plans = {}; clones = []; jobs = []
            with mock.patch.object(needles, 'payload', side_effect=AssertionError('Do not import over native routes')):
                needles.prepare(plans, clones, jobs, root, rows, mock.Mock())
            self.assertEqual((plans, clones, jobs), ({}, [], []))
            self.assertEqual(config.read_bytes(), previous)


if __name__ == '__main__': unittest.main()
