"""Add newly discovered source cinematics while preserving existing pack boundaries.

Only changed JSON packs and new movie packs are written. Existing source movies
are kept byte-for-byte, including their verified previews. Run the full library
verifier after extending. The main source builder can reproduce a fresh library.
"""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile


def sha(raw):return hashlib.sha256(raw).hexdigest()
def encoded(value):return (json.dumps(value,ensure_ascii=False,separators=(',',':'))+'\n').encode()


def extend(output,work,source):
    manifest=json.loads((output/'manifest.json').read_bytes());files=manifest['files']
    packs={p['name']:p for p in manifest['packs']}
    def read(name):
        with zipfile.ZipFile(output/files[name]['pack']) as archive:raw=archive.read(name)
        if sha(raw)!=files[name]['sha256']:raise ValueError('Changed source library member: '+name)
        return raw
    movies=json.loads(read('movies.json'));catalog=json.loads(read('catalog.json'))
    provenance=json.loads(read('provenance.json'))
    incoming=json.loads((work/'movies/index.json').read_bytes())
    new={name:entry for name,entry in incoming.items() if name not in movies}
    if not new:print('No new cinematics.');return manifest
    members={}
    for name,entry in sorted(new.items()):
        if Path(name).name!=name or Path(entry['file']).name!=entry['file']:raise ValueError('Invalid movie filename')
        for logical,path,digest in (
                ('source-movies/'+name,work/'movies'/name,entry['sourceSha256']),
                ('movies/'+entry['file'],work/'movies'/entry['file'],entry['previewSha256'])):
            raw=path.read_bytes()
            if sha(raw)!=digest:raise ValueError('Changed cinematic: '+name)
            members[logical]=raw
        record=json.loads((source/'memorial-source'/(name+'.source.json')).read_bytes())
        if record['sha256']!=entry['sourceSha256']:raise ValueError('Changed delivery source: '+name)
        provenance['sources'][name]=record
    movies.update(new)
    catalog['movies']=[{'key':'movie:'+name,'kind':'movie','id':name,'name':name,'hasAnimation':True,'movies':[name]} for name in sorted(movies,key=str.casefold)]
    summary=manifest['summary'];summary['cinematicClips']=len(movies)
    summary['missingCinematicFiles']=sorted({name for s in catalog['skills'] for name in s.get('movies',[]) if name not in movies})
    provenance['summary']=summary
    replacements={'movies.json':encoded(movies),'catalog.json':encoded(catalog),'provenance.json':encoded(provenance)}
    touched={files[name]['pack'] for name in replacements}
    for pack in sorted(touched):
        path=output/pack
        if sha(path.read_bytes())!=packs[pack]['sha256']:raise ValueError('Changed source pack: '+pack)
        temporary=path.with_suffix('.staging')
        with zipfile.ZipFile(path) as old,zipfile.ZipFile(temporary,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as archive:
            for info in old.infolist():
                name=info.filename;raw=old.read(info)
                if sha(raw)!=files[name]['sha256']:raise ValueError('Changed packed member: '+name)
                raw=replacements.get(name,raw);archive.writestr(info,raw)
                files[name]={'pack':pack,'bytes':len(raw),'sha256':sha(raw)}
        temporary.replace(path);packs[pack].update(bytes=path.stat().st_size,sha256=sha(path.read_bytes()))
    groups=[];current=[];size=0
    for name,raw in sorted(members.items()):
        if current and size+len(raw)>48*1024*1024:groups.append(current);current=[];size=0
        current.append((name,raw));size+=len(raw)
    if current:groups.append(current)
    for entries in groups:
        name=f'library-{len(packs)+1:02d}.zip';path=output/name
        if path.exists():raise ValueError('Unexpected existing new pack: '+name)
        with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as archive:
            for member,raw in entries:
                info=zipfile.ZipInfo(member,(2026,10,17,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;archive.writestr(info,raw)
                files[member]={'pack':name,'bytes':len(raw),'sha256':sha(raw)}
        packs[name]={'name':name,'bytes':path.stat().st_size,'sha256':sha(path.read_bytes())}
    manifest['packs']=list(packs.values())
    path=output/'manifest.json';temporary=path.with_suffix('.staging')
    temporary.write_text(json.dumps(manifest,ensure_ascii=False,indent=1)+'\n');temporary.replace(path)
    print(json.dumps({'newMovies':list(new),'clips':len(movies),'packs':len(packs),'bytes':sum(p['bytes'] for p in packs.values())},indent=2))
    return manifest


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,default=Path(__file__).resolve().parents[1]/'assets/ffbe_library');p.add_argument('--work',type=Path,required=True);p.add_argument('--source',type=Path,required=True);a=p.parse_args();extend(a.output,a.work,a.source)
