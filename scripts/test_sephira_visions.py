"""The actual installed loader must exclude disabled presets before any build work."""
import ast
import copy
import json
import os
from pathlib import Path
import tempfile
import unittest

from test_existing_visions import ROOT, installer, fina_installer
import _ffr_sephira as pack


def member(name, enabled):
    return {'key': name, 'id': 13500, 'skills': {'485000': {'from': 400010}},
            pack.FIELD: {'version': 1, 'preset': name, 'enabled': enabled}}


class SephiraTests(unittest.TestCase):
    def test_complete_catalog_coverage_unique_grants_and_native_stat_budgets(self):
        catalog = json.loads((ROOT / 'assets/sephira_visions/catalog.json').read_bytes())
        audit = json.loads((ROOT / 'assets/sephira_visions/native_coverage.json').read_bytes())
        self.assertEqual(len(catalog['presets']), 30)
        self.assertNotIn('great_dragon',[p['id'] for p in catalog['presets']])
        seen = {}
        for p in catalog['presets']:
            u = p['profile']; budget = catalog['nativeBudgets'][str(p['balance']['nativeBudget'])]
            self.assertEqual(u['stats'], budget['stats'])
            rewards = [[rank,*g] for rank,t in enumerate(u['synchro']) for g in t if g[0]=='BaseParameter']
            self.assertEqual(rewards, budget['statRewards'])
            self.assertEqual(u['synchro'][0], [])
            self.assertTrue(all(len(t)<=8 for t in u['awakening']))
            self.assertTrue(all(len(t)<=5 for t in u['synchro']))
            masters = [g for t in u['synchro'] for g in t if g[0]=='MasterSkill']
            self.assertEqual(masters, [['MasterSkill',u['master']['id'],-1]])
            self.assertEqual(u['master']['id'],u['id']*100)
            owned={int(s) for s in u['skills']} | {440000+(u['id']-13099)*10}
            self.assertFalse(owned & set(catalog['nativeReservations']['skills']))
            for kind,id in [('visions',u['id']),('units',u['id']),('commands',u['command']['id']),('masters',u['master']['id'])]:
                self.assertNotIn(id,catalog['nativeReservations'][kind])
            self.assertEqual(u['lb_custom']['mechanics'],'custom')
            self.assertFalse({'magnification','breakDamageValue','Cost','effectBundleList'} & u['lb_custom']['set'].keys())
            for field in ['awakening','synchro']:
                for rank,tier in enumerate(u[field]):
                    for kind,id,*_ in tier:
                        if kind not in ['ActiveSkill','PassiveSkill']: continue
                        if kind=='ActiveSkill': id=u['skills'].get(str(id),{}).get('from',id)
                        key=f'{kind}:{id}'
                        self.assertNotIn(key,seen,key)
                        seen[key]=p['id']
                        possible=catalog['grantUnlocks'].get(key,[])
                        if possible:
                            self.assertIn([field,rank],possible,key)
        for e in audit['entries']:
            self.assertEqual(seen[f"{e['kind']}:{e['id']}"],e['assignedTo'])
        self.assertEqual(len(audit['entries']),291)
        excluded={v['id'] for v in audit['excludedVisions']}
        budgets={p['balance']['nativeBudget'] for p in catalog['presets']}
        self.assertLessEqual(excluded,budgets)

    def test_expanded_kits_stay_in_requested_bounds_and_enemy_copies_have_player_limits(self):
        catalog=json.loads((ROOT/'assets/sephira_visions/catalog.json').read_bytes())
        hidden={s['id'] for s in json.loads((ROOT/'assets/existing_visions/payload/ability_hiding_review.json').read_bytes())['skills']}
        enemy_count=0
        for p in catalog['presets']:
            u=p['profile']; b=p['balance']
            grants=[g for t in u['awakening'] for g in t if g[0] in ['ActiveSkill','PassiveSkill']]
            mr=[g for t in u['synchro'] for g in t if g[0] in ['ActiveSkill','PassiveSkill']]
            self.assertGreaterEqual(len(grants),20,p['id'])
            self.assertLessEqual(len(grants),28,p['id'])
            self.assertEqual(len(grants),b['kitCount'])
            self.assertEqual(sum(g[0]=='ActiveSkill' for g in grants),b['activeCount'])
            self.assertEqual(sum(g[0]=='PassiveSkill' for g in grants),b['passiveCount'])
            self.assertEqual(sum(g[0]=='ActiveSkill' for g in mr),b['mrActiveCount'])
            self.assertEqual(sum(g[0]=='PassiveSkill' for g in mr),b['mrPassiveCount'])
            self.assertEqual(len(mr),b['mrSkillCount'])
            self.assertEqual(len(grants)+len(mr),b['totalSkillCount'])
            self.assertGreater(b['kitCount'],b['previousCount'])
            visual_ids=set()
            for sid in map(int,u['skills']):
                self.assertFalse(visual_ids & {sid,sid+1,sid+2})
                visual_ids.update([sid,sid+1,sid+2])
            for x in b['playerCopies']:
                recipe=u['skills'][str(x['id'])]; s=recipe['set']; combat=x['combat']
                self.assertNotIn(x['source'],hidden)
                self.assertEqual(s['belongCommandList'],[u['command']['id']])
                self.assertEqual(s['skillIdAfterModeChange'],-1)
                self.assertFalse(s['isApplyAllMag'])
                self.assertGreater(s['Cost'],0)
                self.assertLessEqual(s['accuracy'],100)
                self.assertLessEqual(combat['hitCount'],4)
                self.assertLessEqual(combat['breakDamageValue'],60)
                self.assertIn(combat['damageCalcType'],['None','Physic','Magic','Fixed','TargetMaxHPRatio','MPAbsorb'])
                if 'hitDamageRatioList' in s:
                    self.assertAlmostEqual(sum(s['hitDamageRatioList']),1)
                    self.assertEqual(sum(v>0 for v in s['hitDamageRatioList']),combat['hitCount'])
                if x['sourceCategory']=='enemy':
                    enemy_count+=1
                    if combat['parameterVariationType']=='Decrease' and combat['DamageType']!='None':
                        self.assertLessEqual(combat['magnification'],40)
                if x['source']==570710:
                    self.assertEqual(x['effects'],[1066])
                    self.assertNotIn(1446,x['effects'])
        self.assertGreater(enemy_count,100)

    def test_awakening_expansion_preserves_every_existing_mr_reward(self):
        catalog=json.loads((ROOT/'assets/sephira_visions/catalog.json').read_bytes())
        baseline=json.loads((ROOT/'scripts/fixtures/sephira_mr_revision2.json').read_bytes())
        self.assertEqual({p['id'] for p in catalog['presets']},set(baseline))
        for p in catalog['presets']:
            self.assertEqual(p['profile']['synchro'],baseline[p['id']],p['id'])
            self.assertEqual(p['profile']['sephiraRecipe'],3)

    def test_new_support_copies_use_finite_player_effects_and_bonus_dependencies(self):
        catalog=json.loads((ROOT/'assets/sephira_visions/catalog.json').read_bytes())
        copies={x['source']:x for p in catalog['presets'] for x in p['balance']['playerCopies']}
        expected={501780:[16101,16102],502710:[16102],502730:[16101],
                  505420:[1042],505430:[1163],505530:[1042,1163],
                  501340:[1042],500930:[1042],503700:[1066],570710:[1066]}
        for source,ids in expected.items():
            self.assertEqual(copies[source]['effects'],ids)
        self.assertNotIn(20001,copies[570610]['effects'])
        by_key={p['id']:p['profile'] for p in catalog['presets']}
        def skills(key): return {g[1] for f in ['awakening','synchro'] for t in by_key[key][f] for g in t}
        self.assertLessEqual({1441,1464},skills('ariana')) # Scion + Skill Flow
        self.assertLessEqual({1450,414600,414610},skills('lilith')) # Shield + guard commands

    def test_retired_dragon_is_excluded_even_in_older_enabled_rosters(self):
        old=member('great_dragon',True)
        user={'key':'independent_dragon','en':'Great Dragon'}
        before=copy.deepcopy(old)
        self.assertEqual(pack.active_units([old,user]),[user])
        self.assertEqual(old,before)

    def test_owner_bindings_change_only_semantic_conditions_on_private_rows(self):
        audit=json.loads((ROOT/'assets/sephira_visions/native_coverage.json').read_bytes())
        entries={e['id']:e for e in audit['entries'] if e['kind']=='PassiveSkill'}
        tables={pack.PASSIVE:{},pack.EFFECT:{},'Skill/DT_SkillData':{}}
        for sid in [1406,1410,1411,1418,1420,1432,1433,1454]:
            e=entries[sid]
            tables[pack.PASSIVE][str(sid)]={'ID':sid,'equipCost':e['equipCost'],'effectBundleList':e['effectBundles']}
            tables[pack.EFFECT].update({str(x['ID']):x for x in e['effects']})
        unit=member('edited',True)
        unit.update({'id':13782,'command':{'id':602},'lb_custom':{'from':440110},
                     'awakening':[[['PassiveSkill',sid,-1] for sid in [1406,1418,1454]]], 'synchro':[]})
        before=copy.deepcopy(tables); saved=copy.deepcopy(unit)
        bound=pack.bind_units([unit],tables.__getitem__)
        operations={};pack.prepare(operations,bound)
        self.assertEqual(tables,before);self.assertEqual(unit,saved)
        self.assertNotEqual(bound[0]['awakening'],unit['awakening'])
        for op in operations[pack.EFFECT]['add']:
            native=tables[pack.EFFECT][op['cloneFrom']]
            params=op['set']['ParamList']
            changed=[i for i,(a,b) in enumerate(zip(native['ParamList'],params)) if a!=b]
            self.assertEqual(len(changed),1)
            self.assertIn(params[changed[0]],[602,440000+(13782-13099)*10])
        tables[pack.EFFECT]['15125']['ParamList'][1]=999
        with self.assertRaisesRegex(ValueError,'re-audit'):
            pack.bind_units([unit],tables.__getitem__)

    def test_build_rejects_a_private_lb_that_would_shadow_a_native_skill(self):
        tables={pack.PASSIVE:{},pack.EFFECT:{},'Skill/DT_SkillData':{'Vanguard Glaive':{'ID':445010}}}
        u=member('a2',True)
        u.update({'id':13600,'lb_custom':{'from':440110},'awakening':[],'synchro':[]})
        with self.assertRaisesRegex(ValueError,'overlaps the game catalog'):
            pack.bind_units([u],tables.__getitem__)

    def test_non_pack_build_never_requires_optional_binding_tables(self):
        def unexpected(_): raise AssertionError('Should not read Sephira tables')
        self.assertEqual(pack.bind_units([{'key':'user'}],unexpected),[{'key':'user'}])

    def test_actual_roster_loader_skips_disabled_before_skill_conversion_and_keeps_save(self):
        raw = (ROOT / 'scripts/fixtures/crystal_fina/make_vision_mod.py').read_bytes()
        patched = installer.hook_builder(fina_installer.hook_builder(raw))
        loader = next(n for n in ast.parse(patched).body if isinstance(n, ast.FunctionDef) and n.name == 'load_units')
        selected = [member('a2', True), member('christine', False), {'key': 'party_1001', 'party': {'id': 1001}}]
        selected[1]['skills'] = {'unused invalid recipe': {}}
        with tempfile.TemporaryDirectory() as directory:
            spec = Path(directory) / 'units.json'
            spec.write_text(json.dumps(selected))
            env = {'os': os, 'json': json, 'SPEC_JSON': str(spec), 'UNITS': []}
            exec(compile(ast.Module(body=[loader], type_ignores=[]), 'installed_loader', 'exec'), env)
            loaded = env['load_units']()
            self.assertEqual([u['key'] for u in loaded], ['a2', 'party_1001'])
            self.assertEqual(loaded[0]['skills'], {485000: {'from': 400010}})
            self.assertNotIn('skills', loaded[1])
            self.assertEqual(json.loads(spec.read_text()), selected)

    def test_membership_filter_preserves_unrelated_native_party_and_user_edits(self):
        selected = [member('a2', False), {'key': 'native_13113', 'native': {'id': 13113}},
                    {'key': 'party_1001', 'party': {'id': 1001}}, {'key': 'user'}]
        before = copy.deepcopy(selected)
        self.assertEqual(pack.active_units(selected), selected[1:])
        self.assertEqual(selected, before)
        selected[0][pack.FIELD]['enabled'] = True
        self.assertEqual(pack.active_units(selected), selected)

    def test_duplicate_members_and_native_tagging_are_rejected(self):
        with self.assertRaises(ValueError): pack.active_units([member('a2', True), member('a2', False)])
        u = member('a2', True); u['native'] = {'id': 13110}
        with self.assertRaises(ValueError): pack.active_units([u])


if __name__ == '__main__': unittest.main()
