#!/usr/bin/env python3
"""Build the offline vendor catalog and entrance previews from decoded native assets.

Inputs are ffr-dt JSON, kept outside the repository. Previews use native LOD0
geometry and diffuse colors with simplified lighting, not a game render. The
known cooked UE5.6 inline mesh layout is checked before reading its buffers.
"""
import argparse
import base64
import copy
import hashlib
import json
import math
from pathlib import Path
import re
import struct

from PIL import Image, ImageDraw

from build_acquisition_map import plain, texture

ENTRANCES = [
    ('rock_cave', 'Rocky cave', 'SM_Env_Wld_00Com_dungeon001', 'T_Env_Wld_00Com_dungeon001_D', (134, 133, 111)),
    ('shrine', 'Shrine', 'SM_Env_Wld_00Com_shrine001', 'T_Env_Wld_00Com_shrine001_D', (126, 131, 113)),
    ('dwarven_cave', 'Dwarven cave', 'SM_Env_Wld_04Dir_dwarvecave001', 'T_Env_Wld_00Com_darwall001_D', (113, 100, 87)),
    ('desert_sinkhole', 'Desert sinkhole', 'SM_Env_Wld_02Lan_sandhole001', None, (181, 150, 111)),
]

# Friendly translations of native inventory row names; original labels and IDs
# remain in the catalog. These are not claimed to be localized NPC names.
WORDS = {
    'グランシェルト炎上': 'Grandshelt (burning)', '土の神殿入り口': 'Earth Shrine entrance',
    'グランシェルト': 'Grandshelt', 'ミトラの町': 'Mitra', 'ミトラ': 'Mitra',
    'コルの村': 'Kol', 'ナシャトの街': 'Nashat', 'ナシャトの町': 'Nashat', 'グランポート': 'Granport',
    'ディルマギア工業都市': 'Dilmagia', 'ディルマギア': 'Dilmagia',
    'ドワーフの鍛冶場': 'Dwarven Forge', 'ドワーフ工房': 'Dwarven Forge',
    'ゾルダードクリア前': 'Zoldaad (before completion)', 'ゾルダードクリア後': 'Zoldaad (after completion)',
    'ゾルダードスラム': 'Zoldaad slums', 'ゾルダード': 'Zoldaad', 'オルデリオン': 'Olderion',
    'アムールの町': 'Amore', 'モズール駅': 'Mozoor Station', '帝都前駅': 'Imperial City Station',
    '反乱軍アジト': 'Rebel hideout', 'ミシディア': 'Mysidia', 'スニウ村': 'Sianu',
    'ガベラダ': 'Gaberada', 'ダグル': 'Duggle', 'シアンの町': 'Sian', 'コロシアムショップ': 'Colosseum',
    '至聖殿': 'Sacred Temple', 'チョコボ餌店': 'Chocobo feed', '飛空艇': 'Airship',
    'アクセサリー': 'Accessories', '防具アクセ': 'Armor & accessories', '武具屋': 'Equipment vendor',
    '武具': 'Equipment', '武器防具アクセ': 'Weapons, armor & accessories', 'ショップ': 'Shop',
    '道具': 'Items', '武器': 'Weapons', '防具': 'Armor', 'アクセ': 'Accessories',
    '露店': 'Stall', '万屋': 'General store', '部下': 'Subordinate', '没': '(unused)',
}


def label(source):
    text = source
    for jp in sorted(WORDS, key=len, reverse=True):
        text = text.replace(jp, ' ' + WORDS[jp] + ' ')
    text = re.sub(r'(\d+)章', r' (chapter \1) ', text)
    text = text.replace('クリア前', 'before completion')
    text = re.sub(r'[_\u3000\s]+', ' ', text).strip()
    return text


def rows(path):
    document = json.loads(path.read_text(encoding='utf-8-sig'))
    export = next(e for e in document['Exports'] if 'DataTableExport' in e['$type'])
    return {r['Name']: plain(r) for r in export['Table']['Data']}


def mesh(document):
    try:
        return _mesh(document)
    except (IndexError, KeyError, StopIteration, struct.error) as error:
        raise ValueError('Truncated or incompatible entrance mesh.') from error


