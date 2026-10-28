"""External session lifecycle, installation isolation and export after process exit."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
import zipfile

from build_game_diagnostics_bundle import build,SOURCES,ROOT

PWSH=shutil.which('pwsh')
LIBRARY=ROOT/'scripts/reference/common/DiagnosticSession.ps1'
COLLECTOR=ROOT/'scripts/reference/game-crash/Collect Resonance Crash.ps1'


def quoted(value):return "'"+str(value).replace("'","''")+"'"


class BundleTests(unittest.TestCase):
    def test_session_download_has_exact_sources_and_no_installed_observer(self):
        with tempfile.TemporaryDirectory() as root:
            for path in (build(Path(root)/'session.zip'),ROOT/'scripts/reference/game-crash/Game-Diagnostic-Session.zip'):
                with zipfile.ZipFile(path) as archive:
                    self.assertEqual(archive.namelist(),list(SOURCES))
                    self.assertIsNone(archive.testzip())
                    for name,source in SOURCES.items():self.assertEqual(archive.read(name),(ROOT/source).read_bytes())
                    self.assertFalse(any(name.endswith('.lua') or name=='enabled.txt' for name in archive.namelist()))


@unittest.skipUnless(PWSH,'PowerShell required')
class SessionTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);self.game=self.root/"Game & user's folder"
        self.binary=self.game/'FFRS/Binaries/Win64';self.binary.mkdir(parents=True)
        self.output=self.root/'reports';self.result=self.root/'result.json'
        self.env=dict(os.environ,USERPROFILE=str(self.root),LOCALAPPDATA=str(self.root/'local'),
                      XDG_CACHE_HOME=str(self.root/'cache'),XDG_CONFIG_HOME=str(self.root/'config'),
                      XDG_DATA_HOME=str(self.root/'data'))

    def run_script(self,body,success=True):
        script=self.root/'test.ps1';script.write_text(body)
        p=subprocess.run([PWSH,'-NoProfile','-File',str(script)],capture_output=True,text=True,env=self.env,timeout=25)
        self.assertEqual(p.returncode,0 if success else 1,p.stdout+p.stderr)
        return p

    def wrapper(self,query,extra='',timeout=0):
        return f"""$ErrorActionPreference='Stop'
. {quoted(LIBRARY)}
$script:game={quoted(self.game)}
$script:step=0;$script:pauses=0
$script:epoch=[DateTime]::Parse('2026-10-28T12:00:00Z').ToUniversalTime()
function Fixture-Process([int]$Id,[string]$Root,[double]$Age=1) {{
    [pscustomobject]@{{Id=$Id;Path=[IO.Path]::Combine($Root,'FFRS/Binaries/Win64/FFRS-Win64-Shipping.exe');StartTime=$script:epoch.AddSeconds(-$Age)}}
}}
$query={{ {query} }}
$pause={{param($Milliseconds) $script:pauses++; {extra} }}
$now={{ $script:epoch.AddMilliseconds(500*$script:pauses) }}
$session=Wait-FFRStudioGameSession -GamePath $script:game -ProcessQuery $query -Pause $pause -UtcNow $now -StartTimeoutSeconds {timeout}
@{{session=$session;queries=$script:step;pauses=$script:pauses}} | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath {quoted(self.result)} -Encoding UTF8
"""

    def data(self):return json.loads(self.result.read_text(encoding='utf-8-sig'))

    def test_waits_for_selected_installation_and_exports_only_when_it_exits(self):
        query="""$script:step++
if ($script:step -eq 1) { Fixture-Process 9 ($script:game+' DEMO') }
elseif ($script:step -eq 2 -or $script:step -eq 3) {
 Fixture-Process 9 ($script:game+' DEMO');Fixture-Process 41 $script:game
} """
        self.run_script(self.wrapper(query))
        d=self.data();self.assertEqual(d['queries'],4);self.assertEqual(d['session']['processId'],41)
        self.assertFalse(d['session']['installedGameScripts'] or d['session']['processControlled'])
        self.assertFalse(self.output.exists())

    def test_attaches_to_existing_game_and_does_not_follow_reused_pid(self):
        query="""$script:step++
if ($script:step -eq 1) { Fixture-Process 41 $script:game 20 }
else { Fixture-Process 41 $script:game 1 }"""
        self.run_script(self.wrapper(query))
        d=self.data();self.assertEqual(d['queries'],2);self.assertTrue(d['session']['attachedToExistingSession'])
        self.assertIn('11:59:40',d['session']['processStartedUtc'])

    def test_unreadable_process_metadata_is_not_mistaken_for_game_exit(self):
        query="""$script:step++
if ($script:step -eq 1 -or $script:step -eq 3) { Fixture-Process 41 $script:game }
elseif ($script:step -eq 2) { [pscustomobject]@{Id=41;Path=$null;StartTime=$null} }"""
        self.run_script(self.wrapper(query))
        self.assertEqual(self.data()['queries'],4)

    def test_multiple_matching_processes_wait_until_unambiguous(self):
        query="""$script:step++
