"""Package the complete pinned Memorial v208 skill/effect/audio source library.

Inputs are the supplied APK's SHA-verified delivery cache and decrypted master
rows. --extract rebuilds effect/sprite members from the original CPKs. Runtime
previews are generated on demand; original sources are never converted in place.
"""
import argparse
import collections
import hashlib
import json
from pathlib import Path
import re
import sys
import zipfile

REVISION='memorial-en-v208-1'
APK_SHA='9d21fc8b61c9900eaacb1c2ddef2cabcad1e97d2dc720be16ac09b06fc0086b4'
TABLES={'magic':('F_MAGIC_MST','QV1HE7Wq'),'ability':('F_ABILITY_MST','Ga5V42LZ'),
        'monster':('F_MONSTER_SKILL_MST','6E5u1xrs'),'lb':('F_LIMITBURST_MST','PR2HIc71'),'summon':('F_BEAST_SKILL_MST','76LymtEu')}


def digest(path):
    with path.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()


def frames(text):return [x.split(':') for x in re.split('[&,]',text or '') if x]


def extract(source,work,effects):
    from ffbe_memorial_cpk import Cpk
    raw=work/'raw';raw.mkdir(parents=True,exist_ok=True)
    origins=collections.defaultdict(list);variants=[]
    required={name for e in effects if e['I1B7wNWc']=='1' for name in e['2HjxCGo6'].split(':')}
    for path in sorted((source/'memorial-source').glob('*.cpk')):
        is_unit=bool(re.fullmatch(r'unit\d+\.cpk',path.name))
        if not is_unit and not re.match(r'(battleEffect|effectResource|mapEffect|uieffect)',path.name):continue
        cpk=Cpk(path)
        for entry in cpk.entries:
            name=entry['name']
            if is_unit and name not in required:continue
            if not name or Path(name).name!=name:raise ValueError('Unexpected source member path')
            data=cpk.read(entry);target=raw/name
            if target.exists() and target.read_bytes()!=data:
                target=raw/'variants'/path.name/name;target.parent.mkdir(parents=True,exist_ok=True)
                variants.append({'file':name,'source':path.name,'variant':target.relative_to(raw).as_posix()})
            target.write_bytes(data);origins[target.relative_to(raw).as_posix()].append(path.name)
        cpk.f.close()
    (work/'raw-origins.json').write_text(json.dumps(origins))
    (work/'source-variants.json').write_text(json.dumps(variants))
    return origins


