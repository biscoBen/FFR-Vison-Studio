"""Decode native Fina motion values and prepare the shared battle body tracks.

SsValue custom payloads live in Ss6Project.Extras, after the ordinary reflected
properties. Decode in animation/part/attribute/key order, matching Ss6Builder's
writer, rather than reading the empty reflected HashType fields as cell data.
"""
import argparse
import base64
import copy
import json
import math
from pathlib import Path
import struct

MAP_HEADER = bytes.fromhex('80090e03')
NAME_HEADER = bytes.fromhex('80090e01')
BODY_FLOAT = 183.5 / 2.7 - 21.0  # The approved cave's sprite float, in sprite pixels.
FALL = 134
SEAT = 183
# Hold the seated pose for 1.25 seconds at the native 60 fps. Gameplay keys stay put.
REFORM = SEAT + 75
# Four keys: begin, full brightness, end of plateau, faded out. The first
# envelope is already on at frame zero; native particles provide the build-up.
FLASHES = ((0, 0, FALL, FALL + 30),)
PREP_FRAMES = 30
RELEASE_FRAMES = 30
ACTION_FRAMES = PREP_FRAMES + RELEASE_FRAMES
# magicattack6 frame 66 is the first hands-forward shot pose (npc_0_15).
# Move all earlier wind-up into native preparation, so release starts firing.
SHOT_SOURCE_FRAME = 65 + 73 + 66


def prop(owner, name):
    values = owner.get('Data', owner.get('Value', []))
    matches = [p for p in values if p['Name'] == name]
    if len(matches) != 1:
        raise ValueError('Missing or ambiguous native property: ' + name)
    return matches[0]['Value']


def vector(owner, name):
    values = prop(owner, name)
    return values[0]['Value'] if values else {'X': 0.0, 'Y': 0.0}


def native_project(view):
    matches = [e for e in view['Exports'] if any(p.get('Name') == 'AnimeList' for p in e.get('Data', []) if isinstance(p, dict))]
    if len(matches) != 1:
        raise ValueError('Expected one native Ss6 project.')
    return matches[0]


def decode(view):
    """Read every native cell/scalar key, rejecting changed or truncated layouts."""
    project = native_project(view)
    payload = base64.b64decode(project['Extras'], validate=True)
    position = 0
    def take(size):
        nonlocal position
        if size < 0 or position + size > len(payload):
            raise ValueError('Truncated SsValue payload.')
        result = payload[position:position + size]; position += size
        return result
    def integer(): return struct.unpack('<i', take(4))[0]
    def name():
        index, number = integer(), integer()
        if not 0 <= index < len(view['NameMap']) or number:
            raise ValueError('Invalid SsValue name reference.')
        return view['NameMap'][index]
    packs = prop(project, 'AnimeList')
    if len(packs) != 1:
        raise ValueError('Expected one Fina animation pack.')
    clips = {}
    for animation in prop(packs[0], 'AnimeList'):
        settings = prop(animation, 'Settings')
        parts = {}
        for part in prop(animation, 'PartAnimes'):
            attributes = {}
            for attribute in prop(part, 'Attributes'):
                keys = []
                for key in prop(attribute, 'Key'):
                    kind = prop({'Value': prop(key, 'Value')}, 'Type')
                    if kind == 'FloatType':
                        value, = struct.unpack('<f', take(4))
                        if not math.isfinite(value): raise ValueError('Nonfinite SsValue scalar.')
                    elif kind == 'HashType':
                        if integer() != 2 or name() != 'mapId' or take(4) != MAP_HEADER:
                            raise ValueError('Unrecognized SsValue cell map.')
                        map_id = integer()
                        if name() != 'name' or take(4) != NAME_HEADER:
                            raise ValueError('Unrecognized SsValue cell name.')
                        size = integer()
                        if not 1 <= size <= 256: raise ValueError('Invalid SsValue cell name size.')
                        raw = take(size)
                        if raw[-1] != 0: raise ValueError('Unterminated SsValue cell name.')
                        value = {'mapId': map_id, 'name': raw[:-1].decode('ascii')}
                    else:
                        raise ValueError('Unsupported SsValue kind: ' + kind)
                    if prop(attribute, 'Tag') == 'Cell' and prop(key, 'IpType') != 'None':
                        raise ValueError('The Fina draft requires stepped native cell keys.')
                    keys.append([prop(key, 'Time'), value])
                attributes[prop(attribute, 'Tag')] = keys
            parts[prop(part, 'PartName')] = attributes
        title = prop(animation, 'AnimationName')
        if title in clips: raise ValueError('Duplicate native animation name.')
        clips[title] = {'name': title, 'fps': prop({'Value': settings}, 'Fps'),
                        'frameCount': prop({'Value': settings}, 'FrameCount'), 'parts': parts}
    if position != len(payload): raise ValueError('Unconsumed SsValue payload; native layout changed.')
    return clips


