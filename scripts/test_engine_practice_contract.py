"""Exercise practice dialogue edits with the pinned engine's actual patcher."""
import copy
import gzip
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from types import SimpleNamespace
from unittest import mock
import zipfile

from test_engine_particle_contract import ENGINE_SHA, bundled_assembly
from test_native_testing import ROOT, practice_game, testing


@unittest.skipUnless(os.name == 'nt' and os.environ.get('GITHUB_ACTIONS') == 'true',
                     'Requires Windows CI and its checksum-verified engine cache.')
class EnginePracticeContractTests(unittest.TestCase):
    def test_boss_scale_matches_the_real_patcher_and_row_exporter_exactly(self):
        from test_crystal_fina_boss import boss, FIXTURE
        archive = Path(os.environ['RUNNER_TEMP'])/'ffr-studio-engine-cache'/(ENGINE_SHA+'.zip')
        with archive.open('rb') as stream:
            self.assertEqual(hashlib.file_digest(stream,'sha256').hexdigest(),ENGINE_SHA)
        with zipfile.ZipFile(archive) as bundle: executable = bundle.read('bin/ffr-dt.exe')
        source = json.loads(gzip.decompress((FIXTURE/'rows.json.gz').read_bytes()))
        operations = {}
        boss.prepare(lambda rel: operations.setdefault(rel,{'add':[],'set':[]}),lambda rel: source[rel],[])
        plan = operations[boss.DESIGN]; edit, = plan['add']
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name in ('Newtonsoft.Json.dll','UAssetAPI.dll','ffr-dt.dll'):
                (root/name).write_bytes(bundled_assembly(executable,name))
            (root/'source.json').write_bytes(gzip.decompress(
                (ROOT/'scripts/fixtures/practice_dialog/talk-properties.json.gz').read_bytes()))
            (root/'scales.json').write_text(json.dumps({'scale':edit['set']['Scale'],'broken':.9*1.3}),encoding='utf-8')
            script = root/'check-scale.ps1'; script.write_text(SCALE_CHECK_SCRIPT,encoding='utf-8')
            result = subprocess.run(['pwsh','-NoProfile','-File',str(script),'-Root',str(root)],
                                    capture_output=True,text=True,timeout=60)
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)
            actual = json.loads((root/'roundtrip.json').read_bytes())
        # The old arithmetic tail must differ after native Single conversion.
        self.assertNotEqual(actual['broken'],.9*1.3)
        built = copy.deepcopy(source[boss.DESIGN])
        built[edit['row']] = testing.apply_fields(built[edit['cloneFrom']],edit['set'])
        built[edit['row']]['Scale'] = actual['scale']
        testing.check_rows(source[boss.DESIGN],built,plan)
        built[edit['row']]['Scale'] = 1.18
        with self.assertRaisesRegex(ValueError,'changed: Studio_CrystalFinaBoss'):
            testing.check_rows(source[boss.DESIGN],built,plan)

    def test_boss_ai_offsets_match_the_real_kismet_serializer(self):
        from test_crystal_fina_boss import boss, native_ai
        archive = Path(os.environ['RUNNER_TEMP'])/'ffr-studio-engine-cache'/(ENGINE_SHA+'.zip')
        with archive.open('rb') as stream:
            self.assertEqual(hashlib.file_digest(stream,'sha256').hexdigest(),ENGINE_SHA)
        with zipfile.ZipFile(archive) as bundle: executable = bundle.read('bin/ffr-dt.exe')
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name in ('Newtonsoft.Json.dll','UAssetAPI.dll'):
                (root/name).write_bytes(bundled_assembly(executable,name))
            (root/'boss.json').write_text(json.dumps(boss.author_ai(native_ai()),ensure_ascii=False),encoding='utf-8')
            script = root/'check-ai.ps1'; script.write_text(AI_CHECK_SCRIPT,encoding='utf-8')
            result = subprocess.run(['pwsh','-NoProfile','-File',str(script),'-Root',str(root)],
                                    capture_output=True,text=True,timeout=60)
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)
            self.assertIn('Real engine boss AI offset contracts passed.',result.stdout)

    def test_real_serializer_retains_each_choice_tag_within_the_iostore_name_prefix(self):
        from test_existing_visions import module
        archive = Path(os.environ['RUNNER_TEMP'])/'ffr-studio-engine-cache'/(ENGINE_SHA+'.zip')
        with archive.open('rb') as stream:
            self.assertEqual(hashlib.file_digest(stream,'sha256').hexdigest(),ENGINE_SHA)
        with zipfile.ZipFile(archive) as bundle: executable = bundle.read('bin/ffr-dt.exe')
        shell = json.loads(gzip.decompress((ROOT/'scripts/fixtures/practice_dialog/shell.json.gz').read_bytes()))
        with mock.patch.dict('sys.modules',{'ffbe_lb':SimpleNamespace(NEUTRAL_COLOR='#808080')}):
            seq = module('practice_engine_name_fixture',ROOT/'scripts/fixtures/engine_motion/ffbe_resonance.py')
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name in ('Newtonsoft.Json.dll','UAssetAPI.dll'):
                (root/name).write_bytes(bundled_assembly(executable,name))
            with mock.patch.dict('sys.modules',{'ffbe_resonance':seq}):
                for page in 'ABCDEFG':
                    asset = testing.author_practice_choice(copy.deepcopy(shell),
                        'UI.Dialog.Choice.Studio_PracticeBattle_Menu_'+page)
                    (root/(page+'.json')).write_text(json.dumps(asset),encoding='utf-8')
            script = root/'check-names.ps1'; script.write_text(NAME_CHECK_SCRIPT,encoding='utf-8')
            result = subprocess.run(['pwsh','-NoProfile','-File',str(script),'-Root',str(root)],
                                    capture_output=True,text=True,timeout=60)
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)
            self.assertIn('Real engine practice script-name contracts passed.',result.stdout)

    def test_real_patcher_accepts_menu_branches_and_existing_npc_replacement(self):
        archive = Path(os.environ['RUNNER_TEMP'])/'ffr-studio-engine-cache'/(ENGINE_SHA+'.zip')
        with archive.open('rb') as stream:
            self.assertEqual(hashlib.file_digest(stream, 'sha256').hexdigest(), ENGINE_SHA)
        with zipfile.ZipFile(archive) as bundle: executable = bundle.read('bin/ffr-dt.exe')
        _, rows, _ = practice_game()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name in ('Newtonsoft.Json.dll', 'UAssetAPI.dll', 'ffr-dt.dll'):
                (root/name).write_bytes(bundled_assembly(executable, name))
            config = root/testing.CONFIG; config.parent.mkdir(parents=True)
            config.write_text(json.dumps({'schema':1,'maxMr':False,'practiceBattle':True}))
            operations = testing.prepare({}, [], root, rows)[testing.SHOP_EVENT]
            (root/'operations.json').write_text(json.dumps(operations), encoding='utf-8')
            fixture = ROOT/'scripts/fixtures/practice_dialog/talk-properties.json.gz'
            (root/'source.json').write_bytes(gzip.decompress(fixture.read_bytes()))
            script = root/'check.ps1'
            script.write_text(CHECK_SCRIPT, encoding='utf-8')
            result = subprocess.run(['pwsh','-NoProfile','-File',str(script),'-Root',str(root)],
                                    capture_output=True,text=True,timeout=60)
            self.assertEqual(result.returncode, 0, result.stdout+result.stderr)
            self.assertIn('Real engine practice dialogue contracts passed.', result.stdout)


