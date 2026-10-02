"""Install managed native-vision hooks after the Crystal Fina extension.

Restore these hooks before reapplying Crystal Fina so each installer sees the
source it owns. Neither operation writes the roster or the game files.
"""
import argparse
import ast
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile

VERSION = '1.1.0'
MARKER = '# FFR-EXISTING-VISIONS v1'
STATE = '.ffr-existing-visions'
SOURCES = ('tools/make_vision_mod.py', 'tools/devui/server.py', 'tools/verify_mod.py')
HELPER = 'tools/_ffr_existingvisions.py'
RESOURCES = ('_ffr_party.py', '_ffr_animation_repair.py', '_ffr_build_sprites.py', '_ffr_library.py', 'ffbe_animation_index.json', 'ffbe_barrage_index.json')


def sha(data):
    return hashlib.sha256(data).hexdigest()


def checked(root, relative):
    root = Path(root).absolute()
    p = root / relative
    if not p.resolve().is_relative_to(root.resolve()):
        raise RuntimeError('Existing vision patch path escapes the engine.')
    for node in (p, *p.parents):
        if node.is_symlink() or (hasattr(node, 'is_junction') and node.is_junction()):
            raise RuntimeError('Existing vision patch paths must not be links.')
    return p


def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp = tempfile.mkstemp(prefix='native-visions-', dir=path.parent)
    try:
        with os.fdopen(fd, 'wb') as f:
            f.write(data); f.flush(); os.fsync(f.fileno())
        os.replace(temp, path)
    finally:
        if os.path.exists(temp): os.unlink(temp)


def transact(changes):
    before = {p: p.read_bytes() if p.exists() else None for p in changes}
    written = []
    try:
        for p, data in changes.items():
            if (p.read_bytes() if p.exists() else None) != before[p]:
                raise RuntimeError('Engine source changed while installing existing vision support.')
            if data is None:
                if p.exists(): p.unlink()
            else: write(p, data)
            written.append(p)
    except BaseException:
        for p in reversed(written):
            if (p.read_bytes() if p.exists() else None) == changes[p]:
                if before[p] is None: p.unlink(missing_ok=True)
                else: write(p, before[p])
        raise


