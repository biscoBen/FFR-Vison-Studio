"""Keep optional Sephira presets editable while excluding disabled entries from builds."""

import copy
import json
import os
from pathlib import Path
import subprocess
import tempfile

FIELD = 'sephiraVision'
RETIRED = {'great_dragon'}
PASSIVE = 'Skill/DT_PassiveSkillData'
EFFECT = 'Skill/DT_SkillEffectData'
CONFIG = 'mods/EstherTsukiko/sephira-settings.json'


def validate_settings(value):
    required = {'schema', 'useBorrowedSkillVisuals'}
    if (not isinstance(value, dict) or not required <= set(value)
            or set(value) - required - {'shopAcquisitionOverride','shopAcquisitionPresets'}
            or type(value['schema']) is not int or value['schema'] != 1
            or type(value['useBorrowedSkillVisuals']) is not bool
            or ('shopAcquisitionOverride' in value and type(value['shopAcquisitionOverride']) is not bool)):
        raise ValueError('Invalid Sephira skill visual settings.')
    selected=value.get('shopAcquisitionPresets')
    if selected is not None:
        known=json.loads(Path(__file__).with_name('sephira_visuals.json').read_bytes())['presets']
        if (not isinstance(selected,list) or any(not isinstance(p,str) or p not in known for p in selected)
                or len(set(selected)) != len(selected)):
            raise ValueError('Invalid Sephira shop vision selection.')
    return dict(value)


def settings(root):
    path = Path(root) / CONFIG
    return validate_settings(json.loads(path.read_bytes())) if path.is_file() else {
        'schema': 1, 'useBorrowedSkillVisuals': True}


def shop_override(unit, controls):
    member=membership(unit)
    selected=controls.get('shopAcquisitionPresets')
    return bool(controls.get('shopAcquisitionOverride') and member is not None and member['enabled']
                and member['preset'] not in RETIRED and (selected is None or member['preset'] in selected))


def visual_units(units, root, rows=None):
    """Choose original visual sources only in the ephemeral build specification.

    Match known preset source/donor pairs, independent of allocated private IDs
    and recipe revisions. Preserve explicitly edited donors and authored sequences.
    Saved recipes keep the borrowed donors so turning the setting on restores them.
    """
    result = [repair_appearance(unit) for unit in copy.deepcopy(units)]
    for unit in result: repair_default_acquisition(unit)
    controls = settings(root)
    if controls.get('shopAcquisitionOverride', False):
        for unit in result:
            value = membership(unit)
            if shop_override(unit, controls):
                unit['studioAcquisition'] = {'version': 1, 'location': 'mitra_shop',
                                            'random': False, 'hideSpoilers': True}
                unit['price'] = 1
    if controls['useBorrowedSkillVisuals']:
        return result
    policy = json.loads(Path(__file__).with_name('sephira_visuals.json').read_bytes())
    if policy.get('schema') != 1:
        raise ValueError('Unsupported Sephira visual policy.')
    sources = {v['ID']: v for v in rows('Skill/DT_SkillData').values()} if rows else {}
    for unit in result:
        value = runtime_membership(unit)
        if value is None:
            continue
        donors = policy['presets'].get(value['preset'], {})
        for recipe in (unit.get('skills') or {}).values():
            if (not recipe or recipe.get('clone_sequence')
                    or recipe.get('tint') is not None or recipe.get('motion')
                    or str(recipe.get('from')) not in donors
                    or recipe.get('visuals') != donors.get(str(recipe.get('from')))):
                continue
            recipe['visuals'] = recipe['from']
            # Some native sources play a shared sequence without owning an asset
            # row. Remove only our default pointer overrides, retaining any
            # explicit user-selected pointer and every combat setting.
            source = sources.get(recipe['from'], {})
            for field in ('playSequencerId', 'sequencerIdWhenTargetFriendlies'):
                if field in source and (recipe.get('set') or {}).get(field) == -1:
                    recipe['set'][field] = source[field]
            # A missing demo source must stay missing even with library repairs
            # enabled. A newly available native source timeline still wins.
            recipe['_sephiraSourceVisuals'] = True
    return result


