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

    def repair(self, ids=None):
        with mock.patch.dict('sys.modules', {'ffbe_resonance': resonance}):
            return motion.prepare_sequences(self.tables, self.clones, self.jobs,
                [{'awakening': [[['ActiveSkill', sid] for sid in (ids or [250020])]]}], self.root,
                lambda rel: copy.deepcopy(self.game[rel]), mock.Mock(), self.support)

    def monster_needles_fixture(self):
        """Needle really binds only offset 2 to the shared enemy Stab folder."""
        self.catalog['skills'] = [
            {'id': sid, 'name': name, 'attr': 'Ability', 'seq': [], 'hits': 1,
             'dmgType': 'Physic', 'calcType': 'Fixed', 'mag': power, 'target': 'Single'}
            for sid, (name, power) in motion.MONSTER_NEEDLES.items()]
        self.catalog['skills'].append({'id': 500260, 'name': 'Needle', 'attr': 'Ability', 'seq': [2], 'hits': 1})
        self.particle = '/Game/Effect/03_SKL/skl500090/NS_EF_SKL500090_Hit_001'
        self.catalog['niagara'] = [self.particle]
        (self.root / 'data/ffr_catalog.json').write_text(json.dumps(self.catalog))
        self.game['Skill/DT_SkillData'] = {str(sid): {**copy.deepcopy(self.skill), 'ID': sid,
            'Name': name, 'skillAttrType': 'Ability', 'DamageType': 'Physic', 'damageCalcType': 'Fixed',
            'TargetType': 'Single', 'defaultTargetRelation': 'Enemies', 'defaultTargetState': 'Alive',
            'hitCount': 1, 'hitDamageRatioList': [1.0], 'magnification': power, 'effectBundleList': []}
            for sid, (name, power) in motion.MONSTER_NEEDLES.items()}
        self.game['Skill/DT_SkillData']['donor'] = {**copy.deepcopy(self.game['Skill/DT_SkillData']['500270']),
            'ID': 500260, 'Name': 'Needle', 'damageCalcType': 'Physic', 'magnification': 18}
        master = 'Sequencer/Battle/EnemySkill/500090/500092/SEQ_Battle_500092_Master'
        path = self.root / 'extracted/legacy/FFRS/Content' / (master + '.uasset')
        path.parent.mkdir(parents=True); path.write_bytes(b'Synthetic shared monster sequence')
        for rel in ('Asset/Skill/DT_SkillAsset', 'Asset/Skill/CDT_SkillAsset_Demo'):
            self.game[rel] = {'donor': {'ID': 500262, 'LevelSequence': '/Game/' + master}, 'shell': {'ID': 440111}}
        self.imports[0]['ObjectName'] = self.particle
        self.imports[1]['ObjectName'] = 'NS_EF_SKL500090_Hit_001'
        self.events[1][2]['Effect_NiagaraData']['niagaraAsset'] = 'import:NS_EF_SKL500090_Hit_001'
        self.game['Battle/Sequencer/DT_BtlHitEffectData'] = {'donor': {'ID': 500090, 'NormalEffectID': 321}, 'generic': {'ID': 449999}}
        self.events[2][2]['Other_Reaction_Id'] = 500090

    def test_both_monster_needle_trials_keep_fixed_damage_one_hit_and_recipient_motion(self):
        self.monster_needles_fixture(); before = copy.deepcopy(self.game)
        self.assertEqual(self.repair([500270, 505110]), [500270, 505110])
        self.assertEqual(self.game, before)
        self.assertNotIn('Skill/DT_SkillData', self.tables)
        self.assertNotIn('Skill/DT_SkillEffectData', self.tables)
        for sid, job in zip((500270, 505110), self.jobs):
            reactions = [e for e in job['plan']['events'] if e['set']['EventType'] == 'OtherReaction']
            self.assertEqual(len(reactions), 1)
            self.assertEqual(reactions[0]['set']['Other_Reaction_Id'], sid)
            self.assertTrue(reactions[0]['set']['Otber_Reaction_bChangeColor'])
            names = {e['set'].get('Unit_PlayAnimByName_AnimationName') for e in job['plan']['events']}
            self.assertTrue({'command', 'attack_A', 'idle'} <= names)
            particles = [e for e in job['plan']['events'] if e['set']['EventType'] == 'EffectSpawnNiagaraAtTarget']
            self.assertEqual(len(particles), 1)
            self.assertEqual(particles[0]['set']['Effect_NiagaraData']['niagaraAsset'],
                {'path': self.particle + '.NS_EF_SKL500090_Hit_001', 'class': 'NiagaraSystem'})
            self.assertFalse(particles[0]['set']['Effect_SpawnNiagaraAtTarget_IsAllSide'])
        record = json.loads((self.root / 'build/animation-repair-report.json').read_bytes())
        self.assertTrue(all(s['donor'] == 500260 and s['rule'] == 'monster_needle' for s in record['skills']))
        self.assertFalse(record['inGameValidated'])

    def test_needles_reject_changed_mechanics_or_unavailable_monster_particles(self):
        self.monster_needles_fixture()
        self.game['Skill/DT_SkillData']['500270']['hitCount'] = 2
        with self.assertRaisesRegex(ValueError, 'original single-hit fixed-damage'): self.repair([500270])
        self.game['Skill/DT_SkillData']['500270']['hitCount'] = 1
        self.events[:] = [e for e in self.events if e[2]['EventType'] != 'EffectSpawnNiagaraAtTarget']
        with self.assertRaisesRegex(ValueError, 'Needle has no reusable target particle'): self.repair([500270])
        self.assertEqual(self.jobs, [])

    def engine_runner(self, calls):
        """Model 1.0.0.15's path/class input and import:name dump contract."""
        state = {}
        def decode(value):
            if isinstance(value, dict):
                if value.get('class') == 'NiagaraSystem':
                    package, name = value['path'].rsplit('.', 1)
                    ref = next(i for i, item in enumerate(state['asset']['Imports'])
                               if item['ObjectName'] == name and item['ClassName'] == 'NiagaraSystem')
                    outer = state['asset']['Imports'][ref]['OuterIndex']
                    self.assertEqual(state['asset']['Imports'][-outer - 1]['ObjectName'], package)
                    return 'import:' + name
                self.assertNotIn('$struct', value)
                return {k: decode(v) for k, v in value.items()}
            if isinstance(value, list): return [decode(v) for v in value]
            self.assertFalse(isinstance(value, str) and value.startswith('import:'),
                             'The real patcher treats this dump label as a literal asset path.')
            return value
        def run(args):
            calls.append(args)
            if 'patch' in args:
                state['patch'] = json.loads(Path(args[2]).read_bytes())
                state['asset'] = json.loads(Path(state['patch']['sequenceData'][0]['json']).read_bytes())
                state['dump'] = {str(e['export']) + ':event': decode(e['set']) for e in state['patch']['bytecode']}
            elif 'tojson' in args:
                Path(args[3]).write_text(json.dumps(state.get('asset', {'Imports': [], 'NameMap': []})))
            elif 'seqdump' in args: Path(args[3]).write_text(json.dumps(state['dump']))
        return run, state

    def author(self, asset, plan):
        return [{'export': str(i + 10), 'set': e['set']} for i, e in enumerate(plan['events'])]

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
        run, _ = self.engine_runner(calls)
        with mock.patch.dict('sys.modules', {'ffbe_resonance': resonance}), mock.patch.object(resonance, 'author',
                side_effect=self.author):
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
        self.repair(); job, = self.jobs; calls = []
        run, state = self.engine_runner(calls)
        with mock.patch.dict('sys.modules', {'ffbe_resonance': resonance}), mock.patch.object(resonance, 'author',
                side_effect=self.author):
            motion.build_effect_sequence(job, self.root, self.root, ['ffr-dt'], 'mapping', run)
        patched = [e['set'] for e in state['patch']['bytecode']]
        particle = next(e['Effect_NiagaraData'] for e in patched if e['EventType'] == 'EffectSpawnNiagaraAtTarget')
        self.assertEqual(particle, {'niagaraAsset': {'path': self.particle + '.NS_EF_SKL220020_PosAll', 'class': 'NiagaraSystem'},
                         'scale': {'x': 1, 'y': 1, 'z': 1},
                         'Scale': {'X': 1.5, 'Y': 2.0, 'Z': 0.5},
                         'userParameterDatas': [{'ParameterName': 'Power', 'Value': 3.0}]})
        self.assertEqual(self.events, before)
        self.assertEqual(len([e for e in patched if e['EventType'] == 'OtherReaction']), 4)

    def test_secondary_particles_and_friend_enemy_imports_keep_their_real_packages(self):
        secondary = '/Game/Effect/03_SKL/skl210260/NS_EF_SKL210260_Vanishla_001_Center'
        self.catalog['niagara'].append(secondary)
        (self.root / 'data/ffr_catalog.json').write_text(json.dumps(self.catalog))
        self.imports.extend([{'ObjectName': secondary, 'ClassName': 'Package', 'ClassPackage': '/Script/CoreUObject', 'OuterIndex': 0},
                             {'ObjectName': secondary.rsplit('/', 1)[-1], 'ClassName': 'NiagaraSystem', 'ClassPackage': '/Script/Niagara', 'OuterIndex': -3}])
        spawn = next(e for _, _, e in self.events if e['EventType'] == 'EffectSpawnNiagaraAtTarget')
        spawn['Effect_SpawnTarget_NiagaraData'] = {'$struct': 'BTL_SEQUENCER_NIAGARA_DATA',
                     'niagaraAsset': 'import:' + secondary.rsplit('/', 1)[-1],
                     'friendNiagaraAsset': -2, 'enemyNiagaraAsset': None}
        before = copy.deepcopy(self.events)
        self.repair(); job, = self.jobs; calls = []
        run, state = self.engine_runner(calls)
        with mock.patch.dict('sys.modules', {'ffbe_resonance': resonance}), mock.patch.object(resonance, 'author', side_effect=self.author):
            motion.build_effect_sequence(job, self.root, self.root, ['ffr-dt'], 'mapping', run)
        effect = next(e['set'] for e in state['patch']['bytecode'] if e['set']['EventType'] == 'EffectSpawnNiagaraAtTarget')
        self.assertEqual(effect['Effect_SpawnTarget_NiagaraData']['niagaraAsset']['path'], secondary + '.' + secondary.rsplit('/', 1)[-1])
        self.assertEqual(effect['Effect_SpawnTarget_NiagaraData']['friendNiagaraAsset'], effect['Effect_NiagaraData']['niagaraAsset'])
        self.assertIsNone(effect['Effect_SpawnTarget_NiagaraData']['enemyNiagaraAsset'])
        self.assertEqual(len(state['asset']['Imports']), 4)
        self.assertEqual(self.events, before)

    def test_same_object_name_in_the_wrong_package_still_stops_mod_packing(self):
        self.repair(); job, = self.jobs; run, state = self.engine_runner([])
        def wrong_package(args):
            run(args)
            if 'seqdump' in args:
                state['asset']['Imports'][0]['ObjectName'] = '/Game/Effect/WrongPackage'
        with mock.patch.dict('sys.modules', {'ffbe_resonance': resonance}), mock.patch.object(resonance, 'author', side_effect=self.author):
            with self.assertRaisesRegex(ValueError, 'reference differs.*Mod packing stopped'):
                motion.build_effect_sequence(job, self.root, self.root, ['ffr-dt'], 'mapping', wrong_package)

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
