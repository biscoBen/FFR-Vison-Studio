"""Keep every approved movie picture, removing the discarded embedded score.

The runtime plays BGM_PP_DUNGEON_CAVE1 through a private native Atom cue; the
browser preview is intentionally picture-only rather than presenting old music.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import zipfile

from cri_usm_movie import chunks, normalize, without_soundtrack


def replace(archive, source, destination, work):
    work.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archive) as z:
        spec = json.loads(z.read('spec.json'))
        original = z.read('movie.usm'); poster = z.read('poster.jpg')
    if hashlib.sha256(source.read_bytes()).hexdigest() != spec['sourceMovie']['sha256']:
        raise ValueError('The approved rotating lighter movie changed.')
    movie, container = normalize(without_soundtrack(original), opaque_alpha=True)
    pictures = lambda raw: [(p['type'], p['payload'], p['header'][16:24]) for p in chunks(raw)
                           if p['kind'] == 0 and p['type'] in (b'@SFV', b'@ALP')]
    if pictures(original) != pictures(movie): raise ValueError('The cave soundtrack changed a picture.')
    preview = work / 'preview.mp4'
    subprocess.run(['ffmpeg', '-y', '-v', 'error', '-i', str(source), '-map', '0:v:0',
                    '-c:v', 'copy', '-an', '-movflags', '+faststart', str(preview)], check=True)
    spec.update(revision='crystal-fina-film-4', audio='Native secret-cave music from the beginning',
                audioReplaced=True, embeddedAudio=None, previewHasAudio=False,
                soundtrack={'kind':'nativeCue', 'cueSheet':'BGM_PP', 'cueName':'BGM_PP_DUNGEON_CAVE1',
                            'startSeconds':0, 'movieStartTick':48000, 'movieEndTick':201600},
                container=container, **container)
    spec.pop('audioEnding', None)
    files = {'spec.json':(json.dumps(spec, indent=2)+'\n').encode(), 'movie.usm':movie,
             'preview.mp4':preview.read_bytes(), 'poster.jpg':poster}
    metadata = {'schema':1, 'revision':spec['revision'],
                'files':{n:hashlib.sha256(b).hexdigest() for n,b in files.items()}}
    with zipfile.ZipFile(destination, 'w', zipfile.ZIP_DEFLATED) as z:
        z.writestr('manifest.json', json.dumps(metadata,indent=2)+'\n')
        for n,b in files.items(): z.writestr(n,b)
    return metadata


if __name__ == '__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('archive','source','destination','work'): p.add_argument('--'+name,type=Path,required=True)
    args=p.parse_args()
    print(json.dumps(replace(args.archive,args.source,args.destination,args.work),indent=2))
