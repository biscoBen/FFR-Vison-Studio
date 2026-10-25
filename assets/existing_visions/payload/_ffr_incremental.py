"""Build-scoped reuse above the native command cache; retain existing entries."""
import functools
import ast
import json
from pathlib import Path
import time

import _ffr_build_cache as reuse


def _groups(cache, cmd, plan=None):
    args = list(map(str, cmd))
    if args[:len(cache.tool)] != cache.tool: return None
    tail = args[len(cache.tool):]
    if len(tail) < 2 or tail[0] != 'patch': return None
    if plan is None: plan = json.loads(Path(tail[1]).read_text(encoding='utf-8-sig'))
    if set(plan) - {'legacyRoot', 'outRoot', 'tables', 'objects', 'clones'}: return None
    if Path(plan['legacyRoot']).resolve() == Path(plan['outRoot']).resolve(): return None
    grouped = {}
    for kind in ('tables', 'objects', 'clones'):
        for operation in plan.get(kind, []):
            asset = operation['to'] if kind == 'clones' else operation['asset']
            group = grouped.setdefault(asset, {k: plan[k] for k in ('legacyRoot', 'outRoot')})
            group.setdefault(kind, []).append(operation)
    result = []
    candidates = {}
    def paths(value):
        if isinstance(value, str) and len(value) < 1024:
            p = Path(value)
            if p.is_absolute():
                if value not in candidates: candidates[value] = p.is_file()
                if candidates[value]: return [value]
        elif isinstance(value, dict):
            return [p for v in value.values() for p in paths(v)]
        elif isinstance(value, list):
            return [p for v in value for p in paths(v)]
        return []
    for asset, group in grouped.items():
        inputs = [tail[tail.index('--usmap') + 1]] if '--usmap' in tail else []
        targets = []
        for kind in ('tables', 'objects', 'clones'):
            for operation in group.get(kind, []):
                source = operation['from'] if kind == 'clones' else operation['asset']
                inputs.append(Path(group['legacyRoot']) / (source + '.uasset'))
                targets.append(Path(group['outRoot']) / (asset + '.uasset'))
        inputs += paths(group)
        targets = list(dict.fromkeys(targets))
        if any(not p.resolve().is_relative_to(cache.root) for p in targets): return None
        value = {'revision': 1, 'recipe': group, 'options': tail[2:], 'sources': cache.inputs(inputs)}
        fingerprint = reuse.digest({'context': cache.context, 'kind': 'asset-patch', 'value': value, 'inputs': []})
        result.append((group, inputs, targets, value, fingerprint))
    # This fast path reads immutable native sources, never another group's output.
    outputs = {str(p.resolve()) for g, i, ts, v, f in result for p in ts}
    if any(str(Path(p).resolve()) in outputs for g, ins, ts, v, f in result for p in ins): return None
    return result


def patch_assets(cache, cmd, original, groups):
    dirty = []; start = time.monotonic()
    stat = cache.stats.setdefault('asset-patch', {'reused': 0, 'built': 0, 'seconds': 0.0})
    for record in groups:
        group, inputs, targets, value, fingerprint = record
        if cache.restore(cache.directory / fingerprint[:32], fingerprint, targets): stat['reused'] += 1
        else: dirty.append(record)
    stat['seconds'] += time.monotonic() - start
    result = None
    if dirty:
        partial = {k: dirty[0][0][k] for k in ('legacyRoot', 'outRoot')}
        for group, inputs, targets, value, fingerprint in dirty:
            for kind in ('tables', 'objects', 'clones'):
                if kind in group: partial.setdefault(kind, []).extend(group[kind])
        path = cache.root / 'build/reuse-plans/changed.json'; path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(partial), encoding='utf-8')
        args = list(cmd); args[len(cache.tool) + 1] = str(path)
        result = original(args)
        for group, inputs, targets, value, fingerprint in dirty:
            if cache.inputs(inputs) != value['sources']:
                raise ValueError('Native patch inputs changed during generation. Retry the build.')
            cache.execute('asset-patch', value, [], targets, lambda: None)
    print(f'  Native patch assets: {len(groups) - len(dirty)} reused / {len(dirty)} built.', flush=True)
    return result


