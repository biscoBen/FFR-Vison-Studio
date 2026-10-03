"""Build an opt-in Crystal Fina shrine using the installed game's own levels."""
import base64
import copy
import json
from pathlib import Path
import struct
import uuid

NAME = 'Studio_CrystalCave'
MAP_ID = 29991
STONE_ID = 29990
STONE_NAME = NAME + '_Stone'
EVENT = NAME + '_Acquire'
SPRITE = '99887755552703'
MAP = 'Map/MapData/DT_MapData_01Gra'
COMPOSITE = 'Map/CDT_MapData_Demo'
MAP_UNIT = 'Asset/Map/DT_MapUnitAsset'
PLACEMENT = 'Asset/Map/DT_MapUnitPlacementAsset'
WORLD = 'Map/Wld/EV/Wld_01Gra_EV'
WORLD_PL = 'Map/Wld/Wld_PL'
ROOM = 'Map/Com/00Com/00Com_217/Com_00Com_217_PL'
ROOM_BG = 'Map/Com/00Com/00Com_217/BG/Com_00Com_217_01_BG'
STONE = 'Map/Dng/01Gra/01Gra_44/Dng_01Gra_44_PL'
STONE_NAV = 'Map/Dng/01Gra/01Gra_44/NAV/Dng_01Gra_44_01_NAV'
DONOR_GD = 'Map/Dng/01Gra/01Gra_44/GD/Dng_01Gra_44_01_GD'
WORLD_BG = 'Map/Wld/01Gra/BG/Wld_01Gra_BG'
TRANSITION_GD = 'Map/Dng/01Gra/01Gra_43/GD/Dng_01Gra_43_GD'
PACKAGE = 'Map/StudioCrystalCave/' + NAME
GRANT_DONOR = 'Sequencer/Event/Main_Event/C01/Ev_C01_014_03/SEQ_C01_014_03'
GRANT_SEQUENCE = PACKAGE + '_Grant'
# Earth Shrine is (18040, 20920); Mitra is (16598, 21654).
# The entrance sits north of their connecting road. Returning lands outside
# its trigger, so leaving cannot immediately send the player back inside.
ENTRANCE = (17600.0, 21400.0, 160.0)
ENTRANCE_MODEL = (ENTRANCE[0], ENTRANCE[1], 80.0)
ENTRANCE_SCALE = (0.8, 0.8, 0.8)
FINA_SCALE = 4.25
FINA_FLOAT = 40.0
FINA_ALIGNMENT_Y = 144.0  # Live test: two field-sprite widths, plus a small final nudge right.
RETURN = (17250.0, 21400.0, 200.0)
SPAWN = (750.0, 0.0, 100.0)
PORTAL = (4000.0, 31.0, 100.0)
PORTAL_RETURN = (3500.0, 31.0, 100.0)


def target(units):
    choices = [u for u in units if not u.get('native') and not u.get('party')
               and str((u.get('ffbe') or {}).get('id')) == SPRITE]
    if len(choices) != 1 or type(choices[0].get('id')) is not int:
        raise ValueError('Crystal Fina cave needs exactly one bundled Crystal Fina in Added visions.')
    return choices[0]


def prepare(tables, units, root, rows):
    import _ffr_testing as testing
    if not testing.settings(root)['crystalCave']:
        return
    unit = target(units)
    def table(rel):
        return tables.setdefault(rel, {'asset': 'FFRS/Content/Datatable/' + rel, 'add': [], 'set': []})
    for rel in (MAP, COMPOSITE, MAP_UNIT):
        originals = rows(rel)
        if NAME in originals or STONE_NAME in originals or any(v.get('ID') in (MAP_ID, STONE_ID) for v in originals.values()):
            raise ValueError('The Crystal Fina cave identity conflicts with a native game entry.')
    room = rows(MAP).get('00Com_217')
    if (not room or room.get('ID') != 10020 or room.get('Level') != '/Game/' + ROOM
            or rows(COMPOSITE).get('00Com_217') != room):
        raise ValueError('The Leah/Tronn crystal room changed; no cave was built.')
    stone = rows(MAP).get('01Gra_44')
    if (not stone or stone.get('ID') != 10001 or stone.get('Level') != '/Game/' + STONE
            or rows(COMPOSITE).get('01Gra_44') != stone):
        raise ValueError('The stone cave template changed; no cave was built.')
    if room.get('startupEventList') or stone.get('startupEventList'):
        raise ValueError('The cave templates gained startup events; no story events were copied.')
    for rel in (MAP, COMPOSITE):
        table(rel)['add'].append({'row': NAME, 'cloneFrom': '00Com_217', 'set': {
            'ID': MAP_ID, 'Name': 'Crystal Fina Cave', 'developmentName': NAME,
            'Level': '/Game/' + PACKAGE + '_PL', 'bOverride_MapType': True, 'MapType': 'Dungeon'}})
        table(rel)['add'].append({'row': STONE_NAME, 'cloneFrom': '01Gra_44', 'set': {
            'ID': STONE_ID, 'Name': 'Crystal Fina Cave', 'developmentName': STONE_NAME,
            'Level': '/Game/' + PACKAGE + '_Stone_PL', 'bOverride_MapType': True}})
    key, source = next((k, v) for k, v in rows(MAP_UNIT).items() if v.get('ID') == 9020)
    if len(source.get('animationAssetList', [])) != 1:
        raise ValueError('The stationary NPC sprite template changed.')
    sprite = f'/Game/Chara/summon/summon{unit["id"]}/summon{unit["id"]}'
    material = f'/Game/BP/Map/Unit/Material/M_CrystalFina_AlphaTest_{unit["id"]}'
    table(MAP_UNIT)['add'].append({'row': NAME, 'cloneFrom': key, 'set': {
        'ID': MAP_ID, 'animationAssetList[0].Ss6Project': sprite,
        'animationAssetList[0].Material': material, 'animationAssetList[0].isVisionCharacter': False,
        'animationAssetList[0].textureBaseColor': sprite + '_tex',
        'animationAssetList[0].textureNormal': sprite + '_normal',
        'animationAssetList[0].textureMetallicRoughness': sprite + '_mreo'}})
    placements = rows(PLACEMENT)
    if NAME in placements or STONE_NAME in placements or any(v.get('mapId') in (MAP_ID, STONE_ID) for v in placements.values()):
        raise ValueError('The Crystal Fina cave placement identity conflicts with the game.')
    key = next(k for k, v in placements.items() if v.get('mapId') == 10020)
    table(PLACEMENT)['add'].append({'row': NAME, 'cloneFrom': key, 'set': {'mapId': MAP_ID}})
    table(PLACEMENT)['add'].append({'row': STONE_NAME, 'cloneFrom': key, 'set': {'mapId': STONE_ID}})
    events = rows(testing.COMPOSITE)
    donor = events['C01_ArijigokuEncount']
    if (any(donor[k] != 'None' for k in ('TalkEventDataTable', 'EventSequence', 'EventBlueprint'))
            or any(donor[k] for k in ('OnFlagList', 'OffFlagList', 'FlagList', 'ProgressList',
                                      'ContinuousEventList', 'ObtainItemList', 'InitUnitDataList'))):
        raise ValueError('The story-free vision grant template changed.')
    desired = testing.apply_fields(donor, {
        'Description': 'Crystal Fina cave acquisition', 'encountGroupId': -1,
        'EventSequence': '/Game/' + GRANT_SEQUENCE,
        'IsGetOffVehicle': False, 'IsHiddenFieldUI': True, 'LoadingScreenSetting': 'White',
        'MapStartupSettings.ChangeBGM': 'NotChange',
        'RestoreSoundVolumeSettings.IsRevertValume': False,
        # The timeline executes the footer, as in the native acquisition event.
        'FooterSettings.IsApplyProgressis': False,
        'IsOpenDialogByFinishEvent': True,
        # Keep the controller-compatible event lifecycle. The same cave return
        # point also serves the room's ordinary exit, independently of grants.
        'TransitionLocation.mapId': STONE_ID, 'TransitionLocation.pointId': 1,
        'TransitionLocation.bDoAutoSave': False,
        'ObtainItemList': [{'Condition': f'{{item:{unit["id"]}}}==0', 'ID': unit['id'],
                            'Num': 1, 'Text': ''}]})
    grant = events['C01_014_03']
    for rel in (testing.EVENT, testing.COMPOSITE):
        if EVENT in rows(rel):
            raise ValueError('The Crystal Fina acquisition event already exists.')
        table(rel)['add'].append({'row': EVENT, 'cloneFrom': 'C01_014_03',
                                  'set': testing.field_delta(grant, desired)})


