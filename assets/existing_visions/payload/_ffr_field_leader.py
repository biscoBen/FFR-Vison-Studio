"""Cosmetic field leader bank and owned UE4SS mod; never edits save/party identity."""
import base64
import copy
import hashlib
import json
import math
import os
from pathlib import Path
import re
import struct
import tempfile

TABLE = 'Asset/Map/DT_MapUnitAsset'
MOD = 'FFRStudioFieldLeader'
REL = 'FFRS/Binaries/Win64/ue4ss/Mods/' + MOD
STAGE = 'build/field-leader/payload.json'
STATE = 'field-leader-state.json'
DFINA = '/Game/Chara/StudioFieldLeader/pc0060'
DIRECTIONS = (1, 2, 3, 4, 6, 7, 8, 9)


def package(mid): return f'/Game/Chara/StudioFieldLeader/pc{mid:04d}'


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
        if uid != 1001: models[uid]['Ss6Project'] = package(mid)
    for u in units:
        if u.get('party') and u.get('overworld'):
            _ffr_party.validate(u)
            for path, value in _ffr_overworld.updates(u).items():
                models[u['id']][path.split('.')[-1]] = value
    # Preserve all original indices, including story costumes and battle assets.
    changes = []; config = {'schema': 1, 'cycling': 1, 'actors': {}, 'defaults': {}}
    for uid, jp, _, _ in _ffr_party.CHARACTERS:
        mid = (uid - 1000) * 10
        source = copy.deepcopy(originals[jp]['animationAssetList'])
        # The game owns the complete native prefix, including primary idle.
        # Saved walking choices exist only in the appended cosmetic bank.
        replacement = next((u for u in units if u.get('id') == uid and u.get('overworld')), None)
        slots = {str(id): len(source) + i for i, id in enumerate(models)}
        changes.append({'row': jp, 'set': {'animationAssetList': source + list(models.values())}})
        config['actors'][str(mid)] = slots
        config['defaults'][str(mid)] = slots[str(uid)] if replacement else 0
    return changes, config


def prepare(tables, units, root, rows):
    if not enabled(root): return
    changes, _ = bank(units, rows)
    table = tables.setdefault(TABLE, {'asset': 'FFRS/Content/Datatable/' + TABLE, 'add': [], 'set': []})
    table['set'].extend(changes)


def animation_payloads(animations, encoded, names, cells=None):
    """Read native field keyframe tails, separate from reflected properties.

    USs6Project::Serialize walks packs/animations/parts/attributes/keys and then
    FSsValue::Serialize. UAssetAPI preserves that stream as opaque Extras.
    Only the float, string and hash layouts present in this field asset are
    supported; reject changed layouts instead of shipping an unreadable asset.
    """
    data = base64.b64decode(encoded, validate=True); offset = 0
    def fail(): raise ValueError('Invalid or unsupported field animation payload; field cycling cannot be built safely.')
    def take(count):
        nonlocal offset
        if not 0 <= count <= len(data) - offset: fail()
        result = data[offset:offset + count]; offset += count
        return result
    def value(kind):
        if kind == 'FloatType': return struct.unpack('<f', take(4))[0]
        elif kind == 'StringType':
            length = struct.unpack('<i', take(4))[0]
            if not 0 < abs(length) <= 65536: fail()
            text = take(length if length > 0 else -length * 2)
            if not text.endswith(b'\0' if length > 0 else b'\0\0'): fail()
            return text[:-1].decode('utf-8') if length > 0 else text[:-2].decode('utf-16-le')
        elif kind == 'HashType':
            count = struct.unpack('<i', take(4))[0]
            if not 0 <= count <= 1024: fail()
            result = {}
            for _ in range(count):
                index, number = struct.unpack('<ii', take(8))
                if not 0 <= index < len(names) or number < 0: fail()
                # Native unversioned FSsValue: all 4 properties, only Type
                # nonzero. The 3 temporary scalar properties are zero-masked.
                if take(3) != b'\x80\x09\x0e': fail()
                child = {1: 'StringType', 3: 'FloatType'}.get(take(1)[0])
                if child is None: fail()
                key = names[index] + ('_' + str(number - 1) if number else '')
                result[key] = value(child)
            return result
        else: fail()
    def field(properties, name): return next(p['Value'] for p in properties if p['Name'] == name)
    result = []
    for animation in animations:
        start = offset; references = []
        for part in field(animation['Value'], 'PartAnimes'):
            for attribute in field(part['Value'], 'Attributes'):
                for key in field(attribute['Value'], 'Key'):
                    decoded = value(field(field(key['Value'], 'Value'), 'Type'))
                    if cells is not None and field(attribute['Value'], 'Tag') == 'Cell':
                        if not isinstance(decoded, dict) or set(decoded) != {'mapId', 'name'}: fail()
                        references.append((decoded['mapId'], decoded['name']))
        result.append(data[start:offset])
        if cells is not None: cells.append(references)
    if offset != len(data): fail()
    return result


