"""Independent party appearances and native battle voices, preserving identity."""
import copy
import json
from pathlib import Path

TABLE = 'Asset/Battle/Unit/DT_BtlUnitAsset'
PLAYABLE_TABLE = 'Asset/Battle/Unit/DT_BtlPlayableUnitAsset'
ASSET = 'FFRS/Content/Datatable/' + TABLE
CHARACTERS = (
    (1001, 'レイン', 'Rain', 'unit0010'),
    (1002, 'ラスウェル', 'Lasswell', 'unit0020'),
    (1003, 'フィーナ', 'Fina', 'unit0030'),
    (1004, 'リド', 'Lid', 'unit0040'),
    (1005, 'ニコル', 'Nichol', 'unit0050'),
    (1006, '魔人フィーナ', 'Dark Fina', 'unit0060'),
    (1007, 'ジェイク', 'Jake', 'unit0070'),
    (1008, 'サクラ', 'Sakura', 'unit0080'),
)
FINA = '99887755552703'
VOICE_TABLE = 'Unit/DT_UnitParameter'
VOICE_ASSET = 'FFRS/Content/Datatable/' + VOICE_TABLE
VOICE_BANK_TABLE = 'Asset/Sound/DT_SoundCueSheetAsset'


def identity(id):
    return next((c for c in CHARACTERS if c[0] == id), None)


def snapshot(id, rows):
    c = identity(id)
    if not c or rows(PLAYABLE_TABLE).get(c[1], {}).get('Ss6Project') != c[3]:
        raise ValueError('The original party battle model is unavailable. Prepare the game files again.')
    return {'key': f'party_{id}', 'id': id, 'jp': c[1], 'en': c[2],
            'party': {'version': 1, 'id': id}}


def validate(u):
    c = identity(u.get('id'))
    if (not c or type(u['id']) is not int or u.get('key') != f'party_{c[0]}'
            or u.get('jp') != c[1] or u.get('en') != c[2]
            or u.get('party') != {'version': 1, 'id': c[0]}
            or set(u) - {'key', 'id', 'jp', 'en', 'party', 'ffbe', 'overworld', 'battleVoice', 'menuScale', 'icon'}):
        raise ValueError('Invalid party replacement; its original character identity must be preserved.')
    if 'battleVoice' in u and (type(u['battleVoice']) is not int or not identity(u['battleVoice'])):
        raise ValueError('The battle voice must belong to an original party character.')
    if 'overworld' in u:
        import _ffr_overworld
        _ffr_overworld.validate(u['overworld'])
    ff = u.get('ffbe')
    if ff is not None:
        if not isinstance(ff, dict) or not isinstance(ff.get('id'), str) or not ff['id'].isdigit():
            raise ValueError('Invalid party sprite model.')
        for field in ('dir', 'baseDir'):
            path = ff.get(field)
            if field == 'dir' and not path: raise ValueError('The party sprite folder is missing.')
            if path and (not isinstance(path, str) or '\\' in path or ':' in path
                         or Path(path).is_absolute() or '..' in Path(path).parts
                         or not path.startswith('units/')):
                raise ValueError('The party sprite folder must stay inside the engine units cache.')
        if ff.get('baseDir') and not str(ff.get('baseForm', '')).isdigit():
            raise ValueError('The party model base form is missing.')
    return u


def split(units, rows):
    party = []; others = []; ids = set()
    for u in units:
        if u.get('party') is None:
            others.append(u); continue
        validate(u); snapshot(u['id'], rows)
        if u['id'] in ids or any(v is not u and v.get('id') == u['id'] for v in units):
            raise ValueError('Duplicate party character override.')
        ids.add(u['id']); party.append(u)
    return party, others


def package(u):
    return f'/Game/Chara/StudioParty/party{u["id"]}/{identity(u["id"])[3]}'


def material(u):
    return f'/Game/BP/Map/Unit/Material/M_StudioParty{u["id"]}'


def asset_updates(u):
    path = package(u)
    fields = {'Ss6Project': path, 'textureBaseColor': path + '_tex', 'textureNormal': path + '_normal',
              'textureMetallicRoughness': path + '_mreo'}
    if str(u['ffbe']['id']) == FINA: fields['Material'] = material(u)
    return {'animationAssetList[0].' + key: value for key, value in fields.items()}