def register(app, env):
    from fastapi import HTTPException

    @app.get('/api/sephira/settings')
    def get_settings():
        try: return settings(env['ROOT'])
        except (OSError, ValueError) as e: raise HTTPException(422, str(e)) from e

    @app.put('/api/sephira/settings')
    def put_settings(value: dict):
        try:
            value = validate_settings(value)
            current = settings(env['ROOT'])
            for key in ('shopAcquisitionOverride','shopAcquisitionPresets'):
                if key not in value and key in current: value[key]=current[key]
            if env.get('state', {}).get('running'):
                raise ValueError('Wait for the current build to finish.')
            path = Path(env['ROOT']) / CONFIG
            path.parent.mkdir(parents=True, exist_ok=True)
            fd, temporary = tempfile.mkstemp(prefix='sephira-settings-', dir=path.parent)
            try:
                with os.fdopen(fd, 'w', encoding='utf-8') as f:
                    json.dump(value, f); f.flush(); os.fsync(f.fileno())
                os.replace(temporary, path)
            finally:
                Path(temporary).unlink(missing_ok=True)
            return value
        except (OSError, ValueError) as e: raise HTTPException(422, str(e)) from e

# Effect ID, semantic type, parameter index, original value, replacement kind.
# These are identified command/LB fields, not a search/replace of all numbers.
BINDINGS = {
    1406: (15125, 'AddBaseBreakDmg', 1, 200, 'command'),
    1410: (19024, 'DominantPower', 0, 102, 'command'),
    1411: (12902, 'DamageMultiplier', 2, 102, 'command'),
    1418: (12206, 'CriticalRateVariation', 5, 440110, 'lb'),
    1420: (13103, 'CriticalRateVariation', 6, 110, 'command'),
    1432: (61000, 'CostVariation', 4, 123, 'command'),
    1433: (12926, 'DmgMulRetaliation', 3, 440240, 'lb'),
    1443: (54220, 'RepeatAction', 7, 202, 'command'),
    1448: (12942, 'AquaTerraSword', 1, 205, 'command'),
    1454: (15127, 'BreakDmgByProtect', 1, 207, 'command'),
}

# Swap command/LB-bound MR rewards with existing, transferable awakening
# bonuses. Each tuple is (MR rank, bound passive, general passive, awakening
# rank). Nothing is added or removed from a complete kit or its AP budget.
MASTERY_SCOPE = {
    'christine': [(7, 1406, 1280, 3)],
    'barusa': [(9, 1454, 1333, 3)],
    'minfilia': [(5, 1410, 1313, 2), (7, 1411, 1336, 3)],
    'trance_terra': [(5, 1432, 1315, 3), (9, 1433, 1307, 3)],
    'nalu': [(7, 1420, 1279, 3), (9, 1418, 1234, 3)],
}
ACQUISITION_SWAPS = {'rikku': ('sephira_13124','sephira_13118'),
                     'lunafreya': ('sephira_13118','sephira_13124')}


def repair_default_acquisition(unit):
    member = runtime_membership(unit)
    if member is None or member['preset'] not in ACQUISITION_SWAPS: return
    old, new = ACQUISITION_SWAPS[member['preset']]
    # The saved canonical location makes this a one-time default migration.
    # A later explicit choice of the old crystal remains the user's choice.
    if (unit.get('sephiraAcquisition') or {}).get('location') != old: return
    for field in ('studioAcquisition','sephiraAcquisition'):
        value = unit.get(field) or {}
        if value.get('version') == 3 and value.get('location') == old:
            unit[field] = dict(value, location=new)
MASTERY_LABELS = {
    'christine': {1406: ('True Stagger', 'Increases the stagger power of Christine’s skills.')},
    'barusa': {1454: ('Bastion', 'Increases the stagger power of Barusa’s skills. The effect increases with the number of allies under Protect.')},
    'minfilia': {
        1410: ('Job Change', 'Minfilia’s skills use the higher of physical or magic attack.'),
        1411: ('Late Bloomer', 'Increases damage dealt by Minfilia’s skills by 30% while the LB gauge is at least 50%.')},
    'trance_terra': {
        1432: ('The Federation’s Fiend', 'Halves the MP cost of Trance Terra’s skills while the LB gauge is at least 50%.'),
        1433: ('Play Rough', 'Increases damage dealt by Trance Judgment, Judgment Shadow, and Trance Terra’s resonance by 40% against enemies that have attacked self.')},
    'nalu': {
        1420: ('Broadsword Mastery', 'Increases the critical hit rate of Nalu’s skills by 30% while at full HP.'),
        1418: ('Signature Moves', 'Increases the critical hit rate of Thunder Spear, Lightning Sweep, and Nalu’s resonance by 15%.')},
}
# Two original traits name two active skills as well as an LB. Rebind those
# typed skill-ID slots to the private signatures, just like their LB slot.
SIGNATURE_BINDINGS = {
    ('trance_terra', 1433): [(1, 447300, 505450), (2, 447310, 503120)],
    ('nalu', 1418): [(3, 446000, 501000), (4, 446010, 500390)],
}


