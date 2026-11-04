"""Native asset preservation and executable controller-map lifecycle checks."""
import copy
import gzip
import hashlib
import itertools
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock
import zipfile

from lupa.lua54 import LuaRuntime
from test_existing_visions import ROOT
import build_local_map as build
import _ffr_field_leader as leader
import _ffr_local_map as local_map
import _ffr_runtime_loader as loader
import _ffr_testing as testing

PAYLOAD = ROOT / 'assets/existing_visions/payload'


def load_fixture(name):
    return json.loads(gzip.decompress((ROOT/'scripts/fixtures'/name).read_bytes()))


def clean(value):
    # Native unversioned zero masks omit values that the JSON writer expands.
    if isinstance(value, dict): return {k: clean(v) for k,v in value.items() if k != 'IsZero'}
    if isinstance(value, list): return [clean(v) for v in value]
    if value in ('+0','-0'): return 0.0
    if isinstance(value,float): return round(value,6)
    return value


class LocalMapAssetsTests(unittest.TestCase):
    def test_native_readback_matches_author_and_preserves_all_original_settings(self):
        native = load_fixture('local_map_native.json.gz')
        authored = build.author(native)
        readback = load_fixture('local_map_readback.json.gz')['assets']
        for name,asset in authored.items():
            self.assertEqual(clean(asset['Exports'][0]['Data']), clean(readback[name]['Exports'][0]['Data']))
            self.assertEqual(asset['Imports'],native['assets'][name]['Imports'])
            self.assertEqual(asset['Exports'][0]['ObjectName'],name)
        properties=readback['DA_MiniMapProperty']['Exports'][0]['Data']
        default=build.field(properties,'DefaultProperty')['Value']
        steps=build.field(build.field(default,'DisplayStepPropertySet')['Value'],'PropertyList')['Value']
        self.assertEqual(len(steps),3)
        self.assertEqual([build.field(p['Value'],'bDisplay')['Value'] for p in steps],[True,True,False])
        self.assertEqual(build.field(build.field(steps[1]['Value'],'ViewPropertyTag')['Value'],'TagName')['Value'],build.FULL)
        original=copy.deepcopy(native['assets']['DA_MiniMapProperty']['Exports'][0]['Data'])
        restored=copy.deepcopy(properties)
        array=build.field(build.field(build.field(restored,'DefaultProperty')['Value'],'DisplayStepPropertySet')['Value'],'PropertyList')['Value']
        del array[1]; array[1]['Name']='1'
        self.assertEqual(clean(restored),clean(original)) # Includes world AND airship overrides.
        views=build.field(readback['DA_MiniMapViewProperty']['Exports'][0]['Data'],'PropertyMap')['Value']
        old_views=build.field(native['assets']['DA_MiniMapViewProperty']['Exports'][0]['Data'],'PropertyMap')['Value']
        self.assertEqual(clean(views[:-1]),clean(old_views))
        key,full=views[-1]
        self.assertEqual(build.field(key['Value'],'TagName')['Value'],build.FULL)
        self.assertEqual(build.field(full['Value'],'OriginType')['Value'],'Image')
        self.assertFalse(build.field(full['Value'],'bUseSaveZoomAlpha')['Value'])
        self.assertEqual(len(views),5)

    def test_staged_assets_are_exactly_the_four_checked_native_packages(self):
        with tempfile.TemporaryDirectory() as directory:
            local_map.stage(directory)
            for name,digest in local_map.ASSETS.items():
                self.assertEqual(hashlib.sha256((Path(directory)/name).read_bytes()).hexdigest(),digest)
            self.assertEqual(len(local_map.ASSETS),4)
            self.assertEqual({p.suffix for p in Path(directory).rglob('*') if p.is_file()},{'.uasset','.uexp'})
        with zipfile.ZipFile(PAYLOAD/'local_map.zip') as archive:
            self.assertEqual(set(archive.namelist()),set(local_map.ASSETS))

    def test_setting_is_opt_in_strict_and_requires_the_owned_loader(self):
        self.assertFalse(testing.validate_settings({'schema':1,'maxMr':False})['localMap'])
        for invalid in (1,'true',None):
            with self.assertRaises(ValueError): testing.validate_settings({'schema':1,'maxMr':False,'localMap':invalid})
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); p=root/testing.CONFIG;p.parent.mkdir(parents=True)
            p.write_text(json.dumps({'schema':1,'maxMr':False,'localMap':True}))
            self.assertTrue(loader.status(root,root/'game',[])['required'])

    def test_build_stages_native_assets_and_runtime_together_then_disables_cleanly(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); p=root/testing.CONFIG;p.parent.mkdir(parents=True)
            for enabled in (True,False):
                out=root/str(enabled)
                p.write_text(json.dumps({'schema':1,'maxMr':False,'localMap':enabled}))
                leader.build([],{'ROOT':root,'OUT':out,'rows':lambda _:self.fail('No game extraction for local map')})
                files=json.loads((root/leader.STAGE).read_bytes())['files']
                self.assertEqual('Scripts/main.lua' in files,enabled)
                self.assertEqual((out/next(iter(local_map.ASSETS))).is_file(),enabled)


