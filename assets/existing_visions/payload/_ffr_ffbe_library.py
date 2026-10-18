"""Read-only Memorial library with portable visual exports; never assigns game skills."""
from functools import lru_cache
import gzip
import hashlib
import io
import json
import math
from pathlib import Path
import re
import sys
import struct
import threading
import zipfile

REVISION = 'memorial-en-v208-1'
MAX_FRAMES = 1800
_LOCK = threading.Lock()
CONVERSION_SCRIPT = r'''"""Convert this visual layer with Studio's existing SpriteStudio converter.

Run using the engine's Python environment. No game tables or bindings are made.
"""
import argparse,json,sys
from pathlib import Path
from PIL import Image
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--engine',type=Path,required=True)
p.add_argument('--out',type=Path,required=True)
p.add_argument('--emitter',type=int,action='append',help='Optionally isolate one or more mesh emitters')
a=p.parse_args()
root=Path(__file__).resolve().parent
if a.out.exists():raise SystemExit('Choose a new output folder.')
sys.path.insert(0,str(a.engine.resolve()/'tools/ffbe_effects'))
import to_ss6
def texture(name):
    path=(root/name).resolve()
    if not path.is_relative_to(root) or path.suffix!='.png':raise ValueError('Invalid texture path')
    with Image.open(path) as image:return image.convert('RGBA')
to_ss6.load_texture=texture
doc=json.loads((root/'doc.json').read_bytes())
if a.emitter:
    doc['frames']=[[p for p in frame if p.get('emitter') in a.emitter] for frame in doc['frames']]
    used=sorted({p['tex'] for frame in doc['frames'] for p in frame})
    if not used:raise SystemExit('No visible frames for those emitters.')
    mapping={old:new for new,old in enumerate(used)}
    doc['textures']=[doc['textures'][i] for i in used]
    for frame in doc['frames']:
        for p in frame:p['tex']=mapping[p['tex']]
to_ss6.convert(doc,str(a.out),'library_effect',max_units=1000000,min_frames=270)
'''


def safe_name(value):
    return (isinstance(value, str) and value and '\\' not in value and ':' not in value
            and not value.startswith('/') and all(x not in ('', '.', '..') for x in value.split('/')))


