"""Cosmetic field leader bank and owned UE4SS mod; never edits save/party identity."""
import base64
import copy
import hashlib
import json
import os
from pathlib import Path
import struct
import tempfile

TABLE = 'Asset/Map/DT_MapUnitAsset'
MOD = 'FFRStudioFieldLeader'
REL = 'FFRS/Binaries/Win64/ue4ss/Mods/' + MOD
STAGE = 'build/field-leader/payload.json'
STATE = 'field-leader-state.json'
DFINA = '/Game/Chara/StudioFieldLeader/pc0060'


def enabled(root):
    import _ffr_testing
    return _ffr_testing.settings(root)['fieldLeader']


def bank(units, rows):
    import _ffr_party
    import _ffr_overworld
    originals = rows(TABLE)
    models = {}
    for uid, jp, _, _ in _ffr_party.CHARACTERS:
        mid = (uid - 1000) * 10
        row = originals.get(jp, {})
        animations = row.get('animationAssetList', [])
        path = f'/Game/Chara/Field_Unit/pc{mid:04d}/pc{mid:04d}'
        if row.get('ID') != mid or not animations or animations[0].get('Ss6Project') != path:
            raise ValueError('The native field leader assets changed; prepare the game files again.')
        models[uid] = copy.deepcopy(animations[0])
        if uid == 1006: models[uid]['Ss6Project'] = DFINA
    for u in units:
        if u.get('party') and u.get('overworld'):
            _ffr_party.validate(u)
            for path, value in _ffr_overworld.updates(u).items():
                models[u['id']][path.split('.')[-1]] = value
    # Preserve all original indices, including story costumes and battle assets.
    changes = []; config = {'schema': 1, 'actors': {}}
    for uid, jp, _, _ in _ffr_party.CHARACTERS:
        mid = (uid - 1000) * 10
        source = copy.deepcopy(originals[jp]['animationAssetList'])
        # Other modules may replace only the primary field slot. Keep that choice.
        replacement = next((u for u in units if u.get('id') == uid and u.get('overworld')), None)
        if replacement:
            for path, value in _ffr_overworld.updates(replacement).items(): source[0][path.split('.')[-1]] = value
        slots = {str(id): len(source) + i for i, id in enumerate(models)}
        changes.append({'row': jp, 'set': {'animationAssetList': source + list(models.values())}})
        config['actors'][str(mid)] = slots
    return changes, config


def prepare(tables, units, root, rows):
    if not enabled(root): return
    changes, _ = bank(units, rows)
    table = tables.setdefault(TABLE, {'asset': 'FFRS/Content/Datatable/' + TABLE, 'add': [], 'set': []})
    table['set'].extend(changes)


def animation_payloads(animations, encoded, names):
    """Read the native pc0060 keyframe tail, separate from reflected properties.

    USs6Project::Serialize walks packs/animations/parts/attributes/keys and then
    FSsValue::Serialize. UAssetAPI preserves that stream as opaque Extras.
    Only the float, string and hash layouts present in this field asset are
    supported; reject changed layouts instead of shipping an unreadable asset.
    """
    data = base64.b64decode(encoded, validate=True); offset = 0
    def fail(): raise ValueError('Invalid or unsupported Dark Fina animation payload; field cycling cannot be built safely.')
    def take(count):
        nonlocal offset
        if not 0 <= count <= len(data) - offset: fail()
        result = data[offset:offset + count]; offset += count
        return result
    def value(kind):
        if kind == 'FloatType': take(4)
        elif kind == 'StringType':
            length = struct.unpack('<i', take(4))[0]
            if not 0 < abs(length) <= 65536: fail()
            text = take(length if length > 0 else -length * 2)
            if not text.endswith(b'\0' if length > 0 else b'\0\0'): fail()
        elif kind == 'HashType':
            count = struct.unpack('<i', take(4))[0]
            if not 0 <= count <= 1024: fail()
            for _ in range(count):
                index, number = struct.unpack('<ii', take(8))
                if not 0 <= index < len(names) or number < 0: fail()
                # Native unversioned FSsValue: all 4 properties, only Type
                # nonzero. The 3 temporary scalar properties are zero-masked.
                if take(3) != b'\x80\x09\x0e': fail()
                child = {1: 'StringType', 3: 'FloatType'}.get(take(1)[0])
                if child is None: fail()
                value(child)
        else: fail()
    def field(properties, name): return next(p['Value'] for p in properties if p['Name'] == name)
    result = []
    for animation in animations:
        start = offset
        for part in field(animation['Value'], 'PartAnimes'):
            for attribute in field(part['Value'], 'Attributes'):
                for key in field(attribute['Value'], 'Key'):
                    value(field(field(key['Value'], 'Value'), 'Type'))
        result.append(data[start:offset])
    if offset != len(data): fail()
    return result


