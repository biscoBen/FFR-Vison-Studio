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


if __name__ == '__main__': unittest.main()
