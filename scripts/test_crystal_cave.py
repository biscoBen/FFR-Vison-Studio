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
