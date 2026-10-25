"""Original unlocks, victory-only rewards, shared boss budgets and cooked AI."""
import copy
import gzip
import json
from pathlib import Path
import re
import sys
import tempfile
import unittest
from unittest import mock

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

    def test_christine_crystal_dialog_checks_tronn_and_only_offers_unowned_reward(self):
        name = challenge.PREFIX + '13024'
        unit = next(u for u in self.units if u['sephiraVision']['preset'] == 'christine')
        def matches(condition, items, flags, progress):
            def token(text):
                item = re.fullmatch(r'\{item:(\d+)\}(>0|==0)', text)
                if item: return (int(item[1]) in items) == (item[2] == '>0')
                story = re.fullmatch(r'\{progress:0\}(>=|<)([0-9]+)', text)
                if story: return (progress >= int(story[2])) == (story[1]=='>=')
                flag = re.fullmatch(r'(!?)\{flag:(\d+)\}', text)
                self.assertIsNotNone(flag, text)
                return (int(flag[2]) in flags) != bool(flag[1])
            return any(all(token(part) for part in alternative.split('&')) for alternative in condition.split('|'))
        for owns_tronn in (False, True):
            for progress in (1089,1090,1095,1200):
                for owns_christine in (False, True):
                    items = ({13024} if owns_tronn else set()) | ({unit['id']} if owns_christine else set())
                    flags = set()  # C01_015_01 clears the temporary tutorial flag.
                    state = name
                    while True:
                        branches = self.built[challenge.COMPOSITE][state]['ContinuousEventList']
                        if not branches: break
                        active = [b['EventId'] for b in branches if matches(b['Condition'],items,flags,progress)]
                        self.assertEqual(len(active),1)
                        state = active[0]
                    expected = '_Locked' if not (owns_tronn or progress>=1090) else '_Done' if owns_christine else '_Menu'
                    self.assertEqual(state,name+expected)
        for rel in ('Map/MapData/DT_MapData_01Gra', caves.COMPOSITE):
            original = self.native[rel]['01Gra_20']
            self.assertEqual(self.built[rel]['01Gra_20'], {**original, 'battleStage': 27500})
        self.assertNotIn(name+'_Return',self.built[challenge.COMPOSITE])
        menu = self.built[challenge.CHOICES][name+'_Menu']
        self.assertEqual(menu['ChoiceTextList'][-1],'Leave')
        self.assertEqual(menu['CancelIndex'],len(menu['ChoiceTextList'])-1)

    def test_rikku_swaps_with_lunafreya_without_moving_eiko_or_changing_group_budgets(self):
        import _ffr_sephira as pack
        groups={spec['origin']:(spec,units) for spec,units in challenge.plans(self.units)}
        for origin,expected in [(13118,{'rikku','eiko'}),(13124,{'lunafreya','elephim'})]:
            spec,units=groups[origin]
            self.assertEqual({u['sephiraVision']['preset'] for u in units},expected)
            self.assertIn('{item:'+str(origin)+'}>0',spec['unlock'])
            self.assertEqual(sum(s['MaxHitPoint'] for s in challenge.team_stats(lambda p:self.native[p],spec['level'],units)),
                             challenge.curve(lambda p:self.native[p],spec['level'])['MaxHitPoint'])
        for key,(old,new) in pack.ACQUISITION_SWAPS.items():
            u=copy.deepcopy(next(u for u in self.units if u['sephiraVision']['preset']==key))
            for field in ('studioAcquisition','sephiraAcquisition'):u[field]['location']=old
            u['studioAcquisition']['hideSpoilers']=False
            pack.repair_default_acquisition(u)
            self.assertEqual(u['studioAcquisition']['location'],new)
            self.assertFalse(u['studioAcquisition']['hideSpoilers'])
            u['studioAcquisition']['location']=old
            pack.repair_default_acquisition(u)
            self.assertEqual(u['studioAcquisition']['location'],old) # A later explicit edit.
            u['sephiraAcquisition']['location']=old
            u['studioAcquisition']={'version':1,'location':'mitra_shop','random':False,'hideSpoilers':True}
            pack.repair_default_acquisition(u)
            self.assertEqual(u['studioAcquisition']['location'],'mitra_shop')

    def test_mitra_practice_stage_is_preserved_when_christine_is_enabled(self):
        native=copy.deepcopy(self.native)
        tables={}
        def table(rel):return tables.setdefault(rel,{'asset':'FFRS/Content/Datatable/'+rel,'add':[],'set':[]})
        for rel in (testing.MAP,testing.MAP_COMPOSITE):
            table(rel)['set'].append({'row':'01Gra_20','set':{'battleStage':testing.PRACTICE_ID}})
        with tempfile.TemporaryDirectory() as root:
            challenge.prepare(tables,[u for u in self.units if u['sephiraVision']['preset']=='christine'],root,lambda rel:native[rel])
        for rel in (testing.MAP,testing.MAP_COMPOSITE):
            edits=[e for e in tables[rel]['set'] if e['row']=='01Gra_20']
            self.assertEqual(edits,[{'row':'01Gra_20','set':{'battleStage':testing.PRACTICE_ID}}])

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
                    self.assertFalse(any(e['row'] == '01Gra_20' for kind in ('set', 'add') for e in plan[kind]))

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
            for key in (name, name+'_Start'):
                branches = events[key]['ContinuousEventList']
                self.assertEqual(branches[0]['Condition'], spec['unlock'])
                self.assertIn('{item:'+str(spec['origin'])+'}>0', branches[0]['Condition'])
                self.assertTrue(branches[1]['Condition'].startswith('{item:'+str(spec['origin'])+'}==0&'))
                self.assertEqual(events[key]['OnFlagList'], [])
                self.assertEqual(events[key]['ProgressList'], [])
            if spec['origin'] == 13062:
                self.assertIn('{progress:48}>=50', spec['unlock'])
                self.assertNotIn('>=10', spec['unlock'])
            if spec['origin'] == 13024: self.assertIn('{progress:0}>=1090', spec['unlock'])
        # No shared "some legend completed" flag can unlock a different vision.
        self.assertTrue(all('{flag:1017}' not in s['unlock'] for s, _ in challenge.plans(self.units)))

    def test_guaranteed_battle_result_rewards_have_no_post_battle_event(self):
        events = self.built[challenge.COMPOSITE]
        for spec, units in challenge.plans(self.units):
            name = challenge.PREFIX+str(spec['origin'])
            group = self.built[challenge.GROUP][name]
            self.assertFalse(group['battleFinishEventId'])
            self.assertNotIn(name+'_Reward',events)
            self.assertFalse(group['battleFinishEscapeEventId'])
            self.assertFalse(group['battleFinishLoseEventId'])
            self.assertNotIn(name+'_Win',events)
            self.assertNotIn(name+'_Grant',events)
            for unit in units:
                enemy=self.built[challenge.UNIT][challenge.PREFIX+str(unit['id'])]
                self.assertEqual(enemy['DropNormalItem'],unit['id'])
                self.assertEqual(enemy['DropNormalItemRate'],self.native[challenge.UNIT]['ベルモーダー']['DropNormalItemRate'])
                self.assertEqual(enemy['DropNormalItemRate'],1)
                self.assertEqual(enemy['DropRareItem'],-1)
                self.assertEqual((enemy['StealNormalItem'],enemy['StealRareItem']),(-1,-1))
                self.assertEqual(enemy['StealItemRate'],0)
            for suffix in ('', '_Available', '_Menu', '_Start', '_Fight', '_Close', '_Locked', '_Done'):
                self.assertEqual(events[name+suffix]['ObtainItemList'], [])
            self.assertFalse(group['isResultSkipOnWin'])
            self.assertTrue(group['CanEscape'])
        # The shared cave actors must never retain their former free grants.
        cave_events = [e for k,e in events.items() if k.startswith('Studio_ResonanceCave_') and k.endswith('_Acquire')]
        self.assertEqual(len(cave_events), 2)
        self.assertTrue(all(not e['ObtainItemList'] and e['encountGroupId'] == -1 for e in cave_events))

    def test_christine_is_a_level_five_boss_with_the_native_curve_budget(self):
        spec=next(s for s in challenge.data()['encounters'] if s['origin']==13024)
        self.assertEqual(spec['level'],5)
        unit=next(u for u in self.units if u['sephiraVision']['preset']=='christine')
        enemy=next(v for v in self.built[challenge.UNIT].values() if v.get('ID')==challenge.boss_id(unit))
        self.assertEqual(enemy['Level'],5)
        expected=challenge.curve(lambda rel:self.native[rel],5)
        for field in challenge.PARAMETERS:
            factor = {'Attack':1.5, 'Intelligence':1.5, 'Agility':1.15}.get(field,1)
            self.assertEqual(enemy[field],round(expected[field]*factor))
        self.assertEqual((enemy['MaxHitPoint'],enemy['MaxBreakPoint']),(2750,162))
        self.assertEqual(enemy['ElementResistanceList']['eElement::Ice'],'eResistance::Halved')
        self.assertEqual(enemy['ElementResistanceList']['eElement::Fire'],'eResistance::Weakness')
        self.assertGreater(enemy['MaxHitPoint'],challenge.curve(lambda rel:self.native[rel],2)['MaxHitPoint'])
        kit=challenge.kit(unit,lambda rel:self.native[rel],1)
        self.assertEqual(kit[0]['source'],220050)
        self.assertEqual(kit[0]['fields']['Name'],'Blizzard')
        originals={v['ID']:v for v in self.native[challenge.SKILL].values()}
        self.assertTrue(any(testing.apply_fields(originals[r['source']],r['fields'])['element']=='Ice' for r in kit))
        slumber=next(r for r in kit if r['source']==500570)
        self.assertEqual(testing.apply_fields(originals[500570],slumber['fields'])['effectBundleList'],
                         originals[500570]['effectBundleList'])

    def test_offensive_pressure_and_role_basics_apply_to_all_28_challenge_visions(self):
        native_skills={v['ID']:v for v in self.native[challenge.SKILL].values()}
        for spec,units in challenge.plans(self.units):
            curve=challenge.curve(lambda p:self.native[p],spec['level'])
            stats=challenge.team_stats(lambda p:self.native[p],spec['level'],units)
            for unit,enemy in zip(units,stats):
                for field,factor in [('Attack',1.5),('Intelligence',1.5),('Agility',1.15)]:
                    self.assertEqual(enemy[field],round(curve[field]*factor))
                config=challenge.data()['kits'][unit['sephiraVision']['preset']]
                recipes=challenge.kit(unit,lambda p:self.native[p],len(units))
                if unit['attackType']=='Magic':
                    self.assertEqual(native_skills[recipes[0]['source']]['DamageType'],'Magic')
                    self.assertNotEqual(recipes[0]['source'],500010)
                for recipe in recipes:
                    if not recipe['damaging']:continue
                    learned=unit.get('skills',{}).get(str(recipe['learned']),{})
                    original=testing.apply_fields(native_skills[recipe['source']],learned.get('set',{}))
                    cap=40 if original['TargetType'] in ('Group','All','SingleAndGroup') else 60
                    factor=1.75 if recipe['source']==config['attacks'][-1] else 1.5
                    expected=max(1,round(min(original['magnification'],cap)*factor/len(units)))
                    expected=max(1,round(expected*config.get('potencyMultipliers',{}).get(str(recipe['source']),challenge.data().get('potencyScale',1))))
                    actual=testing.apply_fields(native_skills[recipe['source']],recipe['fields'])
                    self.assertEqual(actual['magnification'],expected)
                    self.assertEqual(actual['DamageType'],original['DamageType'])
                    self.assertEqual(actual['element'],original['element'])
        christine=next(u for u in self.units if u['sephiraVision']['preset']=='christine')
        recipes=challenge.kit(christine,lambda p:self.native[p],1)
        self.assertEqual(testing.apply_fields(native_skills[220050],recipes[0]['fields'])['magnification'],39)
        spike=next(r for r in recipes if r['source']==220080)
        self.assertEqual(testing.apply_fields(native_skills[220080],spike['fields'])['magnification'],78)
        blizzara=next(r for r in recipes if r['source']==220060)
        old_power=round(native_skills[220060]['magnification']*1.5)
        self.assertEqual(testing.apply_fields(native_skills[220060],blizzara['fields'])['magnification'],round(old_power*1.5))

    def test_casual_ai_uses_reviewed_moves_without_unguarded_heals(self):
        for spec, units in challenge.plans(self.units):
            for index, unit in enumerate(units):
                recipes=challenge.kit(unit,lambda rel:self.native[rel],len(units))
                allowed={r['id'] for r in challenge.rotation(unit,recipes,index) if not r['healing']}
                ai=self.built[challenge.AI][challenge.PREFIX+str(unit['id'])]
                for field in ('skillRandData1','skillRandData2'):
                    choices=ai[field]
                    self.assertEqual({c['SkillId'] for c in choices},allowed)
                    self.assertTrue(all(c['Probability']>0 for c in choices))
                    self.assertAlmostEqual(sum(c['Probability'] for c in choices),100)
                if unit['sephiraVision']['preset']=='christine':
                    self.assertEqual(ai['fightSkillId'],recipes[0]['id'])
                    self.assertGreater(len(allowed),1)
                    self.assertNotIn(500010,{r['source'] for r in recipes})

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

    def test_complete_existing_actor_schemas_are_loaded_for_cave_serialization(self):
        path=ROOT/'scripts/fixtures/sephira_challenges'
        native=json.loads(gzip.decompress((path/'decoded-cave-blueprints.json.gz').read_bytes()))
        trigger=json.loads(gzip.decompress((path/'crystal-interaction.json.gz').read_bytes()))
        bg=json.loads(gzip.decompress((path/'crystal-background.json.gz').read_bytes()))
        spec=challenge.data()['encounters'][0]
        spec=copy.deepcopy(spec)
        spec['crystalInteraction']['mapPackage']='Map/Dng/01Gra/01Gra_44/Dng_01Gra_44_PL'
        room=json.loads(gzip.decompress((path/'secret-cave.json.gz').read_bytes()))
        views=challenge.christine_views(room,trigger,bg,spec)
        collected=[]
        with tempfile.TemporaryDirectory() as root:
            root=Path(root);legacy=root/'legacy';work=root/'work';work.mkdir()
            mapping=root/'Mappings.usmap';mapping.write_bytes(b'original mappings')
            for view in views.values():
                for imp in view['Imports']:
                    if imp['ClassName']=='BlueprintGeneratedClass':
                        package=view['Imports'][-imp['OuterIndex']-1]['ObjectName']
                        p=legacy/('FFRS/Content/'+package.removeprefix('/Game/')+'.uasset')
                        p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b'native BP')
            def run(cmd):
                source,target=Path(cmd[2]),Path(cmd[3])
                target.write_text(json.dumps(native['blueprints'][source.stem]))
            def mapped(original,blueprints):
                self.assertEqual(original,b'original mappings');collected.extend(blueprints)
                return b'private complete mappings'
            env={'ROOT':root,'LEGACY':legacy,'USMAP':str(mapping),'FFRDT':['native'],'run':run}
            with mock.patch.object(caves,'map_mappings',side_effect=mapped):
                private=caves.blueprint_mappings(views,env,work)
            self.assertEqual(Path(private).read_bytes(),b'private complete mappings')
            self.assertEqual(mapping.read_bytes(),b'original mappings')
        self.assertEqual(set(collected),{'BP_MapGimmick_EventTrigger_C'})

    def test_preflight_write_is_reused_once_and_never_after_output_changed(self):
        spec=challenge.data()['encounters'][0]
        unit=next(u for u in self.units if u['sephiraVision']['preset']=='christine')
        with tempfile.TemporaryDirectory() as root:
            root=Path(root);out=root/'out';stages=[]
            env={'ROOT':root,'OUT':out,'BUILD':root/'build','LEGACY':root/'legacy','stage':stages.append}
            rel=spec['crystalInteraction']['mapPackage']
            asset=out/('FFRS/Content/'+rel+'.umap')
            def build(*args):
                asset.parent.mkdir(parents=True,exist_ok=True);asset.write_bytes(b'validated map')
                asset.with_suffix('.uexp').write_bytes(b'validated exports')
            with mock.patch.object(challenge,'build_christine_interaction',side_effect=build) as native_build:
                challenge.preflight([unit],env)
                self.assertTrue(challenge.checked_crystal(env,spec))
                self.assertFalse(challenge.checked_crystal(env,spec))
                challenge.preflight([unit],env);asset.write_bytes(b'changed later')
                self.assertFalse(challenge.checked_crystal(env,spec))
                self.assertEqual(native_build.call_count,2)
            self.assertEqual(stages[0],'Checking cave interactions before sprite conversion')

    def test_physical_christine_crystal_retains_all_native_cave_streams(self):
        path = ROOT/'scripts/fixtures/sephira_challenges'
        def load(name): return json.loads(gzip.decompress((path/name).read_bytes()))
        room, trigger, bg = [load(n) for n in ('mitra-cave.json.gz','crystal-interaction.json.gz','crystal-background.json.gz')]
        before = copy.deepcopy((room,trigger,bg))
        spec = challenge.data()['encounters'][0]
        views = challenge.christine_views(room,trigger,bg,spec)
        self.assertEqual((room,trigger,bg),before)
        self.assertEqual(len(views),1)
        private = next(iter(views.values()))
        owner = caves.export(private,'BP_MapGimmick_EventTrigger_C_1')[1]
        event, = caves.property_data(owner,'m_EventList')['Value']
        self.assertEqual(caves.property_data(event,'EventId')['Value'],challenge.PREFIX+'13024')
        crystal_id, crystal = caves.export(private,'Studio_ChristineCrystal')
        owner_id=caves.export(private,'BP_MapGimmick_EventTrigger_C_1')[0]
        self.assertIn(owner_id,caves.export(private,'PersistentLevel')[1]['Actors'])
        self.assertEqual(crystal['OuterIndex'],owner_id)
        self.assertEqual(caves.property_data(owner,'VisibleCondition')['Value'],'{item:13024}>0|{progress:0}>=1090')
        self.assertEqual(caves.property_data(owner,'m_FlagCondition')['Value'],spec['unlock'])
        self.assertEqual(caves.property_data(owner,'m_MapInteractType')['Value'],'Check_Gimmick')
        self.assertEqual(caves.property_data(owner,'m_UniqueId')['Value'],27500)
        component = crystal
        self.assertEqual(caves.property_data(component,'VisibilityId')['Value'],-1)
        self.assertEqual(caves.property_data(component,'Mobility')['Value'],'Movable')
        mesh = private['Imports'][-caves.property_data(component,'StaticMesh')['Value']-1]
        self.assertEqual(mesh['ObjectName'],'SM_Env_Com_magicstone001')
        position=caves.property_data(component,'RelativeLocation')['Value'][0]['Value']
        self.assertEqual([position[k] for k in ('X','Y','Z')],[0.0,0.0,0.0])
        root_box=private['Exports'][caves.property_data(owner,'m_pRootBoxComponent')['Value']-1]
        position=caves.property_data(root_box,'RelativeLocation')['Value'][0]['Value']
        self.assertEqual([position[k] for k in ('X','Y','Z')],[6610.0,52639.0,-705.02])
        built=private
        self.assertTrue(next(iter(views)) == spec['crystalInteraction']['mapPackage'])
        self.assertEqual(built['Imports'][:len(room['Imports'])],room['Imports'])
        self.assertEqual(built['NameMap'][:len(room['NameMap'])],room['NameMap'])
        for index,original in enumerate(room['Exports']):
            if original['ObjectName'] == 'PersistentLevel':
                self.assertEqual(built['Exports'][index]['Actors'][:len(original['Actors'])],original['Actors'])
            else: self.assertEqual(built['Exports'][index],original)
        for view in views.values(): caves.check_object_names(view)


if __name__ == '__main__': unittest.main()