def install(env):
    cache = reuse._active
    if cache is None or getattr(cache, '_incremental_installed', False): return
    cache._incremental_installed = True
    _sprite_dependencies(cache)
    original_run = cache.run
    def run(cmd, original):
        args = list(map(str, cmd))
        if args[:len(cache.tool)] != cache.tool or args[len(cache.tool):len(cache.tool)+1] != ['patch']:
            return original_run(cmd, original)
        try:
            plan = json.loads(Path(args[len(cache.tool)+1]).read_text(encoding='utf-8-sig'))
            supported = not set(plan)-{'legacyRoot','outRoot','tables','objects','clones'} and Path(plan['legacyRoot']).resolve()!=Path(plan['outRoot']).resolve()
            if not supported: return original_run(cmd, original)
            spec = cache.command(cmd)
            if spec is None: return original(cmd)
            kind, value, inputs, targets = spec
            fingerprint = reuse.digest({'context':cache.context,'kind':kind,'value':value,'inputs':cache.inputs(inputs)})
            entry = cache.directory / fingerprint[:32]
            marker = entry / 'split-index.json'
            try: indexed = json.loads(marker.read_bytes()) == {'schema':1,'fingerprint':fingerprint}
            except (OSError,ValueError,TypeError): indexed = False
        except (OSError, ValueError, KeyError, TypeError):
            return original_run(cmd, original)
        groups = None; executed = []
        def action(actual):
            nonlocal groups
            executed.append(True)
            groups = _groups(cache, actual, plan)
            return patch_assets(cache, actual, original, groups) if groups else original(actual)
        returned = []
        cache.execute(kind,value,inputs,targets,lambda:returned.append(action(cmd)))
        result = returned[0] if returned else None
        if not executed and not indexed:
            # Seed individual assets from an already verified whole-patch hit.
            # Do not restore each package a second time after the whole hit.
            groups = _groups(cache, cmd, plan)
            for group, group_inputs, group_targets, group_value, group_fingerprint in groups or []:
                if cache.inputs(group_inputs) != group_value['sources']:
                    raise ValueError('Native patch inputs changed during generation. Retry the build.')
                try: present = json.loads((cache.directory/group_fingerprint[:32]/'manifest.json').read_bytes()).get('fingerprint') == group_fingerprint
                except (OSError, ValueError, TypeError): present = False
                if not present: cache.execute('asset-patch', group_value, [], group_targets, lambda: None)
        if groups:
            try:
                if json.loads((entry/'manifest.json').read_bytes()).get('fingerprint') == fingerprint:
                    temporary = marker.with_suffix('.tmp'); temporary.write_text(json.dumps({'schema':1,'fingerprint':fingerprint}))
                    temporary.replace(marker)
            except (OSError, ValueError, TypeError): pass
        return result
    cache.run = run
    import _ffr_fina_battle as battle
    import _ffr_fina_cinematic as movie
    if not getattr(battle.build, '_incremental', False):
        battle.build = _presentation(battle.build)
    if not getattr(movie.build, '_incremental', False):
        movie.build = _cinematic(movie.build)


# Audited 1.2.80 sprite dependency: cave placement, levels and dialog text do
# not affect converted pixels or motions. Preserve its existing cache keys
# while checking the exact motion-call contract, rather than the entire file.
_SHRINE_SPRITE_SOURCE = '6c0a942322749e3c10e5e7c2a7dd2ab436dcf0dcc35dd2ff3173f289cae08d38'
_SHRINE_SPRITE_CONTRACT = '124450711ed49a35a4366af698bdfb0d630b119ead315da79394f0070f8e64c6'
_SEPHIRA_SPRITE_SOURCE = '94ea55499755b9e6abe5f02abf5add547bba48755430b0b6a4eb024ecbfdbf55'
_SEPHIRA_SPRITE_CONTRACT = '46234d2ce2395104f2a9a80f7a0eab7963c6bd1a5be57587406ceefde3890992'


def _ast_contract(node):
    # Ignore empty optional fields added/omitted by different Python versions.
    if isinstance(node, ast.AST):
        return [type(node).__name__,{k:_ast_contract(v) for k,v in ast.iter_fields(node) if v is not None and v!=[]}]
    if isinstance(node, list): return [_ast_contract(v) for v in node]
    return node


