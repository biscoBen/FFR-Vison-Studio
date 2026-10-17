"""Read-only trace scope, game-thread access and managed helper lifecycle."""
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
HELPER = ROOT / 'scripts/reference/skill-runtime'


class SkillTraceRuntimeTests(unittest.TestCase):
    def runtime(self):
        from lupa.lua54 import LuaRuntime
        lua = LuaRuntime()
        lua.execute((ROOT / 'scripts/fixtures/skill_trace_runtime.lua').read_text())
        lua.execute((HELPER / 'main.lua').read_text())
        return lua

    def test_native_paths_and_motion_are_sampled_without_mutating_playback(self):
        lua = self.runtime()
        lua.execute('''
            setup_battle(); sample()
            assert(contains('READY') and contains('skillId=500270'))
            assert(contains('sequence=LevelSequence /Game/OriginalMaster'))
            assert(contains('GameMotion=Idle') and contains('project=Ss6Project OriginalProject'))
            assert(contains('JOB_NIAGARA') and contains('asset=NiagaraSystem /Game/OriginalFX'))
            assert(contains('JOB_SPRITE') and contains('position=2.00,-500.00,125.00'))
            local before=#messages; sample(); assert(#messages==before, 'Deduplicate unchanged state')
            sprite.playing='atk'; sample(); assert(contains('GameMotion=atk'))
            effect.active=false; player.playing=false; sample()
            assert(contains('ENDED | fx:') and contains('ENDED | sequence:'))
            assert(sprite.rate==1 and sprite.frame==0 and skill.id==500270)
            assert(actor.m_IsVisible and job.m_pLevelSequenceActor==sequence)
        ''')

    def test_reads_wait_for_game_thread_and_queue_is_bounded(self):
        lua = self.runtime()
        lua.execute('''
            setup_battle(); loop(); loop(); loop()
            assert(reads==0 and #callbacks==1, 'Async callback cannot touch Unreal objects')
            sample(); assert(reads>0 and #callbacks==0)
        ''')

    def test_missing_skill_interface_and_bad_object_do_not_end_other_observation(self):
        lua = self.runtime()
        lua.execute('''
            setup_battle(); skill.GetSkillId=nil
            table.insert(classes.CPP_BtlUnit, obj('CPP_BtlUnit Invalid', {invalid=true}))
            sample(); sample(); sample()
            assert(count('READ_UNAVAILABLE | skill:GetSkillId')==1)
            assert(contains('skillId=?') and contains('JOB_NIAGARA'))
            assert(not contains('STOPPED'))
        ''')

    def test_defaults_outside_battle_and_capture_limits(self):
        lua = self.runtime()
        lua.execute('''
            classes.CPP_BtlUnit={obj('CPP_BtlUnit Default__CPP_BtlUnit')}; sample()
            assert(not contains('BATTLE_OBJECTS_FOUND'))
            assert(not contains('JOB |'))
            setup_battle(); sample(); classes={}; sample()
            assert(contains('BATTLE_OBJECTS_ENDED'))
            setup_battle()
            for _=1,6000 do sample() end
            assert(contains('STOPPED | capture limit'))
            local before=reads; assert(loop()==true); sample(); assert(reads==before)
        ''')

    def test_bookmark_stop_and_event_cap(self):
        lua = self.runtime()
        lua.execute('''
            keybinds[8](); assert(contains('BOOKMARK'))
            setup_battle()
            for i=1,5500 do sprite.playing='action'..i; skill.id=i; sample() end
            assert(contains('STOPPED | capture limit') and #messages<=10000)
        ''')
        lua = self.runtime()
        lua.execute('''
            keybinds[9](); setup_battle(); sample()
            assert(contains('STOPPED | F9') and reads==0)
        ''')


PWSH = shutil.which('pwsh') or (str(Path('/tmp/ffr-pwsh/pwsh')) if Path('/tmp/ffr-pwsh/pwsh').is_file() else None)


