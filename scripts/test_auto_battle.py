"""Replay native command UI, not fabricated jobs: lifecycle, costs and targeting."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock
from lupa.lua54 import LuaRuntime
import _ffr_testing as testing
import _ffr_field_leader as leader

ROOT=Path(__file__).resolve().parents[1]

class RuntimeTests(unittest.TestCase):
    def setUp(self):
        self.lua=LuaRuntime()
        self.lua.execute((ROOT/'scripts/fixtures/auto_battle_runtime.lua').read_text())
        self.lua.execute((ROOT/'assets/existing_visions/payload/auto_battle.lua').read_text())
    def run_lua(self,s):self.lua.execute(s)

    def test_saved_command_replayed_through_the_captured_hierarchy_and_next_turn(self):
        self.run_lua('''
            tick();assert(not guidesCreated and #submissions==0)
            active=true;press();tick();tick();assert(#submissions==1 and availableMP==9)
            tick();assert(#submissions==1)
            new_turn();tick();tick();tick();assert(#submissions==2 and availableMP==8)
        ''')

    def test_manual_memory_retains_multicast_and_all_mode_across_battles(self):
        self.run_lua('''
            active=true;requiredActions=2;manual({344,420070,420070},true)
            press();for i=1,5 do tick() end
            assert(#submissions==1 and availableMP==8)
            active=false;tick();assert(guidesRemoved==1)
            actor=11;enemy=72;friend=14;ui.name='NextBattleWorld';manager.name='NextCommandManager'
            active=true;new_turn();for i=1,5 do tick() end
            assert(#submissions==2 and availableMP==6)
            local data=submissions[2];data.DecideDataList:ForEach(function(_,v)
                assert(v:get().IsAll)
                v:get().targetUnitUniqueIdList:ForEach(function(_,n) assert(n:get()>=72) end)
            end)
        ''')

    def test_low_mp_pauses_before_an_invalid_or_partial_multicast_submission(self):
        self.run_lua('''
            active=true;requiredActions=2;availableMP=1;manual({344,420070,420070})
            press();for i=1,5 do tick() end
            assert(not FFRStudioAutoBattle.enabled and #submissions==0 and availableMP==1)
            assert(badge:find('unavailable',1,true))
        ''')

    def test_friendly_target_is_resolved_again_after_actor_ids_change(self):
        self.run_lua('''
            active=true;manual(nil,false,friend)
            actor=11;enemy=72;friend=14;new_turn();press();tick();tick()
            local selected;submissions[1].DecideDataList:ForEach(function(_,v)
                v:get().targetUnitUniqueIdList:ForEach(function(_,n) selected=n:get() end)
            end)
            assert(selected==14)
        ''')

    def test_remembered_items_use_native_availability_and_consumption(self):
        self.run_lua("""
            active=true;parentId=5;actionId=9001;actionCategory=2
            manual({5,9001});press();tick();tick();assert(#submissions==1 and itemQty==1 and availableMP==10)
            new_turn();tick();tick();tick();assert(#submissions==2 and itemQty==0)
            new_turn();tick();tick();assert(not FFRStudioAutoBattle.enabled and #submissions==2)
        """)

    def test_native_menu_or_mp_changes_pause_without_replacing_remembered_command(self):
        self.run_lua('''
            active=true;manual();local memory=FFRStudioAutoBattle.memory[1001]
            menuChanged=true
            press();tick();assert(not FFRStudioAutoBattle.enabled and #submissions==0)
            assert(FFRStudioAutoBattle.memory[1001]==memory)
        ''')

    def test_pause_event_extra_phases_and_no_hud_do_not_submit_commands(self):
        self.run_lua('''
            active=true;manual();press();paused=true;tick();assert(#submissions==0)
            paused=false;event=true;tick();assert(#submissions==0)
            event=false;phase=1;tick();assert(#submissions==0)
            phase=0;guideAvailable=false;tick();assert(#submissions==0 and not FFRStudioAutoBattle.enabled)
        ''')

    def test_controller_hold_uses_real_time_and_latches_until_release(self):
        self.run_lua('''
            active=true;vm.bDisplayCmd=false;controller.left=1;controller.right=1
            tick(.1);tick(.9);assert(not FFRStudioAutoBattle.enabled)
            tick(.11);assert(FFRStudioAutoBattle.enabled)
            tick(4);assert(FFRStudioAutoBattle.enabled)
            controller.left=0;tick();controller.left=1;tick();tick(1.1)
            assert(not FFRStudioAutoBattle.enabled)
        ''')

    def test_guide_tracks_the_actual_speed_guide_without_changing_native_widgets(self):
        self.run_lua("""
            active=true;showSpeed=true;tick()
            assert(guidePosition.X==558 and guidePosition.Y==30)
            assert(badge:find('F9',1,true) and badge:find('OFF',1,true))
        """)

    def test_manual_memory_is_captured_when_native_input_and_command_ui_have_closed(self):
        self.run_lua('''
            active=true;inputEnabled=false;vm.bDisplayCmd=false;manual()
            assert(FFRStudioAutoBattle.memory[1001]~=nil)
            inputEnabled=true;new_turn();press();tick();tick();assert(#submissions==1)
        ''')

    def test_indicator_fallback_is_at_the_bottom_and_empty_selected_stack_is_not_an_empty_menu(self):
        self.run_lua('''
            active=true;tick()
            assert(guidePosition.anchorY==1 and guidePosition.Y<0)
            assert(#stack==0);press();tick();tick();assert(#submissions==1)
        ''')

    def test_manual_input_takes_over_and_callbacks_survive_gc(self):
        self.run_lua('''
            active=true;manual();press() -- auto selects the parent
            collectgarbage('collect');vm:DecideActionKey({Category=1,ID=420070})
            assert(not FFRStudioAutoBattle.enabled and #submissions==0)
            local weak=setmetatable({},{__mode='v'})
            ExecuteInGameThread=function(fn) weak.callback=fn end
            FFRStudioAutoBattle.async();collectgarbage('collect')
            assert(type(weak.callback)=='function');weak.callback()
        ''')

    def test_native_loop_uses_the_real_hud_with_typed_text_and_no_async_polling(self):
        lua=LuaRuntime()
        lua.execute((ROOT/'scripts/fixtures/auto_battle_runtime.lua').read_text())
        lua.execute('''
            local originalFind=StaticFindObject
            local gameplay=originalFind('/Script/Engine.Default__GameplayStatics')
            function gameplay:GetPlayerController(context,index) assert(context==ui and index==0);return controller end
            local factory={IsValid=function() return true end}
            function factory:Create(context,class,player)
                assert(context==ui and player==controller)
                local label={IsValid=function() return true end,SetVisibility=function() end,SetRenderOpacity=function() end}
                function label:SetText(value)
                    assert(value.nativeType=='FText','Native HUD requires typed FText')
                    badge=value.value
                end
                local widget={Text_Name=label,IsValid=function() return true end,
                    Horizontal_Content={IsValid=function() return true end,SetVisibility=function() end,SetRenderOpacity=function() end},
                    WBP_DirectionGridPanel={IsValid=function() return true end,SetVisibility=function() end}}
                for _,name in ipairs({'SetVisibility','SetRenderOpacity','AddToViewport','SetAnchorsInViewport',
                    'SetAlignmentInViewport','SetDesiredSizeInViewport','SetPositionInViewport','RemoveFromParent'}) do
                    widget[name]=function() end
                end
                return widget
            end
            function StaticFindObject(path)
                if path=='/Script/UMG.Default__WidgetBlueprintLibrary' then return factory end
                return originalFind(path)
            end
            function FText(value) return {nativeType='FText',value=value} end
            function LoopInGameThreadWithDelay(ms,fn) assert(ms==100);nativeTick=fn;return 77 end
            function LoopAsync() error('Native scheduler must not start async polling') end
        ''')
        lua.execute('create_status_hud=(function()\n'+(ROOT/'assets/existing_visions/payload/status_hud.lua').read_text()+'\nend)()')
        lua.execute((ROOT/'assets/existing_visions/payload/auto_battle.lua').read_text())
        lua.execute('''
            assert(FFRStudioAutoBattle.async==nil);nativeTick();assert(badge==nil)
            active=true;nativeTick();assert(badge:find('OFF',1,true))
            press();collectgarbage('collect');nativeTick();nativeTick()
            assert(#submissions==1 and badge:find('ON',1,true))
        ''')

    def test_combined_runtime_keeps_all_native_loops_and_removes_auto_when_disabled(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);config=root/testing.CONFIG;config.parent.mkdir(parents=True)
            for enabled in (True,False):
                config.write_text(json.dumps({'schema':1,'maxMr':False,'autoBattle':enabled,'noEncounters':True}))
                units=[{'id':13515,'synchro':[[['PassiveSkill',1960,-1]]]}]
                with mock.patch('_ffr_overworld.runtime_config',return_value={'schema':1,'cycling':0,'actors':{},'defaults':{}}):
                    leader.build(units,{'ROOT':root,'rows':lambda _:self.fail('No conversion required')})
                files=json.loads((root/leader.STAGE).read_bytes())['files']
                self.assertEqual('FFRStudioAutoBattle' in files['Scripts/main.lua'],enabled)
                lua=LuaRuntime()
                lua.execute('''
                    loops={};Key={F7=118,F9=120}
                    function print() end
                    function RegisterKeyBind() end
                    function RegisterHook() end
                    function StaticFindObject() return {IsValid=function() return true end} end
                    function LoopInGameThreadWithDelay(ms,fn) loops[#loops+1]={ms,fn};return #loops end
                    function LoopAsync() error('Combined runtime must use native game-thread loops') end
                ''')
                lua.execute('package.preload.config=function() '+files['Scripts/config.lua']+' end')
                lua.execute(files['Scripts/main.lua'])
                self.assertEqual(len(lua.globals().loops),3 if enabled else 2)

class BuildTests(unittest.TestCase):
    def test_opt_in_stages_runtime_and_removes_it_when_disabled_without_asset_conversion(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);p=root/testing.CONFIG;p.parent.mkdir(parents=True)
            for enabled in (True,False):
                p.write_text(json.dumps({'schema':1,'maxMr':False,'autoBattle':enabled}))
                with mock.patch('_ffr_fina_cinematic.ensure_assets') as film:
                    testing.ensure_assets(root,lambda _:self.fail('No extraction required'))
                leader.build([],{'ROOT':root,'rows':lambda _:self.fail('No tables needed')})
                files=json.loads((root/leader.STAGE).read_bytes())['files']
                self.assertEqual(bool(files),enabled)
                if enabled:
                    self.assertIn('autoBattle',files['Scripts/config.lua'])
                    self.assertIn('RegisterKeyBind(Key.F9',files['Scripts/main.lua'])
                    self.assertNotIn('RegisterKeyBind(Key.F7',files['Scripts/main.lua'])
                    self.assertNotIn('StaticConstructObject',files['Scripts/main.lua'])
                    LuaRuntime().eval('function(code) assert(load(code)) end')(files['Scripts/main.lua'])

    def test_auto_only_install_offers_the_optional_loader(self):
        import _ffr_runtime_loader as loader
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);p=root/testing.CONFIG;p.parent.mkdir(parents=True)
            p.write_text(json.dumps({'schema':1,'maxMr':False,'autoBattle':True}))
            self.assertTrue(loader.status(root,root/'Game',[])['required'])

    def test_legacy_default_and_strict_boolean(self):
        self.assertFalse(testing.validate_settings({'schema':1,'maxMr':False})['autoBattle'])
        with self.assertRaises(ValueError):testing.validate_settings({'schema':1,'maxMr':False,'autoBattle':1})

if __name__=='__main__':unittest.main()
