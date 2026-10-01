import ast
import copy
import io
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
from types import SimpleNamespace
from PIL import Image

from test_existing_visions import ROOT, module, installer, native, fina_installer

PAYLOAD = ROOT / 'assets/existing_visions/payload'
motion = module('motion_repair_tests', PAYLOAD / '_ffr_animation_repair.py')
library = module('library_tests', PAYLOAD / '_ffr_library.py')
with mock.patch.dict('sys.modules', {'ffbe_lb': SimpleNamespace(NEUTRAL_COLOR='#ff6600')}):
    resonance = module('engine_resonance_fixture', ROOT / 'scripts/fixtures/engine_motion/ffbe_resonance.py')


class CapacityTests(unittest.TestCase):
    def test_64_visions_keep_unique_commands_and_portraits_without_modifying_donor_icons(self):
        source = (ROOT / 'scripts/fixtures/crystal_fina/make_vision_mod.py').read_bytes()
        patched = installer.hook_builder(fina_installer.hook_builder(source))
        main = next(n for n in ast.parse(patched).body if isinstance(n, ast.FunctionDef) and n.name == 'main')
        loop = next(n for n in main.body if isinstance(n, ast.For) and ast.unparse(n.iter) == 'UNITS' and any(isinstance(x, ast.Assign) and ast.unparse(x.targets[0]) == 'icon_tag' for x in n.body))
        start = next(i for i, n in enumerate(loop.body) if isinstance(n, ast.Assign) and ast.unparse(n.targets[0]) == 'icon_tag')
        stop = next(i for i, n in enumerate(loop.body) if isinstance(n, ast.Assign) and ast.unparse(n.targets[0]) == 'donor_seal')
        block = ast.Module(body=loop.body[start:stop], type_ignores=[])
        tags = [13104, 13106, 13107, 13109, 13111, 13112, 13114, 13115, 13117, 13119, 13121, 13122, 13126, 13129, 13131, 13132]
        units = [{'id': 13500+i, 'donor': 13125, 'jp': f'Vision{i}', 'command': {'id': 320+i, 'en': f'Commands{i}', 'desc': ''}} for i in range(64)]
        game = {'Skill/DT_CommandSkillData': {'Lightning': {'unitIdToUseSkill': 13125, 'SkillIcon': {'TagName': 'UI.Skill.Command.Icon.13125'}}}}
        for rel in ('UI/Skill/DT_CommandSkillIcon', 'UI/Skill/CDT_SkillIcon'):
            game[rel] = {f'Placeholder{t}': {'Tag': {'TagName': f'UI.Skill.Command.Icon.{t}'}} for t in tags}
            game[rel]['Lightning'] = {'Tag': {'TagName': 'UI.Skill.Command.Icon.13125'}, 'Brush': {'ResourceObject': 'OriginalLightningIcon'}}
        before = copy.deepcopy(game); tables = {}
        def row_by(rel, field, value): return next((k, v) for k, v in game[rel].items() if v.get(field) == value)
        env = {'_ffr_existingvisions': native, 'UNITS': units, 'UNUSED_ICON_TAGS': tags, 'rows': lambda rel: copy.deepcopy(game[rel]),
               'row_by': row_by, 'text': lambda s: s, 'tbl': lambda rel: tables.setdefault(rel, {'add': [], 'set': []}), 'donor_cmd': ('Lightning', game['Skill/DT_CommandSkillData']['Lightning'])}
        for unit in units:
            env.update(u=unit, vid=unit['id']); exec(compile(block, 'command_icon_fixture', 'exec'), env)
        commands = tables['Skill/DT_CommandSkillData']['add']
        self.assertEqual(len(commands), 64); self.assertEqual(len({r['set']['ID'] for r in commands}), 64)
        self.assertEqual([r['set']['unitIdToUseSkill'] for r in commands], [u['id'] for u in units])
        self.assertTrue(all(r['set']['SkillIcon.TagName'] == 'UI.Skill.Command.Icon.13125' for r in commands[16:]))
        for rel in ('UI/Skill/DT_CommandSkillIcon', 'UI/Skill/CDT_SkillIcon'):
            self.assertEqual(len(tables[rel]['set']), 16)
            self.assertNotIn('Lightning', [r['row'] for r in tables[rel]['set']])
        self.assertEqual(game, before)


