"""Native-source and saved-mode regressions for the Sephira correction."""
import copy
import gzip
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from test_existing_visions import ROOT
import _ffr_sephira as pack
import _ffr_testing as testing
import _ffr_shrine_challenges as challenges
import _ffr_crystal_cave as caves
from sephira_reward_sources import protected_rewards


def inputs():
    catalog = json.loads((ROOT/'assets/sephira_visions/catalog.json').read_bytes())
    native = json.loads(gzip.decompress((ROOT/'scripts/fixtures/sephira_challenges/rows.json.gz').read_bytes()))
    units = [dict(copy.deepcopy(p['profile']), sephiraVision={'version':1, 'preset':p['id'], 'enabled':True})
             for p in catalog['presets']]
    return catalog, native, units


def settings(root, *, borrowed=True, shop=False):
    path = Path(root)/pack.CONFIG
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({'schema':1, 'useBorrowedSkillVisuals':borrowed, 'shopAcquisitionOverride':shop}))


class SephiraRewardSourceTests(unittest.TestCase):
    def test_visual_settings_save_cannot_clear_shop_override_and_legacy_snapshots_default_off(self):
        routes = {}
        class App:
            def get(self, path):
                def register(function): routes['GET',path] = function; return function
                return register
            def put(self, path):
                def register(function): routes['PUT',path] = function; return function
                return register
        with tempfile.TemporaryDirectory() as root:
            settings(root,shop=True)
            pack.register(App(), {'ROOT':root,'state':{}})
            put=routes['PUT','/api/sephira/settings']
            get=routes['GET','/api/sephira/settings']
            self.assertTrue(put({'schema':1,'useBorrowedSkillVisuals':False})['shopAcquisitionOverride'])
            self.assertFalse(get()['useBorrowedSkillVisuals'])
            self.assertFalse(put({'schema':1,'useBorrowedSkillVisuals':False,'shopAcquisitionOverride':False})['shopAcquisitionOverride'])
            Path(root,pack.CONFIG).write_text(json.dumps({'schema':1,'useBorrowedSkillVisuals':True}))
            self.assertFalse(get().get('shopAcquisitionOverride',False))
            with self.assertRaises(ValueError):
                pack.validate_settings({'schema':1,'useBorrowedSkillVisuals':True,'shopAcquisitionOverride':1})

    def test_every_learned_grant_and_private_recipe_excludes_kept_vision_mr(self):
        catalog, native, units = inputs()
        excluded = {v['id'] for v in json.loads((ROOT/'assets/sephira_visions/native_coverage.json').read_bytes())['excludedVisions']}
        protected = protected_rewards(native['Item/Vision/DT_VisionSynchroMasteryData'], excluded)
        self.assertEqual(len(protected), 55)
        for u in units:
            for field in ('awakening', 'synchro'):
                for tier in u[field]:
                    for kind, identity, *_ in tier:
                        source = u['skills'].get(str(identity), {}).get('from', identity) if kind=='ActiveSkill' else identity
                        self.assertNotIn((kind,source), protected, u['key'])
            for recipe in u['skills'].values():
                self.assertNotIn(('ActiveSkill',recipe['from']),protected)
        replacements = [r for p in catalog['presets'] for r in p['rewardReplacements']]
        self.assertEqual(len(replacements),52)
        self.assertEqual(sum(r['field']=='awakening' for r in replacements),8)
        for r in replacements:
            self.assertEqual(r['protectedOwners'],protected[r['oldKind'],r['oldSource']])
            if r['newGrant'][0]=='PassiveSkill':
                self.assertTrue(r['equipment'] or r['enemies'])
            else:
                self.assertGreaterEqual(r['source'],240000)
        self.assertEqual(len(catalog['protectedMrRewards']),55)

    def test_private_bonus_names_preserve_native_mechanics_and_positive_equip_cost(self):
        _, native, units = inputs()
        before = copy.deepcopy(units)
        bound = pack.bind_units(units,native.__getitem__)
        tables = {}; pack.prepare(tables,bound)
        labels = {int(k):v for u in units for k,v in u.get('sephiraPassiveText',{}).items()}
        bonus_rows = [r for r in tables[pack.PASSIVE]['add'] if 'Name' in r['set'] and 'effectBundleList' not in r['set']]
        self.assertEqual(len(bonus_rows),18)
        for row in bonus_rows:
            source = native[pack.PASSIVE][row['cloneFrom']]
            result = testing.apply_fields(source,row['set'])
            self.assertEqual(result['effectBundleList'],source['effectBundleList'])
            self.assertEqual(result['equipCost'],source['equipCost'] or 20)
            self.assertEqual(result['Name'],labels[source['ID']]['name'])
            self.assertEqual(set(row['set'])-{'ID','Name','Description','equipCost'},set())
        self.assertEqual(units,before)

    def test_shop_override_is_ephemeral_reversible_and_excludes_disabled_or_unrelated_units(self):
        _,native,units = inputs()
        units[0]['sephiraVision']['enabled'] = False
        units[1]['studioAcquisition'] = {'version':1,'location':'battle','random':False,'hideSpoilers':True}
        untagged = copy.deepcopy(units[2]); untagged.pop('sephiraVision'); untagged['price']=987
        roster = units+[untagged]; before=copy.deepcopy(roster)
        with tempfile.TemporaryDirectory() as root:
            settings(root,shop=True)
            self.assertTrue(pack.validate_settings(pack.settings(root))['shopAcquisitionOverride'])
            active=pack.visual_units(pack.active_units(roster),root,native.__getitem__)
            tagged=[u for u in active if pack.membership(u) is not None]
            self.assertEqual(len(tagged),29)
            self.assertTrue(all(u['price']==1 and u['studioAcquisition']['location']=='mitra_shop' for u in tagged))
            self.assertEqual(challenges.plans(tagged),[])
            tables={}; caves.prepare_shops(tables,tagged,native.__getitem__)
            shop=native['Shop/DT_ShopList']
            edits=tables['Shop/DT_ShopList']['set']
            self.assertEqual(len(edits),1)
            inventory=testing.apply_fields(shop[edits[0]['row']],edits[0]['set'])['ItemList']
            offered=[i for i in inventory if i['ItemId'] in {u['id'] for u in tagged}]
            self.assertEqual(len(offered),29)
            self.assertTrue(all(i['PriceRatio']==1 and i['Condition']=='' and i['MaxOrderNum']==1 for i in offered))
            self.assertEqual(active[-1],untagged)
            settings(root,shop=False)
            self.assertEqual(pack.visual_units(roster,root,native.__getitem__),before)
        self.assertEqual(roster,before)

    def test_verifier_uses_original_visual_mode_even_though_saved_recipes_keep_borrowed_donors(self):
        _,native,units=inputs(); rel='Asset/Skill/DT_SkillAsset'
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);settings(root,borrowed=False)
            spec=root/'mods/EstherTsukiko/units.json';spec.write_text(json.dumps(units))
            for name,rows in native.items():
                path=root/'extracted/rows'/(name+'.json');path.parent.mkdir(parents=True,exist_ok=True)
                path.write_text(json.dumps({'rows':rows}))
            selected=pack.visual_units(units,root,native.__getitem__)
            actual=testing.prepare({},selected,root,native.__getitem__)[rel]
            raw=testing.prepare({},units,root,native.__getitem__)[rel]
            self.assertNotEqual(actual,raw)  # This is the reported final-check mismatch.
            built=copy.deepcopy(native[rel])
            for op in actual['add']:built[op['row']]=testing.apply_fields(native[rel][op['cloneFrom']],op['set'])
            plan=root/'build/visions_mod/patch.json';plan.parent.mkdir(parents=True)
            plan.write_text(json.dumps({'tables':[actual]}))
            def operations(folder,selected,rows):
                return {rel:testing.prepare({},selected,folder,native.__getitem__)[rel]}
            def readback(command,**kwargs):Path(command[3]).write_text(json.dumps({'rows':built}))
            with mock.patch.object(testing,'verification_operations',side_effect=operations), mock.patch.object(testing.subprocess,'run',side_effect=readback):
                testing.verify(root,['native-tool'],'unused.usmap')


if __name__=='__main__':unittest.main()
