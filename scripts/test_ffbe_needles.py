"""Source-backed visual isolation, mechanics, placement and cleanup contracts."""
import copy
import hashlib
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock

from test_existing_visions import ROOT, module
import _ffr_ffbe_needles as needles
import _ffr_testing as testing
from build_ffbe_needles import compose


class FfbeNeedlesTests(unittest.TestCase):
    def fixture(self, root):
        config = Path(root) / testing.CONFIG
        config.parent.mkdir(parents=True)
        config.write_text(json.dumps({'schema': 1, 'maxMr': False, 'ffbeNeedles': True}))
        shell = 'FFRS/Content/Sequencer/Battle/Skill/440110/440111/Track/SEQ_Battle_440111_Cut_000'
        path = Path(root) / 'extracted/legacy' / (shell + '.uasset')
        path.parent.mkdir(parents=True); path.write_bytes(b'explicit file-presence fixture')
        data = {'Skill/DT_SkillData': {'Needles': {'ID': 500270, 'skillAttrType': 'Ability',
            'DamageType': 'Physic', 'damageCalcType': 'Fixed', 'TargetType': 'Single',
            'defaultTargetRelation': 'Enemies', 'hitCount': 1, 'magnification': 1000,
            'Cost': 0, 'playSequencerId': -1}}}
        for rel in needles.RELS:
            data[rel] = {'template': {'ID': 440111, 'LevelSequence': '/Game/original', 'soundSequence': '/Game/audio'}}
        return data, lambda rel: copy.deepcopy(data[rel]), SimpleNamespace(SHELL=shell)

    def test_disabled_has_no_asset_or_table_dependencies(self):
        with tempfile.TemporaryDirectory() as root:
            self.assertFalse(testing.settings(root)['ffbeNeedles'])
            tables = {}; clones = []; jobs = []
            needles.prepare(tables, clones, jobs, root, mock.Mock(side_effect=AssertionError), mock.Mock())
            self.assertEqual((tables, clones, jobs), ({}, [], []))

    def test_original_source_checksums_composition_and_hidden_tail(self):
        source = ROOT/'scripts/fixtures/ffbe_needles'
        proof = json.loads((source/'provenance.json').read_bytes())
        for name, digest in proof['files'].items():
            self.assertEqual(hashlib.sha256((source/name).read_bytes()).hexdigest(), digest)
        rows = json.loads((source/'source-rows.json').read_bytes())
        single = {'frames': [[{'pos': [3, 5]}] for _ in range(20)], 'pixelsPerUnit': 2.4}
        result = compose(single, rows)
        self.assertEqual(result['frameCount'], 60)
        self.assertEqual(sum(map(len, result['frames'])), 220)
        self.assertEqual(result['frames'][0][0]['pos'], [3, -91])
        self.assertEqual(result['frames'][4][1]['pos'], [3, 5])
        self.assertEqual(single['frames'][0][0]['pos'], [3, 5])
        files, manifest = needles.payload()
        spec = json.loads(files['spec.json'])
        self.assertEqual(manifest['source'], proof)
        self.assertEqual(manifest['conversion']['sourceSpriteFrames'], 1760)
        self.assertEqual(manifest['conversion']['droppedSpriteFrames'], 0)
        self.assertEqual(manifest['conversion']['shrunkSpriteFrames'], 0)
        anim = spec['animations'][0]
        self.assertEqual(anim['frameCount'], 270)
        self.assertTrue(all(p['Hide'][-1][1] == 1 for n, p in anim['parts'].items() if n != 'root'))

    def test_only_adds_private_bindings_without_editing_mechanics_or_existing_rows(self):
        with tempfile.TemporaryDirectory() as root:
            data, rows, seq = self.fixture(root); before = copy.deepcopy(data)
            tables = {}; clones = []; jobs = []
            with mock.patch.dict('sys.modules', {'ffbe_resonance': seq}):
                needles.prepare(tables, clones, jobs, root, rows, mock.Mock())
            self.assertEqual(set(tables), set(needles.RELS))
            for table in tables.values():
                self.assertEqual(table['set'], [])
                self.assertEqual([r['set']['ID'] for r in table['add']], [500271, 500272])
                self.assertTrue(all(r['set']['soundSequence'] == 'None' for r in table['add']))
            self.assertEqual(data, before)
            self.assertEqual(clones[0]['from'], seq.SHELL)
            self.assertEqual(jobs[0]['asset'], needles.ASSET)
            events = jobs[0]['plan']['events']
            hits = [e for e in events if e['set']['EventType'] == 'OtherReaction']
            self.assertEqual(len(hits), 1)
            self.assertEqual(hits[0]['time'], 92*400)
            self.assertEqual(hits[0]['set']['Other_Reaction_Id'], -1)
            spawn = next(e for e in events if e['set']['EventType'] == 'SsActorSpawnSpriteStudioActor')
            self.assertTrue(spawn['set']['SsActor_SsData']['bSpawnRelativeTarget'])
            move = next(e for e in events if e['set']['EventType'] == 'SsActorMoveToTargetToSsID')
            self.assertEqual(move['set']['SsActor_MoveToTarget_targetPointID'], -1)
            destroy = next(e for e in events if e['set']['EventType'] == 'SsActorDestroyToSsID')
            self.assertGreater(destroy['time'], spawn['time'] + 60*400)
            self.assertLess(destroy['time'], jobs[0]['plan']['duration'])
            self.assertFalse(any(e['set']['EventType'].startswith(('Camera', 'Post', 'OtherSetGameSpeed')) for e in events))

    def test_changed_native_definition_and_future_binding_fail_before_staging(self):
        for changed in ('definition', 'pointer', 'parent', 'composite'):
            with self.subTest(changed=changed), tempfile.TemporaryDirectory() as root:
                data, rows, seq = self.fixture(root)
                if changed == 'definition': data['Skill/DT_SkillData']['Needles']['hitCount'] = 2
                elif changed == 'pointer': data['Skill/DT_SkillData']['Needles']['playSequencerId'] = 999
                else: data[needles.RELS[changed == 'composite']]['future'] = {'ID': 500271}
                tables = {}; clones = []; jobs = []
                with mock.patch.dict('sys.modules', {'ffbe_resonance': seq}), self.assertRaises(ValueError):
                    needles.prepare(tables, clones, jobs, root, rows, mock.Mock())
                self.assertEqual((tables, clones, jobs), ({}, [], []))

    def test_needles_flag_requires_a_boolean(self):
        for bad in ('true', 1, None):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                testing.validate_settings({'schema': 1, 'maxMr': False, 'ffbeNeedles': bad})


if __name__ == '__main__': unittest.main()