SCALE_CHECK_SCRIPT = r'''param([string]$Root)
$ErrorActionPreference = 'Stop'
[void][Reflection.Assembly]::LoadFrom((Join-Path $Root 'Newtonsoft.Json.dll'))
[void][Reflection.Assembly]::LoadFrom((Join-Path $Root 'UAssetAPI.dll'))
$tool = [Reflection.Assembly]::LoadFrom((Join-Path $Root 'ffr-dt.dll'))
$asset = [UAssetAPI.UAsset]::DeserializeJson([string](Get-Content -Raw -Encoding utf8 (Join-Path $Root 'source.json')))
$flags = [Reflection.BindingFlags]'Static,Public,NonPublic'
$apply = $tool.GetType('Patch',$true).GetMethod('Apply',$flags)
$export = $tool.GetType('Program',$true).GetMethod('ToJson',$flags)
$field = [UAssetAPI.PropertyTypes.Objects.FloatPropertyData]::new([UAssetAPI.UnrealTypes.FName]::new($asset,'Scale'))
$field.Value = [single]0.9
$inputScales = [Newtonsoft.Json.Linq.JObject]::Parse([string](Get-Content -Raw -Encoding utf8 (Join-Path $Root 'scales.json')))
$outputScales = [Newtonsoft.Json.Linq.JObject]::new()
foreach ($key in @('scale','broken')) {
    $patched = $apply.Invoke($null,[object[]]@($asset,$field,$inputScales[$key]))
    $outputScales.Add($key,$export.Invoke($null,[object[]]@($patched,$asset)))
}
[IO.File]::WriteAllText((Join-Path $Root 'roundtrip.json'),$outputScales.ToString([Newtonsoft.Json.Formatting]::None))
'''