def dark_fina_aliases(view):
    """Private copy: diagonal idle aliases use the game's own cardinal poses."""
    view = copy.deepcopy(view)
    project = view['Exports'][0]
    packs = next(p for p in project['Data'] if p['Name'] == 'AnimeList')['Value']
    if len(packs) != 1 or any(p['Name'] == 'EffectList' and p['Value'] for p in project['Data']):
        raise ValueError('Unsupported Dark Fina animation packs; field cycling cannot be built safely.')
    animations = next(p for p in packs[0]['Value'] if p['Name'] == 'AnimeList')['Value']
    def name(a): return next(p for p in a['Value'] if p['Name'] == 'AnimationName')
    by_name = {name(a)['Value']: a for a in animations}
    payloads = animation_payloads(animations, project['Extras'], view['NameMap'])
    by_payload = dict(zip(by_name, payloads))
    if not {'idle2', 'idle4', 'idle6', 'idle8'} <= by_name.keys():
        raise ValueError('Dark Fina lacks the expected native idle poses.')
    for destination, source in [('idle1', 'idle2'), ('idle3', 'idle2'), ('idle7', 'idle8'), ('idle9', 'idle8')]:
        if destination in by_name: continue
        alias = copy.deepcopy(by_name[source]); alias['Name'] = str(len(animations))
        name(alias)['Value'] = destination; animations.append(alias)
        payloads.append(by_payload[source])
        if destination not in view['NameMap']: view['NameMap'].append(destination)
    project['Extras'] = base64.b64encode(b''.join(payloads)).decode('ascii')
    animation_payloads(animations, project['Extras'], view['NameMap'])
    old = '/Game/Chara/Field_Unit/pc0060/pc0060'
    def rename(value):
        if isinstance(value, str): return DFINA if value == old else value
        if isinstance(value, list): return [rename(v) for v in value]
        if isinstance(value, dict): return {k: rename(v) for k, v in value.items()}
        return value
    view = rename(view)
    # IoStore resolves export names through this prefix of the legacy name map.
    # Include the new aliases so they retain names after container conversion.
    view['NamesReferencedFromExportDataCount'] = len(view['NameMap'])
    return view


def build(units, env):
    root = Path(env['ROOT']); work = root / 'build/field-leader'; work.mkdir(parents=True, exist_ok=True)
    payload = {'schema': 1, 'files': {}}
    if enabled(root):
        _, config = bank(units, env['rows'])
        payload['files'] = {'enabled.txt': '', 'Scripts/config.lua': 'return ' + lua(config) + '\n',
                            'Scripts/main.lua': Path(__file__).with_name('field_leader.lua').read_text(encoding='utf-8')}
        legacy = Path(env['LEGACY']); relative = 'FFRS/Content/Chara/Field_Unit/pc0060/pc0060.uasset'
        source = legacy / relative
        if not source.is_file():
            env['run'](env['ffrenv'].py(str(root / 'tools/extract_legacy.py'), '--filter', 'Chara/Field_Unit/pc0060/'))
        original = work / 'dark-fina-original.json'; edited = work / 'dark-fina.json'
        env['run'](env['FFRDT'] + ['tojson', str(source), str(original), '--usmap', env['USMAP']])
        edited.write_text(json.dumps(dark_fina_aliases(json.loads(original.read_text(encoding='utf-8-sig')))), encoding='utf-8')
        target = Path(env['OUT']) / ('FFRS/Content/' + DFINA.removeprefix('/Game/') + '.uasset')
        target.parent.mkdir(parents=True, exist_ok=True)
        env['run'](env['FFRDT'] + ['fromjson', str(edited), str(target), '--usmap', env['USMAP']])
    atomic(work / 'payload.json', json.dumps(payload).encode())


def lua(value):
    if isinstance(value, dict): return '{' + ','.join('[' + json.dumps(k) + ']=' + lua(v) for k, v in value.items()) + '}'
    if type(value) is int: return str(value)
    raise ValueError('Unsupported field leader runtime configuration.')


def atomic(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix='field-leader-', dir=path.parent)
    try:
        with os.fdopen(fd, 'wb') as f: f.write(data); f.flush(); os.fsync(f.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary): os.unlink(temporary)


