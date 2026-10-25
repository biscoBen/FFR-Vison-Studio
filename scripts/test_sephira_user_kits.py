"""Requested healer layouts and stable MR/Spirit ownership, using native rows."""
import copy
import json
from pathlib import Path
import unittest

from test_sephira_runtime_rewards import inputs
import _ffr_sephira as pack
from sephira_user_kits import revise,standalone

ROOT=Path(__file__).resolve().parents[1]


class UserKitTests(unittest.TestCase):
    def test_reviewed_tiers_and_castable_reraise_preserve_stats_and_mr(self):
        catalog,rows,units=inputs()
        baseline=json.loads((ROOT/'scripts/fixtures/sephira_user_kits_before.json').read_bytes())
        by={p['id']:p['profile'] for p in catalog['presets']}
        for name,counts in [('crystal_fina',[7,8,7,3]),('aria',[8,8,7,2])]:
            u=by[name];old=baseline[name]
            self.assertEqual(list(map(len,u['awakening'])),counts)
            for field in ('id','key','stats','ffbe','lb_custom','studioAcquisition'):
                self.assertEqual(u.get(field),old.get(field))
            self.assertEqual(u['master']['id'],old['master']['id'])
            self.assertIn(['ActiveSkill',210160,-1],u['awakening'][3])
            self.assertFalse(any(g[:2]==['ActiveSkill',210240] for tier in u['awakening'] for g in tier))
            expected=copy.deepcopy(old['synchro'])
            if name=='aria':expected[9][0][1]=1524
            self.assertEqual(u['synchro'],expected)
        skills={r['ID']:r for r in rows['Skill/DT_SkillData'].values()}
        self.assertEqual(skills[210160]['Cost'],40)
        self.assertTrue(any(b['effectId']==1077 for b in skills[210160]['effectBundleList']))
        for identity in (420100,420110,420120):
            self.assertEqual(skills[identity]['element'],'Water')
            self.assertEqual(skills[identity]['DamageType'],'Physic')

    def test_aria_water_imbue_uses_the_old_private_reward_id_and_correct_effect(self):
        catalog,rows,units=inputs()
        aria=next(u for u in units if u[pack.FIELD]['preset']=='aria')
        before=copy.deepcopy(aria)
        fixed=pack.bind_units([aria],rows.__getitem__)[0]
        identity=fixed['synchro'][9][0][1]
        self.assertEqual(identity,pack.private_passive_id('aria',1527))
        self.assertEqual(identity,pack.private_passive_id('aria',1524))
        private=next(b['passive'] for b in fixed['_sephiraBindings'] if b['passive']['set']['ID']==identity)
        source=rows[pack.PASSIVE][private['cloneFrom']]
        self.assertEqual(source['ID'],1524)
        self.assertEqual([b['effectId'] for b in source['effectBundleList'] if b['effectId']>=0],[40207])
        self.assertEqual(private['set']['Name'],'Imbue Water')
        self.assertEqual(private['set']['equipCost'],20)
        self.assertEqual(aria,before)
        # The backend also repairs an old roster used without opening Studio.
        old=json.loads((ROOT/'scripts/fixtures/sephira_user_kits_before.json').read_bytes())['aria']
        old[pack.FIELD]={'version':1,'preset':'aria','enabled':True}
        legacy=pack.bind_units([old],rows.__getitem__)[0]
        self.assertEqual(legacy['synchro'][9][0][1],identity)
        private=next(b['passive'] for b in legacy['_sephiraBindings'] if b['passive']['set']['ID']==identity)
        self.assertEqual(rows[pack.PASSIVE][private['cloneFrom']]['ID'],1524)

    def test_spirits_keep_their_owner_and_only_the_five_mastery_passives(self):
        _,rows,units=inputs()
        for name,expected in [('crystal_fina',{1283,1551,1077,1552,1042}),('aria',{1104,1251,1381,1311,1524})]:
            u=next(u for u in units if u[pack.FIELD]['preset']==name)
            self.assertEqual(u['master']['id'],u['id']*100)
            mr={g[1] for tier in u['synchro'] for g in tier if g[0]=='PassiveSkill'}
            self.assertEqual(mr,expected)
            aw={g[1] for tier in u['awakening'] for g in tier if g[0]=='PassiveSkill'}
            self.assertFalse(mr&aw)
            bound=pack.bind_units([u],rows.__getitem__)[0]
            self.assertEqual(bound['master']['id'],u['master']['id'])
            self.assertEqual(bound['synchro'][9][-1],['MasterSkill',u['master']['id'],-1])

    def test_catalog_and_independent_generation_are_repeatable(self):
        catalog,_,_=inputs();expected=copy.deepcopy(catalog)
        self.assertEqual(revise(catalog),expected)
        baseline=json.loads((ROOT/'scripts/fixtures/sephira_user_kits_before.json').read_bytes())
        for p in catalog['presets']:
            if p['id'] not in ('aria','crystal_fina'):continue
            p['profile']=copy.deepcopy(baseline[p['id']]);p.pop('kitUpdate')
        self.assertEqual(revise(catalog),expected)
        supplied=json.loads((ROOT/'assets/crystal_fina/profile.json').read_bytes())
        self.assertEqual(standalone(baseline['independent_fina'],catalog),supplied)
        shared=next(p['profile'] for p in catalog['presets'] if p['id']=='crystal_fina')
        names=[r['jp'] for u in (shared,supplied) for r in u['skills'].values()]
        self.assertEqual(len(names),len(set(names)), 'Independent and collection skills must not overwrite table rows')


if __name__=='__main__':unittest.main()
