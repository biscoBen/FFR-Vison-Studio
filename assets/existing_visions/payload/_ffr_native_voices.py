"""Default resonance voices: native Atom cues and movie-only voice streams.

Read donors from original game files, never from another selected override.
Keep every video/alpha packet and every non-voice sound section unchanged.
"""
import copy
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import struct
import subprocess
import zipfile

import _ffr_movie_audio as movie
import _ffr_party_voices as party

REVISION = 2
VISION = 'Item/Vision/DT_VisionItemData'


def selected(units):
    return [u for u in units if u.get('native') and u.get('nativeVoice', u['id']) != u['id']]


def choose(items, index, count):
    """Keep opening/final lines when the two resonances have different counts."""
    if not items: raise ValueError('This original resonance has no voice recordings.')
    return items[round(index * (len(items)-1) / max(1, count-1))]


def adx_stream(raw):
    parts = movie.chunks(raw)
    headers = [p for p in parts if p['type'] == b'@SFA' and p['kind'] == 1]
    directory = movie._read_utf(parts[0]['payload'])[2]
    audio = [r for r in directory if r['stmid'] == int.from_bytes(b'@SFA', 'big')]
    if len(headers) != 1 or headers[0]['channel'] != 0 or len(audio) != 1:
        raise ValueError('Expected one original movie voice channel.')
    info = movie._read_utf(headers[0]['payload'])[2][0]
    # These native movie tracks are explicitly named VO_, not mixed effect/BGM tracks.
    filename=audio[0]['filename'].replace('\\','/').rsplit('/',1)[-1]
    if not filename.startswith('VO_') or info['audio_codec'] != 2 or info['sampling_rate'] != 48000 or info['num_channels'] != 2:
        raise ValueError('The original movie voice format changed; effects/music were not replaced.')
    data = b''.join(p['payload'] for p in parts if p['type'] == b'@SFA' and p['kind'] == 0)
    if data[:2] != b'\x80\0' or data[4:8] != bytes((3,18,4,2)):
        raise ValueError('The original movie voice is not native stereo ADX.')
    return data, info, audio[0]


