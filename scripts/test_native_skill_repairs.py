"""Audited own-skill routes preserve native definitions and unrelated tracks."""
import copy
import json
import hashlib
from pathlib import Path
import tempfile
import unittest
from unittest import mock
from test_existing_visions import ROOT, module
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


if __name__=='__main__':unittest.main()
