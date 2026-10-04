#!/usr/bin/env python3
"""Export native landscape heights for cave grounding and the placement preview.

Pass decoded UE5.6 landscapes and their .ubulk files with --landscape JSON BULK.
Reads the checked, single-subsection, delta-coded mip0 layout. Original files
stay private. Heights are checked against each component's native local bounds.
"""
import argparse
import base64
import hashlib
import json
import math
from pathlib import Path
import struct
import zlib

from build_acquisition_map import plain


def fields(export):
    return {p['Name']: plain(p) for p in export.get('Data', [])}


def vector(value):
    return [float(value[k]) for k in ('X', 'Y', 'Z')]


def landscape(document, bulk):
    imports, exports = document['Imports'], document['Exports']
    actors = [e for e in exports if e['ClassIndex'] < 0 and imports[-e['ClassIndex'] - 1]['ObjectName'] == 'Landscape']
    result = []
    for actor in actors:
        a = fields(actor)
        root = fields(exports[a['RootComponent'] - 1])
        if 'RelativeRotation' in root or a['NumSubsections'] != 1 or a['SubsectionSizeQuads'] != 127:
            raise ValueError('Unsupported landscape transform/subsections.')
        origin, scale = vector(root['RelativeLocation']), vector(root['RelativeScale3D'])
        for index in a['LandscapeComponents']:
            c = fields(exports[index - 1])
            t = fields(exports[c['HeightmapTexture'] - 1])
            raw = base64.b64decode(exports[t['AssetUserData'][1] - 1]['Extras'], validate=True)
            if len(raw) < 52 or struct.unpack_from('<4i', raw, 32) != (8, 128, 128, 1):
                raise ValueError('Unsupported native heightmap mip0.')
            factory = fields(exports[t['AssetUserData'][1] - 1])
            if any(factory.get(k, 0) for k in ('BoundaryCountX', 'BoundaryCountY')):
                raise ValueError('Shared landscape heightmap boundaries are unsupported.')
            resource = document['DataResources'][struct.unpack_from('<i', raw, 48)[0]]
            size = (128 * 128 + (128 + 128) * 2 - 4) * 2
            if resource['LegacyBulkDataFlags'] != 66817 or resource['SerialSize'] != size or resource['RawSize'] != size:
                raise ValueError('Native heightmap bulk resource changed.')
            offset = resource['SerialOffset']
            payload = bulk[offset:offset + size]
            if offset < 0 or len(payload) != size:
                raise ValueError('Truncated native landscape heights.')
            # UE LandscapeTextureStorageProviderFactory: big-endian U16 deltas,
            # cumulative across rows, initial height 32768. Border normals follow.
            heights, current = [], 32768
            for delta in struct.unpack('>16384H', payload[:32768]):
                current = (current + delta) & 65535
                heights.append(current)
            box = next(iter(c['CachedLocalBox'].values()))
            actual = ((min(heights) - 32768) / 128, (max(heights) - 32768) / 128)
            if any(abs(v - float(box[k]['Z'])) > 1e-5 for v, k in zip(actual, ('Min', 'Max'))):
                raise ValueError('Decoded heights do not match native component bounds.')
            result.append({'x': origin[0] + c.get('SectionBaseX', 0) * scale[0],
                           'y': origin[1] + c.get('SectionBaseY', 0) * scale[1],
                           'z': origin[2], 'dx': scale[0], 'dy': scale[1], 'dz': scale[2],
                           'heights': base64.b64encode(zlib.compress(struct.pack('<16384H', *heights), 9)).decode()})
    if not result or any(not math.isfinite(v) or v <= 0 for p in result for v in (p['dx'], p['dy'], p['dz'])):
        raise ValueError('Missing or invalid native landscape.')
    return result


def build(pairs, output):
    patches, sources = [], []
    for source, bulk in pairs:
        patches += landscape(json.loads(source.read_text(encoding='utf-8-sig')), bulk.read_bytes())
        sources.append({'landscape': source.name, 'sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
                        'bulkSha256': hashlib.sha256(bulk.read_bytes()).hexdigest()})
    output.write_text(json.dumps({'schema': 1, 'size': 128, 'sources': sources, 'patches': patches}, separators=(',', ':')) + '\n', encoding='utf-8')
    print(f'Exported {len(patches)} checked native terrain patches ({output.stat().st_size} bytes).')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--landscape', nargs=2, action='append', required=True, type=Path)
    parser.add_argument('--output', type=Path, default=Path('assets/existing_visions/payload/cave_terrain.json'))
    args = parser.parse_args()
    build(args.landscape, args.output)
