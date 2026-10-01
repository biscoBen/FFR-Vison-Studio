"""Apply Crystal Fina's material to the current build, never a saved whole table."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile

VERSION = '1.1.1'
STATE = '.ffr-crystalfina'
SPRITE_ID = '99887755552703'
VISION_ID = 13503
TABLE = 'FFRS/Content/Datatable/Asset/Battle/Unit/DT_BtlUnitAsset'
MATERIAL = '/Game/BP/Map/Unit/Material/M_CrystalFina_AlphaTest_13503'
ASSET = 'FFRS/Content/BP/Map/Unit/Material/M_CrystalFina_AlphaTest_13503'
MATERIAL_FILES = tuple('material/' + ASSET + ext for ext in ('.uasset', '.uexp'))


def fail(message):
    raise RuntimeError('Crystal Fina transparency: ' + message)


def target_unit(units):
    targets = []
    for unit in units:
        ffbe = unit.get('ffbe') or {}
        if str(ffbe.get('id')) == SPRITE_ID or str(ffbe.get('base')) == SPRITE_ID:
            targets.append(unit)
    if not targets:
        return None
    if len(targets) != 1:
        fail('the custom sprite appears on multiple visions; refusing an ambiguous material assignment.')
    unit = targets[0]
    native = unit.get('native')
    baseline = native.get('baseline') if isinstance(native, dict) else None
    original = (isinstance(native, dict) and isinstance(baseline, dict)
                and native.get('version') == 1 and native.get('id') == unit.get('id')
                and baseline.get('id') == unit.get('id') and unit.get('donor') == unit.get('id'))
    if type(unit.get('id')) is not int or unit['id'] <= 0 or (unit['id'] < 13100 and not original):
        fail('the custom vision has an invalid game ID.')
    if (unit.get('ffbe') or {}).get('source') != 'CUSTOM':
        fail('the matching sprite is no longer a custom source; refusing to change an unrelated vision.')
    if sum(u.get('id') == unit['id'] for u in units) != 1:
        fail('duplicate vision ID ' + str(unit['id']) + ' in this roster.')
    return unit


def checked(root, relative):
    root = Path(root).absolute()
    for parent in (root, *root.parents):
        if parent.is_symlink() or (hasattr(parent, 'is_junction') and parent.is_junction()):
            fail('material or output root is a link/junction; no files copied.')
    root = root.resolve()
    path = root
    for part in Path(relative).parts:
        if part in ('..', '.') or Path(part).is_absolute():
            fail('invalid material path.')
        path = path / part
        if path.is_symlink() or (hasattr(path, 'is_junction') and path.is_junction()):
            fail('material or output path is a link/junction; no files copied.')
    if not path.resolve().is_relative_to(root):
        fail('material path escapes the selected engine.')
    return path


def materials(root):
    engine = Path(root).resolve()
    private = engine / STATE
    try:
        manifest = json.loads(checked(private, 'manifest.json').read_text(encoding='utf-8'))
        files = manifest['files']
        if manifest.get('schema') != 1 or set(files) != {'_ffr_crystalfina.py', *MATERIAL_FILES}:
            fail('unsupported material manifest; reapply the complete patch package.')
        helper = checked(engine, 'tools/_ffr_crystalfina.py')
        if hashlib.sha256(helper.read_bytes()).hexdigest() != files['_ffr_crystalfina.py']:
            fail('the helper changed after installation; reapply a verified patch package.')
        result = []
        for rel in MATERIAL_FILES:
            source = checked(private, rel)
            if hashlib.sha256(source.read_bytes()).hexdigest() != files[rel]:
                fail('material checksum mismatch: ' + rel)
            result.append((source, rel.removeprefix('material/')))
        return result
    except (OSError, ValueError, KeyError, TypeError) as exc:
        fail('material files are missing or invalid; reapply the patch. ' + str(exc))


def check_old_overlay(root):
    config = Path(root) / 'config.json'
    if not config.is_file():
        return
    try:
        game = json.loads(config.read_text(encoding='utf-8')).get('gameRoot')
    except (ValueError, OSError) as exc:
        fail('cannot check the configured game for the old conflicting patch: ' + str(exc))
    if game:
        mods = Path(game) / 'FFRS/Content/Paks/~mods'
        if any((mods / ('zzz_CrystalFina_AlphaFlagTest_999_P' + ext)).exists()
               for ext in ('.utoc', '.ucas', '.pak')):
            fail('the old AlphaFlagTest_999_P overlay is still installed. Disable it; it overrides new vision entries.')


def prepare(patch, units, root):
    unit = target_unit(units)
    if unit is None:
        return
    check_old_overlay(root)
    vid = unit['id']
    material = MATERIAL.replace(str(VISION_ID), str(vid))
    materials(root)
    out = Path(root).resolve() / 'build/visions_mod/assets'
    if Path(patch.get('outRoot', '')).resolve() != out:
        fail('builder output location changed; refusing an unfamiliar build layout.')
    tables = [table for table in patch.get('tables', []) if table.get('asset') == TABLE]
    if len(tables) != 1:
        fail('expected one freshly generated battle asset table.')
    table = tables[0]
    added = table.get('add', [])
    # Verify every current vision is represented before changing Fina's two fields.
    for roster_unit in units:
        matches = [row for row in added if row.get('set', {}).get('ID') == roster_unit.get('id')]
        if len(matches) != 1:
            fail('fresh battle table is missing or duplicates vision ' + str(roster_unit.get('id')))
    rows = [row for row in added if row.get('set', {}).get('ID') == vid]
    row = rows[0]
    if row.get('row') != unit.get('jp'):
        fail('the matching table row does not belong to the custom Crystal Fina.')
    overrides = row['set']
    material_key = 'animationAssetList[0].Material'
    flag_key = 'animationAssetList[0].isVisionCharacter'
    if (material_key in overrides and overrides[material_key] not in
            (material, '/Game/BP/Map/Unit/Material/CharaPBR/M_Ss_Component_PBRBattle')):
        fail('this builder already assigns a different custom material; refusing to replace it.')
    if flag_key in overrides and not isinstance(overrides[flag_key], bool):
        fail('the builder sprite flag has an unfamiliar format.')
    expected = f'/Game/Chara/summon/summon{vid}/summon{vid}'
    if (overrides.get('animationAssetList[0].Ss6Project') != expected
            or overrides.get('animationAssetList[0].textureBaseColor') != expected + '_tex'):
        fail('Crystal Fina sprite/texture paths changed; material reference would be incorrect.')
    overrides['animationAssetList[0].isVisionCharacter'] = False
    overrides['animationAssetList[0].Material'] = material
    print(f'  Crystal Fina transparency: applied to current vision {vid}; all roster rows retained.')


def run_asset_tool(root, args):
    # Use the current engine's serializer, retaining its name map indices and
    # opaque cooked export bytes. Never patch asset bytes with string replacement.
    import ffrenv
    mapping = Path(root) / 'extracted/Mappings.usmap'
    command = list(ffrenv.FFRDT) + args
    if mapping.is_file():
        command += ['--usmap', str(mapping)]
    result = subprocess.run(command, capture_output=True, text=True, encoding='utf-8', errors='replace')
    if result.returncode:
        fail('material serialization failed: ' + (result.stderr or result.stdout)[-1500:])


def verify_material_view(view, vid):
    name = f'M_CrystalFina_AlphaTest_{vid}'
    texture = f'summon{vid}_tex'
    package = f'/Game/Chara/summon/summon{vid}/{texture}'
    imports = view.get('Imports', [])
    packages = [i + 1 for i, item in enumerate(imports)
                if item.get('ObjectName') == package and item.get('ClassName') == 'Package']
    if len(packages) != 1 or not any(item.get('ObjectName') == texture and
                                    item.get('ClassName') == 'Texture2D' and
                                    item.get('OuterIndex') == -packages[0] for item in imports):
        fail('material texture import does not target the allocated vision.')
    if len(view.get('Exports', [])) != 1 or view['Exports'][0].get('ObjectName') != name:
        fail('material export does not match the allocated vision.')
    if not any(item.get('ObjectName') == '/SpriteStudio6/Function/MF_Ss6_PartColorInv' for item in imports):
        fail('the sprite material function import was lost.')


def retarget_material(root, sources, vid):
    private = checked(Path(root) / STATE, f'generated/{vid}')
    private.mkdir(parents=True, exist_ok=True)
    # A private staging directory prevents an interrupted serializer run being
    # mistaken for a complete material. Regenerate through the current tool.
    with tempfile.TemporaryDirectory(prefix='material-', dir=private) as temporary:
        folder = Path(temporary)
        original_json = folder / 'original.json'
        edited_json = folder / 'edited.json'
        output = folder / f'M_CrystalFina_AlphaTest_{vid}.uasset'
        roundtrip = folder / 'roundtrip.json'
        run_asset_tool(root, ['tojson', str(sources[0][0]), str(original_json)])
        original = json.loads(original_json.read_text(encoding='utf-8-sig'))
        verify_material_view(original, VISION_ID)
        names = [f'M_CrystalFina_AlphaTest_{VISION_ID}', MATERIAL,
                 f'summon{VISION_ID}_tex', f'/Game/Chara/summon/summon{VISION_ID}/summon{VISION_ID}_tex']
        replacements = {name: name.replace(str(VISION_ID), str(vid)) for name in names}
        def rename(value):
            if isinstance(value, str): return replacements.get(value, value)
            if isinstance(value, list): return [rename(item) for item in value]
            if isinstance(value, dict): return {key: rename(item) for key, item in value.items()}
            return value
        edited = rename(original)
        edited_json.write_text(json.dumps(edited, ensure_ascii=False), encoding='utf-8')
        run_asset_tool(root, ['fromjson', str(edited_json), str(output)])
        run_asset_tool(root, ['tojson', str(output), str(roundtrip)])
        result = json.loads(roundtrip.read_text(encoding='utf-8-sig'))
        verify_material_view(result, vid)
        if any(name in result.get('NameMap', []) for name in names):
            fail('material retained an old package or texture name.')
        if output.with_suffix('.uexp').read_bytes() != sources[1][0].read_bytes():
            fail('the serializer changed the cooked material export payload.')
        for field in ('Data', 'Extras'):
            if result['Exports'][0].get(field) != original['Exports'][0].get(field):
                fail('the serializer changed the material shader/export data.')
        result_files = []
        for suffix in ('.uasset', '.uexp'):
            source = output.with_suffix(suffix)
            destination = checked(private, source.name)
            shutil.copyfile(source, destination)
            result_files.append((destination, ASSET.replace(str(VISION_ID), str(vid)) + suffix))
        return result_files


def copy_material(root, out, units):
    unit = target_unit(units)
    if unit is None:
        return
    engine = Path(root).resolve()
    expected = engine / 'build/visions_mod/assets'
    if Path(out).resolve() != expected:
        fail('builder output location changed; material was not copied.')
    sources = materials(root)
    if unit['id'] != VISION_ID:
        sources = retarget_material(root, sources, unit['id'])
    destinations = []
    for source, rel in sources:
        destination = checked(expected, rel)
        if destination.exists() and destination.read_bytes() != source.read_bytes():
            fail('another asset already uses the custom material path; refusing to overwrite it.')
        destinations.append((source, destination))
    for source, destination in destinations:
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)
        if destination.read_bytes() != source.read_bytes():
            fail('copied material verification failed; build stopped before packing.')
    print('  Crystal Fina transparency: original verified material included in this Studio mod.')
