"""Effect-only reuse across different mechanics, using cooked import shapes."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from test_animation_and_library import motion, resonance


class TargetEffectReuseTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.root = Path(self.temp.name)
        self.skill = {'ID': 250020, 'Name': 'Fira', 'skillAttrType': 'Magic', 'hasUnit': 'All',
                      'DamageType': 'Magic', 'element': 'Fire', 'TargetType': 'Group',
                      'defaultTargetRelation': 'Friendlies', 'defaultTargetState': 'Dead',
                      'hitCount': 4, 'hitDamageRatioList': [.1, .2, .3, .4],
                      'magnification': 22, 'Cost': 9, 'effectBundleList': [{'effectId': 1003}]}
        donor = {**copy.deepcopy(self.skill), 'ID': 220020, 'TargetType': 'Single',
                 'defaultTargetRelation': 'Enemies', 'defaultTargetState': 'Alive', 'hitCount': 2,
                 'hitDamageRatioList': [.5, .5], 'magnification': 33, 'Cost': 15, 'effectBundleList': []}
        self.game = {'Skill/DT_SkillData': {'recipient': self.skill, 'donor': donor},
                     'Skill/DT_SkillEffectData': {'effect': {'ID': 1003, 'EffectType': 'Revival', 'ParamList': [100]}},
                     'Battle/Sequencer/DT_BtlHitEffectData': {'donor': {'ID': 220020, 'NormalEffectID': 123, 'CriticalEffectID': 124},
                                                          'recipient': {'ID': 250020, 'NormalEffectID': -1},
                                                          'generic': {'ID': 449999}}}
        self.particle = '/Game/Effect/03_SKL/skl220020/NS_EF_SKL220020_PosAll'
        self.catalog = {'skills': [
            {'id': 250020, 'name': 'Fira', 'attr': 'Magic', 'seq': [], 'hits': 4, 'element': 'Fire', 'dmgType': 'Magic', 'mag': 22, 'target': 'Group'},
            {'id': 220020, 'name': 'Fira', 'attr': 'Magic', 'hasUnit': 'All', 'seq': [1], 'hits': 2, 'element': 'Fire', 'dmgType': 'Magic', 'mag': 33, 'target': 'Single'}],
            'niagara': [self.particle]}
        (self.root / 'data').mkdir(); (self.root / 'data/ffr_catalog.json').write_text(json.dumps(self.catalog))
        folder = 'Sequencer/Battle/Magic/220010/220011'
        asset = {'ID': 220021, 'LevelSequence': f'/Game/{folder}/SEQ_Battle_220011_Master'}
        for rel in ('Asset/Skill/DT_SkillAsset', 'Asset/Skill/CDT_SkillAsset_Demo'):
            self.game[rel] = {'donor': copy.deepcopy(asset), 'shell': {'ID': 440111}}
        path = self.root / 'extracted/legacy/FFRS/Content' / folder / 'SEQ_Battle_220011_Master.uasset'
        path.parent.mkdir(parents=True); path.write_bytes(b'explicit synthetic package presence')
        shell = self.root / 'extracted/legacy' / (resonance.SHELL + '.uasset')
        shell.parent.mkdir(parents=True); shell.write_bytes(b'explicit synthetic authored shell')
        self.imports = [{'ObjectName': self.particle, 'ClassName': 'Package', 'ClassPackage': '/Script/CoreUObject', 'OuterIndex': 0, 'PackageName': 'None'},
                        {'ObjectName': 'NS_EF_SKL220020_PosAll', 'ClassName': 'NiagaraSystem', 'ClassPackage': '/Script/Niagara', 'OuterIndex': -1, 'PackageName': 'None'}]
        # Incompatible owner choreography is intentionally not copied.
        self.events = [(0, 'cast', {'EventType': 'UnitPlayAnimByName', 'Unit_PlayAnimByName_AnimationName': 'LB1'}),
                       (12000, 'spawn', {'EventType': 'EffectSpawnNiagaraAtTarget',
                         'Effect_NiagaraData': {'niagaraAsset': 'import:NS_EF_SKL220020_PosAll', 'scale': {'x': 1, 'y': 1, 'z': 1}},
                         'Effect_SpawnNiagaraAtTarget_IsAllSide': True}),
                       (18000, 'hit1', {'EventType': 'OtherReaction', 'Other_Reaction_Id': 220020}),
                       (22000, 'hit2', {'EventType': 'OtherReaction', 'Other_Reaction_Id': 220020}),
                       (30000, 'cleanup', {'EventType': 'EffectDestroyNiagaraToNiagaraID', 'Effect_DestroyNiagaraToNiagaraID_Id': 1}),
                       (35000, 'speed', {'EventType': 'OtherSetGameSpeed', 'Other_SetGameSpeed_TimeDilation': .1})]
        self.support = {'dumps': lambda path: ({'Imports': copy.deepcopy(self.imports)},
                          {f'{i+1}:{name}': copy.deepcopy(e) for i, (_, name, e) in enumerate(self.events)}),
                        'keys': lambda path: [(t, e['EventType'], n) for t, n, e in self.events],
                        'clone': mock.Mock(side_effect=AssertionError('Must not clone donor choreography')),
                        'objects': [], 'bytecode': []}
        self.tables = {}; self.clones = []; self.jobs = []

    def tearDown(self): self.temp.cleanup()

    def repair(self):
        with mock.patch.dict('sys.modules', {'ffbe_resonance': resonance}):
            return motion.prepare_sequences(self.tables, self.clones, self.jobs,
                [{'awakening': [[['ActiveSkill', 250020]]]}], self.root,
                lambda rel: copy.deepcopy(self.game[rel]), mock.Mock(), self.support)

    def test_effects_reuse_preserves_recipient_mechanics_routing_hits_and_white_fix(self):
        before = copy.deepcopy(self.game)
        self.assertEqual(self.repair(), [250020])
        self.assertEqual(self.game, before)
        self.assertNotIn('Skill/DT_SkillData', self.tables); self.assertNotIn('Skill/DT_SkillEffectData', self.tables)
        job, = self.jobs; self.assertEqual(job['kind'], 'skill_effect')
        hits = [e for e in job['plan']['events'] if e['set']['EventType'] == 'OtherReaction']
        self.assertEqual(len(hits), 4)
        self.assertTrue(all(e['set']['Other_Reaction_Id'] == 250020 and e['set']['Otber_Reaction_bChangeColor'] for e in hits))
        particles = [e for e in job['plan']['events'] if e['set']['EventType'] == 'EffectSpawnNiagaraAtTarget']
        self.assertEqual(len(particles), 1); self.assertFalse(particles[0]['set']['Effect_SpawnNiagaraAtTarget_IsAllSide'])
        self.assertTrue(all(e['time'] < job['plan']['duration'] for e in job['plan']['events']))
        self.assertFalse(any(e['set'].get('Unit_PlayAnimByName_AnimationName') == 'LB1' for e in job['plan']['events']))
        self.assertFalse(any(e['set']['EventType'] == 'OtherSetGameSpeed' for e in job['plan']['events']))
        change, = self.tables['Battle/Sequencer/DT_BtlHitEffectData']['set']
        self.assertEqual(change, {'row': 'recipient', 'set': {'NormalEffectID': 123, 'CriticalEffectID': 124}})
        record = json.loads((self.root / 'build/animation-repair-report.json').read_bytes())['skills'][0]
        self.assertEqual((record['status'], record['donor'], record['particleEvents']), ('effect_reuse', 220020, 1))
        self.assertEqual(self.repair(), []); self.assertEqual(len(self.jobs), 1)

    def test_missing_particles_fail_instead_of_reporting_a_motion_only_success(self):
        self.events = [e for e in self.events if e[1] != 'spawn']
        with self.assertRaisesRegex(ValueError, 'Fira.*no reusable target particle'):
            self.repair()
        self.assertEqual(self.jobs, [])

    def test_missing_or_character_imports_fail_without_changing_installed_data(self):
        for change in ('missing', 'character'):
            with self.subTest(change=change):
                original = copy.deepcopy(self.imports)
                if change == 'missing': self.imports = []
                else: self.imports[0]['ObjectName'] = '/Game/Chara/summon/OwnerBody'
                with self.assertRaises(ValueError): self.repair()
                self.assertEqual(self.tables, {}); self.assertEqual(self.jobs, [])
                self.imports = original

    def test_existing_or_explicit_sequence_keeps_its_original_visuals(self):
        self.game['Asset/Skill/DT_SkillAsset']['existing'] = {'ID': 250021, 'LevelSequence': '/Game/Existing'}
        self.assertEqual(self.repair(), []); self.assertEqual(self.jobs, [])

    def test_niagara_imports_are_remapped_without_copying_donor_actors_and_are_idempotent(self):
        self.repair(); job, = self.jobs
        shell = {'Imports': [{'ObjectName': '/Script/Engine', 'ClassName': 'Package', 'ClassPackage': '/Script/CoreUObject', 'OuterIndex': 0}], 'NameMap': []}
        motion.effect_imports(shell, job['effectImports'])
        self.assertEqual(len(shell['Imports']), 3)
        self.assertEqual(shell['Imports'][2]['OuterIndex'], -2)
        self.assertEqual(shell['Imports'][2]['ClassName'], 'NiagaraSystem')
        self.assertIn('NS_EF_SKL220020_PosAll', shell['NameMap'])
        before = copy.deepcopy(shell); motion.effect_imports(shell, job['effectImports']); self.assertEqual(shell, before)
        bad = copy.deepcopy(job['effectImports']); bad[0]['imports'][0]['OuterIndex'] = -2
        with self.assertRaisesRegex(ValueError, 'ancestry'): motion.effect_imports(copy.deepcopy(shell), bad)

    def test_authored_output_contains_particle_imports_and_effect_constants(self):
        self.repair(); job, = self.jobs; calls = []
        def run(args):
            calls.append(args)
            if 'tojson' in args:
                Path(args[3]).write_text(json.dumps({'Imports': [], 'NameMap': []}))
            elif 'seqdump' in args:
                particle = next(e['set'] for e in job['plan']['events'] if e['set']['EventType'] == 'EffectSpawnNiagaraAtTarget')
                Path(args[3]).write_text(json.dumps({'10:particle': particle}))
        with mock.patch.dict('sys.modules', {'ffbe_resonance': resonance}), mock.patch.object(resonance, 'author',
                side_effect=lambda asset, plan: [{'export': '10', 'set': e['set']} for e in plan['events']]):
            motion.build_effect_sequence(job, self.root, self.root, ['ffr-dt'], 'mapping', run)
        patch = json.loads(Path(next(c[2] for c in calls if 'patch' in c)).read_bytes())
        cooked = json.loads(Path(patch['sequenceData'][0]['json']).read_bytes())
        self.assertEqual(cooked['Imports'][1]['ClassName'], 'NiagaraSystem')
        self.assertTrue(any(e['set']['EventType'] == 'EffectSpawnNiagaraAtTarget' for e in patch['bytecode']))

    def test_seqdump_struct_annotations_do_not_reach_the_engine_patch(self):
        # seqdump describes struct types; the patcher's struct replacement
        # accepts only real fields, including fields inside nested arrays.
        data = next(e['Effect_NiagaraData'] for _, _, e in self.events if 'Effect_NiagaraData' in e)
        data.update({'$struct': 'BTL_SEQUENCER_NIAGARA_DATA',
                     'Scale': {'$struct': 'Vector', 'X': 1.5, 'Y': 2.0, 'Z': 0.5},
                     'userParameterDatas': [{'$struct': 'BTL_NIAGARA_USER_PARAMETER_DATA',
                                              'ParameterName': 'Power', 'Value': 3.0}]})
        before = copy.deepcopy(self.events)
        self.repair(); job, = self.jobs; patched = []
        def check_fields(value):
            if isinstance(value, dict):
                self.assertNotIn('$struct', value, "ffr-dt rejects '$struct' as a field")
                for child in value.values(): check_fields(child)
            elif isinstance(value, list):
                for child in value: check_fields(child)
        def run(args):
            if 'tojson' in args:
                Path(args[3]).write_text(json.dumps({'Imports': [], 'NameMap': []}))
            elif 'patch' in args:
                patch = json.loads(Path(args[2]).read_bytes())
                check_fields(patch['bytecode'])
                patched.extend(e['set'] for e in patch['bytecode'])
            elif 'seqdump' in args:
                particle = next(e for e in patched if e['EventType'] == 'EffectSpawnNiagaraAtTarget')
                Path(args[3]).write_text(json.dumps({'10:particle': particle}))
        with mock.patch.dict('sys.modules', {'ffbe_resonance': resonance}), mock.patch.object(resonance, 'author',
                side_effect=lambda asset, plan: [{'export': '10', 'set': e['set']} for e in plan['events']]):
            motion.build_effect_sequence(job, self.root, self.root, ['ffr-dt'], 'mapping', run)
        particle = next(e['Effect_NiagaraData'] for e in patched if e['EventType'] == 'EffectSpawnNiagaraAtTarget')
        self.assertEqual(particle, {'niagaraAsset': 'import:NS_EF_SKL220020_PosAll',
                         'scale': {'x': 1, 'y': 1, 'z': 1},
                         'Scale': {'X': 1.5, 'Y': 2.0, 'Z': 0.5},
                         'userParameterDatas': [{'ParameterName': 'Power', 'Value': 3.0}]})
        self.assertEqual(self.events, before)
        self.assertEqual(len([e for e in patched if e['EventType'] == 'OtherReaction']), 4)

    def test_written_timeline_missing_the_particle_reference_stops_mod_packing(self):
        self.repair(); job, = self.jobs
        def run(args):
            if 'tojson' in args: Path(args[3]).write_text(json.dumps({'Imports': [], 'NameMap': []}))
            elif 'seqdump' in args: Path(args[3]).write_text('{}')
        particle = next(e['set'] for e in job['plan']['events'] if e['set']['EventType'] == 'EffectSpawnNiagaraAtTarget')
        with mock.patch.dict('sys.modules', {'ffbe_resonance': resonance}), mock.patch.object(resonance, 'author',
                return_value=[{'export': '10', 'set': particle}]):
            with self.assertRaisesRegex(ValueError, 'did not retain particle'):
                motion.build_effect_sequence(job, self.root, self.root, ['ffr-dt'], 'mapping', run)


class EffectPolicyTests(unittest.TestCase):
    def test_name_precedes_element_and_earth_awakening_families_use_blade_tiers(self):
        donors = [{'id': sid, 'name': name, 'seq': [0], 'attr': 'MagicSword', 'hasUnit': 'All'}
                  for sid, name in [(420160, 'Stone Blade'), (420170, 'Stonera Blade'), (420180, 'Stonega Blade')]]
        recipients = [{'id': sid, 'name': name, 'seq': [], 'attr': 'MagicSword', 'hits': 1,
                       'dmgType': 'Physic', 'element': 'Earth', 'mag': power}
                      for sid, name, power in [(421340, 'Stone Slam', 12), (421350, 'Stonera Slam', 24),
                          (421360, 'Stonega Slam', 39), (421400, 'Stone Surge', 12),
                          (421410, 'Stonera Surge', 24), (421420, 'Stonega Surge', 39)]]
        p = motion.effect_policy({'skills': donors + recipients})['skills']
        self.assertEqual([p[str(r['id'])]['donor'] for r in recipients], [420160, 420170, 420180] * 2)
        donors.append({'id': 1, 'name': 'STONE SLAM', 'seq': [1], 'attr': 'Magic', 'hasUnit': 'All'})
        self.assertEqual(motion.effect_policy({'skills': donors + recipients})['skills']['421340']['donor'], 1)

    def test_magic_uses_spell_tiers_and_missing_donors_or_special_actions_stay_unmapped(self):
        donors = [{'id': sid, 'name': name, 'seq': [1], 'attr': 'Magic', 'hasUnit': 'All'}
                  for sid, name in [(220210, 'Stone'), (220220, 'Stonera'), (220230, 'Stonega')]]
        skills = [{'id': i, 'name': name, 'seq': [], 'attr': 'Magic', 'hits': 3,
                   'dmgType': 'Magic', 'element': 'Earth', 'mag': power}
                  for i, name, power in [(1, 'Rock', 19), (2, 'Rock II', 24), (3, 'Rock III', 39)]]
        p = motion.effect_policy({'skills': donors + skills})['skills']
        self.assertEqual([p[str(i)]['donor'] for i in (1, 2, 3)], [220210, 220220, 220230])
        skills[0]['element'] = 'None'; skills[1]['attr'] = 'Mimic'; skills[2]['hits'] = 0
        self.assertEqual(motion.effect_policy({'skills': donors + skills})['skills'], {})


if __name__ == '__main__': unittest.main()