def repair_mastery_scope(unit):
    member = runtime_membership(unit)
    if member is None: return
    for rank, bound, general, preferred in MASTERY_SCOPE.get(member['preset'], []):
        if rank >= len(unit.get('synchro', [])): continue
        reward = next((g for g in unit['synchro'][rank] if g[:2] == ['PassiveSkill', bound]), None)
        if reward is None: continue  # Already repaired or a deliberate MR edit.
        replacement = next((g for tier in unit['awakening'] for g in tier
                            if g[:2] == ['PassiveSkill', general]), None)
        if replacement is not None: replacement[1] = bound
        else:
            # Revision-6 saves have not received the general awakening reward.
            target = next((tier for tier in unit['awakening'][preferred:] if len(tier) < 8), None)
            if target is None: raise ValueError(unit['en'] + ': free an awakening slot for its unit-specific bonus.')
            target.append(['PassiveSkill', bound, -1])
        reward[1] = general


# Saved-game compatibility: freeze the preset/conditional seeds and existing
# label positions. Append later explicit labels only within their reserved range.
# Skill IDs 1000..1999 are passive IDs; command/active/master
# lookups classify IDs before searching their respective native tables.
_PASSIVE_PRESETS = ('a2', 'christine', 'crystal_fina', 'barusa', 'fran', 'lunafreya', 'minfilia', 'folka', 'fryevia', 'lenneth', 'lila', 'mystea', 'reberta', 'snow_white', 'aria', 'eiko', 'alice', 'mog', 'lilith', 'freya', 'trance_terra', 'ariana', 'elephim', 'jade', 'primm', 'relm', 'rikku', 'nalu', 'elza', 'lunera')
_PASSIVE_CONDITIONALS = (1406, 1410, 1411, 1418, 1420, 1432, 1433, 1443, 1448, 1454)
_PASSIVE_LABELS = (('crystal_fina', 1551), ('crystal_fina', 1552), ('lunafreya', 1510), ('lunafreya', 1517), ('folka', 1535), ('fryevia', 1522), ('mystea', 1530), ('mystea', 1274), ('mystea', 1513), ('reberta', 1507), ('aria', 1527), ('aria', 1519), ('eiko', 1498), ('eiko', 1373), ('alice', 1481), ('alice', 1531), ('mog', 1511), ('freya', 1529), ('freya', 1516), ('freya', 1497), ('freya', 1539), ('trance_terra', 1532), ('ariana', 1515), ('ariana', 1499), ('ariana', 1518), ('primm', 1521), ('primm', 1525), ('relm', 1500), ('rikku', 1009), ('nalu', 1523), ('nalu', 1537), ('nalu', 1496), ('elza', 1528), ('elza', 1495), ('elza', 1506), ('elza', 1276), ('lunera', 1051), ('folka', 1524), ('barusa', 1526), ('lilith', 1513), ('eiko', 1009), ('fryevia', 1539), ('primm', 1531), ('lunera', 1510))
_PASSIVE_KEYS = [(preset, sid) for preset in _PASSIVE_PRESETS for sid in _PASSIVE_CONDITIONALS] + list(_PASSIVE_LABELS)
_PRIVATE_PASSIVES = {key: 1600 + index for index, key in enumerate(_PASSIVE_KEYS)}
# Appended independently: never shift the established private passive IDs.
_PRIVATE_PASSIVES[('mog',1498)] = 1944
_FALLBACK_FIRST = 1970


