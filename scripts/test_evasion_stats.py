"""Selected-parameter correctness, native layout preservation and delivery paths."""
import copy
import gzip
import hashlib
import io
import itertools
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock
import zipfile

from lupa.lua54 import LuaRuntime
from test_existing_visions import ROOT
from test_local_map import clean
import build_evasion_ui as build
import _ffr_evasion_stats as assets
import _ffr_field_leader as leader
import _ffr_runtime_loader as loader
import _ffr_testing as testing
from _ffr_crystal_cave import semantic

PAYLOAD = ROOT / 'assets/existing_visions/payload'


def fixture(name):
    return json.loads(gzip.decompress((ROOT/'scripts/fixtures'/name).read_bytes()))


class EvasionAssetsTests(unittest.TestCase):
    def test_native_bytecode_grid_stat_types_and_bindings_preserved_after_serialized_readback(self):
        native = fixture('evasion_ui_native.json.gz')
        original = copy.deepcopy(native)
        authored = build.author(native)
        readback = fixture('evasion_ui_readback.json.gz')
        self.assertEqual(native, original)
        for i, export in enumerate(original['widget']['Exports']):
            if export['ObjectName'] not in ('Overlay_0', 'WidgetTree', 'WBP_UnitParam_Detail_C'):
                self.assertEqual(clean(export.get('Data')), clean(readback['Exports'][i].get('Data')))
                if 'ScriptBytecode' in export:
                    self.assertEqual(export['ScriptBytecode'], readback['Exports'][i]['ScriptBytecode'])
        for a, b in zip(authored['Exports'], readback['Exports']):
            self.assertEqual(semantic(a.get('Data')), semantic(b.get('Data')))
        original_class=original['widget']['Exports'][24]
        cls=readback['Exports'][24]
        self.assertEqual(original_class['LoadedProperties'],cls['LoadedProperties'][:-4])
        self.assertEqual(original_class['FuncMap'],cls['FuncMap'])
        self.assertEqual(original_class['Children'],cls['Children'])
        self.assertEqual([p['Name'] for p in cls['LoadedProperties'][-4:]],
                         ['Text_StudioPhysicalEvasion','Text_StudioPhysicalEvasionValue',
                          'Text_StudioMagicalEvasion','Text_StudioMagicalEvasionValue'])
        self.assertEqual(build.field(readback['Exports'][25],'RootWidget')['Value'],27)
        for e in readback['Exports'][30:34:2]+readback['Exports'][36:40:2]:
            self.assertEqual(build.field(e,'Visibility')['Value'],'Collapsed')
            self.assertEqual(e['OuterIndex'],26)
            style=readback['Imports'][-build.field(e,'Style')['Value']-1]
            is_value=e['ObjectName'].endswith('Value')
            self.assertEqual(style['ObjectName'],'BP_SystemTextStyle_PramNUM_C' if is_value else 'BP_SystemTextStyle_C')
            if is_value:
                self.assertEqual(build.field(e,'Justification')['Value'],'Right')
                self.assertEqual(semantic(build.field(e,'Font')),semantic(build.field(native['number'],'Font')))
            else:
                self.assertEqual(build.field(e,'Text')['CultureInvariantString'],
                                 'Phys. Eva' if 'Physical' in e['ObjectName'] else 'Mag. Eva')
                self.assertEqual(semantic(build.field(e,'Font')),semantic(build.field(native['label'],'Font')))
        self.assertEqual(len(readback['Exports']),40)

    def test_packaged_native_assets_stage_exactly_and_reject_tampering(self):
        with tempfile.TemporaryDirectory() as directory:
            assets.stage(directory)
            for name,digest in assets.ASSETS.items():
                self.assertEqual(hashlib.sha256((Path(directory)/name).read_bytes()).hexdigest(),digest)
        with zipfile.ZipFile(PAYLOAD/'evasion_stats.zip') as z:
            self.assertEqual(set(z.namelist()),set(assets.ASSETS))
            files={n:z.read(n) for n in z.namelist()}
        buffer=io.BytesIO()
        with zipfile.ZipFile(buffer,'w') as z:
            for n,data in files.items(): z.writestr(n,data+b'changed')
        with self.assertRaises(ValueError): assets.validate(buffer.getvalue())

    def test_opt_in_persists_and_builds_without_a_roster_with_loader_required(self):
        self.assertFalse(testing.validate_settings({'schema':1,'maxMr':False})['evasionStats'])
        for value in (1,'true',None):
            with self.assertRaises(ValueError):testing.validate_settings({'schema':1,'maxMr':False,'evasionStats':value})
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);p=root/testing.CONFIG;p.parent.mkdir(parents=True)
            for enabled in (True,False):
                p.write_text(json.dumps({'schema':1,'maxMr':False,'evasionStats':enabled}))
                self.assertEqual(loader.status(root,root/'game',[])['required'],enabled)
                out=root/str(enabled)
                leader.build([],{'ROOT':root,'OUT':out,'rows':lambda _:self.fail('No game extraction needed')})
                files=json.loads((root/leader.STAGE).read_bytes())['files']
                self.assertEqual('Scripts/main.lua' in files,enabled)
                self.assertEqual((out/next(iter(assets.ASSETS))).is_file(),enabled)

    def test_combined_generated_runtime_starts_with_esper_mastery_and_each_control_combination(self):
        import _ffr_overworld as overworld
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);p=root/testing.CONFIG;p.parent.mkdir(parents=True)
            for local_map,encounters,auto in itertools.product((False,True),repeat=3):
                p.write_text(json.dumps({'schema':1,'maxMr':False,'evasionStats':True,
                    'localMap':local_map,'noEncounters':encounters,'autoBattle':auto}))
                units=[{'id':13515,'synchro':[[['PassiveSkill',1960,-1]]]}]
                with mock.patch.object(overworld,'runtime_config',return_value={'schema':1,'cycling':0,'actors':{},'defaults':{}}):
                    leader.build(units,{'ROOT':root,'OUT':root/'out','rows':lambda _:[]})
                files=json.loads((root/leader.STAGE).read_bytes())['files']
                lua=LuaRuntime()
                self.assertTrue(lua.eval('function(code) return load(code) ~= nil end')(files['Scripts/main.lua']))
                self.assertIn('evasionStats',files['Scripts/config.lua'])
                lua.execute('''
                    Key={F7=118,F9=120};loops={}
                    function print() end
                    function RegisterHook() end
                    function RegisterKeyBind() end
                    function NotifyOnNewObject() end
                    function ExecuteInGameThread(fn) fn() end
                    function StaticFindObject() return nil end
                    function LoopInGameThreadWithDelay(ms,fn) loops[#loops+1]={ms,fn};return #loops end
                ''')
                lua.execute('package.preload.config=function() '+files['Scripts/config.lua']+' end')
                lua.execute(files['Scripts/main.lua'])
                lua.execute('assert(FFRStudioEvasionStats and FFRStudioEsperMastery)')


