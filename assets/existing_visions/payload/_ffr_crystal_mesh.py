"""Read-only native geometry codec and retained rejected tip-material experiment.

The live test produced dark tips. Runtime caves use the unmodified native mesh;
builds read its original LOD0 for view-depth calculation, never applying the partition.

Layout checked against FStaticMeshLODResources/FStaticMeshSection and
FRawStaticIndexBuffer in CUE4Parse, and the demo's three native LODs. Reject
streamed LODs, ray tracing, populated samplers or any unrecognized layout.
"""
import math
import struct
from collections import defaultdict


class Reader:
    def __init__(self, raw): self.raw, self.pos = raw, 0

    def take(self, count):
        end = self.pos + count
        if count < 0 or end > len(self.raw):
            raise ValueError('Truncated Sanctum crystal mesh.')
        result = self.raw[self.pos:end]; self.pos = end
        return result

    def ints(self, count): return struct.unpack('<' + 'I' * count, self.take(count * 4))

    def expect(self, data):
        if self.take(len(data)) != data:
            raise ValueError('Unsupported Sanctum crystal mesh layout.')


def lod0_geometry(raw):
    """Read original LOD0 triangles without changing any mesh/bulk bytes."""
    reader = Reader(raw)
    reader.expect(bytes.fromhex('0500010000000100000002000000')); reader.take(20)
    if reader.ints(1) != (3,): raise ValueError('The native crystal LOD count changed.')
    reader.expect(b'\x05\x08')
    if reader.ints(1) != (1,): raise ValueError('The native crystal material sections changed.')
    section = reader.take(40); material, first, triangles, low, high = struct.unpack_from('<5I', section)
    if material or first or not 0 < triangles <= 20000: raise ValueError('Invalid crystal section.')
    header = reader.take(72)
    if struct.unpack_from('<3I', header, 60) != (0, 1, 0): raise ValueError('Expected an inline crystal LOD.')
    reader.expect(b'\x05\x08'); stride, count, size, items = reader.ints(4)
    if stride != 12 or size != 12 or count != items or not 0 < count <= 20000: raise ValueError('Invalid crystal positions.')
    positions = list(struct.iter_unpack('<3f', reader.take(count * 12)))
    if not 0 <= low <= high < count or not all(math.isfinite(c) for p in positions for c in p):
        raise ValueError('Invalid crystal bounds.')
    reader.expect(b'\x05\x00'); coords, items, full_uv, high_tangent = reader.ints(4)
    if items != count or not 0 < coords <= 4 or full_uv not in (0, 1) or high_tangent not in (0, 1):
        raise ValueError('Invalid crystal vertex metadata.')
    for expected in [(16 if high_tangent else 8, count), (8 if full_uv else 4, count * coords)]:
        size, items = reader.ints(2)
        if (size, items) != expected: raise ValueError('Invalid crystal tangent/UV buffer.')
        reader.take(size * items)
    reader.expect(b'\x05\x00'); stride, colors = reader.ints(2)
    if colors:
        size, items = reader.ints(2)
        if (stride, colors, size, items) != (4, count, 4, count): raise ValueError('Invalid crystal color buffer.')
        reader.take(size * items)
    elif stride: raise ValueError('Invalid empty crystal color buffer.')
    wide, size, items = reader.ints(3)
    if wide not in (0, 1) or size != 1 or items != triangles * (12 if wide else 6): raise ValueError('Invalid crystal indices.')
    indices = list(struct.iter_unpack('<3I' if wide else '<3H', reader.take(items)))
    if reader.ints(1) != (0,) or any(v >= count for tri in indices for v in tri): raise ValueError('Invalid crystal triangles.')
    return positions, indices


def split_tips(raw, lower, upper):
    """Material 1 on wholly outlying triangles; material 0 on the central band.

    Preserve winding, all vertices/tangents/UVs, depth-buffer correspondence,
    bounds, physics and external bulk data. Match depth-only triangles by their
    oriented geometry before partitioning. Empty samplers gain a section entry.
    """
    if not math.isfinite(lower) or not math.isfinite(upper) or lower >= upper:
        raise ValueError('Invalid crystal tip band.')
    reader = Reader(raw)
    reader.expect(bytes.fromhex('0500010000000100000002000000'))
    reader.take(20)  # Native lighting GUID and zero mobile MinLOD.
    count, = reader.ints(1)
    if count != 3: raise ValueError('The Sanctum crystal LOD count changed.')
    parts = [raw[:reader.pos]]
    for _ in range(count): parts.append(_split_lod(reader, lower, upper))
    parts.append(raw[reader.pos:])  # Nanite/SDF/bounds and bulk references stay intact.
    return b''.join(parts)


