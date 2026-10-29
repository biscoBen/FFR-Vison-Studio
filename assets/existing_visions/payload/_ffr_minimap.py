"""Install the reviewed, user-supplied minimap package without rebuilding visions."""
import hashlib
import json
from pathlib import Path
import zipfile

import _ffr_deck_sync as sync

NAME = 'MinimapShowTreasure_P'
PAKS = 'FFRS/Content/Paks/'
HASHES = {
    NAME + '.pak': '75e7144577253917f6da7312ef5e585b12fb728226a22b0938323751a6b555cd',
    NAME + '.ucas': '5776c39b5b2790b6f7533d6cd8345df55596d75cd8495268bbd848f279fd1642',
    NAME + '.utoc': '6bba1df558c8ea077195734037d988d3b544dfd43c5dd9e6e574606f2c289588',
}
COUNTER_NAME = 'FFRStudioTreasureCounter_P'
COUNTER_HASHES = {
    COUNTER_NAME + '.pak': '75e7144577253917f6da7312ef5e585b12fb728226a22b0938323751a6b555cd',
    COUNTER_NAME + '.ucas': '740057a167ac1b3b5a50b8e067be01b4195a517c81a1b5cbb9c42e2c0b83505d',
    COUNTER_NAME + '.utoc': 'a301431d7bedeb167227e0689ada3fece0f5a9abe9228701df5e48afd52366fb',
}


def bundle():
    with zipfile.ZipFile(Path(__file__).with_name('minimap_treasure.zip')) as archive:
        if set(archive.namelist()) != set(HASHES):
            raise ValueError('The bundled treasure radar package is incomplete. Reinstall Studio.')
        files = {name: archive.read(name) for name in HASHES}
    if any(hashlib.sha256(raw).hexdigest() != HASHES[name] for name, raw in files.items()):
        raise ValueError('The bundled treasure radar checksum does not match. Reinstall Studio.')
    return files


def counter_bundle():
    with zipfile.ZipFile(Path(__file__).with_name('minimap_counter.zip')) as archive:
        if set(archive.namelist()) != set(COUNTER_HASHES):
            raise ValueError('The bundled remaining-item counter is incomplete. Reinstall Studio.')
        files = {name: archive.read(name) for name in COUNTER_HASHES}
    if any(hashlib.sha256(raw).hexdigest() != COUNTER_HASHES[name] for name, raw in files.items()):
        raise ValueError('The remaining-item counter checksum does not match. Reinstall Studio.')
    return files


def ledger(root, game):
    import _ffr_field_leader as leader
    return sync.checked(root, 'minimap-treasure/' + hashlib.sha256(leader.game_key(game).encode()).hexdigest() + '.json')


def known_files(game):
    files, conflicts = {}, []
    for folder in (PAKS, PAKS + '~mods/'):
        for name, digest in (HASHES | COUNTER_HASHES).items():
            relative = folder + name
            path = sync.checked(game, relative)
            if path.exists():
                if not path.is_file() or sync.sha(path) != digest: conflicts.append(relative)
                else: files[relative] = path.read_bytes()
    return files, conflicts


def status(game):
    if not game: return {'available': False, 'enabled': False, 'message': 'Select your game folder first.'}
    files, conflicts = known_files(game)
    available = sync.checked(game, sync.MARKER).is_file()
    complete = any(all(folder + name in files for name in HASHES) for folder in (PAKS, PAKS + '~mods/'))
    counter = any(all(folder + name in files for name in COUNTER_HASHES) for folder in (PAKS, PAKS + '~mods/'))
    message = ('A different or edited treasure radar package is present. Its files have been preserved.' if conflicts else
               'Switch treasure radar off and on once to add its remaining-item counter. No vision rebuild needed.' if complete and not counter else
               'Close Resonance before switching. Radar and remaining-item counter apply on the next launch; no vision rebuild needed.' if available else
               'Select a complete Resonance installation first.')
    return {'available': available, 'enabled': complete and not conflicts, 'conflict': bool(conflicts),
            'partial': bool(files) and not complete, 'counterEnabled': complete and counter and not conflicts,
            'message': message, 'game': str(game)}


