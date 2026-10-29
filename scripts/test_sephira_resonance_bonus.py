"""The native skill-specific resonance bonus must target a learned signature."""
import copy
import unittest

from test_sephira_runtime_rewards import inputs
import _ffr_sephira as pack
from _ffr_testing import apply_fields


class ResonanceBonusTests(unittest.TestCase):
    def setUp(self):
        self.catalog,self.rows,self.units=inputs()
        self.unit=next(u for u in self.units if pack.membership(u)['preset']=='primm')

    def test_descriptions_reference_signatures_actually_learned(self):
        for key,signature,sid in [('minfilia','Blade Torrent',445200),('primm','Moonlightbringer',445300)]:
            unit=next(u for u in self.units if pack.membership(u)['preset']==key)
            self.assertIn(['ActiveSkill',sid,-1],unit['awakening'][2])
            self.assertEqual(unit['lb_custom']['desc'],
                f'Deal non-elemental magic damage to all enemies. Increase power of {signature} by 20% until battle ends.')
        self.assertNotIn(445200,{g[1] for t in self.unit['awakening'] for g in t if g[0]=='ActiveSkill'})

    def test_built_effect_changes_only_primm_bonus_target_preserving_budget_and_native_originals(self):
        original=copy.deepcopy((self.units,self.rows))
        bound=pack.bind_units(self.units,self.rows.__getitem__)
        tables={};pack.prepare(tables,bound)
        primm=next(u for u in bound if pack.membership(u)['preset']=='primm')
        plan,=primm['_sephiraResonanceEffects']
        source=self.rows[pack.EFFECT][plan['cloneFrom']]
        actual=apply_fields(source,plan['set'])
        expected=copy.deepcopy(source);expected['ID']=135262946;expected['ParamList'][1]=445300
        self.assertEqual(actual,expected)
        self.assertIn(plan,tables[pack.EFFECT]['add'])
        native=next(r for r in self.rows['Skill/DT_SkillData'].values() if r['ID']==440030)
        bundles=copy.deepcopy(native['effectBundleList']);bundles[0]['effectId']=135262946
        self.assertEqual(primm['lb_custom']['set'],{'effectBundleList':bundles})
        self.assertEqual(bundles[1]['effectId'],12966,'Native LB level scaling must remain intact')
        self.assertEqual(actual['effectEndActionNum'],-1)
        for unit,old in zip(bound,self.units):
            if pack.membership(unit)['preset']!='primm':
                self.assertEqual(unit['lb_custom'],old['lb_custom'])
                self.assertNotIn('_sephiraResonanceEffects',unit)
        self.assertEqual((self.units,self.rows),original)

    def test_allocated_private_copy_follows_its_learned_identity(self):
        self.unit['id']=13782
        for tier in self.unit['awakening']:
            for grant in tier:
                if grant[:2]==['ActiveSkill',445300]:grant[1]=513299
        self.unit['skills']['513299']={'from':445300,'en':'My signature','desc':'Edited', 'set':{'Cost':17}}
        old=copy.deepcopy(self.unit)
        unit,=pack.bind_units([self.unit],self.rows.__getitem__)
        effect,=unit['_sephiraResonanceEffects']
        self.assertEqual(effect['set']['ID'],137832946)
        self.assertEqual(effect['set']['ParamList'][1],513299)
        self.assertEqual(unit['skills'],old['skills'])
        self.assertEqual(self.unit,old)

    def test_custom_effects_donor_and_removed_or_ambiguous_signature_are_preserved(self):
        for change in ('effects','donor','removed','ambiguous','untagged','native','party'):
            unit=copy.deepcopy(self.unit)
            if change=='effects':unit['lb_custom']['set']['effectBundleList']=[]
            elif change=='donor':unit['lb_custom']['from']=440110
            elif change=='removed':
                for tier in unit['awakening']:tier[:]=[g for g in tier if g[:2]!=['ActiveSkill',445300]]
            elif change=='ambiguous':
                unit['skills']['487599']={'from':445300}
                unit['awakening'][3].append(['ActiveSkill',487599,-1])
            elif change=='untagged':unit.pop(pack.FIELD)
            else:unit[change]={'id':13102}
            before=copy.deepcopy(unit)
            skills={r['ID']:r for r in self.rows['Skill/DT_SkillData'].values()}
            effects={r['ID']:(k,r) for k,r in self.rows[pack.EFFECT].items()}
            pack.bind_resonance(unit,skills,effects)
            self.assertEqual(unit,before,change)

    def test_changed_native_effect_or_identity_collision_is_rejected(self):
        for change in ('type','amount','signature','bundle','collision'):
            skills={r['ID']:copy.deepcopy(r) for r in self.rows['Skill/DT_SkillData'].values()}
            effects={r['ID']:(k,copy.deepcopy(r)) for k,r in self.rows[pack.EFFECT].items()}
            if change=='type':effects[12946][1]['EffectType']='DamageMultiplier'
            elif change=='amount':effects[12946][1]['ParamList'][0]=50
            elif change=='signature':effects[12946][1]['ParamList'][1]=445300
            elif change=='bundle':skills[440030]['effectBundleList'][0]['effectId']=-1
            else:effects[135262946]=('occupied',{})
            unit=copy.deepcopy(self.unit)
            with self.assertRaisesRegex(ValueError,'re-audit|overlaps'):pack.bind_resonance(unit,skills,effects)
            self.assertEqual(unit,self.unit)


if __name__=='__main__':unittest.main()
