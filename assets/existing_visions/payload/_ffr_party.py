"""Battle-only party model overrides. Original field/cutscene packages stay intact."""
import copy
import json
from pathlib import Path

TABLE = 'Asset/Battle/Unit/DT_BtlPlayableUnitAsset'
ASSET = 'FFRS/Content/Datatable/' + TABLE
CHARACTERS = (
    (1001, 'レイン', 'Rain', 'unit0010'),
    (1002, 'ラスウェル', 'Lasswell', 'unit0020'),
    (1003, 'フィーナ', 'Fina', 'unit0030'),
    (1004, 'リド', 'Lid', 'unit0040'),
    (1005, 'ニコル', 'Nichol', 'unit0050'),
    (1006, '魔人フィーナ', 'Dark Fina', 'unit0060'),
    (1007, 'ジェイク', 'Jake', 'unit0070'),
    (1008, 'サクラ', 'Sakura', 'unit0080'),
)
FINA = '99887755552703'


def identity(id):
    return next((c for c in CHARACTERS if c[0] == id), None)


def snapshot(id, rows):
    c = identity(id)
    if not c or rows(TABLE).get(c[1], {}).get('Ss6Project') != c[3]:
        raise ValueError('The original party battle model is unavailable. Prepare the game files again.')
    return {'key': f'party_{id}', 'id': id, 'jp': c[1], 'en': c[2],
            'party': {'version': 1, 'id': id}}


def validate(u):
    c = identity(u.get('id'))
    if (not c or type(u['id']) is not int or u.get('key') != f'party_{c[0]}'
            or u.get('jp') != c[1] or u.get('en') != c[2]
            or u.get('party') != {'version': 1, 'id': c[0]}
            or set(u) - {'key', 'id', 'jp', 'en', 'party', 'ffbe', 'menuScale', 'icon'}):
        raise ValueError('Invalid party replacement; its original character identity must be preserved.')
    ff = u.get('ffbe')
    if ff is not None:
        if not isinstance(ff, dict) or not isinstance(ff.get('id'), str) or not ff['id'].isdigit():
            raise ValueError('Invalid party sprite model.')
        for field in ('dir', 'baseDir'):
            path = ff.get(field)
            if field == 'dir' and not path: raise ValueError('The party sprite folder is missing.')
            if path and (not isinstance(path, str) or '\\' in path or ':' in path
                         or Path(path).is_absolute() or '..' in Path(path).parts
                         or not path.startswith('units/')):
                raise ValueError('The party sprite folder must stay inside the engine units cache.')
        if ff.get('baseDir') and not str(ff.get('baseForm', '')).isdigit():
            raise ValueError('The party model base form is missing.')
    return u


def split(units, rows):
    party = []; others = []; ids = set()
    for u in units:
        if u.get('party') is None:
            others.append(u); continue
        validate(u); snapshot(u['id'], rows)
        if u['id'] in ids or any(v is not u and v.get('id') == u['id'] for v in units):
            raise ValueError('Duplicate party character override.')
        ids.add(u['id']); party.append(u)
    return party, others


def package(u):
    return f'/Game/Chara/StudioParty/party{u["id"]}/{identity(u["id"])[3]}'


def material(u):
    return f'/Game/BP/Map/Unit/Material/M_StudioParty{u["id"]}'


def replacements(units):
    return {f'/Game/Chara/unit/{identity(u["id"])[3]}': package(u).rsplit('/', 1)[0]
            for u in units if u.get('ffbe')}


def rename(value, changes):
    if isinstance(value, str):
        for old, new in changes.items():
            if value == old or value.startswith(old + '/'):
                return new + value[len(old):]
        return value
    if isinstance(value, list): return [rename(v, changes) for v in value]
    if isinstance(value, dict): return {k: rename(v, changes) for k, v in value.items()}
    return value


def table_view(original, units):
    edited = rename(copy.deepcopy(original), replacements(units))
    for u in units:
        if str((u.get('ffbe') or {}).get('id')) != FINA: continue
        imports = edited['Imports']; path = material(u); leaf = path.rsplit('/', 1)[1]
        start = len(imports)
        template = {'$type': 'UAssetAPI.Import, UAssetAPI', 'PackageName': None, 'bImportOptional': False}
        imports.append(dict(template, ObjectName=path, OuterIndex=0,
                            ClassName='Package', ClassPackage='/Script/CoreUObject'))
        imports.append(dict(template, ObjectName=leaf, OuterIndex=-start-1,
                            ClassName='Material', ClassPackage='/Script/Engine'))
        for name in (path, leaf):
            if name not in edited['NameMap']: edited['NameMap'].append(name)
        export = next(e for e in edited['Exports'] if 'Table' in e)
        row = next(r for r in export['Table']['Data'] if r['Name'] == u['jp'])
        prop = next(p for p in row['Value'] if p['Name'] == 'Material')
        prop['Value'] = -start-2
        dep = export.get('SerializationBeforeSerializationDependencies')
        if isinstance(dep, list) and -start-2 not in dep: dep.append(-start-2)
    return edited