def private_passive_id(preset, source):
    # Aria's requested Water replacement keeps the already-learned Spirit/MR
    # passive identity of her former Light imbue. Other visions keep their IDs.
    if preset == 'aria' and source == 1524: source = 1527
    key = (preset, source)
    if key in _PRIVATE_PASSIVES: return _PRIVATE_PASSIVES[key]
    # Preserve support for explicitly edited/imported membership names without
    # reassigning any bundled preset when another preset is disabled.
    import hashlib
    first = _FALLBACK_FIRST
    return first + int.from_bytes(hashlib.sha256(f'{preset}:{source}'.encode()).digest()[:4], 'big') % (2000 - first)


def repair_kit_rewards(unit):
    """The old Aria draft must also build Water with the unchanged MR/Spirit ID."""
    value=runtime_membership(unit)
    if value is None or value['preset']!='aria' or unit.get('sephiraKitRevision',0)>=1:return
    for tier in unit.get('synchro',[]):
        for grant in tier:
            if grant[:2]==['PassiveSkill',1527]:
                grant[1]=1524
                labels=unit.setdefault('sephiraPassiveText',{})
                labels.pop('1527',None)
                labels['1524']={'name':'Imbue Water','desc':'Add water to non-elemental standard attacks and battle skills.'}


_mr_restoration_cache = None


def mr_restoration():
    global _mr_restoration_cache
    if _mr_restoration_cache is None:
        value=json.loads(Path(__file__).with_name('sephira_mr_restoration.json').read_bytes())
        if value.get('schema')!=1:raise ValueError('Unsupported Sephira MR restoration data.')
        _mr_restoration_cache=value['presets']
    return _mr_restoration_cache


def repair_equipable_mr(unit):
    value=runtime_membership(unit)
    update=mr_restoration().get(value['preset']) if value else None
    if (not update or unit.get('sephiraMrRevision',0)>=update['version']
            or unit.get('sephiraRecipe',0)<7):return
    # Validate every edited MR slot before making any in-memory changes.
    def same(a,b):return a[:2]==b[:2] and (a[2] if len(a)>2 else -1)==(b[2] if len(b)>2 else -1)
    for op in update['mr']:
        grants=[g for g in unit['synchro'][op['rank']] if g[0] in ('ActiveSkill','PassiveSkill')]
        if len(grants)!=1 or not (same(grants[0],op['from']) or same(grants[0],op['to'])):
            raise ValueError(f'{unit["en"]} MR{op["rank"]} was edited. Resolve it in Apply kit and MR updates before building.')
    for op in update['mr']:
        tier=unit['synchro'][op['rank']]
        tier[:]=[list(op['to']) if same(g,op['from']) else g for g in tier]
    for _,kind,identity in update['remove']:
        for tier in unit['awakening']:tier[:]=[g for g in tier if g[:2]!=[kind,identity]]
    for preferred,kind,identity in update['add']:
        if any(g[:2]==[kind,identity] for f in ('awakening','synchro') for t in unit[f] for g in t):continue
        rank=next((r for r in range(preferred,4) if len(unit['awakening'][r])<8),None)
        if rank is None:raise ValueError(f'{unit["en"]} needs an awakening slot for its MR update. Resolve it in Studio before building.')
        unit['awakening'][rank].append([kind,identity,-1])
    unit['sephiraMrRevision']=update['version']


