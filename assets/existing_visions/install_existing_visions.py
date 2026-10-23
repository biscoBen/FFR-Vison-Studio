"""Install managed native-vision hooks after the Crystal Fina extension.

Restore these hooks before reapplying Crystal Fina so each installer sees the
source it owns. Neither operation writes the roster or the game files.
"""
import argparse
import ast
import hashlib
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import zipfile

VERSION = '1.2.64'
MARKER = '# FFR-EXISTING-VISIONS v1'
STATE = '.ffr-existing-visions'
SOURCES = ('tools/make_vision_mod.py', 'tools/devui/server.py', 'tools/verify_mod.py')
HELPER = 'tools/_ffr_existingvisions.py'
RESOURCES = ('_ffr_sephira_ffbe.py', 'sephira_blood_recovery.zip', '_ffr_sephira_sequences.py', 'sephira_native_presentations.json', '_ffr_shrine_challenges.py', 'sephira_challenges.json', '_ffr_game_tables.py', '_ffr_fina_boss.py', 'crystal_fina_boss.json', '_ffr_launch.py', 'launch_prep.html', 'launch_demo.json.gz', 'launch_tests.json', '_ffr_ffbe_download.py', 'ffbe_library_manifest.json', 'ffbe_library_browser.zip', '_ffr_ffbe_texture.py', '_ffr_ffbe_uv.py', '_ffr_ffbe_library.py', '_ffr_ffbe_placement.py', '_ffr_ffbe_renderer.py', 'ffbe_library.html', '_ffr_ffbe_needles.py', 'ffbe_needles.zip', '_ffr_native_skills.py', 'native_skill_repairs.json', '_ffr_build_icons.py', 'ability_live_tests.json', 'fina_battle.lua', '_ffr_fina_preview.py', 'fina_battle_preview.zip', '_ffr_fina_battle.py', '_ffr_fina_motion.py', '_ffr_deck_sync.py', '_ffr_sephira.py', 'sephira_visuals.json', '_ffr_ability_modes.py', 'ability_hiding_review.json', '_ffr_testing.py', '_ffr_crystal_cave.py', '_ffr_crystal_mesh.py', 'cave_terrain.json', '_ffr_party.py', '_ffr_party_voices.py', 'party_voice_cues.json', '_ffr_overworld.py', '_ffr_field_leader.py', 'field_leader.lua', 'vagrant_knight_rain_field.png', 'overworld_catalog.json', 'overworld_assets.zip', '_ffr_animation_repair.py', '_ffr_build_sprites.py', '_ffr_library.py', 'ffbe_animation_index.json', 'ffbe_barrage_index.json')


def sha(data):
    return hashlib.sha256(data).hexdigest()


def validate_field_archive(raw, catalog):
    if catalog.get('schema') != 1 or catalog.get('archive_sha256') != sha(raw):
        raise RuntimeError('Directional field archive checksum mismatch.')
    expected = {entry[kind]: entry[kind + '_sha256'] for entry in catalog['models'].values()
                for kind in ('sheet', 'icon')}
    try:
        with zipfile.ZipFile(io.BytesIO(raw)) as archive:
            if set(archive.namelist()) != set(expected) or len(archive.namelist()) != len(expected):
                raise RuntimeError('Directional field archive contents differ from the catalog.')
            for name, digest in expected.items():
                if '/' in name or '\\' in name or not name.endswith('.png'):
                    raise RuntimeError('Unsupported directional field archive member.')
                data = archive.read(name)
                if sha(data) != digest or not data.startswith(b'\x89PNG\r\n\x1a\n'):
                    raise RuntimeError('Directional field sprite checksum mismatch: ' + name)
    except zipfile.BadZipFile as error:
        raise RuntimeError('Invalid directional field archive.') from error


def validate_preview_archive(raw):
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        expected = {'manifest.json', 'idle.webp', 'atk.webp', 'limitatk.webp'}
        if len(archive.namelist()) != len(expected) or set(archive.namelist()) != expected:
            raise RuntimeError('Native Fina preview archive contents differ from the manifest.')
        manifest = json.loads(archive.read('manifest.json'))
        if (manifest.get('schema') != 1 or manifest.get('presentation') != 'native-fina-10'
                or set(manifest.get('animations', {})) != {'idle', 'atk', 'limitatk'}):
            raise RuntimeError('Unsupported native Fina preview archive.')
        for name, entry in manifest['animations'].items():
            if entry.get('file') != name + '.webp' or not 0 < entry.get('seconds', 0) <= 100:
                raise RuntimeError('Invalid native Fina preview entry.')
            data = archive.read(entry['file'])
            if not data.startswith(b'RIFF') or data[8:12] != b'WEBP' or sha(data) != entry.get('sha256'):
                raise RuntimeError('Native Fina preview checksum mismatch.')


