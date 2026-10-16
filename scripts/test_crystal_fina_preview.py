"""The bundled native presentation must replace stale FFBE previews."""
import io
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'assets/existing_visions/payload'))
import _ffr_fina_preview as preview


class PreviewTests(unittest.TestCase):
    def test_all_three_animations_decode_and_match_their_declared_duration(self):
        manifest, images = preview.bundle()
        self.assertEqual(set(images), {'idle', 'atk', 'limitatk'})
        for name, data in images.items():
            with self.subTest(name=name):
                image = Image.open(io.BytesIO(data)); total = 0
                self.assertGreater(image.n_frames, 2)
                for frame in range(image.n_frames):
                    image.seek(frame); image.load(); total += image.info['duration']
                self.assertAlmostEqual(total, manifest['animations'][name]['seconds'] * 1000, delta=1)
        image = Image.open(io.BytesIO(images['limitatk'])); image.seek(0); image.load()
        first = image.convert('RGBA').getbbox()
        image.seek(image.n_frames - 1); image.load(); last = image.convert('RGBA').getbbox()
        self.assertGreater(first[3] - first[1], 250)  # The crystal is visible before the fall.
        self.assertLess(last[3] - last[1], 100)  # Grounded seated pose, without the casing.
        self.assertGreater(last[1], 240)

    def test_literal_fina_routes_bypass_old_files_and_leave_generic_routes_untouched(self):
        routes = {}
        class App:
            def get(self, path):
                def add(fn): routes[path] = fn; return fn
                return add
        class HTTPException(Exception):
            def __init__(self, code, detail): self.status_code = code; super().__init__(detail)
        def response(content, **kw): return SimpleNamespace(body=content, **kw)
        with tempfile.TemporaryDirectory() as root, patch.dict('sys.modules', {
            'fastapi': SimpleNamespace(HTTPException=HTTPException),
            'fastapi.responses': SimpleNamespace(Response=response),
        }):
            old = Path(root) / (preview.SPRITE + '_idle.webp'); old.write_bytes(b'old cached FFBE animation')
            preview.register(App(), {'ROOT': root, 'PREVIEWS': root, 'ffbe_anim_webp': lambda form, anim: ('original', form, anim)})
            generic = lambda: 'generic preview'
            routes['/api/ffbe/anim/{form}/{anim}.webp'] = generic
            result = routes['/api/ffbe/anim/' + preview.SPRITE + '/{anim}.webp']('idle')
            self.assertTrue(result.body.startswith(b'RIFF')); self.assertEqual(result.media_type, 'image/webp')
            self.assertEqual(result.headers['Cache-Control'], 'no-store')
            self.assertEqual(result.headers['X-Fina-Presentation'], preview.VERSION)
            self.assertEqual(routes['/api/ffbe/anim/' + preview.SPRITE + '/{anim}.webp']('atk', original=True), ('original', preview.SPRITE, 'atk'))
            self.assertEqual(old.read_bytes(), b'old cached FFBE animation')
            self.assertIs(routes['/api/ffbe/anim/{form}/{anim}.webp'], generic)
            self.assertEqual(routes['/api/ffbe/anims/' + preview.SPRITE]()['anims'], ['idle', 'atk', 'limitatk'])
            with self.assertRaises(HTTPException): routes['/api/ffbe/preview/' + preview.SPRITE + '/{anim}']('../other')


if __name__ == '__main__': unittest.main()