def player_units(units, rows):
    """Normalize private learned commands and pure healing outside battle.

    Saved recipes, IDs, numeric power/cost and the native donors stay unchanged.
    Explicit edits to these presentation/availability fields retain precedence.
    """
    result = copy.deepcopy(units)
    selected = [u for u in result if runtime_membership(u) is not None and u.get('skills')]
    if not selected: return result
    native = {r['ID']: r for r in rows('Skill/DT_SkillData').values()}
    for unit in selected:
        import _ffr_esper_mastery
        _ffr_esper_mastery.repair(unit)
        repair_mastery_scope(unit)
        repair_kit_rewards(unit)
        repair_equipable_mr(unit)
        learned = {g[1] for tier in unit.get('synchro', []) for g in tier if g[0] == 'ActiveSkill'}
        command = unit['command']['id']
        for identity, recipe in unit['skills'].items():
            source = native.get(recipe.get('from'))
            if not source or recipe.get('resonance'): continue
            import _ffr_sephira_ffbe
            if _ffr_sephira_ffbe.selected(unit, recipe): recipe['visuals'] = recipe['from']
            fields = recipe.setdefault('set', {})
            # Enemy attack donors commonly keep the generic weapon icon even
            # after the private player copy gains an element. Damage and its
            # menu icon are independent native fields. Explicit icon edits win.
            effective = dict(source, **fields)
            if ('SkillIcon.TagName' not in fields and 'SkillIcon' not in fields
                    and effective.get('skillEffectType') == 'DamageAndRecovery'
                    and effective.get('parameterVariationType') == 'Decrease'
                    and effective.get('parameterType') == 'HitPoint'
                    and effective.get('element') in ('Fire', 'Ice', 'Thunder', 'Water', 'Wind', 'Earth', 'Light', 'Dark')):
                fields['SkillIcon.TagName'] = 'UI.Skill.Action.Icon.' + effective['element']
            if int(identity) in learned and fields.get('belongCommandList') == [command]:
                fields['belongCommandList'] = [1]
                if fields.get('commandIdBelongDebuggingAllSkills') == [command, -1]:
                    fields['commandIdBelongDebuggingAllSkills'] = [901 if source.get('skillAttrType') == 'Magic' else 900, -1]
            effective = dict(source, **fields)
            if (effective.get('skillEffectType') == 'DamageAndRecovery'
                    and effective.get('parameterVariationType') == 'Increase'
                    and effective.get('parameterType') == 'HitPoint'
                    and effective.get('defaultTargetRelation') == 'Friendlies'
                    and effective.get('defaultTargetState') == 'Alive'
                    and effective.get('damageCalcType') in ('Magic', 'Fixed', 'TargetMaxHPRatio')):
                fields.setdefault('availableLocation', 'Anywhere')
                fields.setdefault('mapEffectType', 'RecoveryHP')
                fields.setdefault('isTargetIgnoreSelf', False)
                if effective.get('damageCalcType') == 'Magic' and effective.get('DamageType') == 'None':
                    fields.setdefault('DamageType', 'Magic')
    return result


def membership(unit):
    value = unit.get(FIELD)
    if value is None:
        return None
    if (not isinstance(value, dict) or set(value) != {'version', 'preset', 'enabled'}
            or value.get('version') != 1 or type(value.get('enabled')) is not bool
            or not isinstance(value.get('preset'), str) or not value['preset']
            or unit.get('native') is not None or unit.get('party') is not None):
        raise ValueError('Invalid Sephira vision membership. Restore its saved character config.')
    return value


def runtime_membership(unit):
    """The independent bundled Fina needs the same runtime reward fixes.

    This does not enroll her in the collection or its acquisition overrides.
    """
    value = membership(unit)
    if value is not None: return value
    ffbe = unit.get('ffbe') or {}
    if (unit.get('native') is None and unit.get('party') is None
            and (unit.get('bundledPreset') == 'custom.crystal_fina.v1'
                 or (ffbe.get('source') == 'CUSTOM'
                     and '99887755552703' in (str(ffbe.get('id')), str(ffbe.get('base')))))):
        return {'version': 1, 'preset': 'crystal_fina', 'enabled': True}
    return None


def repair_appearance(unit):
    """Match Studio's one-time presentation swap without changing learned data."""
    if unit.get('native') is not None or unit.get('party') is not None: return unit
    member = membership(unit)
    if member is None: return unit
    policy = json.loads(Path(__file__).with_name('sephira_visuals.json').read_bytes())
    update = policy.get('appearanceUpdates', {}).get(member['preset'])
    if (not update or unit.get('sephiraAppearanceRevision', 0) >= update['version']
            or (unit.get('ffbe') or {}).get('id') != update['from']): return unit
    result = copy.deepcopy(unit)
    result.update(copy.deepcopy(update['fields']))
    result['ffbe']['dir'] = f"units/ffbe/{unit['key']}/sprites/{result['ffbe']['id']}"
    result['command'].update(update['command'])
    result['master'].update(update['master'])
    result['sephiraAppearanceRevision'] = update['version']
    return result


