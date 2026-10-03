"""Cave acquisition, original-story preservation and cooked asset safeguards."""
import copy
import json
from pathlib import Path
import struct
import sys
import tempfile
import unittest

from test_existing_visions import module, ROOT
from test_native_testing import game, testing

cave = module('_ffr_crystal_cave', ROOT / 'assets/existing_visions/payload/_ffr_crystal_cave.py')
sys.modules['_ffr_crystal_cave'] = cave


def cave_game():
    tables, _, _ = game()
    for row in tables[testing.COMPOSITE].values():
        row['FooterSettings'] = {'IsApplyProgressis': False}
        row['TransitionLocation'] = {'mapId': -1, 'pointId': -1, 'bDoAutoSave': False}
        row['IsOpenDialogByFinishEvent'] = False
    tables[testing.EVENT] = {'C01_014_03': copy.deepcopy(tables[testing.COMPOSITE]['C01_014_03'])}
    room = {'ID': 10020, 'Level': '/Game/' + cave.ROOM, 'Name': 'Original shrine',
            'MapType': 'VisionSmallShrine', 'startupEventList': [], 'doMovementEncount': False}
    tables[cave.MAP] = {'00Com_217': room, '01Gra_44': {
        'ID': 10001, 'Level': '/Game/' + cave.STONE, 'Name': 'Original cave',
        'startupEventList': [], 'doMovementEncount': False}}
    tables[cave.COMPOSITE] = copy.deepcopy(tables[cave.MAP])
    tables[cave.MAP_UNIT] = {'Shopkeeper': {'ID': 9020, 'Footstep': 'NPC01', 'animationAssetList': [{
        'Ss6Project': 'original sprite', 'Material': 'original material', 'isVisionCharacter': False,
        'textureBaseColor': 'original texture', 'textureNormal': 'original normal',
        'textureMetallicRoughness': 'original mreo'}]}}
    tables[cave.PLACEMENT] = {'Original shrine': {'mapId': 10020, 'npcTable': 'original NPC list'}}
    unit = {'id': 13507, 'ffbe': {'id': cave.SPRITE}, 'en': 'Crystal Fina'}
    return tables, lambda rel: copy.deepcopy(tables[rel]), unit


def enabled(root):
    p = Path(root) / testing.CONFIG
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps({'schema': 1, 'maxMr': False, 'crystalCave': True}))