def validate_needles_archive(raw):
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        if sorted(archive.namelist()) != ['audio.json', 'manifest.json', 'needle.hca', 'spec.json', 'tex.bgra']:
            raise RuntimeError('Unexpected FFBE Needles archive contents.')
        manifest = json.loads(archive.read('manifest.json'))
        if (manifest.get('schema') != 1 or manifest.get('name') != 'ffbe_needles_test'
                or manifest.get('files') != {k: sha(archive.read(k)) for k in ('spec.json', 'tex.bgra', 'audio.json', 'needle.hca')}):
            raise RuntimeError('FFBE Needles archive checksum mismatch.')
        spec = json.loads(archive.read('spec.json'))
        w, h = spec['pixelSize']
        if w <= 0 or h <= 0 or len(archive.read('tex.bgra')) != w*h*4:
            raise RuntimeError('Invalid FFBE Needles atlas dimensions.')


def validate_blood_archive(raw):
    expected = {'manifest.json', 'audio.json', 'needle.hca',
                *(role + '/' + suffix for role in ('front', 'back', 'flash') for suffix in ('spec.json', 'tex.bgra'))}
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        if len(archive.namelist()) != len(expected) or set(archive.namelist()) != expected:
            raise RuntimeError('Unexpected Blood Recovery archive contents.')
        manifest = json.loads(archive.read('manifest.json'))
        if (manifest.get('schema') != 1 or manifest.get('ability') != 231688
                or manifest.get('files') != {name: sha(archive.read(name)) for name in expected - {'manifest.json'}}):
            raise RuntimeError('Blood Recovery archive checksum mismatch.')
        for role in ('front', 'back', 'flash'):
            width, height = json.loads(archive.read(role + '/spec.json'))['pixelSize']
            if min(width, height) <= 0 or len(archive.read(role + '/tex.bgra')) != width * height * 4:
                raise RuntimeError('Invalid Blood Recovery atlas dimensions.')


