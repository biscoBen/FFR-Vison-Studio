"""Native vision snapshots and narrow overrides against freshly extracted game rows."""
import copy
import json
from pathlib import Path
import re
import shutil

UNIT = 'Unit/DT_UnitParameter'
VISION = 'Item/Vision/DT_VisionItemData'
BATTLE = 'Asset/Battle/Unit/DT_BtlUnitAsset'
AWAKENING = 'Item/Vision/DT_VisionAwakeningMasteryData'
SYNCHRO = 'Item/Vision/DT_VisionSynchroMasteryData'
FIELDS = ('MaxHitPoint', 'MaxMagicPoint', 'Attack', 'Defence', 'Intelligence', 'Mind', 'Agility')


def one(rows, rel, field, value):
    found = [(k, v) for k, v in rows(rel).items() if v.get(field) == value]
    if len(found) != 1: raise ValueError(f'Expected one original {rel} row for {value}. Re-run game preparation.')
    return found[0]


def grants(row):
    out = []
    for d in row.get('detailData', []):
        kind = d.get('parameterType', '').split('::')[-1]; params = d.get('params') or []
        if kind == 'None' or not params or params[0] in (-1, None): continue
        # Passive and master rewards can also use the second parameter.
        out.append([kind, params[0]] + ([params[1]] if len(params) > 1 else []))
    return out


def text(value, catalog_name, fallback='', locale=None):
    if isinstance(value, str): return value
    if isinstance(value, dict) and value.get('key') and locale:
        ns = value.get('table', '').split('/')[-1].split('.')[-1]
        found = (locale.get(ns) or {}).get(value['key'])
        if found: return found
        for group in locale.values():
            if isinstance(group, dict) and group.get(value['key']): return group[value['key']]
    return catalog_name or fallback


def snapshot(vid, rows, catalog, locale=None):
    if type(vid) is not int or vid < 13100: raise ValueError('Select an original game vision.')
    uk, u = one(rows, UNIT, 'ID', vid); _, v = one(rows, VISION, 'ID', vid)
    _, asset = one(rows, BATTLE, 'ID', vid)
    animations = asset.get('animationAssetList') or []
    expected = f'/Game/Chara/summon/summon{vid}/summon{vid}'
    if not animations or animations[0].get('Ss6Project', '').split('.')[0] != expected:
        raise ValueError('This original vision uses a sprite layout not supported by this engine.')
    cv = next((x for x in catalog.get('visions', []) if x['id'] == vid), {})
    _, command = one(rows, 'Skill/DT_CommandSkillData', 'ID', v['CommandId'])
    _, master = one(rows, 'Skill/DT_MasterSkillData', 'VisionId', vid)
    tiers = {}
    for rel, name in ((AWAKENING, 'awakening'), (SYNCHRO, 'synchro')):
        values = sorted([r for r in rows(rel).values() if r['ID'] == vid], key=lambda r: r['Level'])
        if not values or [r['Level'] for r in values] != list(range(len(values))): raise ValueError('Original mastery ranks are not contiguous.')
        tiers[name] = values
    name = text(v.get('Name'), cv.get('name'), uk, locale)
    result = {'key': f'native_{vid}', 'id': vid, 'donor': vid, 'jp': uk, 'en': name,
              'sort': v.get('SortId', vid), 'price': v.get('buyingPrice', 0),
              'desc': text(v.get('Description'), cv.get('desc'), locale=locale),
              'attackType': v['attackType'].split('::')[-1], 'roles': copy.deepcopy(v['roles']),
              'stats': {f: u[f] for f in FIELDS}, 'elemRes': copy.deepcopy(u['ElementResistanceList']),
              'command': {'id': command['ID'], 'en': text(command.get('Name'), None, name + "'s Skills", locale), 'desc': text(command.get('Description'), None, locale=locale)},
              'master': {'id': master['ID'], 'en': text(master.get('Name'), None, 'Spirit of ' + name, locale), 'desc': text(master.get('Description'), None, locale=locale)},
              'lb': v['finishBlowSkill'], 'skills': {}, 'awakening': [grants(r) for r in tiers['awakening']],
              'synchro': [grants(r) for r in tiers['synchro']]}
    result['native'] = {'version': 1, 'id': vid, 'baseline': copy.deepcopy(result),
                        'synchroCaps': [len(r['detailData']) for r in tiers['synchro']]}
    return result


