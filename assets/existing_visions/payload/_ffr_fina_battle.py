"""Private native Crystal Fina battle presentation; no skill or roster edits."""
import copy
import json
import math
import struct
from pathlib import Path

import _ffr_crystal_cave as cave

SPRITE = cave.SPRITE
EFFECT_TABLE = 'Asset/Battle/Effect/DT_BtlUnitEffectAsset'
UNIT_TABLE = 'Asset/Battle/Unit/DT_BtlUnitAsset'
DESIGN_TABLE = 'Battle/Unit/DT_BtlUnitDesignParameter'
AURA = 'Effect/07_EV/CMN/FinaCristalAuraParticle001/NS_EF_EV_CMN_FinaCristalAuraParticle'
PREFIX = 'Chara/StudioCrystalFinaBattle/'
BATTLE_SPRITE_SCALE = 2.7
# Keep the approved cave surface, but protect the nearer battle body from
# background distortion. Unreal's soft gate starts at bias * (bias/2): 288 UU
# here, versus 72 UU for the cave's 12. Distant background still refracts.
BATTLE_REFRACTION_DEPTH_BIAS = 24.0


def selected(units):
    matches = [u for u in units if not u.get('party') and str((u.get('ffbe') or {}).get('id')) == SPRITE]
    if not matches: return None
    if len(matches) != 1 or type(matches[0].get('id')) is not int or matches[0]['id'] <= 0:
        raise ValueError('Crystal Fina battle presentation needs one unambiguous vision ID.')
    if (matches[0].get('ffbe') or {}).get('source') != 'CUSTOM':
        raise ValueError('The Crystal Fina sprite source changed.')
    return matches[0]


def package(unit, leaf):
    return PREFIX + str(unit['id']) + '/' + leaf


def glow_package(unit):
    return 'Effect/StudioCrystalFinaBattle/' + str(unit['id']) + '/NS_Studio_CrystalFinaGlow'


def clone_glow(source, destination, unit, tool, usmap, run):
    """Rename the native package without a lossy Niagara JSON roundtrip.

    The JSON representation omits native NiagaraVariable names/offsets and
    bindings. A native clone preserves their export bytes, curves and VM.
    LightPower is suppressed on the owned component at runtime instead.
    """
    source, destination = Path(source), Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    run(tool + ['clone-package', str(source), str(destination), '/Game/' + AURA,
                '/Game/' + glow_package(unit), Path(AURA).name + '=' + destination.stem, '--usmap', usmap])
    original, built = source.with_suffix('.uexp'), destination.with_suffix('.uexp')
    if not original.is_file() or not built.is_file() or original.read_bytes() != built.read_bytes():
        raise ValueError('The native Crystal Fina glow export data changed during cloning.')


def table_rows(view):
    exports = [e for e in view['Exports'] if isinstance(e.get('Table'), dict)]
    if len(exports) != 1: raise ValueError('Expected one native battle data table.')
    return exports[0]['Table']['Data']


def soften_battle_glass(original, leaf):
    """Change only the private battle depth gate; preserve cave/source assets."""
    view = copy.deepcopy(original)
    _, instance = cave.export(view, leaf)
    parameters = cave.property_data(instance, 'ScalarParameterValues')['Value']
    matches = [p for p in parameters if cave.property_data(cave.property_data(p, 'ParameterInfo'), 'Name')['Value'] == 'RefractionDepthBias']
    if len(matches) != 1:
        raise ValueError('The approved glass refraction depth override is missing or ambiguous.')
    cave.set_value(matches[0], 'ParameterValue', BATTLE_REFRACTION_DEPTH_BIAS)
    return view


def soft_path(owner, name, path):
    value = cave.property_data(owner, name)
    value['Value']['AssetPath'].update(PackageName=path, AssetName=Path(path).name)
    value['Value']['SubPathString'] = None; value['IsZero'] = False


def battle_table(original, unit):
    """Postprocess the fresh build, preserving every other row and all metadata."""
    view = copy.deepcopy(original)
    matches = [r for r in table_rows(view) if cave.property_data(r, 'ID')['Value'] == unit['id']]
    if len(matches) != 1 or matches[0]['Name'] != unit['jp']:
        raise ValueError('The freshly built Crystal Fina battle row is missing or ambiguous.')
    animation, = cave.property_data(matches[0], 'animationAssetList')['Value']
    expected = f'/Game/Chara/summon/summon{unit["id"]}/summon{unit["id"]}'
    if cave.property_data(animation, 'Ss6Project')['Value']['AssetPath']['PackageName'] != expected:
        raise ValueError('Crystal Fina battle assets no longer match this build.')
    target = '/Game/' + package(unit, 'FinaNative' + str(unit['id']))
    for name, path in [('Ss6Project', target), ('textureBaseColor', target + '_tex'),
                       ('textureNormal', target + '_normal'), ('textureMetallicRoughness', target + '_mreo'),
                       ('Material', '/Game/BP/Map/Unit/Material/CharaPBR/M_Ss_Component_PBRBattle')]:
        soft_path(animation, name, path)
    cave.set_value(animation, 'isVisionCharacter', False)
    cave.names(view, matches)
    return view


