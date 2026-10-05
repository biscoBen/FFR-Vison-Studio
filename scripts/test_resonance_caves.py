"""Selected-vision acquisition, shared caves, stable IDs and installer routing."""
import ast
import copy
import json
import math
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import test_crystal_cave as reference
from test_existing_visions import installer, fina_installer, ROOT

cave = reference.cave
testing = reference.testing


def vision(uid, key='cave_test', entrance='rock_cave', x=17600, y=21400):
    return {'id': uid, 'key': f'vision_{uid}', 'en': f'Test vision {uid}',
            'ffbe': {'id': '401001207'}, 'studioAcquisition': {
                'version': 2, 'random': False, 'hideSpoilers': True, 'location': key,
                'cave': {'version': 1, 'id': key, 'name': 'User cave', 'entrance': entrance,
                         'worldX': x, 'worldY': y}}}


def applied(original, operations):
    result = copy.deepcopy(original)
    for rel, operation in operations.items():
        for item in operation['add']:
            if item['row'] in result[rel]: raise AssertionError('Duplicate authored row')
            result[rel][item['row']] = testing.apply_fields(original[rel][item['cloneFrom']], item['set'])
        for item in operation['set']:
            result[rel][item['row']] = testing.apply_fields(result[rel][item['row']], item['set'])
        testing.check_rows(original[rel], result[rel], operation)
    return result


