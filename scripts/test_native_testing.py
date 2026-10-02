"""Original-item grants, clean-save controls and bounded native MR rewards."""
import copy
import json
from pathlib import Path
import tempfile
import sys
import unittest
from types import SimpleNamespace
from unittest import mock
from test_existing_visions import fixture, native
import _ffr_testing as testing
sys.modules['_ffr_existingvisions'] = native


def game():
    tables, _, unit = fixture()
    noop = {'TalkEventDataTable': 'None', 'EventSequence': 'None', 'EventBlueprint': 'None',
            'OnFlagList': [], 'OffFlagList': [], 'FlagList': [], 'ProgressList': [],
            'ContinuousEventList': [], 'ObtainItemList': [], 'InitUnitDataList': [],
            'Description': '', 'encountGroupId': 9060, 'IsGetOffVehicle': True, 'IsHiddenFieldUI': True,
            'MapStartupSettings': {'ChangeBGM': 'Stop'},
            'RestoreSoundVolumeSettings': {'IsRevertValume': True, 'FadeTime': 1.0},
            'IsSetAutoSave': False, 'IsForceAutoSave': False, 'LoadingScreenSetting': 'None'}
    grant = copy.deepcopy(noop)
    grant.update(ObtainItemList=[{'Condition': '', 'ID': 13024, 'Num': 1, 'Text': ''}],
                 OnFlagList=[105], ProgressList=[{'ID': 0, 'Value': 1080}], IsSetAutoSave=True)
    tables[testing.EVENT] = {'C01_ArijigokuEncount': noop, 'C01_014_03': grant}
    tables[testing.COMMON] = {'tutorial': {'eventCondition': 'BattleBegin', 'eventDataList': [
        {'playSetting': {'Condition': '{progress:0}>=1050&!{flag:1188}', 'EventList': [
            {'EventId': 'Tutorial_EnemyLevel', 'Weight': 1, 'MoveInfo': {'MoveType': 'Walk'},
             'FadeInfo': {'IsEnabled': False}}]}, 'ParameterList': []}]}}
    tables[testing.GROUP] = {'normal': {'ap': 6, 'isResultSkipOnWin': False, 'battleEventId': 123},
                             'scripted': {'ap': 0, 'isResultSkipOnWin': True, 'battleEventId': 456}}
    return tables, lambda rel: copy.deepcopy(tables[rel]), unit