def check_table(original, built, units):
    expected = table_view(original, units)
    # Layout offsets and counts can change during serialization. Check the
    # actual object imports and every table property, including untouched rows.
    for field in ('Imports',):
        if built.get(field) != expected.get(field):
            raise ValueError('Party battle table imports did not match the selected private models.')
    original_tables = [e['Table'] for e in expected['Exports'] if 'Table' in e]
    written_tables = [e['Table'] for e in built['Exports'] if 'Table' in e]
    if written_tables != original_tables:
        raise ValueError('Party battle table changed an unrelated row or property.')


def write_table(units, root, legacy, out, tool, usmap, run):
    selected = [u for u in units if u.get('ffbe')]
    if not selected: return
    work = Path(root) / 'build/party-models'; work.mkdir(parents=True, exist_ok=True)
    source = Path(legacy) / (ASSET + '.uasset')
    destination = Path(out) / (ASSET + '.uasset'); destination.parent.mkdir(parents=True, exist_ok=True)
    original_path = work / 'original.json'; edited_path = work / 'edited.json'; written_path = work / 'written.json'
    run(tool + ['tojson', str(source), str(original_path), '--usmap', usmap])
    original = json.loads(original_path.read_text(encoding='utf-8-sig'))
    edited_path.write_text(json.dumps(table_view(original, selected), ensure_ascii=False), encoding='utf-8')
    run(tool + ['fromjson', str(edited_path), str(destination), '--usmap', usmap])
    run(tool + ['tojson', str(destination), str(written_path), '--usmap', usmap])
    check_table(original, json.loads(written_path.read_text(encoding='utf-8-sig')), selected)


def party_motions(spec):
    """Nichol's original mixture sequence uses a held pose and a return phase."""
    attack = next((a for a in spec['animations'] if a['name'] == 'attack_B'), None)
    if not attack: return
    total = attack['frameCount']
    for name, hold in (('attack_B_pose', True), ('attack_B_reverse', False)):
        if any(a['name'] == name for a in spec['animations']): continue
        motion = copy.deepcopy(attack); motion['name'] = name
        if hold: motion['frameCount'] = 1
        for channels in motion['parts'].values():
            for channel, keys in channels.items():
                if not keys: continue
                if hold: channels[channel] = [[0, keys[-1][1]]]
                else:
                    ends = [k[0] for k in keys[1:]] + [total]
                    channels[channel] = sorted([[max(0, total-end), k[1]] for k, end in zip(keys, ends)])
        spec['animations'].append(motion)