class LocalMapRuntimeTests(unittest.TestCase):
    def runtime(self):
        lua=LuaRuntime()
        lua.execute((ROOT/'scripts/fixtures/local_map_runtime.lua').read_text())
        lua.execute((PAYLOAD/'local_map.lua').read_text())
        lua.execute('ready()')
        return lua

    def test_entire_zone_fits_at_any_rotation_across_different_bounds_and_ui_sizes(self):
        lua=self.runtime()
        lua.execute('''
            for _,size in ipairs({{20000,10000},{1000,90000},{200,200}}) do
                for _,range in ipairs({320,640,900}) do
                    vm.width,vm.height=size[1],size[2]; vm.rangeX,vm.rangeY=range,range
                    show()
                    local scale=widget.paint
                    local x,y=vm.width*vm.projection*scale/2,vm.height*vm.projection*scale/2
                    for angle=0,360,15 do
                        local rad=math.rad(angle)
                        local px,py=x*math.cos(rad)-y*math.sin(rad),x*math.sin(rad)+y*math.cos(rad)
                        assert(math.sqrt(px*px+py*py)<=range*.45+1e-7,'Image clipped by native mask')
                    end
                    assert(vm.ZoomProperty.ScaleInterval.min==scale and vm.ZoomProperty.ScaleInterval.max==scale)
                    assert(not vm.ZoomProperty.bSaveZoom and vm.alpha==0)
                end
            end
            assert(vm.zoomCalls==9 and widget.paints==18,'Reentry must be bounded')
            assert(#messages==1)
        ''')

    def test_small_hidden_world_maps_and_unrelated_widgets_are_untouched(self):
        lua=self.runtime()
        lua.execute('''
            for _,tag in ipairs({'UI.Field.MiniMap.View.Decrale.Instance','None','UI.Field.MiniMap.View.Decrale.World','UI.Field.MiniMap.View.Decrale.Wide'}) do
                vm.tag=tag; show(); assert(not widget.paint and not vm.zoomCalls)
            end
            vm.tag='UI.Field.MiniMap.View.Decrale'; vm.world=true; show(); assert(not widget.paint)
            vm.world=false; class_name('WidgetBlueprintGeneratedClass /Game/Other'); show(); assert(not widget.paint)
        ''')

    def test_native_settings_and_remembered_zoom_are_restored_after_full_view(self):
        lua=self.runtime()
        lua.execute('''
            show(); assert(widget.paint<1)
            vm.tag='UI.Field.MiniMap.View.Decrale.Instance'; show()
            assert(vm.restores==1 and vm.alpha==.7 and vm.ZoomProperty.bSaveZoom)
            assert(vm.ZoomProperty.ScaleInterval.min==1 and widget.paint==1)
            show(); assert(vm.restores==1)
        ''')

    def test_destroying_or_missing_objects_do_not_read_map_properties(self):
        lua=self.runtime()
        lua.execute('''
            widget.destroying=true; show(); assert(not vm.zoomCalls); widget.destroying=false
            vm.destroying=true; show(); assert(not vm.zoomCalls); vm.destroying=false
            local saved=widget.MiniMapVM; widget.MiniMapVM=nil; show(); assert(not vm.zoomCalls)
            widget.MiniMapVM=saved; vm.invalid=true; show(); assert(not vm.zoomCalls)
        ''')

    def test_invalid_bounds_fall_back_without_saving_zoom_or_repeated_logging(self):
        for field,value in [('width','0'),('height','-10'),('projection','0/0'),('rangeX','math.huge')]:
            lua=self.runtime()
            lua.execute(f"vm.{field}={value}; show(); assert(vm.fallback==1 and not vm.zoomCalls and vm.ZoomProperty.bSaveZoom)")
            lua.execute("vm.tag='UI.Field.MiniMap.View.Decrale'; show(); assert(vm.fallback==2 and #messages==2)")

    def test_reloaded_blueprint_functions_rebind_but_discovery_does_not_duplicate(self):
        lua=self.runtime()
        lua.execute('''
            local count=0; for _ in pairs(hooks) do count=count+1 end; assert(count==2)
            discover(); discover(); drain(); show(); assert(vm.zoomCalls==1)
        ''')

    def test_combined_generated_script_starts_with_each_runtime_feature_combination(self):
        import _ffr_fina_battle as fina
        import _ffr_overworld as overworld
        # Test actual concatenation, including only-map and every-feature builds.
        for encounter,auto,esper,film,walking in itertools.product((False,True),repeat=5):
            with self.subTest(encounter=encounter,auto=auto,esper=esper,film=film,walking=walking):
                with tempfile.TemporaryDirectory() as d:
                    root=Path(d); config=root/testing.CONFIG; config.parent.mkdir(parents=True)
                    config.write_text(json.dumps({'schema':1,'maxMr':False,'localMap':True,'noEncounters':encounter,'autoBattle':auto}))
                    units=[]
                    if esper: units.append({'id':13515,'synchro':[[['PassiveSkill',1960,-1]]]})
                    if film:
                        units.append({'id':13503,'ffbe':{'id':fina.SPRITE,'source':'CUSTOM'}})
                        native=root/'build/crystal-fina-battle/runtime.json'; native.parent.mkdir(parents=True)
                        native.write_text(json.dumps({'schema':1,'id':13503,'attackPlayRate':.8}))
                    if walking: units.append({'id':1001,'party':True,'overworld':{'version':1,'model':'native_party_1006'}})
                    with mock.patch.object(overworld,'runtime_config',return_value={'schema':1,'cycling':0,'actors':{},'defaults':{}}):
                        leader.build(units,{'ROOT':root,'rows':lambda _:self.fail('No native extraction')})
                    files=json.loads((root/leader.STAGE).read_bytes())['files']
                lua=LuaRuntime()
                lua.execute('''
                    Key={F7=118,F9=120}; loops={}; messages={}
                    function print(s) messages[#messages+1]=s end
                    function RegisterHook() end
                    function RegisterKeyBind() end
                    function NotifyOnNewObject() end
                    function ExecuteInGameThread(fn) fn() end
                    function StaticFindObject() return nil end
                    function LoopInGameThreadWithDelay(ms,fn) loops[#loops+1]={ms,fn}; return #loops end
                ''')
                lua.execute('package.preload.config=function() '+files['Scripts/config.lua']+' end')
                lua.execute(files['Scripts/main.lua'],name='@FFRStudioFieldLeader/Scripts/main.lua')
                self.assertIsNotNone(lua.globals().FFRStudioLocalMap)
                self.assertEqual(bool(lua.globals().FFRStudioAutoBattle),auto)
                self.assertEqual(bool(lua.globals().FFRStudioEsperMastery),esper)


if __name__=='__main__': unittest.main()