class CrystalCaveTests(unittest.TestCase):
    def test_disabled_cave_needs_no_model_assets_or_game_tables(self):
        with tempfile.TemporaryDirectory() as root:
            original = {'old': {'kept': True}}
            cave.prepare(original, [], root, lambda _: self.fail('disabled cave read game data'))
            cave.build([], {'ROOT': root})
            self.assertEqual(original, {'old': {'kept': True}})

    def test_grant_is_once_only_uses_allocated_profile_and_preserves_native_scene(self):
        original, rows, unit = cave_game(); before = copy.deepcopy(original)
        with tempfile.TemporaryDirectory() as root:
            enabled(root)
            operations = testing.prepare({}, [unit], root, rows)
        self.assertEqual(original, before)
        self.assertEqual(set(operations), {cave.MAP, cave.COMPOSITE, cave.MAP_UNIT, cave.PLACEMENT,
                                           testing.EVENT, testing.COMPOSITE})
        for rel, op in operations.items():
            self.assertEqual(op['set'], [])
            built = copy.deepcopy(original[rel])
            for added in op['add']:
                built[added['row']] = testing.apply_fields(original[rel][added['cloneFrom']], added['set'])
            testing.check_rows(original[rel], built, op)
            if rel in (testing.EVENT, testing.COMPOSITE):
                event = built[cave.EVENT]
                self.assertEqual(event['ObtainItemList'], [{'Condition': '{item:13507}==0', 'ID': 13507,
                                                          'Num': 1, 'Text': ''}])
                for field in ('OnFlagList', 'OffFlagList', 'FlagList', 'ProgressList',
                              'ContinuousEventList', 'InitUnitDataList'):
                    self.assertEqual(event[field], [])
                self.assertEqual(event['EventSequence'], 'None')
                self.assertEqual(event['encountGroupId'], -1)
                self.assertFalse(event['IsSetAutoSave']); self.assertFalse(event['IsForceAutoSave'])
                self.assertTrue(event['FooterSettings']['IsApplyProgressis'])
                self.assertTrue(event['IsOpenDialogByFinishEvent'])
                self.assertEqual(event['LoadingScreenSetting'], 'White')
                self.assertEqual(event['TransitionLocation'], {'mapId': 29990, 'pointId': 1, 'bDoAutoSave': False})
            elif rel == cave.MAP_UNIT:
                sprite = built[cave.NAME]['animationAssetList'][0]
                self.assertIn('summon13507', sprite['Ss6Project'])
                self.assertTrue(sprite['Material'].endswith('_13507'))
            elif rel == cave.MAP:
                self.assertEqual(built[cave.NAME]['ID'], 29991)
                self.assertEqual(built[cave.NAME]['Level'], '/Game/' + cave.PACKAGE + '_PL')

    def test_conflicting_game_ids_or_wrong_room_are_rejected(self):
        for change in ('map', 'npc', 'placement', 'room'):
            with self.subTest(change=change), tempfile.TemporaryDirectory() as root:
                original, rows, unit = cave_game(); enabled(root)
                if change == 'map': original[cave.COMPOSITE]['collision'] = {'ID': cave.MAP_ID}
                if change == 'npc': original[cave.MAP_UNIT]['collision'] = {'ID': cave.MAP_ID}
                if change == 'placement': original[cave.PLACEMENT]['collision'] = {'mapId': cave.MAP_ID}
                if change == 'room': original[cave.MAP]['00Com_217']['Level'] = '/Game/another-map'
                with self.assertRaises(ValueError): cave.prepare({}, [unit], root, rows)
        _, _, unit = cave_game()
        for units in ([], [unit, unit], [dict(unit, native={'id': 13507})], [dict(unit, party={'id': 13507})]):
            with self.assertRaises(ValueError): cave.target(units)

    def test_room_cleanup_removes_crystal_glows_but_keeps_fog_and_lighting(self):
        assets = ['SM_Env_Com_magicstone001', 'SM_Env_Com_magicstone002',
                  'NS_EF_BG_00Common_Glow_001', 'NS_EF_BG_00Common_Glow_001',
                  'NS_EF_BG_00Common_FogGroundBTL002_001', 'NS_EF_BG_GodRay001_001']
        view = {'Imports': [{'ObjectName': name} for name in assets],
                'Exports': [{'ObjectName': 'PersistentLevel', 'OuterIndex': 20,
                    'Actors': [0, 2, 3, 4, 5, 6, 7],
                    'CreateBeforeSerializationDependencies': [2, 3, 4, 5, 6, 7, 0]}]}
        view['Exports'] += [{'ObjectName': 'actor' + str(i), 'OuterIndex': 1, 'Data': []}
                            for i in range(2, 8)]
        view['Exports'] += [{'ObjectName': 'component' + str(i), 'OuterIndex': i + 2,
            'Data': [{'Name': 'StaticMesh' if i < 2 else 'Asset', 'Value': -(i + 1)}],
            'Extras': 'retained opaque component data'} for i in range(6)]
        before = copy.deepcopy(view)
        crystals = cave.clear_crystals(view)
        self.assertEqual(crystals['SM_Env_Com_magicstone001'], (2, 8))
        self.assertEqual(view['Exports'][0]['Actors'], [0, 6, 7])
        self.assertEqual(view['Exports'][0]['CreateBeforeSerializationDependencies'], [6, 7, 0])
        self.assertEqual(view['Exports'][1:], before['Exports'][1:])
        self.assertEqual(view['Imports'], before['Imports'])
        changed = copy.deepcopy(before); changed['Imports'][2]['ObjectName'] = 'new glow effect'
        with self.assertRaises(ValueError): cave.clear_crystals(changed)
        self.assertEqual(changed['Exports'], before['Exports'])

    def test_private_blueprint_mapping_retains_native_schema_and_property_indices(self):
        names = ['CPP_Parent']
        name_bytes = struct.pack('<i', 1) + struct.pack('<h', len(names[0])) + names[0].encode()
        native_schema = struct.pack('<iiHH', 0, -1, 0, 0)
        payload = name_bytes + struct.pack('<ii', 0, 1) + native_schema + b'CEXT' + struct.pack('<i', 0)
        header = b'\xc4\x30\x04' + struct.pack('<iBII', 0, 0, len(payload), len(payload))
        view = {'Imports': [{'ObjectName': 'CPP_Parent'}, {'ObjectName': 'PointerToUberGraphFrame'}]}
        cl = {'SuperStruct': -1, 'LoadedProperties': [
            {'Name': 'UberGraphFrame', 'SerializedType': 'StructProperty', 'Struct': -2},
            {'Name': 'InitializeOnce', 'SerializedType': 'BoolProperty'}]}
        source = header + payload
        mapped = cave.map_mappings(source, {'BP_Child_C': (view, cl)})
        self.assertEqual(mapped[:8], source[:8])
        self.assertEqual(struct.unpack_from('<II', mapped, 8), (len(mapped) - 16,) * 2)
        self.assertIn(native_schema, mapped)
        self.assertTrue(mapped.endswith(b'CEXT' + struct.pack('<i', 0)))
        self.assertIn(b'UberGraphFrame', mapped)
        self.assertIn(b'InitializeOnce', mapped)
        with self.assertRaises(ValueError): cave.map_mappings(b'bad', {})
        invalid = copy.deepcopy(cl); invalid['LoadedProperties'][0]['SerializedType'] = 'Unsupported'
        with self.assertRaises(ValueError): cave.map_mappings(source, {'BP_Child_C': (view, invalid)})

    def test_fina_spawn_centers_native_acquisition_lights_not_mesh_origins(self):
        def location(x, y, z):
            return {'Name': 'RelativeLocation', 'Value': [{'Value': {'X': x, 'Y': y, 'Z': z}}]}
        crystal = {'Data': [location(100, 200, 532)]}
        view = {'Imports': [{'ObjectName': 'SM_Env_Com_00Com_44_ground001'},
                            {'ObjectName': 'PointLightComponent'},
                            {'ObjectName': 'SM_Env_Com_magicstone002'}], 'Exports': [
            {'ClassIndex': 0, 'Data': [{'Name': 'StaticMesh', 'Value': -1}, location(0, 0, '+0')]},
            {'ClassIndex': -2, 'Data': [location(110, 210, 342)]},
            {'ClassIndex': -2, 'Data': [location(120, 520, 340)]},
            {'ClassIndex': -2, 'Data': [location('+0', '+0', 0)]},
            {'ClassIndex': 0, 'Data': [{'Name': 'StaticMesh', 'Value': -3}, location(100, 500, 532)]}]}
        original = copy.deepcopy(view)
        self.assertEqual(cave.fina_spawn(view, crystal), (115, 365, 341))
        cave.vector(crystal, 'RelativeLocation', (100, 200, 900))
        self.assertEqual(cave.fina_spawn(view, crystal), (115, 365, 341))
        self.assertEqual(view, original)
        cave.vector(view['Exports'][0], 'RelativeLocation', (0, 0, -800))
        self.assertEqual(cave.fina_spawn(view, crystal), (115, 365, 341))
        for exports in (view['Exports'][1:], view['Exports'][:-1], view['Exports'][:1]):
            with self.assertRaises(ValueError): cave.fina_spawn(dict(view, Exports=exports), crystal)
        # Never silently reuse the same light for two crystal anchors.
        cave.vector(view['Exports'][-1], 'RelativeLocation', (100, 200, 532))
        with self.assertRaises(ValueError): cave.fina_spawn(view, crystal)

    def test_stationary_fina_settles_with_attached_interaction_and_preserves_other_movement_settings(self):
        def prop(name, value, kind, **extra):
            return dict(Name=name, Value=value, IsZero=False,
                        **{'$type': 'UAssetAPI.PropertyTypes.Objects.' + kind + ', UAssetAPI'}, **extra)
        def location(z):
            return prop('RelativeLocation', [{'Value': {'X': 0, 'Y': 0, 'Z': z}, 'IsZero': False}], 'StructPropertyData')
        view = {'NameMap': ['native'], 'Exports': [{'Data': []} for _ in range(119)]}
        view['Exports'][30]['Data'] = [prop('m_IsAnimationUseDirection', False, 'BoolPropertyData'),
            prop('m_Direction', 'South', 'EnumPropertyData', EnumType='eMapDirectionType', InnerType='ByteProperty')]
        view['Exports'][36]['Data'] = [location(33)]
        view['Exports'][42]['Data'] = [prop('bAlwaysCheckFloor', False, 'BoolPropertyData'),
            prop('WalkableFloorZ', 0.71, 'FloatPropertyData')]
        view['Exports'][63]['Data'] = [prop('UUPerPixel', 2.5, 'FloatPropertyData')]
        view['Exports'][109]['Data'] = [location(-33)]
        view['Exports'][11]['Data'] = [prop('AttachParent', 37, 'ObjectPropertyData')]
        before = copy.deepcopy(view)
        cave.settle_fina(view, (110, 210, 342))
        root = cave.property_data(view['Exports'][36], 'RelativeLocation')['Value'][0]['Value']
        self.assertEqual(root, {'X': 110, 'Y': 210, 'Z': 375})
        movement = view['Exports'][42]
        for name in ('bRunPhysicsWithNoController', 'bAlwaysCheckFloor'):
            self.assertIs(cave.property_data(movement, name)['Value'], True)
        self.assertEqual(cave.property_data(movement, 'GravityScale')['Value'], 1.0)
        for name, value in [('MovementMode', 'MOVE_Falling'), ('DefaultLandMovementMode', 'MOVE_Walking')]:
            p = cave.property_data(movement, name)
            self.assertEqual((p['EnumType'], p['InnerType'], p['Value']), ('EMovementMode', 'ByteProperty', value))
        self.assertEqual(cave.property_data(movement, 'WalkableFloorZ')['Value'], 0.71)
        for i in (11, 30, 63, 109): self.assertEqual(view['Exports'][i], before['Exports'][i])
        self.assertTrue({'MOVE_Falling', 'MOVE_Walking', 'bRunPhysicsWithNoController'} <= set(view['NameMap']))
        settled = copy.deepcopy(view)
        cave.settle_fina(view, (110, 210, 342))
        self.assertEqual(view, settled)

    def test_manual_portal_preserves_destination_and_transition_safeguards(self):
        actor = {'Data': [{'Name': 'm_MapId', 'Value': 1000}, {'Name': 'm_PointID', 'Value': 0}]}
        fields = [('FlagCondition', 'story flag'), ('mapId', 3000), ('pointId', 4),
                  ('isEnableAutoSave', True), ('EventList', ['story event']),
                  ('eventList2', ['another event']), ('afterTransitionEventList', ['tutorial'])]
        template = {'Data': [{'Name': 'm_IsAutoTransition', 'Value': True, 'IsZero': False},
                            {'Name': 'm_IsUseCondion', 'Value': True},
                            {'Name': 'mTransitionDataList', 'Value': [{'Name': 'entry', 'Value': [
                                {'Name': k, 'Value': v} for k, v in fields]}]}]}
        auto = copy.deepcopy(actor)
        cave.transition(auto, template, 29990, 1)
        cave.transition(actor, template, 29991, 0, auto=False)
        self.assertTrue(cave.property_data(auto, 'm_IsAutoTransition')['Value'])
        manual = cave.property_data(actor, 'm_IsAutoTransition')
        self.assertFalse(manual['Value']); self.assertFalse(manual['IsZero'])
        values = {p['Name']: p['Value'] for p in cave.named_properties(cave.property_data(actor, 'mTransitionDataList'))}
        self.assertEqual((values['mapId'], values['pointId']), (29991, 0))
        self.assertEqual(values['FlagCondition'], '')
        self.assertFalse(values['isEnableAutoSave'])
        for name in ('EventList', 'eventList2', 'afterTransitionEventList'):
            self.assertEqual(values[name], [])
        self.assertTrue(cave.property_data(template, 'm_IsAutoTransition')['Value'])

    def test_portal_blocker_is_inside_interaction_area_without_transition_callbacks(self):
        def location(name, xyz):
            return {'Name': name, 'Value': [{'Value': dict(zip(('X','Y','Z'), xyz)), 'IsZero': False}],
                    'StructType': 'Vector', 'SerializeNone': True, 'IsZero': False}
        def obj(name, value):
            return {'Name': name, 'Value': value, '$type': 'UAssetAPI.PropertyTypes.Objects.ObjectPropertyData, UAssetAPI'}
        donor = {'Imports': [{'ObjectName': '/Script/Engine', 'OuterIndex': 0},
                            {'ObjectName': 'BoxComponent', 'OuterIndex': -1},
                            {'ObjectName': 'CPP_MapTransitionTrigger', 'OuterIndex': -1}],
                 'Exports': [], 'DependsMap': [[] for _ in range(14)]}
        for i in range(14):
            donor['Exports'].append({'$type': 'UAssetAPI.ExportTypes.NormalExport, UAssetAPI',
                'ObjectName': str(i), 'ClassIndex': 0, 'OuterIndex': 8, 'SuperIndex': 0, 'TemplateIndex': 0,
                'SerializationBeforeSerializationDependencies': [], 'CreateBeforeSerializationDependencies': [],
                'SerializationBeforeCreateDependencies': [], 'CreateBeforeCreateDependencies': [], 'Data': []})
        donor['Exports'][4].update(ClassIndex=-3, Data=[obj('RootComponent',2), {'Name':'m_MapId','Value':1000}])
        donor['Exports'][1].update(ClassIndex=-2, OuterIndex=5, Data=[
            location('RelativeLocation',(0,0,0)),location('BoxExtent',(160,200,200)),
            {'Name':'OnComponentBeginOverlap','Value':[{'Object':5,'Delegate':'OnBeginOverlap'}]}])
        view = {'Imports': [], 'Exports': [], 'DependsMap': [], 'NameMap': []}
        before = copy.deepcopy(donor)
        # A serialized instance must not inherit its donor's overlap-only archetype.
        donor['Exports'][1]['TemplateIndex'] = -3
        donor['Exports'][1]['SerializationBeforeSerializationDependencies'] = [-3]
        donor['Exports'][1]['SerializationBeforeCreateDependencies'] = [-3]
        donor['Exports'][1]['ObjectFlags'] = 'RF_Transactional, RF_DefaultSubObject'
        before = copy.deepcopy(donor)
        actor_id = cave.blocking_box(view, donor, 0, 0, 'PortalCollision',
                                     (4000, 31, 0), (85, 85, 300))
        owner = view['Exports'][actor_id-1]; root = cave.property_data(owner,'RootComponent')['Value']
        box = view['Exports'][root-1]
        self.assertEqual(view['Imports'][-owner['ClassIndex']-1]['ObjectName'], 'Actor')
        self.assertTrue(cave.property_data(owner, 'bActorEnableCollision')['Value'])
        self.assertEqual(cave.property_data(owner, 'InstanceComponents')['Value'][0]['Value'], root)
        self.assertEqual(box['TemplateIndex'], 0)
        self.assertEqual(box['SerializationBeforeSerializationDependencies'], [])
        self.assertEqual(box['SerializationBeforeCreateDependencies'], [box['ClassIndex']])
        self.assertNotIn('RF_DefaultSubObject', box['ObjectFlags'])
        self.assertEqual(cave.property_data(box, 'CreationMethod')['Value'], 'Instance')
        self.assertFalse(any(p['Name'].startswith('OnComponent') for p in box['Data']))
        body = {p['Name']:p['Value'] for p in cave.property_data(box,'BodyInstance')['Value']}
        self.assertEqual(body, {'CollisionProfileName':'BlockAll','CollisionEnabled':'QueryAndPhysics',
                                'ObjectType':'ECC_WorldStatic'})
        self.assertFalse(cave.property_data(box,'bGenerateOverlapEvents')['Value'])
        extent = cave.property_data(box,'BoxExtent')['Value'][0]['Value']
        self.assertLess(extent['X'] + 18.666666, 160); self.assertLess(extent['Y'] + 18.666666, 200)
        center = cave.property_data(box, 'RelativeLocation')['Value'][0]['Value']
        self.assertLess(center['Z'] - extent['Z'], 0)
        self.assertGreater(center['Z'] + extent['Z'], 2 * 33.333332)
        self.assertEqual(donor, before)

    def test_event_only_acquisition_uses_manual_input_and_follows_grounded_capsule(self):
        from unittest.mock import patch
        def prop(name, value): return {'Name': name, 'Value': value, 'IsZero': False}
        event = {'StructType': 'TalkEventPlayData', 'Name': '0', 'Value': [
            prop('Condition', '!{flag:1170}'), prop('EventId', 'Tutorial_Party')]}
        entry = {'Name': '0', 'Value': [prop('FlagCondition', ''), prop('isEventOnly', False),
            prop('mapId', 3000), prop('pointId', 0), prop('isEnableAutoSave', True),
            prop('EventList', []), prop('eventList2', []), prop('afterTransitionEventList', [event])]}
        template = {'Data': [prop('m_IsAutoTransition', True), prop('m_IsUseCondion', True),
                            prop('mTransitionDataList', [entry])]}
        actor = {'Data': [prop('RootComponent', 4), prop('m_MapId', 1000), prop('m_PointID', 0),
                          prop('m_UniqueId', 0), prop('m_MapInteractType', 'Transition')]}
        def vector(name): return prop(name, [{'Value': {'X': 0, 'Y': 0, 'Z': 300}, 'IsZero': False}])
        box = {'Data': [vector('RelativeLocation'), vector('BoxExtent')],
               'CreateBeforeSerializationDependencies': []}
        npc = {'NameMap': [], 'Exports': [
            {'ObjectName': 'PersistentLevel', 'Actors': [0], 'OuterIndex': 2,
             'CreateBeforeSerializationDependencies': []},
            {'ObjectName': cave.NAME + '_NPC', 'OuterIndex': 0},
            dict(actor, ObjectName='donor', OuterIndex=1), dict(box, ObjectName='root', OuterIndex=3)]}
        before = copy.deepcopy(template)
        with patch.object(cave, 'clone_graph', return_value={5: 3, 2: 4}):
            cave.acquisition_interaction(npc, {}, template, {'id': 13507})
        actor = npc['Exports'][2]
        self.assertFalse(cave.property_data(actor, 'm_IsAutoTransition')['Value'])
        actual, = cave.property_data(actor, 'mTransitionDataList')['Value']
        self.assertTrue(cave.property_data(actual, 'isEventOnly')['Value'])
        self.assertEqual(cave.property_data(actual, 'FlagCondition')['Value'], '{item:13507}==0')
        scheduled, = cave.property_data(actual, 'EventList')['Value']
        self.assertEqual(scheduled['StructType'], 'TalkEventPlayData')
        self.assertEqual(cave.property_data(scheduled, 'EventId')['Value'], cave.EVENT)
        self.assertEqual(cave.property_data(scheduled, 'Condition')['Value'], '{item:13507}==0')
        self.assertEqual(cave.property_data(actual, 'afterTransitionEventList')['Value'], [])
        self.assertFalse(cave.property_data(actual, 'isEnableAutoSave')['Value'])
        self.assertEqual(cave.property_data(box, 'AttachParent')['Value'], 37)
        self.assertEqual(cave.property_data(box, 'RelativeLocation')['Value'][0]['Value'], {'X': 0, 'Y': 0, 'Z': 0})
        self.assertIn(37, box['CreateBeforeSerializationDependencies'])
        self.assertEqual(npc['Exports'][0]['Actors'], [0, 3])
        self.assertEqual(template, before)

    def test_appended_overlap_delegate_names_survive_iostore_name_map_trimming(self):
        view = {'NameMap': ['original', 'RootBoxComponent'], 'NamesReferencedFromExportDataCount': 2}
        original_names = view['NameMap'][:]
        delegate = {'$type': 'UAssetAPI.PropertyTypes.Objects.FDelegate, UAssetAPI',
                    'Object': 139, 'Delegate': 'OnBeginOverlap'}
        cave.names(view, delegate)
        # retoc copies exactly this prefix into the cooked container, leaving
        # property payload indices unchanged. The old header lost this name.
        packed_names = view['NameMap'][:view['NamesReferencedFromExportDataCount']]
        self.assertEqual(packed_names[view['NameMap'].index(delegate['Delegate'])], 'OnBeginOverlap')
        self.assertEqual(view['NameMap'][:len(original_names)], original_names)
        cave.names(view, delegate)
        self.assertEqual(view['NameMap'], packed_names)

    def test_level_readback_rejects_lost_actor_reference_opaque_bytes_and_names(self):
        expected = {'NameMap': ['actor'], 'NamesReferencedFromExportDataCount': 1,
                    'Imports': [], 'Exports': [{'ObjectName': 'actor', 'OuterIndex': 2,
            'Extras': 'opaque', 'Data': [{'Name': 'm_MapId', 'Value': 29991}]}]}
        cave.check_level(expected, copy.deepcopy(expected))
        for field, value in [('OuterIndex', 0), ('Extras', 'corrupted'),
                             ('Data', [{'Name': 'm_MapId', 'Value': 1000}])]:
            broken = copy.deepcopy(expected); broken['Exports'][0][field] = value
            with self.assertRaises(ValueError): cave.check_level(expected, broken)
        for field, value in [('NameMap', ['renamed']), ('NamesReferencedFromExportDataCount', 0)]:
            broken = copy.deepcopy(expected); broken[field] = value
            with self.assertRaisesRegex(ValueError, 'lose names'): cave.check_level(expected, broken)


if __name__ == '__main__': unittest.main()
