"""Audited own-skill routes preserve native definitions and unrelated tracks."""
import copy
import json
import hashlib
from pathlib import Path
import tempfile
import unittest
from unittest import mock
from test_existing_visions import ROOT, module
import sys
native=module('native_skill_cases',ROOT/'assets/existing_visions/payload/_ffr_native_skills.py')


class NativeSkillRepairTests(unittest.TestCase):
    def fixture(self, root):
        raw={'ID':505040,'hasUnit':'All','TargetType':'Group','hitCount':4,'magnification':100}
        binding={'ID':505042,'LevelSequence':'/Game/Sequencer/Battle/EnemySkill/500560/500562/SEQ_Battle_500562_Master','soundSequence':'None'}
        folder='Sequencer/Battle/EnemySkill/500560/500562';file='Track/SEQ_Battle_500562_Cut_001.uasset'
        path=Path(root)/'extracted/legacy/FFRS/Content'/folder/file;path.parent.mkdir(parents=True);path.write_bytes(b'Explicit native identity fixture')
        rule={'name':'Thwack','folder':folder,'sourceSequence':500562,'definitionSha256':native.digest(raw),
              'bindingSha256':native.digest(binding),'files':{file:hashlib.sha256(path.read_bytes()).hexdigest()},
              'motionEdits':[{'file':file,'function':'EventSEQ_Battle_500562','set':{'Unit_PlayAnimByName_AnimationName':'attack_A'}}],
              'enableTracks':[{'file':file,'export':'MovieSceneEventTrack_18'}]}
        game={'Skill/DT_SkillData':{'Thwack':raw},**{rel:{'enemy':copy.deepcopy(binding)} for rel in ('Asset/Skill/DT_SkillAsset','Asset/Skill/CDT_SkillAsset_Demo')}}
        return game,rule,path

    def test_missing_route_uses_only_own_native_source_and_exact_motion_track(self):
        with tempfile.TemporaryDirectory() as root:
            game,rule,path=self.fixture(root);before=copy.deepcopy(game);tables={};clones=[]
            support={'clone':mock.Mock(return_value={'LevelSequence':'/Game/private/505040/505041/SEQ_Battle_505041_Master','soundSequence':'None'}),'objects':[],'bytecode':[]}
            original=Path.read_bytes
            with mock.patch.object(Path,'read_bytes',lambda p:json.dumps({'schema':1,'skills':{'505040':rule}}).encode() if p.name=='native_skill_repairs.json' else original(p)):
                report=native.prepare(tables,clones,{505040:[{}]},root,lambda r:copy.deepcopy(game[r]),mock.Mock(),support)
            self.assertEqual(report[505040]['sequence'],505041)
            self.assertEqual(support['clone'].call_args.args[1:4],(500562,505040,505041))
            self.assertEqual(support['clone'].call_args.args[8],{})
            self.assertEqual(set(tables),{'Asset/Skill/DT_SkillAsset','Asset/Skill/CDT_SkillAsset_Demo'})
            self.assertTrue(all(t['set']==[] and t['add'][0]['set']['ID']==505041 for t in tables.values()))
            enabled=[o['export'] for o in support['objects'] if o['set'].get('bIsEvalDisabled') is False]
            self.assertEqual(enabled,['MovieSceneEventTrack_18']);self.assertNotIn('MovieSceneEventTrack_0',enabled)
            self.assertEqual(support['bytecode'][0]['export'],'EventSEQ_Battle_505041')
            self.assertEqual(support['bytecode'][0]['set'],{'Unit_PlayAnimByName_AnimationName':'attack_A'})
            self.assertEqual(game,before)

    def test_native_custom_changed_definition_binding_and_file_guards(self):
        for case in ('future','custom','definition','binding','bytes'):
            with self.subTest(case=case), tempfile.TemporaryDirectory() as root:
                game,rule,path=self.fixture(root);selected={505040:[{}]};tables={};support={'clone':mock.Mock(),'objects':[],'bytecode':[]}
                if case=='future':game['Asset/Skill/CDT_SkillAsset_Demo']['future']={'ID':505041}
                if case=='custom':selected[505040]=[{'skills':{'505040':{'from':500120}}}]
                if case=='definition':game['Skill/DT_SkillData']['Thwack']['magnification']=999
                if case=='binding':game['Asset/Skill/DT_SkillAsset']['enemy']['soundSequence']='/Game/Changed'
                if case=='bytes':path.write_bytes(b'Changed native asset')
                original=Path.read_bytes
                with mock.patch.object(Path,'read_bytes',lambda p:json.dumps({'schema':1,'skills':{'505040':rule}}).encode() if p.name=='native_skill_repairs.json' else original(p)):
                    report=native.prepare(tables,[],selected,root,lambda r:copy.deepcopy(game[r]),mock.Mock(),support)
                support['clone'].assert_not_called();self.assertEqual(tables,{})
                if case not in ('future','custom'):self.assertEqual(report[505040]['status'],'native_repair_unresolved')

    def test_shared_enemy_source_gets_player_and_enemy_routes_without_changing_shared_row(self):
        with tempfile.TemporaryDirectory() as root:
            game, rule, _ = self.fixture(root)
            raw = game['Skill/DT_SkillData']['Thwack']; raw['ID'] = 501010
            for rel in native.RELS: game[rel]['enemy']['ID'] = 501010
            binding = game[native.RELS[0]]['enemy']
            rule.update(sourceBinding=501010, retainEnemyRoute=True,
                        definitionSha256=native.digest(raw), bindingSha256=native.digest(binding),
                        effectEdits=[{'file': next(iter(rule['files'])), 'function': 'EffectSEQ_Battle_500562',
                                      'set': {'Effect_NiagaraData': {'LookAtTargetID': 18}}}])
            before = copy.deepcopy(game); tables = {}
            support = {'clone': mock.Mock(return_value={'LevelSequence': '/Game/private/501010/501011/SEQ_Battle_501011_Master',
                                                        'soundSequence': 'None'}), 'objects': [], 'bytecode': []}
            original = Path.read_bytes
            with mock.patch.object(Path, 'read_bytes', lambda p: json.dumps({'schema': 1, 'skills': {'501010': rule}}).encode()
                                   if p.name == 'native_skill_repairs.json' else original(p)):
                report = native.prepare(tables, [], {501010: [{}]}, root, lambda r: copy.deepcopy(game[r]), mock.Mock(), support)
            self.assertEqual(report[501010]['enemySequence'], 501012)
            for rel in native.RELS:
                self.assertEqual(tables[rel]['set'], [])
                self.assertEqual([r['set']['ID'] for r in tables[rel]['add']], [501011, 501012])
                self.assertEqual(tables[rel]['add'][1]['set'], {'ID': 501012})
            self.assertNotIn('Skill/DT_SkillData', tables)
            self.assertEqual(game, before)

    def explicit_fixture(self, root):
        game, rule, path = self.fixture(root)
        raw = game['Skill/DT_SkillData']['Thwack']
        raw.update(ID=500230, playSequencerId=225042, Cost=15, magnification=24)
        binding = next(iter(game['Asset/Skill/DT_SkillAsset'].values()))
        binding['ID'] = 225042
        game['Asset/Skill/CDT_SkillAsset_Demo']['enemy'] = copy.deepcopy(binding)
        points = {'party': {'ID': 2, 'Position': [0, 500, 0]}, 'enemy': {'ID': 18, 'Position': [0, -500, 0]}}
        game['Battle/Sequencer/DT_BtlSkillPointTargetData'] = points
        rule.update(name='Absolute Zero', sourceBinding=225042, definitionSha256=native.digest(raw),
                    bindingSha256=native.digest(binding), retainEnemyRoute=True, definitionSet={'playSequencerId': -1},
                    pointTargets={str(r['ID']): native.digest(r) for r in points.values()},
                    effectEdits=[{'file': next(iter(rule['files'])), 'function': 'EffectSEQ_Battle_500562',
                                  'set': {'Effect_SpawnTarget_ID': 18}}])
        return game, rule, path

    def invoke_explicit(self, root, game, rule, tables=None, owners=None):
        tables = {} if tables is None else tables
        support = {'clone': mock.Mock(return_value={'LevelSequence': '/Game/private/500230/500231/SEQ_Battle_500231_Master',
                                                    'soundSequence': 'None'}), 'objects': [], 'bytecode': []}
        original = Path.read_bytes
        units = [{'awakening': [[['ActiveSkill', 500230]]]}] if owners is None else owners
        policy = {'schema': 1, 'skills': {'500230': rule}}
        with mock.patch.object(Path, 'read_bytes', lambda p: json.dumps(policy).encode()
                               if p.name == 'native_skill_repairs.json' else original(p)):
            report = native.prepare(tables, [], {500230: units}, root, lambda r: copy.deepcopy(game[r]), mock.Mock(), support)
            destination = Path(root) / 'build/animation-repair-report.json'
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(json.dumps({'schema': 1, 'skills': list(report.values())}))
            with mock.patch.dict(sys.modules, {'_ffr_animation_repair': module('motion_native_test', ROOT/'assets/existing_visions/payload/_ffr_animation_repair.py')}):
                expected = native.expected_definition_edits(root, units, lambda r: copy.deepcopy(game[r]))
        return report, tables, support, expected

    def test_explicit_enemy_pointer_becomes_two_routes_with_enemy_presentation_retained(self):
        with tempfile.TemporaryDirectory() as root:
            game, rule, _ = self.explicit_fixture(root); before = copy.deepcopy(game)
            report, tables, support, expected = self.invoke_explicit(root, game, rule)
            self.assertEqual(report[500230]['enemySequence'], 500232)
            for rel in native.RELS:
                additions = tables[rel]['add']
                self.assertEqual([r['set']['ID'] for r in additions], [500231, 500232])
                self.assertEqual(additions[1]['set'], {'ID': 500232})
                self.assertEqual(additions[1]['cloneFrom'], 'enemy')
                self.assertEqual(tables[rel]['set'], [])
            edits = tables['Skill/DT_SkillData']['set']
            self.assertEqual(edits, [{'row': 'Thwack', 'set': {'playSequencerId': -1}}])
            self.assertEqual(expected, {('Skill/DT_SkillData', 'Thwack'): {'playSequencerId': -1}})
            from test_existing_visions import native as verifier
            original = game['Skill/DT_SkillData']['Thwack']
            built = dict(original, playSequencerId=-1)
            self.assertTrue(verifier.expected_row_change('Skill/DT_SkillData', 'Thwack', original, built, expected, lambda a,b: a==b))
            self.assertFalse(verifier.expected_row_change('Skill/DT_SkillData', 'Thwack', original, dict(built, Cost=0), expected, lambda a,b: a==b))
            event = support['bytecode'][-1]
            self.assertEqual(event['export'], 'EffectSEQ_Battle_500231')
            self.assertEqual(event['set'], {'Effect_SpawnTarget_ID': 18})
            self.assertEqual(game, before)  # MP, damage, hit count, and original bindings stay intact.

    def test_changed_points_future_enemy_route_and_custom_presentation_prevent_pointer_repair(self):
        for case in ('points', 'futureEnemy', 'custom', 'stagedPointer', 'bytes'):
            with self.subTest(case=case), tempfile.TemporaryDirectory() as root:
                game, rule, path = self.explicit_fixture(root); tables = {}; owners = None
                if case == 'points': game['Battle/Sequencer/DT_BtlSkillPointTargetData']['enemy']['Position'] = [0, 500, 0]
                if case == 'futureEnemy': game[native.RELS[1]]['future'] = {'ID': 500232}
                if case == 'custom': owners = [{'skills': {'500230': {'from': 500230}}, 'awakening': [[['ActiveSkill', 500230]]]}]
                if case == 'stagedPointer': tables = {'Skill/DT_SkillData': {'set': [{'row': 'Thwack', 'set': {'playSequencerId': 999}}]}}
                if case == 'bytes': path.write_bytes(b'Changed source')
                before = copy.deepcopy(tables)
                report, tables, support, expected = self.invoke_explicit(root, game, rule, tables, owners)
                support['clone'].assert_not_called(); self.assertEqual(tables, before)
                self.assertEqual(expected, {})
                if case in ('points', 'bytes', 'stagedPointer'):
                    self.assertEqual(report[500230]['status'], 'native_repair_unresolved')

