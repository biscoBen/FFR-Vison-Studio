"""Source joins and portable fog alpha, including the native triangle fill rule."""
import gzip
import hashlib
import io
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import zipfile
import numpy as np
from PIL import Image
from test_ffbe_animation_library import make_library
import build_ffbe_library_browser as builder
import _ffr_ffbe_renderer as renderer


def quad(alpha=.5):
    return {'vertices':[(-1,1,0),(1,1,0),(1,-1,0),(-1,-1,0)],
            'colors':[(1,1,1,alpha)]*4,'uvs':[(0,0),(1,0),(1,1),(0,1)],
            'indices':[0,1,2,0,2,3]}


class FogEdgesTests(unittest.TestCase):
    def test_billboard_fog_sampler_stores_the_same_portable_alpha(self):
        import _ffr_ffbe_texture as textures
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);Image.new('RGBA',(32,32),'white').save(root/'source_cloud1.png')
            channel={'pivot':[.5,.5,.5],'translation':[0,0,0],'rotation':[0,0,0],'scaling':[1,1,1],'unsupported':[]}
            data={'texture':'source_cloud1','channels':[channel],'wrap':1,'fogEdgeFade':.075}
            with patch.object(textures,'MESH_SPRITE_DIR',str(root/'generated')):
                actual=textures.TextureCache([tmp]).get('nativeuv:'+json.dumps(data))
            self.assertEqual(actual[0,:,3].max(),0)
            self.assertEqual(actual[:,0,3].max(),0)
            self.assertEqual(actual[16,16,3],1)

    def test_translucent_quad_diagonal_is_shaded_once_with_either_winding(self):
        texture=np.ones((2,2,4),dtype=np.float32)
        for indices in ([0,1,2,0,2,3],[2,1,0,3,2,0]):
            mesh=quad();mesh['indices']=indices
            actual=renderer.rasterise_mesh(mesh,texture,size=32)
            np.testing.assert_allclose(actual[...,3],.5)
            np.testing.assert_allclose(actual[...,:3],1.)

    def test_converted_png_alpha_feathers_real_geometry_without_darkening_rgb(self):
        raw=renderer.rasterise_mesh(quad(.6),np.ones((2,2,4),dtype=np.float32),size=64)
        soft=renderer.rasterise_mesh(quad(.6),np.ones((2,2,4),dtype=np.float32),size=64,fog_edge_fade=.075)
        self.assertEqual(float(soft[0,:,3].max()),0)
        self.assertEqual(float(soft[-1,:,3].max()),0)
        self.assertEqual(float(soft[:,0,3].max()),0)
        self.assertEqual(float(soft[:,-1,3].max()),0)
        self.assertAlmostEqual(float(soft[32,32,3]),.6)
        np.testing.assert_allclose(soft[...,:3],raw[...,:3])
        self.assertTrue(np.all(soft[...,3]<=raw[...,3]))
        # The feather is stored in PNG alpha, independent of canvas masking.
        stream=io.BytesIO();Image.fromarray((soft*255).astype('uint8')).save(stream,format='PNG')
        with Image.open(io.BytesIO(stream.getvalue())) as image:
            for size in [(480,270),(270,480),(128,128)]:
                resized=np.asarray(image.resize(size,Image.Resampling.BILINEAR))
                self.assertEqual(resized[0,:,3].max(),0)
                self.assertEqual(resized[:,0,3].max(),0)
                self.assertGreater(resized[size[1]//2,size[0]//2,3],145)

    def test_feather_applies_to_fog_boundaries_not_additive_or_already_faded_art(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp)/'sheet.m3r').touch()
            def context(index,texture,blend=1):
                return SimpleNamespace(emitter=SimpleNamespace(index=index,texture=texture,blend=blend,model='sheet'))
            cases=[context(1,'source_cloud1'),context(2,'source_cloud1',2),context(3,'source_stone1')]
            with patch.object(renderer,'parse_m3r',return_value=quad(1)):
                self.assertEqual(renderer.fog_edge_emitters(cases,[tmp]),{1})
            billboard=context(4,'source_smoke1');billboard.emitter.model=None
            self.assertEqual(renderer.fog_edge_emitters([billboard],[tmp]),{4})
            faded=quad(0);faded['vertices'].append((0,0,0));faded['colors'].append((1,1,1,1));faded['uvs'].append((.5,.5))
            faded['indices']=[0,1,4,1,2,4,2,3,4,3,0,4]
            with patch.object(renderer,'parse_m3r',return_value=faded):
                self.assertEqual(renderer.fog_edge_emitters(cases,[tmp]),set())

    def test_conversion_archive_retains_exact_png_and_world_dimensions(self):
        with tempfile.TemporaryDirectory() as tmp:
            library,_,_=make_library(tmp);library.cache.mkdir(parents=True)
            pixels=renderer.rasterise_mesh(quad(1),np.ones((2,2,4),dtype=np.float32),size=32,fog_edge_fade=.1)
            stream=io.BytesIO();Image.fromarray((pixels*255).astype('uint8')).save(stream,format='PNG');raw=stream.getvalue()
            name=hashlib.sha256(raw).hexdigest()+'.png';(library.cache/name).write_bytes(raw)
            simulation={'textures':[{'url':'/api/ffbe-library/preview-texture/'+name}],
                        'frames':[[{'tex':0,'uv':[0,0,1,1],'pos':[4,8,2],'scale':[120,80],'alpha':1,'blend':'normal'}]],
                        'fps':60,'frameCount':1,'conversion':{'fogEdges':'soft'}}
            with patch.object(library,'simulation',return_value=gzip.compress(json.dumps(simulation).encode())):
                archive=library.conversion_archive('1002460')
            with zipfile.ZipFile(io.BytesIO(archive)) as z:
                doc=json.loads(z.read('doc.json'));self.assertEqual(z.read(doc['textures'][0]),raw)
                part=doc['frames'][0][0]
                self.assertEqual(part['uv'],[0,0,32,32])
                self.assertEqual(part['scale'],[3.75,2.5]);self.assertEqual(part['pos'],[4,8])
                self.assertFalse(doc['gameAssigned']);self.assertEqual(doc['scope'],'visual-layer-only')
                compile(z.read('convert_to_ss6.py'),'convert_to_ss6.py','exec')
                self.assertFalse(any(n.endswith(('.uasset','.pak','.ini')) for n in z.namelist()))
            (library.cache/name).write_bytes(b'changed')
            with patch.object(library,'simulation',return_value=gzip.compress(json.dumps(simulation).encode())):
                with self.assertRaisesRegex(ValueError,'checksum'):library.conversion_archive('1002460')


class OwnershipBuilderTests(unittest.TestCase):
    def test_exact_global_grants_cover_missing_units_and_explicit_esper_status_links(self):
        tables={name:[] for name in builder.OWNER_TABLES}
        tables.update({'F_MAGIC_MST':[{'QV1HE7Wq':'20210','G4L0YIB2':'Blizzaga'}],
            'F_ABILITY_MST':[{'Ga5V42LZ':'100740','G4L0YIB2':'Auto-Refresh'},
                             {'Ga5V42LZ':'42','G4L0YIB2':'Different record'}],
            'F_UNIT_MST':[{'3HriTp6B':'100','woghJa61':'100','G4L0YIB2':'Lasswell'}],
            'F_UNIT_SERIES_LV_ACQUIRE_MST':[{'woghJa61':'100','i6kc1jN0':'20210'},
                                            {'woghJa61':'401002606','1Zsh27mS':'100740'}],
            'F_BEAST_MST':[{'Iwfx42Wo':'2','G4L0YIB2':'Ifrit'}],
            'F_BEAST_SKILL_MST':[{'76LymtEu':'20101','G4L0YIB2':'Hellfire','KF9Av5yX':'1'}],
            'F_BEAST_STATUS_MST':[{'Iwfx42Wo':'2','76LymtEu':'20101'}]})
        global_data={'units.json':{'401002605':{'name':'Christine','entries':{'401002606':{}},
                        'skills':[{'type':'MAGIC','id':20210},{'type':'ABILITY','id':912855},{'type':'ABILITY','id':42}]},
                     '900':{'name':'Another missing unit','entries':{},'skills':[{'type':'ABILITY','id':9001}]}},
            'skills_magic.json':{'20210':{'name':'Blizzaga'}},
            'skills_ability.json':{'912855':{'name':'Snow Burial'},'42':{'name':'Same numeric ID, different skill'},'9001':{'name':'Other skill'}},
            'skills_passive.json':{},'limitbursts.json':{},'enhancements.json':{}}
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            for name,data in tables.items():(root/(name+'-memorial.json')).write_text(json.dumps(data))
            with patch.object(builder,'load_global',return_value=(global_data,{'test':'provenance'})):
                result=builder.ownership(root,root)
        self.assertEqual([o['name'] for o in result['owners']['magic:20210']],['Lasswell','Christine'])
        self.assertEqual(result['owners']['ability:100740'][0]['name'],'Christine')
        self.assertNotIn('ability:42',result['owners'])
        self.assertEqual(result['owners']['summon:20101'][0]['name'],'Ifrit')
        missing=result['sources']['character:Christine']['missing']
        self.assertEqual({r['name'] for r in missing},{'Snow Burial','Same numeric ID, different skill'})
        self.assertIn('character:Another missing unit',result['coverage']['sourcesWithNoAvailableRecord'])

    def test_changed_global_source_file_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp);(folder/'units.json').write_text('{}')
            with self.assertRaisesRegex(ValueError,'checksum mismatch'):builder.load_global(folder)


if __name__=='__main__':unittest.main()
