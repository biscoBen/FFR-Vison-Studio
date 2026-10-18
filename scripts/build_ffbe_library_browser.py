"""Generate source ownership and original Christine/Cactuar preview sheets.

Ownership follows actual unit level grants, limit bursts, esper boards and enemy
skill sets. A missing association stays uncredited; names are never guessed from
spell names. The complete raw animation archive is left unchanged.
"""
import argparse
import collections
import hashlib
import io
import json
from pathlib import Path
import re
import zipfile

ROOT=Path(__file__).resolve().parents[1]
TABLE_KEYS={'magic':('F_MAGIC_MST','QV1HE7Wq'),'ability':('F_ABILITY_MST','Ga5V42LZ'),
            'monster':('F_MONSTER_SKILL_MST','6E5u1xrs'),'lb':('F_LIMITBURST_MST','PR2HIc71'),'summon':('F_BEAST_SKILL_MST','76LymtEu')}
OWNER_TABLES=tuple(table for table,_ in TABLE_KEYS.values())+(
    'F_UNIT_MST','F_UNIT_SERIES_LV_ACQUIRE_MST','F_SUBLIMATION_RECIPE_MST',
    'F_MONSTER_DICTIONARY_MST','F_MONSTER_MST','F_MONSTER_SKILL_SET_MST',
    'F_MONSTER_PARTS_MST','F_BEAST_MST','F_BEAST_STATUS_MST','F_BEAST_BOARD_PIECE_MST')


def load_global(folder):
    lock=json.loads((ROOT/'scripts/fixtures/ffbe_library/global-ownership-lock.json').read_bytes())
    data={}
    for name,digest in lock['files'].items():
        raw=(folder/name).read_bytes()
        if hashlib.sha256(raw).hexdigest()!=digest:raise ValueError('Global ownership checksum mismatch: '+name)
        data[name]=json.loads(raw)
    return data,lock