class MotionTests(unittest.TestCase):
    def setUp(self):
        motion._attempted.clear()
        self.temp = tempfile.TemporaryDirectory(); self.root = Path(self.temp.name); self.form = '100000107'
        png = io.BytesIO(); Image.new('RGBA', (3, 1), (50, 60, 70, 255)).save(png, format='PNG')
        self.cgg = ('\n'.join(f'0,1,0,0,0,0,100,0,{i},0,1,1,0' for i in range(3))+'\n').encode()
        self.assets = {f'unit_animated/unit_anime_{self.form}.png': png.getvalue(), f'unit_animated_csv/unit_cgg_{self.form}.csv': self.cgg,
                       f'unit_animated_csv/unit_idle_cgs_{self.form}.csv': b'0,0,0,1\n',
                       f'unit_animated_csv/unit_atk1_cgs_{self.form}.csv': b'1,0,0,2\n',
                       f'unit_animated_csv/unit_atk2_cgs_{self.form}.csv': b'2,0,0,3\n',
                       f'unit_animated_csv/unit_magic_atk_cgs_{self.form}.csv': b'2,0,0,4\n'}
        self.entry = {'atlas': motion.blob_sha(png.getvalue()), 'cgg': motion.blob_sha(self.cgg), 'idle': motion.blob_sha(b'0,0,0,1\n'),
                      'atk1': motion.blob_sha(b'1,0,0,2\n'), 'atk2': motion.blob_sha(b'2,0,0,3\n'), 'magic_atk': motion.blob_sha(b'2,0,0,4\n')}
        self.source = {'schema': 1, 'repository': 'DaddyRaegen/ffbe_asset_dump', 'commit': 'a'*40, 'forms': {self.form: self.entry}}
        for path in self.assets:
            if '_cgs_' not in path or '_idle_' in path: (self.root / Path(path).name).write_bytes(self.assets[path])
    def tearDown(self): self.temp.cleanup()
    def download(self, path, digest, source):
        self.assertEqual(motion.blob_sha(self.assets[path]), digest); return self.assets[path]
    def test_matching_sheet_recovers_missing_attack_and_magic_without_replacing_existing_files(self):
        before = {p: p.read_bytes() for p in self.root.iterdir()}
        self.assertEqual(set(motion.repair_form(self.root, self.form, self.source, self.download)), {'atk1','atk2','magic_atk'})
        self.assertTrue(all(p.read_bytes() == data for p, data in before.items()))
        self.assertEqual(motion.repair_form(self.root, self.form, self.source, mock.Mock(side_effect=AssertionError('should be cached'))), [])
    def test_edited_frames_or_atlas_and_offline_errors_keep_original_pack(self):
        (self.root/f'unit_cgg_{self.form}.csv').write_bytes(b'0,0\n')
        self.assertEqual(motion.repair_form(self.root, self.form, self.source, self.download), [])
        self.assertFalse((self.root/f'unit_atk1_cgs_{self.form}.csv').exists())
        (self.root/f'unit_cgg_{self.form}.csv').write_bytes(self.cgg)
        motion._attempted.clear()
        Image.new('RGBA',(3,1),(100,100,100,255)).save(self.root/f'unit_anime_{self.form}.png')
        self.assertEqual(motion.repair_form(self.root,self.form,self.source,self.download),[])
        (self.root/f'unit_anime_{self.form}.png').write_bytes(self.assets[f'unit_animated/unit_anime_{self.form}.png'])
        motion._attempted.clear()
        self.assertEqual(motion.repair_form(self.root, self.form, self.source, mock.Mock(side_effect=OSError('offline'))), [])
        self.assertEqual((self.root/f'unit_cgg_{self.form}.csv').read_bytes(),self.cgg)
    def test_existing_alias_files_and_invalid_remote_frames_are_not_replaced(self):
        custom=self.root/f'unit_magicatk_cgs_{self.form}.csv'; custom.write_bytes(b'1,0,0,99\n')
        self.assets[f'unit_animated_csv/unit_atk1_cgs_{self.form}.csv']=b'100,0,0,1\n'
        self.entry['atk1']=motion.blob_sha(b'100,0,0,1\n')
        self.assertEqual(motion.repair_form(self.root, self.form, self.source, self.download),[])
        self.assertEqual(custom.read_bytes(),b'1,0,0,99\n');self.assertFalse((self.root/f'unit_atk1_cgs_{self.form}.csv').exists())
    def test_real_engine_converter_plays_recovered_atk1_atk2_and_magic_instead_of_idle(self):
        motion.repair_form(self.root, self.form, self.source, self.download)
        engine=self.root/'engine'; tools=engine/'tools'; frames=tools/'ffbe2ss6'; frames.mkdir(parents=True)
        for name in ('ffbe_frames.py','build_sprites.py'):shutil.copyfile(ROOT/'scripts/fixtures/engine_motion'/name,frames/name)
        for name in ('_ffr_animation_repair.py','_ffr_build_sprites.py'):shutil.copyfile(PAYLOAD/name,tools/name)
        out=self.root/'converted'
        result=subprocess.run([sys.executable,str(tools/'_ffr_build_sprites.py'),str(self.root),self.form,'13520',str(out)],capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr)
        spec=json.loads((out/'battle/spec.json').read_text()); anims={a['name']:a for a in spec['animations']}
        self.assertEqual(anims['idle']['frameCount'],1);self.assertEqual(anims['attack_A']['frameCount'],2)
        self.assertEqual(anims['attack_B']['frameCount'],3);self.assertEqual(anims['magic_attack']['frameCount'],4)
        self.assertNotEqual(anims['attack_A']['parts']['part_0']['Cell'],anims['idle']['parts']['part_0']['Cell'])
        (self.root/f'unit_atk_cgs_{self.form}.csv').write_bytes(b'2,0,0,7\n')
        result=subprocess.run([sys.executable,str(tools/'_ffr_build_sprites.py'),str(self.root),self.form,'13520',str(out)],capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr)
        anims={a['name']:a for a in json.loads((out/'battle/spec.json').read_text())['animations']}
        self.assertEqual(anims['attack_A']['frameCount'],7) # A valid existing primary attack keeps its own motion.