class Library:
    def __init__(self, root):
        self.root = Path(root) / 'library/ffbe'
        self.manifest = json.loads((self.root/'manifest.json').read_bytes())
        if self.manifest.get('schema') != 1 or self.manifest.get('revision') != REVISION:
            raise ValueError('Unsupported FFBE animation library. Restart the updated Studio to prepare its assets.')
        self.directory = self.root / REVISION
        self.files = self.manifest['files']
        self.packs = {p['name']: p for p in self.manifest['packs']}
        for name, record in self.files.items():
            if not safe_name(name) or record['pack'] not in self.packs or not 0 <= record['bytes'] <= 128*1024*1024:
                raise ValueError('Invalid FFBE library member.')
        for name in self.packs:
            if not re.fullmatch(r'library-\d{2}\.zip', name): raise ValueError('Invalid library pack name.')
        self._verified = set()
        self.cache = Path(root) / 'build/ffbelib1'

    def read(self, name):
        record = self.files.get(name)
        if record is None: raise ValueError('This file is not in the FFBE animation library.')
        path = self.directory / record['pack']
        if path.is_symlink() or self.directory.is_symlink(): raise ValueError('Linked FFBE library path.')
        stat = path.stat(); fingerprint = (path.name, stat.st_size, stat.st_mtime_ns)
        if fingerprint not in self._verified:
            expected = self.packs[path.name]
            if stat.st_size != expected['bytes']:
                raise ValueError('FFBE library pack has changed; restart Studio to restore it.')
            with path.open('rb') as stream: digest = hashlib.file_digest(stream, 'sha256').hexdigest()
            if digest != expected['sha256']: raise ValueError('FFBE library pack checksum mismatch.')
            self._verified.add(fingerprint)
        with zipfile.ZipFile(path) as archive:
            info = archive.getinfo(name)
            if info.file_size != record['bytes']: raise ValueError('FFBE library file size mismatch.')
            raw = archive.read(info)
        if hashlib.sha256(raw).hexdigest() != record['sha256']:
            raise ValueError('FFBE library file checksum mismatch.')
        return raw

    @lru_cache(maxsize=8)
    def document(self, name): return json.loads(self.read(name))

    @property
    def catalog(self): return self.document('catalog.json')

    @lru_cache(maxsize=1)
    def browser(self):
        path=Path(__file__).with_name('ffbe_library_browser.zip')
        if not path.is_file():return {'owners':{},'actors':{}}
        with zipfile.ZipFile(path) as archive:return json.loads(archive.read('browser.json'))

    @lru_cache(maxsize=1)
    def browsing(self):
        owners=self.browser()['owners'];groups=self.document('groups.json');effects=self.document('effects.json')
        effect_signatures={}
        for eid,effect in effects.items():
            names=effect['file'].split(':') if effect['type']=='1' else effect.get('asset',effect['file']).split(':')
            effect_signatures[eid]=[effect['type'],effect.get('scale',1),
                [self.files.get('raw/'+name,{}).get('sha256',name) for name in names]]
        group_signatures={}
        for gid,group in groups.items():
            signature={'effects':[[e['frame'],effect_signatures.get(e['effectId'],e['effectId']),e['flags']] for e in group['effects']],
                       'sounds':group['sounds'],'camera':group.get('raw',{}).get('rPHs9p8F','')}
            group_signatures[gid]=hashlib.sha256(json.dumps(signature,sort_keys=True).encode()).hexdigest()
        buckets={};aliases={};reverse={k:{} for k in ('groups','effects','movies')}
        for original in self.catalog['skills']:
            key=original['key'];origin='monster' if original['kind']=='monster' else 'summon' if original['kind']=='summon' else 'character'
            sequences=[];used_groups=[]
            for variant in original.get('timeline','').split('@'):
                sequence=[]
                for fields in split_frames(variant):
                    if len(fields)<2:continue
                    sequence.append([fields[0],group_signatures.get(fields[1],'missing:'+fields[1]),fields[2:]])
                    used_groups.append(fields[1])
                sequences.append(sequence)
            hit_frames=[[([f[0],*f[2:]]) for f in (h.split(':') for h in part.split('-')) if f and f[0]] for part in original.get('hits','').split('@')]
            signature=[original['name'].casefold().strip(),origin,original['kind']=='lb',sequences,hit_frames,original.get('movies',[])]
            fingerprint=hashlib.sha256(json.dumps(signature,sort_keys=True).encode()).hexdigest()
            entry=buckets.get(fingerprint)
            if entry is None:
                entry={**original,'sourceLabel':'Unattributed FFBE source','sourceType':origin,'sourceNames':[],
                       'equivalentCount':0,'aliasKeys':[],'sourceMembers':{}};buckets[fingerprint]=entry
            entry['equivalentCount']+=1;entry['aliasKeys'].append(key);aliases[key]=entry
            for owner in owners.get(key,[]):
                entry['sourceMembers'].setdefault(source_key(owner),key)
                if owner['name'] not in entry['sourceNames']:entry['sourceNames'].append(owner['name'])
                if entry['sourceLabel']=='Unattributed FFBE source':
                    entry['sourceLabel']=owner['name'];entry['sourceType']=owner['type']
            for gid in used_groups:
                reverse['groups'].setdefault(gid,[]).append(entry)
                for effect in groups.get(gid,{}).get('effects',[]):reverse['effects'].setdefault(effect['effectId'],[]).append(entry)
            for name in original.get('movies',[]):reverse['movies'].setdefault(name,[]).append(entry)
        result={'skills':list(buckets.values())}
        for scope in ('groups','effects','movies'):
            result[scope]=[]
            for original in self.catalog.get(scope,[]):
                candidates=reverse[scope].get(original['id'],[])
                owner=next((e for e in candidates if e['sourceNames']),None)
                result[scope].append({**original,'sourceLabel':owner['sourceLabel'] if owner else 'Unattributed FFBE source',
                    'sourceType':owner['sourceType'] if owner else scope[:-1],
                    'sourceMembers':{source:original['key'] for e in candidates for source in e['sourceMembers']},
                    'sourceNames':list(dict.fromkeys(n for e in candidates for n in e['sourceNames']))})
        return result,aliases

    @lru_cache(maxsize=1)
    def skill_rows(self):return {r['key']:r for r in self.catalog['skills']}

    @lru_cache(maxsize=1)
    def sources(self):
        """List actual named owners, counting each deduplicated presentation once."""
        sources={key:{**record,'skills':0} for key,record in self.browser().get('sources',{}).items()}
        for entry in self.browsing()[0]['skills']:
            for key in entry['sourceMembers']:
                kind,_,name=key.partition(':')
                source=sources.setdefault(key,{'key':key,'name':name,'type':kind,'skills':0})
                source['skills']+=1
        return {'items':sorted(sources.values(),key=lambda s:(s['type'],s['name'].casefold()))}

    def search(self, query='', kind='all', scope='skills', offset=0, limit=60, animated=True, source=''):
        if scope not in ('skills', 'groups', 'effects', 'movies'): raise ValueError('Unknown library view.')
        if not 0 <= offset <= 200000 or not 1 <= limit <= 100: raise ValueError('Invalid library page.')
        rows = self.browsing()[0][scope]
        if source:
            selected=[]
            for row in rows:
                member=row['sourceMembers'].get(source)
                if member is None:continue
                # Preserve the selected owner's exact record, even when the
                # unfiltered presentation is listed under another owner's ID.
                original=self.skill_rows()[member] if scope=='skills' else row
                source_type,_,name=source.partition(':')
                selected.append({**row,**original,'sourceLabel':name,'sourceType':source_type})
            rows=selected
        query = query.casefold().strip()
        result = [r for r in rows if (kind == 'all' or r['kind'] == kind)
                  and (not animated or r.get('hasAnimation', True))
                  and (not query or query in (r['name']+' '+r['id']+' '+r.get('file','')+' '+' '.join(r.get('sourceNames',[]))).casefold())]
        coverage=next((r for r in self.sources()['items'] if r['key']==source),None) if source else None
        return {'total': len(result), 'offset': offset, 'items': result[offset:offset+limit], 'sourceCoverage':coverage,
                'summary': {**self.manifest['summary'],'uniqueSkills':len(self.browsing()[0]['skills'])}, 'revision': REVISION}

    def detail(self, kind, identity, source=''):
        key = kind+':'+str(identity)
        for scope in ('skills', 'groups', 'effects', 'movies'):
            row = next((r for r in self.catalog.get(scope,[]) if r['key'] == key), None)
            if row is not None: break
        if row is None: raise ValueError('No such FFBE animation entry.')
        if kind in ('group','effect','movie'):
            row=next(r for r in self.browsing()[0][scope] if r['key']==key)
        else:
            info=self.browsing()[1][key]
            row={**row,**{k:info[k] for k in ('sourceLabel','sourceType','sourceNames','equivalentCount')}}
        if source:
            if kind in ('group','effect','movie'):
                owns=source in row['sourceMembers']
            else:owns=any(source_key(o)==source for o in self.browser()['owners'].get(key,[]))
            if not owns:raise ValueError('This entry is not recorded for the selected source.')
            source_type,_,name=source.partition(':')
            row={**row,'sourceLabel':name,'sourceType':source_type}
        groups = self.document('groups.json'); effects = self.document('effects.json')
        variants = []
        if kind == 'effect':
            variants = [[{'frame':0,'groupId':'single','flags':['1','1','0'], 'effects':[
                {'frame':0,'effectId':str(identity),'flags':['99999999','1','2','2','0','0']}], 'sounds':[]}]]
        elif kind == 'group':
            variants = [[{'frame':0,'groupId':str(identity),'flags':['1','1','0'],
                          'effects':groups[str(identity)]['effects'], 'sounds':groups[str(identity)]['sounds']}]]
        else:
            for text in row.get('timeline','').split('@'):
                entries = []
                for fields in split_frames(text):
                    if len(fields)<2 or not integer(fields[0]) or fields[1] not in groups: continue
                    group=groups[fields[1]]
                    entries.append({'frame':int(fields[0]), 'groupId':fields[1], 'flags':fields[2:],
                                    'effects':group['effects'], 'sounds':group['sounds']})
                variants.append(entries)
        audio = self.document('audio.json')
        if kind == 'lb':
            opening=next((k for k,c in audio['cues'].items() if c['bank']=='System' and c['name']=='se_battle_limitopen_1'),None)
            if opening:
                for variant in variants:
                    variant.append({'frame':0,'groupId':'lb-opening','flags':['1','3','0'],'effects':[],
                        'sounds':[{'frame':0,'cueId':opening,'flags':['1']}]})
        used = {e['effectId'] for v in variants for g in v for e in g['effects']}
        sound_ids = {s['cueId'] for v in variants for g in v for s in g['sounds']}
        audio = self.document('audio.json')
        cues = {cid:audio['cues'].get(cid if ':' in cid else 'SE:'+cid) for cid in sound_ids}
        movies=self.document('movies.json') if 'movies.json' in self.files else {}
        return {'entry':row, 'variants':variants, 'effects':{eid:effects.get(eid) for eid in used},
                'cues':cues, 'movies':[{**movies.get(name,{}),'name':name,'available':name in movies} for name in row.get('movies',[])],
                'waves':{e['wave']:audio['waves'][e['wave']]
                    for cue in cues.values() if cue for alt in cue['variants'] for e in alt},
                'previewNote':'Approximate FFBE effect preview. Original source files and audio are retained.',
                'missingGroups':[f[1] for f in split_frames(row.get('timeline','').replace('@','&'))
                    if len(f)>1 and f[1] and f[1] not in groups] if kind not in ('group','effect') else []}

    def materialize(self, name):
        if name not in self.files: return None
        path = self.cache/'source'/name
        if not path.exists() or hashlib.sha256(path.read_bytes()).hexdigest()!=self.files[name]['sha256']:
            path.parent.mkdir(parents=True, exist_ok=True); raw=self.read(name)
            temporary=path.with_suffix(path.suffix+'.part'); temporary.write_bytes(raw);temporary.replace(path)
        return path

    def simulation(self, identity, edges='soft'):
        if not str(identity).isdigit(): raise ValueError('Invalid effect ID.')
        if edges not in ('soft','original'):raise ValueError('Unknown edge treatment.')
        effects=self.document('effects.json'); effect=effects.get(str(identity))
        if not effect: raise ValueError('No such FFBE effect.')
        output=self.cache/(str(identity)+'.v4.'+edges+'.json.gz')
        if output.exists():return output.read_bytes()
        with _LOCK:
            if output.exists():return output.read_bytes()
            if effect['type'] == '5':result=self.particle_simulation(effect,edges)
            elif effect['type'] == '1':result=self.sprite_simulation(effect)
            else:result={'frames':[],'textures':[],'warnings':['This source effect is a control command.'],'fps':60,'durationDeclared':0}
            raw=json.dumps(result,allow_nan=False,separators=(',',':')).encode()
            data=gzip.compress(raw,compresslevel=5)
            self.cache.mkdir(parents=True,exist_ok=True);temporary=output.with_suffix('.part');temporary.write_bytes(data);temporary.replace(output)
            return data

    def conversion_archive(self,identity,edges='soft'):
        """Portable layer frames and PNGs; no unit assignment or game writes.

        Pixel UVs / per-cell scale follow the engine's to_ss6 input contract.
        The exact prepared PNG bytes are shared with the library preview.
        """
        baked=json.loads(gzip.decompress(self.simulation(identity,edges)))
        if not any(baked['frames']):raise ValueError('This source layer has no convertible visual frames.')
        members={};textures=[];sizes=[]
        from PIL import Image
        for texture in baked['textures']:
            if texture is None:raise ValueError('This effect has unavailable source textures.')
            url=texture['url']
            if url.startswith('/api/ffbe-library/preview-texture/'):
                name=url.rsplit('/',1)[-1]
                if not re.fullmatch(r'[a-f0-9]{64}\.png',name):raise ValueError('Invalid generated texture.')
                raw=(self.cache/name).read_bytes()
                if hashlib.sha256(raw).hexdigest()+'.png'!=name:raise ValueError('Generated texture checksum mismatch.')
            elif url.startswith('/api/ffbe-library/file/'):
                raw=self.read(url[len('/api/ffbe-library/file/'):])
            else:raise ValueError('Unknown conversion texture.')
            with Image.open(io.BytesIO(raw)) as image:
                sizes.append(image.size)
                if not url.startswith('/api/ffbe-library/preview-texture/'):
                    buffer=io.BytesIO();image.convert('RGBA').save(buffer,format='PNG');raw=buffer.getvalue()
            # Preserve generated PNG bytes exactly. Raw JPG/PNG sources use a
            # deterministic RGBA PNG so the output archive needs no decoders.
            name='textures/'+hashlib.sha256(raw).hexdigest()+'.png';members[name]=raw;textures.append(name)
        frames=[]
        for frame in baked['frames']:
            output=[]
            for original in frame:
                p={**original};w,h=sizes[p['tex']];u,v,du,dv=p.get('uv',[0,0,1,1])
                p['uv']=[u*w,v*h,du*w,dv*h]
                p['scale']=[p['scale'][0]/max(abs(du*w),1e-9),p['scale'][1]/max(abs(dv*h),1e-9)]
                p['pos']=p['pos'][:2];output.append(p)
            frames.append(output)
        doc={**baked,'textures':textures,'frames':frames,'pixelsPerUnit':1,
             'sourceEffectId':str(identity),'scope':'visual-layer-only','gameAssigned':False}
        members['doc.json']=json.dumps(doc,allow_nan=False,separators=(',',':')).encode()
        members['convert_to_ss6.py']=CONVERSION_SCRIPT.encode()
        members['README.txt']=b'Portable visual layer, not a game installer. Use the engine Python environment to run: convert_to_ss6.py --engine <Studio engine folder> --out <new output folder>. Optional --emitter <number> isolates a mesh emitter when splitting large effects into separate atlases. This uses the existing to_ss6 converter to make a SpriteStudio spec and atlas while preserving the prepared PNG edges. Skill routing, anchors, timeline placement, audio, asset capacity and game bindings need separate integration. This archive assigns nothing.'
        buffer=io.BytesIO()
        with zipfile.ZipFile(buffer,'w',zipfile.ZIP_DEFLATED) as archive:
            for name,raw in members.items():archive.writestr(name,raw)
        return buffer.getvalue()

    def particle_simulation(self, effect, edges='soft'):
        ibmb = renderer()
        path=self.materialize('raw/'+effect.get('asset',effect['file'].split(':')[0]))
        if path is None: raise ValueError('The source APK delivery has no file for this effect.')
        # Keep every source dependency; hydrate only files required by this preview.
        original=ibmb._library_raw_parse(path)
        assets=[*(x+'.png' for x in original.textures),*(x+'.m3r' for x in original.models)]
        # Positioning meshes are referenced by null emitters, outside models[].
        assets.extend(self.document('bmb-dependencies.json').get(path.name,[]))
        for name in assets: self.materialize('raw/'+name)
        warnings=[]
        try: original=ibmb.parse(path)
        except (ValueError,FileNotFoundError) as e: warnings.append(str(e)+'; preview uses the base particle model.')
        baked=ibmb.bake(original,max_frames=MAX_FRAMES,max_particles=256,model_dirs=[str(path.parent)],soften_fog_edges=edges=='soft')
        if original.duration>MAX_FRAMES: warnings.append('Preview shows the first 30 seconds; the full original effect is retained.')
        import _ffr_ffbe_texture as textures
        textures.MESH_SPRITE_DIR = str(self.cache/'virtual-textures')
        cache=textures.TextureCache([str(path.parent)])
        baked['textures']=[self.texture(name,path.parent,warnings,cache) for name in baked['textures']]
        if not any(baked['frames']):warnings.append('The original file is saved, but this renderer produced no visible particles.')
        baked['warnings']=warnings
        baked['screenReference']=self.screen_reference(original,baked)
        return baked

    def screen_reference(self,original,baked):
        """Find an authored flat backdrop for screen-anchored effect projection.

        The skill's anchor flag decides whether this reference is used. Normal
        cloud walls take priority over additive flashes; volumetric meshes are
        excluded. Unit/target anchored effects retain their original world scale.
        """
        ibmb=renderer();candidates=[]
        for emitter in original.chunks:
            if not emitter.model:continue
            path=self.materialize('raw/'+emitter.model+'.m3r')
            if path is None:continue
            try:mesh=ibmb.parse_m3r(path)
            except (ValueError,OSError,struct.error):continue
            if not mesh['vertices'] or mesh['extent'][2]>1e-4:continue
            parts=(p for frame in baked['frames'] for p in frame
                   if p.get('emitter')==emitter.index and p.get('alpha',1)>.01)
            reference=max(parts,key=lambda p:abs(p['scale'][0]*p['scale'][1]),default=None)
            if reference is None:continue
            width,height=map(abs,reference['scale'][:2])
            if min(width,height)<1:continue
            candidates.append((emitter.blend!=1,-width*height,emitter.index,
                {'emitter':emitter.index,'center':reference['pos'][:2],'size':[width,height]}))
        return min(candidates,key=lambda item:item[:3])[-1] if candidates else None

    def texture(self,name,directory,warnings,cache):
        if name.startswith(('nativeuv:', 'quadcolor:', 'mesh:', 'solid:')):
            from PIL import Image
            import numpy as np
            try:
                pixels=cache.get(name)
                if pixels is None:raise ValueError('A required source texture is unavailable.')
                buffer=io.BytesIO();Image.fromarray((np.clip(pixels,0,1)*255).astype(np.uint8),'RGBA').save(buffer,format='PNG')
                raw=buffer.getvalue();key=hashlib.sha256(raw).hexdigest()+'.png';(self.cache/key).write_bytes(raw)
                return {'url':'/api/ffbe-library/preview-texture/'+key}
            except (ValueError,OSError) as e:
                warnings.append(str(e));return None
        key=next((x for x in ('raw/'+name,'raw/'+name+'.png','raw/'+name+'.jpg') if x in self.files),None)
        if key is None: warnings.append('Missing texture: '+name); return None
        return {'url':'/api/ffbe-library/file/'+key}

    def sprite_simulation(self,effect):
        sys.path.insert(0,str(Path(__file__).parent/'ffbe2ss6'))
        from ffbe_frames import read_cgg,read_cgs
        files=effect['file'].split(':')
        if len(files)!=3: raise ValueError('Unsupported source sprite effect.')
        paths=[self.materialize('raw/'+x) for x in files]
        if any(p is None for p in paths):raise ValueError('The source APK delivery is missing this sprite effect’s files.')
        cgg=read_cgg(str(paths[1]));steps=read_cgs(str(paths[2]));frames=[]
        from PIL import Image
        with Image.open(paths[0]) as source:atlas=source.convert('RGBA')
        for step in steps:
            # CGG conversion uses the engine's existing sprite renderer without
            # baking this preview into a unit or any Resonance asset.
            from ffbe_frames import compose_frame
            from PIL import Image
            image=compose_frame(atlas,cgg[step['frame']])
            box=image.getbbox()
            if box:
                image=image.crop(box);buf=io.BytesIO();image.save(buf,format='PNG');raw=buf.getvalue()
                key=hashlib.sha256(raw).hexdigest()+'.png';self.cache.mkdir(parents=True,exist_ok=True);(self.cache/key).write_bytes(raw)
                texture={'url':'/api/ffbe-library/preview-texture/'+key}
                part={'tex':len(frames),'pos':[box[0]-512+image.width/2+step['x'],512-box[1]-image.height/2-step['y'],0],
                      'scale':[image.width,image.height],'rot':0,'alpha':1,'color':[1,1,1],'blend':'normal'}
            else:texture=None;part=None
            # Return compact run-length frames to avoid duplicate PNGs.
            frames.append({'texture':texture,'part':part,'delay':max(1,step['delay'])})
        textures=[];flat=[]
        for frame in frames:
            index=len(textures);textures.append(frame['texture'])
            part={**frame['part'],'tex':index} if frame['part'] else None
            flat.extend([[part] if part else []]*frame['delay'])
        return {'fps':60,'frameCount':len(flat),'durationDeclared':len(flat),'textures':textures,'frames':flat,'warnings':[]}