def stitch(clips, name, phases):
    """Flatten the native position/body hierarchy without changing cell pivots."""
    cells, frames = [], 0
    for source, count in phases:
        clip = clips[source]
        if clip['fps'] != 60 or not 0 < count <= clip['frameCount']:
            raise ValueError('Invalid native motion range.')
        for time, value in clip['parts']['part_0']['Cell']:
            if time < count:
                if value['mapId'] != 0: raise ValueError('Unexpected native Fina cell map.')
                cells.append([frames + time, value['name']])
        frames += count
    return {'name': name, 'fps': 60, 'frameCount': frames, 'canvas': [320.0, 320.0],
            'pivot': [0.0, 0.0], 'isSetup': False,
            'parts': {'root': {'Hide': [[0, 0.0]]}, 'part_0': {
                'Cell': cells, 'Posx': [[0, 0.0]], 'Posy': [[0, 22.0 + BODY_FLOAT]],
                'Posz': [[0, 1.0]], 'Sclx': [[0, 1.0]], 'Scly': [[0, 1.0]], 'Hide': [[0, 0.0]]}}}


def draft(view, seated_hold=90):
    clips = decode(view)
    attack = stitch(clips, 'attack', [('openarmopeneye2', 65), ('curlup2', 73), ('magicattack6', 91)])
    resonance = stitch(clips, 'resonance', [('openarmidle2', 49), ('openarmopeneye2', 65), ('curlup2', 20), ('down6', 49)])
    fall = 134
    seat = resonance['frameCount']
    body = resonance['parts']['part_0']
    # Translate the body to its grounded origin over the native 49-frame fall.
    body['Posy'] = [[0, 22.0 + BODY_FLOAT]] + [
        [fall + t, 22.0 + BODY_FLOAT * (1.0 - (t / 48.0) ** 2)] for t in range(49)]
    body['Cell'].append([seat, 'original_jacket_free_seated'])
    body['Posy'].append([seat, 0.0])
    resonance['frameCount'] += seated_hold
    return {'schema': 1, 'status': 'body motion draft; crystal/glow attachment not implemented',
            'attack': attack, 'resonance': resonance,
            'presentationEvents': [{'frame': 0, 'event': 'begin_intro_aura'},
                                   {'frame': fall, 'event': 'hide_casing_and_fall'},
                                   {'frame': seat, 'event': 'jacket_free_seated_hold'}],
            'gameplay': 'No skill, hit, healing or stat changes; regular attack release timing still requires sequence inspection.'}


def extract_atlas(texture):
    """Read the confirmed single-mip native BGRA layout; reject other formats."""
    from PIL import Image
    data = base64.b64decode(texture['Exports'][0]['Extras'], validate=True)
    if len(data) < 108 or data[60:72] != b'PF_B8G8R8A8\0':
        raise ValueError('Unsupported native Fina texture format.')
    width, height = struct.unpack_from('<II', data, 44)
    size = width * height * 4
    if (not 0 < width <= 4096 or not 0 < height <= 4096
            or len(data) != 84 + size + 24 or struct.unpack_from('<I', data, 76)[0] != 1
            or struct.unpack_from('<III', data, 84 + size) != (width, height, 1)):
        raise ValueError('Native Fina texture layout changed.')
    return Image.frombytes('RGBA', (width, height), data[84:84 + size], 'raw', 'BGRA')


