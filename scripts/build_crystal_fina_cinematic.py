"""Render the illustrated Crystal Fina movie test (developer tool, not needed by players).

Input is the image-generated keyframe in artwork/. Animation is deliberately
illustrated: camera movement, light, particles, growing cracks and glass shards.
The character is not represented as a fully animated 3D model.
Requires Pillow, numpy, ffmpeg and WannaCRI 0.3.3 for the VP9/USM container.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import subprocess
import wave
import zipfile

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

WIDTH, HEIGHT, FPS, FRAMES = 1280, 720, 30, 192
SECONDS = FRAMES / FPS
ROOT = Path(__file__).resolve().parents[1]


def ease(x):
    x = max(0., min(1., x))
    return x*x*(3-2*x)


def score(path):
    """Original, quiet chime/air buildup with a short glass release, no speech."""
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
    # Deterministic short, bright but bounded glass-like release.
    q=np.maximum(t-5.55,0); env=np.exp(-q*7)*(t>=5.55)
    for freq in [2137,2861,3547,4871,6311]:
        sound += .018*env*np.sin(2*np.pi*freq*q)
    sound *= np.minimum(t/.08,1)*np.clip((SECONDS-t)/.35,0,1)
    sound = np.clip(sound,-.85,.85)
    with wave.open(str(path),'wb') as w:
        w.setnchannels(1);w.setsampwidth(2);w.setframerate(rate)
        w.writeframes((sound*32767).astype('<i2').tobytes())


def render(art, directory):
    directory.mkdir(parents=True,exist_ok=True)
    image=Image.open(art).convert('RGB').resize((WIDTH,HEIGHT),Image.Resampling.LANCZOS)
    rng=np.random.default_rng(13503)
    motes=[(rng.uniform(.12,.88),rng.uniform(0,1),rng.uniform(.015,.07),
            rng.uniform(.5,1.8),rng.uniform(0,6.3)) for _ in range(95)]
    # Fracture paths stay predominantly on the crystal's outer faces.
    paths=[]
    for x0,y0 in [(.5,.05),(.39,.28),(.61,.28),(.41,.53),(.59,.53),(.47,.79),(.53,.79)]:
        points=[(x0,y0)]
        for _ in range(5):
            x,y=points[-1];points.append((x+rng.uniform(-.025,.025),min(.95,y+rng.uniform(.03,.07))))
        paths.append(points)
    fragments=[]
    for _ in range(28):
        side=rng.choice([-1,1]); x=.5+side*rng.uniform(.10,.155);y=rng.uniform(.2,.78)
        width=rng.uniform(.015,.043);height=rng.uniform(.045,.115)
        polygon=[(round(x*WIDTH),round(y*HEIGHT)),(round((x+side*width)*WIDTH),round((y+height*.3)*HEIGHT)),
                 (round((x-side*width*.3)*WIDTH),round((y+height)*HEIGHT))]
        mask=Image.new('L',image.size);ImageDraw.Draw(mask).polygon(polygon,fill=115)
        # Glass catches the release light; dark background cutouts look opaque.
        box=mask.getbbox()
        piece=Image.blend(image.crop(box),Image.new('RGB',(box[2]-box[0],box[3]-box[1]),(220,244,255)),.8).convert('RGBA')
        piece.putalpha(mask.crop(box))
        edge=ImageDraw.Draw(piece)
        edge.line([(px-box[0],py-box[1]) for px,py in polygon+[polygon[0]]],fill=(237,251,255,210),width=1)
        fragments.append((piece,box,side*rng.uniform(220,650),rng.uniform(-210,180),rng.uniform(-100,100)))
    silent=directory/'crystal-fina-silent.mp4'
    encoder=subprocess.Popen(['ffmpeg','-v','error','-y','-f','rawvideo','-pix_fmt','rgb24',
        '-s',f'{WIDTH}x{HEIGHT}','-r',str(FPS),'-i','pipe:0','-an','-c:v','libx264',
        '-preset','fast','-crf','18','-pix_fmt','yuv420p',str(silent)],stdin=subprocess.PIPE)
    thumbnails=[]
    try:
        for index in range(FRAMES):
            t=index/FPS
            # Begin close to the face/heart, reveal the complete crystal, then hold.
            zoom=1.72-.72*ease(t/3.8)
            crop_width=WIDTH/zoom;crop_height=HEIGHT/zoom
            cy=HEIGHT*(.38+.12*ease(t/3.8));cx=WIDTH*(.5+.002*math.sin(t*.9))
            left=max(0,min(WIDTH-crop_width,cx-crop_width/2));top=max(0,min(HEIGHT-crop_height,cy-crop_height/2))
            frame=image.crop((left,top,left+crop_width,top+crop_height)).resize(image.size,Image.Resampling.BICUBIC)
            def point(x,y):return ((x*WIDTH-left)*zoom,(y*HEIGHT-top)*zoom)
            glow=Image.new('RGBA',image.size);draw=ImageDraw.Draw(glow)
            hx,hy=point(.5,.34);pulse=.5+.5*math.sin(t*2.3)
            strength=.16+.16*pulse+.65*ease((t-3.9)/1.8)
            radius=25+45*strength
            draw.ellipse((hx-radius,hy-radius,hx+radius,hy+radius),fill=(255,221,154,round(95*strength)))
            for x,y,speed,size,phase in motes:
                px,py=point(x+.008*math.sin(t+phase),(y-t*speed)%1)
                alpha=round((.3+.7*abs(math.sin(phase+t*1.4)))*145)
                draw.ellipse((px-size,py-size,px+size,py+size),fill=(170,222,255,alpha))
                if size>1.3:draw.line((px-4,py,px+4,py),fill=(212,239,255,alpha//2))
            crack=ease((t-4.15)/1.3)
            if crack:
                for number,path in enumerate(paths):
                    count=max(1,round((len(path)-1)*min(1,crack*1.3-number*.025)))
                    pts=[point(*p) for p in path[:count+1]]
                    draw.line(pts,fill=(160,230,255,round(225*crack)),width=2)
            frame=Image.alpha_composite(frame.convert('RGBA'),glow.filter(ImageFilter.GaussianBlur(11)))
            frame=Image.alpha_composite(frame,glow)
            blast=ease((t-5.45)/.7)
            if blast:
                frame=Image.blend(frame,Image.new('RGBA',frame.size,(238,249,255,255)),blast*.88)
                elapsed=max(t-5.55,0)
                for piece,box,vx,vy,spin in fragments:
                    if not elapsed:continue
                    p=piece.rotate(spin*elapsed,Image.Resampling.BICUBIC,expand=True)
                    x=(box[0]+box[2])/2+vx*elapsed;y=(box[1]+box[3])/2+vy*elapsed+80*elapsed**2
                    frame.alpha_composite(p,(round(x-p.width/2),round(y-p.height/2)))
            white=ease((t-6.02)/.33)
            if white:frame=Image.blend(frame,Image.new('RGBA',frame.size,'white'),white)
            fade=ease(t/.32)
            frame=Image.blend(Image.new('RGBA',frame.size,'black'),frame,fade).convert('RGB')
            if index in (15,60,115,155,171,182):thumbnails.append(frame.resize((384,216)))
            encoder.stdin.write(frame.tobytes())
        encoder.stdin.close()
        if encoder.wait():raise RuntimeError('Cinematic video encoder failed')
    finally:
        if encoder.poll() is None:encoder.kill()
    sheet=Image.new('RGB',(384*3,216*2))
    for i,frame in enumerate(thumbnails):sheet.paste(frame,((i%3)*384,(i//3)*216))
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
    report={'schema':1,'revision':'crystal-fina-film-1','width':WIDTH,'height':HEIGHT,'fps':FPS,
            'frames':FRAMES,'seconds':SECONDS,'artSha256':hashlib.sha256(art.read_bytes()).hexdigest(),
            'method':'Illustrated keyframe, authored camera/light/particles/fractures/shards; original synthesized score',
            'usmCodec':'VP9','audio':'Separate native HCA sound bank, synchronized to movie start',
            'maxPictureDataSize':video.crid_page['minbuf'].val}
    (directory/'render.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


def package(directory, destination):
    """Package a rendered movie and VGAudio Highest-quality mono HCA score."""
    spec = json.loads((directory/'render.json').read_text())
    hca = (directory/'score.hca').read_bytes()
    digest = hashlib.sha256(hca).hexdigest()
    audio = {'schema':'ffr-audio-1', 'cues':{'1':{'name':'studio_crystal_fina_intro','cueIndex':0,'durationMs':6400}},
             'recordings':[{'sourceCueId':1,'variation':0,'sourceWaveIndex':0,'sourceWaveId':0,
                            'name':'studio_crystal_fina_intro__v1','durationMs':6400,'sourceEncodeType':2,
                            'channels':1,'sampleRate':48000,'samples':307200}],
             'waves':{'0':{'sha256':digest}}}
    files = {'spec.json':(json.dumps(spec,indent=2)+'\n').encode(),
             'movie.usm':(directory/'crystal-fina.usm').read_bytes(),'score.hca':hca,
             'audio.json':(json.dumps(audio,indent=2)+'\n').encode(),
             'preview.mp4':(directory/'Crystal-Fina-Cinematic-Preview.mp4').read_bytes()}
    poster=Image.open(ROOT/'artwork/crystal_fina_cinematic.png').convert('RGB')
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
    p.add_argument('--package',type=Path,help='Package existing render plus score.hca instead of rendering')
    a=p.parse_args()
    if a.package:package(a.output,a.package)
    else:render(a.art,a.output)
