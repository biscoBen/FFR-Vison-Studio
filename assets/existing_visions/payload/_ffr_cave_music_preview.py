"""Preview the installed cave recording locally; retain no game keys or full bank."""
import hashlib
import io
import json
from pathlib import Path
import struct
import subprocess
import tempfile
import threading
import zipfile

_LOCK=threading.Lock()
ENTRY='FFRS/Content/Streams/Sound/BGM_PP.awb'
STREAM_ID=56  # BGM_PP_DUNGEON_CAVE1: native cue 10046 / waveform 46.


def read_exact(stream, count):
    result=bytearray()
    while len(result)<count:
        part=stream.read(min(count-len(result),1024*1024))
        if not part: raise ValueError('The cave music stream is incomplete.')
        result.extend(part)
    return bytes(result)


def extract_wave(stream, stream_id=STREAM_ID):
    header=read_exact(stream,16)
    if header[:4]!=b'AFS2': raise ValueError('The cave music bank has an unknown format.')
    width,id_width=header[5:7];count=int.from_bytes(header[8:12],'little')
    align=int.from_bytes(header[12:14],'little');subkey=int.from_bytes(header[14:16],'little')
    if width not in (2,4,8) or id_width not in (2,4) or not align or not 0<count<10000:
        raise ValueError('The cave music bank layout changed.')
    table=read_exact(stream,count*id_width+(count+1)*width)
    ids=[int.from_bytes(table[i*id_width:(i+1)*id_width],'little') for i in range(count)]
    if ids.count(stream_id)!=1: raise ValueError('The cave recording is absent from this bank.')
    index=ids.index(stream_id);base=count*id_width
    start=int.from_bytes(table[base+index*width:base+(index+1)*width],'little')
    end=int.from_bytes(table[base+(index+1)*width:base+(index+2)*width],'little')
    start=(start+align-1)//align*align;position=16+len(table)
    if not position<=start<end or end-start>16*1024**2 or start>2*1024**3:
        raise ValueError('The cave recording bounds changed.')
    while position<start:
        size=min(1024*1024,start-position);read_exact(stream,size);position+=size
    return read_exact(stream,end-start),subkey


def decrypt(raw,key,subkey):
    from ffbe_effects.hca_host import encryption_table,crc
    raw=bytearray(raw);size=int.from_bytes(raw[6:8],'big')
    if not 40<=size<=len(raw): raise ValueError('Invalid cave recording header.')
    # HCA obfuscates tag characters separately from its encrypted frame bytes.
    tags=(b'HCA\0',b'fmt\0',b'comp',b'dec\0',b'vbr\0',b'ath\0',b'loop',b'ciph',b'rva\0',b'comm',b'pad\0')
    for pos in range(size-3):
        tag=bytes(v&127 for v in raw[pos:pos+4])
        if tag in tags:raw[pos:pos+4]=tag
    if raw[:4]!=b'HCA\0' or raw[8:12]!=b'fmt\0':raise ValueError('Unsupported cave recording.')
    comp=raw[:size].find(b'comp');cipher=raw[:size].find(b'ciph')
    if comp<0 or cipher<0:raise ValueError('The cave recording codec changed.')
    frame_size=int.from_bytes(raw[comp+4:comp+6],'big');mode=int.from_bytes(raw[cipher+4:cipher+6],'big')
    if not frame_size or (len(raw)-size)%frame_size:raise ValueError('Invalid cave recording frames.')
    if mode==56:
        encrypt=encryption_table(key,subkey);inverse=bytearray(256)
        for plain,encoded in enumerate(encrypt):inverse[encoded]=plain
        for pos in range(size,len(raw),frame_size):
            block=raw[pos:pos+frame_size-2].translate(inverse)
            raw[pos:pos+frame_size]=block+struct.pack('>H',crc(block))
    elif mode!=0:raise ValueError('Unsupported cave recording cipher.')
    raw[cipher+4:cipher+6]=bytes(2);raw[size-2:size]=struct.pack('>H',crc(raw[:size-2]))
    return bytes(raw)