class NativeTestingTests(unittest.TestCase):
    def test_default_off_requires_no_assets_and_does_not_change_tables(self):
        with tempfile.TemporaryDirectory() as root:
            self.assertEqual(testing.settings(root), {'schema': 1, 'maxMr': False})
            result = {'existing': {'untouched': True}}
            testing.prepare(result, [], root, lambda _: self.fail('No testing assets should be read'))
            self.assertEqual(result, {'existing': {'untouched': True}})

    def test_native_acquisition_uses_original_id_once_without_rewriting_vision_or_story(self):
        original, rows, unit = game(); before = copy.deepcopy(original); unit['testAcquire'] = True
        with tempfile.TemporaryDirectory() as root: ops = testing.prepare({}, [unit], root, rows)
        self.assertEqual(original, before)
        self.assertEqual(set(ops), {testing.EVENT, testing.COMMON})
        for rel, operation in ops.items():
            self.assertEqual(operation['set'], [])
            added, = operation['add']
            built = copy.deepcopy(original[rel])
            built[testing.NAME] = testing.apply_fields(original[rel][added['cloneFrom']], added['set'])
            testing.check_rows(original[rel], built, operation)
            if rel == testing.EVENT:
                event = built[testing.NAME]
                self.assertEqual(event['ObtainItemList'], [{'Condition': '{item:13110}==0', 'ID': 13110, 'Num': 1, 'Text': ''}])
                self.assertEqual(event['OnFlagList'], []); self.assertEqual(event['ProgressList'], [])
                self.assertFalse(event['IsSetAutoSave']); self.assertFalse(event['IsForceAutoSave'])
                self.assertEqual(event['encountGroupId'], -1)
            else:
                self.assertEqual(built[testing.NAME]['eventCondition'], 'BattleBegin')
                self.assertEqual(built[testing.NAME]['eventDataList'][0]['playSetting']['Condition'], '{item:13110}==0')
            built[next(iter(original[rel]))]['unexpected'] = True
            with self.assertRaises(ValueError): testing.check_rows(original[rel], built, operation)

    def test_disabling_acquisition_preserves_original_vision_edits(self):
        _, rows, unit = game(); unit['stats']['Attack'] = 99; unit['testAcquire'] = False
        with tempfile.TemporaryDirectory() as root:
            self.assertEqual(testing.prepare({}, [unit], root, rows), {})
        self.assertEqual(unit['stats']['Attack'], 99)

    def test_max_mr_only_changes_ap_for_every_battle_and_preserves_scripted_results(self):
        original, rows, unit = game()
        with tempfile.TemporaryDirectory() as root:
            p = Path(root) / testing.CONFIG; p.parent.mkdir(parents=True); p.write_text(json.dumps({'schema': 1, 'maxMr': True}))
            ops = testing.prepare({}, [], root, rows)
            self.assertEqual(set(ops), {testing.GROUP})
            expected = testing.expected_edits(root, [], rows)
        self.assertEqual(testing.reward(rows), 4995)
        self.assertEqual(set(expected), {(testing.GROUP, k) for k in original[testing.GROUP]})
        self.assertTrue(all(fields == {'ap': 4995} for fields in expected.values()))
        built = {k: {**v, 'ap': 4995} for k, v in original[testing.GROUP].items()}
        testing.check_rows(original[testing.GROUP], built, ops[testing.GROUP])
        self.assertTrue(built['scripted']['isResultSkipOnWin']); self.assertEqual(built['scripted']['battleEventId'], 456)

    def test_rejects_custom_acquisition_duplicate_ids_and_unknown_thresholds(self):
        original, rows, unit = game()
        with tempfile.TemporaryDirectory() as root:
            custom = copy.deepcopy(unit); custom.pop('native'); custom['testAcquire'] = True
            with self.assertRaises(ValueError): testing.prepare({}, [custom], root, rows)
            unit['testAcquire'] = True
            with self.assertRaises(ValueError): testing.prepare({}, [unit, unit], root, rows)
            unit['testAcquire'] = 'true'
            with self.assertRaises(ValueError): testing.prepare({}, [unit], root, rows)
        original[native.SYNCHRO]['Mr9']['masteryPoint'] = 2**31 - 1
        with self.assertRaises(ValueError): testing.reward(rows)

    def test_settings_routes_persist_and_reject_changes_while_building(self):
        routes = {}
        class App:
            def get(self, path):
                def route(func): routes[('get', path)] = func; return func
                return route
            def put(self, path):
                def route(func): routes[('put', path)] = func; return func
                return route
        class Error(Exception):
            def __init__(self, code, detail): super().__init__(detail)
        with tempfile.TemporaryDirectory() as root, mock.patch.dict('sys.modules', {'fastapi': SimpleNamespace(HTTPException=Error)}):
            env = {'ROOT': root, 'state': {'running': False}}
            testing.register(App(), env)
            get = routes['get', '/api/testing']; put = routes['put', '/api/testing']
            self.assertFalse(get()['maxMr'])
            put({'schema': 1, 'maxMr': True}); self.assertTrue(get()['maxMr'])
            spec = Path(root) / 'mods/EstherTsukiko/units.json'
            self.assertEqual(json.loads(spec.read_bytes()), [])
            spec.write_text(json.dumps([{'existing': True}]))
            env['state']['running'] = True
            with self.assertRaises(Error): put({'schema': 1, 'maxMr': False})
            self.assertTrue(get()['maxMr'])
            env['state']['running'] = False
            put({'schema': 1, 'maxMr': False}); self.assertFalse(get()['maxMr'])
            put({'schema': 1, 'maxMr': True})
            self.assertEqual(json.loads(spec.read_bytes()), [{'existing': True}])
            for bad in ({'maxMr': True}, {'schema': True, 'maxMr': True}, {'schema': 1, 'maxMr': 1}):
                with self.assertRaises(Error): put(bad)


if __name__ == '__main__': unittest.main()
