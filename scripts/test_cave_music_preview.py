"""Read only the requested streamed recording; keep movie/audio duration aligned."""
import io
from pathlib import Path
import struct
import sys
import unittest
import wave
import zipfile
from unittest import mock
import tempfile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'assets/existing_visions/payload'))
import _ffr_cave_music_preview as preview


class CaveMusicPreviewTests(unittest.TestCase):
    def bank(self):
        # Two distinct recordings, padded with native AFS2 alignment.
        return b'AFS2'+bytes([2,4,2,0])+struct.pack('<IHH',2,32,17)+struct.pack('<HHIII',55,56,32,96,160)+b'A'*64+b'B'*64

    def test_selects_requested_recording_and_preserves_subkey(self):
        raw,subkey=preview.extract_wave(io.BytesIO(self.bank()))
        self.assertEqual((raw,subkey),(b'B'*64,17))
        with self.assertRaises(ValueError):preview.extract_wave(io.BytesIO(self.bank()),999)
        with self.assertRaises(ValueError):preview.extract_wave(io.BytesIO(self.bank()[:-1]))
        with self.assertRaises(ValueError):preview.extract_wave(io.BytesIO(b'bad'))

    def test_bounds_reject_an_invalid_or_giant_recording(self):
        raw=bytearray(self.bank());struct.pack_into('<I',raw,28,2**31)
        with self.assertRaisesRegex(ValueError,'bounds'):preview.extract_wave(io.BytesIO(raw))

    def test_short_browser_copy_starts_at_first_sample_and_keeps_stereo(self):
        output=io.BytesIO()
        with wave.open(output,'wb') as f:
            f.setparams((2,2,48000,0,'NONE','not compressed'));f.writeframes(b'\x11\x22\x33\x44'*48000*8)
        with wave.open(io.BytesIO(preview.trim_wave(output.getvalue())),'rb') as f:
            self.assertEqual((f.getnchannels(),f.getsampwidth(),f.getframerate(),f.getnframes()),(2,2,48000,307200))
            self.assertEqual(f.readframes(1),b'\x11\x22\x33\x44')

    def test_rejects_truncated_and_non_pcm_decodes(self):
        with self.assertRaises(ValueError):preview.trim_wave(b'RIFF')
        raw=b'RIFF'+struct.pack('<I',40)+b'WAVEfmt '+struct.pack('<I',100)+bytes(16)
        with self.assertRaisesRegex(ValueError,'Incomplete'):preview.trim_wave(raw)
        fmt=struct.pack('<HHIIHH',3,2,48000,384000,8,32)
        raw=b'RIFF'+struct.pack('<I',36)+b'WAVEfmt '+struct.pack('<I',16)+fmt+b'data'+bytes(4)
        with self.assertRaisesRegex(ValueError,'format'):preview.trim_wave(raw)

    def test_decoder_archive_has_license_and_compatible_framework_assembly(self):
        with zipfile.ZipFile(ROOT/'assets/existing_visions/payload/cave_music_preview.zip') as z:
            self.assertEqual(set(z.namelist()),{'VGAudio.dll','LICENSE.txt','decode.ps1','encode.ps1'})
            self.assertTrue(z.read('VGAudio.dll').startswith(b'MZ'))
            self.assertIn(b'MIT',z.read('LICENSE.txt'))
            if sys.platform=='win32':
                import subprocess
                with tempfile.TemporaryDirectory() as tmp:
                    dll=Path(tmp)/'VGAudio.dll';dll.write_bytes(z.read('VGAudio.dll'))
                    ps=Path(tmp)/'load.ps1'
                    ps.write_text("$ErrorActionPreference='Stop'\nAdd-Type -Path (Join-Path $PSScriptRoot 'VGAudio.dll')\n[VGAudio.Containers.Hca.HcaReader]::new() | Out-Null")
                    subprocess.run(['powershell.exe','-NoProfile','-File',str(ps)],check=True,capture_output=True)


if __name__=='__main__':unittest.main()
