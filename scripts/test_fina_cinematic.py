"""Movie transport, audio synchronization and opt-out behavior."""
import copy
import hashlib
import io
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock
import zipfile

from test_existing_visions import ROOT
import _ffr_fina_cinematic as film
import _ffr_testing as testing
import cri_usm_movie as usm


class CinematicTests(unittest.TestCase):
    def test_runtime_test_uses_the_exact_reviewed_lighter_movie(self):
        spec, files = film.payload()
        source = spec['sourceMovie']
        self.assertEqual(source['name'], 'Crystal-Fina-Rotating-Lighter.mp4')
        self.assertEqual(source['sha256'], '680e099c04a03f5e0e7206e2a2d5b8bb843613e218f7ee213d390b66a6b649c5')
        self.assertEqual((source['width'], source['height'], source['frames']), (1920, 1080, 192))
        self.assertTrue(spec['previewMatchesSource'])
        self.assertFalse(spec['artworkRerendered'])
        self.assertEqual(hashlib.sha256(files['preview.mp4']).hexdigest(), source['sha256'])
        self.assertEqual(spec['materialVariant'], 'lighter')

    def test_movie_headers_and_seek_offsets_match_native_container_conventions(self):
        spec, files = film.payload(); raw = files['movie.usm']; parts = usm.chunks(raw)
        self.assertTrue(all(p['position'] % 32 == 0 and p['size'] % 32 == 0 for p in parts))
        packets = [p for p in parts if p['type'] == b'@SFV' and p['kind'] == 0]
        metadata = [p for p in parts if p['type'] == b'@SFV' and p['kind'] == 3]
        header, = [p for p in parts if p['type'] == b'@SFV' and p['kind'] == 1]
        row, = usm.integer_rows(header['payload'])
        self.assertEqual(usm.value(header['payload'], row, 'metadata_size'), sum(p['size'] for p in metadata))
        self.assertEqual(usm.value(header['payload'], row, 'ixsize'), max(p['size'] for p in packets))
        self.assertEqual(spec['maxPictureDataSize'], max(p['size'] for p in packets))
        self.assertEqual(len(packets), 192)
        for channel, codec in [(b'@SFV', 9), (b'@ALP', 1)]:
            stream = [p for p in parts if p['type'] == channel and p['kind'] == 0]
            header, = [p for p in parts if p['type'] == channel and p['kind'] == 1]
            row, = usm.integer_rows(header['payload'])
            self.assertEqual(usm.value(header['payload'], row, 'mpeg_codec'), codec)
            self.assertEqual(usm.value(header['payload'], row, 'total_frames'), 192)
            self.assertEqual((usm.value(header['payload'], row, 'width'),
                              usm.value(header['payload'], row, 'height')), (1920, 1080))
            self.assertEqual(len(stream), 192)
            for part in (p for p in parts if p['type'] == channel and p['kind'] == 3):
                for seek in usm.integer_rows(part['payload']):
                    self.assertEqual(usm.value(part['payload'], seek, 'ofs_byte'),
                                     stream[usm.value(part['payload'], seek, 'ofs_frmid')]['position'])
        root = parts[0]['payload']
        row, = [r for r in usm.integer_rows(root) if usm.value(root, r, 'stmid') == 0]
        self.assertEqual(usm.value(root, row, 'filesize'), len(raw))

    def test_container_normalization_repairs_lengths_without_changing_a_video_packet(self):
        raw = film.payload()[1]['movie.usm']; parts = usm.chunks(raw)
        broken = bytearray(raw)
        for part in parts:
            if part['type'] == b'@SFV' and part['kind'] == 1:
                row, = usm.integer_rows(part['payload'])
                usm.put(part['payload'], row, 'metadata_size', 7)
                usm.put(part['payload'], row, 'ixsize', 8)
                start = part['position'] + len(part['header'])
                broken[start:start+len(part['payload'])] = part['payload']
        fixed, report = usm.normalize(bytes(broken), opaque_alpha=True)
        self.assertEqual(fixed, raw)
        self.assertEqual(report['chunkAlignment'], 32)
        self.assertEqual([p['payload'] for p in usm.chunks(fixed) if p['kind'] == 0],
                         [p['payload'] for p in usm.chunks(bytes(broken)) if p['kind'] == 0])
        with self.assertRaisesRegex(ValueError, 'bounds|Truncated'):
            usm.normalize(raw[:-1], opaque_alpha=True)

    def test_every_frame_has_native_opacity_with_matching_presentation_time(self):
        spec, files = film.payload()
        self.assertTrue(spec['opaqueAlpha'])
        self.assertEqual(spec['alphaCodec'], 'SofdecPrime')
        parts = usm.chunks(files['movie.usm'])
        color = [p for p in parts if p['type'] == b'@SFV' and p['kind'] == 0]
        alpha = [p for p in parts if p['type'] == b'@ALP' and p['kind'] == 0]
        self.assertEqual(len(alpha), 192)
        self.assertTrue(all(hashlib.sha256(p['payload']).hexdigest() ==
            '5d7aecb273db8cebabf70319bdd35c11731bb85312330034dfc45f93994067d3' for p in alpha))
        self.assertEqual([p['header'][16:24] for p in color], [p['header'][16:24] for p in alpha])
        with self.assertRaisesRegex(ValueError, 'video-only'):
            usm.normalize(files['movie.usm'])

    def test_approved_art_and_playable_media_are_checksum_pinned(self):
        spec, files = film.payload()
        self.assertEqual(spec['artSha256'], hashlib.sha256((ROOT/'artwork/crystal_fina_cinematic.png').read_bytes()).hexdigest())
        self.assertEqual(spec['seconds'], 6.4)
        self.assertEqual(spec['revision'], 'crystal-fina-film-2')
        self.assertEqual(spec['eyeColor'], 'red')
        self.assertEqual(spec['cameraZoom'], [1, 5.05])
        self.assertEqual(spec['spinAxis'], 'vertical')
        self.assertGreater(spec['spinDegreesPerSecond'], 0)
        self.assertEqual(spec['eyesOpenFrames'], [156, 177])
        self.assertFalse(spec['fractures'] or spec['shards'] or spec['whiteout'])
        self.assertEqual(spec['layers'], {p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT/'artwork/crystal_fina_layers').glob('*.png')})
        audio = json.loads(files['audio.json'])
        self.assertEqual(audio['recordings'][0]['samples'], 307200)
        self.assertEqual(audio['waves']['0']['sha256'], hashlib.sha256(files['score.hca']).hexdigest())
        # A corrupt media file is rejected before writing a pak or changing a row.
        original = ROOT/'assets/existing_visions/payload/fina_cinematic.zip'
        stream = io.BytesIO()
        with zipfile.ZipFile(original) as source, zipfile.ZipFile(stream, 'w') as changed:
            for name in source.namelist():
                changed.writestr(name, b'changed' if name == 'movie.usm' else source.read(name))
        with self.assertRaisesRegex(ValueError, 'checksum'): film.validate(stream.getvalue())

    def test_old_settings_default_off_and_templates_are_not_read(self):
        with tempfile.TemporaryDirectory() as root:
            self.assertFalse(film.enabled(root))
            film.ensure_assets(root, lambda _: self.fail('Disabled movie should not extract assets'))
            film.build([], {'ROOT':root, 'LEGACY':root, 'OUT':root, 'FFRDT':[], 'USMAP':'',
                            'run':lambda _:self.fail('Disabled movie should not run tools'), 'ffrenv':SimpleNamespace()})
        with self.assertRaises(ValueError): testing.validate_settings({'schema':1,'maxMr':False,'finaCinematic':1})

    def test_continuation_preserves_every_gameplay_event_and_heal_sound_offset(self):
        plan = {'duration':220000, 'events':[
            {'time':12000, 'set':{'EventType':'UnitPlayAnimByName','Unit_PlayAnimByName_AnimationName':'LB1'}},
            {'time':12000, 'set':{'EventType':'SoundPlayHitSound','Sound_PlayHitSound_playLabel':'se_battle_limitopen_1__v1'}},
            {'time':12000, 'set':{'EventType':'SoundPlayHitSound','Sound_PlayHitSound_playLabel':film.SCORE+'__v1'}},
            {'time':65600, 'set':{'EventType':'OtherReaction','Other_Reaction_Id':444030}},
            {'time':65600, 'set':{'EventType':'SoundPlayHitSound','Sound_PlayHitSound_playLabel':'se_magic_heal_1__v1'}},
            {'time':190000, 'set':{'EventType':'UnitPlayAnimByName','Unit_PlayAnimByName_AnimationName':'idle'}}]}
        before = copy.deepcopy(plan); result = film.continuation(plan)
        self.assertEqual(before, plan)
        shift = film.END - 12000
        for event in plan['events']:
            if event['set']['EventType'] != 'SoundPlayHitSound':
                self.assertIn({'time':event['time']+shift,'set':event['set']}, result['events'])
        sounds={e['set']['Sound_PlayHitSound_playLabel']:e['time'] for e in result['events'] if e['set']['EventType']=='SoundPlayHitSound'}
        self.assertEqual(sounds['se_battle_limitopen_1__v1'], 0)
        self.assertEqual(sounds[film.SCORE+'__v1'], film.START)
        reaction,=[e for e in result['events'] if e['set']['EventType']=='OtherReaction']
        self.assertEqual(reaction['time'],sounds['se_magic_heal_1__v1'])
        self.assertEqual(result['duration'],plan['duration']+shift)
        self.assertTrue(all(0<=e['time']<result['duration'] for e in result['events']))
        self.assertEqual(sum(e['set']['EventType']=='OtherReaction' for e in result['events']),1)
        ui=[e for e in result['events'] if e['set']['EventType'].startswith('UI')]
        self.assertEqual(ui,[
            {'time':film.START,'set':{'EventType':'UISetVisibility',
                'UI_SetVisibillity_IsVisibility':False,'UI_SetVisibillityMovie_IsVisibility':True}},
            {'time':film.END,'set':{'EventType':'UISetVisibility',
                'UI_SetVisibillity_IsVisibility':True,'UI_SetVisibillityMovie_IsVisibility':True}}])
        too_long=copy.deepcopy(plan);too_long['duration']=film.NATIVE_DURATION
        with self.assertRaisesRegex(ValueError,'duration'):film.continuation(too_long)

    def test_changed_movie_timing_refreshes_only_private_evaluation_signatures(self):
        asset='FFRS/Content/Sequencer/Battle/Skill/444010/444011/SEQ_Battle_444011_Master'
        updates=film.evaluation_updates(asset)
        self.assertEqual({u['export'] for u in updates}, {'SEQ_Battle_444011_Master', 'MovieScene_0',
            'MovieSceneManaSection_1','MovieSceneManaTrack_1','MovieSceneSpawnSection_0','MovieSceneSpawnTrack_1'})
        self.assertTrue(all(u['asset']==asset and u['set']=={'Signature':'new'} for u in updates))

    def test_pak_includes_movie_and_disabling_replaces_only_its_companion(self):
        calls=[]
        with tempfile.TemporaryDirectory() as root:
            root=Path(root); other=root/'build/out/other.pak';other.parent.mkdir(parents=True);other.write_bytes(b'other')
            def run(command):
                calls.append(command)
                stage=Path(command[-2]); content={p.relative_to(stage).as_posix():p.read_bytes().hex() for p in stage.rglob('*') if p.is_file()}
                Path(command[-1]).write_text(json.dumps(content))
            environment=SimpleNamespace(MOD_NAME='EstherTsukiko')
            obsolete=root/'build/fina-cinematic/pak-input'/(film.PRIVATE+'.usm')
            obsolete.parent.mkdir(parents=True);obsolete.write_bytes(b'old misplaced movie')
            film.prepare_pak(root,environment,run,b'CRID test media')
            pak=root/'build/out/zzz_EstherTsukiko_P.pak'
            self.assertEqual(json.loads(pak.read_bytes()),{film.VIDEO:b'CRID test media'.hex()})
            self.assertEqual(film.VIDEO,'FFRS/Content/Streams/Movies/Studio/CrystalFina_Test.usm')
            self.assertFalse(obsolete.exists())
            self.assertIn('V11',calls[0])
            film.prepare_pak(root,environment,run)
            self.assertEqual(json.loads(pak.read_bytes()),{})
            self.assertEqual(other.read_bytes(),b'other')
            film.prepare_pak(root,environment,lambda _:self.fail('Already disabled should do no work'))

    def test_score_augments_existing_banks_and_honors_mute(self):
        unit={'ffbe':{'id':film.SPRITE},'lb_custom':{'presentation':'ffbe'}}
        bank={'name':'existing','additionalBanks':[{'name':'opening'}]};events=[{'frame':20}]
        before=copy.deepcopy((unit,bank,events))
        with tempfile.TemporaryDirectory() as root:
            config=Path(root)/testing.CONFIG;config.parent.mkdir(parents=True)
            config.write_text(json.dumps({'schema':1,'maxMr':False,'finaCinematic':True}))
            def prepare(u, skill, source, table):
                self.assertFalse(skill['lb_charge'])
                self.assertEqual(source['sounds'][0]['role'],'fina_cinematic')
                self.assertTrue(Path(skill['audio_bank']).is_file())
                return {'name':'intro'},[{'frame':0,'role':'fina_cinematic'}]
            audio=SimpleNamespace(ROOT=root,prepare=prepare)
            with mock.patch.dict('sys.modules',{'ffbe_audio':audio}):
                result,sounds=film.attach_audio(unit,{},bank,events,lambda _:None)
                self.assertEqual([b['name'] for b in result['additionalBanks']],['opening','intro'])
                self.assertEqual(len(sounds),2)
                with mock.patch.object(audio,'prepare',side_effect=AssertionError('Muted')):
                    self.assertEqual(film.attach_audio(unit,{'audio':'none','sephiraAudio':1},bank,events,None),(bank,events))
        self.assertEqual((unit,bank,events),before)

    def test_browser_preview_is_read_only(self):
        routes={}
        class App:
            def get(self,path,**_):return lambda fn:routes.setdefault(path,fn)
        film.register(App())
        self.assertEqual(set(routes),{'/crystal-fina-cinematic','/api/testing/fina-cinematic/preview','/api/testing/fina-cinematic/poster'})
        response=routes['/api/testing/fina-cinematic/preview']()
        self.assertEqual(response.media_type,'video/mp4')
        self.assertEqual(response.body,film.payload()[1]['preview.mp4'])


if __name__=='__main__':unittest.main()
