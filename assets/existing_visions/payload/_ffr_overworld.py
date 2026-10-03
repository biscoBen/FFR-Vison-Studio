"""Opt-in party field sprites, separate from battle appearance and identity."""
import copy
import hashlib
import json
from pathlib import Path

MODEL = 'vagrant_knight_rain'
SHEET = 'vagrant_knight_rain_field.png'
# DaddyRaegen/ffbe_asset_dump town/map_character11.png, git blob
# ec345dbeb6a3f68d53aa24a107b8b53e78abfb51. Bundled; no build-time download.
SHEET_SHA256 = 'c138277635d7539920af898cc89a59f0baade2d956a5ea5aa2c474ec76c7e6ba'
TABLE = 'Asset/Map/DT_MapUnitAsset'
# FFBE's rows: south, north, west, southeast, southwest, east,
# northeast, northwest. Resonance uses keypad directions, including 9.
DIRECTIONS = ((2, 0), (8, 1), (4, 2), (3, 3), (1, 4), (6, 5), (9, 6), (7, 7))


def validate(choice):
    if (not isinstance(choice, dict) or type(choice.get('version')) is not int
            or choice != {'version': 1, 'model': MODEL}):
        raise ValueError('This overworld model has no supported directional sprite sheet.')


def package(u):
    name = f'pc{(u["id"] - 1000) * 10:04d}'
    return f'/Game/Chara/StudioOverworld/party{u["id"]}/{name}'


def updates(u):
    validate(u['overworld'])
    path = package(u)
    return {'animationAssetList[0].' + k: path + suffix for k, suffix in (
        ('Ss6Project', ''), ('textureBaseColor', '_tex'),
        ('textureNormal', '_normal'), ('textureMetallicRoughness', '_mreo'))}


def prepare(tables, units, rows):
    for u in units:
        if not u.get('overworld'): continue
        row = rows(TABLE).get(u['jp'], {})
        map_id = (u['id'] - 1000) * 10
        original = f'/Game/Chara/Field_Unit/pc{map_id:04d}/pc{map_id:04d}'
        animations = row.get('animationAssetList', [])
        if row.get('ID') != map_id or not animations or animations[0].get('Ss6Project') != original:
            raise ValueError('The original party field assets changed; prepare the game files again.')
        table = tables.setdefault(TABLE, {'asset': 'FFRS/Content/Datatable/' + TABLE, 'add': [], 'set': []})
        table['set'].append({'row': u['jp'], 'set': updates(u)})


def check_rows(original, built, units):
    expected = copy.deepcopy(original)
    for u in units:
        if not u.get('overworld'): continue
        for key, value in updates(u).items():
            expected[u['jp']]['animationAssetList'][0][key.split('.')[-1]] = value
    if built != expected:
        raise ValueError('Party field assets differ from the selected model or an unrelated field changed.')


def spec(name):
    cells = [{'name': f'field_{row}_{col}', 'pos': [col*64, row*64],
              'size': [64, 64], 'pivot': [0.0, -0.3125]}
             for row in range(24) for col in range(7)]
    animations = []
    for direction, row in DIRECTIONS:
        for motion, offset, delay in (('idle', 0, 1), ('move', 16, 8), ('dash', 8, 5)):
            count = 1 if motion == 'idle' else 7
            parts = {'root': {'Hide': [[0, 0.0]]},
                     'part_0': {'Cell': [[i*delay, f'field_{row+offset}_{i}'] for i in range(count)],
                                'Posx': [[0, 0.0]], 'Posy': [[0, 0.0]], 'Posz': [[0, 1.0]],
                                'Sclx': [[0, 1.0]], 'Scly': [[0, 1.0]], 'Hide': [[0, 0.0]]},
                     'NULL_Head': {'Posx': [[0, 0.0]], 'Posy': [[0, 46.0]]},
                     'NULL_Center': {'Posx': [[0, 0.0]], 'Posy': [[0, 23.0]]}}
            animations.append({'name': f'{motion}{direction}', 'fps': 60, 'frameCount': count*delay,
                               'canvas': [128.0, 128.0], 'pivot': [0.0, 0.0], 'isSetup': False, 'parts': parts})
    # Undirected requests and alternative movement names share the same poses.
    for alias, source in [('idle', 'idle2'), ('move', 'move2'), ('dash', 'dash2'),
                          *[(f'walk{d}', f'move{d}') for d, _ in DIRECTIONS],
                          *[(f'run{d}', f'dash{d}') for d, _ in DIRECTIONS]]:
        animation = copy.deepcopy(next(a for a in animations if a['name'] == source))
        animation['name'] = alias; animations.append(animation)
    setup = copy.deepcopy(animations[0]); setup.update(name='Setup', isSetup=True)
    animations.append(setup)
    return {'pixelSize': [448, 1536], 'cellmapName': name, 'animePackName': name,
            'imagePath': name + '_tex.png', 'cells': cells, 'animations': animations}


