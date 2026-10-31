"""General authored voice substitution and isolation from mechanics/effect audio."""
import copy
import contextlib
import gzip
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
                              'personal': {'ID': 666030, 'skillAttrType': 'Ability', 'hasUnit': owner},
                              'counter': {'ID': 666040, 'skillAttrType': 'ChaseAttack', 'hasUnit': owner},
                              'other': {'ID': 666020, 'skillAttrType': 'LimitBurst', 'hasUnit': 'Other'}},
              'Asset/Skill/DT_SkillAsset': {}, 'Asset/Skill/CDT_SkillAsset_Demo': {}}
    for sid in (987650, 666010, 666030, 666040):
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
                                               (f'VO_BTL_{old}_082_Cue', 700), ('VO_C01_DIALOGUE_Cue', 50)]),
                                      (666030, [(f'VO_BTL_{old}_041_Cue', 100), ('SE_ICE_Cue', 200),
                                               (f'VO_BTL_ATK_01_{old}_Cue', 300)]),
                                      (666040, [(f'VO_BTL_ABL_01_{old}_Cue', 0), ('SE_SWORD_Cue', 100)])]:
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
                    self.assertEqual(len(sound_edits), 8)
                    self.assertTrue(all(x['set']['Sound'] and party.voice_label(source) in x['set']['Sound'] for x in sound_edits))
                    plan = json.loads((root / voices.PLAN).read_bytes())
                    self.assertEqual({c['export'] for c in plan['changes'] if '666010' in c['asset']}, {'Section0','Section2','Section3','Section4'})
                    for c in plan['changes']:
                        if '666010' not in c['asset']: continue
                        phase = {'Section3':'opening','Section0':'release','Section2':'attack','Section4':'finish'}[c['export']]
                        self.assertTrue(c['new'].endswith('_' + phase + '_Cue'))
                    self.assertEqual(len(clones), 9); self.assertEqual(len(cue_edits), 5)
                    self.assertEqual({c['set']['CueName'] for c in cue_edits}, {c['name'] for c in voices.profile(source).values()})
                    for c in plan['changes']:
                        if '666030' in c['asset'] or '666040' in c['asset']:
                            phase = 'attack' if c['old'].startswith('VO_BTL_ATK_') else 'ability'
                            self.assertTrue(c['new'].endswith('_' + phase + '_Cue'))

    def test_captured_full_game_routes_include_every_owned_personal_and_counter_skill(self):
        captured = json.loads(gzip.decompress((ROOT / 'scripts/fixtures/party_voice_routes.json.gz').read_bytes()))
        for uid, _, _, _ in party.CHARACTERS:
            u = unit(uid); u.pop('ffbe')
            routes = dict(voices.voice_skills(u, lambda rel: captured['rows'][rel]))
            attack = routes.pop(captured['attacks'][str(uid)])
            self.assertEqual(attack, 'attack')
            owner = next(s['hasUnit'] for s in captured['rows'][voices.SKILLS].values()
                         if s['ID'] == captured['attacks'][str(uid)])
            owned = [s for s in captured['rows'][voices.SKILLS].values() if s['hasUnit'] == owner]
            self.assertEqual(set(routes), {s['ID'] for s in owned} - {captured['attacks'][str(uid)]})
            self.assertTrue(any(s['skillAttrType'] == 'ChaseAttack' and routes[s['ID']] == 'ability' for s in owned))
        lasswell = dict(voices.voice_skills(unit(1002), lambda rel: captured['rows'][rel]))
        self.assertEqual(lasswell[402130], 'ability')  # Dawn Frost
        self.assertEqual(lasswell[402020], 'ability')  # Native counter sequence
        self.assertEqual(lasswell[402500], 'ability')  # Simplified attack

    def test_captured_dawn_frost_and_counter_replace_only_lasswell_voice_exports(self):
        captured = json.loads(gzip.decompress((ROOT / 'scripts/fixtures/party_voice_routes.json.gz').read_bytes()))
        u = unit(1002); u.pop('ffbe'); u['battleVoice'] = 1008
        values = copy.deepcopy(captured['rows'])
        # Keep the real voice ownership and command guard, selecting only the
        # two captured sequence packages for this focused timeline regression.
        values['Asset/Skill/DT_SkillAsset'] = captured['assets']
        values['Asset/Skill/CDT_SkillAsset_Demo'] = {}
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); views = {}
            for rel, view in captured['tracks'].items():
                path = root / 'extracted/legacy' / (rel + '.uasset')
                path.parent.mkdir(parents=True); path.touch(); views[str(path)] = view
                master = path.parent.parent / ('SEQ_Battle_' + ('402131' if '402130' in rel else '402021') + '_Master.uasset')
                master.touch()
            def extract(rel):
                name = Path(rel).name
                path = root / 'extracted/legacy/FFRS/Content' / (rel + '.uasset')
                path.parent.mkdir(parents=True, exist_ok=True); path.touch()
                views[str(path)] = template(u, name)
            post = []
            with contextlib.redirect_stdout(io.StringIO()):
                voices.prepare([], [], post, [u], root, lambda rel: values[rel], extract,
                               lambda path: (copy.deepcopy(views[path]), {}))
            plan = json.loads((root / voices.PLAN).read_bytes())
            self.assertEqual({c['old'] for c in plan['changes']},
                             {'VO_BTL_CHR0020_041_Cue', 'VO_BTL_ABL_01_CHR0020_Cue'})
            self.assertEqual(len(plan['changes']), 2)
            for rel, original in captured['tracks'].items():
                changes = [c for c in plan['changes'] if c['asset'] == rel]
                built = copy.deepcopy(original)
                for c in changes:
                    built['Imports'].append({'ObjectName': c['new']})
                    outer = -len(built['Imports'])
                    built['Imports'].append({'ObjectName': c['new'].rsplit('/', 1)[1], 'OuterIndex': outer})
                    sound = next(p for p in built['Exports'][c['export_index']]['Data'] if p['Name'] == 'Sound')
                    sound['Value'] = -len(built['Imports'])
                voices.check_track(original, built, changes)
            self.assertEqual(plan['cues'][0]['set']['CueName'], 'VO_BTL_ABL_01_CHR0080')

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

    def test_captured_duplicate_names_redirect_voice_imports_and_preserve_other_exports(self):
        captured = json.loads(gzip.decompress((ROOT / 'scripts/fixtures/party_voice_routes.json.gz').read_bytes()))
        self.assertEqual(len(captured['ambiguousTracks']), 6)
        for asset, sample in captured['ambiguousTracks'].items():
            original = sample['data']; label = party.voice_label(sample['target'])
            new = '/Game/Sound/StudioPartyVoice/CHR0020/StudioPartyVoice_CHR0020_ability_Cue'
            changes = [{'export': name, 'export_index': index, 'old': cue, 'new': new, 'target': sample['target']}
                       for name, cue, _, index in voices.sounds(original) if cue.startswith('VO_BTL_') and label in cue]
            clone, post = voices.track_edits(asset, original, changes)
            self.assertEqual(post, [])
            self.assertEqual(clone['from'], asset); self.assertEqual(clone['to'], asset)
            self.assertTrue(clone['rename'])
            built = copy.deepcopy(original)
            # The native SDK clone rewrites name references, without resolving
            # an export by its ambiguous short name. Real package readback is
            # also performed before release against these six cooked tracks.
            for entry in built['Imports']:
                for old, replacement in clone['rename']:
                    entry['ObjectName'] = entry['ObjectName'].replace(old, replacement)
            voices.check_track(original, built, changes)
            self.assertEqual(len(list(voices.sounds(built))), len(list(voices.sounds(original))))

    def test_prepare_retains_both_voice_exports_sharing_a_name_after_an_effect(self):
        u = unit(1004); u.pop('ffbe'); u['battleVoice'] = 1008
        data = fixture(u); data['Asset/Skill/DT_SkillAsset'] = {
            k:v for k,v in data['Asset/Skill/DT_SkillAsset'].items() if v['ID'] == 666041}
        original = track([('SE_SWORD_Cue', 100), ('VO_BTL_ABL_01_CHR0040_Cue', 200),
                          ('VO_BTL_CHR0040_041_Cue', 300)])
        for index, export in enumerate(original['Exports']):
            export.update(ObjectName='RepeatedSection', OuterIndex=index+10)
        for index in (2,3):
            entry=original['Imports'][index]
            original['Imports'].append({'ObjectName':
                '/Game/Sound/Cri/Voice/VO_BTL/VO_BTL_CHR0040/'+entry['ObjectName']})
            entry['OuterIndex']=-len(original['Imports'])
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); folder = root/'extracted/legacy/FFRS/Content/Sequencer/Battle/Skill/666040'
            folder.mkdir(parents=True); (folder/'SEQ_Battle_666041_Master.uasset').touch()
            path = folder/'SEQ_Battle_666041_Sound.uasset'; path.touch(); views={str(path):original}
            def extract(rel):
                p=root/'extracted/legacy/FFRS/Content'/(rel+'.uasset');p.parent.mkdir(parents=True,exist_ok=True);p.touch()
                views[str(p)]=template(u,Path(rel).name)
            clones=[];post=[]
            with contextlib.redirect_stdout(io.StringIO()):
                voices.prepare([],clones,post,[u],root,lambda rel:data[rel],extract,lambda p:(views[p],{}))
            plan=json.loads((root/voices.PLAN).read_bytes())
            self.assertEqual([c['export_index'] for c in plan['changes']],[1,2])
            self.assertFalse(any('Sound' in edit['set'] for edit in post))
            sound_clone=next(c for c in clones if c['from']==c['to'])
            self.assertEqual(len(sound_clone['rename']),4)
            self.assertTrue(all(c['new'].endswith('StudioPartyVoice_CHR0080_ability_Cue') for c in plan['changes']))

    def test_import_redirect_refuses_conflicting_or_unselected_uses(self):
        original = track([('SE_SWORD_Cue',100),('VO_BTL_ABL_01_CHR0020_Cue',200),
                          ('VO_BTL_ABL_01_CHR0020_Cue',300)])
        for e in original['Exports']:e['ObjectName']='RepeatedSection'
        edits=[{'export':'RepeatedSection','export_index':i,'old':'VO_BTL_ABL_01_CHR0020_Cue',
                'new':'/Game/StudioVoice','target':1002} for i in (1,2)]
        with self.assertRaisesRegex(ValueError,'unselected'):voices.track_edits('NativeSoundTrack',original,edits[:1])
        edits[1]['new']='/Game/DifferentVoice'
        with self.assertRaisesRegex(ValueError,'different recordings'):voices.track_edits('NativeSoundTrack',original,edits)

    def test_opt_in_and_missing_native_command_are_guarded(self):
        u = unit(); forbidden = mock.Mock(side_effect=AssertionError('Unneeded game data access'))
        for choice in (None, u['id']):
            if choice is not None: u['battleVoice'] = choice
            voices.prepare([], [], [], [u], '/unused', forbidden, forbidden, forbidden)
        u['battleVoice'] = 1008; data = fixture(u)
        data[voices.COMMANDS][u['jp']]['detailData'].append({'SkillId':987650})
        with self.assertRaisesRegex(ValueError, 'command'): voices.voice_skills(u, lambda rel:data[rel])

    def test_verified_inventory_contains_every_selected_speaker_phase(self):
        captured = json.loads(gzip.decompress((ROOT / 'scripts/fixtures/party_voice_routes.json.gz').read_bytes()))
        for id, _, _, _ in party.CHARACTERS:
            p = voices.profile(id); label = party.voice_label(id)
            self.assertEqual(p['attack']['name'], f'VO_BTL_ATK_01_{label}')
            self.assertEqual(p['ability']['name'], f'VO_BTL_ABL_01_{label}')
            self.assertGreater(p['ability']['duration'], 0)
            self.assertEqual(p['ability'], captured['abilityCues'][label])
            for phase in ('opening','release','finish'):
                self.assertIn(label, p[phase]['name']); self.assertGreater(p[phase]['duration'], 0)


if __name__ == '__main__': unittest.main()