class EvasionRuntimeTests(unittest.TestCase):
    def runtime(self):
        lua=LuaRuntime()
        lua.execute((ROOT/'scripts/fixtures/evasion_stats_runtime.lua').read_text())
        lua.execute((PAYLOAD/'evasion_stats.lua').read_text())
        lua.execute('ready()')
        return lua

    def test_live_effect_types_stack_by_damage_type_and_cap_overrides_are_read_fresh(self):
        lua=self.runtime()
        lua.execute('''
            menu.effects={param(effect(15,1)),param(effect(20,1)),param(effect(25,2)),param(effect(10,0))}
            show(); values('45','35')
            menu.effects[#menu.effects+1]=effect(50,1);show();values('75','35')
            capRow.evasionLimit=60;show();values('60','35')
            capRow.evasionLimit=90;show();values('90','35')
        ''')

    def test_high_raw_values_use_the_native_cap_and_decoy_uses_its_physical_bypass(self):
        lua=self.runtime()
        lua.execute('''
            menu.effects={effect(500,1),effect(500,2)};show();values('75','75')
            capRow.evasionLimit=50;show();values('50','50')
            menu.effects[#menu.effects+1]=effect(nil,nil,true);show();values('100','50')
            table.remove(menu.effects);show();values('50','50')
        ''')

    def test_selected_menu_and_battle_parameters_never_borrow_another_character_or_snapshot(self):
        lua=self.runtime()
        lua.execute('''
            menu.effects={effect(15,1)};battle.effects={effect(60,2)}
            show();values('15','0')
            vm.class='/Script/mucha.CPP_VM_BtlUnitParam';vm.BtlUnitParam=battle
            show('SetCPP_VM_UnitParam');values('0','60')
            battle.effects={effect(50,1),effect(50,2)};show();values('50','50')
            battle.effects={};show();values('0','0')
            battle.dead=true;show();hidden()
            vm.class=nil;show('SetUnitId');values('15','0')
            vm.UnitParam=parameter(false);vm.UnitParam.effects={effect(20,2)}
            show('SetItemId');values('0','20')
        ''')

    def test_garbage_is_ignored_but_lifetime_and_duplicates_follow_the_native_active_list(self):
        lua=self.runtime()
        lua.execute('''
            local garbage=effect(500,1);garbage.flags=0x40000000
            local dying=effect(500,2);dying.flags=0x8000
            local shared=effect(20,1);shared.life=0
            menu.effects={shared,shared,garbage,dying,effect(10,255)};show();values('40','0')
            menu.effects={};show();values('0','0')
        ''')

    def test_failed_reads_hide_both_stale_values_and_do_not_turn_struct_memory_into_uobjects(self):
        lua=self.runtime()
        lua.execute('''
            menu.effects={effect(20,1)};show();values('20','0')
            capRow.evasionLimit='75';show();hidden();assert(#logs>1)
            capRow.evasionLimit=75;show();values('20','0')
            schema.name='ScriptStruct /Wrong';show();hidden()
            schema.name='ScriptStruct /Script/mucha.UNIT_PARAMETER_CALC_DATA'
            show();values('20','0');menu.relation=2;show();hidden()
            menu.relation=1;show();values('20','0');vm.dead=true;show();hidden()
        ''')

    def test_signature_mismatch_fails_closed_and_loading_does_not_duplicate_hooks(self):
        lua=LuaRuntime()
        lua.execute((ROOT/'scripts/fixtures/evasion_stats_runtime.lua').read_text())
        lua.execute((PAYLOAD/'evasion_stats.lua').read_text())
        lua.execute("functions['/Script/mucha.CPP_ContEffect:GetEffectData']={'IntProperty'};ready()")
        lua.execute('''
            discover(widgetType);discover(widgetType);drain()
            show();hidden();assert(#logs>1)
        ''')

    def test_first_loaded_page_is_refreshed_and_float32_sum_matches_native_rounding(self):
        lua=self.runtime()
        lua.execute('''
            values('0','0')
            menu.effects={effect(16777216,1),effect(1,1),effect(-16777216,1)}
            show();values('0','0')
        ''')


if __name__=='__main__':unittest.main()
