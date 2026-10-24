"""Native movie audio metadata and every original picture must survive rescoring."""
import hashlib
from pathlib import Path
import struct
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock
import zipfile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'assets/existing_visions/payload'))
import _ffr_movie_audio as movie
import _ffr_fina_cave_music as music


def adx_fixture():
    # Valid silent stereo ADX v4; copyright/header and end marker are native.
    header=bytearray(40);header[:8]=bytes.fromhex('8000002403120402')
    struct.pack_into('>II',header,8,48000,307200);header[18:20]=bytes((4,0));header[-6:]=b'(c)CRI'
    return bytes(header)+bytes(307200//32*36)+bytes.fromhex('8001000e')+bytes(14)


class MovieAudioTests(unittest.TestCase):
    def test_mux_preserves_all_color_and_alpha_packets_and_exact_native_adx(self):
        with zipfile.ZipFile(ROOT/'assets/existing_visions/payload/fina_cinematic.zip') as z:raw=z.read('movie.usm')
        adx=adx_fixture();result,report=movie.with_soundtrack(raw,adx)
        self.assertEqual((report['videoPackets'],report['alphaPackets'],report['audioPackets']),(192,192,194))
        for typ in (b'@SFV',b'@ALP'):
            packets=lambda data:[bytes(c['payload']) for c in movie.chunks(data) if c['type']==typ and c['kind']==0]
            self.assertEqual(packets(raw),packets(result))
        parts=movie.chunks(result)
        self.assertEqual(b''.join(bytes(c['payload']) for c in parts if c['type']==b'@SFA' and c['kind']==0),movie.native_adx(adx))
        header,=[c for c in parts if c['type']==b'@SFA' and c['kind']==1]
        self.assertEqual(movie._read_utf(header['payload'])[2][0],{'audio_codec':2,'sampling_rate':48000,'total_samples':307200,'num_channels':2,'metadata_count':0,'metadata_size':0,'ixsize':27860,'ambisonics':0,'channel_config':0})
        directory=movie._read_utf(parts[0]['payload'])[2]
        self.assertEqual(directory[0]['filesize'],len(result))
        self.assertEqual(directory[-1]['stmid'],int.from_bytes(b'@SFA','big'))
        with self.assertRaises(ValueError):movie.with_soundtrack(result,adx)
        with self.assertRaises(ValueError):movie.native_adx(adx[:-1])
        changed=bytearray(adx);changed[7]=1
        with self.assertRaises(ValueError):movie.native_adx(changed)

    def test_utf_round_trips_strings_signed_numbers_and_aligned_binary(self):
        columns=[('id',5),('name',10),('payload',11),('number',8)]
        rows=[{'id':-1,'name':'cave','payload':b'abc','number':1.5},{'id':42,'name':'cave','payload':b'12345','number':2.5}]
        self.assertEqual(movie._read_utf(movie._write_utf('test',columns,rows)),('test',columns,rows))

    def test_local_encoded_movie_cache_verifies_content_before_reuse(self):
        import _ffr_cave_music_preview as preview
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);tools=root/'tools';tools.mkdir()
            (tools/'cave_music_preview.zip').write_bytes((ROOT/'assets/existing_visions/payload/cave_music_preview.zip').read_bytes())
            def encode(cmd,**kwargs):
                self.assertTrue(cmd[-1].endswith('VGAudio.dll'))
                Path(cmd[-2]).write_bytes(adx_fixture());return SimpleNamespace(returncode=0)
            with mock.patch.object(preview,'audio',return_value=b'wave'),mock.patch.object(music.subprocess,'run',side_effect=encode) as run,mock.patch.object(movie,'with_soundtrack',return_value=(b'local movie',{})):
                first=music.movie_audio({'ROOT':root,'ffrenv':None},b'pictures')
                self.assertIsNotNone(first);self.assertEqual(first.read_bytes(),b'local movie')
                self.assertEqual(music.movie_audio({'ROOT':root,'ffrenv':None},b'pictures'),first)
                self.assertEqual(run.call_count,1)
                first.write_bytes(b'corrupt');music.movie_audio({'ROOT':root,'ffrenv':None},b'pictures')
                self.assertEqual(run.call_count,2);self.assertEqual(first.read_bytes(),b'local movie')


if __name__=='__main__':unittest.main()