def hook_builder(raw):
    text = raw.decode('utf-8-sig'); tree = ast.parse(text)
    loader, = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'load_units']
    skill_conversion, = [n for n in ast.walk(loader) if isinstance(n, ast.Assign)
                         and ast.unparse(n.targets[0]) == "u['skills']"]
    if skill_conversion.lineno != skill_conversion.end_lineno:
        raise RuntimeError('Unsupported roster skill conversion layout.')
    main, = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'main']
    loops = [n for n in main.body if isinstance(n, ast.For) and ast.unparse(n.target) == 'u' and ast.unparse(n.iter) == 'UNITS'
             and any(isinstance(a, ast.Assign) and ast.unparse(a.targets[0]) == 'skill_rows' for a in n.body)]
    loop, = loops
    start, = [i for i, n in enumerate(loop.body) if isinstance(n, ast.Assign) and ast.unparse(n.targets[0]) == 'skill_rows']
    stop, = [i for i, n in enumerate(loop.body) if isinstance(n, ast.Assign) and ast.unparse(n.targets[0]) == 'aw']
    if stop <= start or not isinstance(loop.body[start].value, ast.Call):
        raise RuntimeError('Unsupported native skill builder layout.')
    patch, = [n for n in main.body if isinstance(n, ast.Assign) and ast.unparse(n.targets[0]) == 'patch']
    pack, = [n for n in main.body if isinstance(n, ast.Expr) and isinstance(n.value, ast.Call)
             and ast.unparse(n.value.func) == 'stage' and 'Packing the mod' in ast.unparse(n.value)]
    if not loop.end_lineno < patch.lineno < pack.lineno:
        raise RuntimeError('Unsupported native vision build order.')
    icon_tag, = [n for n in loop.body if isinstance(n, ast.Assign) and ast.unparse(n.targets[0]) == 'icon_tag']
    icon_loop, = [n for n in loop.body if isinstance(n, ast.For) and ast.unparse(n.target) == 'rel'
                 and 'UI/Skill/DT_CommandSkillIcon' in ast.unparse(n.iter)]
    if 'UNUSED_ICON_TAGS' not in ast.unparse(icon_tag.value):
        raise RuntimeError('Unsupported command icon allocation.')
    generator, = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'generate_sprites']
    sprite_call, = [n for n in ast.walk(generator) if isinstance(n, ast.Call) and ast.unparse(n.func) == 'ffrenv.py'
                    and n.args and 'build_sprites.py' in ast.unparse(n.args[0])]
    timeline_loop, = [n for n in main.body if isinstance(n, ast.For) and ast.unparse(n.target) == 'job'
                     and ast.unparse(n.iter) == 'authored_sequences']
    timeline_stage, = [n for n in timeline_loop.body if isinstance(n, ast.Expr) and isinstance(n.value, ast.Call)
                      and ast.unparse(n.value.func) == 'stage']
    skill_body = '\n'.join(ast.unparse(n) for n in loop.body[start:stop])
    prelude = [MARKER, 'global UNITS', 'import _ffr_existingvisions', 'import _ffr_animation_repair', 'import _ffr_party',
               'party_units, UNITS = _ffr_party.split(UNITS, rows)',
               'native_units, UNITS = _ffr_existingvisions.split(UNITS, rows)',
               'for u in native_units + UNITS:', '    if u.get("ffbe"):',
               '        _ffr_animation_repair.repair_unit(u, ROOT)',
               'for u in native_units:', '    if u.get("ffbe"):',
               '        stage("Preparing original sprites: " + u["en"])',
               '        _ffr_existingvisions.ensure_sprite_templates(u, LEGACY,',
               '            lambda folder: run(ffrenv.py(os.path.join(ROOT, "tools", "extract_legacy.py"), "--filter", folder)))',
               '_ffr_animation_repair.prepare_barrage_trial(native_units + UNITS, ROOT, rows)',
               'def _native_skills(u):',
               '    nonlocal clones, post_objects, post_bytecode, post_frames, post_retime, authored_sequences, effect_jobs, built_effects',
               '    vid = u["id"]', '    d = u["donor"]',
               *['    ' + s for s in skill_body.splitlines()]]
    before_patch = [MARKER, 'for u in native_units:', '    _native_skills(u)',
                    '_ffr_existingvisions.prepare(tables, objects, native_units, ROOT, rows)',
                    '_ffr_animation_repair.prepare_sequences(tables, clones, authored_sequences, native_units + UNITS, ROOT, rows,',
                    '    lambda folder: run(ffrenv.py(os.path.join(ROOT, "tools", "extract_legacy.py"), "--filter", folder)),',
                    '    native_support={"clone": clone_sequence, "dumps": seq_dumps, "keys": event_keys,',
                    '                    "objects": post_objects, "bytecode": post_bytecode})']
    before_pack = [MARKER, 'for u in native_units:',
                   '    if u.get("ffbe"):', '        stage("Replacing sprites: " + u["en"])', '        generate_sprites(u)',
                   '_ffr_existingvisions.copy_materials(native_units, ROOT, OUT)',
                   '_ffr_party.build(party_units, dict(globals(), OUT=OUT, LEGACY=LEGACY))']
    additions = {main.body[0].lineno - 1: prelude, patch.lineno - 1: before_patch, pack.lineno - 1: before_pack}
    nl = '\r\n' if '\r\n' in text else '\n'; out = []; lines = text.splitlines(keepends=True)
    # Party specs describe only appearance. The legacy vision loader adds
    # skills={} even to untouched party entries, violating that sparse contract.
    index = skill_conversion.lineno - 1
    line = lines[index]; indent = line[:len(line) - len(line.lstrip())]
    lines[index] = indent + "if u.get('party') is None:" + nl + '    ' + line
    argument = sprite_call.args[0]
    if argument.lineno != argument.end_lineno: raise RuntimeError('Unsupported sprite converter call layout.')
    lines[argument.lineno - 1] = lines[argument.lineno - 1].replace(ast.get_source_segment(text, argument),
                                                                                'os.path.join(ROOT, "tools", "_ffr_build_sprites.py")')
    stage_indent = ' ' * timeline_stage.col_offset
    lines[timeline_stage.lineno - 1] = stage_indent + 'stage("Writing skill motions and effects" if job.get("kind") in ("skill_motion", "skill_effect") else "Writing the FFBE limit-burst timeline")' + nl
    timeline_build, = [n for n in timeline_loop.body if isinstance(n, ast.Expr) and isinstance(n.value, ast.Call)
                      and ast.unparse(n.value.func) == 'ffbe_resonance.build']
    lines[timeline_build.lineno - 1] = stage_indent + '(_ffr_animation_repair.build_effect_sequence if job.get("kind") == "skill_effect" else ffbe_resonance.build)(job, OUT, BUILD, FFRDT, USMAP, run)' + nl
    indent = lines[icon_tag.lineno - 1][:len(lines[icon_tag.lineno - 1]) - len(lines[icon_tag.lineno - 1].lstrip())]
    lines[icon_tag.lineno - 1] = indent + 'icon_tag = _ffr_existingvisions.command_icon(u, UNITS, UNUSED_ICON_TAGS, rows)' + nl
    for i in range(icon_loop.lineno - 1, icon_loop.end_lineno): lines[i] = '    ' + lines[i]
    lines[icon_loop.lineno - 1] = indent + 'if UNITS.index(u) < len(UNUSED_ICON_TAGS):' + nl + lines[icon_loop.lineno - 1]
    for i, line in enumerate(lines, 1):
        out.append(line)
        if i in additions: out.append(nl.join('    ' + s for s in additions[i]) + nl)
    result = ''.join(out); compile(result, 'make_vision_mod.py', 'exec')
    return (b'\xef\xbb\xbf' if raw.startswith(b'\xef\xbb\xbf') else b'') + result.encode('utf-8')


