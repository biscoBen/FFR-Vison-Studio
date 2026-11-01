"""All shipped resonances use their damage element, without changing mechanics."""
import copy
import unittest
from test_existing_visions import ROOT
from test_sephira_runtime_rewards import inputs
import _ffr_sephira as pack
import _ffr_esper_mastery as kits


def donor_fixtures():
    # Synthetic rows containing only the fields needed for icon selection.
    # Full native rows are neither needed nor bundled with this test.
    icons={440170:'Fire',414090:'Ice',412510:'Heal',412620:'Support',440020:'Light',
           440190:'Wind',440030:'Attack',440060:'Attack',440010:'Attack',440310:'Fire',
           440040:'Light',414100:'Heal',440090:'Attack',440210:'Water',440290:'Attack',
           440240:'Dark',440110:'Thunder',440250:'Fire'}
    return {str(sid):{'ID':sid,'SkillIcon':{'TagName':'UI.Skill.Action.Icon.'+icon},
                     'skillEffectType':'DamageAndRecovery' if icon!='Support' else 'None',
                     'parameterVariationType':'Increase' if icon=='Heal' else 'Decrease',
                     'parameterType':'HitPoint','element':{'440010':'None','440020':'Light','440030':'None','440040':'Light','440060':'None','440090':'None','440110':'Thunder','440170':'Fire','440190':'Wind','440210':'Water','440240':'Dark','440250':'Fire','440290':'None','440310':'Fire','414090':'Ice'}.get(str(sid),'None')} for sid,icon in icons.items()}


class ResonanceIconTests(unittest.TestCase):
    def test_all_thirty_resonances_keep_mechanics_and_healing_support_icons(self):
        catalog, rows, units = inputs()
        fixture=donor_fixtures()
        rows['Skill/DT_SkillData'].update(fixture)
        donors={r['ID']:r for r in fixture.values()}
        before=copy.deepcopy(units)
        expected={'a2':'Attack','fran':'Wind','lunafreya':'Water','folka':'Water','fryevia':'Ice',
                  'snow_white':'Dark','eiko':'Light','alice':'Ice','mog':'Wind','freya':'Water',
                  'relm':'Thunder','elza':'Dark'}
        mismatches={}
        for preset,old,new in zip(catalog['presets'],units,pack.player_units(units,rows.__getitem__)):
            lb=new['lb_custom'];source=donors[lb['from']]
            actual=lb.get('set',{}).get('SkillIcon.TagName',source['SkillIcon']['TagName'])
            if actual!=source['SkillIcon']['TagName']:mismatches[preset['id']]=actual.rsplit('.',1)[-1]
            effective=dict(source,**lb['set'])
            if effective['skillEffectType']=='DamageAndRecovery' and effective['parameterVariationType']=='Decrease' and effective['parameterType']=='HitPoint':
                self.assertEqual(actual,'UI.Skill.Action.Icon.'+('Attack' if effective['element']=='None' else effective['element']))
            else:self.assertEqual(actual,source['SkillIcon']['TagName'])
            restored=copy.deepcopy(lb);restored['set'].pop('SkillIcon.TagName',None)
            self.assertEqual(restored,old['lb_custom'],preset['id'])
        self.assertEqual(mismatches,expected)
        self.assertEqual(units,before)

    def test_explicit_icons_other_rosters_and_saved_element_edits_keep_precedence(self):
        source=donor_fixtures()
        row=next(r for r in source.values() if r['ID']==440210)
        def unit(fields):return {'sephiraVision':{'version':1,'preset':'mog','enabled':True},
                                'lb_custom':{'from':440210,'set':fields}}
        for fields in ({'element':'Dark'},{'element':'Earth'},
                       {'element':'Wind','SkillIcon.TagName':'UI.Skill.Action.Icon.Support'},
                       {'element':'Wind','SkillIcon':{'TagName':'UI.Skill.Action.Icon.Heal'}}):
            old=unit(fields);before=copy.deepcopy(old)
            new,=pack.player_units([old],lambda _: {'donor':row})
            expected=fields.get('SkillIcon.TagName') or fields.get('SkillIcon',{}).get('TagName') or 'UI.Skill.Action.Icon.'+fields['element']
            self.assertEqual(new['lb_custom']['set'].get('SkillIcon.TagName') or new['lb_custom']['set']['SkillIcon']['TagName'],expected)
            self.assertEqual(old,before)
        for field in ('native','party',None):
            other=unit({'element':'Wind'});other.pop('sephiraVision')
            if field:other[field]={'id':13120}
            self.assertEqual(pack.player_units([other],lambda _:self.fail('Do not read other rosters')), [other])

    def test_mog_saved_kit_changes_only_water_resistance_and_preserves_custom_mrs(self):
        catalog,_,units=inputs();mog=next(u for u in units if u['sephiraVision']['preset']=='mog')
        self.assertEqual(next(p for p in catalog['presets'] if p['id']=='mog')['profile']['sephiraKitRevision'],2)
        for tier in mog['awakening']:
            for grant in tier:
                if grant[:2]==['PassiveSkill',1248]:grant[1]=1251
        mog['sephiraKitRevision']=1;mog['awakening'][0].reverse()
        mog['synchro'][3]=[['PassiveSkill',1280,-1]]
        mog['stats']['Magic']=999;mog['master']['desc']='My Spirit';mog['en']='My Mog'
        before=copy.deepcopy(mog);expected=copy.deepcopy(mog)
        for tier in expected['awakening']:
            for g in tier:
                if g[:2]==['PassiveSkill',1251]:g[1]=1248
        expected['sephiraKitRevision']=2;kits.repair(mog);self.assertEqual(mog,expected)
        kits.repair(mog);self.assertEqual(mog,expected)
        for mode in ('already_wind','removed_water'):
            edited=copy.deepcopy(before)
            if mode=='already_wind':edited['awakening'][3].append(['PassiveSkill',1248,-1])
            else:
                for tier in edited['awakening']:tier[:]=[g for g in tier if g[:2]!=['PassiveSkill',1251]]
            kits.repair(edited)
            self.assertFalse(any(g[:2]==['PassiveSkill',1251] for tier in edited['awakening'] for g in tier))
            self.assertEqual(sum(g[:2]==['PassiveSkill',1248] for tier in edited['awakening'] for g in tier),1 if mode=='already_wind' else 0)
            self.assertEqual(edited['synchro'],before['synchro'])

if __name__=='__main__':unittest.main()