def _sprite_dependencies(cache):
    original_file, original_execute = cache.file, cache.execute
    shrine = str((cache.root/'tools/_ffr_shrine_challenges.py').resolve())
    sephira = str((cache.root/'tools/_ffr_sephira.py').resolve())
    scope = [False]; signatures = {}
    def file(path):
        record = original_file(path)
        if not scope[0] or record[0] not in (shrine,sephira) or record[1] is None: return record
        if record[1] not in signatures:
            try:
                tree = ast.parse(Path(path).read_text(encoding='utf-8-sig'))
                if record[0] == shrine:
                    selected = {'data','route','needs_enemy_motion','enemy_motion_for'}
                    contract = [_ast_contract(n) for n in tree.body
                                if isinstance(n,ast.FunctionDef) and n.name in selected]
                    constants = [n for n in tree.body if isinstance(n,ast.Assign)
                                 and any(isinstance(t,ast.Name) and t.id=='DATA' for t in n.targets)]
                    data_name = ast.literal_eval(constants[0].value) if len(constants)==1 else None
                    data = json.loads(Path(path).with_name(data_name).read_bytes())
                    contract += [data_name, data['schema'], sorted(s['origin'] for s in data['encounters'])]
                    expected,source = _SHRINE_SPRITE_CONTRACT,_SHRINE_SPRITE_SOURCE
                else:
                    selected = {'runtime_membership','membership','active_units','native_motion_for','native_motion_names'}
                    contract = [_ast_contract(n) for n in tree.body
                        if isinstance(n,ast.FunctionDef) and n.name in selected
                        or isinstance(n,(ast.Import,ast.ImportFrom))
                        or isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id in {'FIELD','RETIRED'} for t in n.targets)]
                    expected,source = _SEPHIRA_SPRITE_CONTRACT,_SEPHIRA_SPRITE_SOURCE
                signatures[record[1]] = source if reuse.digest(contract)==expected else record[1]
            except (OSError,ValueError,TypeError,KeyError,IndexError): signatures[record[1]] = record[1]
        return [record[0],signatures[record[1]]]
    def execute(kind,value,inputs,targets,action):
        previous = scope[0]; scope[0] = kind == 'sprites'
        try:
            if scope[0] and not value.get('nativeCaster',True):
                import _ffr_shrine_challenges as challenges
                roster=cache.root/'mods/EstherTsukiko/units.json'
                units=json.loads(roster.read_bytes()) if roster.is_file() else []
                value={**value,'challengeEnemyMotion':challenges.enemy_motion_for(units,value['id'])}
            return original_execute(kind,value,inputs,targets,action)
        finally: scope[0] = previous
    cache.file=file; cache.execute=execute


def _sources(root, modules):
    return [Path(__file__), *[Path(m.__file__) for m in modules]]


def _ensure_native(env, paths):
    legacy = Path(env['LEGACY'])
    for path in paths:
        if path.suffix not in ('.uasset', '.umap') or path.is_file(): continue
        rel = path.relative_to(legacy / 'FFRS/Content').with_suffix('').as_posix()
        env['run'](env['ffrenv'].py(str(Path(env['ROOT']) / 'tools/extract_legacy.py'), '--filter', rel))