def field_aliases(view, mid, *, target_package=None, source_package=None, walk_run_fallback=False):
    """Private player-compatible clips; keep genuine usable diagonals intact."""
    view = copy.deepcopy(view)
    project = view['Exports'][0]
    packs = next(p for p in project['Data'] if p['Name'] == 'AnimeList')['Value']
    if len(packs) != 1 or any(p['Name'] == 'EffectList' and p['Value'] for p in project['Data']):
        raise ValueError('Unsupported field animation packs; field cycling cannot be built safely.')
    animations = next(p for p in packs[0]['Value'] if p['Name'] == 'AnimeList')['Value']
    def name(a): return next(p for p in a['Value'] if p['Name'] == 'AnimationName')
    by_name = {name(a)['Value']: a for a in animations}
    if len(by_name) != len(animations): raise ValueError('Duplicate field animation names.')
    references = []
    payloads = animation_payloads(animations, project['Extras'], view['NameMap'], references)
    by_payload = dict(zip(by_name, payloads))
    def field(properties, key): return next(p['Value'] for p in properties if p['Name'] == key)
    maps = field(project['Data'], 'CellmapList')
    cells = []
    for cellmap in maps:
        lookup = {}
        for cell in field(cellmap['Value'], 'Cells'):
            size = field(cell['Value'], 'Size')
            vector = size[0]['Value'] if size else {}
            lookup[field(cell['Value'], 'CellName')] = float(vector.get('X', 0)) > 0 and float(vector.get('Y', 0)) > 0
        cells.append(lookup)
    def drawable(refs):
        return bool(refs) and all(type(index) in (int, float) and index == int(index)
            and 0 <= index < len(cells) and cells[int(index)].get(cell, False) for index, cell in refs)
    usable = {n: drawable(refs) for n, refs in zip(by_name, references)}
    aliases = []
    for motion in ('idle', 'move', 'dash'):
        for direction in (2, 4, 6, 8):
            destination=f'{motion}{direction}'
            if not usable.get(destination):
                # Native NPCs can have a walk family without a distinct dash.
                # Reuse an actual drawable walk; never invent empty clips.
                donors = ([f'walk{direction}',f'dash{direction}'] if motion=='move'
                          else [f'move{direction}',f'walk{direction}'] if motion=='dash' else [])
                source=next((n for n in donors if usable.get(n)),None) if walk_run_fallback else None
                if source is None:raise ValueError(f'Native field clip {destination} has no usable sprite cells.')
                aliases.append((destination,source));usable[destination]=True
        for direction, fallback in ((1, 2), (3, 2), (7, 8), (9, 8)):
            destination = f'{motion}{direction}'
            if not usable.get(destination): aliases.append((destination, f'{motion}{fallback}'))
    # Rain's controller can request this longer overworld idle family when
    # displaying another party member, which originally has only idleN clips.
    aliases.extend((f'fieldidle{d}', f'idle{d}') for d in DIRECTIONS if not usable.get(f'fieldidle{d}'))
    for destination, source in aliases:
        alias = copy.deepcopy(by_name[source])
        if destination in by_name:
            index = animations.index(by_name[destination]); alias['Name'] = animations[index]['Name']
            animations[index] = alias; payloads[index] = by_payload[source]
        else:
            alias['Name'] = str(len(animations)); animations.append(alias); payloads.append(by_payload[source])
        name(alias)['Value'] = destination
        by_name[destination] = alias; by_payload[destination] = by_payload[source]
        if destination not in view['NameMap']: view['NameMap'].append(destination)
    project['Extras'] = base64.b64encode(b''.join(payloads)).decode('ascii')
    animation_payloads(animations, project['Extras'], view['NameMap'])
    old = source_package or f'/Game/Chara/Field_Unit/pc{mid:04d}/pc{mid:04d}'
    def rename(value):
        if isinstance(value, str): return (target_package or package(mid)) if value == old else value
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
    import _ffr_fina_battle as fina
    selected = fina.selected(units, root)
    field = enabled(root)
    walking = any(u.get('party') and u.get('overworld') for u in units)
    import _ffr_esper_mastery
    espers = _ffr_esper_mastery.enabled(units)
    import _ffr_testing
    encounters = _ffr_testing.settings(root)['noEncounters']
    if field or walking or selected or espers or encounters:
        import _ffr_overworld
        config = bank(units, env['rows'])[1] if field else _ffr_overworld.runtime_config(units, env['rows'])
        code = ''
        if encounters:
            config['encounterToggle'] = 1
            code += '(function()\n' + Path(__file__).with_name('encounter_toggle.lua').read_text(encoding='utf-8') + '\nend)();\n'
        if espers:
            config['esperMastery'] = 1
            # A newline does not terminate a Lua call. The next parenthesized
            # block would call this nil result and abort the entire mod startup.
            code += '(function()\n' + Path(__file__).with_name('esper_mastery.lua').read_text(encoding='utf-8') + '\nend)();\n'
        if selected:
            native = json.loads((root / 'build/crystal-fina-battle/runtime.json').read_bytes())
            if native.get('schema') != 1 or native.get('id') != selected['id']:
                raise ValueError('Rebuild Crystal Fina battle assets before staging her runtime.')
            import _ffr_fina_cinematic
            native.pop('cinematicMovie', None)
            if any(u['id']==selected['id'] for u in _ffr_fina_cinematic.selected(units, root)):
                native['cinematicMovie'] = _ffr_fina_cinematic.PRIVATE.replace('FFRS/Content/', '/Game/')
            config['fina'] = native
            code += '(function()\n' + Path(__file__).with_name('fina_battle.lua').read_text(encoding='utf-8') + '\nend)();\n'
        if field or walking: code += Path(__file__).with_name('field_leader.lua').read_text(encoding='utf-8')
        payload['files'] = {'enabled.txt': '', 'Scripts/config.lua': 'return ' + lua(config) + '\n', 'Scripts/main.lua': code}
    if field:
        for mid in range(20, 81, 10):
            source = Path(env['LEGACY']) / f'FFRS/Content/Chara/Field_Unit/pc{mid:04d}/pc{mid:04d}.uasset'
            if not source.is_file():
                env['run'](env['ffrenv'].py(str(root / 'tools/extract_legacy.py'), '--filter', f'Chara/Field_Unit/pc{mid:04d}/'))
            original = work / f'pc{mid:04d}-original.json'; edited = work / f'pc{mid:04d}.json'
            env['run'](env['FFRDT'] + ['tojson', str(source), str(original), '--usmap', env['USMAP']])
            edited.write_text(json.dumps(field_aliases(json.loads(original.read_text(encoding='utf-8-sig')), mid)), encoding='utf-8')
            target = Path(env['OUT']) / ('FFRS/Content/' + package(mid).removeprefix('/Game/') + '.uasset')
            target.parent.mkdir(parents=True, exist_ok=True)
            env['run'](env['FFRDT'] + ['fromjson', str(edited), str(target), '--usmap', env['USMAP']])
    atomic(work / 'payload.json', json.dumps(payload).encode())


