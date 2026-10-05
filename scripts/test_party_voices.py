"""General authored voice substitution and isolation from mechanics/effect audio."""
import copy
import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock
from test_existing_visions import ROOT, party, module
from test_party_characters import unit

voices = module('_ffr_party_voices', ROOT / 'assets/existing_visions/payload/_ffr_party_voices.py')


def fixture(u):
    owner = u['en'].replace(' ', '')
    values = {voices.COMMANDS: {u['jp']: {'ID': u['id'], 'detailData': [{'SkillId': 987650}]}},
              voices.SKILLS: {'attack': {'ID': 987650, 'skillAttrType': 'Fight', 'hasUnit': owner},
                              'lb': {'ID': 666010, 'skillAttrType': 'LimitBurst', 'hasUnit': owner},
                              'other': {'ID': 666020, 'skillAttrType': 'LimitBurst', 'hasUnit': 'Other'}},
              'Asset/Skill/DT_SkillAsset': {}, 'Asset/Skill/CDT_SkillAsset_Demo': {}}
    for sid in (987650, 666010):
        values['Asset/Skill/DT_SkillAsset'][str(sid + 1)] = {'ID': sid + 1,
            'LevelSequence': f'/Game/Sequencer/Battle/Skill/{sid}/SEQ_Battle_{sid+1}_Master'}
    return values


def track(cues):
    imports = [{'ObjectName': 'MovieSceneAtomSection'}] + [{'ObjectName': cue} for cue, _ in cues]
    return {'Imports': imports, 'Exports': [
        {'ObjectName': f'Section{i}', 'ClassIndex': -1, 'Data': [{'Name': 'Sound', 'Value': -i-2},
          {'Name': 'SectionRange', 'Value': [{'Value': {'LowerBound': {'Value': {'Value': start}},
                                                       'UpperBound': {'Value': {'Value': start + 1000}}}}]}]}
        for i, (_, start) in enumerate(cues)]}


def template(u, name):
    bank = 'VO_BTL_' + party.voice_label(u['id'])
    return {'Imports': [{'ObjectName': 'SoundAtomCue'}, {'ObjectName': bank}], 'Exports': [
        {'ObjectName': name, 'ClassIndex': -1, 'Data': [{'Name': 'CueSheet', 'Value': -2}, {'Name': 'CueName', 'Value': name[:-4]}]}]}


