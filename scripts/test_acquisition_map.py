import base64
import hashlib
import json
from pathlib import Path
import struct
import unittest

from PIL import Image

from build_acquisition_map import texture

ROOT = Path(__file__).resolve().parents[1]


class AcquisitionMapTests(unittest.TestCase):
    def test_bundled_shipping_images_match_their_native_catalog_and_checksums(self):
        root = ROOT / 'assets/acquisition_map'
        manifest = json.loads((root / 'manifest.json').read_text())
        self.assertEqual(manifest['wholeSize'], [47400, 49800])
        self.assertEqual(manifest['worldOffset'], [0, -400])
        self.assertEqual(manifest['projection'], ['worldY', '-worldX'])
        self.assertEqual([t['id'] for t in manifest['tiles']], list(range(1, 10)))
        self.assertEqual(set(manifest['files']), {f'Wld_{i}.png' for i in range(1, 10)} | {'T_Wld_ocean.png'})
        for name, entry in manifest['files'].items():
            with self.subTest(name=name):
                data = (root / name).read_bytes()
                self.assertEqual(hashlib.sha256(data).hexdigest(), entry['sha256'])
                self.assertTrue(entry['source'].startswith('/Game/UI/Textures/MapCapture/Wld/'))
                with Image.open(root / name) as image:
                    self.assertEqual(list(image.size), entry['size'])
                    self.assertEqual(image.mode, 'RGBA')
                    self.assertIsNotNone(image.getbbox())
        first = manifest['tiles'][0]
        self.assertEqual(first['center'], [20200, -15100])
        self.assertEqual(first['size'], [9000, 9000])
        self.assertEqual(first['regionSize'], [7000, 9000])
        for tile in manifest['tiles']:
            self.assertEqual(tile['size'], [max(tile['regionSize'])] * 2)

    def fixture(self):
        # Known BC7 block from the native tutorial texture: native tutorial image.
        raw = bytearray(79 + 16 + 24)
        raw[:8] = b'\x05\x00\x05\x00\x01\x00\x00\x00'
        struct.pack_into('<4I', raw, 44, 4, 4, 1, 7)
        raw[60:67] = b'PF_BC7\0'
        struct.pack_into('<3I', raw, 67, 0, 1, 0)
        raw[79:95] = bytes.fromhex('f0071cf07f22048240fb0da6c4c82aba')
        struct.pack_into('<3I', raw, 95, 4, 4, 1)
        return {'Imports': [{'ObjectName': 'Texture2D'}],
                'Exports': [{'ClassIndex': -1, 'Extras': base64.b64encode(raw).decode()}]}

    def test_native_bc7_pixel_decode(self):
        image = texture(self.fixture())
        self.assertEqual(image.size, (4, 4))
        self.assertEqual(image.getpixel((0, 1)), (41, 41, 27, 255))

    def test_truncated_or_incompatible_texture_is_rejected(self):
        for offset, value in [(0, 0), (71, 2), (44, 255), (60, ord('X'))]:
            with self.subTest(offset=offset):
                document = self.fixture()
                raw = bytearray(base64.b64decode(document['Exports'][0]['Extras']))
                raw[offset] = value
                document['Exports'][0]['Extras'] = base64.b64encode(raw).decode()
                with self.assertRaises(ValueError):
                    texture(document)
        document = self.fixture()
        raw = base64.b64decode(document['Exports'][0]['Extras'])[:-1]
        document['Exports'][0]['Extras'] = base64.b64encode(raw).decode()
        with self.assertRaises(ValueError):
            texture(document)


if __name__ == '__main__':
    unittest.main()
