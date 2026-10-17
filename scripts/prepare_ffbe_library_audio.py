"""Preserve original cue IDs, variants, delays and sound banks; decode preview FLACs."""
import sys,json,struct,hashlib,subprocess,concurrent.futures,collections
from pathlib import Path
import argparse
parser=argparse.ArgumentParser(description='Extract original Memorial cue graphs and lossless preview recordings.')
parser.add_argument('--source',type=Path,required=True);parser.add_argument('--work',type=Path,required=True);parser.add_argument('--engine-tools',type=Path,required=True)
args=parser.parse_args();r=args.source;sys.path.insert(0,str(args.engine_tools))
from ffbe_effects.acb_cues import utf,commands,cues
from ffbe_effects.acb_native import awb_files
out=args.work/'audio';out.mkdir(parents=True,exist_ok=True)
allcues={};allwaves={};sources={};unhandled=[]
for bank in ('SE','System'):
 p=r/'memorial-source'/(bank+'.acb');raw=p.read_bytes();sources[p.name]=hashlib.sha256(raw).hexdigest()
 h=utf(raw)[1][0];tables={k:utf(h[k])[1] for k in ('CueTable','SynthTable','SequenceTable','TrackTable','TrackEventTable','SeqCommandTable','SynthCommandTable','TrackCommandTable','WaveformTable','SoundGeneratorTable') if h.get(k)}
 if not h.get('TrackEventTable') and h.get('CommandTable'):tables['TrackEventTable']=utf(h['CommandTable'])[1]
 wavs=awb_files(h['AwbFile'])
 def track_events(index):
  row=tables['TrackTable'][index];events=[];offset=0
  for op,args in commands(tables['TrackEventTable'][row['EventIndex']]['Command']):
   if op==2000: events.append((offset,*struct.unpack('>HH',args)))
   elif op==2001:
    # CRI Delay is a uint32 millisecond wait. Preserve the command explicitly.
    offset+=int.from_bytes(args,'big')/1000
   elif op!=0: unhandled.append((bank,'track',op,args.hex()))
  return events
 def flatten(kind,index,seen=()):
  if (kind,index) in seen:raise ValueError('Audio graph cycle')
  seen=(*seen,(kind,index))
  if kind==1:
   wave=tables['WaveformTable'][index]; wid=wave.get('MemoryAwbId',wave.get('Id')); data=wavs[wid]
   digest=hashlib.sha256(data).hexdigest();name=digest+'.hca'
   if not (out/name).exists():(out/name).write_bytes(data)
   allwaves[digest]={'sourceBank':bank,'waveId':wid,'sampleRate':wave['SamplingRate'],'samples':wave['NumSamples'],'channels':wave['NumChannels'],'loop':wave['LoopFlag'],'hca':name,'file':digest+'.flac'}
   return [[{'at':0,'wave':digest}]]
  if kind==7:return flatten(3,index,seen)
  if kind==2:
   row=tables['SynthTable'][index];refs=[struct.unpack_from('>HH',row['ReferenceItems'],i) for i in range(0,len(row['ReferenceItems']),4)]
   variants=[[]]
   for ref in refs:
    child=flatten(*ref,seen);variants=[a+b for a in variants for b in child]
   return variants
  if kind==3:
   row=tables['SequenceTable'][index];tracks=[]
   for i in range(row['NumTracks']):
    track=int.from_bytes(row['TrackIndex'][2*i:2*i+2],'big');variants=[[]]
    for offset,k,idx in track_events(track):
     child=[[{**e,'at':e['at']+offset} for e in alt] for alt in flatten(k,idx,seen)]
     variants=[a+b for a in variants for b in child]
    tracks.append(variants)
   if row['Type']==3:return [a for t in tracks for a in t]
   if row['Type']!=0:unhandled.append((bank,'sequenceType',row['Type']))
   variants=[[]]
   for t in tracks:variants=[a+b for a in variants for b in t]
   return variants
  unhandled.append((bank,'referenceType',kind,index)); return [[]]
 for cid,meta in cues(p).items():
  cue=tables['CueTable'][meta['index'] if 'index' in meta else meta['cueIndex']]
  before=len(unhandled)
  variants=flatten(cue['ReferenceType'],cue['ReferenceIndex'])
  allcues[bank+':'+str(cid)]={'warnings':unhandled[before:],'bank':bank,'id':cid,'name':meta['name'],'variants':variants,'lengthMs':cue['Length']}
 print(bank,'cues',len(cues(p)),flush=True)
(args.work/'audio.json').write_text(json.dumps({'cues':allcues,'waves':allwaves,'sourceBanks':sources,'unhandled':unhandled},indent=1))
def decode(item):
 digest,entry=item;dst=out/entry['file']
 if dst.exists():
  raw=dst.read_bytes();bits=int.from_bytes(raw[18:26],'big')
  if bits>>44==entry['sampleRate'] and bits&((1<<36)-1)==entry['samples']:return
 raw=(out/entry['hca']).read_bytes();delay=int.from_bytes(raw[20:22],'big') if raw.startswith(b'HCA') else 0
 r=subprocess.run(['ffmpeg','-v','error','-i',str(out/entry['hca']),'-af',f"atrim=start_sample={delay}:end_sample={delay+entry['samples']},asetpts=PTS-STARTPTS",'-c:a','flac','-y',str(dst)],capture_output=True)
 if r.returncode:raise RuntimeError(entry['hca']+': '+r.stderr.decode()[:1000])
with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:list(pool.map(decode,allwaves.items()))
print('COMPLETE',len(allcues),'cues',len(allwaves),'waves','flacBytes',sum((out/w['file']).stat().st_size for w in allwaves.values()),'unhandled',unhandled)
