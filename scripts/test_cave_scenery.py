"""Validate packaged native scenery against its heights and image provenance."""
import hashlib
import io
import json
from pathlib import Path
import unittest
import zipfile
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]


class CaveSceneryTests(unittest.TestCase):
    def test_archive_paint_foliage_and_visible_geometry_are_complete_and_checksummed(self):
        root = ROOT / 'assets/acquisition_map'; raw = (root/'scenery.zip').read_bytes()
        manifest = json.loads((root/'scenery.json').read_text(encoding='utf-8'))
        self.assertEqual(hashlib.sha256(raw).hexdigest(), manifest['sha256'])
        terrain = json.loads((ROOT/'assets/existing_visions/payload/cave_terrain.json').read_bytes())['patches']
        with zipfile.ZipFile(io.BytesIO(raw)) as z:
            data = z.read('scene.json'); scene = json.loads(data)
            self.assertEqual(hashlib.sha256(data).hexdigest(), manifest['sceneSha256'])
            self.assertEqual(set(z.namelist()), set(scene['files']) | {'scene.json'})
            self.assertEqual(len(scene['terrain']), len(terrain))
            for t in scene['terrain']:
                self.assertTrue(any(abs(t['x']-p['x']) < .01 and abs(t['y']-p['y']) < .01 for p in terrain))
                with Image.open(io.BytesIO(z.read(t['image']))) as image:
                    self.assertEqual(image.size, (128, 128))
            for name, digest in scene['files'].items(): self.assertEqual(hashlib.sha256(z.read(name)).hexdigest(), digest)
            self.assertGreater(len(scene['foliage']), 2500)
            self.assertTrue(any(abs(f['at'][0]-16964.99)<800 and abs(f['at'][1]-22678.74)<800 for f in scene['foliage']))
            for f in scene['foliage']:
                self.assertIn(f['image'], scene['files']); self.assertGreater(f['width'], 0); self.assertGreater(f['height'], 0)
            self.assertTrue(any('earthtemple001' in p['name'] for p in scene['props']))
            self.assertFalse(any('forest_col' in p['name'] or 'foam' in p['name'] for p in scene['props']))
            for prop in scene['props']:
                for ids, rgb in prop['faces']:
                    self.assertTrue(all(0<=i<len(prop['vertices']) for i in ids)); self.assertTrue(all(0<=c<=255 for c in rgb))