def validate(unit, rows):
    native = unit.get('native')
    if not isinstance(native, dict) or native.get('version') != 1 or native.get('id') != unit.get('id') or unit.get('donor') != unit['id']:
        raise ValueError('Original vision identity cannot be changed.')
    base = native.get('baseline', {})
    if base.get('id') != unit['id'] or unit.get('lb_custom'):
        raise ValueError('Original visions support existing Resonances; a new custom Resonance must be added as a separate vision.')
    one(rows, UNIT, 'ID', unit['id']); _, item = one(rows, VISION, 'ID', unit['id'])
    _, master = one(rows, 'Skill/DT_MasterSkillData', 'VisionId', unit['id'])
    if base['command']['id'] != item['CommandId'] or base['master']['id'] != master['ID']:
        raise ValueError('The original game identities changed; reset and review this vision before building.')
    _, asset = one(rows, BATTLE, 'ID', unit['id'])
    expected = f'/Game/Chara/summon/summon{unit["id"]}/summon{unit["id"]}'
    if not asset.get('animationAssetList') or asset['animationAssetList'][0].get('Ss6Project', '').split('.')[0] != expected:
        raise ValueError('This original vision has an unsupported sprite layout.')
    if unit['command']['id'] != base['command']['id'] or unit['master']['id'] != base['master']['id']:
        raise ValueError('Original command and master identities cannot be changed.')
    skill_rows = rows('Skill/DT_SkillData'); ids = {r['ID'] for r in skill_rows.values()}; names = set(skill_rows)
    visual_ids = set()
    if unit.get('skills'):
        for rel in ('Asset/Skill/DT_SkillAsset', 'Asset/Skill/CDT_SkillAsset_Demo', 'Battle/Sequencer/DT_BtlHitEffectData'):
            visual_ids.update(r['ID'] for r in rows(rel).values())
    start = 445000 + (unit['id'] - 13100) * 100
    for key, recipe in (unit.get('skills') or {}).items():
        sid = int(key)
        if (not start <= sid < start + 100 or sid in ids or recipe.get('jp') in names
                or any(sid + off in visual_ids for off in (0, 1, 2))):
            raise ValueError('A custom skill conflicts with original game data; choose a free skill slot.')
    return base


def split(units, rows):
    native, added = [], []
    seen = set()
    for u in units:
        if u['id'] in seen: raise ValueError('Duplicate vision ID in this roster.')
        seen.add(u['id'])
        if u.get('native') is not None:
            validate(u, rows); native.append(u)
        else: added.append(u)
    return native, added


