"""Original-item grants, clean-save controls and bounded native MR rewards."""
import copy
import gzip
import json
from pathlib import Path
import tempfile
import sys
import unittest
from types import SimpleNamespace
from unittest import mock
from test_existing_visions import ROOT, fixture, native
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
    source_events = json.loads((ROOT/'scripts/fixtures/practice_dialog/talk-events.json').read_bytes())['rows']
    woman = copy.deepcopy(source_events['DT_Town_010Gra_20_0920_8'])
    # Explicit identities from the observed conversation: do not derive the
    # fixture key from the implementation's selected NPC constant.
    other_woman = copy.deepcopy(woman); other_woman['ArgList'] = {'id': '39'}
    tables[testing.SHOP_EVENT] = {'DT_Town_010Gra_20_0920_8': woman,
                                'DT_Town_010Gra_20_1170_1': other_woman, 'shopkeeper': {'shop': 1}}
    tables[testing.SHOP_EVENT].update(copy.deepcopy(source_events))
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
    tables[testing.GROUP]['Cactuar solo'] = {
        **copy.deepcopy(tables[testing.GROUP]['plant and rats']),
        'ID': 4035, 'UnitIdList': [38], 'locationIdList': [10], 'ap': 220}
    tables[native.UNIT]['Cactuar'] = {'ID': 38, 'Level': 30, 'Category': 'Enemy', 'MaxHitPoint': 1111}
    tables[testing.CHOICES] = {'native choice': {'ChoiceTag': {'TagName': 'native'}, 'ChoiceTextList': ['Yes', 'No'],
        'DefaultIndex': 0, 'CancelIndex': 1, 'ChoiceDialogType': 'Normal'}}
    # Independent supplied-game rows: do not manufacture categories/levels
    # from the implementation's opponent list. That hid the Boss-category bug.
    source = json.loads((ROOT/'scripts/fixtures/practice_dialog/opponents.json').read_bytes())['rows']
    for source_key, original in source.items():
        key = next((k for k,v in tables[native.UNIT].items() if v.get('ID') == original['ID']), source_key)
        tables[native.UNIT].setdefault(key, {}).update(copy.deepcopy(original))
    boss_rows = json.loads(gzip.decompress((ROOT/'scripts/fixtures/crystal_fina_boss/rows.json.gz').read_bytes()))
    for rel, data in boss_rows.items(): tables.setdefault(rel, {}).update(data)
    return tables, lambda rel: copy.deepcopy(tables[rel]), unit