def _split_lod(reader, lower, upper):
    reader.expect(b'\x05\x08')  # Cooked editor/server stripped; ray tracing stripped.
    count, = reader.ints(1)
    if count != 1: raise ValueError('The Sanctum crystal material sections changed.')
    section = reader.take(40)
    material, first, triangles, low, high = struct.unpack_from('<5I', section)
    if material or first or not 0 < triangles <= 20000:
        raise ValueError('Invalid native crystal section.')
    header = reader.take(72)  # LWC bounds, max deviation, cooked/inline/RT booleans.
    if struct.unpack_from('<3I', header, 60) != (0, 1, 0):
        raise ValueError('Crystal LODs must be inline with ray tracing disabled.')
    start = reader.pos
    reader.expect(b'\x05\x08')
    stride, vertices, size, items = reader.ints(4)
    if stride != 12 or size != 12 or vertices != items or not 0 < vertices <= 20000:
        raise ValueError('Invalid crystal position buffer.')
    positions = list(struct.iter_unpack('<3f', reader.take(items * size)))
    if not all(math.isfinite(a) for v in positions for a in v) or not 0 <= low <= high < vertices:
        raise ValueError('Invalid crystal vertex bounds.')
    gpu_size = vertices * 12
    reader.expect(b'\x05\x00')
    coords, items, full_uv, high_tangent = reader.ints(4)
    if items != vertices or not 0 < coords <= 4 or full_uv not in (0, 1) or high_tangent not in (0, 1):
        raise ValueError('Invalid crystal vertex metadata.')
    for expected_size, expected_items in ((16 if high_tangent else 8, vertices),
                                           (8 if full_uv else 4, vertices * coords)):
        size, items = reader.ints(2)
        if (size, items) != (expected_size, expected_items):
            raise ValueError('Invalid crystal tangent/UV buffer.')
        reader.take(size * items); gpu_size += size * items
    reader.expect(b'\x05\x00')
    stride, colors = reader.ints(2)
    if colors:
        size, items = reader.ints(2)
        if (stride, colors, size, items) != (4, vertices, 4, vertices):
            raise ValueError('Invalid crystal color buffer.')
        reader.take(size * items); gpu_size += size * items
    elif stride: raise ValueError('Invalid empty crystal color buffer.')
    vertex_data = reader.raw[start:reader.pos]
    buffers = []
    for number in range(4):  # Main, reversed, depth-only, reversed depth-only.
        wide, size, items = reader.ints(3)
        if wide not in (0, 1) or size != 1 or items % (12 if wide else 6):
            raise ValueError('Invalid crystal index buffer.')
        data = reader.take(items); expand, = reader.ints(1)
        if expand or (number in (1, 3) and items):
            raise ValueError('Unsupported reversed/expanded crystal index buffer.')
        fmt = '<3I' if wide else '<3H'
        indices = list(struct.iter_unpack(fmt, data))
        if number in (0, 2) and (len(indices) != triangles or any(i >= vertices for t in indices for i in t)):
            raise ValueError('Crystal index buffers do not match their section.')
        buffers.append((wide, fmt, indices)); gpu_size += items
    # The native asset does not enable uniform-area sampling. Do not silently
    # retain a populated per-triangle sampler after reordering its triangles.
    reader.expect(b'\0' * 24)
    sizes = reader.take(12)
    if struct.unpack('<3I', sizes) != (gpu_size, triangles * (12 if buffers[2][0] else 6), 0):
        raise ValueError('Crystal GPU buffer sizes changed.')
    main, depth = buffers[0][2], buffers[2][2]
    def geometry(tri):
        vertices = tuple(positions[i] for i in tri)
        return min(vertices, vertices[1:] + vertices[:1], vertices[2:] + vertices[:2])
    matches = defaultdict(list)
    for tri in depth: matches[geometry(tri)].append(tri)
    aligned = []
    for tri in main:
        candidates = matches[geometry(tri)]
        if not candidates: raise ValueError('Crystal depth-only geometry or winding changed.')
        aligned.append(candidates.pop())
    buffers[2] = (buffers[2][0], buffers[2][1], aligned)
    groups = [[], []]
    for i, tri in enumerate(main):
        z = [positions[v][2] for v in tri]
        groups[int(max(z) < lower or min(z) > upper)].append(i)
    if not all(groups): raise ValueError('Crystal tip selection left an empty section.')
    order = groups[0] + groups[1]
    sections = []
    for material, group in enumerate(groups):
        ids = [v for i in group for v in main[i]]
        sections.append(struct.pack('<5I', material, 0 if material == 0 else len(groups[0]) * 3,
                                    len(group), min(ids), max(ids)) + section[20:])
    output = [b'\x05\x08', struct.pack('<I', 2), *sections, header, vertex_data]
    for wide, fmt, indices in buffers:
        data = b''.join(struct.pack(fmt, *indices[i]) for i in order) if indices else b''
        output += [struct.pack('<3I', wide, 1, len(data)), data, struct.pack('<I', 0)]
    # SerializedBuffersSize counts GPU bytes, not headers or empty samplers.
    output += [b'\0' * 36, sizes]
    return b''.join(output)