def export(view, name):
    matches = [(i, e) for i, e in enumerate(view['Exports'], 1) if e['ObjectName'] == name]
    if len(matches) != 1:
        raise ValueError('Cave level object missing or ambiguous: ' + name)
    return matches[0]


def property_data(owner, name):
    matches = [v for v in owner.get('Data', owner.get('Value', [])) if v['Name'] == name]
    if len(matches) != 1:
        raise ValueError('Cave level property missing or ambiguous: ' + name)
    return matches[0]


def set_value(owner, name, value):
    p = property_data(owner, name)
    p['Value'] = copy.deepcopy(value)
    p['IsZero'] = False


def vector(owner, name, values):
    p = property_data(owner, name)
    child, = p['Value']
    for axis, value in zip(('X', 'Y', 'Z'), values):
        child['Value'][axis] = value
    p['IsZero'] = child['IsZero'] = False


def named_properties(value):
    """Only visit decoded properties; retain every opaque cooked export byte."""
    if isinstance(value, dict):
        if 'Name' in value and 'Value' in value:
            yield value
        for child in value.values():
            yield from named_properties(child)
    elif isinstance(value, list):
        for child in value:
            yield from named_properties(child)


def names(view, value):
    # Append names, never reorder/remove names used by retained opaque exports.
    found = set(view['NameMap'])
    def visit(v):
        if isinstance(v, str):
            if v and v not in found:
                view['NameMap'].append(v); found.add(v)
        elif isinstance(v, list):
            for child in v: visit(child)
        elif isinstance(v, dict):
            for key, child in v.items():
                if key not in ('$type', 'Extras', 'Data') or not isinstance(child, str):
                    visit(child)
    visit(value)
    # IoStore keeps only this prefix of the legacy name map. Retained opaque
    # exports still use their original indices; new delegate/animation names
    # must also survive packing, so keep the complete map without reordering.
    view['NamesReferencedFromExportDataCount'] = len(view['NameMap'])


def clone_graph(dst, src, indices, roots):
    """Import a fully decoded actor/component graph with typed reference remapping."""
    mapping = dict(roots)
    mapping.update({old: len(dst['Exports']) + i for i, old in enumerate(indices, 1)})
    imported = {0: 0}
    def ref(index):
        if index == 0: return 0
        if index >= 0:
            if index not in mapping:
                raise ValueError('Cave actor graph has an unresolved export reference: ' + str(index))
            return mapping[index]
        if index not in imported:
            imp = copy.deepcopy(src['Imports'][-index - 1]); imp['OuterIndex'] = ref(imp['OuterIndex'])
            try: new = -(dst['Imports'].index(imp) + 1)
            except ValueError:
                dst['Imports'].append(imp); new = -len(dst['Imports'])
            imported[index] = new
        return imported[index]
    def remap(value):
        if isinstance(value, list): return [remap(v) for v in value]
        if not isinstance(value, dict): return value
        result = {k: remap(v) for k, v in value.items()}
        if value.get('$type', '').split('.')[-1] == 'ObjectPropertyData, UAssetAPI':
            result['Value'] = ref(value['Value'])
        if 'Delegate' in value and 'Object' in value:
            result['Object'] = ref(value['Object'])
        return result
    for old in indices:
        item = src['Exports'][old - 1]
        if 'NormalExport' not in item['$type'] or not isinstance(item.get('Data'), list):
            raise ValueError('Cave actor graph contains an opaque export; refusing to remap it.')
        copied = remap(item)
        for key in ('OuterIndex', 'ClassIndex', 'SuperIndex', 'TemplateIndex'):
            copied[key] = ref(item[key])
        for key in ('SerializationBeforeSerializationDependencies', 'CreateBeforeSerializationDependencies',
                    'SerializationBeforeCreateDependencies', 'CreateBeforeCreateDependencies'):
            copied[key] = [ref(i) for i in item[key]]
        dst['Exports'].append(copied)
        dst['DependsMap'].append([ref(i) for i in (src['DependsMap'][old - 1] or [])])
    names(dst, [dst['Imports'], dst['Exports'][-len(indices):]])
    return mapping


def private_level(original, old, new):
    result = copy.deepcopy(original)
    old_leaf, new_leaf = old.rsplit('/', 1)[1], new.rsplit('/', 1)[1]
    def replace(value):
        if isinstance(value, str): return {old: new, old_leaf: new_leaf}.get(value, value)
        if isinstance(value, list): return [replace(v) for v in value]
        if isinstance(value, dict): return {k: replace(v) for k, v in value.items()}
        return value
    return replace(result)


def actors(view, selected):
    _, level = export(view, 'PersistentLevel')
    level['Actors'] = list(selected)
    # The cooked level also retains explicit preload dependencies on its actors.
    old_actors = set(i for i, e in enumerate(view['Exports'], 1) if e['OuterIndex'] == export(view, 'PersistentLevel')[0])
    level['CreateBeforeSerializationDependencies'] = [i for i in level['CreateBeforeSerializationDependencies']
                                                       if i not in old_actors or i in selected]
    for i in selected:
        if i and i not in level['CreateBeforeSerializationDependencies']:
            level['CreateBeforeSerializationDependencies'].append(i)


