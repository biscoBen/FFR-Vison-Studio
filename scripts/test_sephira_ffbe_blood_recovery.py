"""The approved FFBE import is scoped to Snow White, with one native heal."""
import copy
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock

from test_existing_visions import ROOT
import _ffr_sephira_ffbe as blood
import _ffr_sephira as pack


def unit():
    catalog = json.loads((ROOT / 'assets/sephira_visions/catalog.json').read_bytes())
    profile = next(p['profile'] for p in catalog['presets'] if p['id'] == 'snow_white')
    return dict(copy.deepcopy(profile), sephiraVision={'version': 1, 'preset': 'snow_white', 'enabled': True})


class BloodRecoveryTests(unittest.TestCase):
    def test_selected_source_frames_sound_and_three_separate_layers(self):
        files, manifest = blood.payload()
        self.assertEqual((manifest['owner'], manifest['ability']), ('Scartio', 231688))
        self.assertEqual([layer['role'] for layer in manifest['layers']], ['back', 'front', 'flash'])
        self.assertEqual([layer['start'] for layer in manifest['layers']], [40, 40, 100])
        self.assertEqual(sum(layer['conversion']['sourceSpriteFrames'] for layer in manifest['layers']), 3037)
        for layer in manifest['layers']:
            self.assertEqual(layer['conversion']['droppedSpriteFrames'], 0)
            self.assertEqual(layer['conversion']['shrunkSpriteFrames'], 0)
            spec = json.loads(files[layer['role'] + '/spec.json'])
            self.assertTrue(all(part['Hide'][-1][1] == 1 for name, part in spec['animations'][0]['parts'].items() if name != 'root'))
        audio = json.loads(files['audio.json'])
        self.assertEqual(audio['recordings'][0]['sourceCueId'], 25)
        events = blood.schedule()['events']
        self.assertEqual([e['time'] for e in events if e['set']['EventType'] == 'SoundPlayHitSound'], [41*400, 41*400])
        hits = [e for e in events if e['set']['EventType'] == 'OtherReaction']
        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0]['time'], 100 * 400)
        self.assertEqual(hits[0]['set']['Other_Reaction_Id'], -1)
        self.assertEqual(len([e for e in events if e['set']['EventType'] == 'SsActorDestroyToSsID']), 3)
        self.assertFalse(any(e['set']['EventType'].startswith(('Camera', 'Post', 'OtherSetGameSpeed')) for e in events))

    def test_scope_and_explicit_user_presentations(self):
        original = unit(); recipe = next(r for r in original['skills'].values() if r['from'] == 501530)
        self.assertTrue(blood.selected(original, recipe))
        for field, value in [('visuals', 220010), ('motion', 'attack_A'), ('clone_sequence', 210021), ('tint', '#FF0000')]:
            changed = {**recipe, field: value}
            self.assertFalse(blood.selected(original, changed))
        changed = copy.deepcopy(recipe); changed['set']['playSequencerId'] = 210021
        self.assertFalse(blood.selected(original, changed))
        for owner in ({k: v for k, v in original.items() if k != 'sephiraVision'},
                      {**original, 'sephiraVision': {'version': 1, 'preset': 'a2', 'enabled': True}}):
            self.assertFalse(blood.selected(owner, recipe))

    def fixture(self, root):
        source = json.loads((ROOT / 'scripts/fixtures/blood_recovery_native.json').read_bytes())
        game = {'Skill/DT_SkillData': {'Native blood recovery': source},
                **{rel: {'Original shell': {'ID': 440111}} for rel in blood.shared.RELS}}
        shell = 'FFRS/Content/Sequencer/Battle/Skill/440110/440111/Track/SEQ_Battle_440111_Cut_000'
        path = Path(root) / 'extracted/legacy' / (shell + '.uasset')
        path.parent.mkdir(parents=True); path.write_bytes(b'explicit file presence fixture')
        return game, SimpleNamespace(SHELL=shell)

    def test_private_player_and_enemy_routes_leave_gameplay_and_original_rows_unchanged(self):
        with tempfile.TemporaryDirectory() as root:
            game, shell = self.fixture(root); original = unit()
            before = copy.deepcopy((game, original)); tables = {}; clones = []; jobs = []
            with mock.patch.dict('sys.modules', {'ffbe_resonance': shell}), mock.patch.object(blood.shared, 'prepare_audio', return_value={'fixture': 'audio'}):
                blood.prepare(tables, clones, jobs, [original], root, game.__getitem__, mock.Mock())
            sid = next(int(k) for k, r in original['skills'].items() if r['from'] == 501530)
            self.assertEqual(set(tables), set(blood.shared.RELS))
            for table in tables.values():
                self.assertEqual(table['set'], [])
                self.assertEqual([r['set']['ID'] for r in table['add']], [sid + 1, sid + 2])
            self.assertEqual((game, original), before)
            self.assertEqual(len(clones), 1)
            self.assertEqual(jobs[0]['asset'], blood.ASSET)

    def test_changed_definition_fails_before_staging_and_unselected_needs_no_files(self):
        blood.prepare({}, [], [], [], None, mock.Mock(side_effect=AssertionError), mock.Mock())
        with tempfile.TemporaryDirectory() as root:
            game, shell = self.fixture(root); game['Skill/DT_SkillData']['Native blood recovery']['magnification'] += 1
            tables = {}; clones = []; jobs = []
            with mock.patch.dict('sys.modules', {'ffbe_resonance': shell}), self.assertRaisesRegex(ValueError, 'definition changed'):
                blood.prepare(tables, clones, jobs, [unit()], root, game.__getitem__, mock.Mock())
            self.assertEqual((tables, clones, jobs), ({}, [], []))

    def test_borrowed_mode_cannot_replace_the_approved_import_or_change_saved_gameplay(self):
        source = json.loads((ROOT / 'scripts/fixtures/blood_recovery_native.json').read_bytes())
        for visual in (501530, 210020):
            original = unit(); sid, recipe = next((k, r) for k, r in original['skills'].items() if r['from'] == 501530)
            original['skills'] = {sid: recipe}; recipe['visuals'] = visual
            before = copy.deepcopy(original)
            actual, = pack.player_units([original], lambda rel: {'Native': source})
            self.assertEqual(actual['skills'][sid]['visuals'], 501530)
            for field in ('Cost', 'magnification', 'hitCount', 'TargetType', 'defaultTargetRelation'):
                self.assertEqual(actual['skills'][sid]['set'].get(field), recipe['set'].get(field))
            self.assertEqual(original, before)


if __name__ == '__main__': unittest.main()
