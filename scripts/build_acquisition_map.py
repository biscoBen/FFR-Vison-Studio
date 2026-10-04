#!/usr/bin/env python3
"""Convert decoded native world-map captures into Studio's offline preview assets.

Run ffr-dt tojson on the Shipping UI/Textures/MapCapture/Wld textures and
Datatable/Map/Land/DA_MapLandCapture first. Pass their JSON directories with
--decoded. Debug captures are deliberately excluded; original game files stay
outside this repository. The known cooked single-mip texture layout is checked
before conversion. This does not change the game's maps or acquisition rules.
"""
import argparse
import base64
import hashlib
import io
import json
import re
from pathlib import Path
import struct

from PIL import Image


def plain(prop):
    kind = prop.get('$type', '')
    value = prop.get('Value')
    if 'MapPropertyData' in kind:
        return {str(plain(k)): plain(v) for k, v in value}
    if 'StructPropertyData' in kind:
        if prop.get('StructType') in ('Vector2D', 'Vector'):
            return plain(value[0]) if len(value) == 1 else [plain(child) for child in value]
        return {child['Name']: plain(child) for child in value}
    if 'ArrayPropertyData' in kind:
        return [plain(child) for child in value]
    return value


def texture(document):
    exports = document['Exports']
    if len(exports) != 1:
        raise ValueError('Expected one cooked Texture2D export.')
    export = exports[0]
    if document['Imports'][-export['ClassIndex'] - 1]['ObjectName'] != 'Texture2D':
        raise ValueError('The map capture is not a Texture2D.')
    raw = base64.b64decode(export['Extras'], validate=True)
    # Known UE5.6 legacy layout: strip/cooked flags, platform format, one mip.
    if raw[:8] != b'\x05\x00\x05\x00\x01\x00\x00\x00':
        raise ValueError('Unsupported cooked texture header.')
    width, height, depth, count = struct.unpack_from('<4I', raw, 44)
    if not (0 < width <= 4096 and 0 < height <= 4096 and depth == 1 and count < 24):
        raise ValueError('Invalid map texture dimensions or pixel format.')
    fmt = raw[60:60 + count - 1].decode('ascii')
    end = 60 + count
    if raw[end - 1] != 0 or struct.unpack_from('<3I', raw, end) != (0, 1, 0):
        raise ValueError('Expected a single inline mip with no skipped mips.')
    formats = {'PF_BC7': (16, 'DX10'), 'PF_DXT5': (16, 'DXT5'), 'PF_DXT1': (8, 'DXT1')}
    if fmt not in formats:
        raise ValueError(f'Unsupported map pixel format {fmt}.')
    block, fourcc = formats[fmt]
    length = ((width + 3) // 4) * ((height + 3) // 4) * block
    start = end + 12
    if len(raw) != start + length + 24 or struct.unpack_from('<3I', raw, start + length) != (width, height, 1):
        raise ValueError('Cooked mip length or dimensions do not match its header.')
    header = (b'DDS ' + struct.pack('<7I', 124, 0x81007, height, width, length, 0, 1) + bytes(44)
              + struct.pack('<8I', 32, 4, int.from_bytes(fourcc.encode(), 'little'), 0, 0, 0, 0, 0)
              + struct.pack('<5I', 0x1000, 0, 0, 0, 0))
    if fmt == 'PF_BC7':
        header += struct.pack('<5I', 98, 3, 0, 1, 0)
    return Image.open(io.BytesIO(header + raw[start:start + length])).convert('RGBA')


def build(decoded, output):
    output.mkdir(parents=True, exist_ok=True)
    native = json.loads((decoded / 'DA_MapLandCapture/data.json').read_text())
    fields = {p['Name']: plain(p) for p in native['Exports'][0]['Data']}
    world = fields['MapLandCaptureDataMap']['1000']
    vector = lambda v: [float(v['X']), float(v['Y'])]
    manifest = {'schema': 1, 'mapId': 1000, 'wholeSize': vector(world['LandWholeSize']),
                'worldOffset': vector(world['LandWorldOffset']),
                'projection': ['worldY', '-worldX'], 'tiles': [], 'files': {}}
    # Native baseline world, before the story-dependent replacement captures.
    for index in range(1, 10):
        entry = world['AreaLandCaptureDataMap'][str(index)]
        capture = entry['LandTextureMap']['eLandTexturePackageType::Shipping']['AssetPath']['PackageName']
        name = f'Wld_{index}'
        if capture != f'/Game/UI/Textures/MapCapture/Wld/{name}':
            raise ValueError('The native Shipping map capture path changed.')
        # BoxSize bounds the region, not the square capture image. The native
        # camera height is half the longest side (90-degree capture). Stretching
        # the image to BoxSize moves landmarks and coastal pins off the land.
        side = float(entry['CaptureCameraHeight']) * 2
        if abs(side - max(vector(entry['BoxSize']))) > .001:
            raise ValueError('The native square capture camera changed.')
        manifest['tiles'].append({'id': index, 'center': vector(entry['WorldLocation']),
                                  'size': [side, side], 'regionSize': vector(entry['BoxSize']),
                                  'image': f'{name}.png'})
    for name in [f'Wld_{i}' for i in range(1, 10)] + ['T_Wld_ocean']:
        data = json.loads((decoded / name / 'data.json').read_text())
        # Numbered Unreal FNames store their base separately from the suffix.
        package_base = re.sub(r'_\d+$', '', name)
        if (f'/Game/UI/Textures/MapCapture/Wld/{package_base}' not in data['NameMap']
                or data['Exports'][0]['ObjectName'] != name):
            raise ValueError('A Debug or unexpected map capture was supplied.')
        image = texture(data)
        dest = output / f'{name}.png'
        image.save(dest, optimize=True)
        manifest['files'][dest.name] = {'sha256': hashlib.sha256(dest.read_bytes()).hexdigest(),
                                      'size': list(image.size), 'source': f'/Game/UI/Textures/MapCapture/Wld/{name}'}
    (output / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print(f"Built {len(manifest['files'])} native map images in {output}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--decoded', required=True, type=Path)
    parser.add_argument('--output', type=Path, default=Path('assets/acquisition_map'))
    args = parser.parse_args()
    build(args.decoded, args.output)
