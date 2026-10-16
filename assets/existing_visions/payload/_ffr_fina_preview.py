"""Serve the native Fina presentation before the generic cached FFBE routes."""
from functools import lru_cache
import hashlib
import json
from pathlib import Path
import zipfile

SPRITE = '99887755552703'
VERSION = 'native-fina-10'


@lru_cache(maxsize=1)
def bundle():
    with zipfile.ZipFile(Path(__file__).with_name('fina_battle_preview.zip')) as archive:
        if len(archive.namelist()) != 4 or set(archive.namelist()) != {'manifest.json', 'idle.webp', 'atk.webp', 'limitatk.webp'}:
            raise ValueError('The native Fina preview archive is incomplete.')
        manifest = json.loads(archive.read('manifest.json'))
        if (manifest.get('schema') != 1 or manifest.get('presentation') != VERSION
                or set(manifest.get('animations', {})) != {'idle', 'atk', 'limitatk'}):
            raise ValueError('Unsupported native Fina preview manifest.')
        images = {}
        for name, entry in manifest['animations'].items():
            if entry.get('file') != name + '.webp' or not 0 < entry.get('seconds', 0) <= 100:
                raise ValueError('Invalid native Fina preview entry.')
            data = archive.read(entry['file'])
            if not data.startswith(b'RIFF') or data[8:12] != b'WEBP' or hashlib.sha256(data).hexdigest() != entry.get('sha256'):
                raise ValueError('The native Fina preview failed verification.')
            images[name] = data
    return manifest, images


def register(app, env):
    from fastapi import HTTPException
    from fastapi.responses import Response
    def entry(anim):
        manifest, images = bundle()
        if anim not in images: raise HTTPException(404, 'No such native Crystal Fina animation.')
        return manifest['animations'][anim], images[anim]
    def image(anim):
        return Response(entry(anim)[1], media_type='image/webp', headers={'Cache-Control': 'no-store', 'X-Fina-Presentation': VERSION})
    # register() runs directly after app creation, before the engine's generic
    # routes. These literal form paths therefore bypass old on-disk previews.
    @app.get('/api/ffbe/anims/' + SPRITE)
    def animations():
        manifest, _ = bundle()
        return {'form': SPRITE, 'anims': list(manifest['animations']), 'presentation': VERSION,
                'description': manifest['description']}
    @app.get('/api/ffbe/motion/' + SPRITE + '/{anim}')
    def duration(anim: str):
        return {'form': SPRITE, 'anim': anim, 'seconds': round(entry(anim)[0]['seconds'], 2)}
    @app.get('/api/ffbe/anim/' + SPRITE + '/{anim}.webp')
    def animation(anim: str, original: bool = False):
        # Party replacements still use the imported FFBE model. Their viewer
        # explicitly requests that model rather than the new vision scene.
        if original: return env['ffbe_anim_webp'](SPRITE, anim)
        return image(anim)
    @app.get('/api/ffbe/preview/' + SPRITE + '/{anim}')
    def preview(anim: str): return image(anim)
    @app.get('/api/ffbe/idle/' + SPRITE + '.webp')
    def idle(): return image('idle')