def generate(u, env):
    from PIL import Image
    validate(u['overworld'])
    sheet = Path(__file__).with_name(SHEET)
    if hashlib.sha256(sheet.read_bytes()).hexdigest() != SHEET_SHA256:
        raise ValueError('The bundled Vagrant Knight Rain field sheet failed checksum validation.')
    image = Image.open(sheet).convert('RGBA')
    if image.size != (448, 1536): raise ValueError('The bundled field sheet dimensions changed.')
    root = Path(env['ROOT']); out = Path(env['OUT']); legacy = Path(env['LEGACY'])
    templates = legacy / 'FFRS/Content/Chara/summon/summon13110'
    if any(not (templates / f'summon13110{s}{e}').is_file()
           for s in ('', '_tex', '_normal', '_mreo') for e in ('.uasset', '.uexp')):
        env['run'](env['ffrenv'].py(str(root / 'tools/extract_legacy.py'), '--filter', 'Chara/summon/summon13110/'))
    work = root / 'build/overworld' / u['key']; work.mkdir(parents=True, exist_ok=True)
    target = package(u); name = target.rsplit('/', 1)[1]
    path = work / 'spec.json'; path.write_text(json.dumps(spec(name)))
    pixels = image.tobytes(); bgra = bytearray(len(pixels))
    bgra[0::4] = pixels[2::4]; bgra[1::4] = pixels[1::4]
    bgra[2::4] = pixels[0::4]; bgra[3::4] = pixels[3::4]
    (work / 'tex.bgra').write_bytes(bgra)
    (work / 'normal.bc5').write_bytes(bytes([128,128,0,0,0,0,0,0]*2) * (448//4) * (1536//4))
    (work / 'mreo.bgra').write_bytes(bytes([0,120,60,0]) * 448 * 1536)
    destination = out / 'FFRS/Content' / target.removeprefix('/Game/').rsplit('/', 1)[0]
    destination.mkdir(parents=True, exist_ok=True)
    old = '/Game/Chara/summon/summon13110/summon13110'
    tool = env['FFRDT']; run = env['run']; usmap = env['USMAP']
    run(tool + ['make-ss6', str(templates / 'summon13110.uasset'), str(path),
                str(destination / (name + '.uasset')), old, target, f'summon13110={name}', '--usmap', usmap])
    for suffix, payload in (('_tex', 'tex.bgra'), ('_normal', 'normal.bc5'), ('_mreo', 'mreo.bgra')):
        run(tool + ['make-texture', str(templates / ('summon13110' + suffix + '.uasset')),
                    str(work / payload), '448', '1536', str(destination / (name + suffix + '.uasset')),
                    old + suffix, target + suffix, f'summon13110={name}', '--usmap', usmap])


def verify(root, tool, usmap, units):
    import subprocess
    selected = [u for u in units if u.get('overworld')]
    if not selected: return
    root = Path(root); work = root / 'build/overworld'; work.mkdir(parents=True, exist_ok=True)
    views = []
    for folder, label in (('extracted/legacy', 'original'), ('build/visions_mod/assets', 'built')):
        path = root / folder / ('FFRS/Content/Datatable/' + TABLE + '.uasset')
        decoded = work / (label + '-rows.json')
        subprocess.run(tool + ['rows', str(path), str(decoded), '--usmap', usmap], check=True, capture_output=True)
        views.append(json.loads(decoded.read_text(encoding='utf-8-sig'))['rows'])
    check_rows(*views, selected)
    for u in selected:
        path = root / 'build/visions_mod/assets/FFRS/Content' / package(u).removeprefix('/Game/')
        for suffix in ('', '_tex', '_normal', '_mreo'):
            for extension in ('.uasset', '.uexp'):
                if not path.with_name(path.name + suffix).with_suffix(extension).is_file():
                    raise ValueError('A generated party overworld asset is missing: ' + str(path))
    print('OK: private party field models and unchanged original map rows verified')
