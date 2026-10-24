"""Build-scoped reuse above the native command cache; retain existing entries."""
import functools
import json
from pathlib import Path
import time

import _ffr_build_cache as reuse


def _groups(cache, cmd):
    args = list(map(str, cmd))
    if args[:len(cache.tool)] != cache.tool: return None
    tail = args[len(cache.tool):]
    if len(tail) < 2 or tail[0] != 'patch': return None
    plan = json.loads(Path(tail[1]).read_text(encoding='utf-8-sig'))
    if set(plan) - {'legacyRoot', 'outRoot', 'tables', 'objects', 'clones'}: return None
    if Path(plan['legacyRoot']).resolve() == Path(plan['outRoot']).resolve(): return None
    grouped = {}
    for kind in ('tables', 'objects', 'clones'):
        for operation in plan.get(kind, []):
            asset = operation['to'] if kind == 'clones' else operation['asset']
            group = grouped.setdefault(asset, {k: plan[k] for k in ('legacyRoot', 'outRoot')})
            group.setdefault(kind, []).append(operation)
    folder = cache.root / 'build/reuse-plans'; folder.mkdir(parents=True, exist_ok=True)
    result = []
    for asset, group in grouped.items():
        recipe = folder / (reuse.digest(asset)[:24] + '.json')
        recipe.write_text(json.dumps(group), encoding='utf-8')
        command = [*cache.tool, 'patch', str(recipe), *tail[2:]]
        spec = cache.command(command)
        if spec is None: return None
        _, _, inputs, targets = spec
        inputs = [p for p in inputs if Path(p) != recipe]
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
        path = cache.root / 'build/reuse-plans/changed.json'
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
    original_run = cache.run
    def run(cmd, original):
        try: groups = _groups(cache, cmd)
        except (OSError, ValueError, KeyError, TypeError): groups = None
        if not groups: return original_run(cmd, original)
        executed = []
        def action(actual):
            executed.append(True)
            return patch_assets(cache, actual, original, groups)
        result = original_run(cmd, action)
        if not executed:
            # Seed individual assets from an already verified whole-patch hit.
            # A small setting edit can then reuse them on the very next build.
            for group, inputs, targets, value, fingerprint in groups:
                if cache.inputs(inputs) != value['sources']:
                    raise ValueError('Native patch inputs changed during generation. Retry the build.')
                cache.execute('asset-patch', value, [], targets, lambda: None)
        return result
    cache.run = run
    import _ffr_fina_battle as battle
    import _ffr_fina_cinematic as movie
    if not getattr(battle.build, '_incremental', False):
        battle.build = _presentation(battle.build)
    if not getattr(movie.build, '_incremental', False):
        movie.build = _cinematic(movie.build)


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
        old = f'Chara/summon/summon{unit["id"]}/summon{unit["id"]}'
        private_boss = unit['id'] == 29670
        if private_boss: old = 'Chara/summon/summon13108/summon13108'
        templates = [(legacy if private_boss else out) / ('FFRS/Content/' + old + s + '.uasset')
                     for s in ('', '_tex', '_normal', '_mreo')]
        _ensure_native(env, templates if private_boss else [])
        spec = (root / 'tools/crystal_fina_boss.json' if private_boss else
                root / 'build/sprites' / unit['key'] / 'battle/spec.json')
        sheet = root / unit['ffbe']['dir'] / ('unit_anime_' + battle.SPRITE + '.png') if not private_boss else None
        inputs = [*native, *tables, *templates, spec, env['USMAP'],
                  *_sources(root, [battle, motion, cave])]
        if sheet is not None: inputs.append(sheet)
        name = 'FinaNative' + str(unit['id'])
        outputs = [out / ('FFRS/Content/' + battle.package(unit, leaf) + '.uasset')
                   for leaf in ('SM_Studio_CrystalFina', 'MI_Studio_CrystalFina', name, name+'_tex', name+'_normal', name+'_mreo')]
        outputs += [out / ('FFRS/Content/' + battle.glow_package(unit) + '.uasset'), *tables,
                    root / 'build/crystal-fina-battle/runtime.json']
        value = {'revision': 1, 'id': unit['id'], 'jp': unit['jp'], 'boss': private_boss,
                 'enemyMotion': testing.settings(root)['practiceBattle'] or challenges.needs_enemy_motion(unit)
                                or sephira.membership(unit) is not None}
        hit = cache.execute('fina-presentation', value, inputs, outputs, lambda: original(units, env))
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
                  (movie.MASTER, movie.MOVIE, movie.MOVIE+'_vp9', music.CUE_DONOR, music.SOUND, ffbe_resonance.SHELL)]
        _ensure_native(env, inputs)
        inputs += [out / (job['asset'] + '.uasset'), root / 'tools/fina_cinematic.zip', env['USMAP'],
                   *_sources(root, [movie, music, cave, ffbe_resonance])]
        outputs = [out / (job['asset'] + '.uasset')]
        outputs += [out / (str(Path(job['asset']).parent / 'Track' / f'SEQ_Battle_{sid + 1}_{s}') + '.uasset')
                    for s in ('Cut_000', 'Sound_001', 'Effect_000')]
        outputs += [out / (p + '.uasset') for p in (movie.PRIVATE, movie.PRIVATE+'_vp9', music.CUE)]
        outputs += [root / 'build/fina-cinematic/timeline.json']
        hit = cache.execute('fina-movie', {'revision': 1, 'asset': job['asset'], 'plan': job['plan']}, inputs, outputs,
                            lambda: original(units, env))
        if hit:
            movie.prepare_pak(root, env['ffrenv'], env['run'], movie.payload()[1]['movie.usm'])
            print('  Crystal Fina movie/music: reused verified native timeline and movie descriptors.', flush=True)
    build._incremental = True
    return build
