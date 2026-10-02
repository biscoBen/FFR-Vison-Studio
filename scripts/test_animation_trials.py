"""Visible Steal routing and FFBE Barrage sprite/timeline integration."""
import copy
import json
from pathlib import Path
import shutil
import subprocess
import sys
import unittest

from PIL import Image
import test_animation_profiles as profiles
from test_animation_and_library import motion, ROOT, PAYLOAD


class AnimationTrialTests(unittest.TestCase):
    def setUp(self):
        self.case = profiles.AnimationProfileTests(); self.case.setUp()
        self.root = self.case.root; self.unit = self.case.unit
        self.unit.update(id=13510, en='A2', ffbe={'dir': 'sprites', 'id': '401001207'})
        self.steal = {'ID': 400260, 'Name': 'Steal', 'hasUnit': 'All', 'skillAttrType': 'Ability',
                     'DamageType': 'None', 'TargetType': 'Single', 'defaultTargetRelation': 'Enemies',
                     'hitCount': 1, 'magnification': 12, 'effectBundleList': [{'effectId': 1030}]}
        self.barrage = {**copy.deepcopy(self.steal), 'ID': 400300, 'Name': 'Barrage',
                        'DamageType': 'Physic', 'TargetType': 'Random', 'hitCount': 4,
                        'magnification': 32, 'Cost': 20, 'accuracy': 100, 'breakDamageValue': 35,
                        'hitDamageRatioList': [.25] * 4, 'effectBundleList': [{'effectId': 1253}]}
        self.case.game['Skill/DT_SkillData'].update(steal=self.steal, barrage=self.barrage)
        self.attack = self.root / 'sprites/unit_atk_cgs_401001207.csv'
        self.attack.write_text('0,0,0,20\n1,0,0,39\n2,0,0,31\n')

    def tearDown(self): self.case.tearDown()

    def rows(self, rel): return copy.deepcopy(self.case.game[rel])

    def prepare(self, owners=None):
        self.unit['awakening'] = [[['ActiveSkill', 400300]]]
        return motion.prepare_barrage_trial(owners or [self.unit], self.root, self.rows)

    def test_steal_approaches_resolves_once_and_returns_without_changing_mechanics(self):
        before = copy.deepcopy(self.case.game)
        self.assertEqual(self.case.repair([400260]), [400260])
        plan = self.case.jobs[0]['plan']
        reactions = [e for e in plan['events'] if e['set']['EventType'] == 'OtherReaction']
        self.assertEqual(len(reactions), 1)
        self.assertEqual(reactions[0]['set']['Other_Reaction_Id'], 400260)
        self.assertTrue(reactions[0]['set']['Otber_Reaction_bChangeColor'])
        approach, = [e for e in plan['events'] if e['set']['EventType'] == 'UnitMoveToTarget']
        returning, = [e for e in plan['events'] if e['set']['EventType'] == 'UnitMoveToDefaultLocation']
        self.assertLess(approach['time'] + 12 * 400, reactions[0]['time'])
        self.assertGreater(returning['time'], reactions[0]['time'])
        self.assertGreater(plan['duration'], returning['time'] + 12 * 400)
        names = {e['set'].get('Unit_PlayAnimByName_AnimationName') for e in plan['events']}
        self.assertTrue({'command', 'idle'} <= names)
        self.assertFalse({'LB1', 'magic_attack', 'attack_A'} & names)
        self.assertEqual(self.case.game, before)
        self.assertNotIn('Skill/DT_SkillData', self.case.tables)
        self.assertNotIn('Skill/DT_SkillEffectData', self.case.tables)
        self.assertEqual(self.case.report()['skills'][0]['status'], 'ffr_steal_motion_trial')
        self.assertFalse(self.case.report()['inGameValidated'])

    def test_steal_rejects_multiple_resolution_hits(self):
        self.steal['hitCount'] = 2
        with self.assertRaisesRegex(ValueError, 'original item-stealing'): self.case.repair([400260])

    def test_changed_steal_definition_is_not_silently_treated_as_original(self):
        self.steal['effectBundleList'] = [{'effectId': 1072}]
        with self.assertRaisesRegex(ValueError, 'original item-stealing'): self.case.repair([400260])

    def test_existing_sequences_and_custom_recipes_keep_precedence(self):
        self.case.game['Asset/Skill/DT_SkillAsset']['originalSteal'] = {'ID': 400261}
        self.case.repair([400260]); self.assertEqual(self.case.jobs, [])
        self.case.game['Asset/Skill/DT_SkillAsset'].pop('originalSteal')
        self.unit['skills'] = {'400260': {'from': 400260}}
        self.case.repair([400260]); self.assertEqual(len(self.case.jobs), 1)
        self.assertEqual(self.case.report()['skills'][0]['status'], 'motion_fallback')

    def test_barrage_has_four_matching_impacts_and_complete_cleanup(self):
        config = self.prepare(); before = copy.deepcopy(self.case.game)
        self.case.repair([400300]); plan = self.case.jobs[0]['plan']
        reactions = [e for e in plan['events'] if e['set']['EventType'] == 'OtherReaction']
        self.assertEqual(len(reactions), 4)
        self.assertEqual([e['time'] for e in reactions],
                         [12000 + (i * config['cycleFrames'] + config['impactFrame']) * 400 for i in range(4)])
        self.assertTrue(all(e['set']['Other_Reaction_Id'] == 400300 and e['set']['Otber_Reaction_bChangeColor'] for e in reactions))
        names = [e['set'].get('Unit_PlayAnimByName_AnimationName') for e in plan['events']]
        self.assertIn('FFBE_Barrage', names); self.assertIn('command', names); self.assertIn('idle', names)
        returns = [e for e in plan['events'] if e['set']['EventType'] == 'UnitMoveToDefaultLocation']
        self.assertEqual(len(returns), 1); self.assertGreater(returns[0]['time'], reactions[-1]['time'])
        self.assertGreater(plan['duration'], returns[0]['time'] + 9600)
        self.assertEqual(self.case.game, before)
        self.assertNotIn('Skill/DT_SkillData', self.case.tables)
        self.assertNotIn('Skill/DT_SkillEffectData', self.case.tables)

    def test_different_owner_motions_align_impacts_without_dropping_poses(self):
        other = copy.deepcopy(self.unit); other.update(id=13511, ffbe={'dir': 'sprites', 'id': '401001205'})
        other['awakening'] = [[['ActiveSkill', 400300]]]
        (self.root / 'sprites/unit_atk_cgs_401001205.csv').write_text('0,0,0,60\n1,0,0,50\n')
        config = self.prepare([self.unit, other])
        source = {'animations': [{'name': 'attack_A', 'fps': 60, 'frameCount': 90,
                                 'parts': {'part_0': {'Cell': [[0, 'A2_0'], [20, 'A2_1'], [59, 'A2_2']]}}}]}
        before = copy.deepcopy(source['animations'][0])
        motion.add_barrage_animation(source, config, 13510)
        trial = source['animations'][-1]; cells = trial['parts']['part_0']['Cell']
        self.assertEqual(source['animations'][0], before)
        self.assertEqual(len(cells), 12); self.assertEqual(trial['frameCount'], 4 * config['cycleFrames'])
        self.assertEqual([t for t, cell in cells if cell == 'A2_2'],
                         [i * config['cycleFrames'] + config['impactFrame'] for i in range(4)])
        self.assertEqual({cell for _, cell in cells}, {'A2_0', 'A2_1', 'A2_2'})

    def test_missing_attack_inputs_fail_without_replacing_cached_data(self):
        self.prepare(); path = self.root / 'build/barrage-trial.json'; before = path.read_bytes()
        self.attack.unlink()
        with self.assertRaisesRegex(ValueError, 'needs FFBE attack sprites'): self.prepare()
        self.assertEqual(path.read_bytes(), before)

    def test_changed_hit_count_or_missing_source_timing_does_not_fake_import(self):
        self.barrage['hitCount'] = 5
        with self.assertRaisesRegex(ValueError, 'original four-hit'): self.prepare()
        self.barrage['hitCount'] = 4; self.attack.write_text('0,0,0,5\n')
        with self.assertRaisesRegex(ValueError, 'timing is unavailable or incompatible'): self.prepare()

    def test_no_selection_clears_stale_trial_and_existing_barrage_is_untouched(self):
        self.prepare(); self.unit['awakening'] = [[]]
        self.assertEqual(motion.prepare_barrage_trial([self.unit], self.root, self.rows)['owners'], {})
        self.case.game['Asset/Skill/DT_SkillAsset']['existingBarrage'] = {'ID': 400301}
        self.unit.pop('ffbe'); self.assertEqual(self.prepare()['owners'], {})
        self.case.repair([400300]); self.assertEqual(self.case.jobs, [])

    def test_real_converter_imports_recipient_frames_into_barrage_animation(self):
        engine = self.root / 'engine'; tools = engine / 'tools'; frames = tools / 'ffbe2ss6'
        frames.mkdir(parents=True)
        for name in ('ffbe_frames.py', 'build_sprites.py'): shutil.copyfile(ROOT / 'scripts/fixtures/engine_motion' / name, frames / name)
        for name in ('_ffr_animation_repair.py', '_ffr_build_sprites.py'): shutil.copyfile(PAYLOAD / name, tools / name)
        sprites = engine / 'sprites'; sprites.mkdir(); shutil.copyfile(self.attack, sprites / self.attack.name)
        Image.new('RGBA', (3, 1), (255, 0, 0, 255)).save(sprites / 'unit_anime_401001207.png')
        (sprites / 'unit_cgg_401001207.csv').write_text(''.join(f'0,1,0,0,0,0,100,0,{i},0,1,1,0\n' for i in range(3)))
        (sprites / 'unit_idle_cgs_401001207.csv').write_text('0,0,0,1\n')
        self.unit['awakening'] = [[['ActiveSkill', 400300]]]
        config = motion.prepare_barrage_trial([self.unit], engine, self.rows)
        out = self.root / 'converted'
        result = subprocess.run([sys.executable, str(tools / '_ffr_build_sprites.py'), str(sprites), '401001207', '13510', str(out)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        spec = json.loads((out / 'battle/spec.json').read_bytes())
        animation = next(a for a in spec['animations'] if a['name'] == 'FFBE_Barrage')
        self.assertEqual(animation['frameCount'], 4 * config['cycleFrames'])
        self.assertEqual({cell for _, cell in animation['parts']['part_0']['Cell']}, {'summon13510_0', 'summon13510_1', 'summon13510_2'})
        self.assertFalse(any(a['name'] == 'FFBE_Barrage' for a in json.loads((out / 'menu/spec.json').read_bytes())['animations']))


if __name__ == '__main__': unittest.main()