def owned(root, game):
    import _ffr_field_leader as leader
    value = sync.read_json(ledger(root, game), {'schema': 1, 'game': str(game), 'files': {}})
    hashes = HASHES | COUNTER_HASHES
    allowed = {folder + name for folder in (PAKS, PAKS + '~mods/') for name in hashes}
    if (not isinstance(value, dict) or value.get('schema') != 1 or leader.game_key(value.get('game', '')) != leader.game_key(game)
            or not isinstance(value.get('files'), dict) or set(value['files']) - allowed
            or any(digest != hashes[Path(name).name] for name, digest in value['files'].items())):
        raise ValueError('The treasure radar ownership record is invalid; no files changed.')
    return value


def plan(root, game, enabled=None):
    """None restores only files this Studio installed; False explicitly removes the reviewed mod."""
    root, game = Path(root), Path(game)
    record = owned(root, game)
    current, conflicts = known_files(game)
    if enabled is None:
        targets = set(record['files'])
        if any(name in conflicts for name in targets):
            raise ValueError('Preserving an edited Studio treasure radar file. Restore the original mod before removing it.')
    else:
        if type(enabled) is not bool: raise ValueError('Choose on or off for treasure radar.')
        if not sync.checked(game, sync.MARKER).is_file(): raise ValueError('Select a complete Resonance installation first.')
        if conflicts: raise ValueError('Preserving a different or edited treasure radar package: ' + ', '.join(conflicts))
        targets = set(current)
    changes = {}
    next_owned = dict(record['files'])
    if enabled:
        # Preserve recognized manual packages; add only each missing companion.
        folder = PAKS if any(name.startswith(PAKS + NAME) for name in current) else PAKS + '~mods/'
        for files, hashes in ((bundle(), HASHES), (counter_bundle(), COUNTER_HASHES)):
            complete = any(all(candidate + name in current for name in hashes) for candidate in (PAKS, PAKS + '~mods/'))
            if complete: continue
            for name, raw in files.items():
                relative = folder + name
                if relative not in current:
                    changes[relative] = raw
                    next_owned[relative] = hashes[name]
    else:
        changes = {name: None for name in targets if name in current}
        next_owned = {name: digest for name, digest in next_owned.items() if name not in targets}
    state = ledger(root, game)
    before = {name: sync.checked(game, name).read_bytes() if sync.checked(game, name).is_file() else None for name in changes}
    return {'game': game, 'state': state, 'previous': state.read_bytes() if state.is_file() else None,
            'before': before, 'changes': changes,
            'record': {'schema': 1, 'game': str(game), 'files': next_owned}}


def deploy(value):
    game, state = value['game'], value['state']
    for name, before in value['before'].items():
        path = sync.checked(game, name)
        if (path.read_bytes() if path.is_file() else None) != before:
            raise ValueError('The treasure radar files changed during installation. Try again.')
    if (state.read_bytes() if state.is_file() else None) != value['previous']:
        raise ValueError('The treasure radar ownership record changed. Try again.')
    if not value['changes'] and not value['previous']: return
    written = []
    try:
        for name, raw in value['changes'].items():
            path = sync.checked(game, name); written.append(name)
            if raw is None: path.unlink(missing_ok=True)
            else: sync.atomic(path, raw)
        if value['record']['files']: sync.json_write(state, value['record'])
        else: state.unlink(missing_ok=True)
    except BaseException:
        for name in reversed(written):
            path = sync.checked(game, name); before = value['before'][name]
            if before is None: path.unlink(missing_ok=True)
            else: sync.atomic(path, before)
        if value['previous'] is None: state.unlink(missing_ok=True)
        else: sync.atomic(state, value['previous'])
        raise


def register(app, env):
    from fastapi import HTTPException

    @app.get('/api/minimap-treasure')
    def get_status():
        try: return status(env['ffrenv'].game_root())
        except (OSError, ValueError, RuntimeError) as error: raise HTTPException(422, str(error)) from error

    @app.put('/api/minimap-treasure')
    def set_enabled(value: dict):
        with sync._operation:
            try:
                import _ffr_launch
                _ffr_launch.busy(env)
                if env['game_running'](): raise ValueError('Close Resonance before changing treasure radar.')
                game = env['ffrenv'].game_root()
                if value.get('game') != str(game): raise ValueError('The selected game changed. Try again.')
                if set(value) != {'game', 'enabled'} or type(value.get('enabled')) is not bool:
                    raise ValueError('Choose on or off for treasure radar.')
                deploy(plan(env['ROOT'], game, value['enabled']))
                return status(game)
            except (OSError, ValueError, RuntimeError) as error: raise HTTPException(422, str(error)) from error