def battle_spec(view, texture, old_sheet, original_spec):
    """Keep native pixels/pivots and fit action bodies to existing motion windows."""
    from PIL import Image
    atlas = extract_atlas(texture)
    cells = []
    for cell in prop(prop(native_project(view), 'CellmapList')[0], 'Cells'):
        pos, size, pivot = (vector(cell, n) for n in ('Pos', 'Size', 'Pivot'))
        rect = [float(pos['X']), float(pos['Y']), float(size['X']), float(size['Y'])]
        if not (0 <= rect[0] < rect[0] + rect[2] <= atlas.width
                and 0 <= rect[1] < rect[1] + rect[3] <= atlas.height):
            raise ValueError('A native Fina cell lies outside its atlas.')
        cells.append({'name': prop(cell, 'CellName'), 'pos': rect[:2], 'size': rect[2:],
                      'pivot': [float(pivot['X']), float(pivot['Y'])]})
    original = Image.open(old_sheet).convert('RGBA')
    if original.size != (1800, 1820): raise ValueError('The original Fina sheet changed.')
    seat = original.crop((1080, 1430, 1200, 1560)); bounds = seat.getbbox()
    if not bounds: raise ValueError('The original seated sprite is blank.')
    seat = seat.crop(bounds); x, y = 0, 330
    if (seat.width > atlas.width or y + seat.height > atlas.height
            or any(c['pos'][0] < x + seat.width and c['pos'][0] + c['size'][0] > x
                   and c['pos'][1] < y + seat.height and c['pos'][1] + c['size'][1] > y for c in cells)):
        raise ValueError('The seated sprite no longer fits the unused native atlas space.')
    atlas.paste(seat, (x, y))
    cells.append({'name': 'original_jacket_free_seated', 'pos': [x, y], 'size': list(seat.size),
                  'pivot': [(60 - bounds[0]) / seat.width - .5, .5 - (100 - bounds[1]) / seat.height]})
    clips = decode(view); body = draft(view)
    idle = stitch(clips, 'idle', [('openarmidle2', 49)])
    # The supplied trace has 30-frame preparation and release windows. Fit the
    # wind-up and shot separately; native release/impact/recovery stay in charge.
    def fit(clip, length):
        result = copy.deepcopy(clip); old_length = result['frameCount']
        result['frameCount'] = length
        for channels in result['parts'].values():
            for tag, keys in channels.items():
                fitted = {}
                for tick, value in keys:
                    fitted[min(length - 1, round(tick * length / old_length))] = value
                channels[tag] = [[tick, value] for tick, value in sorted(fitted.items())]
        return result
    windup = copy.deepcopy(body['attack']); windup['frameCount'] = SHOT_SOURCE_FRAME
    windup['parts']['part_0']['Cell'] = [key for key in windup['parts']['part_0']['Cell'] if key[0] < SHOT_SOURCE_FRAME]
    shot = copy.deepcopy(body['attack']); shot['frameCount'] -= SHOT_SOURCE_FRAME
    shot['parts']['part_0']['Cell'] = [[tick - SHOT_SOURCE_FRAME, cell]
        for tick, cell in shot['parts']['part_0']['Cell'] if tick >= SHOT_SOURCE_FRAME]
    if not shot['parts']['part_0']['Cell'] or shot['parts']['part_0']['Cell'][0][0] != 0:
        raise ValueError('The native first shot pose changed.')
    windup = fit(windup, PREP_FRAMES); shot = fit(shot, RELEASE_FRAMES)
    animations = []
    source_names = set()
    for original_clip in original_spec['animations']:
        name = original_clip['name']
        if name in source_names: raise ValueError('Duplicate battle animation name.')
        source_names.add(name)
        length = original_clip['frameCount']
        if type(length) is not int or not 1 <= length <= 36000:
            raise ValueError('Invalid existing battle animation window.')
        if name == 'LB1':
            clip = copy.deepcopy(body['resonance'])
            clip['frameCount'] = max(length, REFORM + 25)
            restored = [[REFORM + repeat * 49 + tick, cell]
                for repeat in range((clip['frameCount'] - REFORM) // 49 + 1)
                for tick, cell in idle['parts']['part_0']['Cell']
                if REFORM + repeat * 49 + tick < clip['frameCount']]
            clip['parts']['part_0']['Cell'] += restored
            clip['parts']['part_0']['Posy'].append([REFORM, 22.0 + BODY_FLOAT])
        elif name.startswith(('attack_', 'M_attack', 'FFBE_')) or name == 'magic_attack':
            clip = copy.deepcopy(shot)
        elif name in ('command', 'magic_idle'):
            clip = copy.deepcopy(windup)
        else:
            clip = copy.deepcopy(idle)
            if name == 'idle':
                clip['parts']['part_0']['Cell'] = [[repeat * 49 + tick, cell]
                    for repeat in range(123) for tick, cell in idle['parts']['part_0']['Cell'] if repeat * 49 + tick < 6000]
                clip['frameCount'] = 6000
            elif name == 'Setup': clip = fit(idle, 1)
        clip['name'] = name; clip['isSetup'] = name == 'Setup'
        parts = clip['parts']; frames = clip['frameCount']; center = 183.5 / 2.7
        for anchor, dx, dy in [('NULL_Head', 0, center + 25), ('NULL_Center', 0, center),
                               ('NULL_Weapon', 20, center), ('NULL_SKL000000_Magic', 0, center)]:
            parts[anchor] = {'Posx': [[0, float(dx)]], 'Posy': [[0, float(dy)]]}
        parts['NULL_Crystal'] = {'Posx': [[0, 0.0]], 'Posy': [[0, center]],
            'Roty': [[t, t * .06] for t in range(frames)]}
        parts['NULL_Aura'] = {'Posx': [[0, 0.0]], 'Posy': [[0, center]]}
        if name == 'LB1':
            parts['NULL_Crystal']['Posy'] += [[FALL, -10000.0], [REFORM, center]]
            # Cell pivots change during the fall and in the original seated
            # fallback. Track the visual center, rather than the feet/pivot.
            body_part = parts['part_0']; lookup = {c['name']: c for c in cells}
            ticks = sorted({tick for tag in ('Cell', 'Posx', 'Posy') for tick, _ in body_part[tag]})
            current = lambda keys, tick: next(value for time, value in reversed(keys) if time <= tick)
            xy = []
            for tick in ticks:
                cell = lookup[current(body_part['Cell'], tick)]
                xy.append((tick, *[current(body_part[tag], tick) - cell['pivot'][axis] * cell['size'][axis]
                                   for axis, tag in enumerate(('Posx', 'Posy'))]))
            parts['NULL_Aura'] = {'Posx': [[tick, x] for tick, x, y in xy],
                                  'Posy': [[tick, y] for tick, x, y in xy]}
        animations.append(clip)
    cast = copy.deepcopy(next(a for a in animations if a['name'] == 'attack_A'))
    cast['name'] = 'Studio_FinaCast'; cast['frameCount'] = ACTION_FRAMES
    cast['parts']['part_0'].update(copy.deepcopy(windup['parts']['part_0']))
    cast['parts']['part_0']['Cell'] += [[PREP_FRAMES + tick, cell] for tick, cell in shot['parts']['part_0']['Cell']]
    # Preview-only concatenation. Runtime never overrides native action playback.
    cast['parts']['NULL_Crystal']['Roty'] = [[t, t * .06] for t in range(ACTION_FRAMES)]
    animations.append(cast)
    for clip in animations:
        active = clip['name'] in ('LB1', 'command', 'magic_idle', 'Studio_FinaCast', 'magic_attack') or clip['name'].startswith(('attack_', 'M_attack', 'FFBE_'))
        # SS6's decoder ignores the legacy Fliph/Flipv attributes. Imgfliph
        # flips the cell image and leaves the body/socket origins intact.
        clip['parts']['part_0']['Imgfliph'] = [[0, 1.0 if active else 0.0]]
        if clip['name'] == 'LB1': clip['parts']['part_0']['Imgfliph'].append([REFORM, 0.0])
    if not {'idle', 'attack_A', 'LB1', 'Setup'} <= source_names:
        raise ValueError('The existing Fina battle motion set is incomplete.')
    names = list(animations[0]['parts'])
    if any(set(a['parts']) != set(names) for a in animations):
        raise ValueError('Fina clips disagree about the model hierarchy.')
    # make-ss6 supports an explicit model; animation tracks alone DO NOT create
    # parts. Every attachment must exist here or native lookups fall to root.
    model = {'parts': [{'name': name, 'parent': -1 if name == 'root' else 0,
                       'type': 'Normal' if name == 'part_0' else 'Null'} for name in names]}
    return atlas, {'pixelSize': list(atlas.size), 'model': model, 'cells': cells, 'animations': animations}


def verify_model(view, spec):
    pack, = prop(native_project(view), 'AnimeList')
    model = prop(pack, 'Model')
    parts = prop({'Value': model}, 'PartList')
    actual = [{'name': prop(p, 'PartName'), 'parent': prop(p, 'ParentIndex'),
               'type': prop(p, 'Type').split('::')[-1]} for p in parts]
    if actual != spec['model']['parts']:
        raise ValueError('Fina model parts/parents did not survive native serialization.')
    if [prop(p, 'ArrayIndex') for p in parts] != list(range(len(parts))):
        raise ValueError('Fina model indices do not match its attachment tracks.')
    if prop({'Value': model}, 'MeshList') or prop({'Value': model}, 'BoneList'):
        raise ValueError('The private flat Fina model retained donor mesh/bone data.')


def verify_image_mirroring(view, spec):
    """Verify the SS6-supported attribute and its native bool fallback cache."""
    decoded = decode(view)
    pack, = prop(native_project(view), 'AnimeList')
    native = {prop(a, 'AnimationName'): a for a in prop(pack, 'AnimeList')}
    for clip in spec['animations']:
        expected = clip['parts']['part_0']['Imgfliph']
        body = decoded[clip['name']]['parts']['part_0']
        if 'Fliph' in body or body.get('Imgfliph') != expected:
            raise ValueError('Fina image mirroring did not survive native serialization.')
        part, = [p for p in prop(native[clip['name']], 'PartAnimes') if prop(p, 'PartName') == 'part_0']
        attribute, = [a for a in prop(part, 'Attributes') if prop(a, 'Tag') == 'Imgfliph']
        actual = [[prop(k, 'Time'), prop({'Value': prop(k, 'Value')}, 'Bool_temp')] for k in prop(attribute, 'Key')]
        if actual != [[tick, bool(value)] for tick, value in expected]:
            raise ValueError('Fina image mirroring has an invalid native bool cache.')