def lua(value):
    if isinstance(value, (list, tuple)): return '{' + ','.join(lua(v) for v in value) + '}'
    if isinstance(value, dict): return '{' + ','.join('[' + json.dumps(k) + ']=' + lua(v) for k, v in value.items()) + '}'
    if type(value) is str: return json.dumps(value, ensure_ascii=False)
    if type(value) in (int, float) and math.isfinite(value): return repr(value)
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


def game_key(game):
    return os.path.normcase(str(Path(game).resolve()))


def state_path(root, game, filename):
    """Keep the legacy ledger with its original game; scope later installations."""
    legacy = checked(root, filename)
    if not game: return legacy
    key = game_key(game)
    scoped = checked(root, 'game-installs/' + hashlib.sha256(key.encode()).hexdigest() + '/' + filename)
    if scoped.is_file(): return scoped
    owners = set()
    if legacy.is_file():
        value = json.loads(legacy.read_bytes())
        if value.get('game'): owners.add(game_key(value['game']))
        owners.update(game_key(v['game']) for v in value.get('installs', []) if v.get('game'))
    # An older package ledger can be absent, or omit its game on restore entries.
    # The legacy runtime ledger still identifies its installation.
    if not owners:
        runtime = checked(root, STATE)
        if runtime.is_file():
            value = json.loads(runtime.read_bytes())
            if value.get('game'): owners.add(game_key(value['game']))
    if not owners or owners == {key}: return legacy
    scoped.parent.mkdir(parents=True, exist_ok=True)
    return scoped