def design_table(original, unit):
    """Make unset presentation scales explicit on Fina's fresh row only.

    A nonpositive source value is not a usable presentation scale or divisor.
    Rather than infer the C++ inheritance/default path, author positive values
    for this private presentation and use them for its casing ratio.
    """
    view = copy.deepcopy(original)
    matches = [r for r in table_rows(view) if cave.property_data(r, 'ID')['Value'] == unit['id']]
    if len(matches) != 1 or matches[0]['Name'] != unit['jp']:
        raise ValueError('The freshly built Crystal Fina design row is missing or ambiguous.')
    row = matches[0]; resolved = []
    for name, fallback in [('Scale', BATTLE_SPRITE_SCALE), ('attachEffectSacle', 1.0)]:
        field = cave.property_data(row, name); raw = field['Value']
        if not (type(raw) in (int, float) or type(raw) is str and raw in ('+0', '-0')):
            raise ValueError('Unsupported Crystal Fina design scale: ' + name + '=' + repr(raw))
        value = float(raw)
        if not math.isfinite(value):
            raise ValueError('Invalid Crystal Fina design scale: ' + name + '=' + repr(raw))
        if value <= 0:
            value = struct.unpack('<f', struct.pack('<f', fallback))[0]
            cave.set_value(row, name, value)
        resolved.append(value)
    return view, tuple(resolved)