def hook_server(raw):
    text = raw.decode('utf-8-sig'); tree = ast.parse(text)
    app, = [n for n in tree.body if isinstance(n, ast.Assign) and any(ast.unparse(t) == 'app' for t in n.targets)]
    if not isinstance(app.value, ast.Call) or ast.unparse(app.value.func) != 'FastAPI':
        raise RuntimeError('Unsupported native vision server layout.')
    nl = '\r\n' if '\r\n' in text else '\n'; lines = text.splitlines(keepends=True)
    lines.insert(app.end_lineno, nl.join([MARKER, 'import _ffr_existingvisions', '_ffr_existingvisions.register(app, globals())', '']))
    result = ''.join(lines); compile(result, 'server.py', 'exec')
    return (b'\xef\xbb\xbf' if raw.startswith(b'\xef\xbb\xbf') else b'') + result.encode('utf-8')


def hook_verifier(raw):
    text = raw.decode('utf-8-sig'); tree = ast.parse(text)
    main, = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'main']
    icons, = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'icon_rows']
    count, = [n for n in icons.body if isinstance(n, ast.Assign) and ast.unparse(n.targets[0]) == 'n']
    expected, = [n for n in main.body if isinstance(n, ast.Assign) and ast.unparse(n.targets[0]) == 'expected']
    unexpected, = [n for n in ast.walk(main) if isinstance(n, ast.Assign) and ast.unparse(n.targets[0]) == 'unexpected']
    if ast.unparse(expected.value) != 'expected_rows()' or count.lineno != count.end_lineno or unexpected.lineno != unexpected.end_lineno:
        raise RuntimeError('Unsupported native vision verifier layout.')
    nl = '\r\n' if '\r\n' in text else '\n'; lines = text.splitlines(keepends=True)
    lines[count.lineno - 1] = '    n = len([u for u in json.load(open(spec, encoding="utf-8")) if u.get("native") is None and u.get("party") is None]) if os.path.exists(spec) else 5' + nl
    finish, = [n for n in main.body if isinstance(n, ast.Expr) and isinstance(n.value, ast.Call) and ast.unparse(n.value.func) == 'sys.exit']
    lines[finish.lineno - 1] = '    import _ffr_party' + nl + '    _ffr_party.verify(ROOT, ffrenv.FFRDT, os.path.join(ROOT, "extracted", "Mappings.usmap"))' + nl + lines[finish.lineno - 1]
    additions = {
        expected.end_lineno: [MARKER, 'import _ffr_existingvisions', 'native_expected = _ffr_existingvisions.expected_edits(ROOT)'],
        unexpected.end_lineno: [MARKER, 'unexpected = [k for k in unexpected if k not in changed or not _ffr_existingvisions.expected_row_change(rel, k, orig[k], built[k], native_expected, equivalent)]'],
    }
    out = []
    for i, line in enumerate(lines, 1):
        out.append(line)
        if i in additions:
            indent = line[:len(line) - len(line.lstrip())]
            out.append(nl.join(indent + s for s in additions[i]) + nl)
    result = ''.join(out); compile(result, 'verify_mod.py', 'exec')
    return (b'\xef\xbb\xbf' if raw.startswith(b'\xef\xbb\xbf') else b'') + result.encode('utf-8')


