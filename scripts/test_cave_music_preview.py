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
from types import ModuleType, SimpleNamespace

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'assets/existing_visions/payload'))
import _ffr_cave_music_preview as preview


def hca_v3_fixture():
    """Synthetic v3 independent stereo with resolution-zero noise bands.

    No game recording: fixed/delta-free scales and signed prefix coefficients
    are packed here so consuming v2's extra coefficient bits cannot pass.
    """
    header=bytearray(96);header[:8]=b'HCA\0\x03\0\0\x60'
    header[8:12]=b'fmt\0';header[12]=2;header[13:16]=(48000).to_bytes(3,'big')
    header[16:20]=(4).to_bytes(4,'big');header[24:28]=b'comp'
    header[28:40]=bytes((0,64,0,15,1,0,4,4,0,0,0,0))
    header[40:50]=b'ciph\0\0pad\0'
    header[-2:]=struct.pack('>H',CaveMusicPreviewTests.crc(header[:-2]))
    frames=[]
    for frame in range(4):
        bits='1'*16+format(180,'09b')+'0'*7
        for scales in ((50,40,48,0),(48,42,50,0)):
            bits+='110'+''.join(format(scale,'06b') for scale in scales)
        for subframe in range(8):
            for channel in range(2):
                # res 2 (+/-1): 01/10; res 1 (+/-1): 10/11.
                positive=(frame+subframe+channel)%2==0
                r2='01' if positive else '10';r1='10' if positive else '11'
                bits+=r2+r1 if channel==0 else r1+r2
        bits+='0'*(62*8-len(bits));raw=int(bits,2).to_bytes(62,'big')
        frames.append(raw+struct.pack('>H',CaveMusicPreviewTests.crc(raw)))
    return bytes(header)+b''.join(frames)


