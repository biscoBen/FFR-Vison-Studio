"""Independent original-visual copies preserve mechanics and can coexist."""
import copy
from pathlib import Path
import tempfile
import unittest
from unittest import mock
from test_animation_and_library import motion, resonance


def fixture():
    skills = {}
    for sid, (original, name) in motion.COMPARISON_SKILLS.items():
        skills[name] = {'ID': original, 'SortId': original, 'Name': name, 'Description': name + ' original description',
                        'skillAttrType': 'Ability', 'DamageType': 'Physic' if original == 505580 else 'None',
                        'defaultTargetRelation': 'Enemies' if original == 505580 else 'Friendlies',
                        'TargetType': 'Group' if original in (505580, 414500) else 'Self' if original == 400440 else 'Single',
                        'hitCount': 2 if original == 505580 else 1, 'magnification': original % 100,
                        'skillIdAfterModeChange': -1, 'playSequencerId': -1,
                        'effectBundleList': [{'effectId': original}], 'hitDamageRatioList': [0.5, 0.5]}
    return {'Skill/DT_SkillData': skills, 'Asset/Skill/DT_SkillAsset': {'shell': {'ID': 440111}},
            'Asset/Skill/CDT_SkillAsset_Demo': {'shell': {'ID': 440111}},
            'Battle/Sequencer/DT_BtlHitEffectData': {'template': {'ID': 449999}}}


