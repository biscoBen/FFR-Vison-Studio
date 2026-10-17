"""Retain original USM sources; generate alpha-aware WebM previews with embedded sound."""
import sys,re,json,subprocess,concurrent.futures,hashlib
from pathlib import Path
import argparse
parser=argparse.ArgumentParser(description='Extract and preview all available Memorial summon/skill cinematics.')
parser.add_argument('--source',type=Path,required=True);parser.add_argument('--work',type=Path,required=True)
args=parser.parse_args();r=args.source
from ffbe_memorial_cpk import Cpk
out=args.work/'movies';out.mkdir(parents=True,exist_ok=True)
origins={}
for path in (r/'memorial-source').glob('*.cpk'):
 if not re.fullmatch(r'(beastMovie\w*|movie\d+)\.cpk',path.name):continue
 c=Cpk(path)
 for e in c.entries:
  if e['name'].endswith('.usm'):
   dest=out/e['name'];data=c.read(e)
   if not dest.exists():dest.write_bytes(data)
   elif dest.read_bytes()!=data:raise ValueError('Conflicting movie '+e['name'])
   origins[e['name']]=path.name
 c.f.close()
for p in (r/'memorial-source').glob('*.usm'):
 dest=out/p.name
 if not dest.exists():dest.write_bytes(p.read_bytes())
 origins[p.name]=p.name
manifest={}
def convert(p):
 info=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_entries','stream=codec_type,codec_name','-of','json',str(p)],text=True))
 videos=[x for x in info['streams'] if x['codec_type']=='video'];audio=any(x['codec_type']=='audio' for x in info['streams'])
 dest=p.with_suffix('.webm')
 if not dest.exists():
  temporary=dest.with_suffix('.staging.webm')
  args=['ffmpeg','-v','error','-i',str(p)]
  if len(videos)==2:args+=['-filter_complex','[0:v:0][0:v:1]alphamerge[v]','-map','[v]']
  else:args+=['-map','0:v:0']
  args+=['-map','0:a?','-c:v','libvpx-vp9','-crf','35','-b:v','0','-row-mt','1','-threads','2','-deadline','good','-cpu-used','4','-c:a','libopus','-b:a','128k','-y',str(temporary)]
  result=subprocess.run(args,capture_output=True)
  if result.returncode:raise RuntimeError(p.name+': '+result.stderr.decode()[-1200:])
  temporary.replace(dest)
 duration=float(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','default=noprint_wrappers=1:nokey=1',str(dest)],text=True).strip())
 manifest[p.name]={'source':p.name,'file':dest.name,'duration':duration,'hasAudio':audio,'hasAlpha':len(videos)==2,'sourceArchive':origins[p.name],'sourceSha256':hashlib.sha256(p.read_bytes()).hexdigest(),'previewSha256':hashlib.sha256(dest.read_bytes()).hexdigest()}
 print('Converted',p.name,'alpha',len(videos)==2,flush=True)
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:list(pool.map(convert,list(out.glob('*.usm'))))
(out/'index.json').write_text(json.dumps(manifest,indent=1));print('COMPLETE',len(manifest),'sources',sum(p.stat().st_size for p in out.glob('*.usm')),'preview bytes',sum(p.stat().st_size for p in out.glob('*.webm')))