def game_state_path(root, game):
    return str(state_path(root, game, 'game_state.json'))


def backup_root(root, game):
    return str(checked(state_path(root, game, 'game_state.json').parent, 'backups'))


def runtime_backup(root, game, name):
    return checked(state_path(root, game, STATE).parent, 'field-leader-backups/' + name + '.json')


def loader_plan(root, game, previous, enabled, allow_bundle=True):
    """Preserve existing loaders; copy a managed core or the opted-in bundle."""
    import _ffr_deck_sync as sync
    owned = previous.get('loader', {})
    if (not isinstance(owned, dict) or any(not sync.allowed(k) or k in sync.PAKS + sync.LEADER_FILES
            or not isinstance(v, str) or not re.fullmatch('[0-9a-f]{64}', v) for k, v in owned.items())):
        raise RuntimeError('Unknown Studio loader ownership record.')
    before = {}; changes = {}
    for relative, digest in owned.items():
        path = checked(game, relative)
        raw = path.read_bytes() if path.is_file() else None
        if raw is not None and hashlib.sha256(raw).hexdigest() != digest:
            raise RuntimeError('Preserving an edited Studio loader file: ' + str(path))
        before[relative] = raw
        if not enabled: changes[relative] = None
    if not enabled: return before, changes, {}
    required = sync.LOADER_FILES[:2]
    if all(checked(game, name).is_file() for name in required): return before, changes, owned
    candidates = [checked(root, STATE), *sorted(checked(root, 'game-installs').glob('*/' + STATE))]
    for record in candidates:
        if not record.is_file(): continue
        original = json.loads(record.read_bytes())
        if original.get('schema') != 1 or not original.get('files') or not original.get('game'): continue
        source = Path(original['game'])
        if game_key(source) == game_key(game): continue
        if not all(checked(source, name).is_file() for name in sync.REQUIRED_LOADER): continue
        names = [name for name in sync.LOADER_FILES if checked(source, name).is_file()]
        signatures = checked(source, sync.BINARY + 'ue4ss/UE4SS_Signatures')
        if signatures.is_dir():
            names.extend(p.relative_to(source).as_posix() for p in sorted(signatures.iterdir())
                         if p.is_file() and sync.allowed(p.relative_to(source).as_posix()))
        copied = dict(owned)
        for relative in names:
            raw = checked(source, relative).read_bytes()
            if not raw: raise RuntimeError('The previous installation has an empty loader file: ' + relative)
            target = checked(game, relative)
            current = target.read_bytes() if target.is_file() else None
            if current is not None and current != raw:
                raise RuntimeError('Preserving a different runtime loader in the selected game: ' + str(target))
            before[relative] = current
            if current is None:
                changes[relative] = raw
                copied[relative] = hashlib.sha256(raw).hexdigest()
        return before, changes, copied
    import _ffr_runtime_loader as runtime
    if allow_bundle and runtime.choice(root, game) == 'install':
        return runtime.bundled_plan(game, owned, before, changes)
    return before, changes, None


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
    state = state_path(root, game, STATE)
    previous = json.loads(state.read_bytes()) if state.is_file() else {'schema': 1, 'files': {}, 'game': str(game)}
    if previous.get('schema') != 1 or set(previous.get('files', {})) - allowed:
        raise RuntimeError('Unknown field leader ownership record.')
    if game_key(previous.get('game', game)) != game_key(game):
        raise RuntimeError('The selected game has a mismatched runtime ownership record.')
    before = {}; changes = {}
    for relative in allowed:
        path = checked(game, REL + '/' + relative)
        current = path.read_bytes() if path.is_file() else None
        known = previous['files'].get(relative)
        if current is not None and hashlib.sha256(current).hexdigest() != known:
            raise RuntimeError('Preserving an unowned or edited field leader file: ' + str(path))
        before[relative] = current
        changes[relative] = payload['files'][relative].encode('utf-8') if relative in payload['files'] else None
    loader_before, loader_changes, loader_owned = loader_plan(root, game, previous, bool(payload['files']))
    skipped = loader_owned is None
    if skipped:
        changes = {name: None for name in allowed}
        loader_owned = previous.get('loader', {})
    return {'root': root, 'game': game, 'before': before, 'changes': changes, 'state': state, 'runtimeSkipped': skipped,
            'loaderBefore': loader_before, 'loaderChanges': loader_changes, 'loaderOwned': loader_owned,
            'previous': state.read_bytes() if state.is_file() else None}