AI_CHECK_SCRIPT = r'''param([string]$Root)
$ErrorActionPreference = 'Stop'
[void][Reflection.Assembly]::LoadFrom((Join-Path $Root 'Newtonsoft.Json.dll'))
[void][Reflection.Assembly]::LoadFrom((Join-Path $Root 'UAssetAPI.dll'))
$asset = [UAssetAPI.UAsset]::DeserializeJson([string](Get-Content -Raw -Encoding utf8 (Join-Path $Root 'boss.json')))
$think = $asset.Exports | Where-Object { $_.ObjectName.ToString() -ceq 'ThinkInner' }
$positions = [Collections.Generic.HashSet[int]]::new()
$offset = 0
foreach ($node in $think.ScriptBytecode) {
    [void]$positions.Add($offset)
    $offset += [int]$node.GetSize($asset)
}
if ($offset -ne 466 -or $think.ScriptBytecodeSize -ne $offset) { throw "Incorrect Kismet size $offset" }
foreach ($node in $think.ScriptBytecode) {
    if ($node -is [UAssetAPI.Kismet.Bytecode.Expressions.EX_Jump] -or
        $node -is [UAssetAPI.Kismet.Bytecode.Expressions.EX_JumpIfNot]) {
        if (-not $positions.Contains([int]$node.CodeOffset)) { throw 'Boss AI jumps inside an instruction.' }
    }
}
$count = $asset.GetType().GetField('NamesReferencedFromExportDataCount',[Reflection.BindingFlags]'Instance,Public,NonPublic').GetValue($asset)
if ($count -ne $asset.GetNameMapIndexList().Count) { throw 'Boss AI would lose script names in IoStore.' }
Write-Output 'Real engine boss AI offset contracts passed.'
'''


NAME_CHECK_SCRIPT = r'''param([string]$Root)
$ErrorActionPreference = 'Stop'
[void][Reflection.Assembly]::LoadFrom((Join-Path $Root 'Newtonsoft.Json.dll'))
[void][Reflection.Assembly]::LoadFrom((Join-Path $Root 'UAssetAPI.dll'))
$index = [UAssetAPI.UnrealTypes.FName].GetProperty('Index',[Reflection.BindingFlags]'Instance,Public,NonPublic')
foreach ($page in @('A','B','C','D','E','F','G')) {
    $asset = [UAssetAPI.UAsset]::DeserializeJson([string](Get-Content -Raw -Encoding utf8 (Join-Path $Root ($page+'.json'))))
    $count = $asset.GetType().GetField('NamesReferencedFromExportDataCount',[Reflection.BindingFlags]'Instance,Public,NonPublic').GetValue($asset)
    if ($count -ne $asset.GetNameMapIndexList().Count) { throw 'IoStore would trim menu names.' }
    $call = @($asset.Exports | Where-Object { $_ -is [UAssetAPI.ExportTypes.FunctionExport] -and $_.ScriptBytecodeSize -eq 40 })
    if ($call.Count -ne 1) { throw 'Missing menu-open call.' }
    $tag = $call[0].ScriptBytecode[0].Parameters[0].Value[0].Value
    $tagIndex = [int]$index.GetValue($tag)
    if ($tagIndex -ne 79 -or $tagIndex -ge $count -or $tag.ToString() -cne ('UI.Dialog.Choice.Studio_PracticeBattle_Menu_'+$page)) {
        throw 'A menu script uses a missing or incorrect packed name.'
    }
}
Write-Output 'Real engine practice script-name contracts passed.'
'''


