"""Cave acquisition, original-story preservation and cooked asset safeguards."""
import base64
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
                self.assertEqual(event['EventSequence'], '/Game/' + cave.GRANT_SEQUENCE)
                self.assertEqual(event['encountGroupId'], -1)
                self.assertFalse(event['IsSetAutoSave']); self.assertFalse(event['IsForceAutoSave'])
                self.assertFalse(event['FooterSettings']['IsApplyProgressis'])
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

    def test_grant_and_sprite_follow_allocated_vision_id(self):
        original, rows, unit = cave_game(); unit['id'] = 13531
        with tempfile.TemporaryDirectory() as root:
            enabled(root)
            operations = testing.prepare({}, [unit], root, rows)
        for rel in (testing.EVENT, testing.COMPOSITE):
            added, = [a for a in operations[rel]['add'] if a['row'] == cave.EVENT]
            event = testing.apply_fields(original[rel][added['cloneFrom']], added['set'])
            self.assertEqual(event['ObtainItemList'], [{'Condition': '{item:13531}==0',
                              'ID': 13531, 'Num': 1, 'Text': ''}])
            self.assertEqual(event['EventSequence'], '/Game/' + cave.GRANT_SEQUENCE)
            self.assertFalse(event['FooterSettings']['IsApplyProgressis'])
        added, = operations[cave.MAP_UNIT]['add']
        sprite = testing.apply_fields(original[cave.MAP_UNIT][added['cloneFrom']], added['set'])
        self.assertIn('summon13531', sprite['animationAssetList'][0]['Ss6Project'])

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
        self.assertEqual(cave.fina_spawn(view, crystal), (115, 365 + cave.FINA_ALIGNMENT_Y, 341))
        cave.vector(crystal, 'RelativeLocation', (100, 200, 900))
        self.assertEqual(cave.fina_spawn(view, crystal), (115, 365 + cave.FINA_ALIGNMENT_Y, 341))
        self.assertEqual(view, original)
        cave.vector(view['Exports'][0], 'RelativeLocation', (0, 0, -800))
        self.assertEqual(cave.fina_spawn(view, crystal), (115, 365 + cave.FINA_ALIGNMENT_Y, 341))
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

    def test_native_blocker_preserves_cooked_physics_and_selects_only_volume(self):
        def prop(name, value): return {'Name': name, 'Value': value, 'IsZero': False}
        def vector(name, xyz): return prop(name, [{'Value': dict(zip(('X', 'Y', 'Z'), xyz))}])
        donor = {'NameMap': ['native'], 'Exports': [
            {'ObjectName': str(i), 'OuterIndex': 66, 'Data': [], 'Extras': 'opaque',
             'CreateBeforeSerializationDependencies': []} for i in range(70)]}
        owner, body, root, settings, level, model = [donor['Exports'][i-1] for i in (1, 2, 64, 65, 66, 69)]
        owner.update(ObjectName='BlockingVolume_1', Data=[prop('RootComponent', 64), prop('Brush', 69)])
        bounds = prop('ElemBox', [{'Value': {'Min': dict(X=-375, Y=-100, Z=-300),
                                           'Max': dict(X=375, Y=100, Z=300)}}])
        body.update(ObjectName='BodySetup_0', Data=[prop('AggGeom', [
            prop('ConvexElems', [prop('0', [bounds, prop('VertexData', ['native convex'])])])]),
            prop('CollisionTraceFlag', 'CTF_UseSimpleAsComplex')], Extras='native Chaos')
        root.update(ObjectName='BrushComponent0', TemplateIndex=-26, Data=[prop('BrushBodySetup', 2),
            vector('RelativeLocation', (-3825, 1000, 100))])
        settings['ObjectName'] = 'CPP_MuchaWorldSetting'
        level.update(ObjectName='PersistentLevel', OuterIndex=70, Actors=[65, 0, 1, 3],
                     CreateBeforeSerializationDependencies=[65, 1, 3, 69])
        model.update(ObjectName='Model_1', Extras='native model')
        donor['Exports'][69].update(ObjectName='Dng_01Gra_43_GD', OuterIndex=0)
        before = copy.deepcopy(donor)
        built = cave.blocking_level(donor, 'PortalCollision', cave.PORTAL, (85, 85, 300))
        self.assertEqual(built['Exports'][65]['Actors'], [65, 0, 1])
        self.assertNotIn(3, built['Exports'][65]['CreateBeforeSerializationDependencies'])
        self.assertEqual(built['Exports'][1], before['Exports'][1])
        self.assertEqual(built['Exports'][68], before['Exports'][68])
        root = built['Exports'][63]
        self.assertEqual(root['TemplateIndex'], -26)
        self.assertEqual(cave.property_data(root, 'RelativeLocation')['Value'][0]['Value'],
                         dict(zip(('X', 'Y', 'Z'), cave.PORTAL)))
        self.assertEqual(cave.property_data(root, 'RelativeScale3D')['Value'][0]['Value'],
                         dict(X=85/375, Y=.85, Z=1))
        self.assertEqual(donor, before)
        cave.property_data(body, 'CollisionTraceFlag')['Value'] = 'CTF_UseComplexAsSimple'
        with self.assertRaises(ValueError): cave.blocking_level(donor, 'PortalCollision', cave.PORTAL, (85, 85, 300))

    def test_collision_stream_preserves_world_streams_and_soft_paths(self):
        obj = lambda name, value: cave.data_property(name, value, 'ObjectPropertyData')
        native = {'Imports': [{'ObjectName': 'LevelStreamingAlwaysLoaded', 'OuterIndex': 0}],
                  'Exports': [], 'DependsMap': [[], []], 'NameMap': ['native']}
        world = {'ObjectName': 'Wld_PL', 'OuterIndex': 0, 'ClassIndex': 0,
                 'Extras': base64.b64encode(struct.pack('<4i', 0, 0, 1, 2)).decode(),
                 'CreateBeforeSerializationDependencies': [2], 'Data': []}
        stream = {'$type': 'UAssetAPI.ExportTypes.NormalExport, UAssetAPI', 'ObjectName': 'nativeStream',
            'OuterIndex': 1, 'ClassIndex': -1, 'SuperIndex': 0, 'TemplateIndex': 0,
            'CreateBeforeSerializationDependencies': [], 'SerializationBeforeSerializationDependencies': [],
            'SerializationBeforeCreateDependencies': [], 'CreateBeforeCreateDependencies': [],
            'Data': [cave.data_property('WorldAsset', {'AssetPath': {'PackageName': '/Game/Original',
                        'AssetName': 'Original'}, 'SubPathString': ''}, 'SoftObjectPropertyData')]}
        native['Exports'] = [world, stream]
        built = copy.deepcopy(native); before = copy.deepcopy(native)
        path = cave.PACKAGE + '_EntranceCollision'
        cave.add_collision_stream(built, 'Wld_PL', native, path)
        self.assertEqual(struct.unpack('<5i', base64.b64decode(built['Exports'][0]['Extras'])), (0, 0, 2, 2, 3))
        self.assertEqual(built['Exports'][0]['CreateBeforeSerializationDependencies'], [2, 3])
        self.assertEqual(built['Exports'][1], before['Exports'][1])
        added = built['Exports'][2]
        self.assertEqual((added['OuterIndex'], added['ClassIndex']), (1, -1))
        self.assertEqual(cave.property_data(added, 'WorldAsset')['Value']['AssetPath'],
                         {'PackageName': '/Game/' + path, 'AssetName': Path(path).name})
        self.assertEqual(native, before)
        broken = copy.deepcopy(native)
        broken['Exports'][0]['Extras'] = base64.b64encode(struct.pack('<4i', 0, 0, 99, 2)).decode()
        with self.assertRaises(ValueError): cave.add_collision_stream(broken, 'Wld_PL', native, path)

    def test_grant_timeline_executes_native_lifecycle_without_original_cutscene(self):
        def prop(name, value): return {'Name': name, 'Value': value, 'IsZero': False}
        def signature(): return prop('Signature', [prop('Signature', '{native signature}')])
        source = {'NameMap': ['native'], 'Imports': [{'ObjectName': name} for name in (
            'CPP_TalkEventSequenceDirector', 'ExecuteHeader', 'ExecuteFooter')], 'Exports': [
            {'ObjectName': 'SEQ_C01_014_03', 'Data': [prop('MovieScene', 2), prop('DirectorClass', 99),
                prop('CompiledData', 88), prop('BindingReferences', [prop('SortedReferences', ['Rain'])]), signature()]},
            {'ObjectName': 'MovieScene_0', 'Data': [prop('Possessables', ['Rain']), prop('ObjectBindings', ['Leah']),
                prop('BindingGroups', ['actors']), prop('CameraCutTrack', 77), prop('Tracks', [prop('0', 3)]),
                prop('PlaybackRange', [{'Value': {'LowerBound': {'Value': {'Value': 0}},
                                                 'UpperBound': {'Value': {'Value': 228000}}}}]), signature()]},
            {'ObjectName': 'MovieSceneEventTrack_0', 'Data': [prop('Sections', [prop('0', 4)]),
                prop('EvaluationField', ['cached cutscene']), prop('EvaluationFieldGuid', 'old'), signature()]},
            {'ObjectName': 'section', 'Data': [signature(), prop('EventChannel', [
                prop('KeyTimes', [prop('0', [{'Value': {'Value': 200}, 'IsZero': False}])]),
                prop('KeyValues', [prop('0', [prop('Ptrs', [prop('Function', 70),
                    prop('BoundObjectProperty', {'Path': ['Rain'], 'ResolvedOwner': 7})])])])])]}]}
        before = copy.deepcopy(source)
        built = cave.grant_sequence(source)
        sequence, scene, track, section = built['Exports']
        self.assertEqual(cave.property_data(sequence, 'DirectorClass')['Value'], -1)
        self.assertEqual(cave.property_data(sequence, 'CompiledData')['Value'], 0)
        for name in ('Possessables', 'ObjectBindings', 'BindingGroups'):
            self.assertEqual(cave.property_data(scene, name)['Value'], [])
        self.assertEqual(cave.property_data(scene, 'CameraCutTrack')['Value'], 0)
        channel = cave.property_data(section, 'EventChannel')
        self.assertEqual([p['Value'][0]['Value']['Value'] for p in cave.property_data(channel, 'KeyTimes')['Value']],
                         [0, 2400])
        functions = []
        for event in cave.property_data(channel, 'KeyValues')['Value']:
            ptrs = cave.property_data(event, 'Ptrs')
            functions.append(cave.property_data(ptrs, 'Function')['Value'])
            self.assertEqual(cave.property_data(ptrs, 'BoundObjectProperty')['Value'], {'Path': [], 'ResolvedOwner': 0})
        self.assertEqual(functions, [-2, -3])
        self.assertEqual(cave.property_data(scene, 'PlaybackRange')['Value'][0]['Value']['UpperBound']['Value']['Value'], 4800)
        self.assertFalse(any(p['Name'] in ('EvaluationField', 'EvaluationFieldGuid') for p in track['Data']))
        for e in built['Exports']: self.assertNotEqual(cave.property_data(e, 'Signature')['Value'][0]['Value'], '{native signature}')
        self.assertEqual(source, before)
        self.assertEqual(cave.grant_sequence(source), built)
        source['Imports'][2]['ObjectName'] = 'not ExecuteFooter'
        with self.assertRaises(ValueError): cave.grant_sequence(source)

    def test_event_only_grant_uses_manual_input_and_follows_grounded_capsule(self):
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
        self.assertEqual(cave.property_data(actor, 'm_MapId')['Value'], cave.STONE_ID)
        self.assertEqual(cave.property_data(actor, 'm_PointID')['Value'], 1)
        actual, = cave.property_data(actor, 'mTransitionDataList')['Value']
        self.assertEqual(cave.property_data(actual, 'mapId')['Value'], cave.STONE_ID)
        self.assertEqual(cave.property_data(actual, 'pointId')['Value'], 1)
        original, rows, unit = cave_game()
        with tempfile.TemporaryDirectory() as root:
            enabled(root)
            operations = testing.prepare({}, [unit], root, rows)
        for rel in (testing.EVENT, testing.COMPOSITE):
            added, = [a for a in operations[rel]['add'] if a['row'] == cave.EVENT]
            grant = testing.apply_fields(original[rel][added['cloneFrom']], added['set'])
            destination = grant['TransitionLocation']
            self.assertEqual((destination['mapId'], destination['pointId']), (cave.STONE_ID, 1))
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

    def test_native_talk_binding_uses_actual_vision_ownership_without_a_transition_pre_event(self):
        def prop(name, value): return {'Name': name, 'Value': value, 'IsZero': False}
        event = prop('0', [prop('Condition', 'old story condition'), prop('EventId', 'OldTalk')])
        owner = {'Data': [prop('m_EventSettings', [prop('EventList', [event])]), prop('m_MapInteractType', 'Talk'),
                          prop('m_VisiblFlagCondition', '{item:13507}==0'),
                          prop('RootComponent', 37), prop('m_SsPlayerScale', 4.25)]}
        cave.npc_grant(owner, {'id': 13507})
        self.assertEqual(cave.property_data(event, 'Condition')['Value'], '{item:13507}==0')
        self.assertEqual(cave.property_data(event, 'EventId')['Value'], cave.EVENT)
        self.assertEqual(cave.property_data(owner, 'm_MapInteractType')['Value'], 'Talk')
        self.assertEqual(cave.property_data(owner, 'RootComponent')['Value'], 37)
        self.assertEqual(cave.property_data(owner, 'm_SsPlayerScale')['Value'], 4.25)
        self.assertEqual(cave.property_data(owner, 'm_VisiblFlagCondition')['Value'], '{item:13507}==0')

    def navigation_source(self):
        trigger = cave.data_property('Trigger', {'AssetPath': {'PackageName': '/Game/' + cave.DONOR_GD,
            'AssetName': Path(cave.DONOR_GD).name}, 'SubPathString': 'PersistentLevel.BP_MapTransitionTrigger_C_1'},
            'SoftObjectPropertyData')
        return {'NameMap': ['native'], 'Exports': [
            {'ObjectName': Path(cave.STONE_NAV).name, 'Data': [], 'Extras': 'original world'},
            {'ObjectName': 'CPP_Map_NavMeshBoundsVolume_1', 'Data': [cave.data_property(
                'm_TransitionTriggerList', [dict(Name='0', Value=[trigger])], 'ArrayPropertyData')],
                'Extras': 'cooked bounds'},
            {'ObjectName': 'RecastNavMeshDataChunk_2', 'Data': [], 'Extras': 'cooked navigation'}]}

    def test_private_navigation_connects_both_private_exits_and_preserves_cooked_data(self):
        source = self.navigation_source(); before = copy.deepcopy(source)
        built = cave.stone_navigation(source)
        area = cave.export(built, 'CPP_Map_NavMeshBoundsVolume_1')[1]
        links = cave.property_data(area, 'm_TransitionTriggerList')['Value']
        self.assertEqual([p['Name'] for p in links], ['0', '1'])
        for link, actor in zip(links, ('BP_MapTransitionTrigger_C_1', cave.NAME + '_Portal')):
            path = cave.property_data(link, 'Trigger')['Value']
            self.assertEqual(path['AssetPath'], {'PackageName': '/Game/' + cave.PACKAGE + '_Stone_GD',
                                                 'AssetName': cave.NAME + '_Stone_GD'})
            self.assertEqual(path['SubPathString'], 'PersistentLevel.' + actor)
        self.assertEqual([e['Extras'] for e in built['Exports']], [e['Extras'] for e in source['Exports']])
        self.assertEqual(source, before)
        cave.property_data(source['Exports'][1], 'm_TransitionTriggerList')['Value'][0]['Value'][0]['Value']['SubPathString'] = 'UnexpectedActor'
        with self.assertRaises(ValueError): cave.stone_navigation(source)

    def test_return_point_is_in_persistent_actor_list_and_bound_to_private_navigation(self):
        from unittest.mock import patch
        def prop(name, value): return {'Name': name, 'Value': value, 'IsZero': False}
        level = {'ObjectName': 'PersistentLevel', 'OuterIndex': 2, 'Actors': [0],
                 'CreateBeforeSerializationDependencies': []}
        point = {'ObjectName': 'old point', 'OuterIndex': 1,
                 'Data': [prop('m_PointID', 0), prop('m_pRootComponent', 4), prop('RootComponent', 4)]}
        root = {'ObjectName': 'DefaultRootComponent', 'OuterIndex': 3, 'Data': [prop(
            'RelativeLocation', [{'Value': {'X': 0, 'Y': 0, 'Z': 0}, 'IsZero': False}])]}
        view = {'NameMap': [], 'Exports': [level, {'ObjectName': cave.NAME + '_Stone_PL', 'OuterIndex': 0}, point, root]}
        nav = cave.stone_navigation(self.navigation_source())
        with patch.object(cave, 'clone_graph', return_value={4: 3, 12: 4}) as clone:
            cave.persistent_return_point(view, {}, nav)
        clone.assert_called_once_with(view, {}, [4, 12], {8: 1, 14: 2})
        self.assertEqual(level['Actors'], [0, 3])
        self.assertIn(3, level['CreateBeforeSerializationDependencies'])
        self.assertEqual(cave.property_data(point, 'm_PointID')['Value'], 1)
        self.assertEqual(cave.property_data(point, 'RootComponent')['Value'], 4)
        self.assertEqual(tuple(cave.property_data(root, 'RelativeLocation')['Value'][0]['Value'][a]
                               for a in ('X', 'Y', 'Z')), cave.PORTAL_RETURN)
        ref, = cave.property_data(point, 'm_AreaBoxList')['Value']
        self.assertEqual(ref['Value']['AssetPath'], {'PackageName': '/Game/' + cave.PACKAGE + '_Stone_NAV',
                                                     'AssetName': cave.NAME + '_Stone_NAV'})
        self.assertEqual(ref['Value']['SubPathString'], 'PersistentLevel.CPP_Map_NavMeshBoundsVolume_1')

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


