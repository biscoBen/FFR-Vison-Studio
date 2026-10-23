"""Runtime classification and learned-command contracts across the whole roster."""
import copy
import gzip
import json
import unittest

from test_existing_visions import ROOT
import _ffr_sephira as pack


def inputs():
    catalog = json.loads((ROOT / 'assets/sephira_visions/catalog.json').read_bytes())
    native = json.loads(gzip.decompress((ROOT / 'scripts/fixtures/sephira_challenges/rows.json.gz').read_bytes()))
    units = [dict(copy.deepcopy(p['profile']), sephiraVision={'version': 1, 'preset': p['id'], 'enabled': True})
             for p in catalog['presets']]
    selected = json.loads((ROOT / 'scripts/fixtures/sephira_runtime_sources.json').read_bytes())
    native['Skill/DT_SkillData'] = {k: r for k, r in selected['skills'].items()}
    return catalog, native, units


class SephiraRuntimeRewardTests(unittest.TestCase):
    def test_every_private_passive_has_a_unique_runtime_passive_id(self):
        _, native, units = inputs()
        before = copy.deepcopy(units)
        bound = pack.bind_units(units, native.__getitem__)
        private = [b['passive'] for u in bound for b in u['_sephiraBindings']]
        identities = [r['set']['ID'] for r in private]
        native_ids = {r['ID'] for r in native[pack.PASSIVE].values()}
        self.assertEqual(len(identities), 47)
        self.assertEqual(len(set(identities)), 47)
        self.assertTrue(all(1000 <= sid < 2000 for sid in identities))
        self.assertFalse(set(identities) & native_ids)
        for unit in bound:
            available = native_ids | {b['passive']['set']['ID'] for b in unit['_sephiraBindings']}
            for field in ('awakening', 'synchro'):
                for tier in unit[field]:
                    for grant in tier:
                        if grant[0] == 'PassiveSkill': self.assertIn(grant[1], available)
        self.assertEqual(units, before)

    def test_passive_ids_stay_stable_when_other_presets_or_allocated_vision_ids_change(self):
        _, native, units = inputs()
        all_bound = {u['key']: u for u in pack.bind_units(units, native.__getitem__)}
        for original in units:
            changed = copy.deepcopy(original)
            changed['id'] += 3000
            changed['command']['id'] += 100
            actual, = pack.bind_units([changed], native.__getitem__)
            expected = all_bound[original['key']]
            for field in ('awakening', 'synchro'):
                def passive_ids(unit):
                    return [g[1] for tier in unit[field] for g in tier if g[0] == 'PassiveSkill']
                self.assertEqual(passive_ids(actual), passive_ids(expected))

    def test_reported_blank_ranks_and_minfilia_awakening_resolve_as_passives(self):
        _, native, units = inputs()
        result = {u[pack.FIELD]['preset']: u for u in pack.bind_units(units, native.__getitem__)}
        for preset, rank in [('crystal_fina', 3), ('crystal_fina', 7), ('christine', 7),
                             ('folka', 7), ('minfilia', 9)]:
            kind, identity, _ = result[preset]['synchro'][rank][0]
            self.assertEqual(kind, 'PassiveSkill')
            self.assertTrue(1000 <= identity < 2000, (preset, rank, identity))
        minfilia = result['minfilia']
        self.assertTrue(any(g[0] == 'PassiveSkill' and 1600 <= g[1] < 2000
                            for g in minfilia['awakening'][0]))

    def test_every_private_mr_active_is_a_learnable_general_command(self):
        _, native, units = inputs()
        before = copy.deepcopy(units)
        result = pack.player_units(units, native.__getitem__)
        fixed = []
        for unit in result:
            learned = {g[1] for tier in unit['synchro'] for g in tier if g[0] == 'ActiveSkill'}
            for identity, recipe in unit['skills'].items():
                if int(identity) in learned:
                    self.assertEqual(recipe['set']['belongCommandList'], [1], unit['key'])
                    self.assertIn(recipe['set']['commandIdBelongDebuggingAllSkills'], ([900, -1], [901, -1]))
                    fixed.append((unit[pack.FIELD]['preset'], recipe['en']))
        self.assertEqual(len(fixed), 15)
        for case in [('crystal_fina', 'Crystal Renewal'), ('folka', 'Waterga Surge'), ('folka', 'Tidal Invocation')]:
            self.assertIn(case, fixed)
        self.assertEqual(units, before)

    def test_hp_healing_is_available_in_field_without_changing_power_cost_or_targets(self):
        _, native, units = inputs()
        result = pack.player_units(units, native.__getitem__)
        fina = next(u for u in result if u[pack.FIELD]['preset'] == 'crystal_fina')
        renewal = [r for r in fina['skills'].values() if r['en'] == 'Crystal Renewal']
        self.assertEqual(len(renewal), 2)
        for recipe in renewal:
            self.assertEqual(recipe['set']['availableLocation'], 'Anywhere')
            self.assertEqual(recipe['set']['mapEffectType'], 'RecoveryHP')
            self.assertFalse(recipe['set']['isTargetIgnoreSelf'])
        for before, after in zip(units, result):
            for sid, recipe in before['skills'].items():
                for field in ('Cost', 'magnification', 'hitCount', 'TargetType', 'defaultTargetRelation'):
                    self.assertEqual(recipe['set'].get(field), after['skills'][sid]['set'].get(field))

    def test_user_availability_edits_and_untagged_units_are_preserved(self):
        _, native, units = inputs()
        fina = next(u for u in units if u[pack.FIELD]['preset'] == 'crystal_fina')
        for recipe in fina['skills'].values():
            if recipe['en'] == 'Crystal Renewal':
                recipe['set'].update(availableLocation='BattleOnly', mapEffectType='None', isTargetIgnoreSelf=True)
        untagged = copy.deepcopy(fina); untagged.pop(pack.FIELD)
        actual, ordinary = pack.player_units([fina, untagged], native.__getitem__)
        self.assertEqual(ordinary, untagged)
        for recipe in actual['skills'].values():
            if recipe['en'] == 'Crystal Renewal':
                self.assertEqual(recipe['set']['availableLocation'], 'BattleOnly')
                self.assertEqual(recipe['set']['mapEffectType'], 'None')
                self.assertTrue(recipe['set']['isTargetIgnoreSelf'])


if __name__ == '__main__': unittest.main()