def checked(root, relative):
    root = Path(root).absolute(); path = root / relative
    if not path.resolve().is_relative_to(root.resolve()) or any(p.is_symlink() or
            (hasattr(p, 'is_junction') and p.is_junction()) for p in (path, *path.parents)):
        raise RuntimeError('Field leader runtime paths must stay inside their folder without links.')
    return path


def install_plan(root, game, payload=None):
    """Preflight before any game packages change; use the BUILT configuration."""
    root = Path(root); game = Path(game)
    if payload is None:
        stage = root / STAGE
        payload = json.loads(stage.read_bytes()) if stage.is_file() else {'schema': 1, 'files': {}}
    allowed = {'enabled.txt', 'Scripts/config.lua', 'Scripts/main.lua'}
    if (payload.get('schema') != 1 or set(payload.get('files', {})) not in (set(), allowed)
            or any(not isinstance(v, str) for v in payload['files'].values())):
        raise RuntimeError('Invalid built field leader payload; rebuild before installing.')
    state = checked(root, STATE)
    previous = json.loads(state.read_bytes()) if state.is_file() else {'schema': 1, 'files': {}, 'game': str(game)}
    if previous.get('schema') != 1 or set(previous.get('files', {})) - allowed:
        raise RuntimeError('Unknown field leader ownership record.')
    if previous['files'] and Path(previous['game']).resolve() != game.resolve():
        raise RuntimeError('Restore the field leader runtime in the previous game folder first.')
    before = {}; changes = {}
    for relative in allowed:
        path = checked(game, REL + '/' + relative)
        current = path.read_bytes() if path.is_file() else None
        known = previous['files'].get(relative)
        if current is not None and hashlib.sha256(current).hexdigest() != known:
            raise RuntimeError('Preserving an unowned or edited field leader file: ' + str(path))
        before[relative] = current
        changes[relative] = payload['files'][relative].encode('utf-8') if relative in payload['files'] else None
    if payload['files']:
        binary = checked(game, 'FFRS/Binaries/Win64')
        if not (binary / 'dwmapi.dll').is_file() or not (binary / 'ue4ss/UE4SS.dll').is_file():
            raise RuntimeError('Field cycling requires the working UE4SS loader from the runtime-reference helper. Prepare it first, or turn cycling off.')
    return {'root': root, 'game': game, 'before': before, 'changes': changes, 'state': state,
            'previous': state.read_bytes() if state.is_file() else None}


def deploy(plan, backup=None):
    changes = plan['changes']; before = plan['before']; game = plan['game']
    if backup:
        payload = {'schema': 1, 'files': {k: v.decode('utf-8') for k, v in before.items() if v is not None}}
        # The engine restores every file inside its pak backup directory to
        # ~mods. Keep runtime snapshots separate so no JSON is copied there.
        atomic(checked(plan['root'], 'field-leader-backups/' + Path(backup).name + '.json'), json.dumps(payload).encode())
    written = []
    try:
        # Disable first; publish enabled.txt last after its scripts are in place.
        for relative in ('enabled.txt', 'Scripts/config.lua', 'Scripts/main.lua'):
            path = checked(game, REL + '/' + relative)
            if (path.read_bytes() if path.is_file() else None) != before[relative]:
                raise RuntimeError('The field leader runtime changed during installation.')
        checked(game, REL + '/enabled.txt').unlink(missing_ok=True)
        for relative in ('Scripts/config.lua', 'Scripts/main.lua', 'enabled.txt'):
            path = checked(game, REL + '/' + relative)
            written.append(relative)
            if changes[relative] is None: path.unlink(missing_ok=True)
            else: atomic(path, changes[relative])
        atomic(plan['state'], json.dumps({'schema': 1, 'game': str(game), 'files': {
            k: hashlib.sha256(v).hexdigest() for k, v in changes.items() if v is not None}}).encode())
    except BaseException:
        for relative in set(written) | {'enabled.txt'}:
            path = checked(game, REL + '/' + relative)
            if before[relative] is None: path.unlink(missing_ok=True)
            else: atomic(path, before[relative])
        if plan['previous'] is None: plan['state'].unlink(missing_ok=True)
        else: atomic(plan['state'], plan['previous'])
        raise


def restore_plan(root, game, backup=None):
    path = checked(root, 'field-leader-backups/' + backup + '.json') if backup else None
    payload = json.loads(path.read_bytes()) if path and path.is_file() else {'schema': 1, 'files': {}}
    return install_plan(root, game, payload)