def active_units(units):
    """Filter before sprite generation, acquisition, animations and verification.

    Keep the full saved roster intact so disabling the collection never deletes
    edits or reuses its IDs. Untagged user entries and native overrides pass through.
    """
    result = []
    seen = set()
    for unit in units:
        value = membership(unit)
        if value is not None:
            if value['preset'] in seen:
                raise ValueError('Duplicate Sephira preset in the saved roster.')
            seen.add(value['preset'])
            if not value['enabled'] or value['preset'] in RETIRED:
                continue
        result.append(unit)
    return result


def native_motion_for(units, identity):
    return any(str(u.get('id')) == str(identity) and runtime_membership(u) is not None
               for u in active_units(units))


def native_motion_names(unit):
    value = runtime_membership(unit)
    if value is None: return []
    policy = json.loads(Path(__file__).with_name('sephira_native_presentations.json').read_bytes())
    return policy.get('modelMotions', {}).get(value['preset'], [])


def prepare_battle_sizes(tables, units, rows):
    """Shrink playable Nalu only; boss design rows keep their separate scale."""
    rel = 'Battle/Unit/DT_BtlUnitDesignParameter'
    for unit in units:
        member = membership(unit)
        if member is None or not member['enabled'] or member['preset'] != 'nalu': continue
        sources = [(key, value) for key, value in rows(rel).items() if value['ID'] == unit['donor']]
        if len(sources) != 1: raise ValueError('The native Nalu battle-size donor is unavailable.')
        key, source = sources[0]
        scale = source['Scale']
        scale = round((scale if scale > 0 else 1.0) * .65, 6)
        table = tables.setdefault(rel, {'asset': 'FFRS/Content/Datatable/' + rel, 'add': [], 'set': []})
        edits = [e for e in table['add'] if e['row'] == unit['jp']]
        if edits:
            edits[0]['set']['Scale'] = scale
        else:
            table['add'].append({'row': unit['jp'], 'cloneFrom': key,
                                 'set': {'ID': unit['id'], 'Scale': scale}})


