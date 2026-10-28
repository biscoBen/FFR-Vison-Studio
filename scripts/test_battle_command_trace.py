"""F8-only survey: retains native callbacks and preserves other installed mods."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
import zipfile

ROOT=Path(__file__).resolve().parents[1]
FOLDER=ROOT/'scripts/reference/battle-commands'
NAMES=['Install Battle Commands.cmd','Collect Battle Commands.cmd','Disable Battle Commands.cmd',
       'Battle Command Diagnostics.ps1','main.lua','Read me.txt']
PWSH=shutil.which('pwsh')


class ObserverTests(unittest.TestCase):
    def test_download_matches_reviewed_sources(self):
        with zipfile.ZipFile(FOLDER/'Battle-Command-Diagnostics.zip') as z:
            self.assertEqual(z.namelist(),NAMES)
            self.assertIsNone(z.testzip())
            for name in NAMES:self.assertEqual(z.read(name),(FOLDER/name).read_bytes())

    def test_f8_only_retained_callbacks_read_saved_commands_across_battles(self):
        from lupa.lua54 import LuaRuntime
        lua=LuaRuntime()
        lua.execute("""
            logs={};registered=setmetatable({},{__mode='v'});Key={F8=119};queueCount=0
            function print(v) logs[#logs+1]=v end
            function RegisterKeyBind(k,fn) assert(k==Key.F8);registered.key=fn end
            function ExecuteInGameThread(fn) queueCount=queueCount+1;registered.queue=fn end
            function array(v)
                return {ForEach=function(_,fn)
                    for i,value in ipairs(v) do fn(i,{get=function() return value end}) end
                end}
            end
            function object(n,fields)
                fields=fields or {};fields.IsValid=function() return true end
                fields.GetFullName=function() return n end
                return fields
            end
            signatureReads=0
            function StaticFindObject(path)
                assert(path:find('/Script/mucha.',1,true)==1)
                return object(path,{ForEachProperty=function(_,fn)
                    signatureReads=signatureReads+1
                    fn(object('IntProperty '..path..':exampleParameter'))
                end})
            end
            savedCommand={actionId=50100,isUseItem=false,targetUnitUniqueIdList=array({17}),ParameterList=array({})}
            save=object('CPP_MuchaGameSaveData Session',{
                unitParameterList=array({{UnitId=1001,btlCmdData={CommandId=4,cmdDataList=array({savedCommand})}}})})
            view=object('CPP_VM_Battle View',{bIsDisplayBattleWidget=true,bIsEvent=false,bIsSequenceUIVisible=true,
                IsAutoBattle=function() return false end})
            function FindAllOf(class)
                if class=='CPP_MuchaGameSaveData' then return {save} end
                if class=='CPP_VM_Battle' then return {view} end
                return {}
            end
        """)
        lua.execute((FOLDER/'main.lua').read_text())
        lua.execute("""
            collectgarbage('collect');assert(type(registered.key)=='function')
            assert(queueCount==0 and signatureReads==0) -- No startup observation or timer.
            registered.key();registered.key();assert(queueCount==1) -- Coalesce pending F8 presses.
            collectgarbage('collect');assert(type(registered.queue)=='function');registered.queue()
            assert(signatureReads>10)
            assert(table.concat(logs):find('unit=1001 | action=50100',1,true))
            -- Battle UI instance changes; persistent unit memory is observed separately.
            view=object('CPP_VM_Battle NextBattle',{bIsDisplayBattleWidget=true,bIsEvent=false,
                bIsSequenceUIVisible=true,IsAutoBattle=function() return false end})
            registered.key();collectgarbage('collect');registered.queue()
            assert(table.concat(logs):find('BOOKMARK_END | number=2',1,true))
            assert(savedCommand.actionId==50100 and savedCommand.isUseItem==false)
            for i=3,10 do registered.key();if i<=8 then registered.queue() end end
            assert(FFRStudioBattleCommandObserver.bookmarks==8 and queueCount==8)
        """)

    def test_missing_native_objects_are_reported_without_writes_or_timer(self):
        from lupa.lua54 import LuaRuntime
        lua=LuaRuntime()
        lua.execute("""
            logs={};Key={F8=119};function print(v) logs[#logs+1]=v end
            function RegisterKeyBind(k,fn) key=fn end
            function ExecuteInGameThread(fn) fn() end
            function StaticFindObject() return nil end
            function FindAllOf() return {} end
        """)
        lua.execute((FOLDER/'main.lua').read_text())
        lua.execute("key();assert(table.concat(logs):find('FUNCTION_MISSING',1,true));assert(FFRStudioBattleCommandObserver.bookmarks==1)")


@unittest.skipUnless(PWSH,'PowerShell required')
class InstallerTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);self.game=self.root/"Game & user's folder"
        self.binary=self.game/'FFRS/Binaries/Win64'
        self.mods=self.binary/'ue4ss/Mods';self.mods.mkdir(parents=True)
        (self.binary/'ue4ss/UE4SS.dll').write_bytes(b'existing loader')
        self.other=self.mods/'FFRStudioFieldLeader/Scripts/main.lua'
        self.other.parent.mkdir(parents=True);self.other.write_bytes(b'existing Studio runtime')
        self.folder=self.mods/'FFRStudioBattleCommandTrace'
        self.output=self.root/'reports'
        self.env=dict(os.environ,XDG_CACHE_HOME=str(self.root/'cache'),
                      XDG_CONFIG_HOME=str(self.root/'config'),XDG_DATA_HOME=str(self.root/'data'))

    def run_action(self,action,success=True):
        r=subprocess.run([PWSH,'-NoProfile','-File',str(FOLDER/'Battle Command Diagnostics.ps1'),
                          '-Action',action,'-GamePath',str(self.game),'-OutputRoot',str(self.output),'-NoPrompt'],
                         env=self.env,text=True,capture_output=True,timeout=20)
        self.assertEqual(r.returncode,0 if success else 1,r.stdout+r.stderr)
        self.assertEqual(self.other.read_bytes(),b'existing Studio runtime')
        self.assertEqual((self.binary/'ue4ss/UE4SS.dll').read_bytes(),b'existing loader')
        return r

    def test_install_collect_disable_preserves_runtime_and_collects_only_scoped_lines(self):
        self.run_action('Install')
        self.assertEqual((self.folder/'Scripts/main.lua').read_bytes(),(FOLDER/'main.lua').read_bytes())
        self.assertTrue((self.folder/'enabled.txt').is_file())
        (self.binary/'ue4ss/UE4SS.log').write_text('unrelated private log line\n[FFR Battle Commands] BOOKMARK | number=1\n')
        self.run_action('Collect')
        z,=self.output.glob('*.zip')
        with zipfile.ZipFile(z) as archive:
            self.assertEqual(set(archive.namelist()),{'report.json','battle-commands.txt'})
            trace=archive.read('battle-commands.txt').decode('utf-8-sig')
            self.assertIn('BOOKMARK',trace);self.assertNotIn('unrelated',trace)
            self.assertFalse(json.loads(archive.read('report.json').decode('utf-8-sig'))['gameplayModified'])
        self.run_action('Disable');self.assertFalse((self.folder/'enabled.txt').exists())

    def test_unknown_and_edited_observer_files_are_preserved(self):
        self.folder.mkdir();(self.folder/'enabled.txt').write_bytes(b'foreign')
        self.run_action('Install',False);self.run_action('Disable',False)
        self.assertEqual((self.folder/'enabled.txt').read_bytes(),b'foreign')
        shutil.rmtree(self.folder)
        self.run_action('Install');(self.folder/'Scripts/main.lua').write_bytes(b'user edit')
        self.run_action('Install',False);self.run_action('Disable',False)
        self.assertEqual((self.folder/'Scripts/main.lua').read_bytes(),b'user edit')


if __name__=='__main__':unittest.main()
