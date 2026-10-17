"""Recover the library's complete, checksum-pinned delivery set from the supplied APK.

The APK is inspected, never executed. Download URLs and byte ranges come only
from its embedded delivery catalogs. Existing verified downloads are reused.
Requires pycryptodome for the APK's original master-table encoding.
"""
import argparse
import base64
import concurrent.futures
import hashlib
import json
from pathlib import Path
import re
import shutil
import urllib.request
from urllib.parse import urldefrag
import zipfile
import zlib

APK_SHA='9d21fc8b61c9900eaacb1c2ddef2cabcad1e97d2dc720be16ac09b06fc0086b4'
TABLES=('F_MAGIC_MST','F_ABILITY_MST','F_MONSTER_SKILL_MST','F_LIMITBURST_MST',
        'F_EFFECT_GROUP_MST','F_EFFECT_MST','F_BEAST_MST','F_BEAST_SKILL_MST')


def sha(path):
    with path.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()


def fetch(record,folder):
    name=record['name']
    if Path(name).name!=name:raise ValueError('Invalid source asset name')
    target=folder/name
    if target.is_file() and target.stat().st_size==record['size'] and sha(target)==record['sha256']:return target
    url,fragment=urldefrag(record['url']);match=re.fullmatch(r'ffbe-range=(\d+):(\d+):(\d+)',fragment)
    if not match or not url.startswith('https://github.com/luminest-llc/ffbe-memorial-downloads/releases/download/'):
        raise ValueError('Unexpected APK delivery URL')
    start,length,total=map(int,match.groups())
    if start+length>total:raise ValueError('Invalid delivery range')
    request=urllib.request.Request(url,headers={'Range':f'bytes={start}-{start+length-1}','Accept-Encoding':'identity'})
    with urllib.request.urlopen(request,timeout=90) as response:
        if response.status==206:
            if response.headers.get('Content-Range')!=f'bytes {start}-{start+length-1}/{total}':raise ValueError('Unexpected source range')
        elif response.status==200:
            remaining=start
            while remaining:
                block=response.read(min(remaining,1024*1024))
                if not block:raise ValueError('Truncated delivery pack')
                remaining-=len(block)
        else:raise ValueError('Unexpected delivery response')
        wire=response.read(length)
        if len(wire)!=length:raise ValueError('Truncated source asset')
    data=zlib.decompress(wire,-15) if record.get('zipMethod')==8 else wire
    if len(data)!=record['size'] or hashlib.sha256(data).hexdigest()!=record['sha256']:raise ValueError('Source checksum mismatch: '+name)
    folder.mkdir(parents=True,exist_ok=True);temporary=target.with_suffix(target.suffix+'.part');temporary.write_bytes(data);temporary.replace(target)
    target.with_suffix(target.suffix+'.source.json').write_text(json.dumps(record,indent=2)+'\n')
    print('Verified',name,len(data),flush=True)
    return target


def prepare(apk,output):
    if sha(apk)!=APK_SHA:raise ValueError('This extractor requires the supplied Memorial EN Global Events v208 APK.')
    output.mkdir(parents=True,exist_ok=True)
    copy=output/'FFBE-Memorial-EN-Global-Events-v208.apk'
    if copy.resolve()!=apk.resolve():shutil.copyfile(apk,copy)
    with zipfile.ZipFile(apk) as archive:
        base=archive.read('assets/base_delivery.tsv').decode();content=archive.read('assets/content_delivery.tsv').decode();native=archive.read('lib/arm64-v8a/libgame.so')
    (output/'memorial-base_delivery.tsv').write_text(base);(output/'memorial-content_delivery.tsv').write_text(content)
    (output/'apk-native').mkdir(exist_ok=True);(output/'apk-native/libgame.so').write_bytes(native)
    records={}
    for line in base.splitlines()[1:]:
        kind,name,length,digest,url=line.split('\t');records[name]={'name':name,'kind':kind,'size':int(length),'sha256':digest,'url':url}
    masters={}
    for table in TABLES:
        match=re.search(table.encode()+rb'\x00([A-Za-z0-9]{8})\x00([A-Za-z0-9]{8})\x00',native)
        if not match:raise ValueError('Master table unavailable in supplied APK: '+table)
        masters[table]=(match[1].decode()+'.dat',match[2])
    names={m[0] for m in masters.values()}|{'SE.acb','System.acb'}
    names.update(n for n in records if re.fullmatch(r'(unit\d+|beastMovie\w*|movie\d+|battleEffect\w*|effectResource\w*|mapEffect\w*|uieffect\w*|beast1|skill1)\.cpk',n))
    selected=[records[n] for n in sorted(names)]
    for line in content.splitlines()[1:]:
        f=line.split('\t')
        if f[0].endswith('.usm'):
            selected.append({'name':Path(f[0]).name,'kind':'content','size':int(f[2]),'sha256':f[1],'url':f[3],'sourceAsset':f[0],'zipMethod':int(f[6])})
    # Include standalone cinematics from the same APK; names are indexed in UI.
    selected.extend(v for n,v in records.items() if n.endswith('.usm') and (n in ('BMT002.usm','LSA_lapis4new.usm') or n.startswith(('LB_','SLB_'))))
    unique={r['name']:r for r in selected}
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:list(pool.map(lambda r:fetch(r,output/'memorial-source'),unique.values()))
    from Crypto.Cipher import AES
    from Crypto.Util.Padding import unpad
    for table,(name,key) in masters.items():
        rows=[]
        for line in (output/'memorial-source'/name).read_bytes().splitlines():
            data=AES.new(key.ljust(16,b'\0'),AES.MODE_CBC,b'dZMjkk8gFDzKHlsx').decrypt(base64.b64decode(line,validate=True))
            rows.append(json.loads(unpad(unpad(data,16),16)))
        (output/(table+'-memorial.json')).write_text(json.dumps(rows,ensure_ascii=False)+'\n')
        print(table,len(rows),'records',flush=True)
    print('Complete:',len(unique),'verified delivery assets')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--apk',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();prepare(a.apk,a.output)