def clear_crystals(view):
    """Remove the two native crystals and their glow, retaining ambient effects."""
    crystals = {}; glows = []
    for i, e in enumerate(view['Exports'], 1):
        if not isinstance(e.get('Data'), list): continue
        for p in e['Data']:
            if p['Name'] not in ('StaticMesh', 'Asset') or p['Value'] >= 0: continue
            name = view['Imports'][-p['Value']-1]['ObjectName']
            if p['Name'] == 'StaticMesh' and name in ('SM_Env_Com_magicstone001', 'SM_Env_Com_magicstone002'):
                if name in crystals: raise ValueError('The original Leah/Tronn crystal geometry changed.')
                crystals[name] = (e['OuterIndex'], i)
            if p['Name'] == 'Asset' and name == 'NS_EF_BG_00Common_Glow_001':
                glows.append(e['OuterIndex'])
    if len(crystals) != 2 or len(glows) != 2:
        raise ValueError('The original Leah/Tronn crystals or glow effects changed.')
    removed = {a for a, _ in crystals.values()} | set(glows)
    level = export(view, 'PersistentLevel')[1]
    actors(view, [i for i in level['Actors'] if i not in removed])
    return crystals


def fina_spawn(view, crystal):
    """Use native acquisition lights and the small live-tested lateral offset.

    Both lights sit above the platform. Their Z is a safe spawn height; the
    capsule must still settle against native floor collision.
    """
    anchors = [property_data(crystal, 'RelativeLocation')['Value'][0]['Value']]
    for e in view['Exports']:
        if not isinstance(e.get('Data'), list): continue
        for p in e['Data']:
            if (p['Name'] == 'StaticMesh' and p['Value'] < 0
                    and view['Imports'][-p['Value']-1]['ObjectName'] == 'SM_Env_Com_magicstone002'):
                anchors.append(property_data(e, 'RelativeLocation')['Value'][0]['Value'])
    if len(anchors) != 2:
        raise ValueError('The paired acquisition crystal anchors changed.')
    lights = []; floors = []
    for e in view['Exports']:
        if not isinstance(e.get('Data'), list): continue
        props = {p['Name']: p for p in e['Data']}
        mesh = props.get('StaticMesh', {}).get('Value', 0)
        if mesh < 0 and view['Imports'][-mesh-1]['ObjectName'] == 'SM_Env_Com_00Com_44_ground001':
            floors.append(e)
        if (e['ClassIndex'] < 0 and view['Imports'][-e['ClassIndex']-1]['ObjectName'] == 'PointLightComponent'
                and 'RelativeLocation' in props):
            lights.append(props['RelativeLocation']['Value'][0]['Value'])
    if len(floors) != 1 or not lights:
        raise ValueError('The crystal room ground or acquisition lights changed.')
    selected = []
    for anchor in anchors:
        def distance(loc):
            return sum((float(loc[a]) - float(anchor[a])) ** 2 for a in ('X', 'Y'))
        light = min(lights, key=distance)
        if distance(light) >= 200.0 ** 2 or light in selected:
            raise ValueError('The paired acquisition lights changed.')
        selected.append(light)
    midpoint = tuple(sum(float(light[a]) for light in selected) / 2 for a in ('X', 'Y', 'Z'))
    return (midpoint[0], midpoint[1] + FINA_ALIGNMENT_Y, midpoint[2])


def data_property(name, value, kind, **extra):
    return dict(Name=name, Value=value, ArrayIndex=0, IsZero=False, PropertyGuid=None,
                PropertyTagFlags='None', PropertyTypeName=None, PropertyTagExtensions='NoExtension',
                **{'$type': 'UAssetAPI.PropertyTypes.Objects.' + kind + ', UAssetAPI'}, **extra)


def blocking_level(donor, label, center, extent):
    """Keep the native cooked BlockingVolume graph and physics bytes intact.

    Generic Actor instance boxes survived serialization but did not block in
    game. A native volume constructs/registers its BrushComponent and brings a
    cooked convex BodySetup. Copy the whole level to preserve opaque model and
    Chaos data at their original export/name indices; activate only the volume.
    """
    view = private_level(donor, '/Game/' + TRANSITION_GD, '/Game/' + PACKAGE + '_' + label)
    owner_id, owner = export(view, 'BlockingVolume_1')
    root_id, root = export(view, 'BrushComponent0')
    body_id, body = export(view, 'BodySetup_0')
    if (property_data(owner, 'RootComponent')['Value'] != root_id
            or property_data(root, 'BrushBodySetup')['Value'] != body_id
            or property_data(body, 'CollisionTraceFlag')['Value'] != 'CTF_UseSimpleAsComplex'):
        raise ValueError('The native blocking volume physics layout changed.')
    convex, = property_data(property_data(body, 'AggGeom'), 'ConvexElems')['Value']
    bounds, = property_data(convex, 'ElemBox')['Value']
    bounds = bounds['Value']
    half = tuple((float(bounds['Max'][axis]) - float(bounds['Min'][axis])) / 2 for axis in ('X', 'Y', 'Z'))
    if half != (375.0, 100.0, 300.0):
        raise ValueError('The native cooked blocker bounds changed.')
    owner['ObjectName'] = NAME + '_' + label
    vector(root, 'RelativeLocation', center)
    scale = copy.deepcopy(property_data(root, 'RelativeLocation')); scale['Name'] = 'RelativeScale3D'
    scale['Value'][0]['Name'] = 'RelativeScale3D'
    root['Data'].append(scale); vector(root, 'RelativeScale3D', tuple(size / old for size, old in zip(extent, half)))
    actors(view, [export(view, 'CPP_MuchaWorldSetting')[0], 0, owner_id])
    names(view, view['Exports'])
    return view


