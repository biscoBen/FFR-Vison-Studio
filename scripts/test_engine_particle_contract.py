"""Check particle constants against the real cached Windows engine patcher."""
import hashlib
import json
import os
from pathlib import Path
import struct
import subprocess
import tempfile
import unittest
import zipfile
import zlib

from test_animation_and_library import motion

ENGINE_SHA = '1c6e4d4b348b048404b6578bf10010c4caa873a5599d9dcbb9f64b00d299c41d'


def bundled_assembly(executable, name):
    """Read the named assembly from the verified .NET 6+ single-file bundle."""
    encoded = name.encode(); start = 0
    while (at := executable.find(encoded, start)) >= 0:
        start = at + len(encoded)
        if at < 26 or executable[at - 1] != len(encoded): continue
        offset, size, compressed = struct.unpack('<qqq', executable[at - 26:at - 2])
        if not (0 <= offset < len(executable) and 0 < size < 32 * 1024 * 1024
                and 0 <= compressed < len(executable) and executable[at - 2] == 1): continue
        data = executable[offset:offset + (compressed or size)]
        if compressed: data = zlib.decompress(data, -15)
        if len(data) == size and data[:2] == b'MZ': return data
    raise AssertionError(f'The verified engine bundle has no {name}.')


@unittest.skipUnless(os.name == 'nt' and os.environ.get('GITHUB_ACTIONS') == 'true',
                     'Requires Windows CI and its checksum-verified engine cache.')
class EngineParticleContractTests(unittest.TestCase):
    def test_real_patcher_resolves_particle_paths_without_literal_dump_prefixes(self):
        archive = Path(os.environ['RUNNER_TEMP']) / 'ffr-studio-engine-cache' / (ENGINE_SHA + '.zip')
        with archive.open('rb') as stream: self.assertEqual(hashlib.file_digest(stream, 'sha256').hexdigest(), ENGINE_SHA)
        with zipfile.ZipFile(archive) as bundle: executable = bundle.read('bin/ffr-dt.exe')
        imports = []
        for name in ('NS_EF_SKL220050_001', 'NS_EF_SKL210260_Vanishla_001_Center'):
            imports.extend([{'ObjectName': '/Game/Effect/Contract/' + name, 'ClassName': 'Package',
                              'ClassPackage': '/Script/CoreUObject', 'OuterIndex': 0},
                            {'ObjectName': name, 'ClassName': 'NiagaraSystem', 'ClassPackage': '/Script/Niagara',
                              'OuterIndex': -len(imports) - 1}])
        constants = [motion.particle_import('import:' + item['ObjectName'], imports)[1]
                     for item in imports if item['ClassName'] == 'NiagaraSystem']
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name in ('Newtonsoft.Json.dll', 'UAssetAPI.dll', 'ffr-dt.dll'):
                (root / name).write_bytes(bundled_assembly(executable, name))
            (root / 'input.json').write_text(json.dumps({'imports': imports, 'constants': constants}))
            script = root / 'check.ps1'
            script.write_text(r'''param([string]$Root)
$ErrorActionPreference = 'Stop'
[void][Reflection.Assembly]::LoadFrom((Join-Path $Root 'Newtonsoft.Json.dll'))
[void][Reflection.Assembly]::LoadFrom((Join-Path $Root 'UAssetAPI.dll'))
$tool = [Reflection.Assembly]::LoadFrom((Join-Path $Root 'ffr-dt.dll'))
$inputData = Get-Content -Raw (Join-Path $Root 'input.json') | ConvertFrom-Json
$asset = [UAssetAPI.UAsset]::new()
$asset.Imports = [Collections.Generic.List[UAssetAPI.Import]]::new()
$names = $asset.GetType().GetField('nameMapIndexList', [Reflection.BindingFlags]'Instance,NonPublic')
$names.SetValue($asset, [Activator]::CreateInstance($names.FieldType))
foreach ($item in $inputData.imports) {
    $asset.Imports.Add([UAssetAPI.Import]::new($item.ClassPackage, $item.ClassName,
        [UAssetAPI.UnrealTypes.FPackageIndex]::new([int]$item.OuterIndex), $item.ObjectName, $false, $asset))
}
$flags = [Reflection.BindingFlags]'Static,Public,NonPublic'
$type = $tool.GetType('KismetTools', $true)
$replace = $type.GetMethod('Replace', $flags)
$dump = $type.GetMethod('ExprToJson', $flags)
foreach ($constant in $inputData.constants) {
    $token = [Newtonsoft.Json.Linq.JObject]::Parse(($constant | ConvertTo-Json -Compress))
    $result = $replace.Invoke($null, [object[]]@($asset, $null,
        [UAssetAPI.Kismet.Bytecode.Expressions.EX_NoObject]::new(), $null, $token))
    $reference = $result.Item1.Value.ToImport($asset)
    $package = $reference.OuterIndex.ToImport($asset).ObjectName.ToString()
    $actual = $package + '.' + $reference.ObjectName.ToString()
    if ($actual -cne $constant.path -or $reference.ClassName.ToString() -cne 'NiagaraSystem') {
        throw "The real engine resolved the wrong particle: $actual"
    }
    $label = $dump.Invoke($null, [object[]]@($asset, $null, $result.Item1, $null)).ToString()
    if ($label -cne ('import:' + $reference.ObjectName.ToString())) { throw 'Unexpected engine dump label.' }
}
if ($asset.Imports.Count -ne $inputData.imports.Count) { throw 'The engine created an unexpected particle import.' }
Write-Output 'Real engine particle path and dump contracts passed.'
''', encoding='utf-8')
            result = subprocess.run(['pwsh', '-NoProfile', '-File', str(script), '-Root', str(root)],
                                    capture_output=True, text=True, timeout=60)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn('Real engine particle path and dump contracts passed.', result.stdout)


if __name__ == '__main__': unittest.main()