class SequenceTests(unittest.TestCase):
    def test_missing_selected_heal_and_attack_get_timelines_with_correct_ids_and_unchanged_mechanics(self):
        game={'Skill/DT_SkillData':{'heal':{'ID':240020,'skillAttrType':'Magic','DamageType':'None','defaultTargetRelation':'Friendlies','hitCount':1,'magnification':500},
                                  'attack':{'ID':400120,'skillAttrType':'Ability','DamageType':'Physic','defaultTargetRelation':'Enemies','hitCount':2,'magnification':15}},
              'Asset/Skill/DT_SkillAsset':{'shell':{'ID':440111}},'Asset/Skill/CDT_SkillAsset_Demo':{'shell':{'ID':440111}},
              'Battle/Sequencer/DT_BtlHitEffectData':{'template':{'ID':449999}}}
        before=copy.deepcopy(game); tables={};clones=[];jobs=[]
        unit={'awakening':[[['ActiveSkill',240020],['ActiveSkill',400120]]],'synchro':[[['ActiveSkill',240020]]],'skills':{}}
        with tempfile.TemporaryDirectory() as temp, mock.patch.dict('sys.modules',{'ffbe_resonance':resonance}):
            source=Path(temp)/'extracted/legacy'/(resonance.SHELL+'.uasset')
            def extract(folder):source.parent.mkdir(parents=True,exist_ok=True);source.write_bytes(b'explicit timeline file fixture')
            result=motion.prepare_sequences(tables,clones,jobs,[unit,copy.deepcopy(unit)],temp,lambda rel:copy.deepcopy(game[rel]),extract)
            self.assertEqual(result,[240020,400120]);self.assertEqual(len(jobs),2)
            for sid,job in zip(result,jobs):
                events=job['plan']['events']; reactions=[e['set']['Other_Reaction_Id'] for e in events if e['set']['EventType']=='OtherReaction']
                self.assertTrue(reactions);self.assertTrue(all(x==sid for x in reactions))
                names=[e['set'].get('Unit_PlayAnimByName_AnimationName') for e in events]
                self.assertIn('magic_attack' if sid==240020 else 'attack_A',names);self.assertNotIn('LB1',names)
            self.assertNotIn('Skill/DT_SkillData',tables);self.assertTrue(all(not t['set'] for t in tables.values()))
            count=len(jobs);self.assertEqual(motion.prepare_sequences(tables,clones,jobs,[unit],temp,lambda rel:copy.deepcopy(game[rel]),extract),[])
            self.assertEqual(len(jobs),count)
        self.assertEqual(game,before)