def state(root):
    p = checked(root, STATE + '/state.json')
    if not p.exists(): return None
    value = json.loads(p.read_bytes())
    if value.get('schema') != 1 or set(value.get('sources', {})) != set(SOURCES):
        raise RuntimeError('Unknown existing vision patch state.')
    return value


def originals(root, saved):
    result = {}
    for rel in SOURCES:
        raw = checked(root, rel).read_bytes()
        if MARKER.encode() in raw:
            if not saved or sha(raw) != saved['sources'][rel]['patched']:
                raise RuntimeError('Existing vision hooks have external edits; no files changed.')
            record = saved['sources'][rel]
            original = checked(root, STATE + '/backups/' + record['original'] + '.py').read_bytes()
            if sha(original) != record['original']: raise RuntimeError('Existing vision backup checksum mismatch.')
            result[rel] = original
        else: result[rel] = raw # Updated upstream source is kept, never downgraded.
    return result


def run(root, action):
    saved = state(root); original = originals(root, saved)
    helper = checked(root, HELPER)
    if helper.exists() and (not saved or sha(helper.read_bytes()) != saved['helper']):
        raise RuntimeError('The existing vision helper has external edits; no files changed.')
    resources = {name: checked(root, 'tools/' + name) for name in RESOURCES}
    for name, path in resources.items():
        if path.exists() and (not saved or sha(path.read_bytes()) != saved.get('resources', {}).get(name)):
            raise RuntimeError('A managed vision resource has external edits; no files changed.')
    if action == 'Restore':
        changes = {checked(root, rel): raw for rel, raw in original.items()}
        if helper.exists(): changes[helper] = None
        changes.update({path: None for path in resources.values() if path.exists()})
        transact(changes)
        return {'status': 'restored', 'patchVersion': VERSION}
    version = checked(root, 'VERSION').read_text().strip().split('.')
    if len(version) != 4 or not all(p.isdigit() for p in version) or tuple(map(int, version)) < (1, 0, 0, 15) or version[0] != '1':
        raise RuntimeError('Existing visions need a compatible engine 1.0.0.15 or newer.')
    payload = Path(__file__).parent / 'payload'; manifest = json.loads((payload / 'manifest.json').read_bytes())
    module = (payload / '_ffr_existingvisions.py').read_bytes()
    resource_data = {name: (payload / name).read_bytes() for name in RESOURCES}
    if manifest.get('schema') != 1 or manifest.get('files') != {'_ffr_existingvisions.py': sha(module), **{k: sha(v) for k, v in resource_data.items()}}:
        raise RuntimeError('Existing vision payload checksum mismatch.')
    compile(module, HELPER, 'exec')
    for name, raw in resource_data.items():
        if name.endswith('.py'): compile(raw, name, 'exec')
        else: json.loads(raw)
    patched = {SOURCES[0]: hook_builder(original[SOURCES[0]]), SOURCES[1]: hook_server(original[SOURCES[1]]), SOURCES[2]: hook_verifier(original[SOURCES[2]])}
    changes = {helper: module, **{resources[name]: raw for name, raw in resource_data.items()}}; records = {}
    for rel in SOURCES:
        digest = sha(original[rel]); backup = checked(root, STATE + '/backups/' + digest + '.py')
        if backup.exists() and backup.read_bytes() != original[rel]: raise RuntimeError('Existing vision backup changed.')
        if not backup.exists(): write(backup, original[rel])
        records[rel] = {'original': digest, 'patched': sha(patched[rel])}
    changes[checked(root, STATE + '/state.json')] = json.dumps({'schema': 1, 'version': VERSION, 'sources': records, 'helper': sha(module),
                                                            'resources': {k: sha(v) for k, v in resource_data.items()}}).encode()
    changes.update({checked(root, rel): raw for rel, raw in patched.items()})
    transact(changes)
    return {'status': 'active', 'patchVersion': VERSION}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('--engine', required=True); parser.add_argument('--action', choices=['Apply', 'Restore'], default='Apply')
    args = parser.parse_args()
    try: print(json.dumps(run(Path(args.engine), args.action)))
    except (OSError, ValueError, SyntaxError, RuntimeError, KeyError) as error:
        print('Existing vision setup failed: ' + str(error), file=sys.stderr); sys.exit(1)