def prepare(tables, units, rows):
    """Patch the runtime soft paths alongside existing vision table operations.

    DT_BtlPlayableUnitAsset supplies resource names, not the loaded battle
    packages. Preserve those names and redirect only selected DT_BtlUnitAsset
    rows. Never rewrite the table after the vision builder has added its rows.
    """
    import _ffr_overworld
    _ffr_overworld.prepare(tables, units, rows)
    prepare_voices(tables, units, rows)
    for u in units:
        if not u.get('ffbe'): continue
        validate(u)
        row = rows(TABLE).get(u['jp'], {})
        animations = row.get('animationAssetList', [])
        original = f'/Game/Chara/unit/{identity(u["id"])[3]}/{identity(u["id"])[3]}'
        if row.get('ID') != u['id'] or not animations or animations[0].get('Ss6Project') != original:
            raise ValueError('The original party runtime battle assets are unavailable. Prepare the game files again.')
        table = tables.setdefault(TABLE, {'asset': ASSET, 'add': [], 'set': []})
        table['set'].append({'row': u['jp'], 'set': asset_updates(u)})


def voice_label(id):
    return 'CHR' + identity(id)[3].removeprefix('unit')


def prepare_voices(tables, units, rows):
    """Use the native battle-only label; never alias audio banks/story assets.

    Generic DT_BtlVoiceData and DT_SkillData cues append this character label.
    Fixed cinematic cues and authored victory conversations are separate routes
    and deliberately retain their original recordings in this first pass.
    """
    for u in units:
        validate(u)
        source = u.get('battleVoice')
        if source is None or source == u['id']: continue
        parameters = rows(VOICE_TABLE)
        for id in (u['id'], source):
            row = parameters.get(identity(id)[1], {})
            if row.get('ID') != id or row.get('BattleVoiceLabel') != voice_label(id):
                raise ValueError('The original party battle voice labels changed. Prepare the game files again.')
        label = voice_label(source); bank = 'VO_BTL_' + label
        reference = rows(VOICE_BANK_TABLE).get(bank[:-1], {})
        if (reference.get('CueSheetName') != bank
                or reference.get('pCueSheet') != f'/Game/Sound/Cri/Voice/VO_BTL/{bank}/{bank}'):
            raise ValueError('The selected battle voice bank is unavailable in the prepared game tables.')
        table = tables.setdefault(VOICE_TABLE, {'asset': VOICE_ASSET, 'add': [], 'set': []})
        table['set'].append({'row': u['jp'], 'set': {'BattleVoiceLabel': label}})


def check_voice_rows(original, built, units):
    replacements = {u['id']: u['battleVoice'] for u in units if u.get('battleVoice') is not None}
    for id, jp, _, _ in CHARACTERS:
        desired = copy.deepcopy(original[jp])
        if id in replacements: desired['BattleVoiceLabel'] = voice_label(replacements[id])
        if built.get(jp) != desired:
            raise ValueError('Party battle voice did not match the selection, or an unrelated character property changed.')


def check_rows(original, built, units):
    for u in units:
        if not u.get('ffbe'): continue
        desired = copy.deepcopy(original[u['jp']])
        for path, value in asset_updates(u).items():
            desired['animationAssetList'][0][path.split('.')[-1]] = value
        if built.get(u['jp']) != desired:
            raise ValueError('Party runtime battle assets did not match the selected model, or an unrelated field changed.')


def party_motions(spec):
    """Nichol's original mixture sequence uses a held pose and a return phase."""
    attack = next((a for a in spec['animations'] if a['name'] == 'attack_B'), None)
    if not attack: return
    total = attack['frameCount']
    for name, hold in (('attack_B_pose', True), ('attack_B_reverse', False)):
        if any(a['name'] == name for a in spec['animations']): continue
        motion = copy.deepcopy(attack); motion['name'] = name
        if hold: motion['frameCount'] = 1
        for channels in motion['parts'].values():
            for channel, keys in channels.items():
                if not keys: continue
                if hold: channels[channel] = [[0, keys[-1][1]]]
                else:
                    ends = [k[0] for k in keys[1:]] + [total]
                    channels[channel] = sorted([[max(0, total-end), k[1]] for k, end in zip(keys, ends)])
        spec['animations'].append(motion)