@lru_cache(maxsize=1)
def renderer():
    # Private copy: library inspection cannot alter the engine's unit converter.
    import _ffr_ffbe_renderer as ibmb
    import _ffr_ffbe_placement
    ibmb._library_raw_parse = ibmb.parse
    _ffr_ffbe_placement.install(ibmb)
    return ibmb


def integer(value): return bool(re.fullmatch(r'-?\d+',value))
def split_frames(text): return [x.split(':') for x in re.split(r'[&,]',text or '') if x]
def source_key(owner):return owner['type']+':'+owner['name']


def register(app, env):
    from fastapi import HTTPException
    from _ffr_ffbe_download import Installation
    @lru_cache(maxsize=1)
    def library(): return Library(env['ROOT'])
    installation=Installation(env['ROOT'],on_ready=library.cache_clear)
    @app.get('/api/ffbe-library/installation')
    def installation_status():return checked(installation.status)
    @app.post('/api/ffbe-library/download')
    def download_library():return checked(installation.start)
    @app.post('/api/ffbe-library/download/cancel')
    def cancel_download():return checked(installation.cancel)
    @app.get('/api/ffbe-library/actors')
    def actors():
        with zipfile.ZipFile(Path(__file__).with_name('ffbe_library_browser.zip')) as archive:return json.loads(archive.read('browser.json'))['actors']
    @app.get('/api/ffbe-library/actor/{name}')
    def actor_image(name:str):
        from fastapi.responses import Response
        if name not in ('christine.png','cactuar.png'):raise HTTPException(404,'Unknown preview actor.')
        with zipfile.ZipFile(Path(__file__).with_name('ffbe_library_browser.zip')) as archive:return Response(archive.read(name),media_type='image/png')
    def checked(fn,*args,**kwargs):
        try:return fn(*args,**kwargs)
        except (ValueError,OSError,KeyError,IndexError,struct.error,zipfile.BadZipFile) as e:raise HTTPException(422,str(e)) from e
    @app.get('/ffbe-animation-library')
    def page():
        from fastapi.responses import HTMLResponse
        return HTMLResponse(Path(__file__).with_name('ffbe_library.html').read_text(encoding='utf-8'),headers={'Cache-Control':'no-store'})
    @app.get('/api/ffbe-library/catalog')
    def catalog(q:str='',kind:str='all',scope:str='skills',offset:int=0,limit:int=60,animated:bool=True,source:str=''):
        return checked(lambda:library().search(q,kind,scope,offset,limit,animated,source))
    @app.get('/api/ffbe-library/sources')
    def sources():return checked(lambda:library().sources())
    @app.get('/api/ffbe-library/entry/{kind}/{identity}')
    def entry(kind:str,identity:str,source:str=''):return checked(lambda:library().detail(kind,identity,source))
    @app.get('/api/ffbe-library/effect/{identity}')
    def effect(identity:str,edges:str='soft'):
        from fastapi.responses import Response
        return Response(checked(lambda:library().simulation(identity,edges)),media_type='application/json',headers={'Content-Encoding':'gzip','Cache-Control':'no-cache'})
    @app.get('/api/ffbe-library/effect/{identity}/conversion')
    def conversion(identity:str,edges:str='soft'):
        from fastapi.responses import Response
        data=checked(lambda:library().conversion_archive(identity,edges))
        return Response(data,media_type='application/zip',headers={'Content-Disposition':'attachment; filename="ffbe-effect-'+identity+'-'+edges+'.zip"'})
    @app.get('/api/ffbe-library/file/{name:path}')
    def file(name:str):
        from fastapi.responses import Response
        if not name.endswith(('.png','.jpg','.flac','.webm')):raise HTTPException(404,'No preview media at this path.')
        media='video/webm' if name.endswith('.webm') else 'audio/flac' if name.endswith('.flac') else 'image/png' if name.endswith('.png') else 'image/jpeg'
        return Response(checked(lambda:library().read(name)),media_type=media)
    @app.get('/api/ffbe-library/preview-texture/{name}')
    def texture(name:str):
        from fastapi.responses import FileResponse
        if not re.fullmatch('[a-f0-9]{64}\\.png',name):raise HTTPException(404,'No preview texture.')
        path=checked(lambda:library().cache/name)
        if not path.is_file():raise HTTPException(404,'No preview texture.')
        return FileResponse(path,media_type='image/png')
