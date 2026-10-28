"""Optional, consented UE4SS bootstrap using a checksum-pinned official bundle.

Only the core loader, default settings and MIT license are deployed. Upstream's
example mods, SDK backends and mod lists are never installed.
"""
import hashlib
import json
from pathlib import Path
import zipfile

VERSION = '3.0.1-1183-gcdbc0b66'
ARCHIVE_SHA256 = 'e4a47e23e2eeb8379c4fc388d1b1686f01c6c5930d84a2ee4a6a9574b274e681'
SOURCE = 'https://github.com/UE4SS-RE/RE-UE4SS/releases/download/experimental-latest/UE4SS_v' + VERSION + '.zip'
CORE = ('dwmapi.dll', 'ue4ss/UE4SS.dll', 'ue4ss/UE4SS-settings.ini', 'ue4ss/LICENSE')
SKIPPED = ('UE4SS is not installed. Installed the game assets without Studio runtime features: '
           'overworld replacements/cycling, Crystal Fina runtime presentation/movie music, '
           'custom esper mastery bonuses, and the in-game encounter toggle. Install UE4SS and reinstall to enable them.')


def choice_path(root, game):
    import _ffr_field_leader as leader
    return leader.checked(root, 'runtime-loader/' + hashlib.sha256(leader.game_key(game).encode()).hexdigest() + '.json')


def choice(root, game):
    import _ffr_field_leader as leader
    path = choice_path(root, game)
    if not path.is_file(): return 'skip'
    value = json.loads(path.read_bytes())
    if (value.get('schema') != 1 or value.get('choice') not in ('install', 'skip')
            or leader.game_key(value.get('game', '')) != leader.game_key(game)):
        raise ValueError('Invalid UE4SS installation choice for this game folder.')
    return value['choice']


def save_choice(root, game, selected):
    import _ffr_field_leader as leader
    if selected not in ('install', 'skip'): raise ValueError('Choose install or skip for UE4SS.')
    leader.atomic(choice_path(root, game), json.dumps({'schema': 1, 'game': str(game), 'choice': selected}).encode())


def bundled_plan(game, owned, before, changes):
    import _ffr_field_leader as leader
    archive = Path(__file__).with_name('ue4ss_runtime.zip')
    if hashlib.sha256(archive.read_bytes()).hexdigest() != ARCHIVE_SHA256:
        raise ValueError('The bundled UE4SS checksum does not match. Reinstall Studio.')
    copied = dict(owned)
    with zipfile.ZipFile(archive) as bundle:
        for name in CORE:
            raw = bundle.read(name)
            if not raw: raise ValueError('The bundled UE4SS file is empty: ' + name)
            relative = 'FFRS/Binaries/Win64/' + name
            path = leader.checked(game, relative)
            current = path.read_bytes() if path.is_file() else None
            if current is not None and current != raw:
                raise RuntimeError('Preserving a different runtime loader in the selected game: ' + str(path))
            before[relative] = current
            if current is None:
                changes[relative] = raw
                copied[relative] = hashlib.sha256(raw).hexdigest()
    return before, changes, copied


def updated_bundle_ownership(game, owned):
    """Recognize an exact official core update without changing game files.

    A controlled loader update can leave an older installation ledger behind.
    Only already-owned binary entries can be reconciled, and both installed
    binaries must match the complete checksum-pinned bundle. Settings and other
    files retain their existing ownership checks.
    """
    import _ffr_field_leader as leader
    names = tuple('FFRS/Binaries/Win64/' + name for name in CORE[:2])
    if not any(name in owned for name in names): return None
    paths = [leader.checked(game, name) for name in names]
    if not all(path.is_file() for path in paths): return None
    archive = Path(__file__).with_name('ue4ss_runtime.zip')
    if hashlib.sha256(archive.read_bytes()).hexdigest() != ARCHIVE_SHA256:
        raise ValueError('The bundled UE4SS checksum does not match. Reinstall Studio.')
    with zipfile.ZipFile(archive) as bundle:
        expected = [bundle.read(name) for name in CORE[:2]]
    if any(path.read_bytes() != raw for path, raw in zip(paths, expected)): return None
    result = dict(owned)
    for name, raw in zip(names, expected):
        if name in result: result[name] = hashlib.sha256(raw).hexdigest()
    return result


def status(root, game, units, last_build=False):
    import _ffr_field_leader as leader
    import _ffr_fina_battle as fina
    import _ffr_esper_mastery as espers
    if last_build:
        stage = Path(root) / leader.STAGE
        required = bool(json.loads(stage.read_bytes()).get('files')) if stage.is_file() else False
    else:
        import _ffr_testing
        required = bool(leader.enabled(root) or _ffr_testing.settings(root)['noEncounters'] or any(u.get('party') and u.get('overworld') for u in units)
                        or fina.selected(units, root) or espers.enabled(units))
    ready = False
    if required:
        state = leader.state_path(root, game, leader.STATE)
        previous = json.loads(state.read_bytes()) if state.is_file() else {}
        ready = leader.loader_plan(root, game, previous, True, allow_bundle=False)[2] is not None
    return {'required': required, 'ready': ready, 'game': str(game), 'version': VERSION}


def register(app, env):
    from fastapi import HTTPException, Request
    globals()['Request'] = Request
    import _ffr_deck_sync as sync
    import _ffr_field_leader as leader
    root = Path(env['ROOT'])
    import _ffr_sephira

    @app.get('/api/runtime/status')
    def runtime_status(lastBuild: bool = False):
        try:
            return status(root, Path(env['ffrenv'].game_root()),
                          _ffr_sephira.active_units(env['load_spec']()), lastBuild)
        except (OSError, ValueError, RuntimeError) as e: raise HTTPException(422, str(e)) from e

    @app.post('/api/runtime/choice')
    async def runtime_choice(request: Request):
        value = await request.json()
        with sync._operation:
            if env.get('state', {}).get('running'):
                raise HTTPException(409, 'Wait for the current build before changing the UE4SS choice.')
            game = Path(env['ffrenv'].game_root())
            if not isinstance(value, dict) or value.get('game') != str(game):
                raise HTTPException(409, 'The selected game changed. Start the installation again.')
            try:
                if value.get('choice') == 'install':
                    state = leader.state_path(root, game, leader.STATE)
                    previous = json.loads(state.read_bytes()) if state.is_file() else {}
                    before, changes, owned = leader.loader_plan(root, game, previous, True, allow_bundle=False)
                    if owned is None:
                        bundled_plan(game, previous.get('loader', {}), before, changes)
                save_choice(root, game, value.get('choice'))
            except (OSError, ValueError, RuntimeError) as e: raise HTTPException(422, str(e)) from e
        return {'ok': True}