def generate(u, env):
    """Generate private battle SS6/texture assets; never menu or field assets."""
    root = Path(env['ROOT']); legacy = Path(env['LEGACY']); out = Path(env['OUT'])
    templates = legacy / 'FFRS/Content/Chara/summon/summon13110'
    if any(not (templates / f'summon13110{suffix}{extension}').is_file() for suffix in ('', '_tex', '_normal', '_mreo') for extension in ('.uasset', '.uexp')):
        env['run'](env['ffrenv'].py(str(root / 'tools/extract_legacy.py'), '--filter', 'Chara/summon/summon13110/'))
    tool = env['FFRDT']; usmap = env['USMAP']; run = env['run']; ff = u['ffbe']
    import _ffr_animation_repair
    _ffr_animation_repair.repair_unit(u, root)
    c = identity(u['id']); name = c[3]; target = package(u)
    work = root / 'build/sprites' / u['key']; battle = work / 'battle'
    args = env['ffrenv'].py(str(root / 'tools/_ffr_build_sprites.py'), str(root / ff['dir']),
                           ff['id'], str(u['id']), str(work), '--battle-only')
    if ff.get('baseDir'): args += ['--base', str(root / ff['baseDir']), str(ff['baseForm'])]
    run(args)
    spec_path = battle / 'spec.json'; spec = json.loads(spec_path.read_bytes())
    # The sprite converter writes pixelSize as floats. make-texture parses
    # integer command-line arguments, so preserve whole dimensions as integers.
    dimensions = spec['pixelSize']
    if len(dimensions) != 2 or any(type(n) not in (int, float) or not 0 < n <= 32768 or n != int(n)
                                   for n in dimensions):
        raise ValueError('The party battle atlas must have two positive whole pixel dimensions.')
    w, h = (str(int(n)) for n in dimensions)
    party_motions(spec)
    spec.update(cellmapName=name, animePackName=name, imagePath=name + '_tex.png')
    spec_path.write_text(json.dumps(spec), encoding='utf-8')
    destination = out / 'FFRS/Content' / target.removeprefix('/Game/').rsplit('/', 1)[0]
    destination.mkdir(parents=True, exist_ok=True)
    donor = 13110; old = f'/Game/Chara/summon/summon{donor}/summon{donor}'
    templates = legacy / f'FFRS/Content/Chara/summon/summon{donor}'
    run(tool + ['make-ss6', str(templates / f'summon{donor}.uasset'), str(spec_path),
                str(destination / (name + '.uasset')), old, target,
                f'summon{donor}={name}', '--usmap', usmap])
    for suffix, payload in (('_tex', 'tex.bgra'), ('_normal', 'normal.bc5'), ('_mreo', 'mreo.bgra')):
        run(tool + ['make-texture', str(templates / f'summon{donor}{suffix}.uasset'),
                    str(battle / payload), w, h, str(destination / (name + suffix + '.uasset')),
                    old + suffix, target + suffix, f'summon{donor}={name}', '--usmap', usmap])
    if str(ff['id']) == FINA:
        import _ffr_crystalfina as fina
        sources = fina.materials(root); source = sources[0][0]
        original_json = work / 'material-original.json'; edited_json = work / 'material-edited.json'
        run(tool + ['tojson', str(source), str(original_json), '--usmap', usmap])
        original = json.loads(original_json.read_text(encoding='utf-8-sig'))
        export = original['Exports'][0]
        class_index = export['ClassIndex']
        if class_index >= 0 or original['Imports'][-class_index-1]['ObjectName'] != 'Material':
            raise ValueError('The Crystal Fina material class changed; the party reference cannot be resolved safely.')
        changes = {fina.MATERIAL: material(u),
                   f'/Game/Chara/summon/summon{fina.VISION_ID}/summon{fina.VISION_ID}_tex': target + '_tex'}
        def replace(v):
            if isinstance(v, str):
                return changes.get(v, {f'M_CrystalFina_AlphaTest_{fina.VISION_ID}': material(u).rsplit('/', 1)[1],
                                       f'summon{fina.VISION_ID}_tex': name + '_tex'}.get(v, v))
            if isinstance(v, list): return [replace(x) for x in v]
            if isinstance(v, dict): return {k: replace(x) for k, x in v.items()}
            return v
        edited = replace(original)
        leaf = material(u).rsplit('/', 1)[1]
        if leaf not in edited['NameMap']: edited['NameMap'].append(leaf)
        edited_json.write_text(json.dumps(edited), encoding='utf-8')
        dest = out / ('FFRS/Content/' + material(u).removeprefix('/Game/') + '.uasset')
        dest.parent.mkdir(parents=True, exist_ok=True)
        run(tool + ['fromjson', str(edited_json), str(dest), '--usmap', usmap])
        if dest.with_suffix('.uexp').read_bytes() != source.with_suffix('.uexp').read_bytes():
            raise ValueError('The party material serializer changed the original shader payload.')