class ComparisonSkillTests(unittest.TestCase):
    def test_catalog_adds_four_distinct_copy_ids_without_touching_originals(self):
        catalog = {'skills': [{'id': original, 'name': name, 'attr': 'Ability', 'seq': [], 'hits': 1,
                               'element': 'Dark', 'dmgType': 'Physic', 'mag': 42}
                              for original, name in motion.COMPARISON_SKILLS.values()],
                   'animationPolicy': {'schema': 1, 'skills': {}}}
        before = copy.deepcopy(catalog); result = motion.comparison_catalog(catalog)
        self.assertEqual(catalog, before); self.assertEqual(result['skills'][:4], catalog['skills'])
        self.assertEqual(len({r['id'] for r in result['skills']}), 8)
        for row in result['skills'][4:]:
            self.assertTrue(row['name'].endswith(' (Copy)'))
            self.assertEqual(row['comparisonOf'], motion.COMPARISON_SKILLS[row['id']][0])
            self.assertNotIn(str(row['id']), motion.effect_policy(result)['skills'])
        missing = motion.comparison_catalog({'skills': []})
        self.assertEqual(missing['skills'], [])
        with self.assertRaisesRegex(ValueError, 'already in use'): motion.comparison_catalog(result)

    def test_selected_copies_share_exact_original_mechanics_without_consuming_custom_slots(self):
        game = fixture(); before = copy.deepcopy(game); tables = {}
        ids = list(motion.COMPARISON_SKILLS); units = [{'skills': {}}]
        definitions = motion.prepare_comparison_skills(tables, lambda rel: game[rel], ids, units)
        self.assertEqual(game, before); self.assertEqual(units, [{'skills': {}}])
        additions = tables['Skill/DT_SkillData']['add']
        self.assertEqual(len(additions), 4); self.assertEqual(tables['Skill/DT_SkillData']['set'], [])
        for op in additions:
            original = game['Skill/DT_SkillData'][op['cloneFrom']]; sid = op['set']['ID']
            result = {**original, **op['set']}
            self.assertEqual(definitions[sid], result)
            self.assertEqual({k: v for k, v in result.items() if k not in ('ID', 'SortId', 'Name')},
                             {k: v for k, v in original.items() if k not in ('ID', 'SortId', 'Name')})
        empty = {}; motion.prepare_comparison_skills(empty, lambda rel: game[rel], [], units)
        self.assertEqual(empty, {})

    def test_collision_or_alternate_mode_cannot_overwrite_game_or_custom_skills(self):
        sid = next(iter(motion.COMPARISON_SKILLS))
        for location in ('Skill/DT_SkillData', 'Asset/Skill/DT_SkillAsset', 'Asset/Skill/CDT_SkillAsset_Demo',
                         'Battle/Sequencer/DT_BtlHitEffectData'):
            game = fixture(); game[location]['occupied'] = {'ID': sid + (location != 'Skill/DT_SkillData')}
            before = copy.deepcopy(game)
            with self.subTest(location=location), self.assertRaisesRegex(ValueError, 'already in use'):
                motion.prepare_comparison_skills({}, lambda rel: game[rel], [sid], [])
            self.assertEqual(game, before)
        game = fixture()
        with self.assertRaisesRegex(ValueError, 'already in use'):
            motion.prepare_comparison_skills({}, lambda rel: game[rel], [sid], [{'skills': {str(sid): {}}}])
        game['Skill/DT_SkillData']['Chakra']['skillIdAfterModeChange'] = 123
        with self.assertRaisesRegex(ValueError, 'alternate target mode'):
            motion.prepare_comparison_skills({}, lambda rel: game[rel], [sid], [])

    def test_same_battle_grants_generate_separate_timelines_and_keep_hit_color_cleanup(self):
        game = fixture(); before = copy.deepcopy(game); tables = {}; clones = []; jobs = []
        ids = [sid for pair in motion.COMPARISON_SKILLS.items() for sid in (pair[0], pair[1][0])]
        unit = {'id': 13501, 'awakening': [[['ActiveSkill', sid] for sid in ids]], 'synchro': [], 'skills': {}}
        native = mock.Mock()
        native.protected_reactions = set()
        native.visual_policy = {str(original): {'donor': 210010} for original, _ in motion.COMPARISON_SKILLS.values()}
        native.target_effects.side_effect = lambda sid: {'donor': 210010, 'donorName': 'Cure', 'rule': 'test', 'tier': 1,
            'reactionRow': None, 'imports': [], 'events': [{'time': 0.2, 'set': {'EventType': 'EffectSpawnNiagaraAtTarget'}}]}
        native.reuse.return_value = (None, 'Original has no native sequence.')
        with tempfile.TemporaryDirectory() as temp, mock.patch.dict('sys.modules', {'ffbe_resonance': resonance}), \
                mock.patch.object(motion, 'NativeAnimations', return_value=native):
            source = Path(temp) / 'extracted/legacy' / (resonance.SHELL + '.uasset')
            source.parent.mkdir(parents=True); source.write_bytes(b'timeline presence fixture')
            motion.prepare_sequences(tables, clones, jobs, [unit, copy.deepcopy(unit)], temp,
                                     lambda rel: copy.deepcopy(game[rel]), mock.Mock(), native_support={'test': True})
            self.assertEqual(len(tables['Skill/DT_SkillData']['add']), 4)
            self.assertEqual(len(jobs), 8)
            for sid, (original, _) in motion.COMPARISON_SKILLS.items():
                copy_job = next(j for j in jobs if f'/Skill/{sid}/' in j['asset'])
                updated_job = next(j for j in jobs if f'/Skill/{original}/' in j['asset'])
                self.assertEqual(copy_job['kind'], 'skill_motion'); self.assertEqual(updated_job['kind'], 'skill_effect')
                self.assertFalse(any(e['set']['EventType'].startswith('EffectSpawn') for e in copy_job['plan']['events']))
                hits = [e['set'] for e in copy_job['plan']['events'] if e['set']['EventType'] == 'OtherReaction']
                self.assertEqual(len(hits), 2 if original == 505580 else 1)
                self.assertTrue(all(e['Other_Reaction_Id'] == sid and e['Otber_Reaction_bChangeColor'] for e in hits))
        self.assertEqual(game, before); self.assertEqual(unit['skills'], {})


if __name__ == '__main__': unittest.main()
