"""Independent binary fixtures for the crystal's material-only LOD partition."""
import importlib.util
from collections import Counter
from pathlib import Path
import struct
import unittest

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location('crystal_mesh_tested', ROOT / 'assets/existing_visions/payload/_ffr_crystal_mesh.py')
mesh = importlib.util.module_from_spec(spec); spec.loader.exec_module(mesh)


def native_mesh_fixture(wide=False):
    vertices = [(x, y, 1233 + z) for z in (1200, 0, -1200) for x, y in ((-1, 0), (1, 0), (0, 1))]
    main = [(0, 1, 2), (3, 4, 5), (6, 7, 8), (0, 4, 5)]
    depth = [(t[1], t[2], t[0]) for t in reversed(main)]
    prefix = bytes.fromhex('0500010000000100000002000000') + b'\0' * 20 + struct.pack('<I', 3)
    blocks = []
    for _ in range(3):
        header = b'\x05\x08' + struct.pack('<I10I', 1, 0, 0, 4, 0, 8, 1, 1, 0, 1, 1)
        header += b'\0' * 60 + struct.pack('<3I', 0, 1, 0)
        data = b'\x05\x08' + struct.pack('<4I', 12, 9, 12, 9) + b''.join(struct.pack('<3f', *v) for v in vertices)
        data += b'\x05\x00' + struct.pack('<4I', 1, 9, 0, 0)
        data += struct.pack('<2I', 8, 9) + bytes(range(72))
        data += struct.pack('<2I', 4, 9) + bytes(range(36))
        data += b'\x05\x00' + struct.pack('<2I', 0, 0)
        gpu_size = 108 + 72 + 36
        fmt = '<3I' if wide else '<3H'
        for triangles in (main, [], depth, []):
            indices = b''.join(struct.pack(fmt, *t) for t in triangles)
            data += struct.pack('<3I', int(wide), 1, len(indices)) + indices + b'\0' * 4
            gpu_size += len(indices)
        blocks.append(header + data + b'\0' * 24 + struct.pack('<3I', gpu_size, 48 if wide else 24, 0))
    return prefix + b''.join(blocks) + b'opaque Nanite/SDF data and bulk references'


def decoded_lods(raw):
    """Test reader, independent of the production rewriter."""
    cursor = 38; output = []
    for _ in range(struct.unpack_from('<I', raw, 34)[0]):
        start = cursor
        n = struct.unpack_from('<I', raw, start + 2)[0]
        sections = [struct.unpack_from('<10I', raw, start + 6 + i * 40) for i in range(n)]
        header = raw[start + 6 + n * 40:start + 78 + n * 40]
        vertex_start = cursor = start + 80 + n * 40
        stride, count, size, items = struct.unpack_from('<4I', raw, cursor); cursor += 16
        vertices = list(struct.iter_unpack('<3f', raw[cursor:cursor + size * items])); cursor += size * items
        cursor += 18
        for _ in range(2):
            size, items = struct.unpack_from('<2I', raw, cursor); cursor += 8 + size * items
        cursor += 10
        vertex_bytes = raw[vertex_start:cursor]; indices = []; index_offsets = []
        for _ in range(4):
            index_offsets.append(cursor)
            wide, size, items = struct.unpack_from('<3I', raw, cursor); cursor += 12
            indices.append(list(struct.iter_unpack('<3I' if wide else '<3H', raw[cursor:cursor + items])))
            cursor += items + 4
        sampler = cursor; cursor += 12 * (n + 1)
        sizes = struct.unpack_from('<3I', raw, cursor); cursor += 12
        output.append(dict(start=start, sections=sections, header=header, vertices=vertices,
            vertex_bytes=vertex_bytes, indices=indices, index_offsets=index_offsets, sampler=sampler, sizes=sizes))
    return output, raw[cursor:]


class CrystalMeshPartitionTests(unittest.TestCase):
    def test_each_lod_preserves_geometry_winding_buffers_and_bulk_tail(self):
        for wide in (False, True):
            original = native_mesh_fixture(wide)
            result = mesh.split_tips(original, 233, 2233)
            old, old_tail = decoded_lods(original); new, new_tail = decoded_lods(result)
            self.assertEqual(old_tail, new_tail)
            for a, b in zip(old, new):
                self.assertEqual((a['header'], a['vertex_bytes'], a['sizes']), (b['header'], b['vertex_bytes'], b['sizes']))
                self.assertEqual(Counter(a['indices'][0]), Counter(b['indices'][0]))
                self.assertEqual(Counter(a['indices'][2]), Counter(b['indices'][2]))
                self.assertEqual(b['sections'][0][:3], (0, 0, 2))
                self.assertEqual(b['sections'][1][:3], (1, 6, 2))
                vertices = b['vertices']
                for tri, depth in zip(b['indices'][0], b['indices'][2]):
                    pos = tuple(vertices[i] for i in tri); other = tuple(vertices[i] for i in depth)
                    self.assertIn(other, (pos, pos[1:] + pos[:1], pos[2:] + pos[:2]))
                for slot, first, count, low, high, *flags in b['sections']:
                    triangles = b['indices'][0][first // 3:first // 3 + count]
                    self.assertEqual((low, high), (min(i for tri in triangles for i in tri), max(i for tri in triangles for i in tri)))
                    self.assertEqual(flags, list(a['sections'][0][5:]))
                    for tri in triangles:
                        z = [vertices[i][2] for i in tri]
                        self.assertEqual(slot == 1, max(z) < 233 or min(z) > 2233)

    def test_incompatible_buffers_and_layout_are_rejected(self):
        source = native_mesh_fixture(); lods, _ = decoded_lods(source)
        for offset, replacement in ((0, b'\0'), (34, struct.pack('<I', 2)),
                (lods[0]['start'] + 6 + 40 + 68, struct.pack('<I', 1)),
                (lods[0]['sampler'], struct.pack('<I', 1)),
                (lods[0]['index_offsets'][0], struct.pack('<I', 5))):
            bad = bytearray(source); bad[offset:offset + len(replacement)] = replacement
            with self.subTest(offset=offset), self.assertRaises(ValueError): mesh.split_tips(bytes(bad), 233, 2233)
        with self.assertRaises(ValueError): mesh.split_tips(source[:100], 233, 2233)
        with self.assertRaises(ValueError): mesh.split_tips(source, 10000, 20000)

    def test_depth_geometry_mismatch_is_rejected(self):
        source = bytearray(native_mesh_fixture()); lods, _ = decoded_lods(source)
        struct.pack_into('<3H', source, lods[0]['index_offsets'][2] + 12, 0, 2, 1)
        with self.assertRaisesRegex(ValueError, 'depth-only geometry'):
            mesh.split_tips(bytes(source), 233, 2233)


if __name__ == '__main__': unittest.main()
