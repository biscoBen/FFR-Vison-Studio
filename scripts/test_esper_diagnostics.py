"""Observer non-interference, live collection and standalone package checks."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
FOLDER = ROOT / 'scripts/reference/esper-mastery'
NAMES = ['Install Esper Diagnostics.cmd', 'Collect Esper Diagnostics.cmd',
         'Disable Esper Diagnostics.cmd', 'Esper Mastery Diagnostics.ps1', 'main.lua', 'Read me.txt']
PWSH = shutil.which('pwsh')
if not PWSH:
    candidate = ROOT.parent / 'scratch/fina-boss-tools/pwsh/pwsh'
    if candidate.is_file(): PWSH = str(candidate)


class EsperObserverTests(unittest.TestCase):
    def runtime(self):
        try:
            from lupa.lua54 import LuaRuntime
        except ImportError:
            self.skipTest('lupa is needed for executable Lua checks')
        lua = LuaRuntime()
        lua.execute('''
            messages={}; pending={}; keys={}; classes={}; inThread=false; reads=0
            function print(s) messages[#messages+1]=s end
            function obj(label, fields)
                fields=fields or {}
                fields.IsValid=function() assert(inThread); reads=reads+1; return true end
                fields.GetFullName=function() assert(inThread); return label end
                fields.GetAddress=function() assert(inThread); return label..'Addr' end
                return setmetatable({}, {__index=fields,__newindex=function() error('Native mutation') end})
            end
            function FindAllOf(kind) assert(inThread); return classes[kind] or {} end
            function LoopAsync(ms,fn) assert(ms==100); loop=fn end
            function ExecuteInGameThread(fn) pending[#pending+1]=fn end
            function RegisterKeyBind(key,fn) keys[key]=fn end
            function RegisterHook() error('Observer must not add hooks') end
            Key={F8=8,F9=9}
            function flush()
                while #pending>0 do
                    local fn=table.remove(pending,1); inThread=true; fn(); inThread=false
                end
            end
            function sample() loop(); flush() end
            function contains(s) return table.concat(messages):find(s,1,true)~=nil end
            function count(s) local n=0; for _,m in ipairs(messages) do if m:find(s,1,true) then n=n+1 end end; return n end
            function unit(id,label)
                local state={hp=120,maxhp=120,mp=10,maxmp=100,action=0,skill=414010,ids={},passives={}}
                local parameterFields={
                    GetUnitId=function() return id end,GetRelation=function() return 1 end,
                    IsDead=function() return false end,GetHitPoint=function() return state.hp end,
                    GetMaxHitPoint=function() return state.maxhp end,GetMagicPoint=function() return state.mp end,
                    GetMaxMagicPoint=function() return state.maxmp end,
                    GetActionCountInBattle=function() return state.action end,
                    GetThinkNum=function() error('Hooked think getter must never be queried') end,
                    GetPassiveSkillList=function() return state.passives end,
                    GetContEffectList=function()
                        local effects={}
                        for _,id in ipairs(state.ids) do
                            effects[#effects+1]=obj('Effect'..id,{GetEffectData=function() return {ID=id} end})
                        end
                        if not state.returnTArray then return effects end
                        return {ForEach=function(_,fn) for i,effect in ipairs(effects) do
                            fn(i,{get=function() return effect end}) end end}
                    end}
                local p=obj('Parameter'..id,parameterFields)
                local aiFields=setmetatable({
                    GetRemainingActionNumSummonedUnit=function() error('Hooked remaining getter must never be queried') end},
                    {__index=function(_,key) if key=='m_SkillId' then return state.skill end end})
                local ai=obj('NativeEsperAI'..id,aiFields)
                local actor=obj(label, {GetUnitParameter=function() return p end,GetUnitAI=function() return ai end})
                return actor,state,parameterFields
            end
            fina,finaState,finaFields=unit(1003,'Fina')
            esper,esperState=unit(10452,'Esper')
            skill=obj('Skill',{GetSkillId=function() error('Unavailable native skill interface method') end})
            job=obj('SkillJob',{m_pActionUnit=esper,m_pSkill=skill})
            classes.CPP_BtlUnit={fina,esper}; classes.CPP_BtlJobSkill={job}
        ''')
        lua.execute((FOLDER / 'main.lua').read_text())
        return lua

    def test_markers_actions_mp_and_jobs_are_observed_without_native_writes_or_hook_queries(self):
        lua = self.runtime()
        lua.execute('''
            finaState.ids={196000,196100,196200,196300}; sample()
            assert(contains('READY') and contains('role=Fina') and contains('role=nativeEsper'))
            assert(contains('masteryMarkers=damage:true,mp:true,extraHP:true,earlySpecial:true'))
            assert(contains('SKILL_JOB') and contains('selectedSkill=414010'))
            local before=#messages; sample(); assert(#messages==before)
            finaState.returnTArray=true; sample(); finaState.returnTArray=false
            assert(#messages==before, 'Both native array shapes must report the same markers')
            finaState.mp=15; esperState.action=1; esperState.skill=300020; sample()
            assert(contains('MP=15') and contains('actions=1') and contains('selectedSkill=300020'))
            assert(not contains('READ_UNAVAILABLE'))
            classes.CPP_BtlUnit={fina}; classes.CPP_BtlJobSkill={}; sample()
            assert(contains('ENDED | unit:Esper') and contains('ENDED | job:SkillJob'))
            finaState.ids={}; sample(); assert(contains('masteryMarkers=damage:false,mp:false'))
            local variant=unit(20452,'OtherVariant'); classes.CPP_BtlUnit={fina,variant}; sample()
            assert(contains('role=other | unitId=20452'))
        ''')

    def test_async_queue_bookmark_missing_fields_and_stop_are_bounded(self):
        lua = self.runtime()
        lua.execute('''
            loop(); loop(); keys[8](); assert(#pending==1 and reads==0)
            flush(); assert(contains('BOOKMARK | number=1'))
            finaFields.GetMaxMagicPoint=function() error('missing reflection') end
            sample(); sample(); assert(count('READ_UNAVAILABLE | GetMaxMagicPoint')==1)
            assert(contains('maxMP=?') and contains('SKILL_JOB'))
            keys[9](); local before=reads; assert(loop()==true); flush(); assert(reads==before)
            assert(contains('STOPPED | F9'))
        ''')

    def test_download_contains_exact_reviewed_sources(self):
        with zipfile.ZipFile(FOLDER / 'Esper-Mastery-Diagnostics.zip') as archive:
            self.assertEqual(archive.namelist(), NAMES)
            self.assertIsNone(archive.testzip())
            for name in NAMES:
                self.assertEqual(archive.read(name).decode().replace('\r\n','\n'), (FOLDER/name).read_text())


@unittest.skipUnless(PWSH, 'PowerShell is required')
class EsperDiagnosticHelperTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.game = self.root / "Full Game & user's folder"
        self.binary = self.game / 'FFRS/Binaries/Win64'
        self.mods = self.binary / 'ue4ss/Mods'
        self.mods.mkdir(parents=True)
        self.runtime = self.mods / 'FFRStudioFieldLeader/Scripts'; self.runtime.mkdir(parents=True)
        (self.runtime/'main.lua').write_text('-- Esper mastery ready; unchanged gameplay runtime')
        (self.runtime/'config.lua').write_text('return {["esperMastery"]=1}\n')
        (self.runtime.parent/'enabled.txt').write_text('')
        self.loader = self.binary/'ue4ss/UE4SS.dll'; self.loader.write_bytes(b'original loader')
        self.mods_txt = self.mods/'mods.txt'; self.mods_txt.write_text('OtherMod : 1\n')
        self.mod = self.mods/'FFRStudioEsperTrace'
        self.output = self.root/'output'
        self.env = dict(os.environ, USERPROFILE=str(self.root), XDG_CACHE_HOME=str(self.root/'cache'),
                        XDG_CONFIG_HOME=str(self.root/'config'), XDG_DATA_HOME=str(self.root/'data'))

    def run_helper(self, action, success=True, output=None):
        args=[PWSH,'-NoLogo','-NoProfile','-File',str(FOLDER/'Esper Mastery Diagnostics.ps1'),
              '-Action',action,'-GamePath',str(self.game),'-NoPrompt']
        if output: args += ['-OutputRoot',str(output)]
        result=subprocess.run(args,capture_output=True,text=True,env=self.env,timeout=30)
        self.assertEqual(result.returncode,0 if success else 1,result.stdout+result.stderr)
        return result

    def test_install_collect_disable_preserves_gameplay_and_includes_activation_evidence(self):
        before={p:p.read_bytes() for p in self.mods.rglob('*') if p.is_file()}
        self.run_helper('Install'); self.run_helper('Install')
        script=self.mod/'Scripts/main.lua'
        self.assertEqual(script.read_bytes(),(FOLDER/'main.lua').read_bytes())
        self.assertEqual(json.loads((self.mod/'observer.json').read_text(encoding='utf-8-sig'))['scriptSha256'].lower(),
                         hashlib.sha256(script.read_bytes()).hexdigest())
        (self.binary/'ue4ss/UE4SS.log').write_text(
            '[OtherMod] unrelated data\n[FFR Esper Trace] READY | schema=1\n'
            '[FFR Esper] Esper mastery ready; equipped rewards only\n'
            '[FFR Esper] esper spawn scan: reflection error\n'
            '[FFR Esper Trace] UNIT | unitId=10452\n')
        self.run_helper('Collect',output=self.output)
        archive,=self.output.glob('*.zip')
        with zipfile.ZipFile(archive) as z:
            report=json.loads(z.read('report.json').decode('utf-8-sig'))
            self.assertEqual(report['observerReadyMarkers'],1)
            self.assertEqual(report['masteryReadyMarkers'],1)
            self.assertTrue(report['esperMasteryConfigured'] and report['runtimeContainsEsperCode'])
            self.assertFalse(report['absenceProvesNoActivation'])
            body=z.read('esper-trace.txt').decode('utf-8-sig')
            self.assertIn('reflection error',body); self.assertNotIn('unrelated data',body)
            self.assertFalse(any(n.endswith(('.dll','.tmp','UE4SS.log')) for n in z.namelist()))
        self.run_helper('Disable'); self.assertFalse((self.mod/'enabled.txt').exists())
        self.run_helper('Install'); self.run_helper('Disable')
        for path,body in before.items(): self.assertEqual(path.read_bytes(),body)

    def test_unknown_or_edited_observer_and_linked_paths_are_preserved(self):
        self.mod.mkdir(); (self.mod/'enabled.txt').write_text('foreign')
        self.run_helper('Install',False); self.run_helper('Disable',False)
        self.assertEqual((self.mod/'enabled.txt').read_text(),'foreign')
        (self.mod/'enabled.txt').unlink(); self.mod.rmdir()
        self.run_helper('Install'); script=self.mod/'Scripts/main.lua'; script.write_text('edited')
        self.run_helper('Install',False); self.run_helper('Disable',False)
        self.assertEqual(script.read_text(),'edited')

    def test_missing_runtime_empty_log_and_output_path_remain_diagnosable(self):
        self.run_helper('Collect',False,output=self.game/'captures')
        self.assertFalse((self.game/'captures').exists())
        (self.runtime/'main.lua').unlink(); (self.runtime/'config.lua').unlink()
        self.run_helper('Collect',output=self.output)
        archive,=self.output.glob('*.zip')
        with zipfile.ZipFile(archive) as z:
            report=json.loads(z.read('report.json').decode('utf-8-sig'))
            self.assertEqual(report['observerReadyMarkers'],0)
            self.assertFalse(report['esperMasteryConfigured'] or report['runtimeContainsEsperCode'])
        self.loader.unlink(); self.run_helper('Install',False)
        self.assertFalse(self.mod.exists())


if __name__ == '__main__': unittest.main()
