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
    tables[testing.COMPOSITE] = {'C01_ArijigokuEncount': noop, 'C01_014_03': grant}
    tables[testing.EVENT] = {'C01_014_03': copy.deepcopy(grant)}
    tables[testing.COMMON] = {'tutorial': {'eventCondition': 'BattleBegin', 'eventDataList': [
        {'playSetting': {'Condition': '{progress:0}>=1050&!{flag:1188}', 'EventList': [
            {'EventId': 'Tutorial_EnemyLevel', 'Weight': 1, 'MoveInfo': {'MoveType': 'Walk'},
             'FadeInfo': {'IsEnabled': False}}]}, 'ParameterList': []}]}}
    tables[testing.GROUP] = {'normal': {'ap': 6, 'isResultSkipOnWin': False, 'battleEventId': 123},
                             'scripted': {'ap': 0, 'isResultSkipOnWin': True, 'battleEventId': 456}}
    return tables, lambda rel: copy.deepcopy(tables[rel]), unit


def practice_game():
    tables, _, unit = game()
    woman = copy.deepcopy(tables[testing.COMPOSITE]['C01_ArijigokuEncount'])
    woman.update(ArgList={'id': '6'}, encountGroupId=-1, OverwriteBattleParty=[],
                 TransitionLocation={'mapId': -1}, ChoicesBranchEventList=[],
                 ConsumeItemList=[], ChangeUnitJoinStatusList=[], IsForceUpdateProgress=False,
                 IsSetForceAutoSave=False, EventSequence='native free-talk timeline')
    # Explicit identities from the observed conversation: do not derive the
    # fixture key from the implementation's selected NPC constant.
    other_woman = copy.deepcopy(woman); other_woman['ArgList'] = {'id': '39'}
    tables[testing.SHOP_EVENT] = {'DT_Town_010Gra_20_0920_8': woman,
                                'DT_Town_010Gra_20_1170_1': other_woman, 'shopkeeper': {'shop': 1}}
    tables[testing.COMPOSITE].update(copy.deepcopy(tables[testing.SHOP_EVENT]))
    town = {'ID': 2000, 'battleStage': -1, 'doMovementEncount': False, 'startupEventList': ['story']}
    tables[testing.MAP] = {'01Gra_20': town, 'other town': {'ID': 2001, 'battleStage': -1}}
    tables[testing.MAP_COMPOSITE] = copy.deepcopy(tables[testing.MAP])
    tables[testing.STAGE] = {'plains': {'ID': 5, 'battleLevelList': [
        '/Game/Map/Btl/00Com/00Com_60/LT/Btl_00Com_60_01_LT',
        '/Game/Map/Btl/00Com/00Com_60/BG/Btl_00Com_60_BG0'],
        'isLoadLevelInstance': False, 'unitLightIntensity': 2.0, 'unitShadowDensity': 0.8}}
    tables[testing.STAGE_COMPOSITE] = copy.deepcopy(tables[testing.STAGE])
    tables[testing.GROUP]['plant and rats'] = {
        'ID': 1026, 'UnitIdList': [20, 22, 22], 'locationIdList': [20, 6, 15], 'ap': 20,
        'CanEscape': True, 'probabilityOfSuccessfulEscape': 50.0,
        'isResultSkipOnWin': False, 'isResultSkipOnLose': False,
        'battleEventId': -1, 'battleFinishEventId': '', 'battleFinishEscapeEventId': '',
        'battleFinishLoseEventId': '', 'battleFinishTransition': {'mapId': -1, 'bDoAutoSave': False}}
    tables[native.UNIT]['Evil Plant'] = {'ID': 20, 'Level': 7, 'Category': 'Enemy', 'MaxHitPoint': 300}
    tables[native.UNIT]['Wild Rat'] = {'ID': 22, 'Level': 8, 'Category': 'Enemy', 'MaxHitPoint': 320}
    return tables, lambda rel: copy.deepcopy(tables[rel]), unit