def verify_runtime_rows(root, tool, usmap, units, rows):
    """Read back every selected kit's grants before converting any sprites."""
    selected = [u for u in units if runtime_membership(u) is not None]
    if not selected: return
    root = Path(root); work = root / 'build/sephira-reward-check'; work.mkdir(parents=True, exist_ok=True)
    rels = ('Skill/DT_SkillData', PASSIVE, 'Skill/DT_MasterSkillData',
            'Item/Vision/DT_VisionAwakeningMasteryData', 'Item/Vision/DT_VisionSynchroMasteryData')
    built = {}
    for rel in rels:
        target = work / (rel.replace('/', '_') + '.json')
        subprocess.run(tool + ['rows', str(root / 'build/visions_mod/assets/FFRS/Content/Datatable' / (rel + '.uasset')),
                               str(target), '--usmap', usmap], check=True, capture_output=True)
        built[rel] = json.loads(target.read_text(encoding='utf-8-sig'))['rows']
    lookups = {kind: {r['ID']: r for r in built[rel].values()} for kind, rel in (
        ('ActiveSkill', rels[0]), ('PassiveSkill', PASSIVE), ('MasterSkill', rels[2]))}
    for unit in selected:
        master=lookups['MasterSkill'].get(unit['master']['id'])
        if not master or master.get('VisionId')!=unit['id']:
            raise ValueError(f'{unit["en"]}: its Spirit points to another vision\'s mastery rewards.')
        for field, rel in [('awakening', rels[3]), ('synchro', rels[4])]:
            for rank, grants in enumerate(unit[field]):
                found = [r for r in built[rel].values() if r['ID'] == unit['id'] and r['Level'] == rank]
                if len(found) != 1: raise ValueError(f'{unit["en"]}: missing {field} rank {rank}.')
                actual = [[g['parameterType'], *g['params']] for g in found[0]['detailData'] if g['parameterType'] != 'None']
                expected = [[*g[:2], g[2] if len(g) > 2 else -1] for g in grants]
                if actual != expected: raise ValueError(f'{unit["en"]}: incorrect {field} rank {rank}; rebuild its reward data.')
                for kind, identity, *_ in grants:
                    if kind not in lookups: continue
                    value = lookups[kind].get(identity)
                    if not value or value.get('Name') in (None, '', 'None'):
                        raise ValueError(f'{unit["en"]}: {field} rank {rank} has an unnamed or unavailable {kind} {identity}.')
                    if kind == 'PassiveSkill' and not 1000 <= identity < 2000:
                        raise ValueError(f'{unit["en"]}: passive {identity} is outside the game\'s passive lookup range.')
        for identity, recipe in (unit.get('skills') or {}).items():
            actual = lookups['ActiveSkill'].get(int(identity))
            if not actual: raise ValueError(f'{unit["en"]}: custom skill {identity} was not written.')
            for field in ('belongCommandList', 'availableLocation', 'mapEffectType', 'isTargetIgnoreSelf'):
                if field in recipe.get('set', {}) and actual.get(field) != recipe['set'][field]:
                    raise ValueError(f'{unit["en"]} / {recipe["en"]}: {field} did not survive serialization.')
            icon = recipe.get('set', {}).get('SkillIcon.TagName')
            if icon and actual.get('SkillIcon', {}).get('TagName') != icon:
                raise ValueError(f'{unit["en"]} / {recipe["en"]}: its elemental icon did not survive serialization.')
    report = root / 'build/sephira-animation-report.json'
    impacts = [e for e in json.loads(report.read_bytes())['skills'] if e.get('elementalImpact')] if report.is_file() else []
    if impacts:
        data = {}
        for rel in ('Battle/Sequencer/DT_BtlHitEffectData', 'Battle/Sequencer/DT_BtlHitAssetData'):
            target = work / (rel.replace('/', '_') + '.json')
            subprocess.run(tool + ['rows', str(root / 'build/visions_mod/assets/FFRS/Content/Datatable' / (rel + '.uasset')),
                                  str(target), '--usmap', usmap], check=True, capture_output=True)
            data[rel] = {r['ID']: r for r in json.loads(target.read_text(encoding='utf-8-sig'))['rows'].values()}
        policy = json.loads(Path(__file__).with_name('sephira_native_presentations.json').read_bytes())['elementalImpacts']
        for entry in impacts:
            reaction = data['Battle/Sequencer/DT_BtlHitEffectData'].get(entry['id'], {})
            effect = data['Battle/Sequencer/DT_BtlHitAssetData'].get(entry['id'], {})
            expected = policy['elements'][entry['elementalImpact']['element']]['path']
            if reaction.get('NormalEffectID') != entry['id'] or effect.get('niagaraAsset') != expected:
                raise ValueError(f'{entry["vision"]} / {entry["name"]}: its cosmetic elemental impact did not serialize.')
            if effect.get('CueSheetName') or effect.get('playLabel') or effect.get('HitSlowDilation') != 1:
                raise ValueError('A cosmetic elemental impact unexpectedly changes sound or battle speed.')
    print(f'OK: all awakening/MR rewards, skill names and learned-command availability checked for {len(selected)} Sephira visions')


