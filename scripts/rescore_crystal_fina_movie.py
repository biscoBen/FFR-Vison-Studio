"""Replace only the score in the existing movie, preserving every video packet.

Developer tool. Encode the clean stereo WAV with encode_movie_adx.ps1 first;
FFmpeg and WannaCRI are required only to prepare the finished Studio payload.
"""
import argparse
import hashlib
import io
import json
from pathlib import Path
import subprocess
import wave
import zipfile

from cri_usm_movie import chunks, native_adx, with_soundtrack, without_soundtrack


def video_hash(path):
    return subprocess.check_output(['ffmpeg','-v','error','-i',str(path),'-map','0:v:0',
        '-c','copy','-f','hash','-hash','sha256','-'],text=True).strip().split('=')[1]


def preview_with_score(source, score, output):
    subprocess.run(['ffmpeg','-v','error','-y','-i',str(source),'-i',str(score),
        '-map','0:v:0','-map','1:a:0','-c:v','copy','-c:a','aac','-b:a','192k',
        '-movflags','+faststart',str(output)],check=True)
    if video_hash(source)!=video_hash(output): raise ValueError('Preview video changed while rescoring')


def rescore(archive, source, score_wave, score_adx, destination, output):
    with zipfile.ZipFile(archive) as z: files={n:z.read(n) for n in z.namelist()}
    spec=json.loads(files['spec.json'])
    if hashlib.sha256(source.read_bytes()).hexdigest()!=spec['sourceMovie']['sha256']:
        raise ValueError('Use the exact approved source movie')
    with wave.open(str(score_wave)) as wav:
        if (wav.getnchannels(),wav.getsampwidth(),wav.getframerate(),wav.getnframes())!=(2,2,48000,307200):
            raise ValueError('Expected a 6.4-second stereo 48-kHz PCM score')
    output.mkdir(parents=True,exist_ok=True)
    preview=output/'Crystal-Fina-Piano-Organ-Preview.mp4'
    preview_with_score(source,score_wave,preview)
    adx=native_adx(score_adx.read_bytes())
    before=chunks(files['movie.usm'])
    movie,container=with_soundtrack(without_soundtrack(files['movie.usm']),adx)
    after=chunks(movie)
    for channel in (b'@SFV',b'@ALP'):
        if [p['payload'] for p in before if p['type']==channel and p['kind']==0] != [
                p['payload'] for p in after if p['type']==channel and p['kind']==0]:
            raise ValueError('Rescoring changed a movie picture')
    spec.update(revision='crystal-fina-film-3',audio='Light spacious piano building into an intense suspended organ ending; embedded stereo ADX',
        audioEnding='Intense unresolved organ crescendo as her eyes open; no breaking sound',
        embeddedAudio={'codec':'Adx','channels':2,'sampleRate':48000,'samples':307200},
        previewMatchesSource=False,previewVideoMatchesSource=True,previewVideoSha256=video_hash(preview),
        audioReplaced=True,container=container)
    spec['soundtrack']=json.loads(score_wave.with_suffix('.json').read_text())
    files={'spec.json':(json.dumps(spec,indent=2)+'\n').encode(),'movie.usm':movie,
           'score.adx':adx,'score.wav':score_wave.read_bytes(),
           'preview.mp4':preview.read_bytes(),'poster.jpg':files['poster.jpg']}
    manifest={'schema':1,'revision':spec['revision'],
              'files':{name:hashlib.sha256(raw).hexdigest() for name,raw in files.items()}}
    files['manifest.json']=(json.dumps(manifest,indent=2)+'\n').encode()
    # Assemble before replacing the destination, which may be the input archive.
    stream=io.BytesIO()
    with zipfile.ZipFile(stream,'w',compression=zipfile.ZIP_DEFLATED) as z:
        for name,raw in sorted(files.items()):
            info=zipfile.ZipInfo(name,date_time=(2026,10,24,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED
            z.writestr(info,raw)
    destination.write_bytes(stream.getvalue())
    for name in ('movie.usm','score.adx'): (output/name).write_bytes(files[name])
    return {'movieSha256':manifest['files']['movie.usm'],'previewVideoSha256':spec['previewVideoSha256'],
            'container':container,'soundtrack':spec['soundtrack']['revision']}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('archive','source','score-wav','score-adx','destination','output'):
        parser.add_argument('--'+name,type=Path,required=True)
    args=parser.parse_args()
    print(json.dumps(rescore(args.archive,args.source,args.score_wav,args.score_adx,args.destination,args.output),indent=2))