def _presentation(original):
    @functools.wraps(original)
    def build(units, env):
        import _ffr_fina_battle as battle
        import _ffr_fina_motion as motion
        import _ffr_crystal_cave as cave
        import _ffr_testing as testing
        import _ffr_shrine_challenges as challenges
        import _ffr_sephira as sephira
        cache = reuse._active; unit = battle.selected(units, env['ROOT'])
        if cache is None or unit is None: return original(units, env)
        root, legacy, out = (Path(env[n]) for n in ('ROOT', 'LEGACY', 'OUT'))
        native = [legacy / ('FFRS/Content/' + rel + ('.umap' if rel == cave.TEST_BACKGROUND else '.uasset'))
                  for rel in (battle.AURA, cave.TEST_BACKGROUND, cave.TEST_NATIVE_MESH, cave.TEST_NATIVE_MATERIAL,
                              cave.TEST_NATIVE_SHADER, cave.TEST_SPRITE.removeprefix('/Game/'),
                              cave.TEST_SPRITE.removeprefix('/Game/') + '_tex')]
        _ensure_native(env, native)
        tables = [out / ('FFRS/Content/Datatable/' + t + '.uasset') for t in (battle.DESIGN_TABLE, battle.UNIT_TABLE)]
        cache.execute('fina-bindings', {'id': unit['id'], 'jp': unit['jp']},
                      [*tables, env['USMAP'], Path(battle.__file__)], tables,
                      lambda: battle.bind_tables(unit, env))
        old = f'Chara/summon/summon{unit["id"]}/summon{unit["id"]}'
        private_boss = unit['id'] == 29670
        if private_boss: old = 'Chara/summon/summon13108/summon13108'
        templates = [(legacy if private_boss else out) / ('FFRS/Content/' + old + s + '.uasset')
                     for s in ('', '_tex', '_normal', '_mreo')]
        _ensure_native(env, templates if private_boss else [])
        spec = (root / 'tools/crystal_fina_boss.json' if private_boss else
                root / 'build/sprites' / unit['key'] / 'battle/spec.json')
        sheet = root / unit['ffbe']['dir'] / ('unit_anime_' + battle.SPRITE + '.png') if not private_boss else None
        inputs = [*native, *templates, spec, env['USMAP'],
                  *_sources(root, [battle, motion, cave])]
        if sheet is not None: inputs.append(sheet)
        name = 'FinaNative' + str(unit['id'])
        outputs = [out / ('FFRS/Content/' + battle.package(unit, leaf) + '.uasset')
                   for leaf in ('SM_Studio_CrystalFina', 'MI_Studio_CrystalFina', name, name+'_tex', name+'_normal', name+'_mreo')]
        outputs += [out / ('FFRS/Content/' + battle.glow_package(unit) + '.uasset'),
                    root / 'build/crystal-fina-battle/runtime.json']
        value = {'revision': 1, 'id': unit['id'], 'jp': unit['jp'], 'boss': private_boss,
                 'enemyMotion': testing.settings(root)['practiceBattle'] or challenges.needs_enemy_motion(unit)
                                or sephira.membership(unit) is not None}
        hit = cache.execute('fina-presentation', value, inputs, outputs,
                            lambda: original(units, dict(env, _fina_tables_bound=True)))
        if hit: print('  Crystal Fina presentation: reused verified body, crystal, glow and runtime data.', flush=True)
    build._incremental = True
    return build


def _cinematic(original):
    @functools.wraps(original)
    def build(units, env):
        import _ffr_fina_cinematic as movie
        import _ffr_fina_cave_music as music
        import _ffr_crystal_cave as cave
        cache = reuse._active
        selected = [u for u in units if movie.matches(u)] if movie.enabled(env['ROOT']) else []
        if cache is None or len(selected) != 1: return original(units, env)
        import ffbe_resonance
        root, legacy, out = (Path(env[n]) for n in ('ROOT', 'LEGACY', 'OUT'))
        sid = env['lb_id'](selected[0]['id'])
        job, = [j for j in env['authored_sequences'] if f'/Skill/{sid}/{sid + 1}/' in j['asset']]
        inputs = [legacy / (rel + '.uasset') for rel in
                  (movie.MASTER, movie.MOVIE, movie.MOVIE+'_vp9', ffbe_resonance.SHELL,
                   music.CUE_DONOR,music.SOUND,music.BANK_DONOR)]
        _ensure_native(env, inputs)
        recording,subkey=music.recording(env)
        inputs += [out / (job['asset'] + '.uasset'), root / 'tools/fina_cinematic.zip', env['USMAP'],
                   recording,root/'tools/sephira_lb_audio.zip',root/'tools/_ffr_cave_music_preview.py',
                   root/'tools/ffbe_effects/acb_native.py',
                   *_sources(root, [movie, music, cave, ffbe_resonance])]
        outputs = [out / (job['asset'] + '.uasset')]
        outputs += [out / (str(Path(job['asset']).parent / 'Track' / f'SEQ_Battle_{sid + 1}_{s}') + '.uasset')
                    for s in ('Cut_000', 'Sound_001', 'Effect_000')]
        outputs += [out / (p + '.uasset') for p in (movie.PRIVATE, movie.PRIVATE+'_vp9')]
        outputs += [out/(p+'.uasset') for p in (music.SHEET,music.CUE)]
        outputs += [root / 'build/fina-cinematic/timeline.json']
        hit = cache.execute('fina-movie', {'revision': 3, 'asset': job['asset'], 'plan': job['plan'],'scoreSubkey':subkey}, inputs, outputs,
                            lambda: original(units, env))
        if hit:
            movie.prepare_pak(root, env['ffrenv'], env['run'], movie.payload()[1]['movie.usm'])
            print('  Crystal Fina movie/music: reused verified native timeline and movie descriptors.', flush=True)
    build._incremental = True
    return build
