"""Verify every packaged library member, source row, cue link and preview sample count."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import zipfile

ROOT=Path(__file__).resolve().parents[1]
KINDS={'magic':('F_MAGIC_MST','QV1HE7Wq'),'ability':('F_ABILITY_MST','Ga5V42LZ'),
       'monster':('F_MONSTER_SKILL_MST','6E5u1xrs'),'lb':('F_LIMITBURST_MST','PR2HIc71'),
       'summon':('F_BEAST_SKILL_MST','76LymtEu')}


def verify(root=ROOT/'assets/ffbe_library'):
    manifest=json.loads((root/'manifest.json').read_bytes())
    assert manifest['schema']==1 and manifest['revision']=='memorial-en-v208-1'
    files=manifest['files'];seen=set();documents={}
    for pack in manifest['packs']:
        path=root/pack['name'];assert re.fullmatch(r'library-\d{2}\.zip',path.name)
        assert path.stat().st_size==pack['bytes']
        with path.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==pack['sha256']
        with zipfile.ZipFile(path) as z:
            assert len(z.namelist())==len(set(z.namelist()))
            for info in z.infolist():
                name=info.filename;assert name not in seen;seen.add(name)
                assert not name.startswith('/') and all(x not in ('','.','..') for x in name.split('/'))
                expected=files[name];assert expected['pack']==path.name and expected['bytes']==info.file_size
                raw=z.read(info);assert hashlib.sha256(raw).hexdigest()==expected['sha256']
                if name.endswith('.json'):documents[name]=json.loads(raw)
                if name.startswith('audio/'):
                    assert raw[:4]==b'fLaC';bits=int.from_bytes(raw[18:26],'big');wave=documents.get('audio.json')
                    # audio.json precedes audio/ lexically; no decoder dependency.
                    assert wave is not None
                    record=next(w for w in wave['waves'].values() if w['file']==Path(name).name)
                    assert bits>>44==record['sampleRate'],name
                    assert bits&((1<<36)-1)==record['samples'],name
    assert seen==set(files)
    catalog=documents['catalog.json'];summ=manifest['summary'];skills=catalog['skills'];bykind={k:[] for k in KINDS}
    assert len(skills)==summ['skills'] and len({r['key'] for r in skills})==len(skills)
    for row in skills:bykind[row['kind']].append(row)
    for kind,(table,key) in KINDS.items():
        original=documents['masters/'+table+'.json'];recorded={r['id']:r for r in bykind[kind]}
        assert len(original)==len(recorded)==summ['byKind'][kind]
        for row in original:
            entry=recorded[str(row[key])]
            assert entry['name']==(row.get('G4L0YIB2') or kind+' '+str(row[key]))
            assert entry['timeline']==row.get('5A8SmwyC','')
            assert entry['hits']==row.get('a9DvZ70c','')
    groups=documents['groups.json'];effects=documents['effects.json'];audio=documents['audio.json']
    assert len(groups)==summ['groups'] and len(effects)==summ['effects']
    for table,key,mapping in (('F_EFFECT_GROUP_MST','qIy86WvJ',groups),('F_EFFECT_MST','h5t4yBm2',effects)):
        original=documents['masters/'+table+'.json'];assert len(original)==len(mapping)
        for row in original:assert mapping[row[key]]['raw']==row
    for cue in audio['cues'].values():
        for alt in cue['variants']:
            for event in alt:assert event['wave'] in audio['waves']
    for group in groups.values():
        for sound in group['sounds']:assert 'SE:'+sound['cueId'] in audio['cues']
    for wave in audio['waves'].values():assert 'audio/'+wave['file'] in files
    for name,entry in documents.get('movies.json',{}).items():
        assert files['source-movies/'+name]['sha256']==entry['sourceSha256']
        assert files['movies/'+entry['file']]['sha256']==entry['previewSha256']
    assert not any('assigned' in r or 'ffrId' in r for r in skills)
    print(f"FFBE library verified: {len(skills)} complete skill records, {len(groups)} groups, {len(effects)} effects, {len(audio['cues'])} cues, {len(seen)} hashed files.")
    return manifest


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--root',type=Path,default=ROOT/'assets/ffbe_library');args=parser.parse_args();verify(args.root)