def add_collision_stream(view, world_name, template_view, path):
    """Always load a private collision level without changing original streams."""
    world_id, world = export(view, world_name)
    donor_id, donor = next((i, e) for i, e in enumerate(template_view['Exports'], 1)
                          if e['ClassIndex'] < 0 and template_view['Imports'][-e['ClassIndex']-1]['ObjectName']
                          == 'LevelStreamingAlwaysLoaded')
    parent = donor['OuterIndex']
    m = clone_graph(view, template_view, [donor_id], {parent: world_id})
    stream_id = m[donor_id]; stream = view['Exports'][stream_id-1]
    stream['ObjectName'] = 'LevelStreamingAlwaysLoaded_' + Path(path).name
    property_data(stream, 'WorldAsset')['Value']['AssetPath'].update(
        PackageName='/Game/' + path, AssetName=Path(path).name)
    raw = base64.b64decode(world['Extras'])
    if len(raw) < 12 or len(raw) % 4:
        raise ValueError('The native world streaming layout changed.')
    values = list(struct.unpack('<' + 'i' * (len(raw) // 4), raw))
    if values[2] != len(values) - 3 or any(not 0 < i <= len(view['Exports']) for i in values[3:]):
        raise ValueError('The native world streaming references changed.')
    values[2] += 1; values.append(stream_id)
    world['Extras'] = base64.b64encode(struct.pack('<' + 'i' * len(values), *values)).decode()
    world['CreateBeforeSerializationDependencies'].append(stream_id)
    names(view, [stream, view['Imports']])


def grant_sequence(source):
    """Run the native event lifecycle; the obtain popup does not apply grants.

    Use the native director's parameterless ExecuteHeader/ExecuteFooter functions
    and current event row. No original actor bindings, dialogue or camera tracks
    participate. Preserve indices/opaque exports, but invalidate compiled tracks.
    """
    view = private_level(source, '/Game/' + GRANT_DONOR, '/Game/' + GRANT_SEQUENCE)
    _, sequence = export(view, Path(GRANT_SEQUENCE).name)
    scene = view['Exports'][property_data(sequence, 'MovieScene')['Value']-1]
    def imported(name):
        candidates = [-(i+1) for i, e in enumerate(view['Imports']) if e['ObjectName'] == name]
        if len(candidates) != 1: raise ValueError('The native grant function changed: ' + name)
        return candidates[0]
    set_value(sequence, 'DirectorClass', imported('CPP_TalkEventSequenceDirector'))
    set_value(sequence, 'CompiledData', 0)
    set_value(property_data(sequence, 'BindingReferences'), 'SortedReferences', [])
    for name in ('Possessables', 'ObjectBindings', 'BindingGroups'): set_value(scene, name, [])
    set_value(scene, 'CameraCutTrack', 0)
    track_id, track = export(view, 'MovieSceneEventTrack_0')
    sections = property_data(track, 'Sections')['Value']
    if len(sections) != 1: raise ValueError('The native event track changed.')
    section = view['Exports'][sections[0]['Value']-1]
    prop = copy.deepcopy(property_data(scene, 'Tracks')['Value'][0]); prop['Value'] = track_id
    set_value(scene, 'Tracks', [prop])
    channel = property_data(section, 'EventChannel')
    times = property_data(channel, 'KeyTimes'); events = property_data(channel, 'KeyValues')
    first_time = times['Value'][0]; first_event = events['Value'][0]
    times['Value'] = []; events['Value'] = []
    for index, (tick, name) in enumerate(((0, 'ExecuteHeader'), (2400, 'ExecuteFooter'))):
        time = copy.deepcopy(first_time); time['Name'] = str(index)
        time['Value'][0]['Name'] = str(index)
        time['Value'][0]['Value']['Value'] = tick
        time['IsZero'] = time['Value'][0]['IsZero'] = False
        event = copy.deepcopy(first_event); event['Name'] = str(index)
        ptrs = property_data(event, 'Ptrs')
        set_value(ptrs, 'Function', imported(name))
        set_value(ptrs, 'BoundObjectProperty', dict(property_data(ptrs, 'BoundObjectProperty')['Value'],
                                                  Path=[], ResolvedOwner=0))
        times['Value'].append(time); events['Value'].append(event)
    times['IsZero'] = events['IsZero'] = channel['IsZero'] = False
    playback = property_data(scene, 'PlaybackRange')['Value'][0]['Value']
    playback['LowerBound']['Value']['Value'] = 0
    playback['UpperBound']['Value']['Value'] = 4800
    # Track-specific cached evaluation ranges/signatures must not reuse the
    # original cutscene's compiled evaluation field.
    track['Data'] = [p for p in track['Data'] if p['Name'] not in ('EvaluationField', 'EvaluationFieldGuid')]
    for e in (sequence, scene, track, section):
        signature = property_data(e, 'Signature')['Value'][0]
        signature['Value'] = '{' + str(uuid.uuid5(uuid.NAMESPACE_URL, GRANT_SEQUENCE + ':' + e['ObjectName'])).upper() + '}'
    names(view, view['Exports'])
    return view


def acquisition_interaction(npc, donor, conditional_template, unit):
    """Use the controller-compatible manual event-only acquisition route."""
    level_id, level = export(npc, 'PersistentLevel')
    world_id = export(npc, NAME + '_NPC')[0]
    m = clone_graph(npc, donor, [2, 5], {8: level_id, 14: world_id})
    actor = npc['Exports'][m[5]-1]; box = npc['Exports'][m[2]-1]
    actor['ObjectName'] = NAME + '_AcquireInteraction'
    # A regular transition pre-event regressed controller confirmation of the
    # obtain dialog. The native event-only route leaves UI input with the event.
    transition(actor, conditional_template, STONE_ID, 1, auto=False)
    set_value(actor, 'm_UniqueId', MAP_ID + 1)
    # Preserve the same native Transition button route as the working portal.
    entry, = property_data(actor, 'mTransitionDataList')['Value']
    condition = f'{{item:{unit["id"]}}}==0'
    set_value(entry, 'FlagCondition', condition); set_value(entry, 'isEventOnly', True)
    original, = property_data(conditional_template, 'mTransitionDataList')['Value'][:1]
    event, = property_data(original, 'afterTransitionEventList')['Value']
    event = copy.deepcopy(event)
    if event['StructType'] != 'TalkEventPlayData':
        raise ValueError('The native manual event schema changed.')
    set_value(event, 'Condition', condition); set_value(event, 'EventId', EVENT)
    set_value(entry, 'EventList', [event])
    # The character lands on collision at runtime. Follow its capsule rather
    # than leaving the interaction volume at the light's floating spawn height.
    parent = copy.deepcopy(property_data(actor, 'RootComponent'))
    parent.update(Name='AttachParent', Value=37)
    box['Data'].append(parent)
    box['CreateBeforeSerializationDependencies'].append(37)
    vector(box, 'RelativeLocation', (0.0, 0.0, 0.0))
    vector(box, 'BoxExtent', (100.0, 100.0, 100.0))
    actors(npc, level['Actors'] + [m[5]])
    names(npc, [actor, box])


def npc_grant(owner, unit):
    """Restore the native talk binding from the previously working dialog flow."""
    for p in named_properties(property_data(owner, 'm_EventSettings')):
        if p['Name'] == 'Condition': p['Value'] = f'{{item:{unit["id"]}}}==0'; p['IsZero'] = False
        if p['Name'] == 'EventId': p['Value'] = EVENT; p['IsZero'] = False


def stone_navigation(source):
    """Retain cooked navigation while binding both connections to private actors."""
    view = private_level(source, '/Game/' + STONE_NAV, '/Game/' + PACKAGE + '_Stone_NAV')
    area = export(view, 'CPP_Map_NavMeshBoundsVolume_1')[1]
    entry, = property_data(area, 'm_TransitionTriggerList')['Value']
    trigger = property_data(entry, 'Trigger')
    original = trigger['Value']
    if (original['AssetPath']['PackageName'] != '/Game/' + DONOR_GD
            or original['SubPathString'] != 'PersistentLevel.BP_MapTransitionTrigger_C_1'):
        raise ValueError('The stone cave navigation connection changed.')
    links = []
    for index, actor in enumerate(('BP_MapTransitionTrigger_C_1', NAME + '_Portal')):
        link = copy.deepcopy(entry); link['Name'] = str(index)
        path = property_data(link, 'Trigger')['Value']
        path['AssetPath'].update(PackageName='/Game/' + PACKAGE + '_Stone_GD', AssetName=NAME + '_Stone_GD')
        path['SubPathString'] = 'PersistentLevel.' + actor
        links.append(link)
    set_value(area, 'm_TransitionTriggerList', links)
    names(view, view['Exports'])
    return view


def persistent_return_point(stone_pl, donor, nav):
    """Register the destination in the persistent level, bound to its own area."""
    level_id, level = export(stone_pl, 'PersistentLevel')
    world_id = export(stone_pl, NAME + '_Stone_PL')[0]
    m = clone_graph(stone_pl, donor, [4, 12], {8: level_id, 14: world_id})
    point = stone_pl['Exports'][m[4]-1]
    point['ObjectName'] = NAME + '_PortalReturn'
    set_value(point, 'm_PointID', 1)
    vector(stone_pl['Exports'][m[12]-1], 'RelativeLocation', PORTAL_RETURN)
    area = export(nav, 'CPP_Map_NavMeshBoundsVolume_1')[1]
    entry, _ = property_data(area, 'm_TransitionTriggerList')['Value']
    ref = copy.deepcopy(property_data(entry, 'Trigger')); ref['Name'] = '0'
    ref['Value']['AssetPath'].update(PackageName='/Game/' + PACKAGE + '_Stone_NAV', AssetName=NAME + '_Stone_NAV')
    ref['Value']['SubPathString'] = 'PersistentLevel.CPP_Map_NavMeshBoundsVolume_1'
    prop = data_property('m_AreaBoxList', [ref], 'ArrayPropertyData')
    prop['ArrayType'] = 'SoftObjectProperty'
    point['Data'] = [p for p in point['Data'] if p['Name'] != 'm_AreaBoxList'] + [prop]
    actors(stone_pl, level['Actors'] + [m[4]])
    names(stone_pl, [point, stone_pl['Exports'][m[12]-1]])


def settle_fina(npc, spawn):
    """Let the NPC capsule land on native collision without needing a controller."""
    movement = npc['Exports'][42]
    boolean = property_data(npc['Exports'][30], 'm_IsAnimationUseDirection')
    scalar = property_data(npc['Exports'][63], 'UUPerPixel')
    enum = property_data(npc['Exports'][30], 'm_Direction')
    for name, value, template in (
            ('bRunPhysicsWithNoController', True, boolean),
            ('bAlwaysCheckFloor', True, boolean),
            ('GravityScale', 1.0, scalar),
            ('DefaultLandMovementMode', 'MOVE_Walking', enum),
            ('MovementMode', 'MOVE_Falling', enum)):
        prop = copy.deepcopy(template)
        prop.update(Name=name, Value=value, IsZero=False)
        if template is enum: prop['EnumType'] = 'EMovementMode'
        movement['Data'] = [p for p in movement['Data'] if p['Name'] != name] + [prop]
    foot = property_data(npc['Exports'][109], 'RelativeLocation')['Value'][0]['Value']
    vector(npc['Exports'][36], 'RelativeLocation', (spawn[0], spawn[1], spawn[2] - float(foot['Z'])))
    names(npc, movement)


def transition(actor, conditional_template, map_id, point, auto=True):
    set_value(actor, 'm_MapId', map_id); set_value(actor, 'm_PointID', point)
    # The native conditional-transition struct exposes autosave and follow-up
    # events explicitly; clear the Earth Shrine's tutorial and story conditions.
    for name in ('m_IsUseCondion', 'mTransitionDataList', 'm_IsAutoTransition'):
        prop = copy.deepcopy(property_data(conditional_template, name))
        if name == 'm_IsAutoTransition': prop['Value'] = auto; prop['IsZero'] = False
        if name == 'mTransitionDataList':
            prop['Value'] = prop['Value'][:1]
            for p in named_properties(prop):
                if p['Name'] == 'FlagCondition': p['Value'] = ''
                if p['Name'] == 'mapId': p['Value'] = map_id
                if p['Name'] == 'pointId': p['Value'] = point
                if p['Name'] == 'isEnableAutoSave': p['Value'] = False
                if p['Name'] in ('EventList', 'eventList2', 'afterTransitionEventList'): p['Value'] = []
                p['IsZero'] = False
        actor['Data'] = [p for p in actor['Data'] if p['Name'] != name] + [prop]


def make_levels(source, unit):
    """Return generated map views without altering any source view."""
    # Reject reordered native graphs rather than editing a different actor.
    expected = {12: 'EventTriggerBox', 31: 'BP_MapUnit_NPC_Field_C_2',
                37: 'CollisionCylinder', 43: 'CharMoveComp', 49: 'BillboardComponent',
                55: 'CPP_MapUnitCommonOperation_0', 64: 'SsPlayerComponent',
                95: 'PersistentLevel', 110: 'FootComponent', 137: 'Wld_01Gra_EV'}
    if any(source[WORLD]['Exports'][i-1]['ObjectName'] != n for i, n in expected.items()):
        raise ValueError('The native overworld NPC graph changed; no cave was built.')
    gd = private_level(source[DONOR_GD], '/Game/' + DONOR_GD, '/Game/' + PACKAGE + '_GD')
    transition(export(gd, 'BP_MapTransitionTrigger_C_1')[1],
               export(source[TRANSITION_GD], 'BP_MapTransitionTrigger_C_0')[1], STONE_ID, 1)
    actors(gd, [7, 0, 5, 4])
    vector(gd['Exports'][11], 'RelativeLocation', SPAWN)
    # Room collision/lighting are the native shrine's. Only this private trigger
    # and spawn level comes from the cave; no original cave quest is loaded.
    vector(gd['Exports'][1], 'RelativeLocation', (-100.0, 0.0, 100.0))
    vector(gd['Exports'][1], 'BoxExtent', (300.0, 500.0, 250.0))

    bg_room = private_level(source[ROOM_BG], '/Game/' + ROOM_BG, '/Game/' + PACKAGE + '_BG')
    crystals = clear_crystals(bg_room)
    clear_mesh = bg_room['Exports'][crystals['SM_Env_Com_magicstone001'][1]-1]
    spawn = fina_spawn(bg_room, clear_mesh)

    npc = private_level(source[WORLD], '/Game/' + WORLD, '/Game/' + PACKAGE + '_NPC')
    actors(npc, [70, 0, 31])
    owner = npc['Exports'][30]
    set_value(owner, 'm_MapUnitId', MAP_ID)
    set_value(owner, 'm_VisiblFlagCondition', f'{{item:{unit["id"]}}}==0')
    set_value(owner, 'm_Direction', 'South')
    npc_grant(owner, unit)
    # Keep the complete original NPC/component graph and its opaque head-widget
    # export at the same indices. Do not copy/remap unknown widget bytes.
    for name, template_name, value in [('m_IsAnimationUseDirection', 'm_IsAnimationUseDirection', False),
                                       ('m_AnimationName', 'm_AnimationName', 'idle')]:
        donor = npc['Exports'][32] if value is False else npc['Exports'][31]
        prop = copy.deepcopy(property_data(donor, template_name)); prop['Value'] = value; prop['IsZero'] = False
        owner['Data'] = [p for p in owner['Data'] if p['Name'] != name] + [prop]
    operation = npc['Exports'][54]
    prop = copy.deepcopy(property_data(npc['Exports'][56], 'm_IsAnimationUseDirection'))
    operation['Data'].append(prop)
    prop = copy.deepcopy(property_data(npc['Exports'][63], 'UUPerPixel'))
    prop['Name'] = 'm_SsPlayerScale'; prop['Value'] = FINA_SCALE; prop['IsZero'] = False
    owner['Data'].append(prop)
    ss = npc['Exports'][63]
    set_value(ss, 'AutoPlayAnimPackName', f'summon{unit["id"]}')
    set_value(ss, 'AutoPlayAnimationName', 'idle'); set_value(ss, 'AutoPlayAnimationIndex', 0)
    set_value(ss, 'UUPerPixel', FINA_SCALE)
    for imp in npc['Imports']:
        if imp['ObjectName'] == '/Game/Chara/Field_Unit/npc9020/npc9020':
            imp['ObjectName'] = f'/Game/Chara/summon/summon{unit["id"]}/summon{unit["id"]}'
        elif imp['ObjectName'] == 'npc9020' and imp['ClassName'] == 'Ss6Project':
            imp['ObjectName'] = f'summon{unit["id"]}'
    # Idle NPCs normally skip movement physics without a controller. Enable
    # gravity/floor checks so the capsule and its attached interaction volumes
    # settle together on the actual platform instead of an assumed height.
    settle_fina(npc, spawn)
    # Only the sprite floats above the capsule's grounded foot.
    billboard = npc['Exports'][48]
    template = copy.deepcopy(property_data(npc['Exports'][109], 'RelativeLocation'))
    billboard['Data'].append(template); vector(billboard, 'RelativeLocation', (0.0, 0.0, FINA_FLOAT))
    names(npc, [owner, ss, npc['Imports']])
    acquisition_interaction(npc, source[DONOR_GD],
                            export(source[TRANSITION_GD], 'BP_MapTransitionTrigger_C_0')[1], unit)

    room = private_level(source[ROOM], '/Game/' + ROOM, '/Game/' + PACKAGE + '_PL')
    bg_path = property_data(room['Exports'][2], 'WorldAsset')['Value']['AssetPath']
    bg_path.update(PackageName='/Game/' + PACKAGE + '_BG', AssetName=NAME + '_BG')
    world_idx, world = export(room, NAME + '_PL')
    extra = base64.b64decode(world['Extras'])
    if extra != struct.pack('<5i', 2, 0, 2, 3, 4):
        raise ValueError('The native shrine streaming-level layout changed.')
    streams = []
    for suffix in ('GD', 'NPC'):
        stream = copy.deepcopy(room['Exports'][2]); idx = len(room['Exports']) + 1
        stream['ObjectName'] = 'LevelStreamingDynamic_Studio_' + suffix
        prop = property_data(stream, 'WorldAsset')
        prop['Value']['AssetPath']['PackageName'] = '/Game/' + PACKAGE + '_' + suffix
        prop['Value']['AssetPath']['AssetName'] = NAME + '_' + suffix
        room['Exports'].append(stream); room['DependsMap'].append(copy.deepcopy(room['DependsMap'][2]))
        world['CreateBeforeSerializationDependencies'].append(idx); streams.append(idx)
    world['Extras'] = base64.b64encode(struct.pack('<7i', 2, 0, 4, 3, 4, *streams)).decode()
    names(room, room['Exports'])

    stone_gd = private_level(source[DONOR_GD], '/Game/' + DONOR_GD, '/Game/' + PACKAGE + '_Stone_GD')
    transition(export(stone_gd, 'BP_MapTransitionTrigger_C_1')[1],
               export(source[TRANSITION_GD], 'BP_MapTransitionTrigger_C_0')[1], 1000, MAP_ID, auto=False)
    actors(stone_gd, [7, 0, 5, 4])
    level_id, stone_level = export(stone_gd, 'PersistentLevel')
    world_id = export(stone_gd, NAME + '_Stone_GD')[0]
    m = clone_graph(stone_gd, source[DONOR_GD], [2, 5], {8: level_id, 14: world_id})
    portal = stone_gd['Exports'][m[5]-1]
    portal['ObjectName'] = NAME + '_Portal'
    transition(portal, export(source[TRANSITION_GD], 'BP_MapTransitionTrigger_C_0')[1], MAP_ID, 0, auto=False)
    # Keep the donor's native Transition interaction type, requiring input
    # instead of entering the room on overlap.
    set_value(portal, 'm_UniqueId', MAP_ID)
    vector(stone_gd['Exports'][m[2]-1], 'RelativeLocation', PORTAL)
    vector(stone_gd['Exports'][m[2]-1], 'BoxExtent', (160.0, 200.0, 200.0))
    # The native crystal mesh marks the portal. Its materials remain game assets.
    actor_idx, mesh_idx = crystals['SM_Env_Com_magicstone001']
    b = clone_graph(stone_gd, source[ROOM_BG], [actor_idx, mesh_idx], {
        export(source[ROOM_BG], 'PersistentLevel')[0]: level_id,
        export(source[ROOM_BG], Path(ROOM_BG).name)[0]: world_id})
    stone_gd['Exports'][b[actor_idx]-1]['ObjectName'] = NAME + '_PortalCrystal'
    vector(stone_gd['Exports'][b[mesh_idx]-1], 'RelativeLocation', (PORTAL[0], PORTAL[1], 250.0))
    actors(stone_gd, stone_level['Actors'] + [m[5], b[actor_idx]])
    names(stone_gd, stone_gd['Exports'])

    stone_pl = private_level(source[STONE], '/Game/' + STONE, '/Game/' + PACKAGE + '_Stone_PL')
    _, stone_world = export(stone_pl, NAME + '_Stone_PL')
    old = base64.b64decode(stone_world['Extras'])
    if old != struct.pack('<12i', 2, 0, 9, 7, 4, 5, 6, 9, 10, 3, 8, 11):
        raise ValueError('The stone cave streaming layout changed.')
    # Retain native navigation, geometry and lighting; omit quest/event/battle levels.
    stone_world['Extras'] = base64.b64encode(struct.pack('<7i', 2, 0, 4, 3, 4, 9, 10)).decode()
    old_streams = set(range(3, 12)); keep = {3, 4, 9, 10}
    stone_world['CreateBeforeSerializationDependencies'] = [i for i in stone_world['CreateBeforeSerializationDependencies']
        if i not in old_streams or i in keep]
    gd_path = property_data(stone_pl['Exports'][3], 'WorldAsset')['Value']['AssetPath']
    gd_path.update(PackageName='/Game/' + PACKAGE + '_Stone_GD', AssetName=NAME + '_Stone_GD')
    stone_nav = stone_navigation(source[STONE_NAV])
    nav_path = property_data(stone_pl['Exports'][2], 'WorldAsset')['Value']['AssetPath']
    nav_path.update(PackageName='/Game/' + PACKAGE + '_Stone_NAV', AssetName=NAME + '_Stone_NAV')
    persistent_return_point(stone_pl, source[DONOR_GD], stone_nav)
    names(stone_pl, stone_pl['Exports'])

    wld = copy.deepcopy(source[WORLD]); level_id, level = export(wld, 'PersistentLevel')
    m = clone_graph(wld, source[DONOR_GD], [2, 5, 4, 12], {8: level_id, 14: len(source[WORLD]['Exports'])})
    entry = wld['Exports'][m[5] - 1]; point = wld['Exports'][m[4] - 1]
    entry['ObjectName'] = NAME + '_Entrance'; point['ObjectName'] = NAME + '_Return'
    transition(entry, export(source[TRANSITION_GD], 'BP_MapTransitionTrigger_C_0')[1], STONE_ID, 0, auto=False)
    set_value(entry, 'm_UniqueId', MAP_ID); set_value(point, 'm_PointID', MAP_ID)
    set_value(point, 'm_Direction', 'South')
    vector(wld['Exports'][m[2] - 1], 'RelativeLocation', ENTRANCE)
    vector(wld['Exports'][m[2] - 1], 'BoxExtent', (160.0, 250.0, 350.0))
    vector(wld['Exports'][m[12] - 1], 'RelativeLocation', RETURN)
    bg = source[WORLD_BG]
    mesh_index = next(i for i, e in enumerate(bg['Exports'], 1) if isinstance(e.get('Data'), list)
                      and any(p['Name'] == 'StaticMesh' and p['Value'] < 0
                              and bg['Imports'][-p['Value']-1]['ObjectName'] == 'SM_Env_Wld_00Com_dungeon001'
                              for p in e['Data']))
    mesh = bg['Exports'][mesh_index - 1]; actor_idx = mesh['OuterIndex']
    bg_level = export(bg, 'PersistentLevel')[0]
    bg_world = export(bg, Path(WORLD_BG).name)[0]
    world_id = export(wld, Path(WORLD).name)[0]
    b = clone_graph(wld, bg, [actor_idx, mesh_index], {bg_level: level_id, bg_world: world_id})
    cave = wld['Exports'][b[actor_idx] - 1]; cave['ObjectName'] = NAME + '_Model'
    cave_mesh = wld['Exports'][b[mesh_index] - 1]
    vector(cave_mesh, 'RelativeLocation', ENTRANCE_MODEL)
    scale = copy.deepcopy(property_data(clear_mesh, 'RelativeScale3D'))
    cave_mesh['Data'] = [p for p in cave_mesh['Data'] if p['Name'] != 'RelativeScale3D'] + [scale]
    vector(cave_mesh, 'RelativeScale3D', ENTRANCE_SCALE)
    actors(wld, level['Actors'] + [m[5], m[4], b[actor_idx]])
    world_pl = copy.deepcopy(source[WORLD_PL])
    add_collision_stream(world_pl, Path(WORLD_PL).name, source[WORLD_PL], PACKAGE + '_EntranceCollision')
    add_collision_stream(stone_pl, NAME + '_Stone_PL', source[WORLD_PL], PACKAGE + '_PortalCollision')
    entrance_collision = blocking_level(source[TRANSITION_GD], 'EntranceCollision', ENTRANCE, (90.0, 150.0, 350.0))
    portal_collision = blocking_level(source[TRANSITION_GD], 'PortalCollision', PORTAL, (85.0, 85.0, 300.0))
    for v in (gd, wld): names(v, v['Exports'])
    return {WORLD: wld, WORLD_PL: world_pl,
            PACKAGE + '_EntranceCollision': entrance_collision, PACKAGE + '_PortalCollision': portal_collision,
            PACKAGE + '_PL': room, PACKAGE + '_GD': gd, PACKAGE + '_NPC': npc,
            PACKAGE + '_BG': bg_room, PACKAGE + '_Stone_PL': stone_pl, PACKAGE + '_Stone_GD': stone_gd,
            PACKAGE + '_Stone_NAV': stone_nav}


def map_mappings(original, blueprints):
    """Append actual Blueprint declarations to a private copy of v4 mappings.

    UAssetAPI discovers these schemas on binary reads, but loses that context
    on JSON deserialization. Keep all native names, schemas and extensions;
    never modify the engine's installed Mappings.usmap or alias a BP to its CPP
    parent (which would lose the BP's own fields and shift property indices).
    """
    if (len(original) < 20 or original[:3] != b'\xc4\x30\x04' or struct.unpack_from('<i', original, 3)[0] != 0
            or original[7] != 0 or original[8:12] != original[12:16]
            or len(original) != 16 + struct.unpack_from('<I', original, 8)[0]):
        raise ValueError('Crystal cave needs uncompressed v4 game mappings; the original file was preserved.')
    payload = original[16:]; pos = 0
    def take(fmt):
        nonlocal pos
        value = struct.unpack_from('<' + fmt, payload, pos); pos += struct.calcsize('<' + fmt)
        return value[0] if len(value) == 1 else value
    count = take('i'); strings = []
    for _ in range(count):
        size = take('h')
        if size < 0 or pos + size > len(payload): raise ValueError('Invalid game mapping name.')
        strings.append(payload[pos:pos+size].decode('utf-8')); pos += size
    names_end = pos
    for _ in range(take('i')):
        take('i'); size = take('h'); pos += size * 12
    schemas_offset = pos; count = take('i'); schemas_start = pos; known = set()
    def skip_property():
        kind = take('B')
        if kind == 26: skip_property(); take('i')
        elif kind == 9: take('i')
        elif kind in (8, 25, 28): skip_property()
        elif kind == 24: skip_property(); skip_property()
        elif not 0 <= kind <= 30: raise ValueError('Unsupported game mapping property type.')
    for _ in range(count):
        name, parent, total, size = take('iiHH'); known.add(strings[name])
        for _ in range(size): take('HBi'); skip_property()
    schemas_end = pos
    # Current mappings use count-delimited CEXT extensions. A legacy MODL
    # extension implicitly iterates every schema and cannot be retained safely.
    if payload[schemas_end:] and payload[schemas_end:schemas_end+4] != b'CEXT':
        raise ValueError('Unsupported mapping extensions; original game mappings were preserved.')
    index = {s: i for i, s in enumerate(strings)}
    def name(value):
        if value not in index: index[value] = len(strings); strings.append(value)
        return index[value]
    def property_bytes(view, p):
        types = {'BoolProperty': 1, 'IntProperty': 2, 'FloatProperty': 3, 'ObjectProperty': 4,
                 'NameProperty': 5, 'DelegateProperty': 6, 'StrProperty': 10,
                 'TextProperty': 11, 'MulticastDelegateProperty': 13,
                 'MulticastInlineDelegateProperty': 13, 'MulticastSparseDelegateProperty': 13}
        kind = p['SerializedType']
        if kind == 'StructProperty':
            imp = view['Imports'][-p['Struct']-1]
            return bytes([9]) + struct.pack('<i', name(imp['ObjectName']))
        if kind not in types:
            raise ValueError('Unsupported cave Blueprint declaration: ' + kind)
        return bytes([types[kind]])
    added = []
    for key, (view, cl) in blueprints.items():
        if key in known: continue
        parent = view['Imports'][-cl['SuperStruct']-1]['ObjectName']; props = cl['LoadedProperties']
        schema = struct.pack('<iiHH', name(key), name(parent), len(props), len(props))
        for i, prop in enumerate(props):
            schema += struct.pack('<HBi', i, 1, name(prop['Name'])) + property_bytes(view, prop)
        added.append(schema)
    encoded = [s.encode('utf-8') for s in strings]
    if any(len(s) > 32767 for s in encoded): raise ValueError('Invalid Blueprint mapping name length.')
    name_bytes = struct.pack('<i', len(strings)) + b''.join(struct.pack('<h', len(s)) + s for s in encoded)
    result = (name_bytes + payload[names_end:schemas_offset] + struct.pack('<i', count + len(added))
              + payload[schemas_start:schemas_end] + b''.join(added) + payload[schemas_end:])
    return original[:8] + struct.pack('<II', len(result), len(result)) + result


def blueprint_mappings(views, env, work):
    root = Path(env['ROOT']); legacy = Path(env['LEGACY']); found = {}
    def collect(package, name):
        if name in found: return
        path = legacy / ('FFRS/Content/' + package.removeprefix('/Game/') + '.uasset')
        if not path.is_file():
            env['run'](env['ffrenv'].py(str(root / 'tools/extract_legacy.py'), '--filter', package.removeprefix('/Game/')))
        dump = work / (Path(package).name + '-schema.json')
        env['run'](env['FFRDT'] + ['tojson', str(path), str(dump), '--usmap', env['USMAP']])
        view = json.loads(dump.read_text(encoding='utf-8-sig')); _, cl = export(view, name)
        if 'ClassExport' not in cl['$type'] or cl['SuperStruct'] >= 0:
            raise ValueError('The cave Blueprint inheritance layout changed.')
        found[name] = (view, cl)
        parent = view['Imports'][-cl['SuperStruct']-1]
        if parent['ClassName'] == 'BlueprintGeneratedClass':
            collect(view['Imports'][-parent['OuterIndex']-1]['ObjectName'], parent['ObjectName'])
    for view in views.values():
        for e in view['Exports']:
            if 'ClassExport' in e['$type'] and e['SuperStruct'] < 0:
                found[e['ObjectName']] = (view, e)
            if 'NormalExport' not in e['$type'] or e['ClassIndex'] >= 0: continue
            cl = view['Imports'][-e['ClassIndex']-1]
            if cl['ClassName'] == 'BlueprintGeneratedClass':
                collect(view['Imports'][-cl['OuterIndex']-1]['ObjectName'], cl['ObjectName'])
    path = work / 'cave-mappings.usmap'
    path.write_bytes(map_mappings(Path(env['USMAP']).read_bytes(), found))
    return str(path)


def semantic(value):
    """Compare authored values, ignoring serialization order/default metadata."""
    if isinstance(value, dict):
        if 'Name' in value and 'Value' in value:
            return (value['Name'], value.get('ArrayIndex', 0), semantic(value['Value']))
        return {k: semantic(v) for k, v in value.items() if k != '$type'}
    if isinstance(value, list):
        result = [semantic(v) for v in value]
        if value and all(isinstance(v, dict) and 'Name' in v and 'Value' in v for v in value):
            return sorted(result, key=lambda p: (p[0], p[1]))
        return result
    return 0.0 if value in ('+0', '-0') else value


def check_level(expected, built):
    if (built['NameMap'] != expected['NameMap']
            or built['NamesReferencedFromExportDataCount'] != expected['NamesReferencedFromExportDataCount']
            or built['NamesReferencedFromExportDataCount'] < len(built['NameMap'])):
        raise ValueError('A generated cave level would lose names during IoStore packing.')
    if expected['Imports'] != built['Imports'] or len(expected['Exports']) != len(built['Exports']):
        raise ValueError('A generated cave level lost its imports or exports.')
    for a, b in zip(expected['Exports'], built['Exports']):
        for key in ('ObjectName', 'OuterIndex', 'ClassIndex', 'SuperIndex', 'TemplateIndex', 'Extras', 'Actors',
                    'ScriptBytecodeRaw'):
            if a.get(key) != b.get(key): raise ValueError('Cave level reference changed: ' + key)
        if semantic(a.get('Data')) != semantic(b.get('Data')):
            raise ValueError('Cave level properties changed: ' + a['ObjectName'])


def build(units, env):
    import _ffr_testing as testing
    if not testing.settings(env['ROOT'])['crystalCave']: return
    unit = target(units); root = Path(env['ROOT']); legacy = Path(env['LEGACY'])
    work = root / 'build/crystal-cave'; work.mkdir(parents=True, exist_ok=True)
    # Binary decoding needs the native Blueprint parents as well as the levels.
    if not (legacy / 'FFRS/Content/BP/Map/Unit/BP_MapUnit_NPC_Field.uasset').is_file():
        env['run'](env['ffrenv'].py(str(root / 'tools/extract_legacy.py'), '--filter', 'BP/Map/'))
    source = {}
    for rel in (WORLD, WORLD_PL, ROOM, ROOM_BG, STONE, STONE_NAV, DONOR_GD, WORLD_BG, TRANSITION_GD, GRANT_DONOR):
        suffix = '.uasset' if rel == GRANT_DONOR else '.umap'
        path = legacy / ('FFRS/Content/' + rel + suffix)
        if not path.is_file():
            env['run'](env['ffrenv'].py(str(root / 'tools/extract_legacy.py'), '--filter', rel))
        dump = work / (Path(rel).name + '-original.json')
        env['run'](env['FFRDT'] + ['tojson', str(path), str(dump), '--usmap', env['USMAP']])
        source[rel] = json.loads(dump.read_text(encoding='utf-8-sig'))
    expected = make_levels(source, unit)
    expected[GRANT_SEQUENCE] = grant_sequence(source[GRANT_DONOR])
    mapping = blueprint_mappings(expected, env, work)
    for rel, view in expected.items():
        names(view, view['Exports'])
        dump = work / (Path(rel).name + '-built.json'); dump.write_text(json.dumps(view), encoding='utf-8')
        suffix = '.uasset' if rel == GRANT_SEQUENCE else '.umap'
        destination = Path(env['OUT']) / ('FFRS/Content/' + rel + suffix)
        destination.parent.mkdir(parents=True, exist_ok=True)
        env['run'](env['FFRDT'] + ['fromjson', str(dump), str(destination), '--usmap', mapping])
        decoded = work / (Path(rel).name + '-verified.json')
        env['run'](env['FFRDT'] + ['tojson', str(destination), str(decoded), '--usmap', mapping])
        check_level(view, json.loads(decoded.read_text(encoding='utf-8-sig')))
    print('  Crystal Fina cave: event-only grant; cave return point 1 in persistent level; private navigation links; button-confirmed cave exit.')
