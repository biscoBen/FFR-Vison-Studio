"""Native catalog coverage, entrance payload rejection and packaged image integrity."""
import base64
import copy
import hashlib
import json
from pathlib import Path
import struct
import unittest

from PIL import Image

from build_acquisition_locations import diffuse, mesh
import test_acquisition_map

ROOT = Path(__file__).resolve().parents[1]


class AcquisitionLocationsTests(unittest.TestCase):
    def test_every_native_shop_record_and_entrance_preview_is_bundled_once(self):
        root = ROOT / 'assets/acquisition_map'
        data = json.loads((root / 'locations.json').read_text())
        self.assertEqual(data['schema'], 1)
        self.assertEqual(len(data['vendors']), 125)
        self.assertEqual(len({v['id'] for v in data['vendors']}), 125)
        self.assertEqual(data['sources']['DT_ShopList']['rows'], 105)
        self.assertEqual(data['sources']['DT_VariousShopsList']['rows'], 20)
        for table, source in data['sources'].items():
            self.assertEqual(len([v for v in data['vendors'] if v['sourceTable'] == table]), source['rows'])
            self.assertEqual(len(source['sha256']), 64)
        ids = {v['nativeId'] for v in data['vendors'] if v['sourceTable'] == 'DT_ShopList'}
        for vendor in data['vendors']:
            self.assertEqual(vendor['id'], f"shop_{vendor['nativeId']}")
            if vendor['sourceTable'] == 'DT_VariousShopsList':
                self.assertTrue(set(vendor['inventories'].values()) <= ids)
        self.assertEqual(data['mitraShop'], 'shop_1')
        self.assertEqual({e['id'] for e in data['entrances']}, {'rock_cave', 'shrine', 'dwarven_cave', 'desert_sinkhole'})
        for entry in data['entrances']:
            self.assertTrue(entry['mesh'].startswith('/Game/Env/Wld/'))
            self.assertEqual(hashlib.sha256((root / entry['image']).read_bytes()).hexdigest(), entry['sha256'])
            with Image.open(root / entry['image']) as image:
                self.assertEqual(image.size, (384, 288))
                self.assertEqual(image.mode, 'RGBA')
            self.assertGreater(entry['vertices'], 200)
            self.assertGreater(entry['triangles'], 400)
        moving = next(v for v in data['vendors'] if v['id'] == 'shop_0')
        self.assertIsNone(moving['worldX'])
        self.assertIsNone(moving['worldY'])

    def fixture(self):
        # Minimal donor-style UE5.6 LOD0, one section, three vertices and a triangle.
        raw = bytearray(158)
        raw[:14] = bytes.fromhex('0500010000000100000002000000')
        struct.pack_into('<I', raw, 34, 1)
        raw[38:40] = b'\x05\x08'
        struct.pack_into('<I', raw, 40, 1)
        struct.pack_into('<5I', raw, 44, 0, 0, 1, 0, 2)
        raw += struct.pack('<4I', 12, 3, 12, 3)
        raw += struct.pack('<9f', 0, 0, 0, 1, 0, 0, 0, 1, 0)
        raw += b'\x05\x00' + struct.pack('<4I', 1, 3, 0, 0)
        raw += struct.pack('<2I', 8, 3) + bytes(24)
        raw += struct.pack('<2I', 4, 3) + bytes(12)
        raw += b'\x05\x00' + bytes(8)
        raw += struct.pack('<3I', 0, 1, 6) + struct.pack('<3H', 0, 1, 2)
        return {'Imports': [{'ObjectName': 'StaticMesh'}], 'Exports': [{
            'ClassIndex': -1, 'Extras': base64.b64encode(raw).decode()}]}

    def test_native_mesh_vertex_uv_and_triangle_relationships(self):
        vertices, uvs, triangles = mesh(self.fixture())
        self.assertEqual(vertices, [(0., 0., 0.), (1., 0., 0.), (0., 1., 0.)])
        self.assertEqual(uvs, [(0., 0.)] * 3)
        self.assertEqual(triangles, [((0, 1, 2), 0)])

    def test_truncated_incompatible_or_out_of_range_mesh_is_rejected(self):
        original = self.fixture()
        raw = bytearray(base64.b64decode(original['Exports'][0]['Extras']))
        for change in ['truncate', 'wrong_stride', 'bad_index', 'nan']:
            edited = bytearray(raw)
            if change == 'truncate':
                edited = edited[:-1]
            elif change == 'wrong_stride':
                struct.pack_into('<I', edited, 158, 16)
            elif change == 'bad_index':
                struct.pack_into('<H', edited, len(edited) - 2, 7)
            else:
                struct.pack_into('<f', edited, 174, float('nan'))
            document = copy.deepcopy(original)
            document['Exports'][0]['Extras'] = base64.b64encode(edited).decode()
            with self.subTest(change=change), self.assertRaises(ValueError):
                mesh(document)

    def test_inline_and_external_mip0_decode_identically_and_reject_wrong_bulk_size(self):
        inline = test_acquisition_map.AcquisitionMapTests().fixture()
        expected = diffuse(inline)
        raw = bytearray(base64.b64decode(inline['Exports'][0]['Extras']))
        payload = bytes(raw[79:95])
        external = copy.deepcopy(inline)
        external['DataResources'] = [{'SerialSize': 16, 'RawSize': 16, 'SerialOffset': 0, 'LegacyBulkDataFlags': 66817}]
        external['Exports'][0]['Extras'] = base64.b64encode(raw[:79] + raw[95:]).decode()
        actual = diffuse(external, payload)
        self.assertEqual(actual.tobytes(), expected.tobytes())
        with self.assertRaises(ValueError):
            diffuse(external, payload[:-1])
        external['DataResources'][0]['RawSize'] = 15
        with self.assertRaises(ValueError):
            diffuse(external, payload)


if __name__ == '__main__':
    unittest.main()
