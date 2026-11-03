"""Reclaim recorded mod rollback copies without removing restoration originals."""
import functools
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import stat

import _ffr_field_leader as leader

KEEP = 3
STAMP = re.compile(r'[0-9]{8}_[0-9]{6}')
FILES = {f'zzz_EstherTsukiko_P.{ext}' for ext in ('utoc', 'ucas', 'pak')}


def regular(path):
    info = path.lstat()
    return stat.S_ISREG(info.st_mode) and not getattr(info, 'st_file_attributes', 0) & 0x400


def policy_path(root, game):
    ledger = Path(leader.game_state_path(root, game))
    return leader.checked(ledger.parent, 'backup-policy.json')


def automatic(root, game):
    path = policy_path(root, game)
    if not path.exists(): return False
    value = json.loads(path.read_bytes())
    if (not isinstance(value, dict) or set(value) != {'schema', 'automatic'}
            or value['schema'] != 1 or type(value['automatic']) is not bool):
        raise ValueError('Unsupported backup cleanup settings.')
    return value['automatic'] is True


def plan(root, game):
    if not game: raise ValueError('Select your game folder before checking backups.')
    ledger = Path(leader.game_state_path(root, game))
    raw = ledger.read_bytes() if ledger.exists() else b'{}'
    record = json.loads(raw)
    if (not isinstance(record, dict) or not isinstance(record.get('original', {}), dict)
            or not isinstance(record.get('installs', []), list)):
        raise ValueError('Unreadable installation history; backups were preserved.')
    protected = set()
    for original in record.get('original', {}).values():
        if not isinstance(original, str): raise ValueError('Unreadable original-file backup reference.')
        parts = original.replace('\\', '/').split('/')
        if len(parts) != 2 or parts[0] in ('', '.', '..') or parts[1] not in FILES:
            raise ValueError('Unrecognized original-file backup reference; backups were preserved.')
        protected.add(parts[0])
    known = set()
    owners = {leader.game_key(record['game'])} if record.get('game') else set()
    for entry in record.get('installs', []):
        if not isinstance(entry, dict): raise ValueError('Unreadable installation history.')
        if entry.get('game'): owners.add(leader.game_key(entry['game']))
        stamp = entry.get('backup')
        if isinstance(stamp, str) and STAMP.fullmatch(stamp): known.add(stamp)
    if owners and owners != {leader.game_key(game)}:
        raise ValueError('Backup history belongs to a different game folder; backups were preserved.')
    base = Path(leader.backup_root(root, game))
    entries, skipped = [], 0
    for folder in sorted(base.iterdir()) if base.exists() else []:
        try:
            leader.checked(base, folder.name)
            if not folder.is_dir() or not STAMP.fullmatch(folder.name):
                skipped += 1; continue
            children = sorted(folder.iterdir())
            if not children or any(p.name not in FILES or not regular(p) for p in children):
                skipped += 1; continue
            metadata = []
            for path in children:
                leader.checked(base, path.relative_to(base))
                info = path.stat()
                metadata.append([path.name, info.st_size, info.st_mtime_ns, info.st_ctime_ns])
            entries.append({'id': folder.name, 'bytes': sum(p[1] for p in metadata),
                            'metadata': metadata, 'original': folder.name in protected,
                            'recorded': folder.name in known})
        except OSError:
            skipped += 1
        except RuntimeError:
            skipped += 1
    # Unrecorded/partial copies and unexpected contents are never guessed away.
    recent = {entry['id'] for entry in entries if entry['recorded']}
    recent = set(sorted(recent)[-KEEP:])
    candidates = [e for e in entries if e['recorded'] and not e['original'] and e['id'] not in recent]
    enabled = automatic(root, game)
    identity = {'game': leader.game_key(game), 'ledger': hashlib.sha256(raw).hexdigest(),
                'base': str(base), 'entries': entries, 'automatic': enabled}
    token = hashlib.sha256(json.dumps(identity, sort_keys=True).encode()).hexdigest()
    return {'token': token, 'backupBytes': sum(e['bytes'] for e in entries),
            'reclaimBytes': sum(e['bytes'] for e in candidates), 'backups': len(entries),
            'removeCount': len(candidates), 'keepCount': len(entries) - len(candidates),
            'originalCount': sum(e['original'] for e in entries), 'skipped': skipped,
            'automatic': enabled, 'configured': policy_path(root, game).exists(),
            'base': str(base), 'candidates': candidates}