class PartyVoiceTests(unittest.TestCase):
    def test_all_64_pairs_replace_fixed_sections_or_preserve_original(self):
        for target, _, _, _ in party.CHARACTERS:
            for source, _, _, _ in party.CHARACTERS:
                with self.subTest(target=target, source=source), tempfile.TemporaryDirectory() as directory:
                    u = unit(target); u.pop('ffbe'); u['battleVoice'] = source
                    data = fixture(u); before = copy.deepcopy(data); root = Path(directory)
                    old = party.voice_label(target); views = {}
                    for sid, cues in [(987650, [(f'VO_BTL_ATK_01_{old}_Cue', 200), ('SE_SWORD_Cue', 100), ('VO_BTL_ATK_01_CHR0150_Cue', 300)]),
                                      (666010, [(f'VO_BTL_{old}_666010_02_Cue', 400), ('SE_MAGIC_Cue', 300),
                                               (f'VO_BTL_{old}_081_Cue', 200), (f'VO_BTL_{old}_666010_01_Cue', 100),
                                               (f'VO_BTL_{old}_082_Cue', 700), ('VO_C01_DIALOGUE_Cue', 50)])]:
                        folder = root / f'extracted/legacy/FFRS/Content/Sequencer/Battle/Skill/{sid}'
                        (folder / 'Track').mkdir(parents=True)
                        (folder / f'SEQ_Battle_{sid+1}_Master.uasset').touch()
                        path = folder / f'Track/SEQ_Battle_{sid+1}_Sound_001.uasset'; path.touch(); views[str(path)] = track(cues)
                        for cue, _ in cues:
                            if old not in cue: continue
                            p = root / f'extracted/legacy/FFRS/Content/Sound/Cri/Voice/VO_BTL/VO_BTL_{old}/{cue}.uasset'
                            p.parent.mkdir(parents=True, exist_ok=True); p.touch(); views[str(p)] = template(u, cue)
                    objects = []; clones = []; post = []
                    forbidden = mock.Mock(side_effect=AssertionError('Cached reference extracted again'))
                    with contextlib.redirect_stdout(io.StringIO()):
                        voices.prepare(objects, clones, post, [u], root, lambda rel: copy.deepcopy(data[rel]),
                                       forbidden, lambda p: (copy.deepcopy(views[p]), {}))
                    self.assertEqual(data, before)
                    if target == source:
                        self.assertEqual((objects, clones, post), ([], [], [])); self.assertFalse((root / voices.PLAN).exists()); continue
                    self.assertEqual(objects, [])
                    sound_edits = [x for x in post if 'Sound' in x['set']]
                    cue_edits = [x for x in post if 'CueName' in x['set']]
                    self.assertEqual(len(sound_edits), 5)
                    self.assertTrue(all(x['set']['Sound'] and party.voice_label(source) in x['set']['Sound'] for x in sound_edits))
                    plan = json.loads((root / voices.PLAN).read_bytes())
                    self.assertEqual({c['export'] for c in plan['changes'] if '666010' in c['asset']}, {'Section0','Section2','Section3','Section4'})
                    for c in plan['changes']:
                        if '666010' not in c['asset']: continue
                        phase = {'Section3':'opening','Section0':'release','Section2':'attack','Section4':'finish'}[c['export']]
                        self.assertTrue(c['new'].endswith('_' + phase + '_Cue'))
                    self.assertEqual(len(clones), 6); self.assertEqual(len(cue_edits), 4)
                    self.assertEqual({c['set']['CueName'] for c in cue_edits}, {c['name'] for c in voices.profile(source).values()})

    def test_readback_rejects_other_sound_timing_and_wrong_package_changes(self):
        original = track([('VO_BTL_ATK_01_CHR0020_Cue', 100), ('SE_SWORD_Cue', 200)])
        new = '/Game/Sound/StudioPartyVoice/CHR0080/StudioPartyVoice_CHR0080_attack_Cue'
        built = copy.deepcopy(original); built['Imports'].extend([{'ObjectName': new}, {'ObjectName': new.rsplit('/',1)[1], 'OuterIndex': -4}])
        built['Exports'][0]['Data'][0]['Value'] = -5
        edits = [{'export': 'Section0','export_index':0,'old':'VO_BTL_ATK_01_CHR0020_Cue','new':new}]
        voices.check_track(original, built, edits)
        for change in ('sound', 'timing', 'package'):
            bad = copy.deepcopy(built)
            if change == 'sound': bad['Exports'][1]['Data'][0]['Value'] = -5
            if change == 'timing': bad['Exports'][0]['Data'][1]['Value'][0]['Value']['UpperBound']['Value']['Value'] += 100
            if change == 'package': bad['Imports'][-2]['ObjectName'] = '/Game/WrongPackage'
            with self.subTest(change=change), self.assertRaises(ValueError): voices.check_track(original,bad,edits)

    def test_duplicate_export_names_do_not_hide_an_effect_change(self):
        original = track([('VO_BTL_ATK_01_CHR0020_Cue', 100), ('SE_SWORD_Cue', 200)])
        original['Exports'][1]['ObjectName'] = 'Section0'
        original['Exports'][1]['OuterIndex'] = 10
        new = '/Game/Sound/StudioPartyVoice/CHR0080/StudioPartyVoice_CHR0080_attack_Cue'
        built = copy.deepcopy(original); built['Imports'].extend([{'ObjectName': new}, {'ObjectName': new.rsplit('/', 1)[1], 'OuterIndex': -4}])
        built['Exports'][0]['Data'][0]['Value'] = -5
        edits = [{'export': 'Section0', 'export_index': 0, 'old': 'VO_BTL_ATK_01_CHR0020_Cue', 'new': new}]
        voices.check_track(original, built, edits)
        built['Exports'][1]['Data'][0]['Value'] = -5
        with self.assertRaisesRegex(ValueError, 'unrelated'): voices.check_track(original, built, edits)

    def test_opt_in_and_missing_native_command_are_guarded(self):
        u = unit(); forbidden = mock.Mock(side_effect=AssertionError('Unneeded game data access'))
        for choice in (None, u['id']):
            if choice is not None: u['battleVoice'] = choice
            voices.prepare([], [], [], [u], '/unused', forbidden, forbidden, forbidden)
        u['battleVoice'] = 1008; data = fixture(u)
        data[voices.COMMANDS][u['jp']]['detailData'].append({'SkillId':987650})
        with self.assertRaisesRegex(ValueError, 'command'): voices.voice_skills(u, lambda rel:data[rel])

    def test_verified_inventory_contains_every_selected_speaker_phase(self):
        for id, _, _, _ in party.CHARACTERS:
            p = voices.profile(id); label = party.voice_label(id)
            self.assertEqual(p['attack']['name'], f'VO_BTL_ATK_01_{label}')
            for phase in ('opening','release','finish'):
                self.assertIn(label, p[phase]['name']); self.assertGreater(p[phase]['duration'], 0)


if __name__ == '__main__': unittest.main()