def validate_library_browser(raw):
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        if sorted(archive.namelist()) != ['browser.json', 'cactuar.png', 'christine.png']:
            raise RuntimeError('Unexpected animation browser archive contents.')
        metadata = json.loads(archive.read('browser.json'))
        if metadata.get('schema') != 1 or set(metadata.get('actors', {})) != {'character', 'monster'}:
            raise RuntimeError('Unsupported animation browser metadata.')
        for actor in metadata['actors'].values():
            if actor.get('file') not in ('christine.png', 'cactuar.png'):
                raise RuntimeError('Invalid animation browser sprite name.')
            if not archive.read(actor['file']).startswith(b'\x89PNG\r\n\x1a\n'):
                raise RuntimeError('Invalid animation browser sprite.')


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
    layout_source, = [n for n in main.body if isinstance(n, ast.Assign)
                     and ast.unparse(n.targets[0]) == 'layout'
                     and 'DA_UIUnitSsLayout.json' in ast.unparse(n.value)]
    if layout_source.lineno != layout_source.end_lineno:
        raise RuntimeError('Unsupported menu layout source assignment.')
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
    shop_slot, = [n for n in loop.body if isinstance(n, ast.Expr) and isinstance(n.value, ast.Call)
                  and ast.unparse(n.value.func) == 'shop_slots.append']
    shop_start, = [n for n in main.body if isinstance(n, ast.Assign) and ast.unparse(n.targets[0]) == 'shop']
    shop_end, = [n for n in main.body if isinstance(n, ast.Expr) and
                 ast.unparse(n).startswith("tbl('Shop/DT_ShopList')['set'].append(")]
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
    prelude = [MARKER, 'global UNITS, rows', 'import _ffr_game_tables', 'rows = _ffr_game_tables.reader(ROOT, rows)', 'import _ffr_existingvisions', 'import _ffr_animation_repair', 'import _ffr_fina_battle', 'import _ffr_party', 'import _ffr_testing', 'import _ffr_crystal_cave', 'import _ffr_ability_modes',
               'import _ffr_sephira', 'UNITS = _ffr_sephira.visual_units(_ffr_sephira.active_units(UNITS), ROOT, rows)',
               'UNITS = _ffr_sephira.player_units(UNITS, rows)',
               'UNITS = _ffr_sephira.bind_units(UNITS, rows)',
               'UNITS = [_ffr_animation_repair.retire_comparison_skills(u) for u in UNITS]',
               'party_units, UNITS = _ffr_party.split(UNITS, rows)',
               'native_units, UNITS = _ffr_existingvisions.split(UNITS, rows)',
               'for u in native_units + UNITS:', '    if u.get("ffbe"):',
               '        _ffr_animation_repair.repair_unit(u, ROOT)',
               'for u in native_units:', '    if u.get("ffbe"):',
               '        stage("Preparing original sprites: " + u["en"])',
               '        _ffr_existingvisions.ensure_sprite_templates(u, LEGACY,',
               '            lambda folder: run(ffrenv.py(os.path.join(ROOT, "tools", "extract_legacy.py"), "--filter", folder)))',
               '_ffr_ability_modes.prepare_barrage_trial(native_units + UNITS, ROOT, rows)',
               'def _native_skills(u):',
               '    nonlocal clones, post_objects, post_bytecode, post_frames, post_retime, authored_sequences, effect_jobs, built_effects',
               '    vid = u["id"]', '    d = u["donor"]',
               *['    ' + s for s in skill_body.splitlines()]]
    before_patch = [MARKER, '_ffr_sephira.prepare(tables, UNITS)', 'for u in native_units:', '    _native_skills(u)',
                    '_ffr_existingvisions.prepare(tables, objects, native_units, ROOT, rows)',
                    '_ffr_party.prepare(tables, party_units, rows)',
                    'import _ffr_party_voices',
                    '_ffr_party_voices.prepare(objects, clones, post_objects, party_units, ROOT, rows,',
                    '    lambda folder: run(ffrenv.py(os.path.join(ROOT, "tools", "extract_legacy.py"), "--filter", folder)), seq_dumps)',
                    '_ffr_testing.ensure_assets(ROOT, lambda folder: run(ffrenv.py(os.path.join(ROOT, "tools", "extract_legacy.py"), "--filter", folder)))',
                    '_ffr_testing.prepare(tables, party_units + native_units + UNITS, ROOT, rows)',
                    '_ffr_ability_modes.prepare_sequences(tables, clones, authored_sequences, native_units + UNITS, ROOT, rows,',
                    '    lambda folder: run(ffrenv.py(os.path.join(ROOT, "tools", "extract_legacy.py"), "--filter", folder)),',
                    '    native_support={"clone": clone_sequence, "dumps": seq_dumps, "keys": event_keys,',
                    '                    "objects": post_objects, "bytecode": post_bytecode})', '_ffr_game_tables.normalize(ROOT, tables, rows)']
    before_pack = [MARKER, '_ffr_testing.build_practice(dict(globals(), OUT=OUT, LEGACY=LEGACY))', 'import _ffr_ffbe_needles',
                   '_ffr_ffbe_needles.build(dict(globals(), OUT=OUT, LEGACY=LEGACY))', 'import _ffr_sephira_ffbe',
                   '_ffr_sephira_ffbe.build(native_units + UNITS, dict(globals(), OUT=OUT, LEGACY=LEGACY))', 'for u in native_units:',
                   '    if u.get("ffbe"):', '        stage("Replacing sprites: " + u["en"])', '        generate_sprites(u)',
                   '_ffr_existingvisions.copy_materials(native_units, ROOT, OUT)',
                   '_ffr_party.build(party_units, dict(globals(), OUT=OUT, LEGACY=LEGACY))',
                   '_ffr_crystal_cave.build(native_units + UNITS, dict(globals(), OUT=OUT, LEGACY=LEGACY))',
                   'import _ffr_shrine_challenges',
                   '_ffr_shrine_challenges.build(UNITS, dict(globals(), OUT=OUT, LEGACY=LEGACY, rows=rows))',
                   'import _ffr_fina_battle',
                   '_ffr_fina_battle.build(native_units + UNITS, dict(globals(), OUT=OUT, LEGACY=LEGACY, rows=rows))',
                   'import _ffr_field_leader',
                   '_ffr_field_leader.build(party_units + native_units + UNITS, dict(globals(), OUT=OUT, LEGACY=LEGACY, rows=rows))']
    early_check = ['stage("Checking game tables before sprite conversion")',
                   '_ffr_testing.verify_table_recipe(ROOT, FFRDT, USMAP)',
                   '_ffr_sephira.verify_runtime_rows(ROOT, FFRDT, USMAP, UNITS, rows)']
    additions = {main.body[0].lineno - 1: prelude, patch.lineno - 1: before_patch,
                 timeline_loop.lineno - 1: early_check, pack.lineno - 1: before_pack}
    nl = '\r\n' if '\r\n' in text else '\n'; out = []; lines = text.splitlines(keepends=True)
    lines[layout_source.lineno - 1] = '    layout = _ffr_existingvisions.menu_layout(dict(globals(), LEGACY=LEGACY), UNITS)' + nl
    # Party specs describe only appearance. The legacy vision loader adds
    # skills={} even to untouched party entries, violating that sparse contract.
    index = skill_conversion.lineno - 1
    line = lines[index]; indent = line[:len(line) - len(line.lstrip())]
    lines[index] = indent + "if u.get('party') is None:" + nl + '    ' + line
    roster_loop, = [n for n in ast.walk(loader) if isinstance(n, ast.For) and ast.unparse(n.iter) == 'units']
    loader_indent = ' ' * roster_loop.col_offset
    lines[roster_loop.lineno - 1] = loader_indent + 'import _ffr_sephira' + nl + loader_indent + 'units = _ffr_sephira.active_units(units)' + nl + lines[roster_loop.lineno - 1]
    # A cave-selected vision is acquired inside its cave, not also sold in Mitra.
    index = shop_slot.lineno - 1
    indent = lines[index][:len(lines[index]) - len(lines[index].lstrip())]
    lines[index] = indent + 'if _ffr_crystal_cave.assignment(u) is None:' + nl + '    ' + lines[index]
    for i in range(shop_start.lineno - 1, shop_end.end_lineno): lines[i] = ''
    lines[shop_start.lineno - 1] = '    _ffr_crystal_cave.prepare_shops(tables, UNITS, rows)' + nl
    argument = sprite_call.args[0]
    if argument.lineno != argument.end_lineno: raise RuntimeError('Unsupported sprite converter call layout.')
    lines[argument.lineno - 1] = lines[argument.lineno - 1].replace(ast.get_source_segment(text, argument),
                                                                                'os.path.join(ROOT, "tools", "_ffr_build_sprites.py")')
    icon_argument, = [n for n in ast.walk(tree) if isinstance(n, ast.Call)
                      and ast.unparse(n.func) == 'os.path.join'
                      and [a.value for a in n.args if isinstance(a, ast.Constant)] ==
                          ['tools', 'ffbe2ss6', 'build_icons.py']]
    if icon_argument.lineno != icon_argument.end_lineno:
        raise RuntimeError('Unsupported icon converter call layout.')
    lines[icon_argument.lineno - 1] = lines[icon_argument.lineno - 1].replace(
        ast.get_source_segment(text, icon_argument), 'os.path.join(ROOT, "tools", "_ffr_build_icons.py")')
    stage_indent = ' ' * timeline_stage.col_offset
    lines[timeline_stage.lineno - 1] = stage_indent + 'stage("Writing skill motions and effects" if job.get("kind") in ("skill_motion", "skill_effect") else "Writing the FFBE limit-burst timeline")' + nl
    timeline_build, = [n for n in timeline_loop.body if isinstance(n, ast.Expr) and isinstance(n.value, ast.Call)
                      and ast.unparse(n.value.func) == 'ffbe_resonance.build']
    lines[timeline_build.lineno - 1] = stage_indent + 'job = _ffr_fina_battle.prepare_job(job, native_units + UNITS, lb_id)' + nl + stage_indent + '(_ffr_animation_repair.build_effect_sequence if job.get("kind") == "skill_effect" else ffbe_resonance.build)(job, OUT, BUILD, FFRDT, USMAP, run)' + nl
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
    # The upstream server has one package ledger and backup directory for every
    # selected game. Resolve all reads/writes against the selected installation.
    source_lines = text.splitlines(keepends=True)
    edits = []
    functions = [n for n in tree.body if isinstance(n, ast.FunctionDef)]
    ledger_functions = {f.name for f in functions} & {'_game_state', '_save_game_state'}
    for function in functions:
        # Bind mutations to the paks folder captured by the operation, even if
        # the selected folder changes while its files are being copied.
        game = ('_game_root(paks)' if function.name in ('install_files', 'restore_game') else
                '(_game_root(paks) if paks else None)' if function.name in ('game_files', 'status') else
                '(game or ffrenv.detect_game())' if function.name in ledger_functions else 'ffrenv.detect_game()')
        if function.name in ledger_functions:
            line = source_lines[function.lineno - 1].encode('utf-8')
            closing = line.index(b'):')
            edits.append((function.lineno, closing, closing,
                          (', game=None' if function.args.args else 'game=None').encode()))
        for node in ast.walk(function):
            replacement = None
            if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load) and node.id in ('GAME_STATE', 'BACKUPS'):
                method = 'game_state_path' if node.id == 'GAME_STATE' else 'backup_root'
                replacement = '_ffr_field_leader.' + method + '(ROOT, ' + game + ')'
            elif (function.name not in ledger_functions and isinstance(node, ast.Call)
                  and isinstance(node.func, ast.Name) and node.func.id in ledger_functions):
                if node.lineno != node.end_lineno: raise RuntimeError('Unsupported installation ledger call.')
                arguments = [ast.get_source_segment(text, arg) for arg in node.args]
                replacement = node.func.id + '(' + ', '.join([*arguments, game]) + ')'
            if replacement is not None:
                if node.lineno != node.end_lineno: raise RuntimeError('Unsupported installation ledger reference.')
                edits.append((node.lineno, node.col_offset, node.end_col_offset, replacement.encode('utf-8')))
    for lineno, start, stop, replacement in sorted(edits, key=lambda e: e[:3], reverse=True):
        line = source_lines[lineno - 1].encode('utf-8')
        source_lines[lineno - 1] = (line[:start] + replacement + line[stop:]).decode('utf-8')
    text = ''.join(source_lines); tree = ast.parse(text)
    app, = [n for n in tree.body if isinstance(n, ast.Assign) and any(ast.unparse(t) == 'app' for t in n.targets)]
    if not isinstance(app.value, ast.Call) or ast.unparse(app.value.func) != 'FastAPI':
        raise RuntimeError('Unsupported native vision server layout.')
    nl = '\r\n' if '\r\n' in text else '\n'; lines = text.splitlines(keepends=True)
    build, = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'run_build']
    # Invalidate the prior export on every attempt; only a verified successful
    # build records a new snapshot, including its exact cycling payload.
    lines[build.body[0].lineno - 1] = nl.join([
        '    import _ffr_deck_sync, _ffr_launch',
        '    try:',
        '        launch_start = _ffr_launch.guard(globals())',
        '        launch_start["inputsSha256"] = _ffr_deck_sync.inputs_digest(ROOT)',
        '        _ffr_deck_sync.begin_build(ROOT)',
        '    except Exception as launch_error:',
        '        state.update(running=False, result="failed", message=str(launch_error))',
        '        return',
    ]) + nl + lines[build.body[0].lineno - 1]
    verified, = [n for n in ast.walk(build) if isinstance(n, ast.If) and ast.unparse(n.test) == 'v.returncode != 0']
    indent = ' ' * verified.col_offset
    lines[verified.lineno - 1] = (indent + 'if v.returncode == 0: _ffr_launch.capture_build(globals(), launch_start)' + nl + lines[verified.lineno - 1])
    setup_call, = [n for n in ast.walk(tree) if isinstance(n, ast.Call) and ast.unparse(n.func) == 'studio_setup.prepare']
    old = ast.get_source_segment(text, setup_call)
    lines[setup_call.lineno - 1] = lines[setup_call.lineno - 1].replace(old,
        '_ffr_launch.prepare_game(game, studio_setup, globals(), log=lambda m: setup_state["log"].append(str(m)))')
    status_fn, = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'status']
    status_return, = [n for n in status_fn.body if isinstance(n, ast.Return)]
    status_text = ast.get_source_segment(text, status_return)
    augmented = 'return {**(' + ast.get_source_segment(text, status_return.value) + '), **_ffr_launch.brief(globals())}'
    if status_return.lineno != status_return.end_lineno:
        for index in range(status_return.lineno - 1, status_return.end_lineno): lines[index] = ''
        lines[status_return.lineno - 1] = ' ' * status_return.col_offset + augmented + nl
    else: lines[status_return.lineno - 1] = lines[status_return.lineno - 1].replace(status_text, augmented)
    finish, = [n for n in build.body if isinstance(n, ast.Assign) and ast.unparse(n.targets[0]) == "state['stage']"]
    lines[finish.lineno - 1] = nl.join([
        '    try:', '        if state["result"] == "ok": _ffr_deck_sync.capture(globals())',
        '    except Exception as deck_error:', '        note("Deck export is unavailable: " + str(deck_error))',
    ]) + nl + lines[finish.lineno - 1]
    route, = [n for n in tree.body if isinstance(n, ast.AsyncFunctionDef) and n.name == 'build']
    thread, = [n for n in route.body if isinstance(n, ast.Expr) and 'threading.Thread' in ast.unparse(n)]
    lines[thread.lineno - 1] = nl.join([
        '    import _ffr_deck_sync', '    with _ffr_deck_sync._operation:',
        '        if state["running"] or _ffr_deck_sync._publishing["running"]:',
        '            raise HTTPException(409, "A build or private publish is running.")',
        '        state["running"] = True',
    ]) + nl + '    ' + lines[thread.lineno - 1]
    install, = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'install_files']
    restore, = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'restore_game']
    # Preflight ownership/loader before package copies, then deploy only after
    # those copies succeed. No changes to another loader or mod's configuration.
    lines[install.body[0].lineno - 1] = '    _ffr_launch.guard(globals(), installing=True)' + nl + lines[install.body[0].lineno - 1]
    state, = [n for n in install.body if isinstance(n, ast.Assign) and ast.unparse(n.targets[0]) == 'st']
    returned, = [n for n in install.body if isinstance(n, ast.Return)]
    lines[state.lineno - 1] = '    import _ffr_field_leader' + nl + '    leader_plan = _ffr_field_leader.install_plan(ROOT, _game_root(paks))' + nl + lines[state.lineno - 1]
    lines[returned.lineno - 1] = '    _ffr_field_leader.deploy(leader_plan, bdir)' + nl + lines[returned.lineno - 1]
    game, = [n for n in restore.body if isinstance(n, ast.Assign) and ast.unparse(n.targets[0]) == 'game']
    lines[game.lineno - 1] += '    import _ffr_field_leader' + nl + '    leader_plan = _ffr_field_leader.restore_plan(ROOT, game, backup)' + nl
    for returned in [n for n in ast.walk(restore) if isinstance(n, ast.Return)]:
        indent = ' ' * returned.col_offset
        lines[returned.lineno - 1] = indent + '_ffr_field_leader.deploy(leader_plan)' + nl + lines[returned.lineno - 1]
    lines.insert(app.end_lineno, nl.join([MARKER, 'import _ffr_existingvisions, _ffr_launch, _ffr_field_leader', '_ffr_existingvisions.register(app, globals())', '']))
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
    lines[count.lineno - 1] = '    import _ffr_sephira' + nl + '    n = len([u for u in _ffr_sephira.active_units(json.load(open(spec, encoding="utf-8"))) if u.get("native") is None and u.get("party") is None]) if os.path.exists(spec) else 5' + nl
    finish, = [n for n in main.body if isinstance(n, ast.Expr) and isinstance(n.value, ast.Call) and ast.unparse(n.value.func) == 'sys.exit']
    lines[finish.lineno - 1] = '    import _ffr_testing' + nl + '    _ffr_testing.verify(ROOT, ffrenv.FFRDT, os.path.join(ROOT, "extracted", "Mappings.usmap"))' + nl + '    import _ffr_party' + nl + '    _ffr_party.verify(ROOT, ffrenv.FFRDT, os.path.join(ROOT, "extracted", "Mappings.usmap"))' + nl + '    import _ffr_crystal_cave' + nl + '    _ffr_crystal_cave.verify_shops(ROOT, ffrenv.FFRDT, os.path.join(ROOT, "extracted", "Mappings.usmap"))' + nl + lines[finish.lineno - 1]
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
        elif name.endswith(('.lua', '.html')): raw.decode('utf-8')
        elif name.endswith('.json'): json.loads(raw)
        elif name == 'launch_demo.json.gz':
            import gzip
            if json.loads(gzip.decompress(raw)).get('kind') != 'ffr-native-reference':
                raise RuntimeError('Invalid demo comparison metadata.')
        elif name.endswith('.png'):
            if not raw.startswith(b'\x89PNG\r\n\x1a\n'):
                raise RuntimeError('Existing vision field sheet is not a PNG.')
        elif name == 'overworld_assets.zip':
            validate_field_archive(raw, json.loads(resource_data['overworld_catalog.json']))
        elif name == 'fina_battle_preview.zip': validate_preview_archive(raw)
        elif name == 'ffbe_needles.zip': validate_needles_archive(raw)
        elif name == 'sephira_blood_recovery.zip': validate_blood_archive(raw)
        elif name == 'ffbe_library_browser.zip': validate_library_browser(raw)
        else: raise RuntimeError('Unsupported existing vision resource: ' + name)
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