def generate(u, env):
    """Generate private battle SS6/texture assets; never menu or field assets."""
    root = Path(env['ROOT']); legacy = Path(env['LEGACY']); out = Path(env['OUT'])
    templates = legacy / 'FFRS/Content/Chara/summon/summon13110'
    if any(not (templates / f'summon13110{suffix}{extension}').is_file() for suffix in ('', '_tex', '_normal', '_mreo') for extension in ('.uasset', '.uexp')):
        env['run'](env['ffrenv'].py(str(root / 'tools/extract_legacy.py'), '--filter', 'Chara/summon/summon13110/'))
    tool = env['FFRDT']; usmap = env['USMAP']; run = env['run']; ff = u['ffbe']
    import _ffr_animation_repair
    _ffr_animation_repair.repair_unit(u, root)
    c = identity(u['id']); name = c[3]; target = package(u)
    work = root / 'build/sprites' / u['key']; battle = work / 'battle'
    args = env['ffrenv'].py(str(root / 'tools/_ffr_build_sprites.py'), str(root / ff['dir']),
                           ff['id'], str(u['id']), str(work), '--battle-only')
    if ff.get('baseDir'): args += ['--base', str(root / ff['baseDir']), str(ff['baseForm'])]
    run(args)
    spec_path = battle / 'spec.json'; spec = json.loads(spec_path.read_bytes())
    # The sprite converter writes pixelSize as floats. make-texture parses
    # integer command-line arguments, so preserve whole dimensions as integers.
    dimensions = spec['pixelSize']
    if len(dimensions) != 2 or any(type(n) not in (int, float) or not 0 < n <= 32768 or n != int(n)
                                   for n in dimensions):
        raise ValueError('The party battle atlas must have two positive whole pixel dimensions.')
    w, h = (str(int(n)) for n in dimensions)
    party_motions(spec)
    spec.update(cellmapName=name, animePackName=name, imagePath=name + '_tex.png')
    spec_path.write_text(json.dumps(spec), encoding='utf-8')
    destination = out / 'FFRS/Content' / target.removeprefix('/Game/').rsplit('/', 1)[0]
    destination.mkdir(parents=True, exist_ok=True)
    donor = 13110; old = f'/Game/Chara/summon/summon{donor}/summon{donor}'
    templates = legacy / f'FFRS/Content/Chara/summon/summon{donor}'
    run(tool + ['make-ss6', str(templates / f'summon{donor}.uasset'), str(spec_path),
                str(destination / (name + '.uasset')), old, target,
                f'summon{donor}={name}', '--usmap', usmap])
    for suffix, payload in (('_tex', 'tex.bgra'), ('_normal', 'normal.bc5'), ('_mreo', 'mreo.bgra')):
        run(tool + ['make-texture', str(templates / f'summon{donor}{suffix}.uasset'),
                    str(battle / payload), w, h, str(destination / (name + suffix + '.uasset')),
                    old + suffix, target + suffix, f'summon{donor}={name}', '--usmap', usmap])
    if str(ff['id']) == FINA:
        import _ffr_crystalfina as fina
        sources = fina.materials(root); source = sources[0][0]
        original_json = work / 'material-original.json'; edited_json = work / 'material-edited.json'
        run(tool + ['tojson', str(source), str(original_json), '--usmap', usmap])
        original = json.loads(original_json.read_text(encoding='utf-8-sig'))
        export = original['Exports'][0]
        class_index = export['ClassIndex']
        if class_index >= 0 or original['Imports'][-class_index-1]['ObjectName'] != 'Material':
            raise ValueError('The Crystal Fina material class changed; the party reference cannot be resolved safely.')
        changes = {fina.MATERIAL: material(u),
                   f'/Game/Chara/summon/summon{fina.VISION_ID}/summon{fina.VISION_ID}_tex': target + '_tex'}
        def replace(v):
            if isinstance(v, str):
                return changes.get(v, {f'M_CrystalFina_AlphaTest_{fina.VISION_ID}': material(u).rsplit('/', 1)[1],
                                       f'summon{fina.VISION_ID}_tex': name + '_tex'}.get(v, v))
            if isinstance(v, list): return [replace(x) for x in v]
            if isinstance(v, dict): return {k: replace(x) for k, x in v.items()}
            return v
        edited = replace(original)
        leaf = material(u).rsplit('/', 1)[1]
        if leaf not in edited['NameMap']: edited['NameMap'].append(leaf)
        edited_json.write_text(json.dumps(edited), encoding='utf-8')
        dest = out / ('FFRS/Content/' + material(u).removeprefix('/Game/') + '.uasset')
        dest.parent.mkdir(parents=True, exist_ok=True)
        run(tool + ['fromjson', str(edited_json), str(dest), '--usmap', usmap])
        if dest.with_suffix('.uexp').read_bytes() != source.with_suffix('.uexp').read_bytes():
            raise ValueError('The party material serializer changed the original shader payload.')


def build(units, env):
    selected = [u for u in units if u.get('ffbe')]
    if not selected: return
    for u in selected:
        env['stage']('Replacing party battle model: ' + u['en'])
        generate(u, env)
    write_table(selected, env['ROOT'], env['LEGACY'], env['OUT'], env['FFRDT'], env['USMAP'], env['run'])


def verify(root, tool, usmap):
    import subprocess
    root = Path(root); units = json.loads((root / 'mods/EstherTsukiko/units.json').read_bytes())
    selected = [validate(u) for u in units if u.get('party') and u.get('ffbe')]
    if not selected: return
    work = root / 'build/party-models'; work.mkdir(parents=True, exist_ok=True)
    def run(args): subprocess.run(args, check=True, capture_output=True)
    original = work / 'verify-original.json'; built = work / 'verify-built.json'
    run(tool + ['tojson', str(root / 'extracted/legacy' / (ASSET + '.uasset')), str(original), '--usmap', usmap])
    run(tool + ['tojson', str(root / 'build/visions_mod/assets' / (ASSET + '.uasset')), str(built), '--usmap', usmap])
    check_table(json.loads(original.read_text(encoding='utf-8-sig')), json.loads(built.read_text(encoding='utf-8-sig')), selected)
    for u in selected:
        path = root / 'build/visions_mod/assets/FFRS/Content' / package(u).removeprefix('/Game/')
        for suffix in ('', '_tex', '_normal', '_mreo'):
            for extension in ('.uasset', '.uexp'):
                if not path.with_name(path.name + suffix).with_suffix(extension).is_file():
                    raise ValueError('A generated party battle asset is missing: ' + str(path))
    print('OK: private party battle models and unchanged original table rows verified')


def register(app, env):
    from fastapi import HTTPException
    def make(id):
        try: return snapshot(id, env['ffr_catalog'].rows)
        except (ValueError, OSError, KeyError) as e: raise HTTPException(422, str(e)) from e
    @app.get('/api/party/catalog')
    def catalog(): return [make(c[0]) for c in CHARACTERS]
    @app.get('/api/party/character/{id}')
    def character(id: int): return make(id)