def trim_wave(raw,seconds=6.4):
    # The distributed frozen engine does not contain Python's wave module.
    # VGAudio writes PCM RIFF; retain its samples/format without that dependency.
    if len(raw)<12 or raw[:4]!=b'RIFF' or raw[8:12]!=b'WAVE':raise ValueError('Invalid decoded cave WAV.')
    pos=12;fmt=None;data=None
    while pos+8<=len(raw):
        kind=raw[pos:pos+4];size=struct.unpack_from('<I',raw,pos+4)[0];start=pos+8
        if start+size>len(raw):raise ValueError('Incomplete decoded cave WAV.')
        if kind==b'fmt ':fmt=raw[start:start+size]
        elif kind==b'data':data=raw[start:start+size]
        pos=start+size+(size&1)
    if fmt is None or len(fmt)<16 or data is None:raise ValueError('Missing decoded cave WAV samples.')
    codec,channels,rate,byte_rate,align,bits=struct.unpack_from('<HHIIHH',fmt)
    if codec==65534 and len(fmt)>=40 and fmt[24:40]==bytes.fromhex('0100000000001000800000aa00389b71'):codec=1
    if codec!=1 or bits not in (8,16,24,32) or not 1<=channels<=8 or not 8000<=rate<=192000 or align!=channels*bits//8 or byte_rate!=rate*align or len(data)%align:
        raise ValueError('Unsupported decoded cave WAV format.')
    data=data[:round(seconds*rate)*align]
    def chunk(tag,value):return tag+struct.pack('<I',len(value))+value+bytes(len(value)&1)
    body=b'WAVE'+chunk(b'fmt ',fmt)+chunk(b'data',data)
    return b'RIFF'+struct.pack('<I',len(body))+body


def audio(root, ffrenv):
    """Read once for preview or the optional cinematic; retain a short local copy."""
    root=Path(root)
    import _ffr_deck_sync
    identity=_ffr_deck_sync.game_identity(Path(ffrenv.game_root()))
    archive=root/'tools/cave_music_preview.zip'
    fingerprint=hashlib.sha256((json.dumps(identity,sort_keys=True)+hashlib.sha256(archive.read_bytes()).hexdigest()).encode()).hexdigest()[:24]
    folder=root/'build/fina-preview-audio';folder.mkdir(parents=True,exist_ok=True)
    target=folder/(fingerprint+'.wav')
    with _LOCK:
        if target.is_file():return target.read_bytes()
        raw=None
        # Loose installed files and official pak entries use the same AFS2 data.
        loose=Path(ffrenv.game_root())/ENTRY
        if loose.is_file():
            with loose.open('rb') as stream:raw,subkey=extract_wave(stream)
        else:
            paks=Path(ffrenv.game_paks())
            for pak in sorted(paks.glob('FFRS-Windows*.pak'),reverse=True):
                process=subprocess.Popen([str(root/'tools/repak/repak.exe'),'get',str(pak),ENTRY],stdout=subprocess.PIPE,stderr=subprocess.DEVNULL)
                try:raw,subkey=extract_wave(process.stdout);break
                except ValueError:continue
                finally:
                    process.stdout.close()
                    if process.poll() is None:process.kill()
                    process.wait()
        if raw is None:raise ValueError('The installed cave audio bank could not be read.')
        import ffbe_audio
        from ffbe_effects.hca_host import key_from_config
        plain=decrypt(raw,key_from_config(ffbe_audio.host_config({})),subkey)
        with tempfile.TemporaryDirectory(prefix='decode-',dir=folder) as temporary:
            work=Path(temporary)
            with zipfile.ZipFile(archive) as z:
                if set(z.namelist())!={'VGAudio.dll','LICENSE.txt','decode.ps1','encode.ps1'}:raise ValueError('Invalid preview decoder.')
                for name in z.namelist():(work/name).write_bytes(z.read(name))
            source=work/'source.hca';source.write_bytes(plain)
            result=subprocess.run(['powershell.exe','-NoProfile','-NonInteractive','-ExecutionPolicy','Bypass','-File',str(work/'decode.ps1'),str(source),str(work/'decoded.wav')],capture_output=True)
            if result.returncode:raise ValueError('The installed cave recording could not be decoded for browser playback.')
            encoded=trim_wave((work/'decoded.wav').read_bytes())
        temporary=target.with_suffix('.tmp');temporary.write_bytes(encoded);temporary.replace(target)
        return encoded