if ($script:step -eq 1) { Fixture-Process 41 $script:game;Fixture-Process 42 $script:game }
elseif ($script:step -eq 2) { Fixture-Process 42 $script:game }"""
        result=self.run_script(self.wrapper(query))
        self.assertIn('More than one',result.stdout);self.assertEqual(self.data()['session']['processId'],42)
        self.assertEqual(self.data()['queries'],3)

    def test_timeout_and_cancellation_leave_game_and_output_unchanged(self):
        marker=self.binary/'unchanged.txt';marker.write_bytes(b'original')
        self.run_script(self.wrapper('$script:step++',timeout=1),False)
        self.assertFalse(self.result.exists() or self.output.exists())
        self.run_script(self.wrapper('$script:step++',extra="throw 'Fixture cancellation'"),False)
        self.assertEqual(marker.read_bytes(),b'original');self.assertFalse(self.output.exists())

    def test_offline_collection_after_session_exit_captures_final_log_and_session_identity(self):
        stage=self.root/'collector';stage.mkdir()
        shutil.copyfile(COLLECTOR,stage/COLLECTOR.name)
        marker=self.binary/'ue4ss/Mods/FFRStudioBattleCommandTrace/enabled.txt'
        marker.parent.mkdir(parents=True);marker.write_bytes(b'')
        log=self.binary/'ue4ss/UE4SS.log';log.parent.mkdir(parents=True,exist_ok=True);log.write_text('Startup\n')
        save=self.game/'FFRS/Saved/SaveGames/player.sav';save.parent.mkdir(parents=True);save.write_bytes(b'private save')
        helper=f""". {quoted(LIBRARY)}
$script:realWait=(Get-Command Wait-FFRStudioGameSession).ScriptBlock
function Wait-FFRStudioGameSession {{
 param($GamePath,$StartTimeoutSeconds)
 $script:phase=0
 $query={{
  $script:phase++
  if ($script:phase -eq 1) {{
   [pscustomobject]@{{Id=41;Path=[IO.Path]::Combine($GamePath,'FFRS/Binaries/Win64/FFRS-Win64-Shipping.exe');StartTime=[DateTime]::UtcNow.AddSeconds(-5)}}
  }}
 }}
 $pause={{param($Milliseconds)
  if (Test-Path -LiteralPath {quoted(self.output)}) {{ throw 'Collector wrote before the game exited' }}
  Add-Content -LiteralPath {quoted(log)} -Value 'Final exit log'
 }}
 & $script:realWait -GamePath $GamePath -StartTimeoutSeconds 1 -ProcessQuery $query -Pause $pause
}}
"""
        (stage/'DiagnosticSession.ps1').write_text(helper)
        script=f"function Read-Host {{ throw 'Session should not ask for unnecessary confirmation' }}\n& {quoted(stage/COLLECTOR.name)} -GamePath {quoted(self.game)} -OutputRoot {quoted(self.output)} -WatchGame\nexit $LASTEXITCODE\n"
        self.run_script(script)
        archive,=self.output.glob('Resonance-Diagnostic-Session-*.zip')
        with zipfile.ZipFile(archive) as z:
            report=json.loads(z.read('report.json').decode('utf-8-sig'))
            self.assertEqual(report['session']['processId'],41)
            self.assertFalse(report['session']['installedGameScripts'])
            self.assertTrue(any(b'Final exit log' in z.read(n) for n in z.namelist()))
            self.assertFalse(any(n.endswith(('.sav','.lua','.dll')) for n in z.namelist()))
        self.assertEqual(save.read_bytes(),b'private save')
        self.assertEqual(marker.read_bytes(),b'')

    def test_default_query_accepts_shortened_windows_process_names(self):
        script=self.wrapper('$script:step++')
        script=script.replace('$session=Wait-FFRStudioGameSession',"""
function Get-Process {
 param($Name,$ErrorAction)
 if ($Name -ne 'FFRS*') { throw 'Exact long process names can be shortened by Windows PowerShell' }
 $script:step++
 if ($script:step -eq 1) { Fixture-Process 41 $script:game }
}
$session=Wait-FFRStudioGameSession""")
        script=script.replace(' -ProcessQuery $query','')
        self.run_script(script)
        self.assertEqual(self.data()['session']['processId'],41)

    def test_full_game_detection_skips_absent_drives_and_stale_demo_root(self):
        demo=self.root/'FINAL FANTASY RESONANCE DEMO';(demo/'FFRS/Binaries/Win64').mkdir(parents=True)
        source=COLLECTOR.read_text().split('\ntry {\n    Add-Type',1)[0]
        source+="\nif (Find-Game 'Z:\\missing-full-game-751956') { throw 'Unexpected game' }\nWrite-Output 'ABSENT_DRIVE_OK'\n"
        source+=f"if (Find-Game {quoted(demo)}) {{ throw 'A stale demo folder must not override full-game detection' }}\n"
        source+=f"if (-not (Find-Game {quoted(self.game)})) {{ throw 'Full game fixture was not recognized' }}\n"
        result=self.run_script(source)
        self.assertIn('ABSENT_DRIVE_OK',result.stdout)


if __name__=='__main__':unittest.main()