class NativeCasterMotionTests(unittest.TestCase):
    def spec(self):
        return {'pixelSize': [16, 16], 'cells': [{'name': 'own_frame'}],
                'animations': [{'name': 'idle', 'frameCount': 2, 'parts': {}},
                               {'name': 'attack_A', 'frameCount': 17, 'parts': {'part_0': {'Cell': [[0, 'own_frame']], 'Posy': [[0, 3]]}}}]}

    def test_mode_gating_and_exact_recipient_clip(self):
        from test_existing_visions import animation
        for show, full, native_only in ((False, True, True), (True, False, False), (True, True, False), (True, False, True)):
            with self.subTest(show=show, full=full, native=native_only):
                spec = self.spec(); before = copy.deepcopy(spec)
                added = animation.native_caster_motions(spec, {'showUnverified': show, 'useChanges': full, 'useNativeRepairs': native_only})
                self.assertEqual(spec['cells'], before['cells'])
                self.assertEqual(spec['animations'][:2], before['animations'])
                if show and (full or native_only):
                    self.assertEqual(added, ['atk'])
                    self.assertEqual(spec['animations'][-1], dict(before['animations'][1], name='atk'))
                    spec['animations'][-1]['parts']['part_0']['Posy'][0][1] = 999
                    self.assertEqual(spec['animations'][1], before['animations'][1])
                else:
                    self.assertEqual(added, []); self.assertEqual(spec, before)

    def test_explicit_native_clip_wins_and_repeat_is_idempotent(self):
        from test_existing_visions import animation
        spec = self.spec(); modes = {'showUnverified': True, 'useChanges': False, 'useNativeRepairs': True}
        animation.native_caster_motions(spec, modes)
        spec['animations'][-1]['frameCount'] = 50
        before = copy.deepcopy(spec)
        self.assertEqual(animation.native_caster_motions(spec, modes), [])
        self.assertEqual(spec, before)


if __name__=='__main__':unittest.main()
