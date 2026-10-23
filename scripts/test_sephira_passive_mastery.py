"""Collection-wide coverage, passive placement and elemental icon contracts."""
import copy
import json
from pathlib import Path
import tempfile
import unittest

from test_existing_visions import ROOT, native
from test_sephira_runtime_rewards import inputs
import _ffr_sephira as pack
from sephira_passive_mastery import REWARDS


class PassiveMasteryTests(unittest.TestCase):
    def test_all_131_original_passives_survive_once_in_150_single_mr_slots(self):
        catalog, _, units = inputs()
        audit = json.loads((ROOT/'assets/sephira_visions/native_coverage.json').read_bytes())
        required = {e['id'] for e in audit['entries'] if e['kind'] == 'PassiveSkill'}
        actual = []
        for preset, unit in zip(catalog['presets'], units):
            self.assertTrue(all(g[0] == 'ActiveSkill' for tier in unit['awakening'] for g in tier))
            choices = [unit['synchro'][rank][0] for rank in (1, 3, 5, 7, 9)]
            self.assertTrue(all(g[0] == 'PassiveSkill' for g in choices))
            self.assertEqual([g[1] for g in choices], REWARDS[preset['id']])
            actual.extend(g[1] for g in choices)
            previous = {g[1] for field in ('awakening','synchro')
                        for tier in preset['revision5Progression'][field] for g in tier if g[0]=='ActiveSkill'}
            self.assertEqual({g[1] for tier in unit['awakening'] for g in tier}, previous)
        self.assertEqual(len(required), 131)
        self.assertEqual(len(actual), len(set(actual)))
        self.assertEqual(len(actual), 150)
        self.assertLessEqual(required, set(actual))
        self.assertEqual(len(set(actual) - required), 19)

    def test_all_elemental_damage_icons_match_damage_with_explicit_user_overrides_preserved(self):
        _, rows, units = inputs()
        for unit in units:
            for recipe in unit['skills'].values(): recipe['set'].pop('SkillIcon.TagName', None)
        before = copy.deepcopy(units)
        native_skills = {s['ID']:s for s in rows['Skill/DT_SkillData'].values()}
        fixed = 0
        for unit in pack.player_units(units, rows.__getitem__):
            for recipe in unit['skills'].values():
                source = native_skills[recipe['from']]; effective = dict(source, **recipe['set'])
                if (effective.get('skillEffectType') == 'DamageAndRecovery' and
                    effective.get('parameterVariationType') == 'Decrease' and effective.get('parameterType') == 'HitPoint' and
                    effective.get('element') in ('Fire','Ice','Thunder','Water','Wind','Earth','Light','Dark')):
                    self.assertEqual(recipe['set']['SkillIcon.TagName'], 'UI.Skill.Action.Icon.' + effective['element'])
                    fixed += source['SkillIcon']['TagName'] != recipe['set']['SkillIcon.TagName']
        self.assertEqual(fixed, 39)
        self.assertEqual(units, before)
        recipe = next(r for u in units for r in u['skills'].values() if r['set'].get('element')=='Ice')
        recipe['set']['SkillIcon.TagName'] = 'UI.Skill.Action.Icon.Support'
        result = pack.player_units(units, rows.__getitem__)
        changed = next(r for u in result for r in u['skills'].values() if r['jp']==recipe['jp'])
        self.assertEqual(changed['set']['SkillIcon.TagName'], 'UI.Skill.Action.Icon.Support')

    def test_more_than_16_command_icons_have_distinct_brushes_and_keep_original_icons(self):
        catalog, _, units = inputs()
        original = {'original': {'Tag': {'TagName':'UI.Skill.Command.Icon.13110'},
                                 'Brush': {'ResourceObject':'Cloud'}}}
        tables = {}
        for unit in units:
            native.prepare_command_icon(tables, unit, lambda _: original)
        for rel, plan in tables.items():
            self.assertEqual(plan['set'], [])
            self.assertEqual(len(plan['add']), 30)
            tags = set()
            for unit, op in zip(units, plan['add']):
                fields = op['set']; tags.add(fields['Tag.TagName'])
                self.assertEqual(fields['Tag.TagName'], native.command_icon(unit, units, [], None))
                self.assertEqual(fields['Brush.ResourceObject'],
                                 f'/Game/UI/Textures/Icon/menu/ICON_Ability_summon{unit["id"]}')
            self.assertEqual(len(tags), 30)
        self.assertEqual(original['original']['Brush']['ResourceObject'], 'Cloud')


if __name__ == '__main__': unittest.main()
