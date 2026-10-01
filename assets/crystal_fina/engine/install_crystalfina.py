"""Install reversible Crystal Fina material hooks into an official Studio engine.

Only the loose Python builder, a helper, and this patch's private assets are edited.
No game, roster, executable, updater manifest, or catalog files are changed here.
"""
import argparse
import ast
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import sys
import tempfile

VERSION = '1.1.1'
MARKER = '# FFR-CRYSTALFINA-TRANSPARENCY v1'
MODULE = '_ffr_crystalfina'
STATE_DIR = '.ffr-crystalfina'
HERE = Path(__file__).resolve().parent


class PatchError(Exception):
    pass


def digest(data):
    return hashlib.sha256(data).hexdigest()


def checked_path(root, *parts):
    root = Path(root).absolute()
    current = root
    for node in (root, *root.parents):
        if node.exists() and (node.is_symlink() or (hasattr(node, 'is_junction') and node.is_junction())):
            raise PatchError(f'Use a physical folder, not a link/junction: {node}')
    for part in parts:
        for piece in Path(part).parts:
            current = current / piece
            if current.exists() and (current.is_symlink() or (hasattr(current, 'is_junction') and current.is_junction())):
                raise PatchError(f'Refusing a link/junction: {current}')
    if not current.resolve().is_relative_to(root.resolve()):
        raise PatchError('A patch path escapes its selected folder.')
    return current


def paths(engine):
    return {
        'builder': checked_path(engine, 'tools', 'make_vision_mod.py'),
        'helper': checked_path(engine, 'tools', MODULE + '.py'),
        'state': checked_path(engine, STATE_DIR, 'state.json'),
        'backup_dir': checked_path(engine, STATE_DIR, 'backups'),
    }


def atomic_write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix='ffr-crystalfina-', suffix='.tmp', dir=path.parent)
    try:
        with os.fdopen(fd, 'wb') as file:
            file.write(data)
            file.flush()
            os.fsync(file.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def same(node, source):
    return ast.dump(node, include_attributes=False) == ast.dump(ast.parse(source).body[0], include_attributes=False)


def hook_builder(original):
    text = original.decode('utf-8-sig')
    if MARKER in text or MODULE in text:
        raise PatchError('An existing or unfamiliar Crystal Fina hook is present. Use Status first.')
    try:
        tree = ast.parse(text)
    except SyntaxError as exc:
        raise PatchError(f'Builder source is not valid Python: {exc}') from exc
    mains = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'main']
    if len(mains) != 1:
        raise PatchError('Unsupported builder: expected exactly one main function.')
    main = mains[0]
    if main.args.args or main.args.posonlyargs or main.args.kwonlyargs or main.args.vararg or main.args.kwarg:
        raise PatchError('Unsupported builder: main signature changed.')
    patch_source = r'''patch = {"legacyRoot": LEGACY.replace("\\", "/"), "outRoot": OUT.replace("\\", "/"), "tables": list(tables.values()), "objects": objects, "clones": clones}'''
    pack_source = '''stage("Packing the mod" + (" and installing it" if install else ""))'''
    command_source = '''cmd = ffrenv.py(os.path.join(ROOT, "tools", "build_mod.py"), OUT, ffrenv.MOD_NAME) + (["--install"] if install else [])'''
    cleanup_source = '''if os.path.isdir(OUT):
    import shutil
    shutil.rmtree(OUT)'''
    patch_nodes = [n for n in main.body if same(n, patch_source)]
    pack_nodes = [n for n in main.body if same(n, pack_source)]
    cmd_nodes = [n for n in main.body if same(n, command_source)]
    clean_nodes = [n for n in main.body if same(n, cleanup_source)]
    if any(len(nodes) != 1 for nodes in (patch_nodes, pack_nodes, cmd_nodes, clean_nodes)):
        raise PatchError('The developers changed the builder layout. This installer will not overwrite unfamiliar logic.')
    patch, pack, command, clean = [nodes[0] for nodes in (patch_nodes, pack_nodes, cmd_nodes, clean_nodes)]
    dumps = [n for n in ast.walk(main) if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
             and isinstance(n.func.value, ast.Name) and n.func.value.id == 'json' and n.func.attr == 'dump'
             and n.args and isinstance(n.args[0], ast.Name) and n.args[0].id == 'patch']
    if len(dumps) != 1 or not patch.end_lineno < dumps[0].lineno < clean.lineno < pack.lineno < command.lineno:
        raise PatchError('Unsupported builder: table writing, output cleanup, or packing order changed.')
    # The pack call must directly follow its stage marker, so all generated assets exist.
    if main.body.index(command) != main.body.index(pack) + 1:
        raise PatchError('Unsupported builder: extra logic was inserted before packing.')
    nl = '\r\n' if '\r\n' in text else '\n'
    additions = {
        patch.end_lineno: [f'    {MARKER}', f'    import {MODULE}', f'    {MODULE}.prepare(patch, UNITS, ROOT)'],
        pack.lineno - 1: [f'    {MARKER}', f'    {MODULE}.copy_material(ROOT, OUT, UNITS)'],
    }
    lines = text.splitlines(keepends=True)
    output = []
    for index, line in enumerate(lines, 1):
        output.append(line)
        if index in additions:
            if not line.endswith(('\n', '\r')):
                output.append(nl)
            output.append(nl.join(additions[index]) + nl)
    result = ''.join(output)
    compile(result, 'make_vision_mod.py', 'exec')
    return (b'\xef\xbb\xbf' if original.startswith(b'\xef\xbb\xbf') else b'') + result.encode('utf-8')


