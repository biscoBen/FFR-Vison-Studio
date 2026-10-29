"""Movement-only encounter recipes; production maps and scripted battle preservation."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from test_existing_visions import ROOT
import _ffr_testing as testing
import _ffr_game_tables as native


class NoEncountersTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        self.tables={
            'Map/MapData/DT_MapData_01Gra': {'cave': {'ID': 10,'doMovementEncount': True,'encountGroupId': 20,
                'doEncountCondition':'story condition','startupEventList':[{'event':'boss'}]},
                'town': {'ID':11,'doMovementEncount':False,'encountGroupId':-1,'startupEventList':[]}},
            'Map/MapData/DT_MapData_05Old': {'dungeon': {'ID':50,'doMovementEncount':True,'encountGroupId':70}},
            'Map/MapData/DT_MapData_00Com_Prod': {'world':{'ID':100,'doMovementEncount':True,'encountGroupId':200}},
            'Map/CDT_MapData_Prod': {'cave':{'ID':10,'doMovementEncount':True,'encountGroupId':20}},
        }
        listing=self.root/'extracted/utoc_filelist.tsv';listing.parent.mkdir(parents=True)
        listing.write_text('\n'.join(native.PREFIX + rel + '.uasset' for rel in self.tables))
        p=self.root/testing.CONFIG;p.parent.mkdir(parents=True);p.write_text(json.dumps({'schema':1,'maxMr':False,'noEncounters':True}))

    def prepare(self):
        result={}
        with mock.patch('_ffr_crystal_cave.prepare'),mock.patch('_ffr_shrine_challenges.prepare'):
            testing.prepare(result,[],self.root,lambda rel:copy.deepcopy(self.tables[rel]))
        return result

    def test_hotkey_feature_preserves_all_native_maps_and_scripted_encounters(self):
        original=copy.deepcopy(self.tables)
        self.assertEqual(self.prepare(),{})
        self.assertEqual(self.tables,original)


    def test_disabling_produces_no_encounter_edits_and_legacy_default_is_off(self):
        (self.root/testing.CONFIG).write_text(json.dumps({'schema':1,'maxMr':False}))
        self.assertFalse(testing.settings(self.root)['noEncounters'])
        self.assertEqual(self.prepare(),{})
        with self.assertRaises(ValueError):testing.validate_settings({'schema':1,'maxMr':False,'noEncounters':1})

    def test_runtime_needs_no_map_extraction_and_stages_without_any_visions(self):
        import _ffr_field_leader as leader
        calls=[]
        with mock.patch('_ffr_fina_cinematic.ensure_assets'):
            testing.ensure_assets(self.root,calls.append)
        self.assertEqual(calls,[])
        leader.build([],{'ROOT':self.root,'rows':lambda _:self.fail('No game assets needed')})
        payload=json.loads((self.root/leader.STAGE).read_bytes())
        self.assertIn('encounterToggle',payload['files']['Scripts/config.lua'])
        self.assertIn('RegisterKeyBind(Key.F7',payload['files']['Scripts/main.lua'])
        (self.root/testing.CONFIG).write_text(json.dumps({'schema':1,'maxMr':False,'noEncounters':False}))
        leader.build([],{'ROOT':self.root,'rows':lambda _:self.fail('No game assets needed')})
        self.assertEqual(json.loads((self.root/leader.STAGE).read_bytes())['files'],{})

    def test_keyboard_controller_hud_and_native_state_restoration(self):
        from lupa.lua54 import LuaRuntime
        lua=LuaRuntime()
        lua.execute((ROOT/'scripts/fixtures/encounter_toggle_runtime.lua').read_text())
        # Drive the factory with the captured native row/UF metadata, including
        # the real equipment passive, instead of inventing an encounter API.
        source=json.loads((ROOT/'scripts/fixtures/encounter_control_native.json').read_bytes())
        def value(v):
            if isinstance(v,dict):return lua.table_from({k:value(x) for k,x in v.items()})
            if isinstance(v,list):return lua.table_from([value(x) for x in v])
            return v
        lua.globals().nativeSource=value(source)
        lua.execute('''
            assert(nativeSource.effect.EffectType=='EncountRatio' and nativeSource.effect.ParamList[1]==0)
            assert(nativeSource.effect.effectEndActionNum==-1)
            assert(nativeSource.passive.ID==1052 and nativeSource.passive.effectBundleList[1].effectId==nativeSource.effect.ID)
        ''')
        helper=(ROOT/'assets/existing_visions/payload/status_hud.lua').read_text()
        code=(ROOT/'assets/existing_visions/payload/encounter_toggle.lua').read_text()
        lua.execute('local create_status_hud=(function()\n'+helper+'\nend)();\n'+code)
        lua.globals().tests()
        messages=list(lua.globals().messages.values())
        self.assertTrue(any('Owned target=' in line for line in messages))
        self.assertTrue(any('source=playable' in line for line in messages))
        self.assertTrue(any('Native battle entry while OFF' in line for line in messages))

    def test_encounter_only_install_requests_the_optional_runtime(self):
        import _ffr_runtime_loader as runtime
        game=self.root/'game';game.mkdir()
        self.assertTrue(runtime.status(self.root,game,[])['required'])
        self.assertFalse(runtime.status(self.root,game,[])['ready'])


if __name__=='__main__':unittest.main()
