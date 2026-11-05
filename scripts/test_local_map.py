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

    def test_initial_visible_widget_uses_the_captured_blueprint_view_model_without_native_cache(self):
        fields=load_fixture('local_map_native.json.gz')['widgetFields']
        self.assertIn('VM_MiniMap',[p['Name'] for p in fields])
        lua=self.runtime()
        lua.execute("assert(initialPaint and initialPaint>0);assert(widget.VM_MiniMap==vm)")
        lua.execute("discover();discover();assert(#queued==1);drain();assert(not widget.paint)")

    def test_actual_native_area_layout_size_is_not_projected_or_scaled_twice(self):
        lua=self.runtime()
        lua.execute('''
            vm.AreaLayoutVM=obj({AreaDataMap={ForEach=function(_,callback)
                callback(param(101),param({Size={X=400,Y=300}}))
            end}})
            vm.width,vm.height=200000,200000;vm.projection=.1
            show();assert(math.abs(widget.paint-(.9*640/500))<1e-7)
            local fitted=widget.paint
            vm.projection=.001;show();assert(math.abs(widget.paint-fitted)<1e-7)
            vm.AreaLayoutVM.AreaDataMap={[101]={Size={X=800,Y=600}}}
            show();assert(math.abs(widget.paint-fitted/2)<1e-7)
        ''')

    def test_current_area_fits_at_any_rotation_across_different_bounds_and_ui_sizes(self):
        lua=self.runtime()
        lua.execute('''
            for _,size in ipairs({{20000,10000},{1000,90000},{200,200}}) do
                for _,range in ipairs({320,640,900}) do
                    vm.width,vm.height=size[1],size[2]; vm.displayX,vm.displayY=range,range
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
            assert(vm.syncCalls==9,'Native position refresh must be bounded too')
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
            vm.tag='None'; show() -- User cycle: large -> hidden -> small.
            vm.tag='UI.Field.MiniMap.View.Decrale.Instance'; show()
            assert(vm.restores==1 and vm.alpha==.7 and vm.ZoomProperty.bSaveZoom)
            assert(vm.ZoomProperty.ScaleInterval.min==1 and widget.paint==1)
            show(); assert(vm.restores==1)
        ''')

    def test_large_view_stays_large_from_world_to_town_building_and_area_section(self):
        lua=self.runtime()
        lua.execute('''
            vm.world=true;vm.areaId=-1;vm.tag='UI.Field.MiniMap.View.Decrale.World';show()
            vm.tag='UI.Field.MiniMap.View.Decrale.Wide';show()
            assert(FFRStudioLocalMap.choice==1)
            vm.world=false;vm.areaId=101;vm.mapId=2001;vm.tag='UI.Field.MiniMap.View.Decrale.Instance';show()
            assert(vm.tag=='UI.Field.MiniMap.View.Decrale' and vm.index==1 and widget.paint)
            vm.mapId=2002;vm.tag='UI.Field.MiniMap.View.Decrale.Instance';show()
            assert(vm.tag=='UI.Field.MiniMap.View.Decrale' and FFRStudioLocalMap.choice==1)
            vm.areaId=202;vm.areas={[202]={BoxSize={X=9000,Y=6000}}}
            vm.tag='UI.Field.MiniMap.View.Decrale.Instance';show()
            assert(vm.tag=='UI.Field.MiniMap.View.Decrale' and FFRStudioLocalMap.choice==1)
            vm.world=true;vm.mapId=1000;vm.areaId=-1;vm.tag='UI.Field.MiniMap.View.Decrale.World';show()
            assert(vm.tag=='UI.Field.MiniMap.View.Decrale.Wide' and vm.index==1)
        ''')

    def test_engine_load_freezes_choice_before_old_hud_resets_even_with_reused_vm_ids(self):
        lua=self.runtime()
        lua.execute('''
            show();assert(FFRStudioLocalMap.choice==1)
            local source=vm.address;local map,area=vm.mapId,vm.areaId
            FindAllOf=function() error('No object scans during map travel') end
            loadMapPre();assert(FFRStudioLocalMap.loading)
            vm.tag='UI.Field.MiniMap.View.Decrale.Instance';vm.display=true;vm.index=0
            show();tick();assert(FFRStudioLocalMap.choice==1 and vm.index==0)
            loadMapPost();tick()
            assert(vm.address==source and vm.mapId==map and vm.areaId==area)
            assert(vm.index==1 and FFRStudioLocalMap.choice==1 and not FFRStudioLocalMap.restorePending)
            set_view(2);tick();set_view(0);assert(vm.index==0 and FFRStudioLocalMap.choice==0)
            set_view(1);assert(vm.index==1 and FFRStudioLocalMap.choice==1)
        ''')

    def test_world_identity_restores_large_when_model_ids_stay_the_same(self):
        lua=self.runtime()
        lua.execute('''
            show();local old=world;world=obj()
            vm.tag='UI.Field.MiniMap.View.Decrale.Instance';vm.display=true;vm.index=0
            show();tick()
            assert(world.address~=old.address and vm.index==1 and FFRStudioLocalMap.choice==1)
        ''')

    def test_legacy_loader_keeps_world_identity_fallback_without_engine_callbacks(self):
        lua=LuaRuntime();lua.execute((ROOT/'scripts/fixtures/local_map_runtime.lua').read_text())
        lua.execute('RegisterLoadMapPreHook=nil;RegisterLoadMapPostHook=nil')
        lua.execute((PAYLOAD/'local_map.lua').read_text())
        lua.execute('''
            ready();show();world=obj()
            vm.tag='UI.Field.MiniMap.View.Decrale.Instance';vm.display=true;vm.index=0
            show();tick();assert(vm.index==1 and FFRStudioLocalMap.choice==1)
        ''')

    def test_direct_native_small_step_is_respected_even_when_hidden_notification_is_absent(self):
        lua=self.runtime()
        lua.execute('''
            show();set_view(2);set_view(0)
            assert(vm.index==0 and FFRStudioLocalMap.choice==0)
            vm.mapId=3000;vm.tag='UI.Field.MiniMap.View.Decrale';show();tick()
            assert(vm.tag=='UI.Field.MiniMap.View.Decrale.Instance' and FFRStudioLocalMap.choice==0)
        ''')

    def test_new_view_model_reuses_the_session_choice_without_retaining_the_old_object(self):
        lua=self.runtime()
        lua.execute('''
            show();local old=vm;local replacement=obj()
            for key,value in pairs(old) do if key~='address' then replacement[key]=value end end
            vm=replacement;widget.VM_MiniMap=vm
            vm.tag='UI.Field.MiniMap.View.Decrale.Instance';vm.mapId=4401
            show();assert(vm.tag=='UI.Field.MiniMap.View.Decrale' and vm.index==1)
            assert(old.address~=vm.address and FFRStudioLocalMap.fitted==vm.address)
        ''')

    def test_hidden_bootstrap_and_missing_fit_keep_native_visibility_without_resize_loops(self):
        lua=self.runtime()
        lua.execute('''
            vm.tag='None';show();assert(FFRStudioLocalMap.choice==nil)
            vm.tag='UI.Field.MiniMap.View.Decrale.Instance';show();assert(FFRStudioLocalMap.choice==0)
            vm.tag='UI.Field.MiniMap.View.Decrale';vm.width=0;show()
            assert(not vm.fallback and FFRStudioLocalMap.choice==1)
            for i=1,20 do show();tick() end
            assert(not vm.stepCalls)
            vm.width=20000;tick();assert(widget.paint and FFRStudioLocalMap.choice==1)
            assert(type(FFRStudioLocalMap.viewKey)=='string')
        ''')

    def test_native_visibility_and_default_tag_cycle_through_all_three_steps(self):
        lua=self.runtime()
        lua.execute('''
            show();vm.resetOnRestore=true
            for i=1,5 do
                set_view(2);tick()
                assert(vm.tag=='UI.Field.MiniMap.View.Decrale.Default' and vm.display==false)
                assert(FFRStudioLocalMap.choice==2 and vm.index==2)
                set_view(0)
                assert(FFRStudioLocalMap.choice==0 and vm.index==0 and vm.display)
                set_view(1)
                assert(FFRStudioLocalMap.choice==1 and vm.index==1 and vm.display)
            end
        ''')

    def test_hidden_view_can_retain_the_large_tag_without_being_forced_on(self):
        lua=self.runtime()
        lua.execute('''
            show();local calls=vm.zoomCalls
            vm.display=false;show()
            assert(vm.tag=='UI.Field.MiniMap.View.Decrale' and FFRStudioLocalMap.choice==2)
            assert(vm.zoomCalls==calls)
            set_view(0);assert(FFRStudioLocalMap.choice==0)
        ''')

    def test_default_setup_view_and_zoom_restoration_do_not_reset_remembered_world_size(self):
        lua=self.runtime()
        lua.execute('''
            show();vm.resetOnRestore=true
            vm.world=true;vm.mapId=9100;vm.areaId=-1
            vm.tag='UI.Field.MiniMap.View.Decrale.Default';vm.display=true;show()
            assert(vm.index==1 and vm.tag=='UI.Field.MiniMap.View.Decrale.Wide')
            assert(FFRStudioLocalMap.choice==1 and vm.restores==1)
            vm.world=false;vm.mapId=9101;vm.areaId=101
            vm.tag='UI.Field.MiniMap.View.Decrale.Default';vm.display=true;show()
            assert(vm.index==1 and vm.tag=='UI.Field.MiniMap.View.Decrale' and widget.paint)
            vm.mapId=9102;vm.tag='UI.Field.MiniMap.View.Decrale.Instance';show()
            assert(vm.index==1 and FFRStudioLocalMap.choice==1)
        ''')

    def test_new_zone_keeps_large_while_geometry_is_missing_then_fits_when_ready(self):
        lua=self.runtime()
        lua.execute('''
            show();vm.mapId=9200;vm.width=0;set_view(0);tick()
            assert(FFRStudioLocalMap.choice==1 and vm.index==1)
            local changes=vm.stepCalls
            for i=1,20 do tick() end
            assert(vm.stepCalls==changes and vm.index==1)
            vm.width=20000;tick()
            assert(vm.index==1 and widget.paint)
            local calls=vm.stepCalls
            for i=1,20 do tick() end
            assert(vm.stepCalls==calls)
        ''')

    def test_hidden_visibility_without_appearance_notification_keeps_the_full_native_cycle(self):
        lua=self.runtime()
        lua.execute('''
            show()
            for i=1,10 do
                set_view(2);assert(FFRStudioLocalMap.choice==1)
                tick();assert(FFRStudioLocalMap.choice==2)
                set_view(0);assert(vm.index==0 and FFRStudioLocalMap.choice==0)
                set_view(1);assert(vm.index==1 and FFRStudioLocalMap.choice==1)
            end
            -- Rapid off -> small between observer ticks still respects small.
            set_view(2);set_view(0);assert(vm.index==0)
        ''')

    def test_zone_reset_without_any_widget_notification_is_reconciled_by_path_lookup(self):
        lua=self.runtime()
        lua.execute('''
            show();local wanted=widget.paint
            FindAllOf=function() error('No repeated object scans') end
            vm.mapId=9300;vm.tag='UI.Field.MiniMap.View.Decrale.Instance';vm.display=true
            tick();assert(vm.index==1 and FFRStudioLocalMap.choice==1)
            local zooms,syncs,paints=vm.zoomCalls,vm.syncCalls,widget.paints
            for i=1,20 do tick() end
            assert(widget.paint==wanted)
            assert(vm.zoomCalls==zooms and vm.syncCalls==syncs and widget.paints==paints,
                'Unchanged observer ticks must not resync or repaint the native map')
            for path,key in pairs(FFRStudioLocalMap.targets) do assert(type(path)=='string' and type(key)=='string') end
        ''')

    def test_area_less_maps_use_only_a_sole_unambiguous_native_area(self):
        lua=self.runtime()
        lua.execute('''
            vm.areaId=-1
            vm.AreaLayoutVM=obj({AreaDataMap={[777]={Size={X=400,Y=300}}}})
            show();assert(math.abs(widget.paint-(.9*640/500))<1e-7)
            vm.AreaLayoutVM=nil;vm.areas={[777]={BoxSize={X=4000,Y=3000}}}
            tick();assert(math.abs(widget.paint-(.9*640/500))<1e-7)
        ''')

    def test_ambiguous_area_less_map_keeps_large_and_waits_for_the_current_area(self):
        lua=self.runtime()
        lua.execute('''
            vm.areaId=-1
            vm.AreaLayoutVM=obj({AreaDataMap={[101]={Size={X=400,Y=300}},[202]={Size={X=800,Y=600}}}})
            show();tick();assert(not widget.paint and not vm.fallback)
            assert(FFRStudioLocalMap.choice==1)
            vm.areaId=101;tick();assert(widget.paint and FFRStudioLocalMap.choice==1)
        ''')

    def test_loading_input_guard_does_not_learn_transient_hidden_or_small_setup(self):
        lua=self.runtime()
        lua.execute('''
            show();input.enabled=false
            vm.display=false;vm.tag='UI.Field.MiniMap.View.Decrale.Default';show();tick()
            assert(FFRStudioLocalMap.choice==1)
            vm.mapId=9400;vm.tag='UI.Field.MiniMap.View.Decrale.Instance';vm.display=true;show();tick()
            assert(FFRStudioLocalMap.choice==1)
            input.enabled=true;tick();assert(vm.index==1 and FFRStudioLocalMap.choice==1)
            set_view(2);set_view(0);assert(vm.index==0 and FFRStudioLocalMap.choice==0)
        ''')

    def test_legacy_async_observer_coalesces_work_on_the_game_thread(self):
        lua=LuaRuntime()
        lua.execute((ROOT/'scripts/fixtures/local_map_runtime.lua').read_text())
        lua.execute('LoopInGameThreadWithDelay=nil;function LoopAsync(ms,fn) assert(ms==100);asyncTick=fn end')
        lua.execute((PAYLOAD/'local_map.lua').read_text())
        lua.execute('''
            ready();show();set_view(2);assert(asyncTick)
            asyncTick();asyncTick();assert(#queued==1)
            drain();assert(FFRStudioLocalMap.choice==2)
            set_view(0);assert(vm.index==0)
        ''')

    def test_destroying_or_missing_objects_do_not_read_map_properties(self):
        lua=self.runtime()
        lua.execute('''
            widget.destroying=true; show(); assert(not vm.zoomCalls); widget.destroying=false
            vm.destroying=true; show(); assert(not vm.zoomCalls); vm.destroying=false
            local saved=widget.VM_MiniMap; widget.VM_MiniMap=nil; show(); assert(not vm.zoomCalls)
            widget.VM_MiniMap=saved; vm.invalid=true; show(); assert(not vm.zoomCalls)
        ''')

    def test_invalid_bounds_keep_the_selected_step_without_saving_zoom_or_repeated_logging(self):
        for field,value in [('width','0'),('height','-10'),('projection','0/0'),('displayX','math.huge')]:
            lua=self.runtime()
            lua.execute(f"vm.{field}={value}; show(); assert(not vm.fallback and not vm.zoomCalls and vm.ZoomProperty.bSaveZoom)")
            lua.execute("show();tick();assert(not vm.fallback and #messages==2)")

    def test_reloaded_blueprint_functions_rebind_but_discovery_does_not_duplicate(self):
        lua=self.runtime()
        lua.execute('''
            local count=0; for _ in pairs(hooks) do count=count+1 end; assert(count==3)
            discover(); discover(); drain(); show(); assert(vm.zoomCalls==1)
        ''')

    def test_active_area_bounds_do_not_shrink_when_the_land_group_contains_other_areas(self):
        lua=self.runtime()
        lua.execute('''
            show();local active=widget.paint
            vm.landWidth,vm.landHeight=2000000,3000000
            show();assert(math.abs(widget.paint-active)<1e-9)
            vm.rangeX,vm.rangeY=80,80
            show();assert(math.abs(widget.paint-active)<1e-9,'Range ring is not the viewport')
            -- The old whole-land fit made this active area a tiny center speck.
            local old=.90*640/math.sqrt((vm.landWidth*.1)^2+(vm.landHeight*.1)^2)
            assert(widget.paint>old*100)
            vm.areas={[202]={BoxSize={X=10000,Y=10000}},[101]={BoxSize={X=20000,Y=10000}}}
            vm.areaId=202
            gameThread=true;widget:SetWorldPosition({X=-100,Y=200});gameThread=false
            assert(widget.paint>active and widget.position.X==-100 and widget.position.Y==200)
            assert(math.abs(widget.paint-(.9*640/math.sqrt(2*1000^2)))<1e-9)
        ''')

    def test_missing_active_area_defers_fit_instead_of_using_unrelated_land_bounds(self):
        lua=self.runtime()
        lua.execute('''
            vm.areaId=404;show()
            assert(not vm.fallback and not widget.paint and not vm.zoomCalls)
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
