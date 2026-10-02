"""Retired comparison grants migrate without recreating skills or losing edits."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock
from test_animation_and_library import motion, resonance


class RetiredComparisonTests(unittest.TestCase):
    def test_all_four_copies_migrate_in_both_tier_types_without_mutating_input(self):
        saved = {'id': 13501, 'stats': {'Attack': 987}, 'skills': {'471010': {'from': 220020, 'en': 'Custom'}},
                 'ffbe': {'id': '401001207'}, 'awakening': [], 'synchro': []}
        for retired, original in motion.RETIRED_COMPARISON_SKILLS.items():
            saved['awakening'].append([['ActiveSkill', retired], ['ActiveSkill', original], ['PassiveSkill', retired, 8]])
            saved['synchro'].append([['ActiveSkill', retired]])
        before = copy.deepcopy(saved); result = motion.retire_comparison_skills(saved)
        self.assertEqual(saved, before)
        for i, (retired, original) in enumerate(motion.RETIRED_COMPARISON_SKILLS.items()):
            self.assertEqual(result['awakening'][i], [['ActiveSkill', original], ['PassiveSkill', retired, 8]])
            self.assertEqual(result['synchro'][i], [['ActiveSkill', original]])
        for field in ('stats', 'skills', 'ffbe'): self.assertEqual(result[field], saved[field])
        self.assertIs(motion.retire_comparison_skills(result), result)
        self.assertIs(motion.retire_comparison_skills({'party': {'id': 1001}}).get('party').get('id'), 1001)

    def test_other_grants_and_existing_duplicates_keep_their_order_and_values(self):
        unit = {'awakening': [[['ActiveSkill', 9400440], ['BaseParameter', 1, 50], ['ActiveSkill', 777], ['ActiveSkill', 777]],
                              [['ActiveSkill', 400440]]], 'synchro': []}
        result = motion.retire_comparison_skills(unit)
        self.assertEqual(result['awakening'][0], [['ActiveSkill', 400440], ['BaseParameter', 1, 50],
                                                ['ActiveSkill', 777], ['ActiveSkill', 777]])
        self.assertEqual(result['awakening'][1], unit['awakening'][1])

    def test_old_saved_grants_generate_only_the_original_skill_and_no_copy_definitions(self):
        game = {'Skill/DT_SkillData': {'Chakra': {'ID': 400440, 'skillAttrType': 'Ability', 'DamageType': 'None',
                 'defaultTargetRelation': 'Friendlies', 'TargetType': 'Self', 'hitCount': 1}},
                'Asset/Skill/DT_SkillAsset': {'shell': {'ID': 440111}},
                'Asset/Skill/CDT_SkillAsset_Demo': {'shell': {'ID': 440111}},
                'Battle/Sequencer/DT_BtlHitEffectData': {'template': {'ID': 449999}}}
        unit = {'awakening': [[['ActiveSkill', 9400440], ['ActiveSkill', 400440]]], 'synchro': [], 'skills': {}}
        before = copy.deepcopy(unit); tables = {}; jobs = []
        with tempfile.TemporaryDirectory() as temp, mock.patch.dict('sys.modules', {'ffbe_resonance': resonance}):
            source = Path(temp) / 'extracted/legacy' / (resonance.SHELL + '.uasset')
            source.parent.mkdir(parents=True); source.write_bytes(b'scheduled template fixture')
            motion.prepare_sequences(tables, [], jobs, [unit], temp, lambda rel: copy.deepcopy(game[rel]), mock.Mock())
            self.assertEqual(unit, before); self.assertEqual(len(jobs), 1)
            self.assertIn('/Skill/400440/', jobs[0]['asset']); self.assertNotIn('Skill/DT_SkillData', tables)
            self.assertNotIn('9400440', json.dumps(tables))
            self.assertFalse(hasattr(motion, 'comparison_catalog'))


if __name__ == '__main__': unittest.main()
