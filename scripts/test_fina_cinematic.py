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


class CinematicTests(unittest.TestCase):
    def test_approved_art_and_playable_media_are_checksum_pinned(self):
        spec, files = film.payload()
        self.assertEqual(spec['artSha256'], hashlib.sha256((ROOT/'artwork/crystal_fina_cinematic.png').read_bytes()).hexdigest())
        self.assertEqual(spec['seconds'], 6.4)
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
        too_long=copy.deepcopy(plan);too_long['duration']=film.NATIVE_DURATION
        with self.assertRaisesRegex(ValueError,'duration'):film.continuation(too_long)

    def test_pak_includes_movie_and_disabling_replaces_only_its_companion(self):
        calls=[]
        with tempfile.TemporaryDirectory() as root:
            root=Path(root); other=root/'build/out/other.pak';other.parent.mkdir(parents=True);other.write_bytes(b'other')
            def run(command):
                calls.append(command)
                stage=Path(command[-2]); content={p.relative_to(stage).as_posix():p.read_bytes().hex() for p in stage.rglob('*') if p.is_file()}
                Path(command[-1]).write_text(json.dumps(content))
            environment=SimpleNamespace(MOD_NAME='EstherTsukiko')
            film.prepare_pak(root,environment,run,b'CRID test media')
            pak=root/'build/out/zzz_EstherTsukiko_P.pak'
            self.assertEqual(json.loads(pak.read_bytes()),{film.VIDEO:b'CRID test media'.hex()})
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