def prepare(tables, objects, units, root, rows):
    def put(rel, row, updates):
        if updates: tables.setdefault(rel, {'asset': 'FFRS/Content/Datatable/' + rel, 'add': [], 'set': []})['set'].append({'row': row, 'set': updates})
    for u in units:
        base = validate(u, rows); vid = u['id']
        uk, original = one(rows, UNIT, 'ID', vid); vk, _ = one(rows, VISION, 'ID', vid)
        stats = {f: u['stats'][f] for f in FIELDS if u['stats'][f] != base['stats'][f]}
        if u['elemRes'] != base['elemRes']: stats['ElementResistanceList'] = u['elemRes']
        vu = {}
        for field, target in (('en', 'Name'), ('desc', 'Description')):
            if u[field] != base[field]:
                vu[target] = u[field]; stats[target] = u[field]
                if field == 'en': vu.update({k: u[field] for k in ('nameSg', 'namePl', 'nameDetSg', 'nameDetPl')})
        if u['attackType'] != base['attackType']: vu['attackType'] = 'eSkillDamageType::' + u['attackType']
        if u['roles'] != base['roles']: vu['roles'] = u['roles']
        if u['lb'] != base['lb']: vu['finishBlowSkill'] = u['lb']
        for field, rel in (('command', 'Skill/DT_CommandSkillData'), ('master', 'Skill/DT_MasterSkillData')):
            key, _ = one(rows, rel, 'ID', base[field]['id'])
            updates = {target: u[field][source] for source, target in (('en', 'Name'), ('desc', 'Description')) if u[field][source] != base[field][source]}
            put(rel, key, updates)
        for rel, field in ((AWAKENING, 'awakening'), (SYNCHRO, 'synchro')):
            values = sorted([(k, r) for k, r in rows(rel).items() if r['ID'] == vid], key=lambda pair: pair[1]['Level'])
            if len(u[field]) != len(base[field]) or len(values) != len(u[field]): raise ValueError('Original mastery rank count changed; review this vision before building.')
            for i, desired in enumerate(u[field]):
                if desired == base[field][i]: continue
                k, old = values[i]; cap = len(old['detailData'])
                if len(desired) > cap: raise ValueError(f'MR/awakening rank {i+1} has more rewards than the game supports.')
                detail = [{'parameterType': 'eVisionMasteryParameterType::' + g[0], 'params': [g[1], g[2] if len(g) > 2 else -1]} for g in desired]
                detail += [{'parameterType': 'eVisionMasteryParameterType::None', 'params': [-1, -1]} for _ in range(cap - len(detail))]
                put(rel, k, {'detailData': detail}) # Preserve Level and masteryPoint.
        if u.get('ffbe'):
            ak, _ = one(rows, BATTLE, 'ID', vid); path = f'/Game/Chara/summon/summon{vid}/summon{vid}'
            asset = {'animationAssetList[0].Ss6Project': path, 'animationAssetList[0].textureBaseColor': path + '_tex',
                     'animationAssetList[0].textureNormal': path + '_normal', 'animationAssetList[0].textureMetallicRoughness': path + '_mreo'}
            ff = u['ffbe']
            if str(ff.get('id')) == '99887755552703':
                import _ffr_crystalfina as fina
                temp = {'outRoot': str(Path(root) / 'build/visions_mod/assets'), 'tables': [{'asset': fina.TABLE, 'add': [{'row': u['jp'], 'set': {'ID': vid, **asset}}]}]}
                fina.prepare(temp, [u], root)
                extra = temp['tables'][0]['add'][0]['set']; extra.pop('ID'); asset.update(extra)
            put(BATTLE, ak, asset)
            if original.get('FaceIconId') != vid: stats['FaceIconId'] = vid
            layout = next((o for o in objects if o.get('asset') == 'FFRS/Content/UI/Unit/UIUnitSs/Data/DA_UIUnitSsLayout'), None)
            if layout is None:
                layout = {'asset': 'FFRS/Content/UI/Unit/UIUnitSs/Data/DA_UIUnitSsLayout'}; objects.append(layout)
            layout.setdefault('mapAdd', {}).setdefault('LayoutOverrideDataMap', {})[str(vid)] = {
                'bOverrideOffset': False, 'bOverrideScale': True, 'Scale': u.get('menuScale', 2.52),
                'bOverrideFlippedHorizontally': False, 'bFlippedHorizontally': False}
        put(UNIT, uk, stats); put(VISION, vk, vu)


def copy_materials(units, root, out):
    for u in units:
        if str((u.get('ffbe') or {}).get('id')) == '99887755552703':
            import _ffr_crystalfina as fina
            fina.copy_material(root, out, [u])


def expected_edits(root):
    """Recompute intentional native field edits for the normal post-build verifier."""
    root = Path(root); spec = root / 'mods/EstherTsukiko/units.json'
    units = json.loads(spec.read_bytes()) if spec.is_file() else []
    units = [u for u in units if u.get('native') is not None]
    if not units: return {}
    def rows(rel): return json.loads((root / 'extracted/rows' / (rel + '.json')).read_bytes())['rows']
    split(units, rows); tables = {}; prepare(tables, [], units, root, rows)
    return {(rel, entry['row']): entry['set'] for rel, table in tables.items() for entry in table['set']}


