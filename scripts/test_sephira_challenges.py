"""Original unlocks, victory-only rewards, shared boss budgets and cooked AI."""
import copy
import gzip
import json
from pathlib import Path
import re
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT/'assets/existing_visions/payload'))
import _ffr_shrine_challenges as challenge
import _ffr_crystal_cave as caves
import _ffr_testing as testing
import _ffr_fina_boss as fina
from test_crystal_fina_boss import choose, native_ai


def fixture():
    return json.loads(gzip.decompress((ROOT/'scripts/fixtures/sephira_challenges/rows.json.gz').read_bytes()))


def roster():
    catalog = json.loads((ROOT/'assets/sephira_visions/catalog.json').read_bytes())
    return [dict(p['profile'], sephiraVision={'version': 1, 'preset': p['id'], 'enabled': True})
            for p in catalog['presets']]


class SephiraChallengeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.native, cls.units = fixture(), roster()
        with tempfile.TemporaryDirectory() as root:
            cls.tables = testing.prepare({}, cls.units, root, lambda rel: cls.native[rel])
        cls.built = copy.deepcopy(cls.native)
        for rel, plan in cls.tables.items():
            for edit in plan['add']:
                cls.built[rel][edit['row']] = testing.apply_fields(cls.built[rel][edit['cloneFrom']], edit['set'])
            for edit in plan['set']:
                cls.built[rel][edit['row']] = testing.apply_fields(cls.built[rel][edit['row']], edit['set'])

    def test_christine_is_offered_behind_rains_house_only_after_tronn_and_until_won(self):
        name = challenge.PREFIX + '13024'
        entry = name + '_Return'
        unit = next(u for u in self.units if u['sephiraVision']['preset'] == 'christine')
        branches = self.built[challenge.COMPOSITE][entry]['ContinuousEventList']
        def matches(condition, items, flags):
            def token(text):
                item = re.fullmatch(r'\{item:(\d+)\}(>0|==0)', text)
                if item: return (int(item[1]) in items) == (item[2] == '>0')
                flag = re.fullmatch(r'(!?)\{flag:(\d+)\}', text)
                self.assertIsNotNone(flag, text)
                return (int(flag[2]) in flags) != bool(flag[1])
            return any(all(token(part) for part in alternative.split('&')) for alternative in condition.split('|'))
        for owns_tronn in (False, True):
            for story_flag in (False, True):
                for owns_christine in (False, True):
                    items = ({13024} if owns_tronn else set()) | ({unit['id']} if owns_christine else set())
                    flags = {147} if story_flag else set()
                    active = [b['EventId'] for b in branches if matches(b['Condition'], items, flags)]
                    should_offer = (owns_tronn or story_flag) and not owns_christine
                    self.assertEqual(active, [name + ('_Menu' if should_offer else '_Close')])
        for rel in ('Map/MapData/DT_MapData_01Gra', caves.COMPOSITE):
            original = self.native[rel]['01Gra_44']
            self.assertEqual(self.built[rel]['01Gra_44'], {
                **original, 'startupEventList': [*original['startupEventList'],
                    {'Condition': branches[0]['Condition'], 'EventId': entry}], 'battleStage': 27500})
            self.assertEqual(self.built[rel]['01Gra_44']['battleStage'], 27500)
        event = self.built[challenge.COMPOSITE][entry]
        self.assertEqual(event['ObtainItemList'] + event['OnFlagList'] + event['ProgressList'], [])
        menu = self.built[challenge.CHOICES][name + '_Menu']
        self.assertEqual(menu['ChoiceTextList'][-1], 'Leave')
        self.assertEqual(menu['CancelIndex'], len(menu['ChoiceTextList']) - 1)

    def test_christine_return_prompt_is_absent_when_removed_or_moved_to_the_shop(self):
        for moved in (False, True):
            units = copy.deepcopy(self.units)
            christine = next(u for u in units if u['sephiraVision']['preset'] == 'christine')
            if moved: christine['studioAcquisition'] = {'version': 1, 'location': 'mitra_shop', 'random': False, 'hideSpoilers': True}
            else: units.remove(christine)
            with tempfile.TemporaryDirectory() as root:
                operations = testing.prepare({}, units, root, lambda rel: self.native[rel])
            for rel, plan in operations.items():
                self.assertFalse(any(e['row'] == challenge.PREFIX + '13024_Return' for e in plan['add']))
                if rel in ('Map/MapData/DT_MapData_01Gra', caves.COMPOSITE):
                    self.assertFalse(any(e['row'] == '01Gra_44' for kind in ('set', 'add') for e in plan[kind]))

    def test_all_original_grants_and_native_replay_targets_are_preserved(self):
        for spec, units in challenge.plans(self.units):
            event = spec['grantEvent']
            self.assertEqual(self.native[challenge.COMPOSITE][event], self.built[challenge.COMPOSITE][event])
            self.assertIn(spec['origin'], [i['ID'] for i in self.native[challenge.COMPOSITE][event]['ObtainItemList']])
            if spec['retry']:
                target = spec['retry'][:-2] + '02'
                self.assertEqual(self.native[challenge.COMPOSITE][target], self.built[challenge.COMPOSITE][target])
                choices = self.built[challenge.COMPOSITE][challenge.PREFIX+str(spec['origin'])+'_Menu']
                self.assertIn(target, [e['EventId'] for branch in choices['ChoicesBranchEventList'] for e in branch['EventList']])
        self.assertEqual(len(challenge.plans(self.units)), 15)
        self.assertEqual(sum(len(u) for _, u in challenge.plans(self.units)), 28)

    def test_unlock_gate_applies_to_every_origin_and_again_at_battle_start(self):
        events = self.built[challenge.COMPOSITE]
        for spec, units in challenge.plans(self.units):
            name = challenge.PREFIX+str(spec['origin'])
            for key in (name, name+'_Start', name+'_Win'):
                branches = events[key]['ContinuousEventList']
                self.assertEqual(branches[0]['Condition'], spec['unlock'])
                self.assertIn('{item:'+str(spec['origin'])+'}>0', branches[0]['Condition'])
                self.assertTrue(branches[1]['Condition'].startswith('{item:'+str(spec['origin'])+'}==0&'))
                self.assertEqual(events[key]['OnFlagList'], [])
                self.assertEqual(events[key]['ProgressList'], [])
            if spec['origin'] == 13062:
                self.assertIn('{progress:48}>=50', spec['unlock'])
                self.assertNotIn('>=10', spec['unlock'])
            if spec['origin'] == 13024: self.assertIn('{flag:147}', spec['unlock'])
        # No shared "some legend completed" flag can unlock a different vision.
        self.assertTrue(all('{flag:1017}' not in s['unlock'] for s, _ in challenge.plans(self.units)))

    def test_only_victory_can_reach_rewards_and_each_reward_is_conditional(self):
        events = self.built[challenge.COMPOSITE]
        for spec, units in challenge.plans(self.units):
            name = challenge.PREFIX+str(spec['origin'])
            group = self.built[challenge.GROUP][name]
            self.assertEqual(group['battleFinishEventId'], name+'_Win')
            self.assertFalse(group['battleFinishEscapeEventId'])
            self.assertFalse(group['battleFinishLoseEventId'])
            grant = events[name+'_Grant']
            self.assertEqual(grant['EventSequence'], '/Game/'+challenge.SEQUENCE+'SEQ_Grant')
            self.assertEqual(grant['ObtainItemList'], [
                {'Condition': f'{{item:{u["id"]}}}==0', 'ID': u['id'], 'Num': 1, 'Text': ''} for u in units])
            for suffix in ('', '_Available', '_Menu', '_Start', '_Fight', '_Close', '_Locked', '_Done'):
                self.assertEqual(events[name+suffix]['ObtainItemList'], [])
            self.assertFalse(group['isResultSkipOnWin'])
            self.assertTrue(group['CanEscape'])
        # The shared cave actors must never retain their former free grants.
        cave_events = [e for k,e in events.items() if k.startswith('Studio_ResonanceCave_') and k.endswith('_Acquire')]
        self.assertEqual(len(cave_events), 2)
        self.assertTrue(all(not e['ObtainItemList'] and e['encountGroupId'] == -1 for e in cave_events))

    def test_team_durability_is_one_boss_budget_and_rotation_executes(self):
        rows = lambda rel: self.native[rel]
        for spec, units in challenge.plans(self.units):
            stats = challenge.team_stats(rows, spec['level'], units)
            self.assertEqual(sum(v['MaxHitPoint'] for v in stats), challenge.curve(rows, spec['level'])['MaxHitPoint'])
            for index, unit in enumerate(units):
                kit = challenge.kit(unit, rows, len(units))
                rotation = challenge.rotation(unit, kit, index)
                self.assertEqual(len(kit), 1+sum(g[0]=='ActiveSkill' for f in ('awakening','synchro') for t in unit[f] for g in t))
                self.assertTrue(all(r['fields']['Cost']==0 for r in kit if 'Cost' in r['fields']))
                authored = fina.author_ai(native_ai(), rotation)
                for turn in range(24):
                    action = rotation[turn%8]
                    self.assertEqual(choose(authored, turn, .49), action['id'])
                    self.assertEqual(choose(authored, turn, 1), rotation[0]['id'] if action['healing'] else action['id'])
                self.assertTrue(any(r['damaging'] for r in rotation))
                self.assertTrue(challenge.needs_enemy_motion(unit))
                identity = challenge.boss_id(unit)
                row = next(v for v in self.built[challenge.UNIT].values() if v['ID']==identity)
                self.assertEqual(row['Level'], spec['level'])
                self.assertEqual(row['Experience']+row['Money'], 0)

    def test_moved_removed_and_disabled_profiles_cannot_spawn_challenge_rewards(self):
        moved = copy.deepcopy(self.units)
        for u in moved:
            if u['sephiraVision']['preset'] == 'christine':
                u['studioAcquisition'] = {'version':1, 'location':'mitra_shop', 'random':False, 'hideSpoilers':True}
        self.assertNotIn(13024, [s['origin'] for s, _ in challenge.plans(moved)])
        self.assertEqual(challenge.plans([]), [])
        disabled = copy.deepcopy(self.units[0]); disabled['sephiraVision']['enabled'] = False
        with self.assertRaises(ValueError): challenge.plans([disabled])
        self.assertFalse(challenge.enemy_motion_for([disabled], disabled['id']))
        self.assertFalse(challenge.enemy_motion_for([disabled], 13599))
        self.assertTrue(challenge.enemy_motion_for(self.units, self.units[0]['id']))
        self.assertEqual(caves.assignment(self.units[0]), None)
        self.assertEqual(caves.assignment(next(u for u in self.units if challenge.route(u)==13062)), challenge.cave_snapshot())

    def test_folka_is_story_gated_and_costs_twice_the_highest_other_item(self):
        key, source = next((k,v) for k,v in self.native['Shop/DT_ShopList'].items() if v['ShopID']==10)
        actual = self.built['Shop/DT_ShopList'][key]
        folka = next(u for u in self.units if u['sephiraVision']['preset']=='folka')
        added = next(i for i in actual['ItemList'] if i['ItemId']==folka['id'])
        items = {v['ID']:v for rel, values in self.native.items() if rel.startswith('Item/DT_') for v in values.values()}
        cost = max(items[i['ItemId']]['buyingPrice']*i['PriceRatio'] for i in source['ItemList'] if i['ItemId']!=-1)
        self.assertAlmostEqual(added['PriceRatio']*folka['price'], 2*cost, places=2)
        self.assertEqual(added['Condition'], '{progress:0}>=3150')
        self.assertEqual(added['MaxOrderNum'], 1)
        self.assertEqual([i for i in actual['ItemList'] if i['ItemId'] not in (-1, folka['id'])], [i for i in source['ItemList'] if i['ItemId']!=-1])

    def test_tronn_interaction_retains_native_streams_and_actor_graph(self):
        path = ROOT/'scripts/fixtures/sephira_challenges'
        room = json.loads(gzip.decompress((path/'tronn-room.json.gz').read_bytes()))
        trigger = json.loads(gzip.decompress((path/'crystal-interaction.json.gz').read_bytes()))
        before = copy.deepcopy((room, trigger))
        views = challenge.tronn_views(room, trigger)
        self.assertEqual((room, trigger), before)
        private = views[challenge.SEQUENCE+'Studio_TronnCrystal_EV']
        owner = caves.export(private, 'BP_MapGimmick_EventTrigger_C_1')[1]
        event, = caves.property_data(owner, 'm_EventList')['Value']
        self.assertEqual(caves.property_data(event, 'EventId')['Value'], challenge.PREFIX+'13024')
        self.assertIn(challenge.PREFIX.rstrip('_'), private['NameMap'][:private['NamesReferencedFromExportDataCount']])
        built = views['Map/Com/00Com/00Com_237/Com_00Com_237_PL']
        self.assertEqual(len(built['Exports']), len(room['Exports'])+1)
        for name in ('LevelStreamingDynamic_0', 'LevelStreamingDynamic_1'):
            self.assertEqual(caves.export(built, name)[1], caves.export(room, name)[1])
        for view in views.values(): caves.check_object_names(view)


if __name__ == '__main__': unittest.main()
