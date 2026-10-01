"""Ordinary skill reaction flags, separate from pending visual profiles."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from test_animation_and_library import motion, resonance


class SkillReactionColorTests(unittest.TestCase):
    def test_single_area_multi_hit_and_support_keep_color_handling_without_extra_hits(self):
        cases = [(400320, 'Ability', 'Physic', 'Enemies', 'Single', 1),
                 (400340, 'Ability', 'Physic', 'Enemies', 'Group', 1),
                 (414420, 'Ability', 'Physic', 'Enemies', 'Single', 3),
                 (210180, 'Magic', 'Magic', 'Friendlies', 'Single', 1)]
        game = {'Skill/DT_SkillData': {str(sid): {'ID': sid, 'skillAttrType': attr, 'DamageType': damage,
                'defaultTargetRelation': relation, 'TargetType': target, 'hitCount': hits,
                'magnification': 55, 'effectBundleList': [{'effectId': sid}]} for sid, attr, damage, relation, target, hits in cases},
                'Asset/Skill/DT_SkillAsset': {'shell': {'ID': 440111}},
                'Asset/Skill/CDT_SkillAsset_Demo': {'shell': {'ID': 440111}},
                'Battle/Sequencer/DT_BtlHitEffectData': {'template': {'ID': 449999}}}
        original = copy.deepcopy(game); tables = {}; clones = []; jobs = []
        unit = {'awakening': [[['ActiveSkill', sid] for sid, *_ in cases]], 'synchro': [], 'skills': {}}
        with tempfile.TemporaryDirectory() as temp, mock.patch.dict('sys.modules', {'ffbe_resonance': resonance}):
            source = Path(temp) / 'extracted/legacy' / (resonance.SHELL + '.uasset')
            source.parent.mkdir(parents=True); source.write_bytes(b'Synthetic cooked-shell presence fixture')
            motion.prepare_sequences(tables, clones, jobs, [unit], temp, lambda rel: copy.deepcopy(game[rel]), mock.Mock())
            for sid, *_, hits in cases:
                job = next(j for j in jobs if f'/Skill/{sid}/' in j['asset'])
                events = [e for e in job['plan']['events'] if e['set']['EventType'] == 'OtherReaction']
                self.assertEqual(len(events), hits)
                self.assertEqual([e['set']['Other_Reaction_Id'] for e in events], [sid] * hits)
                self.assertTrue(all(e['set']['Otber_Reaction_bChangeColor'] is True for e in events))
                self.assertTrue(all(e['set']['Otber_Reaction_bReturnIdleMotion'] is True for e in events))
                self.assertTrue(all(e['time'] < job['plan']['duration'] for e in events))
            self.assertNotIn('Skill/DT_SkillData', tables)
            self.assertEqual(game, original)
            self.assertEqual(len(jobs), len(cases))
            self.assertEqual(motion.prepare_sequences(tables, clones, jobs, [unit], temp,
                             lambda rel: copy.deepcopy(game[rel]), mock.Mock()), [])
            self.assertEqual(len(jobs), len(cases))

    def test_ordinary_fix_does_not_change_the_lb_scheduler_or_existing_sequences(self):
        plan = resonance.schedule(1.0, 1, 440110)
        reaction = next(e['set'] for e in plan['events'] if e['set']['EventType'] == 'OtherReaction')
        self.assertIs(reaction['Otber_Reaction_bChangeColor'], False)
        game = {'Skill/DT_SkillData': {'skill': {'ID': 400320}},
                'Asset/Skill/DT_SkillAsset': {'native': {'ID': 400321}}}
        tables = {}; clones = []; jobs = []
        with tempfile.TemporaryDirectory() as temp:
            result = motion.prepare_sequences(tables, clones, jobs,
                     [{'awakening': [[['ActiveSkill', 400320]]]}], temp,
                     lambda rel: copy.deepcopy(game[rel]), mock.Mock())
        self.assertEqual(result, []); self.assertEqual(tables, {}); self.assertEqual(jobs, [])


if __name__ == '__main__':
    unittest.main()