def build(source,work,output,extract_raw=False,chunk_bytes=48*1024*1024):
    if digest(source/'FFBE-Memorial-EN-Global-Events-v208.apk')!=APK_SHA:raise ValueError('Unexpected Memorial APK')
    groups_raw=json.loads((source/'F_EFFECT_GROUP_MST-memorial.json').read_bytes())
    effects_raw=json.loads((source/'F_EFFECT_MST-memorial.json').read_bytes())
    if extract_raw:extract(source,work,effects_raw)
    members={}
    def add(name,value):
        members[name]=(json.dumps(value,ensure_ascii=False,separators=(',',':'))+'\n').encode()
    skills=[]
    for kind,(table,key) in TABLES.items():
        rows=json.loads((source/(table+'-memorial.json')).read_bytes())
        seen=set()
        for row in rows:
            identity=str(row[key])
            if identity in seen:raise ValueError('Duplicate skill identity '+kind+':'+identity)
            seen.add(identity)
            skills.append({'key':kind+':'+identity,'kind':kind,'id':identity,'name':row.get('G4L0YIB2') or kind+' '+identity,
                'timeline':row.get('5A8SmwyC',''),'hits':row.get('a9DvZ70c',''),
                'hasAnimation':bool(row.get('5A8SmwyC') or re.search(r'\.usm',row.get('q4f9IdMs',''))),'sourceTable':table,
                'movies':re.findall(r'[A-Za-z0-9_./-]+\.usm',row.get('q4f9IdMs',''))})
        add('masters/'+table+'.json',rows)
    groups={}
    for row in groups_raw:
        groups[row['qIy86WvJ']]={'name':row.get('h9UFW3qt',''),'raw':row,
            'effects':[{'frame':int(f[0]),'effectId':f[1],'flags':f[2:]} for f in frames(row.get('5A8SmwyC')) if len(f)>1],
            'sounds':[{'frame':int(f[0].rstrip(']')),'cueId':f[1],'flags':f[2:]} for f in frames(row.get('1fVZ3rKd')) if len(f)>1 and f[1]]}
    effects={row['h5t4yBm2']:{'type':row['I1B7wNWc'],'name':row.get('o2ye8th6',''),
        'file':row.get('2HjxCGo6',''),'scale':float(row.get('avX1k34K') or 100)/100,'raw':row} for row in effects_raw}
    source_aliases=[]
    for eid,effect in effects.items():
        base=effect['file'].split(':')[0]
        candidates=[base,base+'.bmb']
        if base.endswith('.bmb0'):candidates.append(base[:-1])
        asset=next((n for n in candidates if (work/'raw'/n).is_file()),base)
        effect['asset']=asset
        if asset!=base:source_aliases.append({'effectId':eid,'reference':base,'resolvedFile':asset})
    add('groups.json',groups);add('effects.json',effects)
    catalog={'skills':skills,'groups':[{'key':'group:'+gid,'kind':'group','id':gid,'name':g['name'],'hasAnimation':bool(g['effects'])} for gid,g in groups.items()],
             'effects':[{'key':'effect:'+eid,'kind':'effect','id':eid,'name':e['name'],'file':e['file'],'hasAnimation':e['type'] in ('1','5')} for eid,e in effects.items()]}
    movie_index=json.loads((work/'movies/index.json').read_bytes()) if (work/'movies/index.json').is_file() else {}
    catalog['movies']=[{'key':'movie:'+name,'kind':'movie','id':name,'name':name,'hasAnimation':True,'movies':[name]} for name in movie_index]
    add('movies.json',movie_index)
    for name,entry in movie_index.items():
        members['source-movies/'+name]=work/'movies'/name
        members['movies/'+entry['file']]=work/'movies'/entry['file']
    for values in catalog.values():values.sort(key=lambda r:(r['name'].casefold(),r['kind'],r['id']))
    add('catalog.json',catalog)
    audio=json.loads((work/'audio.json').read_bytes());add('audio.json',audio)
    for bank in ('SE','System'):members['source-audio/'+bank+'.acb']=source/'memorial-source'/(bank+'.acb')
    for p in sorted((work/'audio').glob('*.flac')):members['audio/'+p.name]=p
    for p in sorted((work/'raw').rglob('*')):
        if p.is_file():members['raw/'+p.relative_to(work/'raw').as_posix()]=p
    bmb_dependencies={}
    for name,value in members.items():
        if name.startswith('raw/') and name.endswith('.bmb'):
            raw=value.read_bytes()
            # The string table includes positioning models omitted by older parsers.
            strings=re.findall(rb'[A-Za-z0-9_ .-]{3,}\x00',raw)
            deps=set()
            for text in strings:
                stem=text[:-1].decode('ascii').strip()
                for ext in ('','.png','.m3r'):
                    if 'raw/'+stem+ext in members:deps.add(stem+ext)
            bmb_dependencies[Path(name).name]=sorted(deps)
    add('bmb-dependencies.json',bmb_dependencies)
    if (work/'source-variants.json').exists():add('source-variants.json',json.loads((work/'source-variants.json').read_bytes()))
    # Preserve the full source tables, including controls not supported by previews.
    add('masters/F_EFFECT_GROUP_MST.json',groups_raw);add('masters/F_EFFECT_MST.json',effects_raw)
    wanted={e['asset'] for e in effects.values() if e['type']=='5'}
    missing_bmb=sorted(n for n in wanted if 'raw/'+n not in members)
    missing_sprites=sorted({n for e in effects.values() if e['type']=='1' for n in e['file'].split(':') if 'raw/'+n not in members})
    missing_cues=sorted({s['cueId'] for g in groups.values() for s in g['sounds'] if 'SE:'+s['cueId'] not in audio['cues']})
    referenced_groups={f[1] for row in skills for text in row['timeline'].split('@') for f in frames(text) if len(f)>1 and f[1]}
    summary={'skills':len(skills),'byKind':dict(collections.Counter(r['kind'] for r in skills)),
             'skillsWithAnimation':sum(r['hasAnimation'] for r in skills),
             'cinematicClips':len(movie_index),'missingCinematicFiles':sorted({m for s in skills for m in s.get('movies',[]) if m not in movie_index}),'groups':len(groups),'effects':len(effects),
             'bmbFiles':sum(n.endswith('.bmb') for n in members),'textures':sum(n.endswith(('.png','.jpg')) for n in members),
             'meshes':sum(n.endswith('.m3r') for n in members),'soundCues':len(audio['cues']),'soundRecordings':len(audio['waves']),
             'missingBmbFiles':missing_bmb,'missingSpriteFiles':missing_sprites,'missingSoundCueIds':missing_cues,
             'missingGroupIds':sorted(referenced_groups-set(groups)),'audioPreviewLimitations':audio.get('unhandled',[]),
             'resolvedSourceAliases':source_aliases,
             'previewTimingCorrections':[{'groupId':'8008297','rawFrame':'318]','previewFrame':318,'originalPreserved':True}]}
    sources={}
    for p in sorted((source/'memorial-source').glob('*.source.json')):
        row=json.loads(p.read_bytes());data=source/'memorial-source'/row['name']
        if data.is_file() and row['name'].endswith(('.cpk','.acb','.dat','.usm')):
            if digest(data)!=row['sha256']:raise ValueError('Source checksum mismatch: '+row['name'])
            sources[row['name']]=row
    add('provenance.json',{'apkSha256':APK_SHA,'sources':sources,'summary':summary,'origins':json.loads((work/'raw-origins.json').read_bytes())})
    output.mkdir(parents=True,exist_ok=True);files={};packs=[];archive=None;size=0;number=0
    def finish():
        if archive:
            archive.close();p=output/pack_name;packs.append({'name':pack_name,'bytes':p.stat().st_size,'sha256':digest(p)})
    for name,value in sorted(members.items()):
        raw=value.read_bytes() if isinstance(value,Path) else value
        if archive is None or size+len(raw)>chunk_bytes:
            finish();number+=1;pack_name=f'library-{number:02d}.zip';archive=zipfile.ZipFile(output/pack_name,'w',zipfile.ZIP_DEFLATED,compresslevel=6);size=0
        info=zipfile.ZipInfo(name,(2026,10,17,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED
        archive.writestr(info,raw);size+=len(raw)
        files[name]={'pack':pack_name,'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
    finish()
    manifest={'schema':1,'revision':REVISION,'source':{'name':'FFBE Memorial EN Global Events v208','apkSha256':APK_SHA},'summary':summary,'packs':packs,'files':files}
    (output/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=1)+'\n')
    owned={p['name'] for p in packs}
    for stale in output.glob('library-*.zip'):
        if re.fullmatch(r'library-\d{2}\.zip',stale.name) and stale.name not in owned:stale.unlink()
    print(json.dumps({'summary':summary,'packs':len(packs),'downloadBytes':sum(p['bytes'] for p in packs),'members':len(files)},indent=2))
    return manifest


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',type=Path,required=True);p.add_argument('--work',type=Path,required=True);p.add_argument('--output',type=Path,default=Path(__file__).resolve().parents[1]/'assets/ffbe_library');p.add_argument('--extract',action='store_true');a=p.parse_args();build(a.source,a.work,a.output,a.extract)