def ownership(source, global_source=None):
    def read(table):return json.loads((source/(table+'-memorial.json')).read_bytes())
    skills={kind:{r[key]:r for r in read(table)} for kind,(table,key) in TABLE_KEYS.items()}
    result=collections.defaultdict(list);sources={};missing=collections.defaultdict(dict)
    def register(name,entity,identity):
        if not name:return
        key=entity+':'+name
        sources.setdefault(key,{'key':key,'name':name,'type':entity,'ids':[]})
        if identity not in sources[key]['ids']:sources[key]['ids'].append(identity)
    def add(kind,sid,name,entity,identity):
        register(name,entity,identity)
        if sid not in skills[kind] or not name:return
        row={'name':name,'type':entity,'id':identity};key=kind+':'+sid
        if not any(o['name']==name and o['type']==entity for o in result[key]):result[key].append(row)
    units=read('F_UNIT_MST');series={u['woghJa61']:u['G4L0YIB2'] for u in reversed(units)}
    global_units={};global_skills={};global_proof=None
    if global_source is not None:
        data,global_proof=load_global(global_source)
        global_units=data['units.json']
        global_skills={'magic':data['skills_magic.json'],
                       'ability':{**data['skills_ability.json'],**data['skills_passive.json']},
                       'lb':data['limitbursts.json']}
        identities={}
        for uid,u in global_units.items():
            if not u.get('name'):continue
            register(u['name'],'character',uid)
            for identity in [uid,*u.get('entries',{})]:
                identities[identity]=u['name'];series.setdefault(identity,u['name'])
        def global_add(kind,sid,name,uid):
            sid=str(sid);original=global_skills[kind].get(sid)
            if original is None or not original.get('name'):return
            native=skills[kind].get(sid)
            # Exact typed ID AND original name: never borrow another spell's
            # owner merely because its name happens to match.
            if native and native['G4L0YIB2'].casefold().strip()==original['name'].casefold().strip():
                add(kind,sid,name,'character',uid)
            else:
                missing['character:'+name][kind+':'+sid]={'kind':kind,'id':sid,'name':original['name'],
                    'reason':'absent' if native is None else 'different-record'}
    for u in units:add('lb',u.get('PR2HIc71',''),u['G4L0YIB2'],'character',u['3HriTp6B'])
    for row in read('F_UNIT_SERIES_LV_ACQUIRE_MST'):
        uid=row['woghJa61'];name=series.get(uid)
        for field in ('i6kc1jN0','1Zsh27mS','eAM5B1qt'):
            for sid in row.get(field,'').split(','):
                for kind in ('magic','ability'):add(kind,sid,name,'character',uid)
    dictionaries={m['V9j8wJcC']:m['G4L0YIB2'] for m in read('F_MONSTER_DICTIONARY_MST')}
    monsters={m['xqartN26']:dictionaries.get(m['V9j8wJcC'],m['G4L0YIB2']) for m in read('F_MONSTER_MST')}
    sets={s['A5x02C6a']:[x for x in s['7qxLC5hP'].split(',') if x] for s in read('F_MONSTER_SKILL_SET_MST')}
    for part in read('F_MONSTER_PARTS_MST'):
        uid=part['xqartN26'];name=monsters.get(uid,part['G4L0YIB2'])
        for sid in sets.get(part.get('A5x02C6a'),[]):add('monster',sid,name,'monster',uid)
    beasts={b['Iwfx42Wo']:b['G4L0YIB2'] for b in read('F_BEAST_MST')}
    for row in read('F_BEAST_STATUS_MST'):
        # STATUS links each esper/rank to its actual skill. KF9Av5yX in
        # SKILL is a boolean flag, not an esper identity.
        uid=row['Iwfx42Wo'];add('summon',row['76LymtEu'],beasts.get(uid),'summon',uid)
    for row in read('F_BEAST_BOARD_PIECE_MST'):
        for sid in re.findall(r'\d+',row.get('XHEZ47ke','')):
            for kind in ('ability','magic'):add(kind,sid,beasts.get(row['Iwfx42Wo']),'summon',row['Iwfx42Wo'])
    for row in read('F_SUBLIMATION_RECIPE_MST'):
        uid=row.get('25oxcKwN','');name=next((u['G4L0YIB2'] for u in units if u['3HriTp6B']==uid),series.get(uid))
        for kind in ('ability','magic'):add(kind,row.get('Q1n9iYgz',''),name,'character',uid)
    if global_source is not None:
        for uid,u in global_units.items():
            name=u.get('name')
            if not name:continue
            for grant in u.get('skills',[]):
                kind='magic' if grant['type']=='MAGIC' else 'ability'
                global_add(kind,grant['id'],name,uid)
            for entry in u.get('entries',{}).values():
                if entry.get('limitburst_id'):global_add('lb',entry['limitburst_id'],name,uid)
        for row in data['enhancements.json'].values():
            for uid in map(str,row.get('units',[])):
                name=identities.get(uid)
                if not name:continue
                for kind in ('magic','ability'):
                    global_add(kind,row['skill_id_new'],name,uid)
    for key,entry in sources.items():
        missing[key]={sid:record for sid,record in missing[key].items()
                      if not any(o['type']+':'+o['name']==key for o in result.get(sid,[]))}
        entry['missing']=sorted(missing[key].values(),key=lambda r:(r['name'].casefold(),r['kind'],r['id']))
    covered={o['type']+':'+o['name'] for records in result.values() for o in records}
    report={'sources':len(sources),'sourcesWithKnownRecords':len(covered),
            'sourcesWithNoAvailableRecord':sorted(set(sources)-covered),
            'globalMissingRecords':sum(len(v) for v in missing.values())}
    return {'owners':dict(result),'sources':sources,'coverage':report,'globalProvenance':global_proof}


def owners(source,global_source=None):return ownership(source,global_source)['owners']


