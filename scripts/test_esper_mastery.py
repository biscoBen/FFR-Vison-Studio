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
        passives=tables[esper.PASSIVE]['add'];fx={op['set']['ID']:op['set'] for op in tables[esper.EFFECT]['add']}
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
        self.assertEqual(fx[196101]['applyTiming'],'None')
        self.assertEqual(fx[196101]['proceedTiming'],'None')
        self.assertEqual(fx[196101]['effectEndActionNum'],1)
        cat=esper.catalog({'passives':[]})
        self.assertEqual(len(cat['passives']),4)
        with self.assertRaisesRegex(ValueError,'overlaps'):esper.catalog(cat)

    def test_runtime_lifecycle_ownership_and_finale_contracts(self):
        try:from lupa import LuaRuntime
        except ImportError:self.skipTest('lupa is needed for executable Lua checks')
        lua=LuaRuntime(unpack_returned_tuples=True)
        lua.execute((ROOT/'scripts/fixtures/esper_mastery_runtime.lua').read_text())
        lua.execute((ROOT/'assets/existing_visions/payload/esper_mastery.lua').read_text())
        lua.globals().run_tests()


if __name__=='__main__':unittest.main()
