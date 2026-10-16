"""Enemy-only Cling gets an isolated ally route; native enemy/groups are retained."""
import copy
import json
import tempfile
from pathlib import Path
import unittest
from unittest import mock
from test_existing_visions import animation as motion


def fixture():
    def prop(name,value):return {'Name':name,'Value':value}
    def key(index):return {'Value':[prop('Ptrs',[prop('Function',index)])]}
    view={'Imports':[{'ObjectName':'MovieSceneEventTrack'}], 'Exports':[
      {'ClassIndex':-1,'Data':[prop('bIsEvalDisabled',True),prop('Sections',[{'Value':2}])]},
      {'Data':[prop('EventChannel',[prop('KeyValues',[key(1),key(2)])])]}]}
    dump={'1:attack':{'EventType':'UnitPlayAnimByName','Unit_PlayAnimByName_AnimationName':'atk'},
          '2:idle':{'EventType':'UnitPlayAnimByName','Unit_PlayAnimByName_AnimationName':'idle'}}
    asset={'ID':500912,'LevelSequence':'/Game/Sequencer/Battle/EnemySkill/500910/500912/SEQ_Battle_500912_Master',
           'soundSequence':'/Game/Sequencer/Battle/EnemySkill/500910/500912/Track/SEQ_Battle_500912_Sound_001'}
    game={rel:{'Cling enemy':copy.deepcopy(asset)} for rel in ['Asset/Skill/DT_SkillAsset','Asset/Skill/CDT_SkillAsset_Demo']}
    game['Skill/DT_SkillData']={'Cling':{'ID':500910,'hasUnit':'All','skillAttrType':'Ability','DamageType':'Physic','TargetType':'Group','hitCount':1,'magnification':12}}
    return game,view,dump


class AllyMonsterAnimationTests(unittest.TestCase):
    def test_private_ally_route_enables_only_cast_track_and_preserves_every_original_row(self):
        game,view,dump=fixture();before=copy.deepcopy(game)
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);cut=root/'extracted/legacy/FFRS/Content/Sequencer/Battle/EnemySkill/500910/500912/Track/SEQ_Battle_500912_Cut_001.uasset'
            cut.parent.mkdir(parents=True);cut.write_bytes(b'explicit fixture')
            clone=mock.Mock(return_value={'LevelSequence':'/Game/private/ClingAlly','soundSequence':'/Game/private/ClingSound'})
            support={'dumps':lambda p:(copy.deepcopy(view),copy.deepcopy(dump)),'clone':clone,'objects':[],'bytecode':[]}
            tables={};clones=[];selected={500910:[{'id':13503,'awakening':[[['ActiveSkill',500910]]]}]}
            report=motion.prepare_ally_cling(tables,clones,selected,root,lambda rel:copy.deepcopy(game[rel]),mock.Mock(),support)
            self.assertEqual(report['sequence'],500911)
            self.assertEqual(set(tables),{'Asset/Skill/DT_SkillAsset','Asset/Skill/CDT_SkillAsset_Demo'})
            for rel in tables:
                self.assertEqual(tables[rel]['set'],[])
                self.assertEqual(tables[rel]['add'][0]['set']['ID'],500911)
                self.assertEqual(tables[rel]['add'][0]['cloneFrom'],'Cling enemy')
            args=clone.call_args.args
            self.assertEqual(args[1:4],(500912,500910,500911))
            edits=args[8]['cut'];self.assertEqual(len(edits),1)
            self.assertTrue(edits[0]['enable_track'])
            self.assertEqual(edits[0]['set'],{'Unit_PlayAnimByName_AnimationName':'attack_A'})
            self.assertEqual(game,before)
            self.assertIsNone(motion.prepare_ally_cling(tables,clones,selected,root,lambda r:game[r],mock.Mock(),support))
            clone.assert_called_once()

    def test_sequence_preparation_reports_cling_repair_before_existing_enemy_binding_skip(self):
        game,view,dump=fixture()
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);cut=root/'extracted/legacy/FFRS/Content/Sequencer/Battle/EnemySkill/500910/500912/Track/SEQ_Battle_500912_Cut_001.uasset'
            cut.parent.mkdir(parents=True);cut.touch()
            support={'dumps':lambda p:(view,dump),'clone':mock.Mock(return_value={'LevelSequence':'/Game/private/ClingAlly'}),'objects':[],'bytecode':[]}
            tables={};jobs=[]
            with mock.patch.object(motion,'NativeAnimations',return_value=None):
                repaired=motion.prepare_sequences(tables,[],jobs,[{'awakening':[[['ActiveSkill',500910]]]}],root,
                                                  lambda rel:copy.deepcopy(game[rel]),mock.Mock(),support)
            self.assertEqual(repaired,[500910]);self.assertEqual(jobs,[])
            report=json.loads((root/'build/animation-repair-report.json').read_text())
            self.assertEqual(report['skills'][0]['status'],'native_ally_variant')
            self.assertFalse(report['skills'][0]['inGameValidated'])

    def test_future_native_route_custom_override_and_changed_track_are_not_overwritten(self):
        game,view,dump=fixture()
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);cut=root/'extracted/legacy/FFRS/Content/Sequencer/Battle/EnemySkill/500910/500912/Track/SEQ_Battle_500912_Cut_001.uasset';cut.parent.mkdir(parents=True);cut.touch()
            clone=mock.Mock();support={'dumps':lambda p:(view,dump),'clone':clone,'objects':[],'bytecode':[]}
            rows=lambda rel:copy.deepcopy(game[rel]);selected={500910:[{}]}
            game['Asset/Skill/DT_SkillAsset']['future native']={'ID':500911}
            self.assertIsNone(motion.prepare_ally_cling({},[],selected,root,rows,mock.Mock(),support))
            del game['Asset/Skill/DT_SkillAsset']['future native']
            self.assertIsNone(motion.prepare_ally_cling({},[],{500910:[{'skills':{'500910':{'from':1}}}]},root,rows,mock.Mock(),support))
            dump['1:attack']['Unit_PlayAnimByName_AnimationName']='unknown_new_motion'
            with self.assertRaisesRegex(ValueError,'caster track changed'):
                motion.prepare_ally_cling({},[],selected,root,rows,mock.Mock(),support)
            clone.assert_not_called()


if __name__=='__main__':unittest.main()