def replace_movie_voice(target, donor):
    """Transplant native @SFA packets; update only directory and picture seek offsets."""
    source = movie.chunks(donor); parts = movie.chunks(target)
    _, info, source_row = adx_stream(donor)
    adx_stream(target)  # Fail closed before touching a mixed or unfamiliar soundtrack.
    name, columns, rows = movie._read_utf(parts[0]['payload'])
    parts[0]['payload'] = bytearray(movie._write_utf(name, columns, [
        source_row if r['stmid'] == int.from_bytes(b'@SFA','big') else r for r in rows]))
    audio = [p for p in source if p['type'] == b'@SFA']
    # Preserve native header/end/metadata grouping and packet timestamps.
    base = [p for p in parts if p['type'] != b'@SFA']
    first = next(i for i,p in enumerate(base) if p['kind'] == 0)
    prefix = base[:first]
    for p in [p for p in audio if p['kind'] == 1]:
        at = next(i for i,q in enumerate(prefix) if q['kind'] == 2)
        prefix.insert(at, p)
    first_audio = next(i for i,p in enumerate(audio) if p['kind'] == 0)
    last_audio = max(i for i,p in enumerate(audio) if p['kind'] == 0)
    prefix.extend(p for p in audio[:first_audio] if p['kind'] in (2,3))
    media = [p for p in base[first:] if p['kind'] == 0] + [p for p in audio if p['kind'] == 0]
    media.sort(key=lambda p: int.from_bytes(p['header'][16:20],'big') / max(1,int.from_bytes(p['header'][20:24],'big')))
    endings = [p for p in base[first:] if p['kind'] != 0] + audio[last_audio+1:]
    result = prefix + media + endings
    position = 0
    for p in result:
        p['new_position'] = position
        position += max(2048 if p['type'] == b'CRID' else 0, (len(p['header'])+len(p['payload'])+31)//32*32)
    offsets = {p['position']:p['new_position'] for p in result if p['type'] in (b'@SFV',b'@ALP') and p['kind'] == 0}
    for p in result:
        if p['type'] in (b'@SFV',b'@ALP') and p['kind'] == 3:
            for row in movie.integer_rows(p['payload']):
                old = movie.value(p['payload'],row,'ofs_byte')
                if old not in offsets: raise ValueError('Original movie seek entry does not point to a picture packet.')
                movie.put(p['payload'],row,'ofs_byte',offsets[old])
    for row in movie.integer_rows(result[0]['payload']):
        if movie.value(result[0]['payload'],row,'stmid') == 0: movie.put(result[0]['payload'],row,'filesize',position)
    raw = movie.pack_chunks(result)
    before = [(p['type'],bytes(p['payload'])) for p in parts if p['type'] in (b'@SFV',b'@ALP') and p['kind'] == 0]
    after = [(p['type'],bytes(p['payload'])) for p in movie.chunks(raw) if p['type'] in (b'@SFV',b'@ALP') and p['kind'] == 0]
    if before != after or adx_stream(raw)[0] != adx_stream(donor)[0]:
        raise ValueError('Voice substitution changed a picture or voice packet.')
    return raw, info


def encoded_movie_voice(template, adx):
    """Use exact native unsigned AUDIO_HDRINFO types and 288-byte ADX headers."""
    parts = movie.chunks(template); _, info, directory = adx_stream(template)
    offset = int.from_bytes(adx[2:4],'big')+4
    samples = int.from_bytes(adx[12:16],'big')
    if adx[4:8] != bytes((3,18,4,2)) or adx[8:12] != (48000).to_bytes(4,'big') or adx[18:20] != b'\4\0':
        raise ValueError('Expected unencrypted 48-kHz stereo ADX v4 voice.')
    body = adx[offset:-18]
    if len(body) != ((samples+31)//32)*36 or adx[-18:-14] != b'\x80\1\0\x0e':
        raise ValueError('Encoded voice ADX size changed.')
    header = bytearray(adx[:32]);header[2:4] = (284).to_bytes(2,'big')
    header.extend(bytes(282-len(header)));header.extend(b'(c)CRI')
    original = next(p for p in parts if p['type']==b'@SFA' and p['kind']==0)
    def packet(payload,tick):
        p=copy.deepcopy(original);p['payload']=bytearray(payload)
        struct.pack_into('>II',p['header'],16,tick,2997)
        return p
    audio=[packet(header,0)]
    for i in range((len(body)+1799)//1800):audio.append(packet(body[i*1800:(i+1)*1800],i*999//10))
    audio.append(packet(adx[-18:],((samples+1599)//1600)*999//10))
    for p in parts:
        if p['type']==b'@SFA' and p['kind']==1:
            name,cols,rows=movie._read_utf(p['payload']);rows[0]['total_samples']=samples
            p['payload']=bytearray(movie._write_utf(name,cols,rows))
    name,cols,rows=movie._read_utf(parts[0]['payload'])
    for row in rows:
        if row['stmid']==int.from_bytes(b'@SFA','big'):
            row['filesize']=len(header)+len(body)+18;row['filename']='VO_STUDIO_NATIVE.sfa'
    parts[0]['payload']=bytearray(movie._write_utf(name,cols,rows))
    # This donor is a packet carrier only; replace_movie_voice preserves the target pictures.
    result=[];inserted=False
    for p in parts:
        if p['type']==b'@SFA' and p['kind']==0:
            if not inserted:result.extend(audio);inserted=True
        else:result.append(p)
    return movie.pack_chunks(result)


def pcm(raw):
    """Read VGAudio's PCM16 WAV without importing wave into the frozen engine."""
    if raw[:4]!=b'RIFF' or raw[8:12]!=b'WAVE':raise ValueError('Invalid native voice WAV.')
    pos=12;fmt=None;data=None
    while pos+8<=len(raw):
        kind,size=raw[pos:pos+4],int.from_bytes(raw[pos+4:pos+8],'little');start=pos+8
        if start+size>len(raw):raise ValueError('Incomplete native voice WAV.')
        if kind==b'fmt ':fmt=raw[start:start+size]
        if kind==b'data':data=raw[start:start+size]
        pos=start+size+(size&1)
    if not fmt or data is None:raise ValueError('Native voice WAV has no samples.')
    codec,channels,rate,_,align,bits=struct.unpack_from('<HHIIHH',fmt)
    if codec==65534 and len(fmt)>=40 and fmt[24:40]==bytes.fromhex('0100000000001000800000aa00389b71'):codec=1
    if codec!=1 or bits!=16 or channels not in (1,2) or rate!=48000 or align!=2*channels:
        raise ValueError('Expected native 48-kHz mono/stereo PCM16 voice.')
    values=struct.unpack('<'+'h'*(len(data)//2),data)
    if channels==1:return [(v,v) for v in values]
    return list(zip(values[::2],values[1::2]))


def wave(samples, channels=2):
    if channels not in (1,2): raise ValueError('Expected mono or stereo native voice.')
    values=(round((left+right)/2) for left,right in samples) if channels==1 else (v for pair in samples for v in pair)
    data=struct.pack('<'+'h'*(len(samples)*channels),*(max(-32768,min(32767,v)) for v in values))
    fmt=struct.pack('<HHIIHH',1,channels,48000,96000*channels,2*channels,16)
    return b'RIFF'+struct.pack('<I',36+len(data))+b'WAVEfmt '+struct.pack('<I',16)+fmt+b'data'+struct.pack('<I',len(data))+data


def phrases(samples):
    """Split movie-only dialogue at silent gaps; retain short padding on each line."""
    blocks=[max((abs(v) for pair in samples[i:i+480] for v in pair),default=0) for i in range(0,len(samples),480)]
    threshold=max(80,max(blocks,default=0)*.025)
    active=[i for i,v in enumerate(blocks) if v>=threshold]
    if not active:raise ValueError('The selected original movie has no audible voice.')
    groups=[[active[0]]]
    for i in active[1:]:
        if i-groups[-1][-1]>25:groups.append([])
        groups[-1].append(i)
    return [samples[max(0,g[0]*480-2400):min(len(samples),(g[-1]+1)*480+4800)] for g in groups]


class Builder:
    def __init__(self,env):
        self.env=env;self.root=Path(env['ROOT']);self.legacy=Path(env['LEGACY']);self.out=Path(env['OUT'])
        self.work=self.root/'build/native-voices';self.work.mkdir(parents=True,exist_ok=True)
        self.views={};self.profiles={};self.entries={};self.number=0

    def extract(self,rel):
        # retoc filters are package paths even when the local filesystem is Windows.
        rel=str(rel).replace('\\','/').removeprefix('FFRS/Content/')
        self.env['run'](self.env['ffrenv'].py(str(self.root/'tools/extract_legacy.py'),'--filter',rel))

    def view(self,rel):
        if rel in self.views:return self.views[rel]
        path=self.legacy/(rel+'.uasset')
        if not path.is_file():self.extract(rel)
        if not path.is_file():raise ValueError('Original vision voice asset unavailable: '+rel)
        target=self.work/'view.json'
        self.env['run']([*self.env['FFRDT'],'tojson',str(path),str(target),'--usmap',self.env['USMAP']])
        self.views[rel]=json.loads(target.read_text(encoding='utf-8-sig'))
        return self.views[rel]

    def profile(self,sid):
        if sid in self.profiles:return self.profiles[sid]
        assets={r['ID']:r for rel in ('Asset/Skill/DT_SkillAsset','Asset/Skill/CDT_SkillAsset_Demo') for r in self.env['rows'](rel).values()}
        masters=[]
        for i in range(sid,sid+4):
            path=assets.get(i,{}).get('LevelSequence','None').split('.')[0]
            if path!='None' and path.startswith('/Game/'):
                masters.append(path.replace('/Game/','FFRS/Content/'))
        if not masters:raise ValueError('The selected original resonance has no sequence.')
        voices=[];movies={}
        for master in masters:
            self.view(master)
            folder=self.legacy/Path(master).parent
            if not list(folder.rglob('*_Sound*.uasset')):self.extract(Path(master).parent.as_posix()+'/')
            for sound in sorted(folder.rglob('*_Sound*.uasset')):
                rel=sound.relative_to(self.legacy).with_suffix('').as_posix();data=self.view(rel)
                for export,cue,start,index in party.sounds(data):
                    if not cue.startswith('VO_BTL_') or '_DUEL_' in cue:continue
                    imp=next(p for p in data['Imports'] if p['ObjectName']==cue)
                    package=party.import_name(data,imp['OuterIndex'])
                    if not package or not package.startswith('/Game/Sound/Cri/Voice/'):
                        raise ValueError('The native resonance voice cue package changed.')
                    voices.append({'asset':rel,'export':export,'index':index,'cue':cue,'package':package.replace('/Game/','FFRS/Content/'),'start':start})
            pending=[p['ObjectName'].replace('/Game/','FFRS/Content/') for p in self.view(master)['Imports'] if p['ObjectName'].startswith('/Game/Movies/Skill/')]
            seen=set()
            while pending:
                rel=pending.pop()
                if rel in seen:continue
                seen.add(rel);view=self.view(rel)
                paths=[p['Value'] for e in view['Exports'] for p in e.get('Data',[]) if p['Name']=='FilePath']
                if paths:movies[rel]=paths[0]
                else:pending.extend(p['ObjectName'].replace('/Game/','FFRS/Content/') for p in view['Imports'] if p['ObjectName'].startswith('/Game/Movies/Skill/'))
        voices=list({(v['asset'],v['index']):v for v in voices}.values());voices.sort(key=lambda v:(v['start'],v['asset'],v['index']))
        if bool(voices)==bool(movies):raise ValueError('Expected either native voice cues or one movie voice track for this resonance.')
        result={'sid':sid,'voices':voices,'movies':movies};self.profiles[sid]=result;return result

    def original(self,entry):
        if entry in self.entries:return self.entries[entry]
        if not re.fullmatch(r'FFRS/Content/Streams/Movies/[A-Za-z0-9_/.-]+\.usm',entry):raise ValueError('Unexpected native movie stream path.')
        loose=Path(self.env['ffrenv'].game_root())/entry
        if loose.is_file():data=loose.read_bytes()
        else:
            data=None
            for pak in sorted(Path(self.env['ffrenv'].game_paks()).glob('FFRS-Windows*.pak'),reverse=True):
                p=subprocess.run([str(self.root/'tools/repak/repak.exe'),'get',str(pak),entry],capture_output=True)
                if p.returncode==0 and p.stdout:data=p.stdout;break
            if data is None:raise ValueError('Original movie voice stream unavailable: '+entry)
        self.entries[entry]=data;return data

    def convert(self,mode,data):
        self.number+=1;prefix=self.work/f'codec-{self.number}'
        source=prefix.with_suffix('.input');target=prefix.with_suffix('.output');source.write_bytes(data)
        dll=self.work/'VGAudio.dll'
        if not dll.is_file():
            with zipfile.ZipFile(self.root/'tools/cave_music_preview.zip') as z:dll.write_bytes(z.read('VGAudio.dll'))
        self.env['run'](['powershell.exe','-NoProfile','-NonInteractive','-ExecutionPolicy','Bypass','-File',str(self.root/'tools/native_voice_codec.ps1'),mode,str(source),str(target),str(dll)])
        return target.read_bytes()

    def recordings(self,profile):
        if profile['movies']:
            rel=next(iter(profile['movies'].values()));adx=adx_stream(self.original('FFRS/Content/Streams/'+rel))[0]
            return phrases(pcm(self.convert('adx-wave',adx)))
        from ffbe_effects.acb_cues import utf,CueGraph
        from ffbe_effects.acb_native import awb_files
        from ffbe_effects.hca_host import key_from_config
        import ffbe_audio
        import _ffr_cave_music_preview as preview
        result=[]
        for voice in profile['voices']:
            cue=self.view(voice['package']);export=next(e for e in cue['Exports'] if e['ObjectName']==voice['cue'])
            props={p['Name']:p['Value'] for p in export['Data']};bank=party.import_name(cue,props['CueSheet'])
            bank_import=next(i for i in cue['Imports'] if i['ObjectName']==bank)
            rel=party.import_name(cue,bank_import['OuterIndex']).replace('/Game/','FFRS/Content/')
            self.view(rel);raw=(self.legacy/(rel+'.uexp')).read_bytes();at=raw.index(b'@UTF');acb=raw[at:at+int.from_bytes(raw[at+4:at+8],'big')+8]
            header=utf(acb)[1][0];names=utf(header['CueNameTable'])[1]
            matches=[n for n in names if n['CueName']==props['CueName']]
            if len(matches)!=1:raise ValueError('The selected native voice recording is missing.')
            row=utf(header['CueTable'])[1][matches[0]['CueIndex']];graph=CueGraph(header);waves=graph.alternatives(row)
            if len(waves)!=1:raise ValueError('The selected native voice has unsupported random/combined recordings.')
            wave_row=graph.row('WaveformTable',waves[0]);awb=header.get('AwbFile',b'')
            if wave_row['Streaming']:
                import io
                entry='FFRS/Content/Streams/Sound/'+bank+'.awb'
                # Read only an official bank; the existing preview helper validates AWB bounds.
                loose=Path(self.env['ffrenv'].game_root())/entry
                bank_data=loose.read_bytes() if loose.is_file() else None
                if bank_data is None:
                    for pak in sorted(Path(self.env['ffrenv'].game_paks()).glob('FFRS-Windows*.pak'),reverse=True):
                        process=subprocess.run([str(self.root/'tools/repak/repak.exe'),'get',str(pak),entry],capture_output=True)
                        if process.returncode==0 and process.stdout:bank_data=process.stdout;break
                if bank_data is None:raise ValueError('The selected native voice stream could not be read.')
                raw,subkey=preview.extract_wave(io.BytesIO(bank_data),wave_row.get('StreamAwbId',wave_row.get('Id')))
            else:
                raw=awb_files(awb)[wave_row.get('MemoryAwbId',wave_row.get('Id'))]
                subkey=int.from_bytes(awb[14:16],'little')
            plain=preview.decrypt(raw,key_from_config(ffbe_audio.host_config({})),subkey)
            result.append(pcm(self.convert('hca-wave',plain)))
        return result

    def write_asset(self,rel,view):
        import _ffr_crystal_cave as assets
        assets.names(view,[view['Imports'],view['Exports']])
        path=self.work/'write.json';path.write_text(json.dumps(view),encoding='utf-8')
        target=self.out/(rel+'.uasset');target.parent.mkdir(parents=True,exist_ok=True)
        self.env['run']([*self.env['FFRDT'],'fromjson',str(path),str(target),'--usmap',self.env['USMAP']])
        self.env['run']([*self.env['FFRDT'],'tojson',str(target),str(path),'--usmap',self.env['USMAP']])
        assets.check_level(view,json.loads(path.read_text(encoding='utf-8-sig')))

    def sound_edits(self,target,cues):
        objects=[];changes=[]
        for i,voice in enumerate(target['voices']):
            package,name=choose(cues,i,len(target['voices']))
            if package.rsplit('/',1)[-1]!=name:raise ValueError('The selected voice cue path is inconsistent.')
            view=self.view(voice['asset'])
            if next(i for i,e in enumerate(view['Exports']) if e['ObjectName']==voice['export'])!=voice['index']:
                raise ValueError('The native voice section has an ambiguous export name.')
            objects.append({'asset':voice['asset'],'export':voice['export'],'set':{'Sound':package}})
            changes.append({'asset':voice['asset'],'export':voice['export'],'export_index':voice['index'],'old':voice['cue'],'new':package})
        path=self.work/'sounds.json'
        # Native patch operations reload each asset. Read the prior output so a
        # later voice section cannot discard an earlier section's replacement.
        for rel in sorted({v['asset'] for v in target['voices']}):
            for suffix in ('.uasset','.uexp'):
                source=self.legacy/(rel+suffix);destination=self.out/(rel+suffix)
                destination.parent.mkdir(parents=True,exist_ok=True)
                if source.resolve()!=destination.resolve():shutil.copy2(source,destination)
        path.write_text(json.dumps({'legacyRoot':str(self.out),'outRoot':str(self.out),'objects':objects}))
        self.env['run']([*self.env['FFRDT'],'patch',str(path),'--usmap',self.env['USMAP']])
        for rel in sorted({v['asset'] for v in target['voices']}):
            self.env['run']([*self.env['FFRDT'],'tojson',str(self.out/(rel+'.uasset')),str(path),'--usmap',self.env['USMAP']])
            party.check_track(self.view(rel),json.loads(path.read_text(encoding='utf-8-sig')),[c for c in changes if c['asset']==rel])

    def private_cues(self,target,recordings,source_id):
        """Movie-only voices become ordinary native one-shot HCA cues for Atom targets."""
        import ffbe_audio
        from ffbe_effects import acb_native
        from ffbe_effects import hca_host
        from ffbe_effects.acb_cues import utf
        # Match the native Atom voice pool through the same mono HCA v3 adapter
        # as working FFBE sounds. Stereo v2 output bypassed that adaptation.
        waves={};records=[]
        for i,samples in enumerate(recordings):
            waves[i]=self.convert('wave-hca',wave(samples,channels=1))
            hca_host.validate_layout(waves[i])
            records.append({'sourceWaveId':i,'name':f'voice_{i}','durationMs':round(len(samples)*1000/48000),'samples':len(samples),'sampleRate':48000,'channels':1,'sourceCueId':i,'variation':0})
        name=f'StudioNativeVoice_{source_id}';self.view(ffbe_audio.SHELL)
        raw=(self.legacy/(ffbe_audio.SHELL+'.uexp')).read_bytes();at=raw.index(b'@UTF');native=raw[at:at+int.from_bytes(raw[at+4:at+8],'big')+8]
        profile={'revision':1,'version':0x300,'key':hca_host.key_from_config(ffbe_audio.host_config({}))}
        acb=acb_native.build(b'',native,name,records,gain=1.0,waveform_profile=profile,raw_waves=waves)
        # Use the game's voice volume categories, rather than the adapter's SE category.
        header=utf(acb)[1][0]
        refs=utf(header['AcfReferenceTable'])[1]
        route=[dict(refs[0],Name='VOICE',Id=4),dict(refs[0],Name='VO_BTL',Id=10),refs[-1]]
        header['AcfReferenceTable']=acb_native.encode_table('AcfReference',acb_native.schema(header['AcfReferenceTable']),route)
        commands=utf(header['SeqCommandTable'])[1]
        command=commands[0]['Command']
        if command[:7]!=struct.pack('>HBI',0x41,4,3):raise ValueError('The native one-shot voice routing changed.')
        commands[0]['Command']=struct.pack('>HBII',0x41,8,4,10)+command[7:]
        header['SeqCommandTable']=acb_native.encode_table('SequenceCommand',acb_native.schema(header['SeqCommandTable']),commands)
        acb=acb_native.encode_table('Header',acb_native.schema(acb),[header])
        bank=self.work/(name+'.acb');bank.write_bytes(acb)
        asset=f'FFRS/Content/Sound/StudioNativeVoice/{name}'
        recipe={'legacyRoot':str(self.legacy),'outRoot':str(self.out),
                'atomBanks':[{'from':ffbe_audio.SHELL,'to':asset,'acb':str(bank),
                              'sha256':hashlib.sha256(acb).hexdigest(),
                              'cues':[{'id':i+1,'name':r['name'],'durationMs':r['durationMs']} for i,r in enumerate(records)]}]}
        path=self.work/'bank.json';path.write_text(json.dumps(recipe))
        self.env['run']([*self.env['FFRDT'],'patch',str(path),'--usmap',self.env['USMAP']])
        cues=[];template=target['voices'][0]
        view=self.view(template['package']);owner=next(e for e in view['Exports'] if e['ObjectName']==template['cue'])
        sheet=next(p['Value'] for p in owner['Data'] if p['Name']=='CueSheet')
        old_bank=view['Imports'][-sheet-1]
        old_package=party.import_name(view,old_bank['OuterIndex'])
        for i,rec in enumerate(records):
            rel=f'FFRS/Content/Sound/StudioNativeVoice/{name}_{i}_Cue'
            target_path=self.out/(rel+'.uasset');target_path.parent.mkdir(parents=True,exist_ok=True)
            renames=[template['cue']+'='+Path(rel).name,
                     old_package+'='+asset.replace('FFRS/Content/','/Game/'),old_bank['ObjectName']+'='+name]
            self.env['run']([*self.env['FFRDT'],'clone-package',str(self.legacy/(template['package']+'.uasset')),str(target_path),template['package'].replace('FFRS/Content/','/Game/'),rel.replace('FFRS/Content/','/Game/'),*renames,'--usmap',self.env['USMAP']])
            edits={'CueName':rec['name'],'Duration':len(recordings[i])/48000,'FirstWaveDuration':len(recordings[i])/48000}
            path=self.work/'cue.json'
            path.write_text(json.dumps({'legacyRoot':str(self.out),'outRoot':str(self.out),
                'objects':[{'asset':rel,'export':Path(rel).name,'set':edits}]}))
            self.env['run']([*self.env['FFRDT'],'patch',str(path),'--usmap',self.env['USMAP']])
            self.env['run']([*self.env['FFRDT'],'tojson',str(target_path),str(path),'--usmap',self.env['USMAP']])
            check=json.loads(path.read_text(encoding='utf-8-sig'))
            props={p['Name']:p['Value'] for p in check['Exports'][0]['Data']}
            sheet=check['Imports'][-props['CueSheet']-1]
            if (props['CueName']!=rec['name'] or sheet['ObjectName']!=name
                    or party.import_name(check,sheet['OuterIndex'])!=asset.replace('FFRS/Content/','/Game/')):
                raise ValueError('The private movie voice cue failed native readback.')
            cues.append((rel.replace('FFRS/Content/','/Game/'),Path(rel).name))

        return cues


def cached_file(cache,kind,relative):
    # Keep the user's portable root + cache suffix below Windows MAX_PATH.
    # Native asset paths are retained only as manifest keys, never nested here.
    return cache/kind/(hashlib.sha256(relative.encode()).hexdigest()[:24]+Path(relative).suffix)


def build(units,env):
    chosen=selected(units);root=Path(env['ROOT']);work=root/'build/native-voices'
    marker=work/'pak-managed.json'
    if not chosen and not marker.is_file():return
    builder=Builder(env);movies={};outputs=[]
    visions={v['ID']:v for v in env['rows'](VISION).values()} if chosen else {}
    selections={}
    for unit in chosen:
        sid=unit['lb'];source=visions[unit['nativeVoice']]['finishBlowSkill']
        if sid in selections and selections[sid]!=source:raise ValueError('Two default visions sharing a resonance have different voice selections.')
        selections[sid]=source
    # Prepared files are keyed by official container identity, mapping and implementation.
    listing=root/'extracted/utoc_filelist.tsv'
    containers=[(p.name,p.stat().st_size,p.stat().st_mtime_ns) for p in sorted(Path(env['ffrenv'].game_paks()).iterdir()) if p.is_file() and p.suffix in ('.pak','.utoc','.ucas')]
    identity={'revision':REVISION,'selection':selections,'containers':containers,'game':hashlib.sha256(listing.read_bytes()).hexdigest() if listing.is_file() else None,
              'mapping':hashlib.sha256(Path(env['USMAP']).read_bytes()).hexdigest(),
              'codec':hashlib.sha256((root/'tools/cave_music_preview.zip').read_bytes()).hexdigest(),
              'code':hashlib.sha256(Path(__file__).read_bytes()+Path(movie.__file__).read_bytes()+(root/'tools/native_voice_codec.ps1').read_bytes()).hexdigest()}
    key=hashlib.sha256(json.dumps(identity,sort_keys=True).encode()).hexdigest();cache=work/'cache'/key[:24]
    cached=cache/'manifest.json';valid=False
    if cached.is_file():
        try:
            saved=json.loads(cached.read_bytes())
            safe=lambda p: isinstance(p,str) and not Path(p).is_absolute() and '..' not in p.replace('\\','/').split('/')
            valid=all(safe(p) and p.startswith('FFRS/Content/') and cached_file(cache,'files',p).is_file() and hashlib.sha256(cached_file(cache,'files',p).read_bytes()).hexdigest()==digest for p,digest in saved['assets'].items())
            valid=valid and all(safe(p) and p.startswith('FFRS/Content/Streams/Movies/') and cached_file(cache,'movies',p).is_file() and hashlib.sha256(cached_file(cache,'movies',p).read_bytes()).hexdigest()==digest for p,digest in saved['movies'].items())
        except (OSError,ValueError,KeyError,TypeError):valid=False
    if chosen and valid:
        for rel in saved['assets']:
            target=Path(env['OUT'])/rel;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(cached_file(cache,'files',rel),target)
        movies={rel:cached_file(cache,'movies',rel).read_bytes() for rel in saved['movies']}
        print(f'  Reused {len(chosen)} prepared default vision voice selections.',flush=True)
    elif chosen:
        for sid,source in selections.items():
            target=builder.profile(sid);donor=builder.profile(source)
            if target['movies']:
                if donor['movies']:
                    voice=builder.original('FFRS/Content/Streams/'+next(iter(donor['movies'].values())))
                else:
                    recordings=builder.recordings(donor)
                    template=builder.original('FFRS/Content/Streams/'+next(iter(target['movies'].values())))
                    _,info,_=adx_stream(template);samples=[(0,0)]*info['total_samples']
                    # Opening and release retain the source's relative voice timing.
                    start=donor['voices'][0]['start']
                    for rec,event in zip(recordings,donor['voices']):
                        offset=round((event['start']-start)*2)
                        for i,pair in enumerate(rec[:max(0,len(samples)-offset)]):samples[offset+i]=pair
                    voice=encoded_movie_voice(template,builder.convert('wave-adx',wave(samples)))
                for rel,file in target['movies'].items():
                    original=builder.original('FFRS/Content/Streams/'+file);changed,info=replace_movie_voice(original,voice)
                    entry='FFRS/Content/Streams/'+file;movies[entry]=changed
                    view=copy.deepcopy(builder.view(rel))
                    for e in view['Exports']:
                        for p in e.get('Data',[]):
                            if p['Name']=='AudioTracks':
                                for track in p['Value']:
                                    for prop in track['Value']:
                                        if prop['Name']=='TotalSamples':prop['Value']=info['total_samples']
                    builder.write_asset(rel,view);outputs.extend([rel+'.uasset',rel+'.uexp'])
            else:
                if donor['voices']:cues=[(v['package'].replace('FFRS/Content/','/Game/'),v['cue']) for v in donor['voices']]
                else:
                    cues=builder.private_cues(target,builder.recordings(donor),source)
                    outputs.extend(p.relative_to(builder.out).as_posix() for p in (builder.out/'FFRS/Content/Sound/StudioNativeVoice').rglob('*') if p.is_file())
                builder.sound_edits(target,cues)
                outputs.extend(p+suffix for p in {v['asset'] for v in target['voices']} for suffix in ('.uasset','.uexp'))
            print(f'  Default resonance {sid}: selected original vision voice {source}; effects and pictures retained.',flush=True)
        cache.mkdir(parents=True,exist_ok=True)
        saved={'assets':{},'movies':{}}
        for rel in sorted(set(outputs)):
            source=builder.out/rel;target=cached_file(cache,'files',rel);target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,target)
            saved['assets'][rel]=hashlib.sha256(source.read_bytes()).hexdigest()
        for rel,data in movies.items():
            target=cached_file(cache,'movies',rel);target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data);saved['movies'][rel]=hashlib.sha256(data).hexdigest()
        cached.write_text(json.dumps(saved,indent=2))
    # Share the existing companion pak; manage only voice-owned original stream overrides.
    stage=root/'build/fina-cinematic/pak-input';stage.mkdir(parents=True,exist_ok=True)
    old=json.loads(marker.read_bytes()) if marker.is_file() else {'files':[]}
    for rel in old['files']:
        if not re.fullmatch(r'FFRS/Content/Streams/Movies/[A-Za-z0-9_/.-]+\.usm',rel):raise ValueError('Invalid managed native voice movie path.')
        target=stage/rel
        if target.is_file():target.unlink()
    for rel,data in movies.items():
        target=stage/rel;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
    if old['files'] or movies:
        destination=root/'build/out'/('zzz_'+env['ffrenv'].MOD_NAME+'_P.pak');destination.parent.mkdir(parents=True,exist_ok=True)
        temporary=work/'companion.pak'
        env['run']([str(root/'tools/repak/repak.exe'),'pack','--version','V11','--mount-point','../../../',str(stage),str(temporary)])
        os.replace(temporary,destination)
    if movies:marker.write_text(json.dumps({'files':sorted(movies)}))
    elif marker.is_file():marker.unlink()