@unittest.skipUnless(PWSH, 'PowerShell is required for the helper lifecycle tests.')
class SkillTraceHelperTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.game = self.root / "Game & user's folder"
        self.binary = self.game / 'FFRS/Binaries/Win64'
        self.mod = self.binary / 'ue4ss/Mods/FFRStudioSkillTrace'
        self.binary.mkdir(parents=True)
        (self.binary / 'ue4ss/Mods/ExistingMod').mkdir(parents=True)
        self.other = self.binary / 'ue4ss/Mods/ExistingMod/keep.txt'
        self.other.write_bytes(b'keep other mod')
        (self.binary / 'ue4ss/Mods/mods.txt').write_bytes(b'ExistingMod : 1\r\n')
        (self.binary / 'dwmapi.dll').write_bytes(b'original proxy')
        (self.binary / 'ue4ss/UE4SS.dll').write_bytes(b'original loader')
        self.output = self.root / 'Downloads/FFR Mod'
        self.env = dict(os.environ, USERPROFILE=str(self.root),
                        XDG_CACHE_HOME=str(self.root / 'cache'),
                        XDG_CONFIG_HOME=str(self.root / 'config'),
                        XDG_DATA_HOME=str(self.root / 'data'))

    def run_helper(self, action, *, success=True, output=None):
        args = [PWSH, '-NoLogo', '-NoProfile', '-File', str(HELPER / 'Skill Runtime Trace.ps1'),
                '-Action', action, '-GamePath', str(self.game), '-NoPrompt']
        if output is not None:
            args += ['-OutputRoot', str(output)]
        result = subprocess.run(args, text=True, capture_output=True, env=self.env, timeout=30)
        self.assertEqual(result.returncode, 0 if success else 1, result.stdout + result.stderr)
        return result

    def test_enable_repeat_collect_remove_preserves_other_mods_and_filters_private_logs(self):
        self.run_helper('Enable'); self.run_helper('Enable')
        self.assertEqual((self.mod / 'Scripts/main.lua').read_bytes(), (HELPER / 'main.lua').read_bytes())
        ownership = json.loads((self.mod / '.ffr-skill-trace.json').read_text())
        self.assertEqual(ownership['files']['Scripts/main.lua'].lower(), hashlib.sha256((HELPER / 'main.lua').read_bytes()).hexdigest())
        (self.binary / 'ue4ss/UE4SS.log').write_text(
            '[OtherMod] private unrelated line\nStarting Lua mod FFRStudioSkillTrace\n'
            '[12:10] [FFR Skill Trace] READY | sample=0\n'
            '[12:11] [FFR Skill Trace] JOB | skillId=500270 | sample=1\n')
        self.run_helper('Collect')
        archive, = self.output.glob('*.zip')
        with zipfile.ZipFile(archive) as z:
            body = z.read('skill-trace.txt').decode('utf-8-sig')
            self.assertIn('skillId=500270', body)
            self.assertIn('Starting Lua mod FFRStudioSkillTrace', body)
            self.assertNotIn('private unrelated', body)
            self.assertFalse(any(n.endswith(('.dll', 'UE4SS.log', 'config.json', '.tmp')) for n in z.namelist()))
            report = json.loads(z.read('report.json').decode('utf-8-sig'))
            self.assertEqual(report['readyMarkers'], 1)
            self.assertFalse(report['absenceProvesNoPlayback'])
        self.run_helper('Remove'); self.run_helper('Remove')
        self.assertFalse(self.mod.exists())
        self.assertEqual(self.other.read_bytes(), b'keep other mod')
        self.assertEqual((self.binary / 'ue4ss/Mods/mods.txt').read_bytes(), b'ExistingMod : 1\r\n')
        self.assertEqual((self.binary / 'ue4ss/UE4SS.dll').read_bytes(), b'original loader')

    def test_only_allowlisted_engine_reports_are_collected(self):
        engine = self.root / 'Downloads/Sephira-Studio-Test/engine'
        (engine / 'tools').mkdir(parents=True)
        (engine / 'tools/make_vision_mod.py').write_text('# fixture')
        (engine / 'build').mkdir()
        (engine / 'build/animation-repair-report.json').write_text('{"schema":1}')
        (engine / '.ffr-existing-visions').mkdir()
        (engine / '.ffr-existing-visions/state.json').write_text('{"version":"1.2.35"}')
        (engine / 'config.json').write_text('{"privateRoster":"never collect"}')
        (engine / 'units.json').write_text('private kits')
        self.run_helper('Collect')
        archive, = self.output.glob('*.zip')
        with zipfile.ZipFile(archive) as z:
            self.assertIn('engine/build/animation-repair-report.json', z.namelist())
            self.assertEqual(json.loads(z.read('engine/.ffr-existing-visions/state.json'))['version'], '1.2.35')
            self.assertFalse(any(n.endswith(('config.json', 'units.json')) for n in z.namelist()))

    def test_missing_loader_does_not_install_anything(self):
        (self.binary / 'ue4ss/UE4SS.dll').unlink()
        result = self.run_helper('Enable', success=False)
        self.assertIn('does not install or replace a loader', result.stdout)
        self.assertFalse(self.mod.exists())

    def test_unowned_edited_and_unknown_files_are_preserved(self):
        self.mod.mkdir(); (self.mod / 'keep').write_bytes(b'keep')
        self.run_helper('Enable', success=False); self.run_helper('Remove', success=False)
        (self.mod / 'keep').unlink(); self.mod.rmdir()
        self.run_helper('Enable')
        script = self.mod / 'Scripts/main.lua'
        original = script.read_bytes(); script.write_bytes(b'edited')
        self.run_helper('Enable', success=False); self.run_helper('Remove', success=False)
        self.assertEqual(script.read_bytes(), b'edited')
        script.write_bytes(original)
        extra = self.mod / 'Scripts/unknown.lua'; extra.write_bytes(b'keep extra')
        self.run_helper('Remove', success=False)
        self.assertEqual(extra.read_bytes(), b'keep extra')
        extra.unlink(); self.run_helper('Remove')

    def test_in_game_output_is_rejected_and_empty_capture_remains_diagnosable(self):
        self.run_helper('Collect', success=False, output=self.game / 'captures')
        self.assertFalse((self.game / 'captures').exists())
        result = self.run_helper('Collect')
        self.assertIn('No trace READY marker', result.stdout)
        archive, = self.output.glob('*.zip')
        with zipfile.ZipFile(archive) as z:
            self.assertEqual(json.loads(z.read('report.json').decode('utf-8-sig'))['traceLines'], 0)

    @unittest.skipIf(os.name == 'nt', 'Linux symlink path-guard fixture.')
    def test_linked_mod_folder_is_not_followed(self):
        target = self.root / 'untouched'; target.mkdir()
        self.mod.symlink_to(target, target_is_directory=True)
        self.run_helper('Enable', success=False); self.run_helper('Remove', success=False)
        self.assertEqual(list(target.iterdir()), [])


if __name__ == '__main__':
    unittest.main()
