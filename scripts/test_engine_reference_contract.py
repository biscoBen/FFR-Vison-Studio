"""Check the actual pinned mappings reader's file-sharing behavior."""
import hashlib
import os
from pathlib import Path
import struct
import subprocess
import tempfile
import unittest
import zipfile

from test_engine_particle_contract import ENGINE_SHA, bundled_assembly


@unittest.skipUnless(os.name == 'nt' and os.environ.get('GITHUB_ACTIONS') == 'true',
                     'Requires Windows CI and its checksum-verified engine cache.')
class EngineReferenceContractTests(unittest.TestCase):
    def test_private_mapping_copies_open_while_the_shared_original_is_locked(self):
        archive = Path(os.environ['RUNNER_TEMP'])/'ffr-studio-engine-cache'/(ENGINE_SHA+'.zip')
        with archive.open('rb') as stream:
            self.assertEqual(hashlib.file_digest(stream,'sha256').hexdigest(),ENGINE_SHA)
        with zipfile.ZipFile(archive) as bundle: executable = bundle.read('bin/ffr-dt.exe')
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name in ('Newtonsoft.Json.dll','ZstdSharp.dll','UAssetAPI.dll'):
                (root/name).write_bytes(bundled_assembly(executable,name))
            # Minimal valid uncompressed version-0 usmap: no names/enums/schemas.
            payload = struct.pack('<III',0,0,0)
            mapping = struct.pack('<HBBII',0x30c4,0,0,len(payload),len(payload))+payload
            for name in ('shared.usmap','0.usmap','1.usmap'): (root/name).write_bytes(mapping)
            script = root/'check-maps.ps1'; script.write_text(MAPPING_CHECK_SCRIPT,encoding='utf-8')
            result = subprocess.run(['pwsh','-NoProfile','-File',str(script),'-Root',str(root)],
                                    capture_output=True,text=True,timeout=60)
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)
            self.assertIn('Native private mapping copies passed.',result.stdout)
            for name in ('shared.usmap','0.usmap','1.usmap'):
                self.assertEqual((root/name).read_bytes(),mapping)


MAPPING_CHECK_SCRIPT = r'''param([string]$Root)
$ErrorActionPreference = 'Stop'
foreach ($name in @('Newtonsoft.Json.dll','ZstdSharp.dll','UAssetAPI.dll')) {
    [void][Reflection.Assembly]::LoadFrom((Join-Path $Root $name))
}
$source = Join-Path $Root 'shared.usmap'
[void][UAssetAPI.Unversioned.Usmap]::new($source)
$hold = [IO.File]::Open($source,[IO.FileMode]::Open)
try {
    $rejected = $false
    try { [void][UAssetAPI.Unversioned.Usmap]::new($source) }
    catch {
        if ($_.Exception.InnerException -is [IO.IOException]) { $rejected = $true }
        else { throw }
    }
    if (-not $rejected) { throw 'The shared-map lock regression control did not fail.' }
    foreach ($name in @('0.usmap','1.usmap')) {
        [void][UAssetAPI.Unversioned.Usmap]::new((Join-Path $Root $name))
    }
} finally { $hold.Dispose() }
Write-Output 'Native private mapping copies passed.'
'''


if __name__ == '__main__': unittest.main()