class NativeTestingTests(unittest.TestCase):
    def test_default_off_requires_no_assets_and_does_not_change_tables(self):
        with tempfile.TemporaryDirectory() as root:
            self.assertEqual(testing.settings(root), {'schema': 1, 'maxMr': False, 'practiceBattle': False, 'practiceEncounter': 'standard', 'surviveAtOne': False, 'ffbeNeedles': False, 'finaCinematic': False, 'crystalCave': False, 'crystalCaveTest': False, 'fieldLeader': False, 'noEncounters': False, 'autoBattle': False})
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
            self.assertNotIn('crystalCaveTestSolid', get())
            self.assertNotIn('crystalCaveTestRotate', get())
            put({'schema': 1, 'maxMr': False, 'crystalCaveTestRotate': True})
            self.assertFalse((Path(root) / 'mods/EstherTsukiko/units.json').exists())
            put({'schema': 1, 'maxMr': False, 'crystalCaveTestSolid': False})
            self.assertFalse((Path(root) / 'mods/EstherTsukiko/units.json').exists())
            put({'schema': 1, 'maxMr': True}); self.assertTrue(get()['maxMr'])
            self.assertNotIn('crystalCaveTestSolid', get())
            self.assertNotIn('crystalCaveTestRotate', get())
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
                                   testing.STAGE, testing.STAGE_COMPOSITE, testing.CHOICES,
                                   *json.loads(gzip.decompress((ROOT/'scripts/fixtures/crystal_fina_boss/rows.json.gz').read_bytes()))})
        self.assertEqual(len(expected), 4)
        for rel, op in ops.items():
            built = copy.deepcopy(original[rel])
            for edit in op['set']: built[edit['row']] = testing.apply_fields(built[edit['row']], edit['set'])
            for edit in op['add']: built[edit['row']] = testing.apply_fields(original[rel][edit['cloneFrom']], edit['set'])
            testing.check_rows(original[rel], built, op)
            if rel in (testing.SHOP_EVENT, testing.COMPOSITE):
                self.assertEqual(op['set'], [])
                self.assertEqual(built[testing.SHOP_WOMAN]['encountGroupId'], -1)
                self.assertEqual(built[testing.SHOP_WOMAN]['ContinuousEventList'][0]['EventId'], testing.PRACTICE + '_Menu_A')
                self.assertEqual(built[testing.SHOP_WOMAN]['ArgList'], {'id': '6'})
                self.assertEqual(built['DT_Town_010Gra_20_1170_1'], original[rel]['DT_Town_010Gra_20_1170_1'])
                self.assertEqual(built['shopkeeper'], original[rel]['shopkeeper'])
                self.assertEqual(built[testing.SHOP_WOMAN]['EventSequence'], original[rel][testing.SHOP_WOMAN]['EventSequence'])
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
            elif rel == testing.GROUP:
                encounter = built[testing.PRACTICE + '_standard']
                self.assertEqual(encounter['UnitIdList'], [20, 22, 22])
                self.assertEqual(encounter['locationIdList'], [20, 6, 15])
                self.assertEqual(encounter['probabilityOfSuccessfulEscape'], 100.0)
                self.assertEqual(encounter['battleFinishTransition'], {'mapId': -1, 'bDoAutoSave': False})
                self.assertEqual(encounter['ap'], 20)
        with tempfile.TemporaryDirectory() as root:
            self.assertEqual(testing.prepare({}, [], root, rows), {})

    def test_dialog_pages_reach_every_opponent_and_cancel_has_no_battle(self):
        original, rows, _ = practice_game()
        with tempfile.TemporaryDirectory() as root:
            path = Path(root)/testing.CONFIG; path.parent.mkdir(parents=True)
            path.write_text(json.dumps({'schema': 1, 'maxMr': False, 'practiceBattle': True}))
            ops = testing.prepare({}, [], root, rows)
        events = {e['row']: testing.apply_fields(original[testing.COMPOSITE][e['cloneFrom']], e['set'])
                  for e in ops[testing.COMPOSITE]['add']}
        dialogs = {e['row']: testing.apply_fields(original[testing.CHOICES][e['cloneFrom']], e['set'])
                   for e in ops[testing.CHOICES]['add']}
        targets = []
        for page in range(7):
            key = testing.PRACTICE + '_Menu_' + chr(65+page)
            branches = events[key]['ChoicesBranchEventList']
            count = 2 if page < 6 else 1
            self.assertEqual([v['Index'] for v in branches], list(range(count+1)))
            self.assertEqual(dialogs[key]['CancelIndex'], count+1)
            self.assertEqual(dialogs[key]['ChoiceTextList'][-1], 'Cancel')
            self.assertEqual(branches[count]['EventList'][0]['EventId'], testing.PRACTICE+'_Menu_'+chr(65+(page+1)%7))
            targets.extend(v['EventList'][0]['EventId'] for v in branches[:count])
        self.assertEqual(len(set(targets)), 13)
        self.assertEqual({events[t]['encountGroupId'] for t in targets}, set(range(29990,30003)))
        for target in targets:
            event = events[target]
            self.assertEqual(event['EventSequence'], 'None')
            self.assertEqual(event['OnFlagList'], [])
            self.assertFalse(event['OverwriteBattleParty'])
            self.assertFalse(event['IsSetAutoSave'])

    def test_menu_link_uses_populated_struct_donor_and_restores_all_original_npc_fields(self):
        original, rows, _ = practice_game()
        with tempfile.TemporaryDirectory() as root:
            path = Path(root)/testing.CONFIG; path.parent.mkdir(parents=True)
            path.write_text(json.dumps({'schema':1,'maxMr':False,'practiceBattle':True}))
            ops = testing.prepare({}, [], root, rows)
            expected = testing.expected_edits(root, [], rows)
        for rel in (testing.SHOP_EVENT, testing.COMPOSITE):
            woman = original[rel][testing.SHOP_WOMAN]
            self.assertEqual(woman['ContinuousEventList'], [])
            replacement, = [e for e in ops[rel]['add'] if e['row'] == testing.SHOP_WOMAN]
            donor = original[rel][replacement['cloneFrom']]
            self.assertTrue(donor['ContinuousEventList'])
            self.assertTrue(donor['OnFlagList'])
            self.assertTrue(donor['ProgressList'])
            self.assertTrue(donor['RequestStateSettings'])
            built = testing.apply_fields(donor, replacement['set'])
            delta = {'ContinuousEventList': [{'Condition':'','EventId':testing.PRACTICE+'_Menu_A'}]}
            self.assertEqual(built, testing.apply_fields(woman, delta))
            self.assertEqual(expected[(rel, testing.SHOP_WOMAN)], delta)
            # Every populated struct array must have native elements to clone.
            # An empty synthetic donor would let Python pass while ffr-dt fails.
            for edit in ops[rel]['add']:
                template = original[rel][edit['cloneFrom']]
                for field, value in edit['set'].items():
                    if isinstance(value, list) and value and isinstance(value[0], dict):
                        self.assertTrue(template[field], (edit['row'], field))

    def test_source_enemy_and_boss_rows_are_accepted_without_reclassifying_them(self):
        original, rows, _ = practice_game()
        source = original[native.UNIT]
        bosses = {v['ID']:v for v in source.values() if v.get('Category') == 'Boss'}
        self.assertEqual(set(bosses), {352,641,651,401})
        with tempfile.TemporaryDirectory() as root:
            path = Path(root)/testing.CONFIG; path.parent.mkdir(parents=True)
            path.write_text(json.dumps({'schema':1,'maxMr':False,'practiceBattle':True}))
            ops = testing.prepare({}, [], root, rows)
        self.assertEqual(ops[native.UNIT]['set'], [])
        self.assertEqual(len(ops[testing.GROUP]['add']), 13)
        self.assertTrue({352,641,651} <= {v['set']['UnitIdList'][0] for v in ops[testing.GROUP]['add']})
        self.assertEqual(source, rows(native.UNIT))
        for identity in (352,641,651):
            key = next(k for k,v in source.items() if v.get('ID') == identity)
            for category in ('Playable','Summon'):
                with self.subTest(identity=identity, category=category), tempfile.TemporaryDirectory() as root:
                    data = copy.deepcopy(original); data[native.UNIT][key]['Category'] = category
                    path = Path(root)/testing.CONFIG; path.parent.mkdir(parents=True)
                    path.write_text(json.dumps({'schema':1,'maxMr':False,'practiceBattle':True}))
                    with self.assertRaisesRegex(ValueError, str(identity)):
                        testing.prepare({}, [], root, lambda rel:copy.deepcopy(data[rel]))

    def test_private_choice_uses_unbound_native_talk_calls_and_compiled_times(self):
        import gzip
        from test_existing_visions import ROOT, module
        with mock.patch.dict('sys.modules', {'ffbe_lb': SimpleNamespace(NEUTRAL_COLOR='#808080')}):
            seq = module('practice_sequence_fixture', ROOT/'scripts/fixtures/engine_motion/ffbe_resonance.py')
        shell = json.loads(gzip.decompress((ROOT/'scripts/fixtures/practice_dialog/shell.json.gz').read_bytes()))
        tag = 'UI.Dialog.Choice.Studio_PracticeBattle_Menu_A'
        with mock.patch.dict('sys.modules', {'ffbe_resonance':seq}):
            built = testing.author_practice_choice(shell,tag)
            testing.verify_practice_choice(built,tag)
            root = next(e for e in built['Exports'] if e['ClassIndex']<0 and built['Imports'][-e['ClassIndex']-1]['ObjectName']=='LevelSequence')
            self.assertEqual(seq.child(root['Data'],'BindingReferences','SortedReferences'),[])
            tags = [i for i in built['Imports'] if i['ObjectName']=='GameplayTag']
            self.assertEqual(built['Imports'][-tags[0]['OuterIndex']-1]['ObjectName'],'/Script/GameplayTags')
            with self.assertRaises(ValueError): testing.verify_practice_choice(built,tag+'Wrong')

    def test_all_menu_pages_keep_appended_script_names_in_the_packed_name_prefix(self):
        import gzip
        from test_existing_visions import module
        with mock.patch.dict('sys.modules', {'ffbe_lb':SimpleNamespace(NEUTRAL_COLOR='#808080')}):
            seq = module('practice_name_fixture', ROOT/'scripts/fixtures/engine_motion/ffbe_resonance.py')
        shell = json.loads(gzip.decompress((ROOT/'scripts/fixtures/practice_dialog/shell.json.gz').read_bytes()))
        self.assertEqual(shell['NamesReferencedFromExportDataCount'],36)
        original_names = shell['NameMap'][:]
        for page in 'ABCDEFG':
            with self.subTest(page=page), mock.patch.dict('sys.modules',{'ffbe_resonance':seq}):
                tag = 'UI.Dialog.Choice.Studio_PracticeBattle_Menu_'+page
                built = testing.author_practice_choice(copy.deepcopy(shell),tag)
                self.assertEqual(built['NameMap'][:len(original_names)],original_names)
                self.assertEqual(built['NameMap'].index(tag),79)
                kept = built['NameMap'][:built['NamesReferencedFromExportDataCount']]
                self.assertEqual(kept[79],tag)
                testing.verify_practice_choice(built,tag)
                restored = copy.deepcopy(built)
                restored['NameMap'].append('/Engine/UnknownPackage')
                testing.verify_practice_choice(restored,tag)
                broken = copy.deepcopy(built)
                broken['NamesReferencedFromExportDataCount'] = 36
                with self.assertRaisesRegex(ValueError,'lose script names'):
                    testing.verify_practice_choice(broken,tag)

    def test_survival_is_unlimited_native_damage_time_reprieve_and_preserves_other_passives(self):
        effects = {
            'reprieve': {'ID': 1359, 'EffectType': 'Reprieve', 'ParamList': [0,-1]+[-1]*13,
                'activationCondition': {'Condition':'None'}, 'activationProbability':100, 'effectEndActionNum':-1},
            'death': {'ID': 1411, 'EffectType':'AddStatusConditionRegist','ParamList':[13,1000]+[-1]*13}}
        bundle = {'effectId':1359,'passiveSkillAddTiming':'SpawnUnit','TargetType':'Self','targetRelation':'Friendlies'}
        data = {'Skill/DT_SkillEffectData': effects,
            'Skill/DT_PassiveSkillData': {'original':{'ID':1259,'effectBundleList':[bundle,dict(bundle),dict(bundle)]}},
            'Unit/DT_UnitParameter': {'Rain': {'ID':1001,'Category':'Playable','passiveSkillList':[7]},
                'Lasswell': {'ID':1002,'Category':'Playable','passiveSkillList':[]},
                'enemy':{'ID':38,'Category':'Enemy','passiveSkillList':[]}}}
        before = copy.deepcopy(data)
        ops = {'Unit/DT_UnitParameter': {'asset':'existing','add':[], 'set':[{'row':'Rain','set':{'passiveSkillList':[7,8]}}]}}
        def table(rel): return ops.setdefault(rel, {'asset':rel,'add':[],'set':[]})
        testing.prepare_survival(table, lambda rel: copy.deepcopy(data[rel]))
        self.assertEqual(data, before)
        self.assertEqual(ops['Unit/DT_UnitParameter']['set'][-2]['set']['passiveSkillList'],[7,8,29660])
        self.assertFalse(any(e['row']=='enemy' for e in ops['Unit/DT_UnitParameter']['set']))
        private = ops['Skill/DT_PassiveSkillData']['add'][0]['set']
        self.assertTrue(private['bBattleOnly']); self.assertFalse(private['isRemovable'])
        self.assertEqual([v['effectId'] for v in private['effectBundleList']][:2],[29661,29662])
        self.assertFalse(any('HitPoint' in str(e) or 'Damage' in str(e) for e in ops['Unit/DT_UnitParameter']['set']))
        effects['reprieve']['ParamList'][1] = 1
        with self.assertRaises(ValueError): testing.prepare_survival(table, lambda rel:copy.deepcopy(data[rel]))
        for bad in (1, 'true', None):
            with self.assertRaises(ValueError): testing.validate_settings({'schema':1,'maxMr':False,'surviveAtOne':bad})

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
        self.assertEqual(ops[testing.COMPOSITE]['add'][-1]['row'], testing.SHOP_WOMAN)

    def test_cactuar_uses_original_solo_group_without_rewriting_enemy_ai_or_skills(self):
        original, rows, _ = practice_game(); before = copy.deepcopy(original)
        for max_mr in (False, True):
            with self.subTest(max_mr=max_mr), tempfile.TemporaryDirectory() as root:
                path = Path(root) / testing.CONFIG; path.parent.mkdir(parents=True)
                path.write_text(json.dumps({'schema': 1, 'maxMr': max_mr,
                                           'practiceBattle': True, 'practiceEncounter': 'cactuar'}))
                ops = testing.prepare({}, [], root, rows)
                group_op = ops[testing.GROUP]
                add = next(v for v in group_op['add'] if v['row'].endswith('_cactuar'))
                group = testing.apply_fields(original[testing.GROUP][add['cloneFrom']], add['set'])
                self.assertEqual(group['UnitIdList'], [38])
                self.assertEqual(group['locationIdList'], [10])
                self.assertEqual(group['ap'], 4995 if max_mr else 20)
                self.assertEqual(group['ID'], testing.PRACTICE_ID + 1)
                self.assertEqual(group['probabilityOfSuccessfulEscape'], 100.0)
                self.assertEqual(group['battleFinishTransition']['mapId'], -1)
                self.assertFalse(group['battleFinishTransition']['bDoAutoSave'])
                self.assertEqual(original, before)
                self.assertTrue(all(not op['set'] for rel, op in ops.items() if 'Skill' in rel or 'Unit' in rel))
                self.assertTrue(all(e['row'].startswith('Studio_CrystalFinaBoss') for rel, op in ops.items()
                                    if 'Skill' in rel or 'Unit' in rel for e in op['add']))

    def test_cactuar_choice_defaults_and_rejects_changed_or_unknown_encounters(self):
        for bad in (None, True, 38, [], {}, 'unknown'):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                testing.validate_settings({'schema': 1, 'maxMr': False, 'practiceEncounter': bad})
        for change in ('monster', 'choice-template', 'branch-template', 'continuous-template'):
            tables, rows, _ = practice_game()
            if change == 'monster': tables[native.UNIT]['Cactuar']['Level'] = 99
            elif change == 'choice-template': tables[testing.CHOICES].clear()
            elif change == 'branch-template': del tables[testing.SHOP_EVENT]['DT_Town_010Gra_20_0920_5']
            else: del tables[testing.SHOP_EVENT]['DT_Town_010Gra_20_0930_1']
            with self.subTest(change=change), tempfile.TemporaryDirectory() as root:
                path = Path(root) / testing.CONFIG; path.parent.mkdir(parents=True)
                path.write_text(json.dumps({'schema': 1, 'maxMr': False, 'practiceBattle': True}))
                with self.assertRaises(ValueError): testing.prepare({}, [], root, rows)

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
            routes['put']({'schema': 1, 'maxMr': False, 'practiceBattle': True, 'practiceEncounter': 'cactuar', 'ffbeNeedles': True})
            self.assertEqual(json.loads((Path(root) / 'mods/EstherTsukiko/units.json').read_bytes()), [])
            routes['put']({'schema': 1, 'maxMr': True})
            self.assertTrue(routes['get']()['practiceBattle'])
            self.assertTrue(routes['get']()['maxMr'])
            self.assertEqual(routes['get']()['practiceEncounter'], 'cactuar')
            self.assertTrue(routes['get']()['ffbeNeedles'])
            routes['put']({'schema': 1, 'maxMr': True, 'practiceBattle': False})
            self.assertFalse(routes['get']()['practiceBattle'])
            self.assertEqual(routes['get']()['practiceEncounter'], 'cactuar')
            self.assertTrue(routes['get']()['ffbeNeedles'])
            with self.assertRaises(Error): routes['put']({'schema': 1, 'maxMr': True, 'practiceBattle': 'true'})


if __name__ == '__main__': unittest.main()