def build(units, env):
    import _ffr_overworld
    for u in units:
        if u.get('overworld'):
            env['stage']('Replacing party overworld model: ' + u['en'])
            _ffr_overworld.generate(u, env)
    selected = [u for u in units if u.get('ffbe')]
    if not selected: return
    for u in selected:
        env['stage']('Replacing party battle model: ' + u['en'])
        generate(u, env)


def verify(root, tool, usmap):
    import subprocess
    root = Path(root); units = json.loads((root / 'mods/EstherTsukiko/units.json').read_bytes())
    party = [validate(u) for u in units if u.get('party')]
    import _ffr_overworld
    _ffr_overworld.verify(root, tool, usmap, units)
    voiced = [u for u in party if u.get('battleVoice') is not None and u['battleVoice'] != u['id']]
    if voiced:
        work = root / 'build/party-voices'; work.mkdir(parents=True, exist_ok=True)
        original = work / 'verify-original.json'; built = work / 'verify-built.json'
        for source, target in ((root / 'extracted/legacy', original), (root / 'build/visions_mod/assets', built)):
            subprocess.run(tool + ['rows', str(source / (VOICE_ASSET + '.uasset')), str(target), '--usmap', usmap],
                           check=True, capture_output=True)
        check_voice_rows(json.loads(original.read_text(encoding='utf-8-sig'))['rows'],
                         json.loads(built.read_text(encoding='utf-8-sig'))['rows'], party)
        import _ffr_party_voices
        _ffr_party_voices.verify(root, tool, usmap, voiced)
        print('OK: native party battle voice labels and unchanged original character properties verified')
    selected = [u for u in party if u.get('ffbe')]
    if not selected: return
    work = root / 'build/party-models'; work.mkdir(parents=True, exist_ok=True)
    def run(args): subprocess.run(args, check=True, capture_output=True)
    original = work / 'verify-original.json'; built = work / 'verify-built.json'
    run(tool + ['rows', str(root / 'extracted/legacy' / (ASSET + '.uasset')), str(original), '--usmap', usmap])
    run(tool + ['rows', str(root / 'build/visions_mod/assets' / (ASSET + '.uasset')), str(built), '--usmap', usmap])
    check_rows(json.loads(original.read_text(encoding='utf-8-sig'))['rows'],
               json.loads(built.read_text(encoding='utf-8-sig'))['rows'], selected)
    for u in selected:
        path = root / 'build/visions_mod/assets/FFRS/Content' / package(u).removeprefix('/Game/')
        for suffix in ('', '_tex', '_normal', '_mreo'):
            for extension in ('.uasset', '.uexp'):
                if not path.with_name(path.name + suffix).with_suffix(extension).is_file():
                    raise ValueError('A generated party battle asset is missing: ' + str(path))
    print('OK: private party battle models and unchanged original table rows verified')


def register(app, env):
    from fastapi import HTTPException
    def make(id):
        try: return snapshot(id, env['ffr_catalog'].rows)
        except (ValueError, OSError, KeyError) as e: raise HTTPException(422, str(e)) from e
    @app.get('/api/party/catalog')
    def catalog(): return [make(c[0]) for c in CHARACTERS]
    @app.get('/api/party/character/{id}')
    def character(id: int): return make(id)
