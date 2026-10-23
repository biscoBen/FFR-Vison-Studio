"""Source-backed LB audio, scoped migration and the real builder hook."""
import ast
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock

from test_existing_visions import ROOT, installer, fina_installer, module

audio = module('sephira_lb_audio', ROOT / 'assets/existing_visions/payload/_ffr_sephira_lb_audio.py')


def units():
    return [dict(copy.deepcopy(p['profile']), sephiraVision={'version': 1, 'preset': p['id'], 'enabled': True})
            for p in json.loads((ROOT / 'assets/sephira_visions/catalog.json').read_bytes())['presets']]


class LbAudioTests(unittest.TestCase):
    def test_original_cues_cover_all_30_without_inventing_missing_soundtracks(self):
        metadata, files = audio.payload()
        self.assertEqual(len(metadata['profiles']), 30)
        self.assertEqual(sum(p['status'] == 'original_cues' for p in metadata['profiles'].values()), 23)
        self.assertEqual({k for k, p in metadata['profiles'].items() if p['status'] == 'opening_only'},
                         {'christine', 'crystal_fina', 'barusa', 'fryevia', 'lilith', 'ariana', 'elza'})
        se = json.loads(files['audio/SE.json']); system = json.loads(files['audio/System.json'])
        self.assertEqual(len(se['cues']), 55)
        self.assertEqual(system['cues']['45']['name'], 'se_battle_limitopen_1')
        self.assertEqual([r['variation'] for r in se['recordings'] if r['sourceCueId'] == 355], [0, 1, 2])
        for rec in se['recordings'] + system['recordings']:
            bank = se if rec in se['recordings'] else system
            raw = files['audio/samples/' + bank['waves'][str(rec['sourceWaveId'])]['sha256'] + '.hca']
            self.assertEqual(raw[:6], b'HCA\0\x02\0')
            self.assertEqual(raw[34], raw[35])  # no unsupported HFR left
            self.assertEqual(raw[40:46], b'ciph\0\0')
        self.assertEqual(metadata['profiles']['fran']['variant'], 1)
        self.assertGreater(len(metadata['profiles']['fran']['sounds']), 0)

    def test_old_defaults_enabled_once_and_explicit_mute_or_custom_audio_preserved(self):
        for unit in units():
            skill = unit['lb_custom']
            self.assertIsNotNone(audio.selected(unit, skill))
            muted = dict(skill, audio='none')
            self.assertIsNone(audio.selected(unit, muted))
            muted.pop('sephiraAudio')
            self.assertIsNotNone(audio.selected(unit, muted))
            for field, value in [('audio_bank', 'custom.json'), ('audio_system_bank', 'custom.acb'),
                                 ('ffbe_lb_id', 'another-lb'), ('presentation', 'template'), ('audio', 'experimental')]:
                self.assertIsNone(audio.selected(unit, dict(skill, **{field: value})))
            changed = dict(unit, ffbe={'id': 'different-form'})
            self.assertIsNone(audio.selected(changed, skill))
        unit = units()[0]; unit.pop('sephiraVision')
        self.assertIsNone(audio.selected(unit, unit['lb_custom']))
        fina = next(u for u in units() if u['sephiraVision']['preset'] == 'crystal_fina')
        fina.pop('sephiraVision')
        self.assertIsNotNone(audio.selected(fina, fina['lb_custom']))

    def test_preparation_preserves_damage_data_and_never_plays_stop_instructions(self):
        unit = next(u for u in units() if u['sephiraVision']['preset'] == 'mog')
        source = {'hitFrames': [42, 84], 'hitPercents': [50, 50], 'moveType': 4, 'sounds': []}
        original = copy.deepcopy((unit, source)); table = mock.Mock(); prepared = []
        with tempfile.TemporaryDirectory() as root:
            def prepare(u, skill, data, tbl):
                prepared.append(copy.deepcopy((skill, data)))
                self.assertTrue(Path(skill['audio_bank']).is_file())
                return {'original bank': True}, data['sounds']
            module = SimpleNamespace(ROOT=root, prepare=prepare)
            with mock.patch.dict('sys.modules', {'ffbe_audio': module}):
                bank, events = audio.prepare(unit, unit['lb_custom'], source, table)
                path = Path(prepared[0][0]['audio_bank']); path.write_bytes(b'changed cache')
                audio.prepare(unit, unit['lb_custom'], source, table)
                self.assertNotEqual(path.read_bytes(), b'changed cache')
            self.assertTrue(events)
            self.assertTrue(all(s['flags'] == ['1'] for s in events))
            self.assertEqual(prepared[0][1]['hitFrames'], source['hitFrames'])
            self.assertEqual(prepared[0][1]['hitPercents'], source['hitPercents'])
            self.assertEqual(prepared[0][1]['moveType'], source['moveType'])
            self.assertEqual((unit, source), original)
            table.assert_not_called()

    def test_actual_resonance_builder_routes_only_audio_through_adapter(self):
        original = (ROOT / 'scripts/fixtures/crystal_fina/make_vision_mod.py').read_bytes()
        result = ast.parse(installer.hook_builder(fina_installer.hook_builder(original)))
        function = next(n for n in result.body if isinstance(n, ast.FunctionDef) and n.name == 'prepare_ffbe_resonance')
        calls = [ast.unparse(n.func) for n in ast.walk(function) if isinstance(n, ast.Call)]
        self.assertIn('_ffr_sephira_lb_audio.prepare', calls)
        self.assertNotIn('ffbe_audio.prepare', calls)
        self.assertIn('ffbe_lb.resolve', calls)
        self.assertIn('ffbe_resonance.schedule', calls)


if __name__ == '__main__': unittest.main()