class CaveMusicPreviewTests(unittest.TestCase):
    @staticmethod
    def crc(data):
        result=0
        for byte in data:
            result^=byte<<8
            for _ in range(8):result=((result<<1)^(0x8005 if result&0x8000 else 0))&0xffff
        return result

    def test_native_prefix_keeps_encrypted_frames_and_removes_looping_without_decoding(self):
        header=bytearray(80);header[:8]=b'HCA\0\x03\0\0P'
        header[8:12]=b'fmt\0';header[12]=2;header[13:16]=(48000).to_bytes(3,'big')
        header[16:20]=(400).to_bytes(4,'big');header[20:22]=(2565).to_bytes(2,'big')
        header[24:28]=b'comp';header[28:30]=(32).to_bytes(2,'big')
        header[40:44]=b'loop';header[56:62]=b'ciph\0\x38';header[62:66]=b'pad\0'
        for offset in (0,8,24,40,56,62):
            header[offset:offset+4]=bytes(v|128 if v else 0 for v in header[offset:offset+4])
        header[-2:]=struct.pack('>H',self.crc(header[:-2]))
        frame=b'\xff\xff'+b'A'*28;frame+=struct.pack('>H',self.crc(frame))
        original=bytes(header)+frame*400
        with mock.patch.dict(sys.modules,{'ffbe_effects':ModuleType('ffbe_effects'),
                'ffbe_effects.hca_host':SimpleNamespace(crc=self.crc)}):
            result=preview.trim_hca(original)
            size=int.from_bytes(result[6:8],'big')
            self.assertEqual(size,64)
            self.assertEqual(self.crc(result[:size]),0)
            self.assertNotIn(b'loop',bytes(v&127 for v in result[:size]))
            frames=int.from_bytes(result[16:20],'big');padding=int.from_bytes(result[22:24],'big')
            self.assertEqual(frames*1024-2565-padding,307200)
            self.assertEqual(result[size:],original[80:80+frames*32])
            self.assertEqual(result[4:6],b'\x03\0')
            for raw in (original[:-1],original[:70]):
                with self.assertRaises(ValueError):preview.trim_hca(raw)
            with self.assertRaises(ValueError):preview.trim_hca(original,10)

    def bank(self):
        # Two distinct recordings, padded with native AFS2 alignment.
        return b'AFS2'+bytes([2,4,2,0])+struct.pack('<IHH',2,32,17)+struct.pack('<HHIII',50,51,32,96,160)+b'A'*64+b'B'*64

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

    def test_actual_cave_cue_matches_runtime_bookmark_and_invalidates_the_old_cache(self):
        import _ffr_fina_cave_music as music
        import _ffr_deck_sync as sync
        self.assertEqual((preview.CUE_NAME,preview.STREAM_ID),('BGM_PP_EVENT_VISIONS_INST',51))
        self.assertEqual(music.CUE_NAME,preview.CUE_NAME)
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);tools=root/'tools';tools.mkdir()
            (tools/'cave_music_preview.zip').write_bytes(b'fixture decoder')
            for name in ('CaveHcaV3.cs','cave_hca_v3.ps1'):(tools/name).write_bytes(b'fixture v3 decoder')
            original=preview.hashlib.sha256
            identity={'sha256':'same game'}
            old_key=original((__import__('json').dumps(identity,sort_keys=True)+original(b'fixture decoder').hexdigest()).encode()).hexdigest()[:24]
            cache=root/'build/fina-preview-audio';cache.mkdir(parents=True);(cache/(old_key+'.wav')).write_bytes(b'old wrong cave sound')
            env=mock.Mock();env.game_root.return_value=str(root);env.game_paks.return_value=str(root/'missing')
            with mock.patch.object(sync,'game_identity',return_value=identity):
                with self.assertRaisesRegex(ValueError,'bank could not be read'):preview.audio(root,env)

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
                    for name in ('encode.ps1','decode.ps1'):(Path(tmp)/name).write_bytes(z.read(name))
                    source=Path(tmp)/'stereo.wav'
                    with wave.open(str(source),'wb') as f:
                        f.setparams((2,2,48000,0,'NONE','not compressed'));f.writeframes(bytes(307200*4))
                    for explicit in (False,True):
                        target=Path(tmp)/('explicit.adx' if explicit else 'default.adx')
                        cmd=['powershell.exe','-NoProfile','-NonInteractive','-ExecutionPolicy','Bypass','-File',str(Path(tmp)/'encode.ps1'),str(source),str(target)]
                        if explicit:cmd.append(str(dll))
                        subprocess.run(cmd,check=True,capture_output=True)
                        raw=target.read_bytes()
                        self.assertEqual(raw[:2],b'\x80\x00')
                        self.assertEqual(struct.unpack_from('>II',raw,8),(48000,307200))
                        self.assertEqual(raw[7],2)

    @unittest.skipUnless(sys.platform=='win32','Requires the actual Windows PowerShell decoder.')
    def test_v3_resolution_zero_noise_bands_decode_as_audio_not_v2_garbage(self):
        import subprocess
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);payload=ROOT/'assets/existing_visions/payload'
            with zipfile.ZipFile(payload/'cave_music_preview.zip') as z:
                (root/'VGAudio.dll').write_bytes(z.read('VGAudio.dll'))
            source=root/'synthetic.hca';source.write_bytes(hca_v3_fixture());target=root/'decoded.wav'
            subprocess.run(['powershell.exe','-NoProfile','-NonInteractive','-ExecutionPolicy','Bypass','-File',
                str(payload/'cave_hca_v3.ps1'),str(source),str(target),str(root/'VGAudio.dll')],check=True,capture_output=True)
            with wave.open(str(target)) as w:
                self.assertEqual((w.getnchannels(),w.getframerate(),w.getnframes()),(2,48000,4096))
                pcm=struct.unpack('<8192h',w.readframes(4096))
            # Independent clHCA v3 reference values for this synthetic frame.
            expected=(-9,65,-21,78,-32,90,-42,100,-50,109,-57,116,-62,122,-66,126,
                -68,128,-69,128,-67,127,-64,123,-59,118,-52,111,-44,102,-34,91)
            for actual,reference in zip(pcm[1024:1056],expected):self.assertLessEqual(abs(actual-reference),1)
            self.assertAlmostEqual((sum(v*v for v in pcm)/len(pcm))**.5,427.042708,delta=.1)

    def test_preview_uses_v3_decoder_and_does_not_reuse_the_bad_v2_cache(self):
        import _ffr_fina_cave_music as music
        import _ffr_deck_sync as sync
        import hashlib,json
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);tools=root/'tools';tools.mkdir()
            payload=ROOT/'assets/existing_visions/payload'
            for name in ('cave_music_preview.zip','CaveHcaV3.cs','cave_hca_v3.ps1'):
                (tools/name).write_bytes((payload/name).read_bytes())
            identity={'sha256':'same installed game'}
            old_fingerprint=hashlib.sha256(json.dumps({'revision':2,'game':identity,'cue':preview.CUE_NAME,
                'stream':preview.STREAM_ID,'decoder':hashlib.sha256((tools/'cave_music_preview.zip').read_bytes()).hexdigest()},
                sort_keys=True).encode()).hexdigest()[:24]
            folder=root/'build/fina-preview-audio';folder.mkdir(parents=True)
            (folder/(old_fingerprint+'.wav')).write_bytes(b'wrong v2 decode')
            raw=root/'recording.hca';raw.write_bytes(hca_v3_fixture())
            output=io.BytesIO()
            with wave.open(output,'wb') as f:f.setparams((2,2,48000,0,'NONE','not compressed'));f.writeframes(b'\x11\x22\x33\x44'*4096)
            def decode(command,**kwargs):
                self.assertEqual(Path(command[command.index('-File')+1]).name,'cave_hca_v3.ps1')
                self.assertEqual(Path(command[-1]).name,'VGAudio.dll')
                Path(command[-2]).write_bytes(output.getvalue());return SimpleNamespace(returncode=0)
            env=SimpleNamespace(game_root=lambda:root)
            modules={'ffbe_audio':SimpleNamespace(host_config=lambda _:Path('/unused')),
                'ffbe_effects':ModuleType('ffbe_effects'),
                'ffbe_effects.hca_host':SimpleNamespace(key_from_config=lambda _:1)}
            with mock.patch.dict(sys.modules,modules),mock.patch.object(sync,'game_identity',return_value=identity),\
                    mock.patch.object(music,'recording',return_value=(raw,0)),\
                    mock.patch.object(preview,'trim_hca',side_effect=lambda v:v),\
                    mock.patch.object(preview,'decrypt',side_effect=lambda v,*_:v),\
                    mock.patch.object(preview.subprocess,'run',side_effect=decode) as run:
                result=preview.audio(root,env)
                self.assertEqual(result,output.getvalue())
                self.assertEqual(preview.audio(root,env),result)
                self.assertEqual(run.call_count,1)



if __name__=='__main__':unittest.main()