def _mesh(document):
    export = next(e for e in document['Exports'] if e['ClassIndex'] < 0 and
                  document['Imports'][-e['ClassIndex'] - 1]['ObjectName'] == 'StaticMesh')
    raw = base64.b64decode(export['Extras'], validate=True)
    if raw[:14] != bytes.fromhex('0500010000000100000002000000') or raw[38:40] != b'\x05\x08':
        raise ValueError('Unsupported cooked entrance mesh layout.')
    lods, sections = struct.unpack_from('<I', raw, 34)[0], struct.unpack_from('<I', raw, 40)[0]
    if not 0 < lods <= 8 or not 0 < sections <= 16:
        raise ValueError('Invalid entrance LOD or section count.')
    section_data = [struct.unpack_from('<5I', raw, 44 + i * 40) for i in range(sections)]
    # UE5.6 LOD0 sections, deviation, LWC bounds, cooked/inlined/raytracing flags,
    # followed by FPositionVertexBuffer. This reader supports these donors only.
    p = 118 + 40 * sections
    stride, count, item_size, item_count = struct.unpack_from('<4I', raw, p)
    p += 16
    if stride != 12 or item_size != 12 or count != item_count or not 0 < count <= 20000:
        raise ValueError('Invalid entrance position buffer.')
    vertices = [struct.unpack_from('<3f', raw, p + i * 12) for i in range(count)]
    if not all(math.isfinite(v) and abs(v) < 100000 for point in vertices for v in point):
        raise ValueError('Invalid entrance vertex coordinates.')
    p += count * 12
    if raw[p:p + 2] != b'\x05\x00':
        raise ValueError('Unsupported entrance UV buffer.')
    p += 2
    coords, n, full, high = struct.unpack_from('<4I', raw, p)
    p += 16
    if n != count or not 0 < coords <= 4 or full not in (0, 1) or high not in (0, 1):
        raise ValueError('Invalid entrance vertex metadata.')
    size, n = struct.unpack_from('<2I', raw, p)
    p += 8
    if n != count or size != (16 if high else 8):
        raise ValueError('Invalid entrance tangent buffer.')
    p += size * n
    size, n = struct.unpack_from('<2I', raw, p)
    p += 8
    if n != count * coords or size != (8 if full else 4):
        raise ValueError('Invalid entrance texture coordinates.')
    uvs = [struct.unpack_from('<2f' if full else '<2e', raw, p + i * coords * size) for i in range(count)]
    p += size * n
    if raw[p:p + 10] != b'\x05\x00' + bytes(8):
        raise ValueError('Unsupported entrance vertex colors.')
    p += 10
    wide, size, n = struct.unpack_from('<3I', raw, p)
    p += 12
    if wide not in (0, 1) or size != 1 or n % (12 if wide else 6):
        raise ValueError('Invalid entrance triangle buffer.')
    indices = struct.unpack_from('<' + ('I' if wide else 'H') * (n // (4 if wide else 2)), raw, p)
    if any(i >= count for i in indices) or sum(s[2] * 3 for s in section_data) != len(indices):
        raise ValueError('Entrance triangles do not match their vertices/sections.')
    triangles = []
    cursor = 0
    for material, first, n, low, high in section_data:
        if first != cursor or not 0 <= low <= high < count:
            raise ValueError('Invalid entrance section range.')
        for i in range(first, first + n * 3, 3):
            triangles.append((indices[i:i + 3], material))
        cursor += n * 3
    return vertices, uvs, triangles


def diffuse(document, bulk=None):
    document = copy.deepcopy(document)
    export = document['Exports'][0]
    raw = bytearray(base64.b64decode(export['Extras'], validate=True))
    width, height, depth, count = struct.unpack_from('<4I', raw, 44)
    fmt = raw[60:60 + count - 1].decode('ascii')
    block = {'PF_DXT1': 8, 'PF_DXT5': 16, 'PF_BC7': 16}[fmt]
    end = 60 + count
    length = ((width + 3) // 4) * ((height + 3) // 4) * block
    # Inline payloads and explicit native .ubulk resources are both supported.
    # The resource's offset, raw/serialized sizes and mip dimensions must agree.
    if document.get('DataResources') and document['DataResources'][0]['LegacyBulkDataFlags'] == 66817:
        index = struct.unpack_from('<I', raw, end + 8)[0]
        resource = document['DataResources'][index]
        if (bulk is None or depth != 1 or resource['SerialSize'] != length or resource['RawSize'] != length
                or struct.unpack_from('<3I', raw, end + 12) != (width, height, 1)):
            raise ValueError('The entrance texture bulk resource does not match mip0.')
        offset = resource['SerialOffset']
        payload = bulk[offset:offset + length]
        if offset < 0 or len(payload) != length:
            raise ValueError('Truncated entrance texture bulk resource.')
        raw = raw[:end + 12] + payload + struct.pack('<3I', width, height, 1) + bytes(12)
    elif depth != 1 or struct.unpack_from('<3I', raw, end + 12 + length) != (width, height, 1):
        raise ValueError('The entrance diffuse texture has no supported inline mip0.')
    struct.pack_into('<I', raw, end + 4, 1)
    export['Extras'] = base64.b64encode(raw[:end + 12 + length + 24]).decode()
    return texture(document)


def preview(vertices, uvs, triangles, image, color, yaw=0):
    angle = math.radians(yaw)
    transformed = [(x * math.cos(angle) - y * math.sin(angle), x * math.sin(angle) + y * math.cos(angle), z)
                   for x, y, z in vertices]
    points = [(x, -z * .9 - y * .43, -y * .9 + z * .43) for x, y, z in transformed]
    bounds = [(min(p[i] for p in points), max(p[i] for p in points)) for i in range(2)]
    scale = min(340 / (bounds[0][1] - bounds[0][0]), 230 / (bounds[1][1] - bounds[1][0]))
    center = [(a + b) / 2 for a, b in bounds]
    out = Image.new('RGBA', (384, 288), (36, 43, 49, 255))
    draw = ImageDraw.Draw(out)
    for ids, material in sorted(triangles, key=lambda t: sum(points[i][2] for i in t[0])):
        a, b, c = [transformed[i] for i in ids]
        ab, ac = [b[i] - a[i] for i in range(3)], [c[i] - a[i] for i in range(3)]
        normal = (ab[1] * ac[2] - ab[2] * ac[1], ab[2] * ac[0] - ab[0] * ac[2], ab[0] * ac[1] - ab[1] * ac[0])
        length = math.sqrt(sum(n * n for n in normal))
        if length < 1e-8:
            continue
        light = .5 + .5 * abs((normal[0] * -.4 + normal[1] * -.5 + normal[2] * .75) / length)
        rgb = color
        if image:
            u, v = [sum(uvs[i][axis] for i in ids) / 3 for axis in range(2)]
            rgb = image.getpixel((int(u % 1 * image.width), int(v % 1 * image.height)))[:3]
        polygon = [(192 + (points[i][0] - center[0]) * scale, 144 + (points[i][1] - center[1]) * scale) for i in ids]
        draw.polygon(polygon, fill=tuple(min(255, round(v * light)) for v in rgb) + (255,))
    return out


def build(decoded, output):
    shops = rows(decoded / 'DT_ShopList.json')
    combined = rows(decoded / 'DT_VariousShopsList.json')
    native_landmarks = json.loads((decoded / 'DA_MapLandmark.json').read_text(encoding='utf-8-sig'))
    landmarks = plain(native_landmarks['Exports'][0]['Data'][0])
    positions = {v['mapId']: p['Location'] for p in landmarks for v in p['landmarkDataList']}
    # Supported mappings come from native map rows, rather than assuming future
    # town IDs follow a numeric pattern. Moving airship shops have no fixed pin.
    city_ids = {'ミトラ': 2000, '土の神殿': 3001, 'グランシェルト': 2010,
                'コルの村': 2020, 'グランポート': 2030, 'ナシャト': 2040}
    vendors = []
    for source_table, values, id_field in [('DT_ShopList', shops, 'ShopID'), ('DT_VariousShopsList', combined, 'ID')]:
        for row, value in values.items():
            native_id = value[id_field]
            if type(native_id) is not int or native_id < 0:
                raise ValueError('Invalid native vendor ID.')
            location_id = next((v for prefix, v in city_ids.items() if row.startswith(prefix)), None)
            pos = positions.get(location_id)
            entry = {'id': f'shop_{native_id}', 'name': label(row), 'nativeId': native_id,
                     'sourceTable': source_table, 'sourceRow': row,
                     'worldX': pos['X'] if pos else None, 'worldY': pos['Y'] if pos else None,
                     'mapId': location_id}
            if source_table == 'DT_VariousShopsList':
                entry['inventories'] = {k: v for k, v in value.items() if k.endswith('ShopID') and v >= 0}
            vendors.append(entry)
    if len({v['id'] for v in vendors}) != len(vendors):
        raise ValueError('Native vendor identities collide.')
    catalog = {'schema': 1, 'mitraShop': 'shop_1', 'vendors': sorted(vendors, key=lambda v: (v['name'], v['nativeId'])),
               'sources': {name: {'sha256': hashlib.sha256((decoded / (name + '.json')).read_bytes()).hexdigest(),
                                 'rows': len(values)} for name, values in [('DT_ShopList', shops), ('DT_VariousShopsList', combined)]},
               'entrances': []}
    output.mkdir(parents=True, exist_ok=True)
    for id, name, asset, texture_name, color in ENTRANCES:
        source = decoded / (asset + '.json')
        document = json.loads(source.read_text(encoding='utf-8-sig'))
        vertices, uvs, triangles = mesh(document)
        bulk_path = decoded / (str(texture_name) + '.ubulk')
        tex = diffuse(json.loads((decoded / (texture_name + '.json')).read_text(encoding='utf-8-sig')),
                      bulk_path.read_bytes() if bulk_path.exists() else None) if texture_name else None
        path = output / f'entrance_{id}.png'
        preview(vertices, uvs, triangles, tex, color, yaw=180 if id == 'rock_cave' else 90 if id == 'dwarven_cave' else 0).save(path, optimize=True)
        package = next(n for n in document['NameMap'] if n.startswith('/Game/Env/Wld/') and n.endswith('/' + asset))
        catalog['entrances'].append({'id': id, 'name': name, 'image': path.name, 'mesh': package,
            'sha256': hashlib.sha256(path.read_bytes()).hexdigest(), 'sourceSha256': hashlib.sha256(source.read_bytes()).hexdigest(),
            'vertices': len(vertices), 'triangles': len(triangles), 'preview': 'Native LOD0 geometry; simplified lighting and diffuse sampling'})
    (output / 'locations.json').write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + '\n',
                                           encoding='utf-8', newline='\n')
    print(f'Built {len(vendors)} native inventory/combined vendor choices and {len(ENTRANCES)} entrance previews.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--decoded', type=Path, required=True)
    parser.add_argument('--output', type=Path, default=Path('assets/acquisition_map'))
    args = parser.parse_args()
    build(args.decoded, args.output)