class NativeTestingTests(unittest.TestCase):
    def test_default_off_requires_no_assets_and_does_not_change_tables(self):
        with tempfile.TemporaryDirectory() as root:
            self.assertEqual(testing.settings(root), {'schema': 1, 'maxMr': False, 'practiceBattle': False, 'crystalCave': False, 'fieldLeader': False})
            result = {'existing': {'untouched': True}}
            testing.prepare(result, [], root, lambda _: self.fail('No testing assets should be read'))
            self.assertEqual(result, {'existing': {'untouched': True}})

    def test_native_acquisition_uses_original_id_once_without_rewriting_vision_or_story(self):
        original, rows, unit = game(); before = copy.deepcopy(original); unit['testAcquire'] = True
        with tempfile.TemporaryDirectory() as root: ops = testing.prepare({}, [unit], root, rows)
        self.assertEqual(original, before)
        self.assertEqual(set(ops), {testing.EVENT, testing.COMPOSITE, testing.COMMON})
        for rel, operation in ops.items():
            self.assertEqual(operation['set'], [])
            added, = operation['add']
            built = copy.deepcopy(original[rel])
            built[testing.NAME] = testing.apply_fields(original[rel][added['cloneFrom']], added['set'])
            testing.check_rows(original[rel], built, operation)
            if rel in (testing.EVENT, testing.COMPOSITE):
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

    def test_practice_battle_preserves_dialogue_party_story_other_npcs_and_random_encounters(self):
        original, rows, _ = practice_game(); before = copy.deepcopy(original)
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / testing.CONFIG; path.parent.mkdir(parents=True)
            path.write_text(json.dumps({'schema': 1, 'maxMr': False, 'practiceBattle': True}))
            ops = testing.prepare({}, [], root, rows)
            expected = testing.expected_edits(root, [], rows)
        self.assertEqual(original, before)
        self.assertEqual(set(ops), {testing.SHOP_EVENT, testing.COMPOSITE,
                                   testing.MAP, testing.MAP_COMPOSITE, testing.GROUP,
                                   testing.STAGE, testing.STAGE_COMPOSITE})
        self.assertEqual(len(expected), 4)
        for rel, op in ops.items():
            built = copy.deepcopy(original[rel])
            for edit in op['set']: built[edit['row']] = testing.apply_fields(built[edit['row']], edit['set'])
            for edit in op['add']: built[edit['row']] = testing.apply_fields(original[rel][edit['cloneFrom']], edit['set'])
            testing.check_rows(original[rel], built, op)
            if rel in (testing.SHOP_EVENT, testing.COMPOSITE):
                self.assertEqual([e['row'] for e in op['set']], ['DT_Town_010Gra_20_0920_8'])
                self.assertEqual(built[testing.SHOP_WOMAN]['encountGroupId'], testing.PRACTICE_ID)
                self.assertEqual(built[testing.SHOP_WOMAN]['ArgList'], {'id': '6'})
                self.assertEqual(built['DT_Town_010Gra_20_1170_1'], original[rel]['DT_Town_010Gra_20_1170_1'])
                self.assertEqual(built['shopkeeper'], original[rel]['shopkeeper'])
                self.assertEqual(built[testing.SHOP_WOMAN]['EventSequence'], 'native free-talk timeline')
                self.assertEqual(built[testing.SHOP_WOMAN]['OverwriteBattleParty'], [])
            elif rel in (testing.MAP, testing.MAP_COMPOSITE):
                self.assertFalse(built['01Gra_20']['doMovementEncount'])
                self.assertEqual(built['01Gra_20']['startupEventList'], ['story'])
                self.assertEqual(built['01Gra_20']['battleStage'], 29990)
            elif rel in (testing.STAGE, testing.STAGE_COMPOSITE):
                self.assertEqual(built['plains'], original[rel]['plains'])
                stage = built[testing.PRACTICE]
                self.assertTrue(stage['isLoadLevelInstance'])
                self.assertEqual(stage['ID'], 29990)
                self.assertEqual(stage['battleLevelList'], original[rel]['plains']['battleLevelList'])
                self.assertEqual(stage['unitLightIntensity'], 2.0)
                self.assertEqual(stage['unitShadowDensity'], 0.8)
            else:
                encounter = built[testing.PRACTICE]
                self.assertEqual(encounter['UnitIdList'], [20, 22, 22])
                self.assertEqual(encounter['locationIdList'], [20, 6, 15])
                self.assertEqual(encounter['probabilityOfSuccessfulEscape'], 100.0)
                self.assertEqual(encounter['battleFinishTransition'], {'mapId': -1, 'bDoAutoSave': False})
                self.assertEqual(encounter['ap'], 20)
        with tempfile.TemporaryDirectory() as root:
            self.assertEqual(testing.prepare({}, [], root, rows), {})

    def test_practice_battle_honors_mr_and_original_vision_acquisition_together(self):
        original, rows, unit = practice_game(); unit['testAcquire'] = True
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / testing.CONFIG; path.parent.mkdir(parents=True)
            path.write_text(json.dumps({'schema': 1, 'maxMr': True, 'practiceBattle': True}))
            ops = testing.prepare({}, [unit], root, rows)
        self.assertEqual(ops[testing.GROUP]['add'][0]['set']['ap'], 4995)
        self.assertEqual(len(ops[testing.GROUP]['set']), len(original[testing.GROUP]))
        self.assertEqual(ops[testing.COMMON]['add'][0]['row'], testing.NAME)
        self.assertEqual(ops[testing.COMPOSITE]['add'][0]['row'], testing.NAME)
        self.assertEqual(ops[testing.COMPOSITE]['set'][0]['row'], testing.SHOP_WOMAN)

    def test_practice_battle_rejects_changed_story_identity_and_incompatible_assets(self):
        for change in ('story', 'map', 'stage', 'stage-parent', 'stage-levels',
                       'stage-collision', 'collision', 'monster', 'return'):
            with self.subTest(change=change), tempfile.TemporaryDirectory() as root:
                tables, rows, _ = practice_game()
                if change == 'story': tables[testing.SHOP_EVENT][testing.SHOP_WOMAN]['OnFlagList'] = [123]
                elif change == 'map': tables[testing.MAP]['01Gra_20']['ID'] = 2001
                elif change == 'stage': tables[testing.STAGE_COMPOSITE].clear()
                elif change == 'stage-parent': tables[testing.STAGE]['plains']['isLoadLevelInstance'] = True
                elif change == 'stage-levels':
                    for rel in (testing.STAGE, testing.STAGE_COMPOSITE):
                        tables[rel]['plains']['battleLevelList'] = ['different level']
                elif change == 'stage-collision':
                    tables[testing.STAGE_COMPOSITE]['existing'] = {'ID': 29990}
                elif change == 'collision': tables[testing.GROUP]['normal']['ID'] = testing.PRACTICE_ID
                elif change == 'monster': tables[native.UNIT]['Wild Rat']['Level'] = 99
                else: tables[testing.GROUP]['plant and rats']['battleFinishTransition']['mapId'] = 2001
                path = Path(root) / testing.CONFIG; path.parent.mkdir(parents=True)
                path.write_text(json.dumps({'schema': 1, 'maxMr': False, 'practiceBattle': True}))
                with self.assertRaises(ValueError): testing.prepare({}, [], root, rows)

    def test_practice_only_route_creates_empty_roster_and_legacy_mr_updates_preserve_it(self):
        routes = {}
        class App:
            def get(self, path):
                def route(func): routes['get'] = func; return func
                return route
            def put(self, path):
                def route(func): routes['put'] = func; return func
                return route
        class Error(Exception):
            def __init__(self, code, detail): super().__init__(detail)
        with tempfile.TemporaryDirectory() as root, mock.patch.dict('sys.modules', {'fastapi': SimpleNamespace(HTTPException=Error)}):
            testing.register(App(), {'ROOT': root})
            routes['put']({'schema': 1, 'maxMr': False, 'practiceBattle': True})
            self.assertEqual(json.loads((Path(root) / 'mods/EstherTsukiko/units.json').read_bytes()), [])
            routes['put']({'schema': 1, 'maxMr': True})
            self.assertTrue(routes['get']()['practiceBattle'])
            self.assertTrue(routes['get']()['maxMr'])
            routes['put']({'schema': 1, 'maxMr': True, 'practiceBattle': False})
            self.assertFalse(routes['get']()['practiceBattle'])
            with self.assertRaises(Error): routes['put']({'schema': 1, 'maxMr': True, 'practiceBattle': 'true'})


if __name__ == '__main__': unittest.main()
