"""Private native Crystal Fina battle presentation; no skill or roster edits."""
import copy
import json
import math
from pathlib import Path

import _ffr_crystal_cave as cave

SPRITE = cave.SPRITE
EFFECT_TABLE = 'Asset/Battle/Effect/DT_BtlUnitEffectAsset'
UNIT_TABLE = 'Asset/Battle/Unit/DT_BtlUnitAsset'
DESIGN_TABLE = 'Battle/Unit/DT_BtlUnitDesignParameter'
AURA = 'Effect/07_EV/CMN/FinaCristalAuraParticle001/NS_EF_EV_CMN_FinaCristalAuraParticle'
PREFIX = 'Chara/StudioCrystalFinaBattle/'


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


def casing_system(source, unit, relative_scale):
    """A component renderer retains the approved ordinary static-mesh shader.

    Keep the compiled Niagara emitter/script layout and opaque VM data intact.
    Render one non-colliding component at the SS6 attachment, without particle
    position/scale bindings moving or stretching the casing.
    """
    if not math.isfinite(relative_scale) or relative_scale <= 0:
        raise ValueError('Invalid battle crystal scale.')
    rel = package(unit, 'NS_Studio_CrystalFinaCasing')
    view = cave.private_level(source[AURA], '/Game/' + AURA, '/Game/' + rel)
    root_id, root = cave.export(view, Path(rel).name)
    emitters = [(i, e) for i, e in enumerate(view['Exports'], 1) if e['ObjectName'] == 'BrightSting_0']
    if len(emitters) != 1: raise ValueError('The native Fina CPU emitter changed.')
    emitter_id, emitter = emitters[0]
    version, = cave.property_data(emitter, 'VersionData')['Value']
    if cave.property_data(version, 'SimTarget')['Value'] != 'CPUSim':
        raise ValueError('The battle crystal requires a native CPU emitter.')
    for handle in cave.property_data(root, 'EmitterHandles')['Value']:
        instance = cave.property_data(handle, 'VersionedInstance')
        cave.set_value(handle, 'bIsEnabled', cave.property_data(instance, 'Emitter')['Value'] == emitter_id)
    renderers = cave.property_data(version, 'RendererProperties')['Value']
    if len(renderers) != 1: raise ValueError('The native Fina emitter renderer layout changed.')
    renderer_id = renderers[0]['Value']; renderer = view['Exports'][renderer_id - 1]
    if renderer['Extras']: raise ValueError('The native renderer gained opaque serialization.')
    guid = copy.deepcopy(cave.property_data(renderer, 'OuterEmitterVersion'))
    renderer.update(ObjectName='Studio_CrystalComponentRenderer',
                    ClassIndex=cave.script_import(view, 'Niagara', 'NiagaraComponentRendererProperties'),
                    TemplateIndex=cave.script_import(view, 'Niagara', 'Default__NiagaraComponentRendererProperties', 'NiagaraComponentRendererProperties'))
    renderer['SerializationBeforeCreateDependencies'] = [renderer['ClassIndex'], renderer['TemplateIndex']]
    renderer['CreateBeforeSerializationDependencies'] = []
    background = source[cave.TEST_BACKGROUND]
    donors = [(i, e) for i, e in enumerate(background['Exports'], 1) if any(
        p['Name'] == 'StaticMesh' and p['Value'] < 0
        and background['Imports'][-p['Value'] - 1]['ObjectName'] == Path(cave.TEST_NATIVE_MESH).name
        for p in e.get('Data', []) if isinstance(p, dict))]
    if len(donors) != 1: raise ValueError('The Sanctum crystal component changed.')
    old_id, donor = donors[0]
    component_id = cave.clone_graph(view, background, [old_id], {donor['OuterIndex']: renderer_id})[old_id]
    component = view['Exports'][component_id - 1]
    component['ObjectName'] = 'Studio_CrystalTemplate'
    component['ObjectFlags'] = 'RF_ArchetypeObject'
    mesh = '/Game/' + package(unit, 'SM_Studio_CrystalFina')
    material = '/Game/' + package(unit, 'MI_Studio_CrystalFina')
    cave.set_value(component, 'StaticMesh', cave.asset_import(view, cave.property_data(component, 'StaticMesh')['Value'], mesh))
    slot, = cave.property_data(component, 'OverrideMaterials')['Value']
    slot['Value'] = cave.asset_import(view, slot['Value'], material); slot['IsZero'] = False
    removed = {'AttachParent', 'CreationMethod', 'Mobility', 'BodyInstance', 'VisibilityId',
               'bIsValidTextureStreamingBuiltData', 'bVisible', 'bHiddenInGame'}
    component['Data'] = [p for p in component['Data'] if p['Name'] not in removed]
    p = cave.native_prop
    component['Data'] += [p('Mobility', 'Movable', 'EnumPropertyData', EnumType='EComponentMobility', InnerType='ByteProperty'),
        p('VisibilityId', -1, 'IntPropertyData'), p('bIsValidTextureStreamingBuiltData', False, 'BoolPropertyData'),
        p('bVisible', True, 'BoolPropertyData'), p('bHiddenInGame', False, 'BoolPropertyData'),
        cave.native_struct('BodyInstance', 'BodyInstance', [
            p('CollisionEnabled', 'NoCollision', 'EnumPropertyData', EnumType='ECollisionEnabled', InnerType='ByteProperty'),
            p('CollisionProfileName', 'NoCollision', 'NamePropertyData')])]
    _, native_mesh = cave.export(source[cave.TEST_NATIVE_MESH], Path(cave.TEST_NATIVE_MESH).name)
    origin = cave.property_data(cave.property_data(native_mesh, 'ExtendedBounds'), 'Origin')['Value'][0]['Value']
    for name, values in [('RelativeScale3D', dict.fromkeys(('X', 'Y', 'Z'), relative_scale)),
                         ('RelativeLocation', {axis: -float(origin[axis]) * relative_scale for axis in ('X', 'Y', 'Z')})]:
        cave.property_data(component, name)['Value'][0]['Value'].update(values)
    component['CreateBeforeSerializationDependencies'] = [cave.property_data(component, 'StaticMesh')['Value'], slot['Value']]
    renderer['Data'] = [p('ComponentType', cave.script_import(view, 'Engine', 'StaticMeshComponent')),
        p('ComponentCountLimit', 1, 'UInt32PropertyData'), p('bAssignComponentsOnParticleID', False, 'BoolPropertyData'),
        p('bCreateComponentFirstParticleFrame', True, 'BoolPropertyData'),
        p('bOnlyActivateNewlyAquiredComponents', False, 'BoolPropertyData'),
        p('TemplateComponent', component_id), p('PropertyBindings', [], 'ArrayPropertyData', ArrayType='StructProperty'),
        p('bIsEnabled', True, 'BoolPropertyData'), guid]
    renderer['CreateBeforeSerializationDependencies'] = [component_id, cave.property_data(renderer, 'ComponentType')['Value']]
    cave.names(view, [view['Imports'], view['Exports']])
    return rel, view


