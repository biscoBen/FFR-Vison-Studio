"""Bulk visual profiles must agree between catalog metadata and engine mechanics."""
import copy
import unittest
from test_animation_and_library import motion


class BulkAnimationPolicyTests(unittest.TestCase):
    def test_healing_status_and_defense_use_actual_mechanics_without_changing_them(self):
        base = {'skillEffectType': 'None', 'defaultTargetRelation': 'Friendlies',
                'parameterType': 'None', 'defaultTargetState': 'Alive'}
        cases = [
            ({**base, 'skillEffectType': 'DamageAndRecovery', 'parameterType': 'HitPoint',
              'parameterVariationType': 'Increase', 'magnification': power}, [], (donor, 'healing_tier'))
            for power, donor in ((100, 210010), (300, 210020), (1500, 210030))]
        cases += [(base, [{'EffectType': 'ParameterVariation', 'statusCondition': 'Regene'}], (210050, 'status_theme')),
                  (base, [{'EffectType': 'Deffence', 'statusCondition': 'None'}], (230040, 'defense_theme')),
                  (base, [{'EffectType': 'CureStatusCondition', 'ParamList': [1]}], (210120, 'cleanse')),
                  ({**base, 'defaultTargetState': 'Dead'}, [{'EffectType': 'Revival'}], (210140, 'revival'))]
        for raw, effects, expected in cases:
            before = copy.deepcopy((raw, effects))
            self.assertEqual(motion.semantic_donor({'id': 1}, raw, effects), expected)
            self.assertEqual((raw, effects), before)
        self.assertIsNone(motion.semantic_donor({}, {**base, 'parameterType': 'MagicPoint'}, []))
        self.assertIsNone(motion.semantic_donor({}, base, [{'EffectType': 'SummonUnit'}, {'statusCondition': 'Haste'}]))

    def test_ui_details_and_raw_rows_generate_identical_profiles_and_preserve_existing_bindings(self):
        raw = {'ID': 900001, 'defaultTargetRelation': 'Friendlies', 'skillEffectType': 'None',
               'effectBundleList': [{'effectId': 5}]}
        effect = {'EffectType': 'ParameterVariation', 'statusCondition': 'Regene'}
        catalog = {'skills': [{'id': 900001, 'name': 'Recovery Aura', 'attr': 'Ability', 'seq': [], 'hits': 2},
                             {'id': 210050, 'name': 'Regen', 'attr': 'Magic', 'seq': [1], 'hits': 1}]}
        before = copy.deepcopy(catalog)
        engine = motion.effect_policy(catalog, {900001: raw}, {5: effect})
        ui = copy.deepcopy(catalog)
        ui['duplicatePolicy'] = {'details': {'skills': {'900001': {**raw,
            'effectBundleList': [{'effectId': {'mechanics': effect}}]}}}}
        self.assertEqual(motion.effect_policy(ui), engine)
        self.assertEqual(engine['skills']['900001']['donor'], 210050)
        self.assertNotIn('210050', engine['skills']); self.assertEqual(catalog, before)

    def test_physical_styles_preserve_barrage_and_do_not_map_hidden_normal_attacks(self):
        donors = [500010, 500020, 500950, 500040, 500050, 501310, 500110, 500150, 500740]
        skills = [{'id': sid, 'name': str(sid), 'attr': 'Ability', 'seq': [2]} for sid in donors]
        for sid, name, power in ((900001, 'Heavy Slash', 50), (900002, 'Quick Shot', 20),
                                  (900003, 'Hammer Smash', 40), (400300, 'Barrage', 12), (400260, 'Steal', 12), (404010, 'Attack', 12)):
            skills.append({'id': sid, 'name': name, 'attr': 'Ability', 'seq': [], 'hits': 4,
                           'dmgType': 'Physic', 'element': 'None', 'mag': power})
        policy = motion.effect_policy({'skills': skills})['skills']
        self.assertEqual({int(sid): row['donor'] for sid, row in policy.items()},
                         {900001: 501310, 900002: 500110, 900003: 500020})


if __name__ == '__main__': unittest.main()
