"""Real builder routing with explicit synthetic native vendor inventory fixtures."""
import ast
import copy
import unittest
from test_resonance_caves import cave, vision
from test_existing_visions import installer, fina_installer, ROOT


class ShopRoutingTests(unittest.TestCase):
    def fixture(self):
        item = {'ItemId': 10, 'Condition': '{progress:0}>2', 'MaxOrderNum': -1, 'PriceRatio': 1.0}
        shops = {name: {'ShopID': sid, 'ItemList': [copy.deepcopy(item), dict(item, ItemId=-1)], 'SellItemList': []}
                 for name, sid in [('Items', 1), ('Weapons', 2001), ('Armor', 4001)]}
        combined = {'Gear': {'ID': 10001, 'ToolShopID': -1, 'WeaponShopID': 2001, 'ArmorShopID': 4001, 'AccessoryShopID': -1}}
        data = {'Shop/DT_ShopList': shops, 'Shop/DT_VariousShopsList': combined}
        return data, lambda rel: copy.deepcopy(data[rel])

    def shop(self, uid, location):
        return {'id': uid, 'studioAcquisition': {'version': 2, 'random': False, 'hideSpoilers': True,
                                                'location': location, 'cave': None}}

    def test_weapon_vendor_default_combined_and_cave_are_routed_without_duplicates(self):
        original, rows = self.fixture(); before = copy.deepcopy(original)
        units = [self.shop(13520, 'shop_2001'), {'id': 13521}, self.shop(13522, 'shop_10001'), vision(13523)]
        operations = cave.prepare_shops({}, units, rows)
        edits = {e['row']: e['set']['ItemList'] for e in operations['Shop/DT_ShopList']['set']}
        self.assertEqual(set(edits), {'Items', 'Weapons'})
        self.assertEqual([i['ItemId'] for i in edits['Weapons']], [10, 13520, 13522])
        self.assertEqual([i['ItemId'] for i in edits['Items']], [10, 13521])
        self.assertEqual(edits['Weapons'][0], original['Shop/DT_ShopList']['Weapons']['ItemList'][0])
        self.assertEqual(edits['Weapons'][1]['MaxOrderNum'], 1)
        self.assertEqual(edits['Weapons'][1]['Condition'], '')
        self.assertEqual(original, before)

    def test_missing_duplicate_and_unavailable_combined_vendors_fail_before_mutation(self):
        original, rows = self.fixture()
        for units in ([self.shop(13520, 'shop_99999')], [self.shop(13520, 'shop_1')]*2,
                      [self.shop(13520, 'wrong')]):
            operations = {'keep': {'unrelated': True}}; before = copy.deepcopy(operations)
            with self.assertRaises(ValueError): cave.prepare_shops(operations, units, rows)
            self.assertEqual(operations, before)
        original['Shop/DT_VariousShopsList']['Gear']['WeaponShopID'] = -1
        original['Shop/DT_VariousShopsList']['Gear']['ArmorShopID'] = -1
        with self.assertRaises(ValueError): cave.prepare_shops({}, [self.shop(13520, 'shop_10001')], rows)

    def test_native_visions_are_preserved_and_installed_builder_has_no_default_shop_write(self):
        unit = self.shop(13110, 'shop_2001'); unit['native'] = {'id': 13110}
        self.assertEqual(cave.prepare_shops({}, [unit], lambda _: self.fail('Native acquisition touched shop')), {})
        raw = (ROOT/'scripts/fixtures/crystal_fina/make_vision_mod.py').read_bytes()
        tree = ast.parse(installer.hook_builder(fina_installer.hook_builder(raw)))
        calls = [ast.unparse(n) for n in ast.walk(tree) if isinstance(n, ast.Call)]
        self.assertIn('_ffr_crystal_cave.prepare_shops(tables, UNITS, rows)', calls)
        self.assertFalse(any(c.startswith("tbl('Shop/DT_ShopList')['set'].append") for c in calls))
