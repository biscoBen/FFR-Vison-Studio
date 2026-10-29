"""Read-only native definition export, exact filtering, patches and split uploads."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile

from restore_reference_chunks import restore

ROOT=Path(__file__).resolve().parents[1]
FOLDER=ROOT/'scripts/reference/treasure-counter'
SCRIPT=FOLDER/'Collect Treasure Counter Reference.ps1'
NAMES=[SCRIPT.name,'Collect Treasure Counter Reference.cmd','Choose Game Folder.cmd','Read me.txt','Collect Small Followup.cmd']
PWSH=shutil.which('pwsh')

class BundleTests(unittest.TestCase):
    def test_bundle_contains_the_exact_reviewed_helpers(self):
        with zipfile.ZipFile(FOLDER/'Treasure-Counter-Reference.zip') as archive:
            self.assertEqual(archive.namelist(),NAMES)
            self.assertIsNone(archive.testzip())
            for name in NAMES:
                self.assertEqual(archive.read(name).decode().replace('\r\n','\n'),(FOLDER/name).read_text())

@unittest.skipUnless(PWSH and sys.platform!='win32','PowerShell and POSIX tool fixture required')
class CollectorTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);self.engine=self.root/"Studio & user's/engine"
        self.game=self.root/"Full game & user's";self.paks=self.game/'FFRS/Content/Paks'
        self.output=self.root/'output';self.fixture=self.root/'fixtures'
        self.level='FFRS/Content/Map/Dng/01Gra/01Gra_40/Dng_01Gra_40_01_GD.umap'
        self.field='FFRS/Content/BP/Map/Gimmick/BP_MapGimmick_FieldItem.uasset'
        self.selected={self.level:b'gameplay actor definitions',self.field:b'native field item blueprint',
            'FFRS/Content/Map/Dng/01Gra/01Gra_40/Dng_01Gra_40_PL.umap':b'level streaming definitions',
            'FFRS/Content/BP/Event/GimmickEvent/BP_GimmickEvent_FieldItem.uasset':b'pickup state flow',
            'FFRS/Content/BP/Event/Tutorial/BP_Tutorial_Fragment.uasset':b'fragment flow',
            'FFRS/Content/UI/Field/MiniMap/Widget/WBP_MiniMap.uasset':b'map widget',
            'FFRS/Content/Datatable/Map/MapData/DT_MapData_01Gra.uasset':b'map groups'}
        self.excluded={
            'FFRS/Content/Map/Dng/01Gra/01Gra_40/Dng_01Gra_40_01_BG.umap':b'background geometry',
            'FFRS/Content/Env/Dng/Textures/private.uasset':b'textures',
            'FFRS/Content/BP/Map/Gimmick/Animation/ABP_Chest.uasset':b'animation',
            'FFRS/Content/Sound/music.uasset':b'music'}
        for name,raw in {**self.selected,**self.excluded}.items():self.write(self.fixture/name,raw)
        for name in ('global.utoc','global.ucas','FFRS-Windows.utoc','FFRS-Windows.ucas','FFRS-Windows.pak',
                     'FFRS-Windows_1_P.utoc','FFRS-Windows_1_P.ucas'):
            self.write(self.paks/name,name.encode())
        self.write(self.paks/'~mods/private.pak',b'private mod')
        self.write(self.paks/'FFRS-Windows_MyMod.utoc',b'private mod named similarly')
        self.write(self.game/'FFRS/Saved/SaveGames/private.sav',b'private save')
        self.write(self.engine/'config.json',json.dumps({'gameRoot':str(self.game),'secret':'private'}).encode())
        self.write(self.engine/'extracted/Mappings.usmap',b'native mappings')
        self.ret=self.engine/'tools/retoc/retoc.exe';self.set_tool()
        self.env=dict(os.environ,USERPROFILE=str(self.root),LOCALAPPDATA=str(self.root/'Local'),
            XDG_CONFIG_HOME=str(self.root/'config'),XDG_CACHE_HOME=str(self.root/'cache'),XDG_DATA_HOME=str(self.root/'data'))

    def write(self,path,raw):path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw)
    def set_tool(self,failed=False,empty=False,omit=None):
        self.write(self.ret,f'''#!{sys.executable}
import pathlib,sys,shutil
args=sys.argv[1:]
view=pathlib.Path(args[-1] if args[0]=='list' else args[-2])
assert all(p.stat().st_ino==(pathlib.Path({str(self.paks)!r})/p.name).stat().st_ino for p in view.iterdir())
assert not any('MyMod' in p.name or p.is_dir() for p in view.iterdir())
assert (view/'global.utoc').is_file() and (view/'FFRS-Windows_1_P.utoc').is_file()
source=pathlib.Path({str(self.fixture)!r})
if args[0]=='list':
 assert args[1]=='--path'
 if not {empty!r}:
  for p in sorted(source.rglob('*')):
   if p.is_file():print('FFRS-Windows hash ExportBundleData ../../../'+p.relative_to(source).as_posix())
else:
 assert args[:2]==['to-legacy','--no-shaders']
 filters=args[3:-2:2];assert 0<len(filters)<=24
 assert not any('/Env/' in p or '/Sound/' in p or '_BG' in p or '/Animation/' in p for p in filters)
 for p in source.rglob('*'):
  if p.is_file() and p.relative_to(source).as_posix()!={omit!r} and any(f in p.relative_to(source).as_posix() for f in filters):
   out=pathlib.Path(args[-1])/p.relative_to(source);out.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,out)
 print('info: Extracted 0 (1 failed)' if {failed!r} else 'info: Extracted 7 (0 failed)')
'''.encode());self.ret.chmod(0o755)
    def digest(self,path):
        return {p.relative_to(path).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in path.rglob('*') if p.is_file()}
    def run_helper(self,success=True,*extra,auto=False,input_text=None):
        before=self.digest(self.game),self.digest(self.engine)
        arguments=[PWSH,'-NoProfile','-File',str(SCRIPT),'-OutputRoot',str(self.output),*extra]
        if not auto:arguments+=['-EnginePath',str(self.engine)]
        result=subprocess.run(arguments,capture_output=True,text=True,env=self.env,timeout=60,input=input_text)
        self.assertEqual(result.returncode,0 if success else 1,result.stdout+result.stderr)
        self.assertEqual(before,(self.digest(self.game),self.digest(self.engine)))
        self.assertEqual(list((self.game/'FFRS/Content').glob('StudioTreasureReference-*')),[])
        return result
    def merged(self):
        folder=self.root/'merged';archives=sorted(self.output.glob('*.zip'));self.assertTrue(archives)
        for path in archives:
            self.assertLess(path.stat().st_size,25*1024*1024)
            with zipfile.ZipFile(path) as archive:self.assertIsNone(archive.testzip());archive.extractall(folder)
        restore(folder);return folder
    def test_collects_only_native_definitions_with_global_and_patch_dependencies(self):
        self.run_helper();folder=self.merged()
        for name,raw in self.selected.items():self.assertEqual((folder/'legacy'/name).read_bytes(),raw)
        for name in self.excluded:self.assertFalse((folder/'legacy'/name).exists())
        self.assertNotIn('private',(folder/'reference.json').read_text())
        self.assertFalse(any(p.suffix in ('.sav','.dll','.pak','.ucas','.utoc') for p in folder.rglob('*')))
    def test_export_supports_metadata_batches_beyond_windows_argument_limit(self):
        for i in range(50):self.write(self.fixture/f'FFRS/Content/Map/Dng/99Test/Dng_{i:03}_GD.umap',b'metadata')
        result=self.run_helper();self.assertIn('batch 3/',result.stdout);self.merged()
    def test_failure_or_missing_definitions_never_produces_success_zip(self):
        self.set_tool(failed=True);self.run_helper(False);self.assertFalse(list(self.output.glob('*.zip')))
        self.set_tool(empty=True);result=self.run_helper(False);self.assertIn('not found',result.stdout)
        self.assertFalse(list(self.output.glob('*.zip')))
    def test_missing_mappings_preserves_sources_and_produces_no_success_zip(self):
        (self.engine/'extracted/Mappings.usmap').unlink();result=self.run_helper(False)
        self.assertIn('mappings were not found',result.stdout);self.assertFalse(list(self.output.glob('*.zip')))
    def test_silent_partial_conversion_cannot_be_reported_as_complete(self):
        self.set_tool(omit=self.level);result=self.run_helper(False)
        self.assertIn('Incomplete definition export',result.stdout);self.assertFalse(list(self.output.glob('*.zip')))
    def test_finds_localappdata_engine_and_uses_its_configured_game_without_a_drive_guess(self):
        target=self.root/'Local/FFR Vision Studio/engine';shutil.copytree(self.engine,target);self.engine=target
        self.run_helper(auto=True);self.merged()
    def test_saved_demo_path_recovers_to_a_full_game_prompt_without_rewriting_settings(self):
        config=self.engine/'config.json';config.write_text(json.dumps({'gameRoot':str(self.root/'FINAL FANTASY RESONANCE DEMO')}))
        result=self.run_helper(input_text=str(self.game)+'\n')
        self.assertIn('saved demo or unavailable',result.stdout)
        self.assertIn('Using game folder: '+str(self.game),result.stdout);self.merged()
    def test_invalid_saved_settings_recover_to_the_full_game_prompt(self):
        (self.engine/'config.json').write_text('{invalid')
        result=self.run_helper(input_text=str(self.game)+'\n')
        self.assertIn('settings could not be read',result.stdout);self.merged()
    def test_full_game_inside_a_demo_named_parent_is_not_rejected(self):
        target=self.root/'FINAL FANTASY RESONANCE DEMO archive/Full game'
        shutil.copytree(self.game,target);self.game=target;self.paks=target/'FFRS/Content/Paks';self.set_tool()
        (self.engine/'config.json').write_text(json.dumps({'gameRoot':str(target)}))
        self.run_helper();self.merged()
    def test_manual_folder_choice_overrides_a_different_valid_saved_game(self):
        old_game=self.game;target=self.root/'Another full game';shutil.copytree(old_game,target)
        self.game=target;self.paks=target/'FFRS/Content/Paks';self.set_tool()
        result=self.run_helper(True,'-ChooseGamePath',input_text=str(target)+'\n')
        self.assertIn('Using game folder: '+str(target),result.stdout);self.merged()
    def test_large_native_level_is_split_and_restored_exactly(self):
        name=self.level.replace('.umap','.uexp');raw=os.urandom(23*1024*1024);self.write(self.fixture/name,raw)
        self.run_helper();self.assertEqual((self.merged()/'legacy'/name).read_bytes(),raw)
    def test_rejects_demo_before_any_export(self):
        result=self.run_helper(False,'-GamePath',str(self.root/'FINAL FANTASY RESONANCE DEMO'))
        self.assertIn('rather than the demo',result.stdout);self.assertFalse(self.output.exists())

    def followup_assets(self):
        result={self.field:self.selected[self.field]}
        for identity in (87,93,94,96,97,112):
            for kind in ('PL','GD'):
                name=f'FFRS/Content/Map/Event/Com/00Eve_{identity}/Event_00Eve_{identity}_{kind}.umap'
                result[name]=b'event dungeon '+str(identity).encode()
        for name in (
            'FFRS/Content/UI/MainMenu/Common/Key/KeyGuide/WBP_KeyGuide.uasset',
            'FFRS/Content/UI/Battle/KeyGuide/Speed/WBP_BtlKeyGuide_Speed.uasset',
            'FFRS/Content/UI/Battle/Command/Data/DA_BtlCmd.uasset',
            'FFRS/Content/UI/Battle/Command/ViewModel/VM_BtlCmd.uasset',
            'FFRS/Content/BP/Map/Unit/BP_MapUnit_Player.uasset',
            'FFRS/Plugins/EnhancedUI/Content/Foundation/Panel/DirGrid/WBP_DirectionGridPanel.uasset'):
            result[name]=b'native input widget'
        for name,raw in result.items():self.write(self.fixture/name,raw)
        return result

    def test_followup_exports_only_six_event_dungeons_and_native_input_widgets(self):
        expected=self.followup_assets()
        self.write(self.fixture/'FFRS/Content/Map/Event/Com/00Eve_80/Event_00Eve_80_PL.umap',b'unrelated event')
        self.run_helper(True,'-Followup');folder=self.merged()
        actual=self.digest(folder/'legacy')
        self.assertEqual(set(actual),set(expected))
        for name,raw in expected.items():self.assertEqual((folder/'legacy'/name).read_bytes(),raw)
        self.assertTrue(json.loads((folder/'reference.json').read_text())['followup'])

    def test_followup_missing_special_floor_or_status_widget_fails_closed(self):
        self.followup_assets()
        missing=self.fixture/'FFRS/Content/Map/Event/Com/00Eve_112/Event_00Eve_112_PL.umap'
        raw=missing.read_bytes();missing.unlink()
        result=self.run_helper(False,'-Followup');self.assertIn('Missing special dungeon 112',result.stdout)
        self.assertFalse(list(self.output.glob('*.zip')))
        self.write(missing,raw)
        (self.fixture/'FFRS/Plugins/EnhancedUI/Content/Foundation/Panel/DirGrid/WBP_DirectionGridPanel.uasset').unlink()
        result=self.run_helper(False,'-Followup');self.assertIn('Native status widgets',result.stdout)
        self.assertFalse(list(self.output.glob('*.zip')))

if __name__=='__main__':unittest.main()