def relative_file(value):
    if not isinstance(value, str) or '\\' in value or ':' in value:
        raise PatchError('Invalid relative payload path.')
    path = PurePosixPath(value)
    if path.is_absolute() or '..' in path.parts or str(path) != value:
        raise PatchError('Unsafe relative payload path.')
    return path


def payload_destination(rel):
    relative_file(rel)
    if rel == MODULE + '.py':
        return 'tools/' + rel
    if rel.startswith('material/FFRS/Content/') and PurePosixPath(rel).suffix in ('.uasset', '.uexp', '.ubulk'):
        return STATE_DIR + '/' + rel
    raise PatchError(f'Unexpected payload file: {rel}')


def owned_path(engine, rel):
    relative_file(rel)
    if rel not in ('tools/' + MODULE + '.py', STATE_DIR + '/manifest.json'):
        prefix = STATE_DIR + '/'
        if not rel.startswith(prefix) or payload_destination(rel[len(prefix):]) != rel:
            raise PatchError('Unexpected managed file in patch state.')
    return checked_path(engine, *PurePosixPath(rel).parts)


def load_payload(payload=None):
    payload = Path(payload or HERE / 'payload')
    manifest_path = checked_path(payload, 'manifest.json')
    try:
        raw = manifest_path.read_bytes()
        manifest = json.loads(raw)
        files = manifest['files']
        if manifest.get('schema') != 1 or not isinstance(files, dict):
            raise ValueError('schema/files')
    except (OSError, ValueError, KeyError) as exc:
        raise PatchError(f'The complete payload/manifest.json is required: {exc}') from exc
    out = {STATE_DIR + '/manifest.json': raw}
    for rel, expected in files.items():
        target = payload_destination(rel)
        data = checked_path(payload, *PurePosixPath(rel).parts).read_bytes()
        if not isinstance(expected, str) or not re.fullmatch('[0-9a-f]{64}', expected) or digest(data) != expected:
            raise PatchError(f'Payload checksum mismatch: {rel}')
        out[target] = data
    if 'tools/' + MODULE + '.py' not in out or not any(rel.startswith(STATE_DIR + '/material/') for rel in out):
        raise PatchError('Payload must include the helper and material files.')
    actual = {p.relative_to(payload).as_posix() for p in payload.rglob('*') if p.is_file() and p != manifest_path}
    if actual != set(files):
        raise PatchError('Payload contains files missing from its manifest.')
    compile(out['tools/' + MODULE + '.py'], MODULE + '.py', 'exec')
    return out


def read_state(p):
    if not p['state'].exists():
        return None
    try:
        state = json.loads(p['state'].read_text(encoding='utf-8'))
    except (OSError, ValueError) as exc:
        raise PatchError(f'Cannot read patch state: {exc}') from exc
    if state.get('schema') != 1 or not isinstance(state.get('files'), dict):
        raise PatchError('Unknown patch-state format.')
    return state


def original_from_state(engine, state):
    rel = state.get('backup', '')
    relative_file(rel)
    if PurePosixPath(rel).parent != PurePosixPath(STATE_DIR) / 'backups' or not rel.endswith('.original.py'):
        raise PatchError('Unsafe original-backup path.')
    file = checked_path(engine, *PurePosixPath(rel).parts)
    data = file.read_bytes()
    if digest(data) != state.get('original_sha256'):
        raise PatchError('Original-backup checksum mismatch.')
    return data


def validate_owned_files(engine, state, wanted=()):
    known = (state or {}).get('files', {})
    for rel in set(known) | set(wanted):
        file = owned_path(engine, rel)
        if file.exists() and (rel not in known or digest(file.read_bytes()) != known[rel]):
            raise PatchError(f'Unknown ownership or external edits: {file}. No files changed.')


def inspect(engine):
    p = paths(engine)
    state = read_state(p)
    if not p['builder'].is_file():
        raise PatchError('No tools/make_vision_mod.py in the selected engine.')
    data = p['builder'].read_bytes()
    hook = MARKER.encode() in data or MODULE.encode() in data
    result = {'engine': str(engine), 'patchVersion': VERSION}
    if not state:
        result['status'] = 'unmanaged-hook' if hook else 'not-installed'
    elif hook and digest(data) == state.get('patched_sha256'):
        valid = all((p := owned_path(engine, rel)).is_file() and digest(p.read_bytes()) == sha for rel, sha in state['files'].items())
        result['status'] = 'active' if valid else 'payload-missing-or-modified'
    elif hook:
        result['status'] = 'patched-file-modified'
    elif digest(data) == state.get('original_sha256'):
        result['status'] = 'restored'
    else:
        result['status'] = 'developer-update-or-other-change'
    return result