def bind_units(units, rows):
    """Private equivalents follow allocated IDs, including imported/reset kits.

    Native originals and saved configs remain unchanged. Ordinary stat/status
    parameters, skill-specific bonuses and equip costs are retained verbatim.
    """
    result = copy.deepcopy(units)
    if not any(runtime_membership(u) is not None for u in result): return result
    passives = {v['ID']: (k, v) for k, v in rows(PASSIVE).items()}
    effects = {v['ID']: (k, v) for k, v in rows(EFFECT).items()}
    native_skills = {v['ID'] for v in rows('Skill/DT_SkillData').values()}
    allocated = {}
    for u in result:
        value = runtime_membership(u)
        if value is None: continue
        import _ffr_esper_mastery
        _ffr_esper_mastery.repair(u)
        repair_mastery_scope(u)
        repair_kit_rewards(u)
        repair_equipable_mr(u)
        owned = {int(sid) for sid in u.get('skills', {})}
        if u.get('lb_custom'): owned.add(440000 + (u['id'] - 13099) * 10)
        if native_skills & owned:
            raise ValueError('A Sephira custom skill/LB ID overlaps the game catalog. Reset this preset in Studio to allocate safe IDs.')
        private = {}
        labels = {str(sid):dict(zip(('name','desc'),text))
                  for sid,text in MASTERY_LABELS.get(value['preset'],{}).items()}
        labels.update(u.get('sephiraPassiveText') or {})
        for field in ['awakening', 'synchro']:
            for tier in u[field]:
                for g in tier:
                    if g[0]=='PassiveSkill' and g[1] in _ffr_esper_mastery.IDS: continue
                    if g[0] == 'PassiveSkill' and str(g[1]) in labels and g[1] not in BINDINGS:
                        sid = g[1]
                        pk, passive = passives[sid]
                        new_sid = private_passive_id(value['preset'], sid)
                        owner = (value['preset'], sid)
                        if new_sid in allocated and allocated[new_sid] != owner:
                            raise ValueError('Edited Sephira passive identities collide; change the duplicated custom membership.')
                        allocated[new_sid] = owner
                        if new_sid in passives:
                            raise ValueError('Sephira private passive ID overlaps the game catalog.')
                        label = labels[str(sid)]
                        fields = {'ID': new_sid, 'Name': label['name'], 'Description': label['desc']}
                        # Item-granted imbues/evasion can have zero equip cost;
                        # learned equivalents use the native 20-AP utility tier.
                        if passive['equipCost'] == 0: fields['equipCost'] = 20
                        private[sid] = {'passive': {'row': f"Studio_Sephira_{u['id']}_Passive_{sid}",
                            'cloneFrom': pk, 'set': fields}}
                        g[1] = new_sid
                        continue
                    if g[0] != 'PassiveSkill' or g[1] not in BINDINGS: continue
                    sid = g[1]
                    eid, kind, index, original, replacement = BINDINGS[sid]
                    pk, passive = passives[sid]; ek, effect = effects[eid]
                    if effect['EffectType'] != kind or effect['ParamList'][index] != original:
                        raise ValueError(f'Native passive {sid} changed; re-audit Sephira owner bindings for this game version.')
                    new_sid = private_passive_id(value['preset'], sid)
                    owner = (value['preset'], sid)
                    if new_sid in allocated and allocated[new_sid] != owner:
                        raise ValueError('Edited Sephira passive identities collide; change the duplicated custom membership.')
                    allocated[new_sid] = owner
                    new_eid = u['id'] * 10000 + eid
                    if new_sid in passives or new_eid in effects:
                        raise ValueError('Sephira private IDs overlap the game catalog; re-audit this game version.')
                    bundles = copy.deepcopy(passive['effectBundleList'])
                    for b in bundles:
                        if b['effectId'] == eid: b['effectId'] = new_eid
                    params = list(effect['ParamList'])
                    params[index] = u['command']['id'] if replacement == 'command' else (440000 + (u['id'] - 13099) * 10 if u.get('lb_custom') else u['lb'])
                    for slot, native_id, source in SIGNATURE_BINDINGS.get((value['preset'],sid), []):
                        if effect['ParamList'][slot] != native_id:
                            raise ValueError('Native signature binding changed; re-audit passive ' + str(sid))
                        matches = [int(k) for k,r in (u.get('skills') or {}).items() if r.get('from') == source]
                        # An edited kit may remove a signature. Never leave a
                        # reference to the unrelated original vision's skill.
                        params[slot] = matches[0] if len(matches) == 1 else -1
                    private[sid] = {
                        'passive': {'row': f"Studio_Sephira_{u['id']}_Passive_{sid}", 'cloneFrom': pk,
                                    'set': {'ID': new_sid, 'effectBundleList': bundles,
                                            **({'Name': labels[str(sid)]['name'], 'Description': labels[str(sid)]['desc']}
                                               if str(sid) in labels else {})}},
                        'effect': {'row': f"Studio_Sephira_{u['id']}_Effect_{eid}", 'cloneFrom': ek,
                                   'set': {'ID': new_eid, 'ParamList': params}}}
                    g[1] = new_sid
        u['_sephiraBindings'] = list(private.values())
    return result


def prepare(tables, units):
    for u in units:
        for binding in u.get('_sephiraBindings', []):
            for rel, key in [(EFFECT, 'effect'), (PASSIVE, 'passive')]:
                if key not in binding: continue
                tables.setdefault(rel, {'asset': 'FFRS/Content/Datatable/' + rel, 'add': [], 'set': []})['add'].append(binding[key])