def prune(root, game, token):
    current = plan(root, game)
    if current['token'] != token:
        raise ValueError('The backup list changed. Refresh and review cleanup again.')
    base = Path(current['base'])
    # Validate every selected directory before deleting any selected file.
    for entry in current['candidates']:
        folder = leader.checked(base, entry['id'])
        if sorted(p.name for p in folder.iterdir()) != [m[0] for m in entry['metadata']]:
            raise ValueError('A backup changed. Refresh and review cleanup again.')
        for name, size, modified, created in entry['metadata']:
            path = leader.checked(folder, name)
            info = path.stat()
            if not regular(path) or (info.st_size, info.st_mtime_ns, info.st_ctime_ns) != (size, modified, created):
                raise ValueError('A backup changed. Refresh and review cleanup again.')
    freed, removed = 0, 0
    for entry in current['candidates']:
        folder = leader.checked(base, entry['id'])
        for name, size, *_ in entry['metadata']:
            leader.checked(folder, name).unlink()
            freed += size
        folder.rmdir()
        removed += 1
    return {'freedBytes': freed, 'removed': removed}


def preflight(source, destination, backups, files, unchanged=()):
    """Budget both the new package and the previous package's backup per volume."""
    volumes = {}
    def reserve(folder, count):
        path = Path(folder)
        while not path.exists(): path = path.parent
        volume = os.path.splitdrive(str(path.resolve()))[0].lower() if os.name == 'nt' else path.stat().st_dev
        if volume not in volumes: volumes[volume] = [path, 0]
        volumes[volume][1] += count
    source, destination = Path(source), Path(destination)
    reserve(destination, sum((source / name).stat().st_size for name in files if name not in unchanged))
    reserve(backups, sum((destination / name).stat().st_size for name in files if (destination / name).is_file()))
    for path, required in volumes.values():
        # Leave room for ledgers/runtime files as well as the large package.
        required += 64 * 1024**2
        free = shutil.disk_usage(path).free
        if free < required:
            raise RuntimeError(f'Not enough free space on {path.anchor}: need {required / 1024**3:.2f} GB, '
                               f'available {free / 1024**3:.2f} GB. Open Mod backup storage to free space, '
                               'then use Install the last build.')


def after_install(root, game, log):
    try:
        if automatic(root, game):
            current = plan(root, game)
            result = prune(root, game, current['token'])
            if result['removed']:
                log(f"  Backup cleanup: removed {result['removed']} older copies; "
                    f"freed {result['freedBytes'] / 1024**3:.2f} GB; newest three and originals preserved.")
    except (OSError, ValueError, RuntimeError) as error:
        log('  Backup cleanup did not complete: ' + str(error))


def installation(action):
    @functools.wraps(action)
    def locked(*args, **kwargs):
        import _ffr_deck_sync as sync
        with sync._operation:
            return action(*args, **kwargs)
    return locked


def register(app, env):
    from fastapi import HTTPException
    import _ffr_deck_sync as sync
    import _ffr_launch as launch
    root = env['ROOT']

    def available():
        launch.busy(env)
        if env['game_running'](): raise ValueError('Close the game before managing its backups.')
        return env['ffrenv'].detect_game()

    @app.get('/api/storage/backups')
    def status():
        with sync._operation:
            try: return plan(root, available())
            except (OSError, ValueError, RuntimeError) as error: raise HTTPException(409, str(error)) from error

    @app.post('/api/storage/backups/cleanup')
    def cleanup(body: dict):
        with sync._operation:
            try:
                game = available()
                if type(body.get('automatic')) is not bool or not isinstance(body.get('token'), str):
                    raise ValueError('Review the backup cleanup preview first.')
                result = prune(root, game, body['token'])
                leader.atomic(policy_path(root, game), json.dumps({'schema': 1, 'automatic': body['automatic']}).encode())
                return {**plan(root, game), **result}
            except (OSError, ValueError, RuntimeError) as error: raise HTTPException(409, str(error)) from error
