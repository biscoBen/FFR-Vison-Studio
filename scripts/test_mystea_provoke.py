"""Mystea's transferable, caster-relative Provoke and saved MR migration."""
import copy
import unittest
from test_sephira_runtime_rewards import inputs
import _ffr_esper_mastery as kits
import _ffr_sephira as pack
from sephira_esper_kits import revise


class MysteaProvokeTests(unittest.TestCase):
    def setUp(self):
        self.catalog,self.rows,_=inputs()
        self.preset=next(p for p in self.catalog['presets'] if p['id']=='mystea')

    def old(self):
        unit=copy.deepcopy(self.preset['provokeKitBefore'])
        unit[pack.FIELD]={'version':1,'preset':'mystea','enabled':True}
        return unit

    def test_private_provoke_removes_rain_restrictions_and_uses_general_command(self):
        unit=copy.deepcopy(self.preset['profile']);unit[pack.FIELD]={'version':1,'preset':'mystea','enabled':True}
        self.assertEqual(unit['synchro'][1],[['ActiveSkill',486142,-1]])
        self.assertEqual(unit['synchro'][2],[['BaseParameter',1,30]])
        recipe=unit['skills']['486142'];source=self.rows['Skill/DT_SkillData']['401090']
        self.assertEqual(recipe['from'],401090)
        self.assertEqual(source['hasUnit'],'Rain');self.assertEqual(source['mimicableUnitId'],1001)
        self.assertEqual(recipe['set'],{'hasUnit':'All','mimicableUnitId':-1,
                                      'belongCommandList':[1],'commandIdBelongDebuggingAllSkills':[900,-1]})
        self.assertNotIn('effectBundleList',recipe['set'],'Retain native caster-relative HateTarget effect')
        fixed,=pack.player_units([unit],self.rows.__getitem__)
        self.assertEqual(fixed['skills']['486142'],recipe)
        self.assertEqual(fixed['master']['id'],1351100)
        self.assertEqual(kits.data()['kits']['mystea']['profile'],self.preset['profile'])
        self.assertEqual(revise(copy.deepcopy(self.catalog)),self.catalog)

    def test_saved_version_one_changes_only_two_mr_rows_and_installs_private_skill_once(self):
        unit=self.old();unit['en']='My Mystea';unit['stats']['Mind']=777
        unit['synchro'][3]=[['PassiveSkill',1280,-1]]
        unit['studioAcquisition']={'version':1,'location':'mitra_shop','random':False,'hideSpoilers':False}
        before=copy.deepcopy(unit);kits.repair(unit)
        for field in before.keys()-{'synchro','skills','sephiraKitRevision'}:self.assertEqual(unit[field],before[field],field)
        for rank in range(10):
            if rank not in (1,2):self.assertEqual(unit['synchro'][rank],before['synchro'][rank])
        for sid,recipe in before['skills'].items():self.assertEqual(unit['skills'][sid],recipe)
        self.assertEqual(unit['synchro'][1],[['ActiveSkill',486142,-1]])
        self.assertEqual(unit['synchro'][2],[['BaseParameter',1,30]])
        self.assertEqual(unit['sephiraKitRevision'],2)
        after=copy.deepcopy(unit);kits.repair(unit);self.assertEqual(unit,after)

    def test_existing_private_copy_keeps_combat_edits_and_occupied_ids_are_not_overwritten(self):
        for existing in (False,True):
            unit=self.old();recipe=copy.deepcopy(self.preset['profile']['skills']['486142'])
            if existing:
                recipe['set'].update(Cost=13,hasUnit='Rain',mimicableUnitId=1001)
                recipe['desc']='My description';unit['skills']['486106']=recipe
            else:
                unit['skills']['486142']=copy.deepcopy(unit['skills']['486136'])
            before=copy.deepcopy(unit);kits.repair(unit);sid=unit['synchro'][1][0][1]
            self.assertEqual(sid,486106)
            self.assertEqual(unit['skills'][str(sid)]['set']['hasUnit'],'All')
            self.assertEqual(unit['skills'][str(sid)]['set']['mimicableUnitId'],-1)
            if existing:
                self.assertEqual(unit['skills'][str(sid)]['set']['Cost'],13)
                self.assertEqual(unit['skills'][str(sid)]['desc'],'My description')
            else:self.assertEqual(unit['skills']['486142'],before['skills']['486142'])

    def test_conflicting_rewards_and_ambiguous_provoke_copies_leave_saved_unit_untouched(self):
        for conflict in ('edited_stat','edited_skill','duplicate_recipe'):
            unit=self.old()
            if conflict=='edited_stat':unit['synchro'][1][0][2]=99
            elif conflict=='edited_skill':unit['synchro'][2]=[['PassiveSkill',1280,-1]]
            else:
                for sid in ('486106','486142'):unit['skills'][sid]=copy.deepcopy(self.preset['profile']['skills']['486142'])
            before=copy.deepcopy(unit)
            with self.assertRaises(ValueError):kits.repair(unit)
            self.assertEqual(unit,before)

if __name__=='__main__':unittest.main()
