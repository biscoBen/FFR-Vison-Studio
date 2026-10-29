"""Requested Libra swaps and migrations from the actual previously shipped roster."""
import copy
import json
import unittest
from pathlib import Path
from test_sephira_runtime_rewards import inputs
from sephira_mr_layout import REWARDS, EARTH_LABEL, revise
import _ffr_sephira as pack

ROOT=Path(__file__).resolve().parents[1]

class MrLayoutTests(unittest.TestCase):
    def setUp(self):
        self.catalog,self.rows,self.units=inputs()
        self.by={p['id']:p for p in self.catalog['presets']}
        self.before=json.loads((ROOT/'scripts/fixtures/sephira_mr_layout_before.json').read_bytes())

    def old(self,key):
        unit=copy.deepcopy(self.before[key]['profile'])
        unit[pack.FIELD]={'version':1,'preset':key,'enabled':True}
        return unit

    def test_requested_layout_preserves_spirits_stats_and_tier_caps(self):
        for key,choices in REWARDS.items():
            old=self.before[key]['profile'];new=self.by[key]['profile']
            for rank,(kind,sid) in choices.items():
                self.assertEqual(new['synchro'][rank][0],[kind,sid,-1])
            for rank in range(10):
                self.assertEqual([g for g in new['synchro'][rank] if g[0] not in ('ActiveSkill','PassiveSkill')],
                                 [g for g in old['synchro'][rank] if g[0] not in ('ActiveSkill','PassiveSkill')])
            for f in old.keys()-{'awakening','synchro','sephiraMrRevision','sephiraPassiveText'}:
                expected=copy.deepcopy(old[f])
                if key=='primm' and f=='lb_custom':
                    expected['desc']=expected['desc'].replace('power of Blade Torrent','power of Moonlightbringer')
                self.assertEqual(expected,new[f],(key,f))
        primm=self.by['primm']['profile'];terra=self.by['trance_terra']['profile']
        self.assertIn(['PassiveSkill',1038,-1],terra['awakening'][2])
        self.assertIn(['PassiveSkill',1460,-1],primm['awakening'][3])
        apocalypse=next(int(s) for s,r in terra['skills'].items() if r['from']==505540)
        self.assertIn(['ActiveSkill',apocalypse,-1],terra['awakening'][3])
        self.assertTrue(all(len(t)<=8 for u in self.units for t in u['awakening']))

    def test_previous_release_migrates_atomically_once_with_custom_edits_preserved(self):
        for key in REWARDS:
            unit=self.old(key);unit['stats']['Attack']=77
            unit['studioAcquisition']={'version':1,'location':'mitra_shop','random':False,'hideSpoilers':False}
            unit['synchro'][2][0][2]=73
            if key=='trance_terra':
                source=next(s for s,r in unit['skills'].items() if r['from']==505540)
                remapped=int(source)//100*100+99
                unit['skills'][str(remapped)]=unit['skills'].pop(source)
                unit['skills'][str(remapped)]['set']['Cost']=19
                for g in unit['awakening'][2]:
                    if g[:2]==['ActiveSkill',int(source)]:g[1]=remapped
            old=copy.deepcopy(unit);pack.repair_equipable_mr(unit)
            self.assertEqual(unit['sephiraMrRevision'],self.by[key]['profile']['sephiraMrRevision'])
            for rank,(kind,sid) in REWARDS[key].items():self.assertEqual(unit['synchro'][rank][0],[kind,sid,-1])
            for f in old.keys()-{'awakening','synchro','sephiraMrRevision','sephiraPassiveText'}:
                self.assertEqual(unit[f],old[f],(key,f))
            self.assertEqual(unit['synchro'][2][0][2],73)
            if key=='trance_terra':self.assertIn(['ActiveSkill',remapped,-1],unit['awakening'][3])
            if key=='primm':self.assertEqual(unit['sephiraPassiveText']['1526'],EARTH_LABEL)
            unit['synchro'][1][0]=['PassiveSkill',1009,-1]
            final=copy.deepcopy(unit);pack.repair_equipable_mr(unit);self.assertEqual(unit,final)

    def test_conflicting_later_step_or_full_tier_leaves_everything_untouched(self):
        terra=self.old('trance_terra')
        while len(terra['awakening'][3])<8:terra['awakening'][3].append(['ActiveSkill',210220,-1])
        for unit,pattern in ((terra,'awakening slot'),(self.old('minfilia'),'MR1 was edited')):
            if unit[pack.FIELD]['preset']=='minfilia':unit['synchro'][1][0]=['PassiveSkill',1009,-1]
            before=copy.deepcopy(unit)
            with self.assertRaisesRegex(ValueError,pattern):pack.repair_equipable_mr(unit)
            self.assertEqual(unit,before)
        # Revision 0 must not partially advance to 1 if its later step conflicts.
        p=self.by['trance_terra'];old=self.old('trance_terra')
        old.update(copy.deepcopy(p['mrRestoration']['before']));old.pop('sephiraMrRevision')
        while len(old['awakening'][3])<8:old['awakening'][3].append(['ActiveSkill',210220,-1])
        before=copy.deepcopy(old)
        with self.assertRaises(ValueError):pack.repair_equipable_mr(old)
        self.assertEqual(old,before)

    def test_earth_imbue_is_named_equipable_and_old_barusa_identity_stays_defined(self):
        bound=pack.bind_units(self.units,self.rows.__getitem__)
        primm=next(u for u in bound if pack.membership(u)['preset']=='primm')
        barusa=next(u for u in bound if pack.membership(u)['preset']=='barusa')
        new=next(b['passive'] for b in primm['_sephiraBindings'] if b['passive']['set']['ID']==1945)
        self.assertEqual(new['set']['Name'],'Imbue Earth');self.assertEqual(new['set']['equipCost'],20)
        self.assertEqual(primm['synchro'][1][0],['PassiveSkill',1945,-1])
        oldid=pack.private_passive_id('barusa',1526)
        self.assertNotEqual(oldid,1945)
        self.assertTrue(any(b['passive']['set']['ID']==oldid for b in barusa['_sephiraBindings']))
        self.assertFalse(any(g[1]==oldid for tier in barusa['synchro'] for g in tier if g[0]=='PassiveSkill'))

if __name__=='__main__':unittest.main()
