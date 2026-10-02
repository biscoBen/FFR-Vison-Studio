"""Validate synthetic party hard references against the checksum-pinned engine."""
import hashlib
import ast
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
import zipfile
from test_engine_particle_contract import ENGINE_SHA, bundled_assembly
from test_party_characters import original_view, unit, party
from test_existing_visions import installer, fina_installer


@unittest.skipUnless(os.name == 'nt' and os.environ.get('GITHUB_ACTIONS') == 'true',
                     'Requires Windows CI and its checksum-verified engine cache.')
class EnginePartyContractTests(unittest.TestCase):
    def test_actual_engine_loader_preserves_saved_party_identity(self):
        archive = Path(os.environ['RUNNER_TEMP']) / 'ffr-studio-engine-cache' / (ENGINE_SHA + '.zip')
        with archive.open('rb') as stream:
            self.assertEqual(hashlib.file_digest(stream, 'sha256').hexdigest(), ENGINE_SHA)
        with zipfile.ZipFile(archive) as bundle: source = bundle.read('tools/make_vision_mod.py')
        patched = installer.hook_builder(fina_installer.hook_builder(source))
        loader = next(n for n in ast.parse(patched).body if isinstance(n, ast.FunctionDef) and n.name == 'load_units')
        rows = lambda rel: {c[1]: {'Ss6Project': c[3]} for c in party.CHARACTERS}
        with tempfile.TemporaryDirectory() as directory:
            spec = Path(directory) / 'units.json'
            selected = [unit(c[0]) for c in party.CHARACTERS]
            spec.write_text(json.dumps(selected))
            env = {'os': os, 'json': json, 'SPEC_JSON': str(spec), 'UNITS': []}
            exec(compile(ast.Module(body=[loader], type_ignores=[]), 'actual_engine_roster_loader', 'exec'), env)
            loaded = env['load_units']()
            self.assertEqual(party.split(loaded, rows), (selected, []))
            self.assertEqual(json.loads(spec.read_text()), selected)

    def test_real_serializer_resolves_private_models_and_row_specific_material(self):
        archive = Path(os.environ['RUNNER_TEMP']) / 'ffr-studio-engine-cache' / (ENGINE_SHA + '.zip')
        with archive.open('rb') as stream:
            self.assertEqual(hashlib.file_digest(stream, 'sha256').hexdigest(), ENGINE_SHA)
        with zipfile.ZipFile(archive) as bundle: executable = bundle.read('bin/ffr-dt.exe')
        original = original_view()
        chosen = unit(form=party.FINA)
        edited = party.table_view(original, [chosen])
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name in ('Newtonsoft.Json.dll', 'UAssetAPI.dll'):
                (root / name).write_bytes(bundled_assembly(executable, name))
            (root / 'input.json').write_text(json.dumps(edited, ensure_ascii=False), encoding='utf-8')
            script = root / 'check.ps1'
            script.write_text(r'''param([string]$Root)
$ErrorActionPreference = 'Stop'
[void][Reflection.Assembly]::LoadFrom((Join-Path $Root 'Newtonsoft.Json.dll'))
[void][Reflection.Assembly]::LoadFrom((Join-Path $Root 'UAssetAPI.dll'))
$asset = [UAssetAPI.UAsset]::DeserializeJson([string](Get-Content -Raw -Encoding utf8 (Join-Path $Root 'input.json')))
$indexProperty = [UAssetAPI.UnrealTypes.FName].GetProperty('Index', [Reflection.BindingFlags]'Instance,Public,NonPublic')
if ($null -eq $indexProperty) { throw 'The engine FName index getter is unavailable.' }
foreach ($import in $asset.Imports) {
    foreach ($name in @($import.ObjectName, $import.ClassName, $import.ClassPackage)) {
        if ($null -eq $name -or [int]$indexProperty.GetValue($name) -lt 0) {
            throw ('Unserializable party import: ' + $import.ObjectName.ToString())
        }
    }
}
$rows = $asset.Exports[0].Table.Data
foreach ($row in $rows) {
    $project = $row.Value | Where-Object { $_.Name.ToString() -ceq 'Ss6Project' }
    $reference = $project.Value.ToImport($asset)
    $path = $reference.OuterIndex.ToImport($asset).ObjectName.ToString()
    if ($row.Name.ToString() -ceq 'レイン') {
        if ($path -cne '/Game/Chara/StudioParty/party1001/unit0010') { throw 'Rain did not use the private battle model.' }
        $mat = $row.Value | Where-Object { $_.Name.ToString() -ceq 'Material' }
        $resolved = $mat.Value.ToImport($asset)
        if ($resolved.ClassName.ToString() -cne 'Material') { throw 'Wrong party material class.' }
        if ($resolved.ObjectName.ToString() -cne 'M_StudioParty1001') { throw 'Wrong party material.' }
    } else {
        if (-not $path.StartsWith('/Game/Chara/unit/')) { throw 'An unselected character changed model.' }
        $mat = $row.Value | Where-Object { $_.Name.ToString() -ceq 'Material' }
        if ($mat.Value.ToImport($asset).ObjectName.ToString() -cne 'Battle') { throw 'A shared material was changed.' }
    }
}
if ($rows.Count -ne 8) { throw 'A party row was added or lost.' }
Write-Output 'Real engine party model, material and FName contracts passed.'
''', encoding='utf-8')
            result = subprocess.run(['pwsh', '-NoProfile', '-File', str(script), '-Root', str(root)],
                                    capture_output=True, text=True, timeout=60)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn('Real engine party model, material and FName contracts passed.', result.stdout)


if __name__ == '__main__': unittest.main()