class CrystalFinaTestModeTests(unittest.TestCase):
    def test_test_mode_uses_existing_identity_grant_and_native_intro_appearance(self):
        original, rows, unit = cave_game(); before = copy.deepcopy(original)
        with tempfile.TemporaryDirectory() as root:
            enabled(root)
            path = Path(root) / testing.CONFIG
            path.write_text(json.dumps({'schema': 1, 'maxMr': False, 'crystalCaveTest': True}))
            plans, _ = cave.cave_plans([unit], root, rows)
            selected, spec = plans[0][0]
            self.assertTrue(spec.fina_test)
            self.assertEqual((spec.map_id, spec.stone_id, spec.npc_id), (29991, 29990, 29991))
            self.assertEqual(spec.sprite, '/Game/Chara/Field_Unit/pc0030/pc0030_01/pc0030_01')
            self.assertEqual(spec.sprite_scale, 2.7)
            self.assertAlmostEqual(spec.sprite_float + 21 * spec.sprite_scale, 183.5)
            self.assertFalse(spec.test_rotate)
            self.assertTrue(spec.material.endswith('/M_Ss_Component_PBR'))
            operations = testing.prepare({}, [unit], root, rows)
            path = Path(root) / testing.CONFIG
            controls = json.loads(path.read_bytes()); controls['crystalCaveTestRotate'] = True
            path.write_text(json.dumps(controls))
            rotated, _ = cave.cave_plans([unit], root, rows)
            self.assertTrue(rotated[0][0][1].test_rotate)
        self.assertEqual(original, before)
        grant, = [a for a in operations[testing.EVENT]['add'] if a['row'] == cave.EVENT]
        event = testing.apply_fields(original[testing.EVENT][grant['cloneFrom']], grant['set'])
        self.assertEqual(event['ObtainItemList'], [{'Condition': '{item:13507}==0', 'ID': 13507, 'Num': 1, 'Text': ''}])
        self.assertEqual(event['TransitionLocation'], {'mapId': 29990, 'pointId': 1, 'bDoAutoSave': False})
        self.assertEqual(selected, unit)

    def test_settings_keep_legacy_files_compatible_and_reject_two_overlapping_caves(self):
        self.assertTrue(testing.validate_settings({'schema': 1, 'maxMr': False})['crystalCaveTestSolid'])
        self.assertFalse(testing.validate_settings({'schema': 1, 'maxMr': False})['crystalCaveTest'])
        self.assertFalse(testing.validate_settings({'schema': 1, 'maxMr': False})['crystalCaveTestRotate'])
        self.assertTrue(testing.validate_settings({'schema': 1, 'maxMr': False, 'crystalCaveTest': True})['crystalCaveTest'])
        for value in (1, 'true', None):
            for flag in ('crystalCaveTest', 'crystalCaveTestSolid', 'crystalCaveTestRotate'):
                with self.assertRaises(ValueError):
                    testing.validate_settings({'schema': 1, 'maxMr': False, flag: value})
        with self.assertRaises(ValueError):
            testing.validate_settings({'schema': 1, 'maxMr': False, 'crystalCave': True, 'crystalCaveTest': True})

    @staticmethod
    def source():
        from test_crystal_mesh import native_mesh_fixture
        def p(name, value, kind='ObjectPropertyData', **extra):
            return {'$type': 'UAssetAPI.PropertyTypes.Objects.' + kind + ', UAssetAPI',
                    'Name': name, 'Value': value, 'IsZero': False, **extra}
        def vec(name, values):
            return p(name, [{'Value': dict(zip(('X', 'Y', 'Z'), values)), 'IsZero': False}], 'StructPropertyData')
        imports = [
            {'ObjectName': '/Game/' + cave.TEST_NATIVE_MESH, 'ClassName': 'Package', 'OuterIndex': 0},
            {'ObjectName': Path(cave.TEST_NATIVE_MESH).name, 'ClassName': 'StaticMesh', 'OuterIndex': -1},
            {'ObjectName': '/Game/' + cave.TEST_NATIVE_MATERIAL, 'ClassName': 'Package', 'OuterIndex': 0},
            {'ObjectName': Path(cave.TEST_NATIVE_MATERIAL).name, 'ClassName': 'MaterialInstanceConstant', 'OuterIndex': -3},
            {'ObjectName': '/Script/Engine', 'ClassName': 'Package', 'OuterIndex': 0},
            {'ObjectName': 'StaticMeshComponent', 'ClassName': 'Class', 'OuterIndex': -5}]
        component = {'$type': 'UAssetAPI.ExportTypes.NormalExport, UAssetAPI', 'ObjectName': 'StaticMeshComponent0',
            'OuterIndex': 1, 'ClassIndex': -6, 'SuperIndex': 0, 'TemplateIndex': 0,
            'ObjectFlags': 'RF_DefaultSubObject', 'Extras': 'opaqueLODData',
            'SerializationBeforeSerializationDependencies': [], 'CreateBeforeSerializationDependencies': [-2, -4],
            'SerializationBeforeCreateDependencies': [-6], 'CreateBeforeCreateDependencies': [1],
            'Data': [p('StaticMesh', -2), p('OverrideMaterials', [p('0', -4)], 'ArrayPropertyData'),
                     vec('RelativeLocation', (6111, -740, 481)), vec('RelativeScale3D', (.25, .25, .25)),
                     p('VisibilityId', 1, 'IntPropertyData'), p('bIsValidTextureStreamingBuiltData', True, 'BoolPropertyData')]}
        background = {'NameMap': ['native'], 'Imports': imports, 'Exports': [{'ObjectName': 'StaticMeshActor_235',
            'Extras': 'nativeActorFooter'}, component], 'DependsMap': [[], []]}
        imports += [{'ObjectName': '/Game/Test/Crystal_Normal', 'OuterIndex': 0, 'ClassName': 'Package', 'ClassPackage': '/Script/CoreUObject'},
                    {'ObjectName': 'Crystal_Normal', 'OuterIndex': -7, 'ClassName': 'Texture2D', 'ClassPackage': '/Script/Engine'}]
        mesh = {'NameMap': ['native'], 'Imports': copy.deepcopy(imports), 'Exports': [{
            'ObjectName': Path(cave.TEST_NATIVE_MESH).name, 'Data': [
                p('StaticMaterials', [{'Value': [p('MaterialInterface', -4)]}], 'ArrayPropertyData'),
                {'Name': 'ExtendedBounds', 'Value': [vec('Origin', (-.29, -2.08, 1233))]}],
                'CreateBeforeSerializationDependencies': [], 'Extras': base64.b64encode(native_mesh_fixture()).decode()}]}
        scalar = p('0', [p('ParameterInfo', [p('Name', 'Crystal_Emissive', 'NamePropertyData')], 'StructPropertyData'),
                         p('ParameterValue', 10.0, 'FloatPropertyData'),
                         p('ExpressionGUID', [p('ExpressionGUID', '{11111111-1111-1111-1111-111111111111}')], 'StructPropertyData')], 'StructPropertyData')
        material = {'NameMap': [Path(cave.TEST_NATIVE_MATERIAL).name, '/Game/' + cave.TEST_NATIVE_MATERIAL],
                    'Imports': copy.deepcopy(imports), 'Exports': [{'ObjectName': Path(cave.TEST_NATIVE_MATERIAL).name,
                        'CreateBeforeSerializationDependencies': [],
                        'Data': [p('Parent', -4), p('bHasStaticPermutationResource', True, 'BoolPropertyData'),
                                 p('ScalarParameterValues', [scalar], 'ArrayPropertyData'),
                                 p('VectorParameterValues', [], 'ArrayPropertyData'),
                                 p('TextureParameterValues', [p('0', [
                                     p('ParameterInfo', [p('Name', 'Crystal_Normal', 'NamePropertyData')], 'StructPropertyData'),
                                     p('ParameterValue', -8), p('ExpressionGUID', [p('ExpressionGUID', '{11111111-1111-1111-1111-111111111111}')], 'StructPropertyData')],
                                     'StructPropertyData')], 'ArrayPropertyData'),
                                 p('StaticParametersRuntime', [], 'StructPropertyData'),
                                 p('BasePropertyOverrides', [], 'StructPropertyData')], 'Extras': 'originalShaderData'}]}
        shader = {'NameMap': list(cave.TEST_CRYSTAL_PARAMETERS), 'Exports': [{
            'ObjectName': Path(cave.TEST_NATIVE_SHADER).name,
            'Data': [p('ShadingModel', 'MSM_SingleLayerWater', 'EnumPropertyData')]}]}
        return {cave.TEST_BACKGROUND: background, cave.TEST_NATIVE_MESH: mesh,
                cave.TEST_NATIVE_MATERIAL: material, cave.TEST_NATIVE_SHADER: shader}

    def test_private_material_inherits_native_glass_transmission_without_crystal_overrides(self):
        source = self.source(); before = copy.deepcopy(source)
        copied = cave.test_crystal_assets(source)
        self.assertEqual(source, before)
        material = copied[cave.TEST_MATERIAL]['Exports'][0]
        view = copied[cave.TEST_MATERIAL]
        ref = cave.property_data(material, 'Parent')['Value']
        self.assertEqual(view['Imports'][-ref - 1]['ObjectName'], Path(cave.TEST_NATIVE_SHADER).name)
        self.assertEqual(view['Imports'][-ref - 1]['ClassName'], 'Material')
        self.assertIn('Material', view['NameMap'])
        self.assertFalse(cave.property_data(material, 'bHasStaticPermutationResource')['Value'])
        self.assertEqual(base64.b64decode(material['Extras']), struct.pack('<ii', 0, 0))
        self.assertFalse({'StaticParametersRuntime', 'BasePropertyOverrides', 'VectorParameterValues',
                          'TextureParameterValues'} & {p['Name'] for p in material['Data']})
        scalars = cave.property_data(material, 'ScalarParameterValues')['Value']
        values = {cave.property_data(cave.property_data(p, 'ParameterInfo'), 'Name')['Value']:
                  cave.property_data(p, 'ParameterValue')['Value'] for p in scalars}
        for name, value in cave.TEST_CRYSTAL_PARAMETERS.items(): self.assertAlmostEqual(values[name], value)
        self.assertEqual(set(values), set(cave.TEST_CRYSTAL_PARAMETERS))
        self.assertLess(values['Opacity'], .25)
        self.assertGreater(values['Fresnel_Intensity'], 0.0)
        self.assertEqual(values['RefractionDepthBias'], 12.0)
        self.assertNotIn('Dither_Intensity', values)
        self.assertNotIn('Crystal_Emissive', values)
        mesh = copied[cave.TEST_MESH]
        ref = cave.property_data(cave.property_data(mesh['Exports'][0], 'StaticMaterials')['Value'][0], 'MaterialInterface')['Value']
        self.assertEqual(mesh['Imports'][-ref - 1]['ObjectName'], Path(cave.TEST_MATERIAL).name)
        self.assertIn('/Game/' + cave.TEST_MATERIAL, mesh['NameMap'])
        self.assertEqual(mesh['NamesReferencedFromExportDataCount'], len(mesh['NameMap']))

    def test_builtin_refraction_bias_does_not_require_a_declared_parent_parameter(self):
        source = self.source(); source[cave.TEST_NATIVE_SHADER]['NameMap'].remove('RefractionDepthBias')
        material = cave.test_crystal_assets(source)[cave.TEST_MATERIAL]['Exports'][0]
        scalars = cave.property_data(material, 'ScalarParameterValues')['Value']
        bias, = [p for p in scalars if cave.property_data(cave.property_data(p, 'ParameterInfo'), 'Name')['Value'] == 'RefractionDepthBias']
        self.assertEqual(cave.property_data(bias, 'ParameterValue')['Value'], 12)

    def test_tip_glass_keeps_central_coverage_and_only_adds_weak_native_normal_detail(self):
        source = self.source(); before = copy.deepcopy(source)
        assets = cave.test_crystal_assets(source)
        base = assets[cave.TEST_MATERIAL]['Exports'][0]
        tips = assets[cave.TEST_TIP_MATERIAL]['Exports'][0]
        def values(owner):
            return {cave.property_data(cave.property_data(p, 'ParameterInfo'), 'Name')['Value']:
                    cave.property_data(p, 'ParameterValue')['Value'] for p in cave.property_data(owner, 'ScalarParameterValues')['Value']}
        base_values, tip_values = values(base), values(tips)
        self.assertEqual({k: v for k, v in tip_values.items() if k != 'Normal_Intensity'},
                         {k: v for k, v in base_values.items() if k != 'Normal_Intensity'})
        self.assertEqual(base_values['Normal_Intensity'], 0)
        self.assertGreater(tip_values['Normal_Intensity'], 0)
        self.assertLess(tip_values['Normal_Intensity'], .05)
        normal, = cave.property_data(tips, 'TextureParameterValues')['Value']
        self.assertEqual(cave.property_data(cave.property_data(normal, 'ParameterInfo'), 'Name')['Value'], 'NormalMap')
        texture = cave.property_data(normal, 'ParameterValue')['Value']
        self.assertEqual(assets[cave.TEST_TIP_MATERIAL]['Imports'][-texture - 1]['ObjectName'], 'Crystal_Normal')
        self.assertEqual(base['Extras'], tips['Extras'])
        self.assertEqual(source, before)

    def test_solid_check_preserves_native_opaque_material_and_uses_identical_mesh(self):
        source = self.source(); before = copy.deepcopy(source)
        source.pop(cave.TEST_NATIVE_SHADER)  # Solid mode must not need the glass shader.
        solid = cave.test_crystal_assets(source, solid=True)
        material = solid[cave.TEST_MATERIAL]['Exports'][0]
        self.assertEqual(material['Data'], before[cave.TEST_NATIVE_MATERIAL]['Exports'][0]['Data'])
        self.assertEqual(material['Extras'], 'originalShaderData')
        self.assertEqual(solid[cave.TEST_MESH], cave.test_crystal_assets(before)[cave.TEST_MESH])
        self.assertNotIn('/Game/' + cave.TEST_NATIVE_SHADER, solid[cave.TEST_MATERIAL]['NameMap'])
        self.assertEqual(source[cave.TEST_NATIVE_MATERIAL], before[cave.TEST_NATIVE_MATERIAL])

    def test_turn_sequence_uses_tick_and_explicit_casing_transform_without_cutscene_controls(self):
        p, st, guid = cave.native_prop, cave.native_struct, cave.native_guid
        zero = '{00000000-0000-0000-0000-000000000000}'
        def obj(name, outer, data, cls=0):
            return {'$type': 'UAssetAPI.ExportTypes.NormalExport, UAssetAPI', 'ObjectName': name,
                'OuterIndex': outer, 'ClassIndex': cls, 'SuperIndex': 0, 'TemplateIndex': 0, 'Data': data,
                'Extras': '', **{k: [] for k in ('SerializationBeforeSerializationDependencies',
                    'CreateBeforeSerializationDependencies', 'SerializationBeforeCreateDependencies', 'CreateBeforeCreateDependencies')}}
        def bounds(name):
            return st(name, 'MovieSceneFrameRange', [{'Name': name, 'Value': {
                'LowerBound': {'Type': 'Inclusive', 'Value': {'Value': 12}},
                'UpperBound': {'Type': 'Exclusive', 'Value': {'Value': 48}}}}])
        def scene(name, outer):
            return obj(name, outer, [p('Possessables', [], 'ArrayPropertyData'), p('ObjectBindings', [], 'ArrayPropertyData'),
                p('BindingGroups', [], 'ArrayPropertyData'), p('Spawnables', [], 'ArrayPropertyData'),
                p('Tracks', [p('0', 1)], 'ArrayPropertyData'), p('CameraCutTrack', 1), p('CustomClock', 1),
                p('ClockSource', 'Custom', 'EnumPropertyData', EnumType='EUpdateClockSource', InnerType='ByteProperty'), bounds('PlaybackRange'),
                st('TickResolution', 'FrameRate', [p('Numerator', 24000, 'IntPropertyData')]), guid('Signature', zero)])
        base_scene = scene('MovieScene', 1)
        root = obj(Path(cave.GRANT_DONOR).name, 0, [p('MovieScene', 2), p('DirectorClass', -1), p('CompiledData', -1),
            st('BindingReferences', 'LevelSequenceBindingReferences', [p('SortedReferences', [], 'ArrayPropertyData')]), guid('Signature', zero)])
        base = {'NameMap': ['native', '/Game/' + cave.GRANT_DONOR], 'Imports': [], 'Exports': [root, base_scene], 'DependsMap': [[], []]}
        # The actual acquisition donor already owns a TransformTrack under its
        # MovieScene. Appending another export with that name aliases its path.
        base['Exports'].append(obj('TransformTrack', 2, [])); base['DependsMap'].append([])
        donor_scene = scene('DonorScene', 0)
        cave.set_value(donor_scene, 'Possessables', [st('0', 'MovieScenePossessable', [guid('Guid', zero),
            guid('ParentGuid', zero), p('Name', 'Original', 'StrPropertyData')])])
        cave.set_value(donor_scene, 'ObjectBindings', [st('0', 'MovieSceneBinding', [guid('ObjectGuid', zero),
            p('BindingName', 'Original', 'StrPropertyData'), p('Tracks', [p('0', 2)], 'ArrayPropertyData')])])
        track = obj('TransformTrack', 1, [p('Sections', [p('0', 3)], 'ArrayPropertyData'), guid('Signature', zero)])
        channel = {'Times': [], 'Values': [{'Value': 27.0, 'InterpMode': 'RCIM_Cubic'}],
                   'TickResolution': {'Numerator': 24000, 'Denominator': 1}}
        rotation = st('Rotation', 'MovieSceneDoubleChannel', [{'Value': channel}]); rotation['ArrayIndex'] = 2
        section = obj('TransformSection', 2, [rotation, bounds('SectionRange'), guid('Signature', zero)], -2)
        donor = {'NameMap': ['native'], 'Imports': [{'ObjectName': '/Script/MovieSceneTracks', 'OuterIndex': 0},
            {'ObjectName': 'MovieScene3DTransformSection', 'OuterIndex': -1}],
            'Exports': [donor_scene, track, section], 'DependsMap': [[], [], []]}
        source = {**self.source(), cave.GRANT_DONOR: base, cave.TEST_SPIN_DONOR: donor}; before = copy.deepcopy(source)
        result = cave.test_spin_sequence(source)
        self.assertEqual(source, before)
        self.assertNotEqual(result['Exports'][-2]['ObjectName'], 'TransformTrack')
        cave.check_object_names(result)
        collision = copy.deepcopy(result); collision['Exports'][-2]['ObjectName'] = 'transformtrack'
        with self.assertRaisesRegex(ValueError, 'Duplicate cooked object path'):
            cave.check_object_names(collision)
        scene = result['Exports'][1]
        for name in ('Spawnables', 'Tracks', 'BindingGroups'):
            self.assertEqual(cave.property_data(scene, name)['Value'], [])
        self.assertEqual(cave.property_data(scene, 'CameraCutTrack')['Value'], 0)
        self.assertEqual(cave.property_data(scene, 'CustomClock')['Value'], 0)
        self.assertEqual(cave.property_data(scene, 'ClockSource')['Value'], 'Tick')
        self.assertEqual(cave.property_data(result['Exports'][0], 'DirectorClass')['Value'], 0)
        binding, = cave.property_data(scene, 'ObjectBindings')['Value']
        self.assertEqual(cave.property_data(binding, 'ObjectGuid')['Value'][0]['Value'], cave.TEST_SPIN_GUID)
        section = result['Exports'][-1]
        self.assertEqual(cave.property_data(cave.property_data(section, 'TransformMask'), 'Mask')['Value'], 511)
        self.assertFalse(cave.property_data(section, 'bUseQuaternionInterpolation')['Value'])
        channels = {(p['Name'], p.get('ArrayIndex', 0)): p['Value'][0]['Value'] for p in section['Data']
                    if p['Name'] in ('Translation', 'Rotation', 'Scale')}
        self.assertEqual(len(channels), 9)
        for axis, expected in enumerate((.0348, .2496, 35.54)):
            self.assertAlmostEqual(channels['Translation', axis]['DefaultValue'], expected)
            self.assertEqual(channels['Translation', axis]['Values'], [])
            self.assertEqual(channels['Scale', axis]['DefaultValue'], .12)
        yaw = channels['Rotation', 2]
        self.assertEqual([k['Value'] for k in yaw['Times']], [0, 2400000])
        self.assertEqual([k['Value'] for k in yaw['Values']], [0, 360])
        self.assertTrue(all(k['InterpMode'] == 'RCIM_Linear' for k in yaw['Values']))

    def test_changed_native_shader_is_rejected_instead_of_inventing_a_blend_permutation(self):
        for change in ('ordinary opaque', 'masked', 'missing scalar', 'missing shading model'):
            source = self.source(); shader = source[cave.TEST_NATIVE_SHADER]
            if change == 'ordinary opaque': shader['Exports'][0]['Data'][0]['Value'] = 'MSM_DefaultLit'
            elif change == 'masked': shader['Exports'][0]['Data'].append({'Name': 'BlendMode', 'Value': 'BLEND_Masked'})
            elif change == 'missing scalar': shader['NameMap'].remove('Opacity')
            else: shader['Exports'][0]['Data'] = []
            with self.subTest(change=change), self.assertRaisesRegex(ValueError, 'glass transmission shader changed'):
                cave.test_crystal_assets(source)

    def assert_shell_setup(self, rotate):
        source = self.source(); before = copy.deepcopy(source)
        npc = {'NameMap': ['native'], 'Imports': [], 'Exports': [{'ObjectName': 'Native_' + str(i), 'Data': [],
               'CreateBeforeSerializationDependencies': []} for i in range(110)], 'DependsMap': [[] for _ in range(110)]}
        condition = {'Name': 'm_VisiblFlagCondition', 'Value': '{item:13507}==0'}
        npc['Exports'][0].update(ObjectName='Fixture_NPC', ClassIndex=cave.script_import(npc, 'Engine', 'World'), OuterIndex=0)
        npc['NameMap'].append('/Game/Map/StudioCrystalCave/Fixture_NPC')
        npc['Exports'][94].update(ObjectName='PersistentLevel', Actors=[31])
        npc['Exports'][30]['Data'].append(condition)
        npc['Exports'][30]['Data'].append({'Name': 'RootComponent', 'Value': 37})
        npc['Exports'][63]['Data'].append({'Name': 'AttachParent', 'Value': 77})
        if rotate:
            cave.attach_test_crystal(npc, source, rotate=True)
        else:
            cave.attach_test_crystal(npc, source)
        self.assertEqual(source, before)
        owner = npc['Exports'][30]
        _, shell = cave.export(npc, 'Studio_CrystalFinaTestCrystal')
        self.assertEqual(cave.property_data(owner, 'm_VisiblFlagCondition')['Value'], '{item:13507}==0')
        self.assertEqual(cave.property_data(owner, 'InstanceComponents')['Value'][0]['Value'], 111)
        self.assertEqual(shell['OuterIndex'], 31)
        self.assertEqual(cave.property_data(shell, 'AttachParent')['Value'], 110)
        self.assertNotIn('Studio_CrystalFinaTestPivot', {e['ObjectName'] for e in npc['Exports']})
        self.assertEqual(cave.property_data(shell, 'VisibilityId')['Value'], -1)
        self.assertFalse(cave.property_data(shell, 'bIsValidTextureStreamingBuiltData')['Value'])
        self.assertTrue(cave.property_data(shell, 'bVisible')['Value'])
        self.assertFalse(cave.property_data(shell, 'bHiddenInGame')['Value'])
        self.assertEqual(cave.property_data(shell, 'CreationMethod')['Value'], 'Instance')
        self.assertEqual(cave.property_data(cave.property_data(shell, 'BodyInstance'), 'CollisionEnabled')['Value'], 'NoCollision')
        loc = cave.property_data(shell, 'RelativeLocation')['Value'][0]['Value']
        self.assertAlmostEqual(loc['Z'] + 1233 * cave.TEST_CRYSTAL_SCALE,
                               cave.TEST_SPRITE_FLOAT + 21.0 * cave.TEST_SPRITE_SCALE)
        self.assertAlmostEqual(loc['Y'] - 2.08 * cave.TEST_CRYSTAL_SCALE, 0.0)
        self.assertIn(110, shell['CreateBeforeSerializationDependencies'])
        registered = [p['Value'] for p in cave.property_data(owner, 'InstanceComponents')['Value']]
        self.assertEqual(registered, [111])
        self.assertEqual(cave.property_data(owner, 'RootComponent')['Value'], 37)
        self.assertEqual(cave.property_data(npc['Exports'][63], 'AttachParent')['Value'], 77)
        self.assertEqual(shell['Extras'], 'opaqueLODData')
        self.assertIn(111, owner['CreateBeforeSerializationDependencies'])
        return npc

    def test_grounded_shell_default_has_no_sequence_or_billboard_attachment(self):
        npc = self.assert_shell_setup(rotate=False)
        self.assertEqual(npc['Exports'][94]['Actors'], [31])
        self.assertNotIn('Studio_CrystalFinaTestSpin', {e['ObjectName'] for e in npc['Exports']})
        self.assertNotIn('/Game/' + cave.TEST_SPIN_SEQUENCE, {e['ObjectName'] for e in npc['Imports']})

    def test_optional_turn_targets_same_grounded_shell_without_player_restrictions(self):
        npc = self.assert_shell_setup(rotate=True)
        turn_id, turn = cave.export(npc, 'Studio_CrystalFinaTestSpin')
        playback = cave.property_data(turn, 'PlaybackSettings')
        self.assertEqual(cave.property_data(cave.property_data(playback, 'LoopCount'), 'Value')['Value'], -1)
        self.assertTrue(cave.property_data(playback, 'bAutoPlay')['Value'])
        self.assertTrue(cave.property_data(playback, 'bDisableCameraCuts')['Value'])
        self.assertFalse(cave.property_data(playback, 'bDisableMovementInput')['Value'])
        overrides = npc['Exports'][cave.property_data(turn, 'BindingOverrides')['Value'] - 1]
        binding = cave.property_data(overrides, 'BindingData')['Value'][0]
        self.assertTrue(cave.property_data(binding, 'Object')['Value']['SubPathString'].endswith('.Native_30.Studio_CrystalFinaTestCrystal'))
        self.assertIn(turn_id, npc['Exports'][94]['Actors'])


if __name__ == '__main__': unittest.main()