CHECK_SCRIPT = r'''param([string]$Root)
$ErrorActionPreference = 'Stop'
[void][Reflection.Assembly]::LoadFrom((Join-Path $Root 'Newtonsoft.Json.dll'))
[void][Reflection.Assembly]::LoadFrom((Join-Path $Root 'UAssetAPI.dll'))
$tool = [Reflection.Assembly]::LoadFrom((Join-Path $Root 'ffr-dt.dll'))
$asset = [UAssetAPI.UAsset]::DeserializeJson([string](Get-Content -Raw -Encoding utf8 (Join-Path $Root 'source.json')))
$ops = Get-Content -Raw -Encoding utf8 (Join-Path $Root 'operations.json') | ConvertFrom-Json
$flags = [Reflection.BindingFlags]'Static,Public,NonPublic'
$patch = $tool.GetType('Patch', $true)
$apply = $patch.GetMethod('ApplyObject', $flags)
$clone = $patch.GetMethod('DeepClone', $flags)
$rows = $asset.Exports[0].Table.Data
# Negative control: the user's original failure must be detected by this test.
$woman = $rows | Where-Object { $_.Name.ToString() -ceq 'DT_Town_010Gra_20_0920_8' }
$broken = $clone.Invoke($null, [object[]]@($woman.psobject.BaseObject))
$bad = [Newtonsoft.Json.Linq.JObject]::Parse('{
  "ContinuousEventList":[{"Condition":"","EventId":"Studio_PracticeBattle_Menu_A"}]}')
$rejected = $false
try { $apply.Invoke($null, [object[]]@($asset, $broken.Value, $bad)) }
catch { if ($_.Exception.ToString().Contains("empty array of type 'StructProperty' ('ContinuousEventList')")) { $rejected = $true } else { throw } }
if (-not $rejected) { throw 'The empty-struct-array regression control did not fail.' }
foreach ($edit in $ops.add) {
    $donor = $rows | Where-Object { $_.Name.ToString() -ceq $edit.cloneFrom }
    if ($null -eq $donor) { throw 'The native practice donor is missing.' }
    $row = $clone.Invoke($null, [object[]]@($donor.psobject.BaseObject))
    $fields = [Newtonsoft.Json.Linq.JObject]::Parse(($edit.set | ConvertTo-Json -Depth 100 -Compress))
    $apply.Invoke($null, [object[]]@($asset, $row.Value, $fields))
    if ($edit.row -ceq 'DT_Town_010Gra_20_0920_8') {
        foreach ($name in @('OnFlagList', 'ProgressList', 'RequestStateSettings')) {
            $property = $row.Value | Where-Object { $_.Name.ToString() -ceq $name }
            if ($property.Value.Length -ne 0) { throw ('Inherited quest state: ' + $name) }
        }
        $argsMap = $row.Value | Where-Object { $_.Name.ToString() -ceq 'ArgList' }
        $entry = @($argsMap.Value.Keys)[0]
        if ($entry.Value.ToString() -cne 'id' -or $argsMap.Value[$entry].Value.ToString() -cne '6') {
            throw 'The shop woman lost her original dialogue argument.'
        }
    }
}
if ($ops.add.Count -ne 21 -or $ops.set.Count -ne 0) { throw 'Unexpected practice row operations.' }
Write-Output 'Real engine practice dialogue contracts passed.'
'''


if __name__ == '__main__': unittest.main()