class ResonanceCavesTests(unittest.TestCase):
    def test_thirty_caves_grant_the_assigned_visions_and_keep_ids_after_restart(self):
        original, rows, _ = reference.cave_game()
        before = copy.deepcopy(original)
        units = [vision(13520 + i, f'cave_{i}', x=17000 + i * 100, y=21000) for i in range(30)]
        with tempfile.TemporaryDirectory() as root:
            operations = testing.prepare({}, units, root, rows)
            built = applied(original, operations)
            plans, _ = cave.cave_plans(units, root)
            self.assertEqual(len(plans), 30)
            self.assertEqual(len(operations[cave.MAP]['add']), 60)
            self.assertEqual(len(operations[cave.MAP_UNIT]['add']), 30)
            self.assertEqual(len({s.map_id for group in plans for _, s in group}), 30)
            for entries in plans:
                unit, spec = entries[0]
                self.assertEqual(built[cave.MAP][spec.name]['Name'], 'Resonance Cave')
                event = built[testing.COMPOSITE][spec.event]
                self.assertEqual(event['ObtainItemList'], [{'Condition': f'{{item:{unit["id"]}}}==0',
                                                          'ID': unit['id'], 'Num': 1, 'Text': ''}])
                self.assertEqual(event['TransitionLocation'], {'mapId': spec.stone_id, 'pointId': 1, 'bDoAutoSave': False})
                self.assertEqual(event['LoadingScreenSetting'], 'White')
                self.assertTrue(event['IsOpenDialogByFinishEvent'])
                self.assertFalse(event['FooterSettings']['IsApplyProgressis'])
                self.assertEqual(event['OnFlagList'], [])
                asset = built[cave.MAP_UNIT][spec.npc_name]['animationAssetList'][0]
                self.assertIn(f'summon{unit["id"]}', asset['Ss6Project'])
                self.assertNotIn('CrystalFina', asset['Material'])
            identities = (Path(root) / cave.IDENTITIES).read_bytes()
            self.assertEqual(testing.prepare({}, list(reversed(units)), root, rows), operations)
            self.assertEqual((Path(root) / cave.IDENTITIES).read_bytes(), identities)
        self.assertEqual(original, before)

    def test_precise_placement_keeps_ids_and_uses_white_portal_without_granting_items(self):
        original, rows, _ = reference.cave_game()
        unit = vision(13520, entrance='shrine')
        saved = unit['studioAcquisition']['cave']
        saved.update(version=2, worldZ=12.5, yaw=-90.0, scale=.75)
        with tempfile.TemporaryDirectory() as root:
            operations = testing.prepare({}, [unit], root, rows)
            plans, _ = cave.cave_plans([unit], root)
            spec = plans[0][0][1]
            built = applied(original, operations)
            portal = built[testing.COMPOSITE][spec.portal_event]
            self.assertEqual(portal['LoadingScreenSetting'], 'White')
            self.assertEqual(portal['ObtainItemList'], [])
            self.assertFalse(portal['IsOpenDialogByFinishEvent'])
            self.assertEqual(portal['TransitionLocation'], {'mapId': spec.map_id, 'pointId': 0, 'bDoAutoSave': False})
            self.assertEqual((spec.ground_z, spec.placement_yaw, spec.placement_scale), (12.5, -90.0, .75))
            self.assertEqual(spec.sprite_scale, cave.VISION_SCALE)
            saved.update(worldX=17400.25, worldY=21700.75)
            testing.prepare({}, [unit], root, rows)
            moved, _ = cave.cave_plans([unit], root)
            self.assertEqual(moved[0][0][1].stone_id, spec.stone_id)
            self.assertEqual(moved[0][0][1].npc_id, spec.npc_id)
        for field, bad in [('worldZ', float('nan')), ('yaw', 181), ('scale', 0), ('version', True)]:
            broken = copy.deepcopy(unit); broken['studioAcquisition']['cave'][field] = bad
            with self.assertRaises(ValueError): cave.assignment(broken)
        self.assertAlmostEqual(cave.terrain_height(17600, 21400), 85.103125)
        self.assertIsNone(cave.terrain_height(0, 0))

    def test_shared_cave_has_one_interior_pair_and_separate_vision_grants(self):
        original, rows, _ = reference.cave_game()
        units = [vision(13520), vision(13521)]
        with tempfile.TemporaryDirectory() as root:
            operations = testing.prepare({}, units, root, rows)
            built = applied(original, operations)
            plans, _ = cave.cave_plans(units, root)
        self.assertEqual(len(plans), 1)
        self.assertEqual(len(operations[cave.MAP]['add']), 2)
        self.assertEqual(len(operations[cave.PLACEMENT]['add']), 2)
        self.assertEqual(len(operations[cave.MAP_UNIT]['add']), 2)
        self.assertEqual(len(operations[testing.COMPOSITE]['add']), 3)
        first, second = [s for _, s in plans[0]]
        self.assertEqual(first.package, second.package)
        self.assertNotEqual(first.npc_package, second.npc_package)
        self.assertNotEqual(first.event, second.event)
        self.assertNotEqual(first.spawn_offset, second.spawn_offset)
        self.assertEqual({built[testing.COMPOSITE][s.event]['ObtainItemList'][0]['ID'] for _, s in plans[0]}, {13520, 13521})

    def test_ordinary_visions_gain_five_percent_without_resizing_crystal_fina(self):
        _, rows, fina = reference.cave_game()
        ordinary = vision(13520); fina['studioAcquisition'] = copy.deepcopy(ordinary['studioAcquisition'])
        with tempfile.TemporaryDirectory() as root:
            plans, _ = cave.cave_plans([ordinary, fina], root, rows)
        by_id = {unit['id']: spec for group in plans for unit, spec in group}
        self.assertAlmostEqual(by_id[ordinary['id']].sprite_scale, 2.55 * 1.05)
        self.assertEqual(by_id[fina['id']].sprite_scale, 4.25)

    def test_returns_follow_rotated_opening_and_ground_not_saved_entrance_height(self):
        for entrance, opening in [('rock_cave', (0, 1)), ('shrine', (0, -1)),
                                  ('dwarven_cave', (-1, 0)), ('desert_sinkhole', (0, -1))]:
            for yaw in (-180, -90, 0, 45, 105, 180):
                unit = vision(13520, entrance=entrance, x=16964.99, y=22678.74)
                unit['studioAcquisition']['cave'].update(version=2, worldZ=900, yaw=yaw, scale=2.0)
                with tempfile.TemporaryDirectory() as root, patch.object(cave, 'terrain_height', return_value=84.33):
                    _, rows, _ = reference.cave_game()
                    plans, _ = cave.cave_plans([unit], root, rows)
                spec = plans[0][0][1]
                dx, dy = spec.return_point[0] - spec.entrance[0], spec.return_point[1] - spec.entrance[1]
                angle = math.radians(yaw)
                self.assertAlmostEqual(dx, (opening[0]*math.cos(angle)-opening[1]*math.sin(angle))*600)
                self.assertAlmostEqual(dy, (opening[0]*math.sin(angle)+opening[1]*math.cos(angle))*600)
                self.assertEqual(spec.return_point[2], 84.33)
                self.assertTrue(abs(dx) > 160 or abs(dy) > 250, 'return overlaps entrance interaction')

    def test_world_banner_changes_only_landmark_policy_and_preserves_native_entries(self):
        def flag(name, value):
            return {'$type': 'UAssetAPI.PropertyTypes.Objects.BoolPropertyData, UAssetAPI',
                    'Name': name, 'Value': value, 'IsZero': not value}
        def entry(uid, value):
            return [{'Name': 'MapIdPropertyMap', 'Value': uid},
                    {'Name': 'MapIdPropertyMap', 'StructType': 'UIPlaceNameProperty',
                     'Value': [flag('bUseLandName', value), flag('bAllowDisplayOnTransition', False)]}]
        owner = {'ObjectName': 'DA_UI_PlaceNameProperty', 'Data': [
            {'Name': 'DefaultProperty', 'Value': [flag('bAllowDisplayOnTransition', True)]},
            {'Name': 'MapIdPropertyMap', 'Value': [entry(1000, True), entry(5200, False)]}]}
        original = {'NameMap': ['NativeName'], 'Exports': [owner], 'Imports': [], 'Extras': 'opaque'}
        before = copy.deepcopy(original)
        patched = cave.world_destination_banner(original)
        expected = copy.deepcopy(original)
        policy = expected['Exports'][0]['Data'][1]['Value'][0][1]['Value'][0]
        policy.update(Value=False, IsZero=False)
        self.assertEqual(original, before)
        self.assertEqual(patched, expected)
        self.assertEqual(cave.world_destination_banner(patched), patched)

        # Fail clearly on a changed native contract rather than touching defaults
        # or applying a map-wide rule to the wrong destination.
        for entries in ([], [entry(5200, False)], [entry(1000, True), entry(1000, True)]):
            malformed = copy.deepcopy(original)
            malformed['Exports'][0]['Data'][1]['Value'] = entries
            with self.assertRaisesRegex(ValueError, 'world-map banner entry changed'):
                cave.world_destination_banner(malformed)
        malformed = copy.deepcopy(original)
        malformed['Exports'][0]['Data'][1]['Value'][0][1]['Value'][0]['Value'] = 1
        with self.assertRaisesRegex(ValueError, 'landmark-name policy changed'):
            cave.world_destination_banner(malformed)

    def test_world_exit_keeps_world_route_and_resets_walking(self):
        def prop(name, value): return {'Name': name, 'Value': value, 'IsZero': False}
        actor = {'Data': [prop('m_MapId', 3000), prop('m_PointID', 0),
                         prop('m_RegionId', 3000),
                         prop('m_IsTransitionChangeMovementMethod', False), prop('m_TransitionMovementType', 'Flying')]}
        template = {'Data': [prop('m_IsUseCondion', True), prop('m_IsAutoTransition', True),
                            prop('mTransitionDataList', [prop('0', [prop('mapId', 3000), prop('pointId', 0)])])]}
        spec = cave.CaveSpec(map_id=29001)
        cave.overworld_exit(actor, template, spec)
        self.assertFalse(cave.property_data(actor, 'm_IsUseCondion')['Value'])
        self.assertEqual(cave.property_data(actor, 'm_MapId')['Value'], 1000)
        self.assertEqual(cave.property_data(actor, 'm_RegionId')['Value'], 1000)
        self.assertEqual(len([p for p in actor['Data'] if p['Name'] == 'm_RegionId']), 1)
        self.assertEqual(cave.property_data(actor, 'm_PointID')['Value'], 29001)
        self.assertTrue(cave.property_data(actor, 'm_IsTransitionChangeMovementMethod')['Value'])
        self.assertEqual(cave.property_data(actor, 'm_TransitionMovementType')['Value'], 'Walking')

        # Native donors omit this field when using their constructor default.
        actor['Data'] = [p for p in actor['Data'] if p['Name'] != 'm_RegionId']
        cave.overworld_exit(actor, template, spec)
        self.assertEqual(cave.property_data(actor, 'm_RegionId')['Value'], 1000)
        self.assertFalse(cave.property_data(actor, 'm_RegionId')['IsZero'])

    def test_new_caves_do_not_reassign_existing_ids_and_native_ids_are_skipped(self):
        original, rows, _ = reference.cave_game()
        original[cave.COMPOSITE]['Occupied'] = {'ID': 29000}
        with tempfile.TemporaryDirectory() as root:
            first = vision(13520, 'cave_z')
            testing.prepare({}, [first], root, rows)
            old, _ = cave.cave_plans([first], root)
            testing.prepare({}, [vision(13521, 'cave_a'), first], root, rows)
            new, _ = cave.cave_plans([first], root)
            self.assertEqual(old[0][0][1], new[0][0][1])
            self.assertEqual(new[0][0][1].stone_id, 29002)

    def test_invalid_or_conflicting_caves_preserve_operations_and_saved_identities(self):
        original, rows, _ = reference.cave_game()
        for change in ('coordinate', 'entrance', 'mismatch', 'duplicate', 'npc_collision', 'corrupt_registry'):
            with self.subTest(change=change), tempfile.TemporaryDirectory() as root:
                units = [vision(13520)]
                operations = {'existing': {'kept': True}}
                path = Path(root) / cave.IDENTITIES
                if change == 'coordinate': units[0]['studioAcquisition']['cave']['worldY'] = float('nan')
                if change == 'entrance': units[0]['studioAcquisition']['cave']['entrance'] = 'unknown'
                if change == 'mismatch': units += [vision(13521, x=18000)]
                if change == 'duplicate': units += copy.deepcopy(units)
                if change == 'npc_collision': original[cave.MAP_UNIT]['Occupied'] = {'ID': 87040}
                if change == 'corrupt_registry':
                    path.parent.mkdir(parents=True); path.write_bytes(b'{broken')
                before = path.read_bytes() if path.exists() else None
                with self.assertRaises(ValueError): cave.prepare(operations, units, root, rows)
                self.assertEqual(operations, {'existing': {'kept': True}})
                self.assertEqual(path.read_bytes() if path.exists() else None, before)
                original[cave.MAP_UNIT].pop('Occupied', None)

    def test_legacy_fina_and_custom_caves_can_coexist_without_duplicate_grants(self):
        original, rows, fina = reference.cave_game()
        with tempfile.TemporaryDirectory() as root:
            reference.enabled(root)
            operations = testing.prepare({}, [fina, vision(13520)], root, rows)
            self.assertEqual(len(operations[cave.MAP]['add']), 4)
            self.assertEqual(len(operations[testing.COMPOSITE]['add']), 4)
            assigned = copy.deepcopy(fina)
            assigned['studioAcquisition'] = vision(fina['id'])['studioAcquisition']
            operations = testing.prepare({}, [assigned], root, rows)
            self.assertEqual(len(operations[cave.MAP]['add']), 2)
            self.assertEqual(len(operations[testing.COMPOSITE]['add']), 2)

    def test_original_vision_planning_preferences_do_not_replace_native_acquisition(self):
        unit = vision(13520)
        unit['native'] = {'id': 13520}
        self.assertIsNone(cave.assignment(unit))

    def test_installed_builder_excludes_cave_visions_from_shop_and_keeps_others(self):
        source = (ROOT / 'scripts/fixtures/crystal_fina/make_vision_mod.py').read_bytes()
        tree = ast.parse(installer.hook_builder(fina_installer.hook_builder(source)))
        gate, = [node for node in ast.walk(tree) if isinstance(node, ast.If)
                 and ast.unparse(node.test) == '_ffr_crystal_cave.assignment(u) is None']
        slots = []
        script = compile(ast.Module(body=[gate], type_ignores=[]), '<installed-shop-gate>', 'exec')
        for unit in (vision(13520), {'id': 13521}, {'id': 13522, 'studioAcquisition': {
                'version': 2, 'random': True, 'hideSpoilers': True, 'location': 'shop_1', 'cave': None}}):
            exec(script, {'_ffr_crystal_cave': cave, 'u': unit, 'vid': unit['id'], 'shop_slots': slots})
        self.assertEqual(slots, [13521, 13522])

    def test_engine_entrance_choices_match_the_studio_catalog(self):
        data = json.loads((ROOT / 'assets/acquisition_map/locations.json').read_text(encoding='utf-8'))
        self.assertEqual(cave.ENTRANCE_MESHES, {e['id']: e['mesh'] for e in data['entrances']})

    def test_shared_vision_stream_names_include_the_unreal_fname_base(self):
        import base64
        import struct
        from unittest.mock import patch
        stream = {'ObjectName': 'NativeStream', 'OuterIndex': 1, 'ClassIndex': -1, 'Data': [{'Name': 'WorldAsset',
                  'Value': {'AssetPath': {'PackageName': '', 'AssetName': ''}}}]}
        view = {'NameMap': ['NativePrefix'], 'Imports': [], 'Exports': [
            {'ObjectName': 'Room', 'Extras': base64.b64encode(struct.pack('<3i', 2, 0, 0)).decode(),
             'CreateBeforeSerializationDependencies': []}, stream]}
        donor = {'Imports': [{'ObjectName': 'LevelStreamingAlwaysLoaded'}], 'Exports': [stream]}
        with patch.object(cave, 'clone_graph', return_value={1: 2}):
            cave.add_collision_stream(view, 'Room', donor, 'Map/Studio_ResonanceCave_29000_NPC_13524')
        name = stream['ObjectName']
        self.assertIn(name.rsplit('_', 1)[0], view['NameMap'])
        self.assertEqual(view['NameMap'][0], 'NativePrefix')
        cave.names(view, {'Value': 'UASSETAPI_INVALID_ENUM_IDX_14'})
        self.assertNotIn('UASSETAPI_INVALID_ENUM_IDX', view['NameMap'])
        self.assertEqual(view['NamesReferencedFromExportDataCount'], len(view['NameMap']))

    def test_switching_entrance_appends_serializable_imports_without_redirecting_existing_meshes(self):
        def vec(name, values): return {'Name': name, 'Value': [{'Value': dict(zip(('X', 'Y', 'Z'), values))}]}
        old = cave.ENTRANCE_MESHES['rock_cave']
        selected = cave.ENTRANCE_MESHES['shrine']
        view = {'Imports': [{'ObjectName': old, 'ClassName': 'Package', 'OuterIndex': 0},
                            {'ObjectName': Path(old).name, 'ClassName': 'StaticMesh', 'OuterIndex': -1}],
                'NameMap': ['NativePrefix'], 'NamesReferencedFromExportDataCount': 1}
        original = copy.deepcopy(view['Imports'])
        component = {'Data': [{'Name': 'StaticMesh', 'Value': -2},
                             vec('RelativeLocation', (0, 0, 0)), vec('RelativeScale3D', (1, 1, 1))]}
        source = {selected: {'Exports': [{'Data': [{'Name': 'ExtendedBounds', 'Value': [
            vec('Origin', (0, 0, 40)), vec('BoxExtent', (120, 100, 75))]}]}]}}
        spec = cave.CaveSpec(mesh=selected)
        cave.entrance_mesh(view, component, spec, source)
        self.assertEqual(view['Imports'][:2], original)
        self.assertEqual(view['NameMap'][0], 'NativePrefix')
        self.assertIn(selected, view['NameMap'])
        self.assertIn(Path(selected).name, view['NameMap'])
        self.assertEqual(view['NamesReferencedFromExportDataCount'], len(view['NameMap']))
        actual = view['Imports'][-cave.property_data(component, 'StaticMesh')['Value'] - 1]
        self.assertEqual(actual['ObjectName'], Path(selected).name)
        self.assertEqual(view['Imports'][-actual['OuterIndex'] - 1]['ObjectName'], selected)


if __name__ == '__main__': unittest.main()
