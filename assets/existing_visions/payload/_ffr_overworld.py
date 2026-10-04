"""Opt-in party field sprites, separate from battle appearance and identity."""
import copy
import hashlib
import json
from pathlib import Path
from functools import lru_cache
import zipfile

MODEL = 'vagrant_knight_rain'
SHEET = 'vagrant_knight_rain_field.png'
# DaddyRaegen/ffbe_asset_dump town/map_character11.png, git blob
# ec345dbeb6a3f68d53aa24a107b8b53e78abfb51. Bundled; no build-time download.
SHEET_SHA256 = 'c138277635d7539920af898cc89a59f0baade2d956a5ea5aa2c474ec76c7e6ba'
TABLE = 'Asset/Map/DT_MapUnitAsset'
# FFBE's rows: south, north, west, east, southwest, southeast,
# northwest, northeast. Resonance uses keypad directions, including 9.
DIRECTIONS = ((2, 0), (8, 1), (4, 2), (6, 3), (1, 4), (3, 5), (7, 6), (9, 7))


@lru_cache(maxsize=1)
def catalog():
    value = json.loads(Path(__file__).with_name('overworld_catalog.json').read_bytes())
    if value.get('schema') != 1 or value.get('archive') != 'overworld_assets.zip':
        raise ValueError('Unsupported directional field catalog.')
    return value


def validate(choice):
    if (not isinstance(choice, dict) or type(choice.get('version')) is not int
            or set(choice) != {'version', 'model'} or choice['version'] != 1
            or not isinstance(choice['model'], str) or choice['model'] not in catalog()['models']):
        raise ValueError('This overworld model has no supported directional sprite sheet.')


def model(choice=None):
    choice = {'version': 1, 'model': MODEL} if choice is None else choice
    validate(choice)
    return catalog()['models'][choice['model']]


def asset_bytes(entry, kind):
    archive = Path(__file__).with_name(catalog()['archive'])
    data = archive.read_bytes()
    if hashlib.sha256(data).hexdigest() != catalog()['archive_sha256']:
        raise ValueError('The bundled field archive failed checksum validation.')
    with zipfile.ZipFile(archive) as zipped:
        data = zipped.read(entry[kind])
    if hashlib.sha256(data).hexdigest() != entry[kind + '_sha256']:
        raise ValueError('The bundled field asset failed checksum validation: ' + entry[kind])
    return data


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


