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
        self.assertEqual(len(catalog['presets']), 31)
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

    def test_owner_bindings_change_only_semantic_conditions_on_private_rows(self):
        audit=json.loads((ROOT/'assets/sephira_visions/native_coverage.json').read_bytes())
        entries={e['id']:e for e in audit['entries'] if e['kind']=='PassiveSkill'}
        tables={pack.PASSIVE:{},pack.EFFECT:{}}
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