def deploy(plan, backup=None, log=print):
    changes = plan['changes']; before = plan['before']; game = plan['game']
    if backup:
        payload = {'schema': 1, 'game': str(game), 'files': {k: v.decode('utf-8') for k, v in before.items() if v is not None}}
        # The engine restores every file inside its pak backup directory to
        # ~mods. Keep runtime snapshots separate so no JSON is copied there.
        atomic(runtime_backup(plan['root'], game, Path(backup).name), json.dumps(payload).encode())
    written = []
    loader_written = []
    # Disable first; publish enabled.txt last after its scripts are in place.
    for relative in ('enabled.txt', 'Scripts/config.lua', 'Scripts/main.lua'):
        path = checked(game, REL + '/' + relative)
        if (path.read_bytes() if path.is_file() else None) != before[relative]:
            raise RuntimeError('The field leader runtime changed during installation.')
    if (plan['state'].read_bytes() if plan['state'].is_file() else None) != plan['previous']:
        raise RuntimeError('The runtime ownership record changed during installation.')
    for relative, current in plan['loaderBefore'].items():
        path = checked(game, relative)
        if (path.read_bytes() if path.is_file() else None) != current:
            raise RuntimeError('The runtime loader changed during installation.')
    try:
        checked(game, REL + '/enabled.txt').unlink(missing_ok=True)
        for relative, data in plan['loaderChanges'].items():
            path = checked(game, relative)
            loader_written.append(relative)
            if data is None: path.unlink(missing_ok=True)
            else: atomic(path, data)
        for relative in ('Scripts/config.lua', 'Scripts/main.lua', 'enabled.txt'):
            path = checked(game, REL + '/' + relative)
            written.append(relative)
            if changes[relative] is None: path.unlink(missing_ok=True)
            else: atomic(path, changes[relative])
        atomic(plan['state'], json.dumps({'schema': 1, 'game': str(game), 'loader': plan['loaderOwned'], 'runtimeSkipped': plan.get('runtimeSkipped', False), 'files': {
            k: hashlib.sha256(v).hexdigest() for k, v in changes.items() if v is not None}}).encode())
    except BaseException:
        for relative in reversed(loader_written):
            path = checked(game, relative)
            if plan['loaderBefore'][relative] is None: path.unlink(missing_ok=True)
            else: atomic(path, plan['loaderBefore'][relative])
        for relative in set(written) | {'enabled.txt'}:
            path = checked(game, REL + '/' + relative)
            if before[relative] is None: path.unlink(missing_ok=True)
            else: atomic(path, before[relative])
        if plan['previous'] is None: plan['state'].unlink(missing_ok=True)
        else: atomic(plan['state'], plan['previous'])
        raise
    if plan.get('runtimeSkipped'):
        import _ffr_runtime_loader
        log(_ffr_runtime_loader.SKIPPED)
    elif any(raw is not None for raw in plan['loaderChanges'].values()):
        log('Installed the UE4SS core loader with the Studio runtime.')


def restore_plan(root, game, backup=None):
    path = runtime_backup(root, game, backup) if backup else None
    payload = json.loads(path.read_bytes()) if path and path.is_file() else {'schema': 1, 'files': {}}
    if payload.get('game') and game_key(payload['game']) != game_key(game):
        raise RuntimeError('The runtime backup belongs to another game folder.')
    return install_plan(root, game, payload)
