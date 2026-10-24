"""Voice-only substitutions, native movie packet integrity and warm build reuse."""
import contextlib
import copy
import io
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock
import zipfile

from test_existing_visions import ROOT, native, fixture
from test_movie_audio import adx_fixture
from test_party_voices import track
import _ffr_movie_audio as movie
import _ffr_native_voices as voices


def movie_fixture():
    with zipfile.ZipFile(ROOT/'assets/existing_visions/payload/fina_cinematic.zip') as z:raw=z.read('movie.usm')
    raw=movie.with_soundtrack(raw,adx_fixture())[0];parts=movie.chunks(raw)
    name,columns,rows=movie._read_utf(parts[0]['payload']);rows[-1]['filename']='VO_NATIVE_TEST.sfa'
    parts[0]['payload']=bytearray(movie._write_utf(name,columns,rows))
    header=next(p for p in parts if p['type']==b'@SFA' and p['kind']==1)
    name,columns,rows=movie._read_utf(header['payload'])
    columns=[(k,0 if k in ('audio_codec','num_channels','ambisonics') else 4) for k,_ in columns]
    header['payload']=bytearray(movie._write_utf(name,columns,rows))
    return movie.normalize(movie.pack_chunks(parts),opaque_alpha=True,soundtrack=True)[0]


class NativeVisionVoiceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.movie=movie_fixture()

    def test_selection_and_native_config_validation(self):
        data,rows,u=fixture();self.assertEqual(voices.selected([u]),[])
        u['nativeVoice']=u['id'];self.assertEqual(voices.selected([u]),[])
        data[voices.VISION]['Tronn']={**data[voices.VISION]['Cloud'],'ID':13024}
        u['nativeVoice']=13024;native.validate(u,lambda rel:copy.deepcopy(data[rel]))
        self.assertEqual(voices.selected([u]),[u])
        for bad in (True,0,-1,'13024',999999):
            with self.subTest(bad=bad),self.assertRaises(ValueError):
                native.validate(dict(u,nativeVoice=bad),lambda rel:copy.deepcopy(data[rel]))

    def test_native_movie_voice_preserves_every_picture_timestamp_and_seek(self):
        adx=bytearray(adx_fixture());adx[40:76]=bytes([1])*36
        donor=voices.encoded_movie_voice(self.movie,bytes(adx))
        result,info=voices.replace_movie_voice(self.movie,donor)
        self.assertEqual(info['total_samples'],307200)
        self.assertEqual(voices.adx_stream(result)[0],voices.adx_stream(donor)[0])
        old=[p for p in movie.chunks(self.movie) if p['type'] in (b'@SFV',b'@ALP') and p['kind']==0]
        new=[p for p in movie.chunks(result) if p['type'] in (b'@SFV',b'@ALP') and p['kind']==0]
        self.assertEqual([(p['type'],p['payload'],p['header'][12:]) for p in old],[(p['type'],p['payload'],p['header'][12:]) for p in new])
        chunks=movie.chunks(result);positions={p['position'] for p in new}
        for p in chunks:
            if p['type'] in (b'@SFV',b'@ALP') and p['kind']==3:
                self.assertTrue(all(movie.value(p['payload'],row,'ofs_byte') in positions for row in movie.integer_rows(p['payload'])))
        for p in chunks:
            if p['type']==b'@SFA' and p['kind']==2 and b'CONTENTS END' in p['payload']:
                self.assertGreater(p['position'],max(q['position'] for q in chunks if q['type']==b'@SFA' and q['kind']==0))
        self.assertEqual(movie._read_utf(chunks[0]['payload'])[2][0]['filesize'],len(result))
        header=next(p for p in chunks if p['type']==b'@SFA' and p['kind']==1)
        types=dict(movie._read_utf(header['payload'])[1]);self.assertEqual(types['num_channels'],0);self.assertEqual(types['total_samples'],4)

    def test_mixed_or_unfamiliar_movie_soundtracks_are_rejected(self):
        parts=movie.chunks(self.movie);name,cols,rows=movie._read_utf(parts[0]['payload']);rows[-1]['filename']='BGM_MIXED.sfa'
        parts[0]['payload']=bytearray(movie._write_utf(name,cols,rows))
        with self.assertRaisesRegex(ValueError,'effects/music'):voices.adx_stream(movie.pack_chunks(parts))

    def test_pcm_roundtrip_and_movie_phrase_selection_keep_opening_and_final(self):
        samples=[(i,-i) for i in range(1000)]
        self.assertEqual(voices.pcm(voices.wave(samples)),samples)
        samples=[(0,0)]*4800+[(2000,-2000)]*9600+[(0,0)]*24000+[(3000,-3000)]*9600+[(0,0)]*4800
        phrases=voices.phrases(samples);self.assertEqual(len(phrases),2)
        self.assertIn((2000,-2000),phrases[0]);self.assertIn((3000,-3000),phrases[1])
        self.assertEqual([voices.choose(['open','middle','finish'],i,2) for i in range(2)],['open','finish'])
        with self.assertRaisesRegex(ValueError,'audible'):voices.phrases([(0,0)]*100)

    def test_direct_cues_change_only_voice_references(self):
        view=track([('VO_BTL_TEST_004_Cue',8800),('SE_IMPACT_Cue',20000),('VO_BTL_TEST_005_Cue',64800)])
        view['Imports'].extend([{'ObjectName':'/Game/Sound/OldVoice'},{'ObjectName':'/Game/Sound/Effect'}])
        for i in (1,3):view['Imports'][i]['OuterIndex']=-5
        view['Imports'][2]['OuterIndex']=-6
        target={'voices':[{'asset':'track','index':i,'export':view['Exports'][i]['ObjectName'],'cue':view['Imports'][i+1]['ObjectName']} for i in (0,2)]}
        with tempfile.TemporaryDirectory() as temporary:
            def run(args):
                path=Path(args[2]) if args[1]=='patch' else Path(args[3])
                if args[1]=='patch':
                    plan=json.loads(path.read_bytes());self.assertEqual(len(plan['objects']),2)
                    self.assertTrue(all(set(o['set'])=={'Sound'} for o in plan['objects']))
                    actual=copy.deepcopy(view)
                    for op in plan['objects']:
                        package=op['set']['Sound'];actual['Imports'].append({'ObjectName':package})
                        parent=-len(actual['Imports']);actual['Imports'].append({'ObjectName':package.rsplit('/',1)[-1],'OuterIndex':parent})
                        section=next(e for e in actual['Exports'] if e['ObjectName']==op['export'])
                        section['Data'][0]['Value']=-len(actual['Imports'])
                    written['track']=actual
                else:path.write_text(json.dumps(written['track']))
            b=voices.Builder({'ROOT':temporary,'LEGACY':temporary,'OUT':temporary,'FFRDT':['tool'],'USMAP':'map','run':run})
            b.views['track']=view;written={}
            b.sound_edits(target,[('/Game/Sound/VO_A','VO_A'),('/Game/Sound/VO_B','VO_B')])
            actual=written['track']
            self.assertEqual(actual['Exports'][1],view['Exports'][1])
            for i in (0,2):
                self.assertEqual(actual['Exports'][i]['Data'][1:],view['Exports'][i]['Data'][1:])
            self.assertEqual(view['Imports'][1]['ObjectName'],'VO_BTL_TEST_004_Cue')
            self.assertEqual(voices.party.import_name(actual,actual['Exports'][0]['Data'][0]['Value']),'VO_A')
            self.assertEqual(voices.party.import_name(actual,actual['Exports'][2]['Data'][0]['Value']),'VO_B')

    def test_cache_flattens_long_native_paths_under_portable_windows_roots(self):
        root=Path('C:/Users/Owner/Desktop/Sephira-Studio-Test/Studio Test Data/FFR Vision Studio/engine')
        cache=root/'build/native-voices/cache'/('a'*24)
        original='FFRS/Content/Sequencer/Battle/Skill/440110/440111/Track/SEQ_Battle_440111_Sound_001.uasset'
        self.assertLess(len(str(voices.cached_file(cache,'files',original))),240)
        self.assertEqual(voices.cached_file(cache,'files',original).suffix,'.uasset')
        self.assertNotEqual(voices.cached_file(cache,'files',original),voices.cached_file(cache,'files',original+'.uexp'))

    def test_unselected_build_is_noop(self):
        with tempfile.TemporaryDirectory() as root:
            with mock.patch.object(voices,'Builder',side_effect=AssertionError('Unexpected voice work')):
                voices.build([],{'ROOT':root})

    def test_warm_voice_cache_checks_hashes_and_game_identity(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);tools=root/'tools';tools.mkdir();paks=root/'paks';paks.mkdir()
            for name in ('native_voice_codec.ps1','cave_music_preview.zip'):(tools/name).write_bytes(b'codec test')
            mapping=root/'map.usmap';mapping.write_bytes(b'mapping')
            official=paks/'FFRS-Windows.utoc';official.write_bytes(b'game A')
            out=root/'out';out.mkdir()
            env={'ROOT':root,'OUT':out,'LEGACY':root,'USMAP':str(mapping),'ffrenv':SimpleNamespace(game_paks=lambda:paks),
                 'rows':lambda _: {'source':{'ID':13024,'finishBlowSkill':414090}}}
            u={'id':13110,'native':{},'nativeVoice':13024,'lb':440110};u['native']={'id':13110}
            profile={'voices':[{'asset':'FFRS/Content/native-track','package':'FFRS/Content/Sound/Voice','cue':'VO_TEST'}],'movies':{}}
            def write(*_):
                (out/'FFRS/Content').mkdir(parents=True,exist_ok=True)
                for suffix in ('.uasset','.uexp'):(out/('FFRS/Content/native-track'+suffix)).write_bytes(b'verified native voice')
            with mock.patch.object(voices.Builder,'profile',return_value=profile) as discover,mock.patch.object(voices.Builder,'sound_edits',side_effect=write) as author,contextlib.redirect_stdout(io.StringIO()):
                voices.build([u],env);self.assertEqual(author.call_count,1)
                for p in out.rglob('*'):
                    if p.is_file():p.unlink()
                voices.build([u],env);self.assertEqual(author.call_count,1)
                self.assertEqual((out/'FFRS/Content/native-track.uasset').read_bytes(),b'verified native voice')
                cached=next((root/'build/native-voices/cache').rglob('*.uexp'));cached.write_bytes(b'corrupt')
                voices.build([u],env);self.assertEqual(author.call_count,2)
                official.write_bytes(b'game update B');voices.build([u],env);self.assertEqual(author.call_count,3)
                next((root/'build/native-voices/cache').glob('*/manifest.json')).write_text('invalid cache metadata')
                # A damaged manifest is recoverable; it never becomes a config error.
                for manifest in (root/'build/native-voices/cache').glob('*/manifest.json'):manifest.write_text('invalid cache metadata')
                voices.build([u],env);self.assertEqual(author.call_count,4)


if __name__=='__main__':unittest.main()
