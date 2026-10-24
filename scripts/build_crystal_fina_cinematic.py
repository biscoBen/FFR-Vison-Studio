"""Render the illustrated Crystal Fina movie test (developer tool, not needed by players).

Input is the image-generated keyframe in artwork/. Animation is deliberately
illustrated: a wide-to-close camera, an intact rotating 3D crystal and opening eyes.
The character is not represented as a fully animated 3D model.
Requires Blender 4.3, Pillow, numpy, ffmpeg and WannaCRI 0.3.3 for the VP9/USM container.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import wave
import zipfile

import numpy as np
from PIL import Image

WIDTH, HEIGHT, FPS, FRAMES = 1280, 720, 30, 192
SECONDS = FRAMES / FPS
ROOT = Path(__file__).resolve().parents[1]


def ease(x):
    x = max(0., min(1., x))
    return x*x*(3-2*x)


def score(path):
    """Original quiet chime/air buildup ending in a soft awakening chord."""
    rate = 48000; t = np.arange(round(SECONDS*rate)) / rate
    rng = np.random.default_rng(13503); sound = np.zeros_like(t)
    for start, freq in [(0.,261.6256),(.35,391.9954),(.8,523.2511),(1.8,659.2551),
                        (3.2,783.9909),(4.3,1046.5023),(5.45,1567.9817)]:
        q = np.maximum(t-start,0); env = (1-np.exp(-q*9))*np.exp(-q/2.0)*(t>=start)
        partial = sum(np.sin(2*np.pi*freq*harm*q)*amp
                      for harm,amp in [(1,1),(2.003,.24),(3.99,.08)])
        sound += .065*env*partial
    air = rng.normal(0,1,len(t))
    air = np.convolve(air,np.ones(21)/21,mode='same')
    sound += air*.05*np.clip(t/5.4,0,1)**2
    # The ending is an awakening, with a soft musical resolution and no break sound.
    q=np.maximum(t-5.5,0);env=(1-np.exp(-q*10))*np.exp(-q*1.8)*(t>=5.5)
    for freq,level in [(523.2511,.045),(659.2551,.032),(783.9909,.022)]:
        sound += level*env*np.sin(2*np.pi*freq*q)
    sound *= np.minimum(t/.08,1)*np.clip((SECONDS-t)/.35,0,1)
    sound = np.clip(sound,-.85,.85)
    with wave.open(str(path),'wb') as w:
        w.setnchannels(1);w.setsampwidth(2);w.setframerate(rate)
        w.writeframes((sound*32767).astype('<i2').tobytes())


def render(art, directory, reuse_frames=False):
    directory.mkdir(parents=True,exist_ok=True)
    if not reuse_frames:
        subprocess.run(['blender','-b','-t','4','--python',str(ROOT/'scripts/render_crystal_fina_rotation.py'),
                        '--','--output',str(directory),'--width',str(WIDTH),'--samples','4'],check=True)
    scene=json.loads((directory/'scene.json').read_text())
    if (scene['width'],scene['height'],scene['fps'],scene['frames']) != (WIDTH,HEIGHT,FPS,FRAMES):
        raise ValueError('The rendered scene does not match the native movie dimensions and duration')
    frames=[directory/f'frame-{i:04d}.png' for i in range(1,FRAMES+1)]
    if not all(p.is_file() for p in frames):raise ValueError('The complete rendered frame sequence is required')
    silent=directory/'crystal-fina-silent.mp4'
    subprocess.run(['ffmpeg','-v','error','-y','-framerate',str(FPS),'-start_number','1',
        '-i',str(directory/'frame-%04d.png'),'-frames:v',str(FRAMES),'-an','-c:v','libx264',
        '-preset','fast','-crf','18','-pix_fmt','yuv420p',str(silent)],check=True)
    sheet=Image.new('RGB',(384*3,216*2))
    for i,index in enumerate((1,40,80,120,156,192)):
        frame=Image.open(directory/f'frame-{index:04d}.png').convert('RGB').resize((384,216),Image.Resampling.LANCZOS)
        sheet.paste(frame,((i%3)*384,(i//3)*216))
    sheet.save(directory/'contact-sheet.jpg',quality=90)
    score(directory/'score.wav')
    subprocess.run(['ffmpeg','-v','error','-y','-i',str(silent),'-i',str(directory/'score.wav'),
        '-c:v','copy','-c:a','aac','-b:a','160k','-movflags','+faststart',str(directory/'Crystal-Fina-Cinematic-Preview.mp4')],check=True)
    subprocess.run(['ffmpeg','-v','error','-y','-i',str(silent),'-an','-c:v','libvpx-vp9',
        '-crf','29','-b:v','0','-row-mt','1','-cpu-used','3','-g','30','-pix_fmt','yuv420p',
        str(directory/'crystal-fina.ivf')],check=True)
    from wannacri.usm import Usm,Vp9,OpMode
    video=Vp9(str(directory/'crystal-fina.ivf'))
    usm=Usm(videos=[video],version=video.crid_page['fmtver'].val)
    with (directory/'crystal-fina.usm').open('wb') as f:
        for packet in usm.stream(OpMode.NONE):f.write(packet)
    from cri_usm_movie import normalize
    normalized, container = normalize((directory/'crystal-fina.usm').read_bytes())
    (directory/'crystal-fina.usm').write_bytes(normalized)
    report={**scene,'artSha256':hashlib.sha256(art.read_bytes()).hexdigest(),
            'eyeColor':'red','audioEnding':'soft awakening chord; no breaking sound',
            'usmCodec':'VP9','audio':'Separate native HCA sound bank, synchronized to movie start',
            'maxPictureDataSize':container['maxPictureDataSize'],'container':container}
    (directory/'render.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


def package(directory, destination):
    """Package a movie, its native stereo ADX score and clean source WAV."""
    spec = json.loads((directory/'render.json').read_text())
    files = {'spec.json':(json.dumps(spec,indent=2)+'\n').encode(),
             'movie.usm':(directory/'crystal-fina.usm').read_bytes(),
             'score.adx':(directory/'score.adx').read_bytes(),
             'score.wav':(directory/'score.wav').read_bytes(),
             'preview.mp4':(directory/'Crystal-Fina-Cinematic-Preview.mp4').read_bytes()}
    poster=Image.open(directory/'frame-0001.png').convert('RGB')
    import io
    stream=io.BytesIO();poster.save(stream,format='JPEG',quality=90);files['poster.jpg']=stream.getvalue()
    files['manifest.json']=(json.dumps({'schema':1,'revision':spec['revision'],
        'files':{n:hashlib.sha256(data).hexdigest() for n,data in files.items()}},indent=2)+'\n').encode()
    with zipfile.ZipFile(destination,'w',compression=zipfile.ZIP_DEFLATED) as archive:
        for name,data in sorted(files.items()):
            info=zipfile.ZipInfo(name,date_time=(2026,10,23,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED
            archive.writestr(info,data)
    print('Packaged',destination)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--art',type=Path,default=ROOT/'artwork/crystal_fina_cinematic.png')
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--package',type=Path,help='Package existing render plus score.adx and score.wav instead of rendering')
    p.add_argument('--reuse-frames',action='store_true',help='Encode the already completed Blender frame sequence')
    a=p.parse_args()
    if a.package:package(a.output,a.package)
    else:render(a.art,a.output,a.reuse_frames)
