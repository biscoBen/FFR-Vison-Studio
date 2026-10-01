"""Visual-only profile regressions with explicit synthetic game packages."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from test_animation_and_library import motion, resonance


class AnimationProfileTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.game = {rel: {} for rel in ('Skill/DT_SkillData', 'Skill/DT_SkillEffectData',
                     'Asset/Skill/DT_SkillAsset', 'Asset/Skill/CDT_SkillAsset_Demo',
                     'Battle/Sequencer/DT_BtlHitEffectData')}
        self.events = {}; self.imports = {}; self.cloned = []
        self.unit = {'awakening': [[]], 'synchro': [], 'skills': {},
                     'ffbe': {'dir': 'sprites', 'id': '123'}}
        (self.root / 'sprites').mkdir()
        (self.root / 'sprites/unit_atk_cgs_123.csv').write_text('0,0,0,120\n')
        (self.root / 'sprites/unit_magicatk_cgs_123.csv').write_text('0,0,0,90\n')
        for sid, profile in motion.ANIMATION_PROFILES.items():
            attr, damage, element, target, relation, hits = profile['expected']
            skill = {'ID': sid, 'Name': profile['name'], 'hasUnit': 'All', 'skillAttrType': attr,
                     'DamageType': damage, 'element': element, 'TargetType': target,
                     'defaultTargetRelation': relation, 'defaultTargetState': 'Dead' if sid == 210150 else 'Alive',
                     'hitCount': hits, 'hitDamageRatioList': [0.33, 0.33, 0.34] if hits == 3 else [1.0],
                     'magnification': 55, 'effectBundleList': [{'effectId': sid}], 'Cost': 75}
            self.game['Skill/DT_SkillData'][str(sid)] = skill
            donor = {**copy.deepcopy(skill), 'ID': profile['donor'], 'Name': profile['donorName'],
                     'skillAttrType': 'Magic' if sid != 400310 else 'Ability',
                     'DamageType': 'Magic' if sid != 400310 else 'Physic', 'magnification': 17,
                     'effectBundleList': [{'effectId': profile['donor']}]}
            self.game['Skill/DT_SkillData'][str(donor['ID'])] = donor
            self.game['Skill/DT_SkillEffectData'][str(sid)] = {'ID': sid, 'EffectType': 'Revival' if sid == 210150 else 'DmgMulConsecutiveUse', 'ParamList': [100]}
            self.game['Skill/DT_SkillEffectData'][str(donor['ID'])] = {'ID': donor['ID'], 'EffectType': 'Revival', 'ParamList': [25]}
            source_id = 400311 if sid == 400310 else donor['ID'] + 1
            folder = f'Sequencer/Battle/Skill/{donor["ID"]}/{source_id}'
            asset = {'ID': donor['ID'] if sid == 400310 else donor['ID'] + 1,
                     'LevelSequence': f'/Game/{folder}/SEQ_Battle_{source_id}_Master', 'soundSequence': '/Game/FixtureSound'}
            for rel in ('Asset/Skill/DT_SkillAsset', 'Asset/Skill/CDT_SkillAsset_Demo'):
                self.game[rel][str(donor['ID'])] = copy.deepcopy(asset)
                self.game[rel]['shell'] = {'ID': 440111}
            # Embedded reactions can belong to the original timeline rather
            # than the catalog donor. Keep the receiving skill's own hit row.
            reaction_id = sid if sid == 400310 else donor['ID']
            self.game['Battle/Sequencer/DT_BtlHitEffectData'][str(reaction_id)] = {'ID': reaction_id, 'NormalEffectID': 123}
            self.game['Battle/Sequencer/DT_BtlHitEffectData'][str(sid)] = {'ID': sid, 'NormalEffectID': 456}
            path = self.root / 'extracted/legacy/FFRS/Content' / folder / f'SEQ_Battle_{source_id}_Master.uasset'
            path.parent.mkdir(parents=True); path.write_bytes(b'Synthetic package presence fixture')
            events = [(0, 'prepare', {'EventType': 'UnitPlayAnimByName', 'Unit_PlayAnimByName_AnimationName': 'magic_idle'}),
                      (12000, 'release', {'EventType': 'UnitPlayAnimByName', 'Unit_PlayAnimByName_AnimationName': 'magic_attack'}),
                      (14000, 'particle', {'EventType': 'EffectSpawnNiagaraAtTarget', 'Effect_NiagaraData': {'niagaraAsset': 'import:SyntheticParticle'}}),
                      (36000, 'idle', {'EventType': 'UnitPlayAnimByName', 'Unit_PlayAnimByName_AnimationName': 'idle'})]
            for i in range(hits):
                events.append((18000 + i * 3000, f'hit{i}', {'EventType': 'OtherReaction', 'Other_Reaction_Id': reaction_id,
                               'Otber_Reaction_ReactionNum': -1}))
            self.events[str(path)] = sorted(events)
            self.imports[str(path)] = []
        self.game['Battle/Sequencer/DT_BtlHitEffectData']['generic'] = {'ID': 449999}
        shell = self.root / 'extracted/legacy' / (resonance.SHELL + '.uasset')
        shell.parent.mkdir(parents=True); shell.write_bytes(b'Synthetic fallback shell fixture')
        self.tables = {}; self.clones = []; self.jobs = []
        def dumps(path):
            return {'Imports': copy.deepcopy(self.imports[path])}, {f'{i+1}:{name}': copy.deepcopy(event)
                    for i, (_, name, event) in enumerate(self.events[path])}
        def clone(asset, source, sid, dest, mute, clones, objects, swaps, edits, bytecode):
            self.cloned.append((source, sid, dest, copy.deepcopy(edits)))
            clones.append({'from': asset['LevelSequence'], 'to': f'/Game/Fixture/{sid}/{dest}'})
            bytecode.extend(copy.deepcopy(edits['master']))
            return {'LevelSequence': f'/Game/Fixture/{sid}/SEQ_Battle_{dest}_Master', 'soundSequence': asset['soundSequence']}
        self.support = {'clone': clone, 'dumps': dumps,
                        'keys': lambda path: [(tick, e['EventType'], name) for tick, name, e in self.events[path]],
                        'objects': [], 'bytecode': []}

    def tearDown(self):
        self.temp.cleanup()

    def repair(self, ids):
        self.unit['awakening'] = [[['ActiveSkill', sid] for sid in ids]]
        with mock.patch.dict('sys.modules', {'ffbe_resonance': resonance}):
            return motion.prepare_sequences(self.tables, self.clones, self.jobs, [self.unit], self.root,
                    lambda rel: copy.deepcopy(self.game[rel]), mock.Mock(side_effect=AssertionError('Already extracted')),
                    native_support=self.support)

    def report(self):
        return json.loads((self.root / 'build/animation-repair-report.json').read_bytes())

    def test_four_profiles_keep_mechanics_targets_hit_rows_and_source_packages(self):
        before = copy.deepcopy(self.game)
        self.assertEqual(self.repair(motion.ANIMATION_PROFILES), sorted(motion.ANIMATION_PROFILES))
        self.assertEqual(self.jobs, [])
        self.assertEqual(self.game, before)
        self.assertNotIn('Skill/DT_SkillData', self.tables)
        self.assertNotIn('Skill/DT_SkillEffectData', self.tables)
        self.assertNotIn('Battle/Sequencer/DT_BtlHitEffectData', self.tables)
        self.assertEqual({r['status'] for r in self.report()['skills']}, {'animation_profile'})
        self.assertFalse(self.report()['inGameValidated'])
        for rel, spec in self.tables.items():
            self.assertEqual(spec['set'], [])
            self.assertEqual({r['set']['ID'] for r in spec['add']},
                             {sid + off for sid in motion.ANIMATION_PROFILES for off in (1, 2)})
        for source, sid, destination, edits in self.cloned:
            self.assertNotEqual(source, destination)
            self.assertEqual(destination, 800000000 + sid + 1)
            reaction, prepare, release = edits['master']
            self.assertEqual(reaction['set'], {'Other_Reaction_Id': sid})
            self.assertEqual(prepare['set']['Unit_PlayAnimByName_AnimationName'], motion.ANIMATION_PROFILES[sid]['prepare'])
            self.assertEqual(release['set']['Unit_PlayAnimByName_AnimationName'], motion.ANIMATION_PROFILES[sid]['release'])
            self.assertEqual(release['set']['Unit_PlayAnimByName_InPlayRate'], 1.5 if sid == 210150 else 2.0)
            self.assertFalse(any(e['match'].get('EventType') == 'EffectSpawnNiagaraAtTarget' for e in edits['master']))
        count = len(self.cloned)
        self.assertEqual(self.repair(motion.ANIMATION_PROFILES), [])
        self.assertEqual(len(self.cloned), count)

    def test_aquatic_keeps_three_hits_and_arise_keeps_full_revival(self):
        self.repair([414410, 210150])
        self.assertEqual(self.game['Skill/DT_SkillData']['414410']['hitCount'], 3)
        self.assertEqual(self.game['Skill/DT_SkillData']['414410']['hitDamageRatioList'], [0.33, 0.33, 0.34])
        self.assertEqual(self.game['Skill/DT_SkillData']['210150']['defaultTargetState'], 'Dead')
        self.assertEqual(self.game['Skill/DT_SkillEffectData']['210150']['ParamList'], [100])

    def test_existing_sequence_and_explicit_custom_recipe_take_precedence(self):
        self.game['Asset/Skill/DT_SkillAsset']['existing'] = {'ID': 400312, 'LevelSequence': '/Game/Existing'}
        self.unit['skills']['420130'] = {'from': 420130, 'set': {'magnification': 23}}
        self.repair([400310, 420130])
        self.assertEqual(self.cloned, [])
        self.assertEqual(self.report()['skills'][0]['status'], 'existing_sequence')
        self.assertNotIn('profileReason', self.report()['skills'][1])

    def test_incompatible_donor_targets_or_hit_count_do_not_clone(self):
        for field, value in [('TargetType', 'Group'), ('hitCount', 2), ('defaultTargetRelation', 'Friendlies')]:
            with self.subTest(field=field):
                donor = self.game['Skill/DT_SkillData']['220170']; previous = donor[field]; donor[field] = value
                native = motion.NativeAnimations(lambda rel: copy.deepcopy(self.game[rel]), self.root, mock.Mock(), self.support)
                result, reason = native.profile(420130, self.game['Skill/DT_SkillData']['420130'], [self.unit], {}, [])
                self.assertIsNone(result); self.assertIn('incompatible', reason); donor[field] = previous
        self.assertEqual(self.cloned, [])

    def test_missing_recovery_or_unbalanced_movement_reports_a_fallback(self):
        path = next(p for p in self.events if '/220170/' in p)
        self.events[path] = [e for e in self.events[path] if e[1] != 'idle']
        self.repair([420130])
        self.assertEqual(self.cloned, [])
        self.assertEqual(self.report()['skills'][0]['status'], 'motion_fallback')
        self.assertIn('recovery', self.report()['skills'][0]['profileReason'])

    def test_owner_actor_and_voice_are_rejected(self):
        path = next(p for p in self.events if '/220170/' in p)
        native = motion.NativeAnimations(lambda rel: copy.deepcopy(self.game[rel]), self.root, mock.Mock(), self.support)
        self.imports[path] = [{'ObjectName': '/Game/Chara/monster/FixtureMonster'}]
        result, reason = native.profile(420130, self.game['Skill/DT_SkillData']['420130'], [self.unit], {}, [])
        self.assertIsNone(result); self.assertIn('owner-specific', reason)
        self.imports[path] = []
        self.events[path].append((20000, 'voice', {'EventType': 'SoundPlayHitSound', 'Sound_PlayHitSound_playLabel': 'VO_BTL_OWNER_01'}))
        result, reason = native.profile(420130, self.game['Skill/DT_SkillData']['420130'], [self.unit], {}, [])
        self.assertIsNone(result); self.assertIn('voice', reason)

    def test_missing_or_disagreeing_secondary_binding_reports_a_fallback(self):
        self.game['Asset/Skill/CDT_SkillAsset_Demo']['220170']['LevelSequence'] = '/Game/Different'
        self.repair([420130])
        self.assertEqual(self.cloned, [])
        self.assertIn('disagree', self.report()['skills'][0]['profileReason'])

    def test_private_sequence_collision_and_changed_recipient_do_not_clone(self):
        self.game['Asset/Skill/DT_SkillAsset']['collision'] = {'ID': 99, 'LevelSequence': '/Game/Fixture/SEQ_Battle_800420131_Master'}
        self.repair([420130]); self.assertEqual(self.cloned, [])
        self.assertIn('already in use', self.report()['skills'][0]['profileReason'])


if __name__ == '__main__':
    unittest.main()