class DuplicateTests(unittest.TestCase):
    def test_full_mechanics_and_original_references_protect_variants_and_equipped_entries(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp); base=root/'extracted/rows'
            tables={'Skill/DT_SkillData':{'a':{'ID':10,'Name':'one','SortId':10,'magnification':50,'effectBundleList':[]},
                                        'b':{'ID':20,'Name':'two','SortId':20,'magnification':50,'effectBundleList':[]},
                                        'c':{'ID':30,'Name':'three','SortId':30,'magnification':80,'effectBundleList':[]}},
                    'Skill/DT_PassiveSkillData':{'a':{'ID':101,'equipCost':20,'effectBundleList':[{'effectId':1}]},
                                               'b':{'ID':102,'equipCost':20,'effectBundleList':[{'effectId':2}]},
                                               'c':{'ID':103,'equipCost':40,'effectBundleList':[{'effectId':2}]}},
                    'Skill/DT_SkillEffectData':{'one':{'ID':1,'ParamList':[5,20]},'two':{'ID':2,'ParamList':[5,20]}},
                    'Unit/OriginalLoadout':{'Rain':{'ActiveSkills':[20],'Passives':[102]}}}
            for rel,data in tables.items():
                p=base/(rel+'.json');p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps({'rows':data}))
            cat={'skills':[{'id':n,'name':'Fire'} for n in (10,20,30)],'passives':[{'id':n,'name':'Boost'} for n in (101,102,103)]}
            before=copy.deepcopy(cat); result=library.analyze(cat,root)
            self.assertEqual(result['groups'],{'skills':[[10,20]],'passives':[[101,102]]})
            self.assertIn(20,result['protected']['skills']);self.assertIn(102,result['protected']['passives'])
            self.assertEqual(result['variants']['skills']['10'], [{'field':'magnification','value':50,'missing':False}])
            self.assertEqual(result['variants']['skills']['30'], [{'field':'magnification','value':80,'missing':False}])
            self.assertEqual(result['variants']['passives']['101'], [{'field':'equipCost','value':20,'missing':False}])
            self.assertEqual(result['variants']['passives']['103'], [{'field':'equipCost','value':40,'missing':False}])
            self.assertEqual(cat,before)

    def test_variant_details_cover_hidden_fields_effect_parameters_and_missing_values(self):
        common = {'effectBundleList': [{'effectId': {'mechanics': {'EffectType': 'Counter', 'ParamList': [6, 400120]}}}]}
        alternative = copy.deepcopy(common)
        alternative['effectBundleList'][0]['effectId']['mechanics']['ParamList'][1] = -1
        alternative['onlyWhenFullHP'] = True
        result = library.variant_fields({'counter': [(10, common), (20, alternative)]})
        self.assertEqual(result['10'][0], {'field':'effectBundleList.0.effectId.mechanics.ParamList.1', 'value':400120, 'missing':False, 'effectType':'Counter'})
        self.assertEqual(result['20'][0]['value'], -1)
        self.assertTrue(result['10'][1]['missing'])
        self.assertEqual(result['20'][1]['value'], True)
        self.assertNotIn('EffectType', [r['field'] for r in result['10']])
        self.assertEqual(library.variant_fields({'same': [(1,common),(2,copy.deepcopy(common))]}), {})


if __name__=='__main__':unittest.main()