def spec(name, choice=None):
    entry = model(choice)
    width, height = entry['size']
    cells = [{'name': f'field_{row}_{col}', 'pos': [col*64, row*64],
              'size': [64, 64], 'pivot': [0.0, -0.3125]}
             for row in range(height // 64) for col in range(width // 64)]
    animations = []
    for direction, _ in DIRECTIONS:
        for motion, delay in (('idle', 1), ('move', 8), ('dash', 5)):
            frames = entry['motions'][f'{motion}{direction}']
            count = len(frames)
            parts = {'root': {'Hide': [[0, 0.0]]},
                     'part_0': {'Cell': [[i*delay, f'field_{row}_{col}'] for i, (row, col) in enumerate(frames)],
                                'Posx': [[0, 0.0]], 'Posy': [[0, 0.0]], 'Posz': [[0, 1.0]],
                                'Sclx': [[0, 1.0]], 'Scly': [[0, 1.0]], 'Hide': [[0, 0.0]]},
                     'NULL_Head': {'Posx': [[0, 0.0]], 'Posy': [[0, 46.0]]},
                     'NULL_Center': {'Posx': [[0, 0.0]], 'Posy': [[0, 23.0]]}}
            animations.append({'name': f'{motion}{direction}', 'fps': 60, 'frameCount': count*delay,
                               'canvas': [128.0, 128.0], 'pivot': [0.0, 0.0], 'isSetup': False, 'parts': parts})
    # Undirected requests and alternative movement names share the same poses.
    for alias, source in [('idle', 'idle2'), ('move', 'move2'), ('dash', 'dash2'),
                          *[(f'fieldidle{d}', f'idle{d}') for d, _ in DIRECTIONS],
                          *[(f'walk{d}', f'move{d}') for d, _ in DIRECTIONS],
                          *[(f'run{d}', f'dash{d}') for d, _ in DIRECTIONS]]:
        animation = copy.deepcopy(next(a for a in animations if a['name'] == source))
        animation['name'] = alias; animations.append(animation)
    setup = copy.deepcopy(animations[0]); setup.update(name='Setup', isSetup=True)
    animations.append(setup)
    return {'pixelSize': [width, height], 'cellmapName': name, 'animePackName': name,
            'imagePath': name + '_tex.png', 'cells': cells, 'animations': animations}


def generate(u, env):
    from PIL import Image
    import io
    validate(u['overworld'])
    entry = model(u['overworld'])
    image = Image.open(io.BytesIO(asset_bytes(entry, 'sheet'))).convert('RGBA')
    width, height = entry['size']
    if image.size != (width, height): raise ValueError('The bundled field sheet dimensions changed.')
    root = Path(env['ROOT']); out = Path(env['OUT']); legacy = Path(env['LEGACY'])
    templates = legacy / 'FFRS/Content/Chara/summon/summon13110'
    if any(not (templates / f'summon13110{s}{e}').is_file()
           for s in ('', '_tex', '_normal', '_mreo') for e in ('.uasset', '.uexp')):
        env['run'](env['ffrenv'].py(str(root / 'tools/extract_legacy.py'), '--filter', 'Chara/summon/summon13110/'))
    work = root / 'build/overworld' / u['key']; work.mkdir(parents=True, exist_ok=True)
    target = package(u); name = target.rsplit('/', 1)[1]
    path = work / 'spec.json'; path.write_text(json.dumps(spec(name, u['overworld'])))
    pixels = image.tobytes(); bgra = bytearray(len(pixels))
    bgra[0::4] = pixels[2::4]; bgra[1::4] = pixels[1::4]
    bgra[2::4] = pixels[0::4]; bgra[3::4] = pixels[3::4]
    (work / 'tex.bgra').write_bytes(bgra)
    (work / 'normal.bc5').write_bytes(bytes([128,128,0,0,0,0,0,0]*2) * (width//4) * (height//4))
    (work / 'mreo.bgra').write_bytes(bytes([0,120,60,0]) * width * height)
    destination = out / 'FFRS/Content' / target.removeprefix('/Game/').rsplit('/', 1)[0]
    destination.mkdir(parents=True, exist_ok=True)
    old = '/Game/Chara/summon/summon13110/summon13110'
    tool = env['FFRDT']; run = env['run']; usmap = env['USMAP']
    run(tool + ['make-ss6', str(templates / 'summon13110.uasset'), str(path),
                str(destination / (name + '.uasset')), old, target, f'summon13110={name}', '--usmap', usmap])
    for suffix, payload in (('_tex', 'tex.bgra'), ('_normal', 'normal.bc5'), ('_mreo', 'mreo.bgra')):
        run(tool + ['make-texture', str(templates / ('summon13110' + suffix + '.uasset')),
                    str(work / payload), str(width), str(height), str(destination / (name + suffix + '.uasset')),
                    old + suffix, target + suffix, f'summon13110={name}', '--usmap', usmap])


def verify(root, tool, usmap, units):
    import subprocess
    import _ffr_testing
    selected = [u for u in units if u.get('party') and u.get('overworld')]
    if not selected: return
    root = Path(root); work = root / 'build/overworld'; work.mkdir(parents=True, exist_ok=True)
    views = []
    for folder, label in (('extracted/legacy', 'original'), ('build/visions_mod/assets', 'built')):
        path = root / folder / ('FFRS/Content/Datatable/' + TABLE + '.uasset')
        decoded = work / (label + '-rows.json')
        subprocess.run(tool + ['rows', str(path), str(decoded), '--usmap', usmap], check=True, capture_output=True)
        views.append(json.loads(decoded.read_text(encoding='utf-8-sig'))['rows'])
    def rows(rel): return json.loads((root / 'extracted/rows' / (rel + '.json')).read_bytes())['rows']
    operations = _ffr_testing.verification_operations(root, units, rows)
    if TABLE not in operations: prepare(operations, selected, rows)
    _ffr_testing.check_rows(*views, operations[TABLE])
    for u in selected:
        path = root / 'build/visions_mod/assets/FFRS/Content' / package(u).removeprefix('/Game/')
        for suffix in ('', '_tex', '_normal', '_mreo'):
            for extension in ('.uasset', '.uexp'):
                if not path.with_name(path.name + suffix).with_suffix(extension).is_file():
                    raise ValueError('A generated party overworld asset is missing: ' + str(path))
    print('OK: private party field models and unchanged original map rows verified')