def sheet(images,durations):
    from PIL import Image
    boxes=[im.getbbox() for im in images if im.getbbox()]
    bounds=(min(b[0] for b in boxes),min(b[1] for b in boxes),max(b[2] for b in boxes),max(b[3] for b in boxes))
    width,height=bounds[2]-bounds[0],bounds[3]-bounds[1];columns=min(8,len(images));rows=(len(images)+columns-1)//columns
    atlas=Image.new('RGBA',(width*columns,height*rows))
    for i,im in enumerate(images):atlas.paste(im.crop(bounds),((i%columns)*width,(i//columns)*height))
    stream=io.BytesIO();atlas.save(stream,format='PNG')
    return stream.getvalue(),{'width':width,'height':height,'columns':columns,'durations':durations,'frames':len(images)}


def cactuar_frames(path,metadata):
    """Respect packed native cells and pivots; this atlas is not a regular grid."""
    from PIL import Image
    if hashlib.sha256(path.read_bytes()).hexdigest()!=metadata['sourceAtlasSha256']:
        raise ValueError('The Cactuar atlas differs from the referenced native idle.')
    with Image.open(path) as image:atlas=image.convert('RGBA')
    frames=[]
    for cell in metadata['cells']:
        sprite=atlas.crop(cell['rect'])
        # Place each original pivot at a shared origin before trimming the strip.
        x=round(64-(.5+cell['pivot'][0])*sprite.width)
        y=round(64-(.5-cell['pivot'][1])*sprite.height)
        frame=Image.new('RGBA',(128,128));frame.paste(sprite,(x,y));frames.append(frame)
    return frames


def build(source,actors,output,global_source=None):
    from PIL import Image,ImageSequence
    ownership_data=ownership(source,global_source);own=ownership_data['owners'];files={};meta={}
    with Image.open(actors/'christine.webp') as image:
        images=[im.convert('RGBA') for im in ImageSequence.Iterator(image)]
        durations=[]
        for i in range(image.n_frames):image.seek(i);durations.append(image.info.get('duration',100)/1000)
    files['christine.png'],meta['character']=sheet(images,durations)
    meta['character'].update(name='Christine',look='6★',file='christine.png',heightInScene=160)
    native_idle=json.loads((ROOT/'scripts/fixtures/ffbe_library/cactuar-idle.json').read_bytes())
    frames=cactuar_frames(actors/'cactuar-native.png',native_idle)
    files['cactuar.png'],meta['monster']=sheet(frames,[h/native_idle['fps'] for h in native_idle['holds']])
    meta['monster'].update(name='Cactuar',file='cactuar.png',heightInScene=150)
    metadata={'schema':1,**ownership_data,'actors':meta,'actorSource':{'character':'Original FFBE Christine 6-star idle, pinned Studio host','monster':'Original Resonance demo Cactuar idle, supplied native reference'},'source':'FFBE Memorial EN Global Events v208; exact Global ownership supplement',
              'provenance':{'nativeIdle':native_idle,'masters':{table+'-memorial.json':hashlib.sha256((source/(table+'-memorial.json')).read_bytes()).hexdigest() for table in sorted(OWNER_TABLES)},
                            'actors':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in actors.iterdir() if p.name in ('christine.webp','cactuar-native.png')}}}
    files['browser.json']=(json.dumps(metadata,ensure_ascii=False,separators=(',',':'))+'\n').encode()
    with zipfile.ZipFile(output,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for name,raw in files.items():
            info=zipfile.ZipInfo(name,(2026,10,17,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;z.writestr(info,raw)
    print('Named records',len(own),'owners',sum(len(v) for v in own.values()),'bundle bytes',output.stat().st_size)
    return metadata


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',type=Path,required=True);p.add_argument('--actors',type=Path,required=True);p.add_argument('--global-source',type=Path);p.add_argument('--output',type=Path,default=ROOT/'assets/existing_visions/payload/ffbe_library_browser.zip');a=p.parse_args();build(a.source,a.actors,a.output,a.global_source)