def transact(changes, expected=None):
    before = {p: p.read_bytes() if p.exists() else None for p in changes}
    for p, data in (expected or {}).items():
        if before.get(p) != data:
            raise PatchError(f'A file changed before patching: {p}. Close Studio and retry.')
    written = []
    try:
        for p, value in changes.items():
            current = p.read_bytes() if p.exists() else None
            if current != before[p]:
                raise PatchError(f'A file changed during patching: {p}. Close Studio and retry.')
            if value is None:
                if p.exists():
                    p.unlink()
            else:
                atomic_write(p, value)
            written.append(p)
    except BaseException:
        for p in reversed(written):
            current = p.read_bytes() if p.exists() else None
            if current != changes[p]:
                continue  # Preserve any external writer's intervening edits.
            if before[p] is None:
                if p.exists():
                    p.unlink()
            else:
                atomic_write(p, before[p])
        raise


def apply(engine, payload=None):
    p = paths(engine)
    state = read_state(p)
    if not p['builder'].is_file():
        raise PatchError('No tools/make_vision_mod.py in this engine.')
    files = load_payload(payload)
    validate_owned_files(engine, state, files)
    current = p['builder'].read_bytes()
    if MARKER.encode() in current or MODULE.encode() in current:
        if not state or digest(current) != state.get('patched_sha256'):
            raise PatchError('The patched builder has external edits; refusing to overwrite them.')
        original = original_from_state(engine, state)
    else:
        original = current  # Reapply to a developer update, never replace it with an old backup.
    patched = hook_builder(original)
    if current == patched and all((f := owned_path(engine, rel)).is_file() and f.read_bytes() == data for rel, data in files.items()) and set(files) == set((state or {}).get('files', {})):
        return dict(inspect(engine), action='already-applied', changed=False)
    backup_rel = f'{STATE_DIR}/backups/{digest(original)}.original.py'
    backup = checked_path(engine, *PurePosixPath(backup_rel).parts)
    if backup.exists() and backup.read_bytes() != original:
        raise PatchError('An original backup has unexpected contents.')
    if not backup.exists():
        atomic_write(backup, original)
    new_state = {'schema': 1, 'patch_version': VERSION, 'applied_at': datetime.now(timezone.utc).isoformat(),
                 'backup': backup_rel, 'original_sha256': digest(original), 'patched_sha256': digest(patched),
                 'files': {rel: digest(data) for rel, data in files.items()}, 'status': 'applied'}
    changes = {owned_path(engine, rel): None for rel in (state or {}).get('files', {}) if rel not in files}
    changes.update({owned_path(engine, rel): data for rel, data in files.items()})
    changes[p['state']] = json.dumps(new_state, indent=2).encode('utf-8')
    changes[p['builder']] = patched  # Activate last, once all helper dependencies exist.
    transact(changes, {p['builder']: current})
    return dict(inspect(engine), action='applied', changed=True, backup=str(backup))


def validate_engine(engine):
    version = checked_path(engine, 'VERSION').read_text(encoding='utf-8').strip()
    if not re.fullmatch(r'1\.\d+\.\d+\.\d+', version) or tuple(map(int, version.split('.'))) < (1, 0, 0, 15):
        raise PatchError(f'Unsupported engine version {version}; Crystal Fina requires a compatible engine 1.0.0.15 or newer.')
    for relative in ('tools/ffrenv.py', 'tools/devui/ffbe_catalog.py', 'bin/ffr-dt.exe'):
        if not checked_path(engine, relative).is_file():
            raise PatchError(f'Unsupported engine layout: missing {relative}.')


def restore(engine):
    p = paths(engine)
    state = read_state(p)
    current = p['builder'].read_bytes()
    hook = MARKER.encode() in current or MODULE.encode() in current
    if not state:
        if hook:
            raise PatchError('A hook exists without its backup record; cannot safely restore it.')
        return dict(inspect(engine), action='nothing-to-restore', changed=False)
    validate_owned_files(engine, state)
    original = original_from_state(engine, state)
    if hook and digest(current) != state.get('patched_sha256'):
        raise PatchError('The builder changed after patching; restoring would overwrite edits.')
    changes = {}
    if hook:
        changes[p['builder']] = original  # Deactivate before removing dependencies.
    changes.update({owned_path(engine, rel): None for rel in state['files']})
    state['status'] = 'restored'
    changes[p['state']] = json.dumps(state, indent=2).encode('utf-8')
    transact(changes, {p['builder']: current} if hook else None)
    return dict(inspect(engine), action='restored' if hook else 'hook-already-absent-kept-current-builder', changed=hook)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--engine', required=True)
    parser.add_argument('--action', choices=['Apply', 'Status', 'Restore'], default='Apply')
    args = parser.parse_args()
    engine = Path(args.engine).absolute()
    if args.action == 'Apply': validate_engine(engine)
    result = {'Apply': apply, 'Status': inspect, 'Restore': restore}[args.action](engine)
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    try:
        main()
    except (PatchError, OSError, UnicodeError, SyntaxError) as exc:
        print(f'ERROR: {exc}', file=sys.stderr)
        sys.exit(1)