def table_rows(view):
    exports = [e for e in view['Exports'] if isinstance(e.get('Table'), dict)]
    if len(exports) != 1: raise ValueError('Expected one native battle data table.')
    return exports[0]['Table']['Data']


def soft_path(owner, name, path):
    value = cave.property_data(owner, name)
    value['Value']['AssetPath'].update(PackageName=path, AssetName=Path(path).name)
    value['Value']['SubPathString'] = None; value['IsZero'] = False


def effect_table(original, unit):
    """Add only this vision, retaining every other unit's native effect bundles."""
    view = copy.deepcopy(original); rows = table_rows(view)
    if any(cave.property_data(r, 'ID')['Value'] == unit['id'] or r['Name'] == unit['jp'] for r in rows):
        raise ValueError('Crystal Fina battle effect identity conflicts with an existing row.')
    donors = [r for r in rows if cave.property_data(r, 'ID')['Value'] == 400]
    if len(donors) != 1: raise ValueError('The native battle effect donor changed.')
    row = copy.deepcopy(donors[0]); row['Name'] = unit['jp']; cave.set_value(row, 'ID', unit['id'])
    bundles = cave.property_data(row, 'effectBundleList')
    template, = bundles['Value']; bundles['Value'] = []; bundles['IsZero'] = False
    for part, rel in [('NULL_Crystal', package(unit, 'NS_Studio_CrystalFinaCasing')), ('NULL_Aura', AURA)]:
        bundle = copy.deepcopy(template); bundle['Name'] = str(len(bundles['Value']))
        soft_path(bundle, 'niagaraAsset', '/Game/' + rel)
        cave.set_value(bundle, 'attachPartsName', part)
        rotation = cave.property_data(bundle, 'additionalRotation')
        rotation['Value'][0]['Value'].update(Pitch=0.0, Yaw=0.0, Roll=0.0); rotation['IsZero'] = False
        bundles['Value'].append(bundle)
    rows.append(row); cave.names(view, rows)
    return view


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
    native_effects = native('Datatable/' + EFFECT_TABLE)
    designs = env['rows'](DESIGN_TABLE)
    donor = [r for r in designs.values() if r.get('ID') == unit['donor']]
    if len(donor) != 1: raise ValueError('The Crystal Fina battle design donor is missing.')
    scale = float(donor[0]['Scale']); effect_scale = float(donor[0]['attachEffectSacle'])
    if not all(math.isfinite(s) and s > 0 for s in (scale, effect_scale)):
        raise ValueError('The native sprite/effect battle scales are invalid.')
    # Match the casing/body ratio approved in the field test. Battle sprite and
    # attachment scales are separate native design parameters.
    rel, system = casing_system(source, unit, cave.TEST_CRYSTAL_SCALE / cave.TEST_SPRITE_SCALE * scale / effect_scale)
    assets = {rel: system}
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
        assets[new] = result
    content = out / 'FFRS/Content'
    effects_path = content / ('Datatable/' + EFFECT_TABLE + '.uasset')
    assets['Datatable/' + EFFECT_TABLE] = effect_table(decode(effects_path, 'built-unit-effects') if effects_path.is_file() else native_effects, unit)
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
    for suffix, payload in [('_tex', 'tex.bgra'), ('_normal', 'normal.bc5'), ('_mreo', 'mreo.bgra')]:
        run(tool + ['make-texture', str(content / (old + suffix + '.uasset')), str(work / payload),
                    str(w), str(h), str(content / (rel + suffix + '.uasset')),
                    '/Game/' + old + suffix, '/Game/' + rel + suffix, rename, '--usmap', usmap])
    print('  Crystal Fina battle: native body; private rotating glass; intro aura; jacket-free seated resonance. Skills and hit events preserved.')