def build(units, env):
    unit = selected(units)
    if unit is None: return
    import _ffr_fina_motion as motion
    root, legacy, out = (Path(env[n]) for n in ('ROOT', 'LEGACY', 'OUT'))
    work = root / 'build/crystal-fina-battle'; work.mkdir(parents=True, exist_ok=True)
    tool, usmap, run = env['FFRDT'], env['USMAP'], env['run']
    def decode(path, label):
        dump = work / (label + '-original.json')
        run(tool + ['tojson', str(path), str(dump), '--usmap', usmap])
        return json.loads(dump.read_text(encoding='utf-8-sig'))
    def native(rel, suffix='.uasset'):
        path = legacy / ('FFRS/Content/' + rel + suffix)
        if not path.is_file() or rel == cave.TEST_NATIVE_MESH and not path.with_suffix('.ubulk').is_file():
            run(env['ffrenv'].py(str(root / 'tools/extract_legacy.py'), '--filter', rel))
        if not path.is_file(): raise ValueError('Missing native Crystal Fina battle asset: ' + rel)
        return decode(path, Path(rel).name)
    source = {rel: native(rel, '.umap' if rel == cave.TEST_BACKGROUND else '.uasset') for rel in (
        AURA, cave.TEST_BACKGROUND, cave.TEST_NATIVE_MESH, cave.TEST_NATIVE_MATERIAL, cave.TEST_NATIVE_SHADER,
        cave.TEST_SPRITE.removeprefix('/Game/'), cave.TEST_SPRITE.removeprefix('/Game/') + '_tex')}
    content = out / 'FFRS/Content'
    design_path = content / ('Datatable/' + DESIGN_TABLE + '.uasset')
    design, (scale, effect_scale) = design_table(decode(design_path, 'built-battle-design'), unit)
    print(f'  Crystal Fina battle scales: sprite={scale:g}, attached effects={effect_scale:g} (explicit built row).')
    # Match the casing/body ratio approved in the field test. Battle sprite and
    # attachment scales are separate native design parameters.
    assets = {'Datatable/' + DESIGN_TABLE: design}
    clone_glow(legacy / ('FFRS/Content/' + AURA + '.uasset'), content / (glow_package(unit) + '.uasset'),
               unit, tool, usmap, run)
    private_mesh, private_material = package(unit, 'SM_Studio_CrystalFina'), package(unit, 'MI_Studio_CrystalFina')
    for old, view in cave.test_crystal_assets(source).items():
        new = private_mesh if old == cave.TEST_MESH else private_material
        result = cave.private_level(view, '/Game/' + old, '/Game/' + new)
        if old == cave.TEST_MESH:
            _, mesh = cave.export(result, Path(new).name)
            slot, = cave.property_data(mesh, 'StaticMaterials')['Value']
            material = cave.property_data(slot, 'MaterialInterface')
            material['Value'] = cave.asset_import(result, material['Value'], '/Game/' + private_material)
            material['IsZero'] = False
        else:
            result = soften_battle_glass(result, Path(new).name)
        assets[new] = result
    unit_path = content / ('Datatable/' + UNIT_TABLE + '.uasset')
    assets['Datatable/' + UNIT_TABLE] = battle_table(decode(unit_path, 'built-battle-units'), unit)
    for rel, view in assets.items():
        cave.names(view, [view['Imports'], view['Exports']])
        dump = work / (Path(rel).name + '-built.json'); dump.write_text(json.dumps(view), encoding='utf-8')
        dest = content / (rel + '.uasset'); dest.parent.mkdir(parents=True, exist_ok=True)
        run(tool + ['fromjson', str(dump), str(dest), '--usmap', usmap])
        check = decode(dest, Path(rel).name + '-verified')
        cave.check_level(view, check)
        if 'Datatable/' in rel and cave.semantic(table_rows(view)) != cave.semantic(table_rows(check)):
            raise ValueError('Crystal Fina battle data did not survive native serialization.')
    for suffix in ('.ubulk', '.uptnl'):
        src = legacy / ('FFRS/Content/' + cave.TEST_NATIVE_MESH + suffix)
        if src.is_file(): (content / (private_mesh + suffix)).write_bytes(src.read_bytes())
        elif suffix == '.ubulk': raise ValueError('Missing Sanctum crystal streamed mesh data.')
    original_spec = root / 'build/sprites' / unit['key'] / 'battle/spec.json'
    sheet = root / unit['ffbe']['dir'] / ('unit_anime_' + SPRITE + '.png')
    atlas, spec = motion.battle_spec(source[cave.TEST_SPRITE.removeprefix('/Game/')],
        source[cave.TEST_SPRITE.removeprefix('/Game/') + '_tex'], sheet, json.loads(original_spec.read_bytes()))
    name = 'FinaNative' + str(unit['id']); rel = package(unit, name)
    spec.update(cellmapName=name, animePackName=name, imagePath=name + '_tex.png')
    spec_path = work / 'spec.json'; spec_path.write_text(json.dumps(spec), encoding='utf-8')
    atlas.save(work / 'atlas.png'); (work / 'tex.bgra').write_bytes(atlas.tobytes('raw', 'BGRA'))
    w, h = atlas.size
    (work / 'normal.bc5').write_bytes(bytes((128, 128, 0, 0, 0, 0, 0, 0)) * (2 * (w // 4) * (h // 4)))
    (work / 'mreo.bgra').write_bytes(bytes((0, 120, 60, 0)) * w * h)
    old = f'Chara/summon/summon{unit["id"]}/summon{unit["id"]}'
    dest = content / (rel + '.uasset'); dest.parent.mkdir(parents=True, exist_ok=True)
    rename = 'summon' + str(unit['id']) + '=' + name
    run(tool + ['make-ss6', str(content / (old + '.uasset')), str(spec_path), str(dest),
                '/Game/' + old, '/Game/' + rel, rename, '--usmap', usmap])
    native_model = decode(dest, 'native-battle-model')
    motion.verify_model(native_model, spec)
    motion.verify_image_mirroring(native_model, spec)
    for suffix, payload in [('_tex', 'tex.bgra'), ('_normal', 'normal.bc5'), ('_mreo', 'mreo.bgra')]:
        run(tool + ['make-texture', str(content / (old + suffix + '.uasset')), str(work / payload),
                    str(w), str(h), str(content / (rel + suffix + '.uasset')),
                    '/Game/' + old + suffix, '/Game/' + rel + suffix, rename, '--usmap', usmap])
    _, mesh = cave.export(source[cave.TEST_NATIVE_MESH], Path(cave.TEST_NATIVE_MESH).name)
    origin = cave.property_data(cave.property_data(mesh, 'ExtendedBounds'), 'Origin')['Value'][0]['Value']
    (work / 'runtime.json').write_text(json.dumps(runtime_config(unit, origin)), encoding='utf-8')
    print('  Crystal Fina battle: native body and full cast; direct runtime crystal/glow attachments. Skills and hit events preserved.')


def prepare_job(job, units, lb_id):
    # Presentation effects are driven by the scoped runtime, not the battle
    # sequencer's ambiguous owner-versus-vision selection.
    return job


def runtime_config(unit, origin):
    import _ffr_fina_motion as motion
    name = 'FinaNative' + str(unit['id'])
    asset = lambda rel: '/Game/' + rel + '.' + Path(rel).name
    return {'schema': 1, 'id': unit['id'], 'project': '/Game/' + package(unit, name),
        'pack': name, 'mesh': asset(package(unit, 'SM_Studio_CrystalFina')),
        'material': asset(package(unit, 'MI_Studio_CrystalFina')), 'glow': asset(glow_package(unit)),
        'origin': origin, 'meshRatio': .12 / 2.7, 'turnRate': cave.TEST_CRYSTAL_TURN_RATE,
        'cast': 'Studio_FinaCast', 'castFrames': motion.ACTION_FRAMES,
        'fall': motion.FALL, 'reform': motion.REFORM, 'flashes': list(motion.FLASHES)}
