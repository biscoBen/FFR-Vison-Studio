"""Real native definitions and executable UE4SS ownership/lifecycle contracts."""
import copy
import json
from pathlib import Path
import unittest

from test_sephira_runtime_rewards import inputs
import _ffr_esper_mastery as esper
import _ffr_sephira as pack
from sephira_esper_kits import revise,REWARDS

ROOT=Path(__file__).resolve().parents[1]


class EsperMasteryTests(unittest.TestCase):
    def test_revelry_proc_is_thirty_of_a_hundred_rolls_with_one_roll_per_action_and_native_finale(self):
        from lupa.lua54 import LuaRuntime
        lua=LuaRuntime()
        lua.execute((ROOT/'scripts/fixtures/esper_mastery_runtime.lua').read_text())
        lua.execute((ROOT/'assets/existing_visions/payload/esper_mastery.lua').read_text())
        lua.execute('''
            fina.parameter.passives={1963}
            local summon=actor(10452,'Ifrit');actors={fina,summon};tick()
            summon.ai.remaining=2;summon.ai:GetRemainingActionNumSummonedUnit()
            local random=math.random;local calls,specials=0,0
            for roll=1,100 do
                summon.parameter.count=roll
                math.random=function(low,high) assert(low==1 and high==100);calls=calls+1;return roll end
                summon.ai:SetSkill(414010)
                assert((summon.ai.skill==300020)==(roll<=30),'Only rolls 1 through 30 proc')
                if summon.ai.skill==300020 then specials=specials+1 end
                summon.ai:SetSkill(500020);summon.ai:SetSkillRandom(0)
                assert(calls==roll,'Repeated native selection callbacks must not reroll this action')
            end
            assert(specials==30 and calls==100)
            summon.ai.remaining=0;summon.ai:GetRemainingActionNumSummonedUnit()
            summon.parameter.count=101;math.random=function() error('Never roll the native final special') end
            summon.ai:SetSkill(300020);assert(summon.ai.skill==300020)
            assert(calls==100);math.random=random
        ''')

    def test_rikku_pharmacology_updates_only_mr7_and_preserves_later_edits(self):
        from sephira_rikku_pharmacology import revise as revise_rikku
        catalog,_,_=inputs()
        p=next(p for p in catalog['presets'] if p['id']=='rikku')
        unit=copy.deepcopy(p['pharmacologyKitBefore'])
        unit['sephiraVision']={'version':1,'preset':'rikku','enabled':False}
        unit['awakening'][0].reverse()
        unit['sephiraPassiveText']={'1387':{'name':'My label','desc':'My text'}}
        unit['en']='My Rikku';unit['stats']['Attack']=999
        before=copy.deepcopy(unit)
        esper.repair(unit)
        self.assertEqual(unit['synchro'][7],[['PassiveSkill',1044,-1]])
        for key in before.keys()-{'synchro','sephiraKitRevision'}:
            self.assertEqual(unit[key],before[key],key)
        for rank in set(range(10))-{7}:self.assertEqual(unit['synchro'][rank],before['synchro'][rank])
        self.assertEqual(unit['master']['id'],1352700)
        unit['synchro'][7]=[['PassiveSkill',1280,-1]]
        later=copy.deepcopy(unit);esper.repair(unit);self.assertEqual(unit,later)
        conflict=copy.deepcopy(before);conflict['synchro'][7]=[['PassiveSkill',1280,-1]]
        original=copy.deepcopy(conflict)
        with self.assertRaisesRegex(ValueError,'MR7 was edited'):esper.repair(conflict)
        self.assertEqual(conflict,original)
        self.assertEqual(revise_rikku(copy.deepcopy(catalog)),catalog)

    def test_eiko_support_update_migrates_current_kit_without_touching_mastery(self):
        catalog,_,_=inputs()
        p=next(p for p in catalog['presets'] if p['id']=='eiko')
        unit=copy.deepcopy(p['profile'])
        unit['sephiraVision']={'version':1,'preset':'eiko','enabled':True}
        raise_grant=['ActiveSkill',210140,-1]
        shellga=['ActiveSkill',230070,-1]
        unit['awakening'][0].remove(raise_grant)
        unit['awakening'][1].remove(shellga)
        unit['awakening'][1].insert(1,raise_grant)
        unit['sephiraKitRevision']=1
        unit['awakening'][0].append(['ActiveSkill',210120,-1])
        before=copy.deepcopy(unit)
        esper.repair(unit)
        self.assertIn(raise_grant,unit['awakening'][0])
        self.assertNotIn(raise_grant,unit['awakening'][1])
        self.assertIn(shellga,unit['awakening'][1])
        self.assertIn(['ActiveSkill',210120,-1],unit['awakening'][0])
        for field in before.keys()-{'awakening','sephiraKitRevision'}:
            self.assertEqual(unit[field],before[field],field)
        self.assertTrue(all(len(t)<=8 for t in unit['awakening']))
        fixed=copy.deepcopy(unit);esper.repair(unit);self.assertEqual(unit,fixed)

    def test_mystea_swaps_keep_master_and_ap_at_rank_nine(self):
        catalog,_,_=inputs();p=next(p for p in catalog['presets'] if p['id']=='mystea')
        unit=copy.deepcopy(p['esperKitBefore']);before=copy.deepcopy(unit)
        unit['sephiraVision']={'version':1,'preset':'mystea','enabled':True}
        esper.repair(unit)
        self.assertEqual(unit['synchro'],p['profile']['synchro'])
        for a,b in ((1,2),(2,1),(5,9),(9,5)):self.assertEqual(unit['synchro'][a][0],before['synchro'][b][0])
        self.assertEqual(unit['synchro'][9][1:],before['synchro'][9][1:])
        self.assertEqual(unit['awakening'],before['awakening'])
    def test_reviewed_rewards_no_summons_and_native_healing_operations(self):
        catalog,rows,units=inputs()
        by={p['id']:p for p in catalog['presets']}
        for name,rewards in REWARDS.items():
            u=by[name]['profile']
            self.assertEqual([u['synchro'][r][0][:2] for r in (1,3,5,7,9)],[list(g) for g in rewards])
            self.assertEqual([len(t) for t in u['synchro']],[0,1,1,1,1,1,1,1,1,3])
            self.assertEqual(u['id'],by[name]['esperKitBefore']['id'])
        eiko=by['eiko']['profile']
        learned={g[1] for tier in eiko['awakening'] for g in tier if g[0]=='ActiveSkill'}
        self.assertTrue({430990,431000}.isdisjoint(learned))
        self.assertIn(['PassiveSkill',1045,-1],eiko['awakening'][2])
        self.assertIn(['PassiveSkill',1256,-1],eiko['awakening'][3])
        result=pack.player_units([dict(eiko,sephiraVision={'version':1,'preset':'eiko','enabled':True})],rows.__getitem__)[0]
        heal=result['skills']['486545'];regen=result['skills']['486548']
        self.assertEqual(heal['from'],215000)
        self.assertEqual(heal['set']['availableLocation'],'Anywhere')
        self.assertEqual(regen['from'],210050)
        self.assertEqual(regen['set']['TargetType'],'Group')
        self.assertEqual(regen['visuals'],210050)

    def test_backend_kit_migration_is_atomic_idempotent_and_keeps_private_edits(self):
        catalog,rows,_=inputs()
        for p in catalog['presets']:
            if p['id'] not in REWARDS:continue
            unit=copy.deepcopy(p['esperKitBefore']);unit['sephiraVision']={'version':1,'preset':p['id'],'enabled':False}
            unit['en']='My name';unit['stats']['Mind']=999
            unit['studioAcquisition']={'version':1,'location':'mitra_shop','random':False,'hideSpoilers':False}
            original=copy.deepcopy(unit)
            esper.repair(unit)
            for key in ('id','key','en','stats','ffbe','lb_custom','studioAcquisition','sephiraVision'):
                self.assertEqual(unit[key],original[key])
            self.assertEqual(unit['awakening'],p['profile']['awakening'])
            self.assertEqual(unit['synchro'],p['profile']['synchro'])
            before=copy.deepcopy(unit);esper.repair(unit);self.assertEqual(unit,before)
            edited=copy.deepcopy(original);edited['synchro'][7][0][1]=9999
            before=copy.deepcopy(edited)
            with self.assertRaisesRegex(ValueError,'MR7 was edited'):esper.repair(edited)
            self.assertEqual(edited,before)
        self.assertEqual(revise(copy.deepcopy(catalog)),catalog)

    def test_native_effect_definitions_are_private_non_recurring_and_equippable(self):
        _,rows,units=inputs();before=copy.deepcopy(rows);tables={}
        esper.prepare(tables,rows.__getitem__,units)
        self.assertEqual(rows,before)
        from _ffr_testing import apply_fields
        passives=tables[esper.PASSIVE]['add']
        fx={op['set']['ID']:apply_fields(rows[esper.EFFECT][op['cloneFrom']],op['set']) for op in tables[esper.EFFECT]['add']}
        self.assertLessEqual(set(esper.IDS),{p['set']['ID'] for p in passives})
        retired={pack.private_passive_id(p['preset'],p['source']) for p in esper.data()['retiredPassives']}
        self.assertEqual({p['set']['ID'] for p in passives},set(esper.IDS)|retired)
        self.assertEqual(len(fx),8)
        for p in passives:
            self.assertTrue(1000<=p['set']['ID']<2000)
            self.assertGreater(p['set']['equipCost'],0)
            if p['set']['ID'] in esper.IDS:
                self.assertEqual(p['set']['effectBundleList'][0]['passiveSkillAddTiming'],'SpawnUnit')
        self.assertEqual(fx[196001]['ParamList'][0],20)
        self.assertEqual(fx[196201]['ParamList'][0],20)
        self.assertEqual(fx[196101]['ParamList'][:3],[5,2,2])
        self.assertEqual(fx[196101]['applyTiming'],'AddEffect')
        self.assertEqual(fx[196101]['proceedTiming'],'AddEffect')
        self.assertEqual(fx[196101]['effectEndActionNum'],1)
        self.assertEqual(fx[196202]['ParamList'][:3],[20,1,2])
        cat=esper.catalog({'passives':[]})
        self.assertEqual(len(cat['passives']),4)
        with self.assertRaisesRegex(ValueError,'overlaps'):esper.catalog(cat)

    def test_native_game_thread_loop_preserves_all_mastery_contracts_without_async_entry(self):
        from lupa.lua54 import LuaRuntime
        lua=LuaRuntime()
        lua.execute((ROOT/'scripts/fixtures/esper_mastery_runtime.lua').read_text())
        lua.execute('''
            nativeCallback=setmetatable({}, {__mode='v'})
            function LoopInGameThreadWithDelay(ms,fn)
                assert(ms==200);nativeCallback[1]=fn;tick=fn;return 71
            end
            function LoopAsync() error('No background Lua entry with the native scheduler') end
            function ExecuteInGameThread() error('No per-tick queue with the native scheduler') end
        ''')
        lua.execute((ROOT/'assets/existing_visions/payload/esper_mastery.lua').read_text())
        lua.execute('''
            collectgarbage('collect')
            assert(type(nativeCallback[1])=='function' and nativeCallback[1]()==false)
            assert(FFRStudioEsperMastery.loopHandle==71)
        ''')
        lua.globals().run_tests()
        lua.globals().run_reader_failure_tests()

    def test_failed_native_registration_uses_a_rooted_bounded_retry_bridge(self):
        from lupa.lua54 import LuaRuntime
        lua=LuaRuntime()
        lua.execute((ROOT/'scripts/fixtures/esper_mastery_runtime.lua').read_text())
        lua.execute('''
            function LoopInGameThreadWithDelay() error('unavailable native loop') end
            waiting=setmetatable({}, {__mode='v'});queued=0
            function ExecuteInGameThread(fn) queued=queued+1;waiting[1]=fn end
        ''')
        lua.execute((ROOT/'assets/existing_visions/payload/esper_mastery.lua').read_text())
        lua.execute('''
            tick();local first=waiting[1]
            for _=1,19 do tick() end
            assert(queued==1)
            tick();assert(queued==2 and waiting[1]==first)
            first=nil;collectgarbage('collect')
            assert(type(waiting[1])=='function')
            waiting[1]();assert(FFRStudioEsperMastery.pending==nil)
            tick();assert(queued==3)
        ''')

    def test_runtime_lifecycle_ownership_and_finale_contracts(self):
        try:from lupa import LuaRuntime
        except ImportError:self.skipTest('lupa is needed for executable Lua checks')
        lua=LuaRuntime(unpack_returned_tuples=True)
        lua.execute((ROOT/'scripts/fixtures/esper_mastery_runtime.lua').read_text())
        lua.execute((ROOT/'assets/existing_visions/payload/esper_mastery.lua').read_text())
        lua.globals().run_tests()
        lua.globals().run_reader_failure_tests()

    def test_spawn_scan_skips_worlds_and_destroying_actors_without_dereferencing_them(self):
        from lupa.lua54 import LuaRuntime
        lua=LuaRuntime()
        lua.execute((ROOT/'scripts/fixtures/esper_mastery_runtime.lua').read_text())
        lua.execute((ROOT/'assets/existing_visions/payload/esper_mastery.lua').read_text())
        lua.execute('''
            local original=FindAllOf;local reads=0
            local old=actor(10451)
            old.flags=0x8000
            old.GetFullName=function() reads=reads+1;error('destroying actor name') end
            old.GetUnitAI=function() reads=reads+1;error('destroying actor AI') end
            actors={old}
            tick();assert(reads==0)
            battleUI.bDuringBattle=false
            FindAllOf=function(class)
                assert(class=='CPP_UI_BattleSubsystem','No spawn scan outside battle')
                return original(class)
            end
            for _=1,120 do tick();collectgarbage('collect') end
            assert(next(FFRStudioEsperMastery.states)==nil)
            FindAllOf=original;battleUI.bDuringBattle=true
            actors={actor(10451)};tick()
            assert(FFRStudioEsperMastery.states.Actor10451~=nil)
        ''')

    def test_returned_capture_contract_rejects_old_unwrapped_and_no_argument_reads(self):
        try:from lupa.lua54 import LuaRuntime
        except ImportError:self.skipTest('lupa is needed for executable Lua checks')
        lua=LuaRuntime()
        lua.execute((ROOT/'scripts/fixtures/esper_mastery_runtime.lua').read_text())
        lua.execute('''
            fina.parameter.effects[196000]=true
            local list=fina.parameter:GetContEffectList()
            assert(type(list)=='table' and type(list[1].get)=='function')
            local ok,error=pcall(function() return list[1]:IsValid() end)
            assert(not ok and error:find('IsValid',1,true))
            ok,error=pcall(function() return fina.parameter:GetPassiveSkillList() end)
            assert(not ok and error:find('expected 1 parameters',1,true))
            fina.parameter.passives={1960,1961,1962,1963}
            local out={};fina.parameter:GetPassiveSkillList(out)
            assert(#out==4 and out[1]:get()==1960)
        ''')


if __name__=='__main__':unittest.main()
