"""Original-source private player routes, independent of borrowed visual modes."""
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from test_existing_visions import ROOT
import _ffr_sephira_sequences as sequences
from _ffr_native_skills import digest
import _ffr_sephira as pack
from test_animation_and_library import motion


class SephiraOriginalSequenceTests(unittest.TestCase):
    def fixture(self, root):
        source = {'ID': 501510, 'playSequencerId': -1, 'sequencerIdWhenTargetFriendlies': -1}
        binding = {'ID': 501512, 'LevelSequence': '/Game/Sequencer/Battle/EnemySkill/500130/500132/SEQ_Battle_500132_Master',
                   'soundSequence': '/Game/Sequencer/Battle/EnemySkill/500130/500132/Track/SEQ_Battle_500132_Sound_001'}
        unit = {'id': 13500, 'en': 'A2', 'sephiraVision': {'version': 1, 'preset': 'a2', 'enabled': True},
                'skills': {'485003': {'from': 501510, 'visuals': 501510, 'en': 'Rend', 'set': {}}}}
        game = {'Skill/DT_SkillData': {'Rend source': source},
                **{rel: {'Enemy binding': copy.deepcopy(binding)} for rel in sequences.RELS},
                'Battle/Sequencer/DT_BtlHitEffectData': {'Actual embedded reaction': {'ID': 500130, 'native': True}}}
        rule = {'sourceBinding': 501512, 'sourceSequence': 500132,
                'folder': 'Sequencer/Battle/EnemySkill/500130/500132', 'files': {},
                'definitionSha256': digest(source), 'bindingSha256': digest(binding), 'reactionIds': [500130],
                'motionEdits': [{'file': 'Track/SEQ_Battle_500132_Cut_001.uasset', 'function': 'Play_SEQ_Battle_500132',
                                 'set': {'Unit_PlayAnimByName_AnimationName': 'attack_A'}}],
                'effectEdits': [], 'enableTracks': [{'file': 'Track/SEQ_Battle_500132_Cut_001.uasset', 'export': 'OwnMotionTrack'}], 'flags': []}
        for name in ('SEQ_Battle_500132_Master.uasset', 'SEQ_Battle_500132_Master.uexp'):
            path = root / 'extracted/legacy/FFRS/Content' / rule['folder'] / name
            path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(b'explicit source fixture')
            rule['files'][name] = hashlib.sha256(path.read_bytes()).hexdigest()
        (root / sequences.POLICY).write_text(json.dumps({'schema': 1, 'skills': {'501510': rule}}))
        table = {'Skill/DT_SkillData': {'asset': 'FFRS/Content/Datatable/Skill/DT_SkillData', 'add': [
            {'row': 'Private Rend', 'cloneFrom': 'Rend source', 'set': {'ID': 485003, 'Cost': 8, 'magnification': 19}}], 'set': []}}
        def clone(asset, src, skill, target, mute, clones, objects, swaps, edits, bytecode):
            self.assertEqual((asset, src, skill, target, mute, swaps), (binding, 500132, 485003, 485004, (), ()))
            self.assertEqual(edits['master'][0]['match']['Other_Reaction_Id'], 500130)
            self.assertEqual(edits['master'][0]['set']['Other_Reaction_Id'], 485003)
            clones.append({'from': asset['LevelSequence'], 'to': target})
            return {'LevelSequence': '/Game/Sequencer/Battle/EnemySkill/485003/485004/SEQ_Battle_485004_Master',
                    'soundSequence': '/Game/Sequencer/Battle/EnemySkill/485003/485004/Track/SEQ_Battle_485004_Sound_001'}
        support = {'clone': mock.Mock(side_effect=clone), 'objects': [], 'bytecode': []}
        return unit, game, table, support

    def test_enemy_only_alias_uses_original_packages_sound_and_embedded_impact(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); unit, game, tables, support = self.fixture(root)
            before_game, before_unit = copy.deepcopy(game), copy.deepcopy(unit)
            with mock.patch.object(sequences, '__file__', str(root / 'module.py')):
                report = sequences.prepare(tables, [], [unit], root, game.__getitem__, mock.Mock(), support)
            self.assertEqual(report[0]['status'], 'own_source_player_route')
            support['clone'].assert_called_once()
            for rel in sequences.RELS:
                row, = tables[rel]['add']
                self.assertEqual(row['cloneFrom'], 'Enemy binding')
                self.assertEqual(row['set']['ID'], 485004)
                self.assertIn('485004_Sound', row['set']['soundSequence'])
                self.assertEqual(tables[rel]['set'], [])
            impact, = tables['Battle/Sequencer/DT_BtlHitEffectData']['add']
            self.assertEqual(impact['cloneFrom'], 'Actual embedded reaction')
            self.assertEqual(impact['set']['ID'], 485003)
            self.assertTrue(any(o['export'] == 'OwnMotionTrack' and o['set']['bIsEvalDisabled'] is False
                                for o in support['objects']))
            fields = tables['Skill/DT_SkillData']['add'][0]['set']
            self.assertEqual(fields, {'ID': 485003, 'Cost': 8, 'magnification': 19, 'playSequencerId': -1})
            self.assertEqual((unit, game), (before_unit, before_game))

    def test_changed_source_bytes_stop_before_any_clone_or_table_changes(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); unit, game, tables, support = self.fixture(root); before = copy.deepcopy(tables)
            path = next((root / 'extracted').rglob('*.uexp')); path.write_bytes(b'changed source')
            with mock.patch.object(sequences, '__file__', str(root / 'module.py')):
                with self.assertRaisesRegex(ValueError, 'timeline bytes'):
                    sequences.prepare(tables, [], [unit], root, game.__getitem__, mock.Mock(), support)
            support['clone'].assert_not_called(); self.assertEqual(tables, before)

    def test_changed_direction_point_guard_stops_before_cloning(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); unit, game, tables, support = self.fixture(root)
            policy = json.loads((root / sequences.POLICY).read_bytes())
            policy['skills']['501510']['pointTargets'] = {'18': digest({'ID': 18, 'side': 'enemy'})}
            (root / sequences.POLICY).write_text(json.dumps(policy))
            game['Battle/Sequencer/DT_BtlSkillPointTargetData'] = {'point': {'ID': 18, 'side': 'party'}}
            with mock.patch.object(sequences, '__file__', str(root / 'module.py')):
                with self.assertRaisesRegex(ValueError, 'target points changed'):
                    sequences.prepare(tables, [], [unit], root, game.__getitem__, mock.Mock(), support)
            support['clone'].assert_not_called()

    def test_user_donors_untagged_units_and_authored_sequences_keep_precedence(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); unit, _, _, _ = self.fixture(root)
            untagged = copy.deepcopy(unit); untagged.pop('sephiraVision')
            borrowed = copy.deepcopy(unit); borrowed['skills']['485003']['visuals'] = 210010
            authored = copy.deepcopy(unit); authored['skills']['485003']['clone_sequence'] = True
            self.assertEqual(list(sequences.selections([untagged, borrowed, authored])), [])

    def test_all_reported_sources_have_their_own_audited_route_and_supported_caster_track(self):
        policy = json.loads((ROOT / 'assets/existing_visions/payload' / sequences.POLICY).read_bytes())
        self.assertEqual(len(policy['skills']), 313)
        bindings = {501510: 500131, 501790: 500091, 500990: 500992,
                    500210: 500061, 500480: 500481, 500190: 500192}
        for source, binding in bindings.items():
            rule = policy['skills'][str(source)]
            self.assertEqual(rule['sourceBinding'], binding)
            if not rule['nativePlayerVariant']:
                self.assertTrue(rule['enableTracks'], source)
                self.assertTrue(any(e['set'].get('Unit_PlayAnimByName_AnimationName') == 'attack_A'
                                    for e in rule['motionEdits']), source)
            self.assertFalse(rule['flags'], source)
            self.assertTrue(any(name.endswith('_Sound_001.uasset') for name in rule['files']), source)
        # Aliases have hit/effect identities different from the copied skill ID.
        self.assertEqual(policy['skills']['501510']['reactionIds'], [500130])
        self.assertEqual(policy['skills']['501790']['reactionIds'], [500090])
        aqua = policy['skills']['500800']
        self.assertEqual(aqua['sourceBinding'], 500801)
        self.assertTrue(aqua['nativePlayerVariant'])

    def test_direction_uses_paired_group_points_and_keeps_working_native_player_effects(self):
        rule = {'nativePlayerVariant': False, 'pointEvents': [
            {'file': 'Effect.uasset', 'function': 'Spawn', 'target': 2,
             'look': {'Effect_NiagaraData': 2}}]}
        native = {'defaultTargetRelation': 'Enemies'}
        fields, = [r['set'] for r in sequences.direction_edits(rule, {}, native)]
        self.assertEqual(fields, {'Effect_SpawnTarget_ID': 18, 'Effect_NiagaraData': {'LookAtTargetID': 18}})
        player = dict(rule, nativePlayerVariant=True)
        self.assertEqual(sequences.direction_edits(player, {}, native), [])
        player['pointEvents'] = [dict(rule['pointEvents'][0], target=18, look={'Effect_NiagaraData': 18})]
        fields, = [r['set'] for r in sequences.direction_edits(player, {'set': {'defaultTargetRelation': 'Friendlies'}}, native)]
        self.assertEqual(fields, {'Effect_SpawnTarget_ID': 2, 'Effect_NiagaraData': {'LookAtTargetID': 2}})

    def test_changed_original_source_family_cannot_reuse_a_previously_chosen_sibling(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); unit, game, tables, support = self.fixture(root)
            policy = json.loads((root / sequences.POLICY).read_bytes())
            policy['skills']['501510']['originBinding'] = {'ID': 501512, 'sha256': 'changed'}
            (root / sequences.POLICY).write_text(json.dumps(policy))
            with mock.patch.object(sequences, '__file__', str(root / 'module.py')):
                with self.assertRaisesRegex(ValueError, 'source no longer points'):
                    sequences.prepare(tables, [], [unit], root, game.__getitem__, mock.Mock(), support)
            support['clone'].assert_not_called()

    def test_every_preset_gets_only_its_required_native_names_from_its_own_clips(self):
        catalog = json.loads((ROOT / 'assets/sephira_visions/catalog.json').read_bytes())
        policy = json.loads((ROOT / 'assets/existing_visions/payload' / sequences.POLICY).read_bytes())
        self.assertEqual(set(policy['modelMotions']), {p['id'] for p in catalog['presets']})
        controls = {'showUnverified': True, 'useChanges': False, 'useNativeRepairs': True}
        for preset in catalog['presets']:
            unit = copy.deepcopy(preset['profile'])
            unit[pack.FIELD] = {'version': 1, 'preset': preset['id'], 'enabled': True}
            required = pack.native_motion_names(unit)
            self.assertTrue(pack.native_motion_for([unit], str(unit['id'])))
            targets = set(motion.NATIVE_MOTION_ALIASES.values())
            spec = {'animations': [{'name': n, 'frameCount': 17, 'ownCharacterMarker': preset['id']} for n in targets]}
            added = motion.native_caster_motions(spec, controls, required)
            names = {a['name'] for a in spec['animations']}
            self.assertTrue(set(required) <= names)
            self.assertTrue(all(a['ownCharacterMarker'] == preset['id'] for a in spec['animations']))
            self.assertEqual(set(added), (set(required) | {'atk'}) - targets)
            self.assertEqual(motion.native_caster_motions(spec, controls, required), [])
            unit[pack.FIELD]['enabled'] = False
            self.assertFalse(pack.native_motion_for([unit], unit['id']))


if __name__ == '__main__': unittest.main()
