"""Exact source variants, safe media reads, real Needles rendering and no mod writes."""
import copy
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import zipfile

ROOT=Path(__file__).resolve().parents[1]
PAYLOAD=ROOT/'assets/existing_visions/payload'
sys.path.insert(0,str(PAYLOAD))
import _ffr_ffbe_library as lib


def make_library(root):
    source=ROOT/'scripts/fixtures/ffbe_needles'
    rows=json.loads((source/'source-rows.json').read_bytes())
    raw_group=rows['F_EFFECT_GROUP_MST'][0]
    group={'name':'harisenbon1','effects':[{'frame':int(f[0]),'effectId':f[1],'flags':f[2:]}
        for f in lib.split_frames(raw_group['5A8SmwyC'])],
        'sounds':[{'frame':int(f[0]),'cueId':f[1],'flags':f[2:]} for f in lib.split_frames(raw_group['1fVZ3rKd'])]}
    skills=[{'key':'magic:40050','kind':'magic','id':'40050','name':'1,000 Needles','timeline':'40:5002490:1:1:0','hasAnimation':True},
            {'key':'monster:151400','kind':'monster','id':'151400','name':'1000 Needles','timeline':'40:5002490:1:1:0@10:5002490:2:1:0','hasAnimation':True},
            {'key':'ability:99','kind':'ability','id':'99','name':'Passive example','timeline':'','hasAnimation':False}]
    data={'catalog.json':{'skills':skills,'groups':[],'effects':[],'movies':[]},
          'groups.json':{'5002490':group},
          'effects.json':{'1002460':{'type':'5','file':'atk_nail1_white.bmb','asset':'atk_nail1_white.bmb','scale':1,'name':'Needles'}},
          'audio.json':{'cues':{'SE:99':{'bank':'SE','name':'se_special_needle_1','variants':[[{'at':0,'wave':'needle'}]]}},
                        'waves':{'needle':{'file':'needle.flac','samples':25088,'sampleRate':44100}}},
          'bmb-dependencies.json':{'atk_nail1_white.bmb':['position_model_circle12.m3r']}}
    members={k:json.dumps(v).encode() for k,v in data.items()}
    for p in source.iterdir():
        if p.suffix in ('.bmb','.m3r','.png'):members['raw/'+p.name]=p.read_bytes()
    folder=Path(root)/'library/ffbe';dest=folder/lib.REVISION;dest.mkdir(parents=True)
    pack=dest/'library-01.zip'
    with zipfile.ZipFile(pack,'w',zipfile.ZIP_DEFLATED) as z:
        for name,raw in members.items():z.writestr(name,raw)
    manifest={'schema':1,'revision':lib.REVISION,'summary':{'skills':3},
        'packs':[{'name':pack.name,'bytes':pack.stat().st_size,'sha256':hashlib.sha256(pack.read_bytes()).hexdigest()}],
        'files':{name:{'pack':pack.name,'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()} for name,raw in members.items()}}
    (folder/'manifest.json').write_text(json.dumps(manifest))
    return lib.Library(root),data,members


class LibraryTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name)
        self.library,self.data,self.members=make_library(self.root)

    def test_search_preserves_ids_types_and_records_without_effects(self):
        self.assertEqual(self.library.search('Needles')['total'],2)
        self.assertEqual(self.library.search('Needles',kind='monster')['items'][0]['id'],'151400')
        self.assertEqual(self.library.search('99')['total'],0)
        self.assertEqual(self.library.search('99',animated=False)['items'][0]['kind'],'ability')
        self.assertEqual(self.library.search('NEEDLES',offset=1,limit=1)['items'][0]['id'],'151400')
        for kwargs in ({'scope':'units'},{'limit':10000},{'offset':-1}):
            with self.assertRaises(ValueError):self.library.search(**kwargs)

    def test_needles_retains_all_spawns_cues_and_conditional_variant(self):
        detail=self.library.detail('magic','40050');group=detail['variants'][0][0]
        self.assertEqual(group['frame'],40)
        self.assertEqual([e['frame'] for e in group['effects']],list(range(0,41,4)))
        self.assertEqual([s['frame'] for s in group['sounds']],list(range(0,40,2)))
        self.assertEqual(len(detail['cues']),1)
        self.assertEqual(len(self.library.detail('monster','151400')['variants']),2)
        self.assertEqual(self.library.detail('monster','151400')['variants'][1][0]['frame'],10)
        with self.assertRaises(ValueError):self.library.detail('magic','151400')

    def test_real_particle_preview_preserves_ordered_placement_and_materials(self):
        state=self.root/'mods/EstherTsukiko/units.json';state.parent.mkdir(parents=True);state.write_text('private roster')
        before=state.read_bytes()
        preview=json.loads(gzip.decompress(self.library.simulation('1002460')))
        self.assertGreater(len(preview['frames']),5)
        self.assertEqual(preview['warnings'],[])
        self.assertEqual(len(preview['textures']),3)
        self.assertTrue(all(t['url'].endswith('.png') for t in preview['textures']))
        self.assertTrue(any(len({tuple(p['pos']) for p in frame})>=4 for frame in preview['frames']))
        self.assertEqual(state.read_bytes(),before)
        self.assertTrue(all(p.is_relative_to(self.root/'build') or p.is_relative_to(self.root/'library') or p==state
                            for p in self.root.rglob('*') if p.is_file()))

    def test_sprite_preview_uses_source_steps_offsets_and_hold_times(self):
        from PIL import Image
        import io
        image=Image.new('RGBA',(8,8),'red');buffer=io.BytesIO();image.save(buffer,format='PNG')
        source={'raw/sprite.png':buffer.getvalue(),
                'raw/sprite.csv':b'0,1,0,0,0,0,100,0,0,0,8,8,0\n',
                'raw/steps.csv':b'0,13,17,4\n'}
        def materialize(name):
            path=self.root/Path(name).name;path.write_bytes(source[name]);return path
        with patch.object(self.library,'materialize',side_effect=materialize), patch.object(sys,'path',[str(ROOT/'scripts/fixtures/engine_motion'),*sys.path]):
            result=self.library.sprite_simulation({'file':'sprite.png:sprite.csv:steps.csv'})
        self.assertEqual(len(result['frames']),4)
        self.assertEqual(result['frames'][0][0]['pos'],[17.0,-21.0,0])
        self.assertEqual(result['warnings'],[])

    def test_pack_corruption_and_unknown_files_are_rejected(self):
        with self.assertRaises(ValueError):self.library.read('../../config.json')
        path=self.library.directory/'library-01.zip';path.write_bytes(path.read_bytes()+b'changed')
        with self.assertRaisesRegex(ValueError,'changed|checksum'):self.library.read('catalog.json')

    def test_identical_presentations_use_first_owner_and_retain_alias_search(self):
        skill=copy.deepcopy(self.data['catalog.json']['skills'][0])
        skill.update(key='magic:40051',id='40051')
        self.data['catalog.json']['skills'].insert(1,skill)
        owners={'magic:40050':[{'name':'Agrias','type':'character'}],
                'magic:40051':[{'name':'Christine','type':'character'}]}
        before=copy.deepcopy(self.data)
        with patch.object(self.library,'document',side_effect=self.data.__getitem__), \
                patch.object(self.library,'browser',return_value={'owners':owners}):
            results=self.library.search('Needles')
            self.assertEqual(results['total'],2)  # Character and monster presentations remain separate.
            entry=results['items'][0]
            self.assertEqual(entry['sourceLabel'],'Agrias')
            self.assertEqual(entry['equivalentCount'],2)
            self.assertEqual(self.library.search('Christine')['items'][0]['key'],'magic:40050')
            self.assertEqual(self.library.detail('magic','40051')['entry']['id'],'40051')
        self.assertEqual(self.data,before)

    def test_distinct_timing_sounds_target_flags_and_sprite_sequences_remain_separate(self):
        base=self.data['catalog.json']['skills'][0]
        # Make the enemy's name identical too: origin, not spelling, must preserve it.
        self.data['catalog.json']['skills'][1].update(name=base['name'],timeline=base['timeline'])
        self.data['effects.json']['1002460']={'type':'1','file':'atlas.png:pieces.csv:idle.csv','scale':1}
        cases=('group-time','effect-time','target','sound','sprite','hits')
        for i,case in enumerate(cases,1):
            skill={**base,'key':f'magic:{40050+i}','id':str(40050+i)}
            group=copy.deepcopy(self.data['groups.json']['5002490'])
            gid=str(5002490+i)
            skill['timeline']=f'40:{gid}:1:1:0'
            if case=='group-time':skill['timeline']=f'41:{gid}:1:1:0'
            if case=='effect-time':group['effects'][0]['frame']+=1
            if case=='target':group['effects'][0]['flags'][0]='different-target'
            if case=='sound':group['sounds'][0]['cueId']='another-sound'
            if case=='sprite':
                self.data['effects.json']['123']={'type':'1','file':'atlas.png:pieces.csv:other-motion.csv','scale':1}
                group['effects'][0]['effectId']='123'
            if case=='hits':skill['hits']='75:100'
            self.data['groups.json'][gid]=group
            self.data['catalog.json']['skills'].append(skill)
        with patch.object(self.library,'document',side_effect=self.data.__getitem__), \
                patch.object(self.library,'browser',return_value={'owners':{}}):
            self.assertEqual(self.library.search('Needles')['total'],len(cases)+2)

    def test_corrupt_owned_source_cache_is_recovered_from_verified_pack(self):
        path=self.library.materialize('raw/atk_nail1_white.bmb');path.write_bytes(b'changed')
        self.assertEqual(self.library.materialize('raw/atk_nail1_white.bmb').read_bytes(),self.members['raw/atk_nail1_white.bmb'])

    def test_routes_only_read_and_reject_arbitrary_media_or_texture_paths(self):
        routes={}
        class App:
            def get(self,path):
                def add(fn):routes[path]=fn;return fn
                return add
            post = get
        class HTTPException(Exception):
            def __init__(self,status,detail):self.status_code=status;super().__init__(detail)
        def response(body,**kwargs):return SimpleNamespace(body=body,**kwargs)
        with patch.dict('sys.modules',{'fastapi':SimpleNamespace(HTTPException=HTTPException),
                'fastapi.responses':SimpleNamespace(Response=response,HTMLResponse=response,FileResponse=response)}):
            lib.register(App(),{'ROOT':str(self.root)})
            self.assertEqual(routes['/api/ffbe-library/catalog'](q='Needles')['total'],2)
            self.assertIn('FFBE Animation Library',routes['/ffbe-animation-library']().body)
            for route,arg in (('/api/ffbe-library/file/{name:path}','../config.json'),
                              ('/api/ffbe-library/preview-texture/{name}','../../private.png')):
                with self.assertRaises(HTTPException):routes[route](arg)
        self.assertNotIn('prepare',routes)


class PackagedCatalogTests(unittest.TestCase):
    def test_large_packs_are_optional_and_browser_bundle_has_named_owners_and_real_actors(self):
        self.assertNotIn('- assets/ffbe_library/',(ROOT/'pubspec.yaml').read_text())
        self.assertEqual(json.loads((PAYLOAD/'ffbe_library_manifest.json').read_bytes()),
                         json.loads((ROOT/'assets/ffbe_library/manifest.json').read_bytes()))
        from PIL import Image
        import io
        with zipfile.ZipFile(PAYLOAD/'ffbe_library_browser.zip') as archive:
            data=json.loads(archive.read('browser.json'))
            self.assertGreater(len(data['owners']),39000)
            self.assertTrue(any(o['name']=='Agrias' for owners in data['owners'].values() for o in owners))
            self.assertEqual({a['name'] for a in data['actors'].values()},{'Christine','Cactuar'})
            for actor in data['actors'].values():
                image=Image.open(io.BytesIO(archive.read(actor['file'])))
                self.assertEqual(image.width,actor['width']*actor['columns'])
                self.assertEqual(len(actor['durations']),actor['frames'])
                self.assertGreater(actor['frames'],1)
                self.assertTrue(all(0<d<1 for d in actor['durations']))
                self.assertEqual(image.mode,'RGBA')
                self.assertGreater(image.getbbox()[2],20)
        app=(ROOT/'lib/state/app_state.dart').read_text()
        self.assertNotIn('FfbeAnimationLibrary',app)

    def test_all_five_source_tables_and_variants_are_preloaded_without_assignment(self):
        manifest=json.loads((ROOT/'assets/ffbe_library/manifest.json').read_bytes())
        self.assertEqual(manifest['summary']['skills'],65428)
        self.assertEqual(manifest['summary']['byKind'],{'magic':486,'ability':43536,'monster':17926,'lb':3417,'summon':63})
        self.assertEqual(manifest['summary']['missingSoundCueIds'],[])
        self.assertEqual(manifest['summary']['groups'],15674)
        self.assertGreater(manifest['summary']['cinematicClips'],60)
        self.assertTrue(all(p['bytes']<100*1024*1024 for p in manifest['packs']))
        # Catalog presence is separate from all mod builder inputs.
        source=(PAYLOAD/'_ffr_ffbe_library.py').read_text()
        import re
        self.assertEqual(re.findall(r"@app.post\('([^']+)'\)", source),
                         ['/api/ffbe-library/download','/api/ffbe-library/download/cancel'])
        self.assertNotIn('@app.put(',source)
        self.assertNotIn('make_vision_mod',source)


if __name__=='__main__':unittest.main()