def expected_row_change(rel, key, original, built, expected, equivalent):
    """Accept precisely the intended fields; unrelated fields and missing rows still fail."""
    updates = expected.get((rel, key))
    if not updates: return False
    desired = copy.deepcopy(original)
    for path, value in updates.items():
        parts = [int(p) if p.isdigit() else p for p in re.findall(r'[^.\[\]]+', path)]
        node = desired
        for part in parts[:-1]: node = node[part]
        node[parts[-1]] = value
    return equivalent(desired, built)


def register(app, env):
    from fastapi import HTTPException
    from fastapi.responses import FileResponse
    def locale():
        path = Path(env['ROOT']) / 'extracted/locres_en.json'
        return json.loads(path.read_bytes()) if path.is_file() else {}
    def make(vid):
        try: return snapshot(vid, env['ffr_catalog'].rows, env['ffr_catalog'].load(), locale())
        except (ValueError, KeyError, OSError) as e: raise HTTPException(422, str(e)) from e
    @app.get('/api/native/catalog')
    def catalog():
        result = []
        try:
            source = env['ffr_catalog'].load(); strings = locale()
            for v in source['visions']:
                if v['id'] < 13100: continue
                try: result.append(snapshot(v['id'], env['ffr_catalog'].rows, source, strings))
                except (ValueError, KeyError, TypeError): continue # Incomplete/unsupported placeholders are excluded.
        except OSError as e:
            raise HTTPException(422, 'Prepare your game files before loading original visions. ' + str(e)) from e
        return sorted(result, key=lambda u: u['en'].lower())
    @app.get('/api/native/vision/{vid}')
    def vision(vid: int): return make(vid)
    @app.get('/api/native/model/{uid}/{form}')
    def model(uid: str, form: str):
        if not uid.isdigit() or not form.isdigit(): raise HTTPException(422, 'Invalid model selection.')
        detail = env['ffbe_catalog'].unit_detail(uid)
        if not detail or form not in detail.get('forms', {}): raise HTTPException(422, 'This look does not belong to the selected model.')
        root = Path(env['ROOT']); key = 'native_model_' + form
        def copy_form(fid):
            source = env['ffbe_catalog'].sprite_dir(fid)
            if not source: raise HTTPException(422, 'Prepare this model\'s sprite pack first.')
            target = root / 'units/ffbe' / key / 'sprites' / fid
            target.mkdir(parents=True, exist_ok=True)
            for source_file in env['ffbe_catalog'].sprite_files(fid):
                dest = target / Path(source_file).name
                if not dest.exists(): shutil.copy2(source_file, dest) # Keep locally edited cached artwork.
            for required in (f'unit_anime_{fid}.png', f'unit_cgg_{fid}.csv'):
                if not (target / required).is_file(): raise HTTPException(422, 'The selected sprite pack is incomplete.')
            return target.relative_to(root).as_posix()
        ffbe = {'id': form, 'base': uid, 'source': detail.get('region', 'JP'), 'dir': copy_form(form)}
        shifted = env['ffbe_catalog'].shift_info(form)
        if shifted:
            ffbe.update({'baseForm': shifted['base'], 'baseDir': copy_form(shifted['base']), 'shift': shifted['kind']})
        return {'ffbe': ffbe}
    @app.get('/api/native/icon/{vid}')
    def icon(vid: int):
        make(vid)
        catalog = env['ffr_catalog']; name = f'ICON_UnitFace_summon{vid}'
        png = Path(catalog.ICONS) / (name + '.png')
        if not png.is_file():
            pkg = Path(env['LEGACY']) / 'FFRS/Content/UI/Textures/Icon/Vision_Face' / (name + '.uasset')
            catalog.export_icon(str(pkg), name)
        if not png.is_file(): raise HTTPException(404, 'Original portrait is not exported.')
        return FileResponse(png, media_type='image/png')
