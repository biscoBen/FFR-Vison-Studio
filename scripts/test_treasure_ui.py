"""Execute the emitted Kismet getter against captured native collection identities."""
import copy
import unittest
from pathlib import Path
import tempfile
from unittest import mock

import build_treasure_ui as ui
import _ffr_field_leader as leader
import _ffr_testing as testing


def getter(asset, map_id, opened):
    function = next(e for e in asset['Exports'] if e['ObjectName'] == 'GetStudioRemainingText')
    variables, queried = {}, []
    def evaluate(node):
        op = node['$type'].split('.')[-1].split(',')[0]
        if op in ('EX_IntConst', 'EX_StringConst'): return node['Value']
        if op == 'EX_LocalVariable': return variables[node['Variable']['New']['Path'][0]]
        if op != 'EX_CallMath': raise AssertionError(op)
        name = asset['Imports'][-node['StackNode']-1]['ObjectName']
        args = [evaluate(a) for a in node['Parameters']]
        if name == 'GetCurrentMapId': return map_id
        if name == 'IsOpenTreasureBox':
            queried.append(tuple(args)); return tuple(args) in opened
        if name == 'EqualEqual_IntInt': return args[0] == args[1]
        if name == 'BooleanOR': return args[0] or args[1]
        if name == 'Add_IntInt': return args[0] + args[1]
        if name == 'SelectInt': return args[0] if args[2] else args[1]
        if name in ('Conv_IntToString', 'Conv_StringToText'): return str(args[0])
        if name == 'Concat_StrStr': return ''.join(args)
        raise AssertionError('A saved-state counter cannot call ' + name)
    code = function['ScriptBytecode']; offsets = {}; at = 0
    for index, instruction in enumerate(code): offsets[at] = index; at += ui.size(instruction)
    assert at == function['ScriptBytecodeSize']
    pc = 0
    while pc < len(code):
        node = code[pc]; op = node['$type'].split('.')[-1].split(',')[0]
        if op == 'EX_Let': variables[node['Variable']['Variable']['New']['Path'][0]] = evaluate(node['Expression'])
        elif op == 'EX_JumpIfNot' and not evaluate(node['BooleanExpression']):
            pc = offsets[node['CodeOffset']]; continue
        elif op == 'EX_Return': return evaluate(node['ReturnExpression']), queried
        pc += 1
    raise AssertionError('Getter did not return text')


class CounterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.native = ui.load_native(); cls.asset = ui.counter_widget(cls.native)

    def test_whole_earth_shrine_includes_the_other_map_and_existing_collections(self):
        for map_id in (3000, 3001):
            text, queries = getter(self.asset, map_id, set())
            self.assertEqual(text, 'Items left: 8')
            self.assertEqual({p[0] for p in queries}, {3000, 3001})
            text, _ = getter(self.asset, map_id, {(3000, 14)})
            self.assertEqual(text, 'Items left: 7')
        # Native chest table ID 2 belongs to unique ID 14, never query table ID 2.
        self.assertNotIn((3000, 2), queries)

    def test_glowing_pickups_and_fragments_share_the_saved_open_predicate(self):
        locations = [l for g in self.native['catalog']['groups'] for l in g['locations']]
        self.assertEqual({kind: sum(l['kind'] == kind for l in locations)
                          for kind in ('chest','pickup','fragment')},
                         {'chest':134,'pickup':3,'fragment':64})
        text, queries = getter(self.asset, 3061, {(3060, 71), (3060, 78)})
        self.assertEqual(text, 'Items left: 5')
        self.assertEqual(len(queries), 7)

    def test_alias_uses_saved_namespace_and_excludes_decorative_open_chests(self):
        self.assertEqual(getter(self.asset, 3020, set())[0], 'Items left: 9')
        self.assertEqual(getter(self.asset, 3020, {(2002,53)})[0], 'Items left: 8')
        self.assertEqual(getter(self.asset, 3020, {(3020,53)})[0], 'Items left: 9')
        queries = getter(self.asset, 3020, set())[1]
        self.assertTrue(all(saved_map == 2002 for saved_map, _ in queries))
        self.assertTrue({50,52,54}.isdisjoint(uid for _,uid in queries))

    def test_complete_groups_reach_zero_without_counting_hidden_floors_twice(self):
        self.assertEqual(len(self.native['catalog']['coverage']),108)
        for group in self.native['catalog']['groups']:
            opened = {(l['map'],l['uid']) for l in group['locations']}
            for map_id in group['maps']:
                text, queries = getter(self.asset, map_id, opened)
                self.assertEqual(text, 'Items left: 0')
                self.assertEqual(set(queries), opened)
                self.assertEqual(len(queries), len(set(queries)))

    def test_unknown_world_and_town_maps_have_no_invented_zero(self):
        for map_id in (-1,1000,2011,999999): self.assertEqual(getter(self.asset,map_id,set()),('',[]))

    def test_missing_floor_or_unreviewed_condition_fails_instead_of_partial_total(self):
        broken = copy.deepcopy(self.native)
        del broken['levels']['Map/Dng/01Gra/01Gra_40/GD/Dng_01Gra_40_GD.umap']
        with self.assertRaises(KeyError): ui.catalog_from_native(broken)
        broken = copy.deepcopy(self.native)
        floor = broken['levels']['Map/Dng/01Gra/01Gra_40/GD/Dng_01Gra_40_GD.umap']
        floor['collectibles'][0]['properties']['m_FlagCondition'] = 'unknown story gate'
        with self.assertRaisesRegex(ValueError,'conditional'): ui.catalog_from_native(broken)

    def test_native_functions_and_unrotated_minimap_root_are_preserved(self):
        original = self.native['miniMap']
        for before, after in zip(original['Exports'], self.asset['Exports']):
            self.assertEqual(before.get('ScriptBytecode'),after.get('ScriptBytecode'))
            if before['ObjectName'] not in ('Overlay_4','WBP_MiniMap_C'):
                self.assertEqual(before,after)
        root = next(e for e in self.asset['Exports'] if e['ObjectName']=='Overlay_4')
        slot = self.asset['Exports'][ui.field(root,'Slots')['Value'][-1]['Value']-1]
        self.assertEqual(ui.field(slot,'VerticalAlignment')['Value'],'VAlign_Bottom')
        self.assertEqual(ui.field(slot,'HorizontalAlignment')['Value'],'HAlign_Left')
        self.assertEqual(slot['OuterIndex'],27)

    def test_status_widget_has_plain_text_explicit_font_and_no_input_code(self):
        asset = ui.status_widget(self.native)
        self.assertEqual(len(asset['Exports']),4)
        cls = asset['Exports'][2]
        self.assertEqual(cls['FuncMap'],[]);self.assertEqual(cls['Children'],[])
        self.assertEqual(cls['ScriptBytecode'],[])
        label = asset['Exports'][0]
        self.assertEqual(asset['Imports'][-label['ClassIndex']-1]['ObjectName'],'TextBlock')
        font = ui.field(label,'Font')['Value']
        self.assertEqual(next(p for p in font if p['Name']=='Size')['Value'],18.0)
        self.assertEqual(next(p for p in font if p['Name']=='Size')['$type'],
                         'UAssetAPI.PropertyTypes.Objects.FloatPropertyData, UAssetAPI')

    def test_counter_binding_has_the_reflected_widget_property_and_text_return(self):
        cls = next(e for e in self.asset['Exports'] if e['ObjectName']=='WBP_MiniMap_C')
        binding = ui.field(cls,'Bindings')['Value'][0]['Value']
        target = next(p['Value'] for p in binding if p['Name']=='ObjectName')
        prop = next(p for p in cls['LoadedProperties'] if p['Name']==target)
        self.assertEqual(self.asset['Imports'][-prop['PropertyClass']-1]['ObjectName'],'TextBlock')
        name = next(p['Value'] for p in binding if p['Name']=='FunctionName')
        function = next(e for e in self.asset['Exports'] if e['ObjectName']==name)
        returned = next(p for p in function['LoadedProperties'] if 'CPF_ReturnParm' in p['PropertyFlags'])
        self.assertEqual(returned['SerializedType'],'TextProperty')
        self.assertIn('FUNC_BlueprintPure',function['FunctionFlags'])

    def test_control_build_copies_only_precompiled_widget_and_off_needs_none(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); out=root/'out';setting=root/testing.CONFIG
            setting.parent.mkdir(parents=True);setting.write_text('{"schema":1,"maxMr":false,"autoBattle":true}')
            with mock.patch('_ffr_overworld.runtime_config',return_value={'schema':1,'cycling':0,'actors':{},'defaults':{}}):
                leader.build([],{'ROOT':root,'OUT':out,'rows':lambda _:self.fail('No game extraction/conversion')})
            self.assertEqual({p.relative_to(out).as_posix() for p in out.rglob('*') if p.is_file()},set(leader.HUD_ASSETS))
            self.assertTrue(all(p.stat().st_size for p in out.rglob('*') if p.is_file()))
            setting.write_text('{"schema":1,"maxMr":false,"autoBattle":false}')
            leader.build([],{'ROOT':root,'OUT':root/'off','rows':lambda _:self.fail('No game reads')})
            self.assertFalse((root/'off').exists())


if __name__ == '__main__': unittest.main()
