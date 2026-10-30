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
        lua.execute((ROOT/'scripts/fixtures/encounter_toggle_runtime.lua').read_text(encoding='utf-8'))
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
            local result=returned_params(nativeSource.effect.ParamList)
            assert(result[1]~=0 and result[1]:get()==0,
                'Returned struct arrays must exercise the actual RemoteUnrealParam representation')
        ''')
        helper=(ROOT/'assets/existing_visions/payload/status_hud.lua').read_text(encoding='utf-8')
        code=(ROOT/'assets/existing_visions/payload/encounter_toggle.lua').read_text(encoding='utf-8')
        lua.execute('local create_status_hud=(function()\n'+helper+'\nend)();\n'+code)
        lua.globals().tests()
        messages=list(lua.globals().messages.values())
        self.assertTrue(any('Owned target=' in line for line in messages))
        self.assertTrue(any('source=playable' in line for line in messages))
        self.assertTrue(any('Native battle entry while OFF' in line for line in messages))
        # The same failed read used to log on every native InputMove frame.
        lua.execute('''
            ExecuteInGameThread=function(fn) fn() end
            local function errors()
                local n=0
                for _,line in ipairs(messages) do
                    if line:find('ratio=0',1,true) and line:find('type=0',1,true) then n=n+1 end
                end
                return n
            end
            local before=errors()
            badNativeEffect=true;press()
            for i=1,120 do hooks['/Script/mucha.CPP_MapUnit_Playable:InputMove'][1]({get=function() return actor end}) end
            assert(errors()==before+1,'Deduplicate identical native movement failures')
            assert(not has_effect(parameters[1001],71000),'Unsupported native data must remain rejected')
        ''')

    def test_native_movement_owner_works_without_map_player_and_clears_on_transitions(self):
        from lupa.lua54 import LuaRuntime
        lua=LuaRuntime()
        lua.execute((ROOT/'scripts/fixtures/encounter_toggle_runtime.lua').read_text(encoding='utf-8'))
        def value(v):
            if isinstance(v,dict):return lua.table_from({k:value(x) for k,x in v.items()})
            if isinstance(v,list):return lua.table_from([value(x) for x in v])
            return v
        lua.globals().nativeSource=value(json.loads((ROOT/'scripts/fixtures/encounter_control_native.json').read_bytes()))
        helper=(ROOT/'assets/existing_visions/payload/status_hud.lua').read_text(encoding='utf-8')
        code=(ROOT/'assets/existing_visions/payload/encounter_toggle.lua').read_text(encoding='utf-8')
        lua.execute('local create_status_hud=(function()\n'+helper+'\nend)();\n'+code)
        lua.execute('''
            mapPlayerMissing=true;press();assert(not FFRStudioEncounterToggle.disabled)
            local move=hooks['/Script/mucha.CPP_MapUnit_Playable:InputMove'][1]
            move({get=function() return actor end});tick()
            assert(lastText.label:find('ON'))
            press();assert(FFRStudioEncounterToggle.disabled and has_effect(parameters[1001],71000))
            assert(actor.m_OverwriteEncountRatio==-1 and actor.m_EncountThresholdDistance==1200)
            assert(type(FFRStudioEncounterToggle.inputPath)=='string' and FFRStudioEncounterToggle.inputActor==nil)
            menuOpen=true;tick();assert(FFRStudioEncounterToggle.inputPath==nil)
            assert(not has_effect(parameters[1001],71000))
            menuOpen=false;tick();assert(not has_effect(parameters[1001],71000))
            actor.vehicle=true;move({get=function() return actor end});tick()
            assert(FFRStudioEncounterToggle.inputPath==nil and not has_effect(parameters[1001],71000))
            actor.vehicle=false;move({get=function() return actor end});tick()
            assert(has_effect(parameters[1001],71000))
            local boundary=hooks['/Script/mucha.CPP_MapTransitionTrigger:ExecuteTransition'][1]
            boundary();assert(FFRStudioEncounterToggle.inputPath==nil and not has_effect(parameters[1001],71000))
        ''')

    def test_encounter_only_install_requests_the_optional_runtime(self):
        import _ffr_runtime_loader as runtime
        game=self.root/'game';game.mkdir()
        self.assertTrue(runtime.status(self.root,game,[])['required'])
        self.assertFalse(runtime.status(self.root,game,[])['ready'])

    def test_native_row_reference_bypasses_table_marshalling_and_rejects_missing_data(self):
        from lupa.lua54 import LuaRuntime
        source=json.loads((ROOT/'scripts/fixtures/encounter_control_native.json').read_bytes())
        helper=(ROOT/'assets/existing_visions/payload/status_hud.lua').read_text(encoding='utf-8')
        code=(ROOT/'assets/existing_visions/payload/encounter_toggle.lua').read_text(encoding='utf-8')
        for kind in ('ByteProperty','IntProperty'):
            with self.subTest(kind=kind):
                lua=LuaRuntime();lua.execute((ROOT/'scripts/fixtures/encounter_toggle_runtime.lua').read_text(encoding='utf-8'))
                def value(v):
                    if isinstance(v,dict):return lua.table_from({k:value(x) for k,x in v.items()})
                    if isinstance(v,list):return lua.table_from([value(x) for x in v])
                    return v
                lua.globals().nativeSource=value(source);lua.globals().dataTableParameterKind=kind
                lua.execute('local create_status_hud=(function()\n'+helper+'\nend)();\n'+code)
                if kind=='IntProperty':
                    lua.execute('''
                        press();assert((effectCreations or 0)==0)
                        assert(not has_effect(parameters[1001],71000))
                        assert(messages[#messages]:find('Unsupported native encounter signature',1,true))
                    ''')
                    continue
                lua.execute('''
                    for _,flag in ipairs({'nativeTableMissing','badNativeSchema','nativeRowMissing'}) do
                        local count=effectCreations or 0
                        _G[flag]=true;press()
                        assert((effectCreations or 0)==count and not has_effect(parameters[1001],71000))
                        _G[flag]=false;tick()
                        assert(has_effect(parameters[1001],71000))
                        assert(nativeEffectRow.ID==71000 and nativeEffectRow.ParamList:GetArrayNum()==15)
                        press();assert(not has_effect(parameters[1001],71000))
                    end
                    local writable=pcall(function() nativeEffectRow.ParamList={} end)
                    assert(not writable,'Keep the engine-owned source row read-only')
                    press();assert(has_effect(parameters[1001],71000))
                    assert(FFRStudioEncounterToggle.nativeFactoryVerified)
                ''')

    def test_all_requested_ground_modes_toggle_and_preserve_native_vehicle_rules(self):
        from lupa.lua54 import LuaRuntime
        lua=LuaRuntime();lua.execute((ROOT/'scripts/fixtures/encounter_toggle_runtime.lua').read_text(encoding='utf-8'))
        def value(v):
            if isinstance(v,dict):return lua.table_from({k:value(x) for k,x in v.items()})
            if isinstance(v,list):return lua.table_from([value(x) for x in v])
            return v
        lua.globals().nativeSource=value(json.loads((ROOT/'scripts/fixtures/encounter_control_native.json').read_bytes()))
        helper=(ROOT/'assets/existing_visions/payload/status_hud.lua').read_text(encoding='utf-8')
        code=(ROOT/'assets/existing_visions/payload/encounter_toggle.lua').read_text(encoding='utf-8')
        lua.execute('local create_status_hud=(function()\n'+helper+'\nend)();\n'+code)
        lua.execute('''
            for _,method in ipairs({nativeSource.enums['eMapMovementMethod.Walking'],
                nativeSource.enums['eMapMovementMethod.Chocobo'],nativeSource.enums['eMapMovementMethod.MagickArmor']}) do
                actor.movementMethod=method;tick();press()
                assert(FFRStudioEncounterToggle.disabled and has_effect(parameters[1001],71000))
                assert(lastText.label:find('OFF') and lastWidget.anchors.Minimum.Y==1)
                press();assert(not FFRStudioEncounterToggle.disabled and not has_effect(parameters[1001],71000))
            end
            for _,method in ipairs({2,4}) do
                actor.movementMethod=method;tick();press()
                assert(not FFRStudioEncounterToggle.disabled and not has_effect(parameters[1001],71000))
            end
            actor.movementMethod=1;actor.raft=true;tick();press()
            assert(not FFRStudioEncounterToggle.disabled and not has_effect(parameters[1001],71000))
        ''')

    def lifecycle_runtime(self):
        from lupa.lua54 import LuaRuntime
        lua=LuaRuntime()
        lua.execute((ROOT/'scripts/fixtures/encounter_toggle_runtime.lua').read_text(encoding='utf-8'))
        def value(v):
            if isinstance(v,dict):return lua.table_from({k:value(x) for k,x in v.items()})
            if isinstance(v,list):return lua.table_from([value(x) for x in v])
            return v
        lua.globals().nativeSource=value(json.loads((ROOT/'scripts/fixtures/encounter_control_native.json').read_bytes()))
        helper=(ROOT/'assets/existing_visions/payload/status_hud.lua').read_text(encoding='utf-8')
        code=(ROOT/'assets/existing_visions/payload/encounter_toggle.lua').read_text(encoding='utf-8')
        lua.execute('local create_status_hud=(function()\n'+helper+'\nend)();\n'+code)
        return lua

    def test_input_owner_is_resolved_again_without_a_retained_actor_pointer(self):
        lua=self.lifecycle_runtime()
        lua.execute('''
            local move=hooks['/Script/mucha.CPP_MapUnit_Playable:InputMove'][1]
            move({get=function() return actor end});tick()
            assert(type(FFRStudioEncounterToggle.inputPath)=='string')
            assert(FFRStudioEncounterToggle.inputActor==nil)
            local old=actor;local reads=0
            old.GetMapMovementMethod=function() reads=reads+1;error('old world actor read') end
            old.GetFullName=function() reads=reads+1;error('old world actor name') end
            actor=new_actor('BP_Player_C /Game/Map/New.New:PersistentLevel.Player',-1)
            tick();assert(reads==0 and lastText.label:find('ON'))
            move({get=function() return actor end});tick()
            assert(FFRStudioEncounterToggle.inputPath=='/Game/Map/New.New:PersistentLevel.Player')
            assert(FFRStudioEncounterToggle.inputActor==nil)
            assert(viewport[#viewport]==lastWidget)
        ''')

    def test_world_map_and_destination_modes_are_excluded_even_when_main_menu_is_closed(self):
        lua=self.lifecycle_runtime()
        lua.execute('''
            tick();press();assert(FFRStudioEncounterToggle.disabled)
            for _,mode in ipairs({18,24,15,17,23,6}) do
                inputContexts={{parentMappingContext=mode,childMappingContextList={}}}
                local before=buttonReads;local widget=lastWidget
                controller.left,controller.right=1,1
                for i=1,20 do tick();press() end
                hooks['/Script/mucha.CPP_MapUnit_Playable:InputMove'][1]({get=function() return actor end})
                assert(buttonReads==before,'Never poll triggers behind the world map/destination list')
                assert(widget.removed and not has_effect(parameters[1001],71000))
                assert(FFRStudioEncounterToggle.disabled,'Map input must not toggle encounter state')
                controller.left,controller.right=0,0
                inputContexts={{parentMappingContext=1,childMappingContextList={14,18}},
                    {parentMappingContext=14,childMappingContextList={18}},
                    {parentMappingContext=12,childMappingContextList={}}}
                tick();assert(has_effect(parameters[1001],71000) and lastText.label:find('OFF'))
            end
        ''')

    def test_map_hold_requires_neutral_triggers_after_returning_to_the_field(self):
        lua=self.lifecycle_runtime()
        lua.execute('''
            tick();controller.left,controller.right=1,1;tick(.1);tick(.5)
            inputContexts={{parentMappingContext=24}};tick(2)
            inputContexts={{parentMappingContext=1}};tick(2);tick(2)
            assert(not FFRStudioEncounterToggle.disabled)
            controller.left=0;tick();controller.left=1;tick();tick(2)
            assert(not FFRStudioEncounterToggle.disabled)
            controller.left,controller.right=0,0;tick()
            controller.left,controller.right=1,1;tick();tick(1.1)
            assert(FFRStudioEncounterToggle.disabled and has_effect(parameters[1001],71000))
        ''')

    def test_unavailable_or_unknown_input_mapping_cannot_arm_the_shortcut(self):
        lua=self.lifecycle_runtime()
        lua.execute('''
            controller.left,controller.right=1,1
            for _,contexts in ipairs({{},{{parentMappingContext=999}},{{parentMappingContext=0}}}) do
                inputContexts=contexts
                for i=1,30 do tick();press() end
                assert(buttonReads==0 and created==0 and not FFRStudioEncounterToggle.disabled)
            end
        ''')

    def test_battle_and_event_guards_run_before_resolving_any_field_actor(self):
        lua=self.lifecycle_runtime()
        lua.execute('''
            local map=StaticFindObject('/Script/mucha.Default__CPP_BFL_Map')
            local original=map.GetPlayerMapUnit;local reads=0
            map.GetPlayerMapUnit=function() reads=reads+1;error('field lookup during transition') end
            inBattle=true;for _=1,30 do tick() end
            inBattle=false;event=true;for _=1,30 do tick() end
            assert(reads==0 and created==0)
            map.GetPlayerMapUnit=original;event=false;tick()
            assert(created==1 and lastText.label:find('ON'))
        ''')

    def test_destroying_actor_is_not_dereferenced_even_when_isvalid_is_true(self):
        for flag in (0x8000,0x10000):
            with self.subTest(flag=flag):
                lua=self.lifecycle_runtime();lua.globals().destroyFlag=flag
                lua.execute('''
                    actor.flags=destroyFlag;assert(actor:IsValid())
                    local reads=0;local original=actor.IsA
                    actor.IsA=function() reads=reads+1;error('retiring actor class') end
                    for _=1,120 do tick();collectgarbage('collect') end
                    assert(reads==0 and created==0)
                    actor.IsA=original;actor.flags=0;tick()
                    assert(created==1 and lastText.label:find('ON'))
                ''')

    def test_retiring_field_widget_is_replaced_without_calling_its_engine_methods(self):
        lua=self.lifecycle_runtime()
        lua.execute('''
            tick();local old=lastWidget;old.flags=0x8000
            local reads=0
            old.GetVisibility=function() reads=reads+1;error('dying widget visibility') end
            old.RemoveFromParent=function() reads=reads+1;error('dying widget removal') end
            tick();assert(reads==0 and created==2 and old~=lastWidget)
            assert(viewport[#viewport]==lastWidget and lastText.label:find('ON'))
            press();assert(FFRStudioEncounterToggle.disabled and lastText.label:find('OFF'))
        ''')

    def test_retiring_private_hud_class_is_not_passed_to_native_widget_creation(self):
        lua=self.lifecycle_runtime()
        lua.execute('''
            tick();event=true;tick();event=false
            guideClass.flags=0x10000;assert(guideClass:IsValid())
            local before=created
            tick();assert(created==before and #viewport==0)
            assert(not FFRStudioEncounterToggle.disabled)
            guideClass.flags=0;tick()
            assert(created==before+1 and lastText.label:find('ON'))
        ''')


if __name__=='__main__':unittest.main()
