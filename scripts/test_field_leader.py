"""Field bank preservation, owned deployment/rollback, and executable Lua guards."""
import base64
import copy
import json
from pathlib import Path
import struct
import tempfile
import unittest
from unittest import mock

from test_existing_visions import ROOT
from test_overworld import map_rows, choice
from test_party_characters import unit
import _ffr_field_leader as leader
import _ffr_testing as testing


class FieldLeaderTests(unittest.TestCase):
    def combined_startup(self, esper=True, fina=True, walking=True, encounters=False):
        from lupa.lua54 import LuaRuntime
        import _ffr_fina_battle as battle
        import _ffr_overworld as overworld
        units=[]
        if esper: units.append({'id':13515,'synchro':[[['PassiveSkill',1960,-1]]]})
        if fina: units.append({'id':13503,'ffbe':{'id':battle.SPRITE,'source':'CUSTOM'}})
        if walking: units.append({'id':1001,'party':True,'overworld':{'version':1,'model':'native_party_1006'}})
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            if encounters:
                settings=root/testing.CONFIG;settings.parent.mkdir(parents=True)
                settings.write_text(json.dumps({'schema':1,'maxMr':False,'noEncounters':True}))
            runtime=root/'build/crystal-fina-battle/runtime.json';runtime.parent.mkdir(parents=True)
            runtime.write_text(json.dumps({'schema':1,'id':13503,'attackPlayRate':.8}))
            with mock.patch.object(overworld,'runtime_config',return_value={'schema':1,'cycling':0,'actors':{},'defaults':{}}):
                leader.build(units,{'ROOT':root,'rows':lambda _:self.fail('Startup needs no game data reads')})
            staged=json.loads((root/leader.STAGE).read_bytes())['files']
        lua=LuaRuntime()
        lua.execute('''
            messages={}; loops={}; hooks={};Key={F7=118}
            function RegisterKeyBind(key,callback) end
            function print(s) messages[#messages+1]=s end
            function LoopAsync(ms,fn) loops[ms]=fn end
            function RegisterHook(path,pre,post) hooks[path]={pre,post} end
            function StaticFindObject() return {IsValid=function() return true end} end
            function ExecuteInGameThread(fn) fn() end
        ''')
        lua.execute('package.preload.config=function() '+staged['Scripts/config.lua']+' end')
        return lua,staged['Scripts/main.lua']

    def test_complete_generated_runtime_starts_esper_fina_and_walking_together(self):
        # Standalone Lua sources pass even when adjoining IIFEs crash the
        # installed main.lua. Execute the exact output of the real builder.
        for esper,fina,walking in ((True,True,True),(True,True,False),(True,False,True),
                                   (False,True,True),(True,False,False),(False,True,False)):
            with self.subTest(esper=esper,fina=fina,walking=walking):
                lua,code=self.combined_startup(esper,fina,walking)
                lua.execute(code,name='@FFRStudioFieldLeader/Scripts/main.lua')
                messages=''.join(lua.globals().messages.values())
                self.assertEqual('Esper mastery ready' in messages,esper)
                self.assertEqual('Battle presentation ready' in messages,fina)
                self.assertEqual('Saved field appearance includes idle' in messages,walking)
                self.assertEqual(set(lua.globals().loops.keys()),
                                 ({200} if esper else set())|({33} if fina else set())|({150} if walking else set()))
                if esper:self.assertEqual(len(lua.globals().FFRStudioEsperMastery.callbacks),6)

    def test_generated_runtime_composes_encounters_with_esper_fina_and_walking(self):
        for esper,fina,walking in ((True,True,True),(True,False,False),(False,False,False)):
            lua,code=self.combined_startup(esper,fina,walking,encounters=True)
            lua.execute(code,name='@FFRStudioFieldLeader/Scripts/main.lua')
            messages=''.join(lua.globals().messages.values())
            self.assertIn('Ready: F7 or hold both triggers',messages)
            self.assertEqual('Esper mastery ready' in messages,esper)
            self.assertEqual('Battle presentation ready' in messages,fina)
            self.assertIn(100,set(lua.globals().loops.keys()))

    def test_old_adjoining_blocks_reproduce_users_exact_startup_failure(self):
        lua,code=self.combined_startup()
        broken=code.replace('\nend)();\n','\nend)()\n')
        with self.assertRaisesRegex(Exception,r'main.lua:\d+: attempt to call a nil value'):
            lua.execute(broken,name='@FFRStudioFieldLeader/Scripts/main.lua')
        self.assertNotIn('Battle presentation ready',''.join(lua.globals().messages.values()))

    def test_fina_movie_switch_only_controls_movie_runtime_and_is_reversible(self):
        import _ffr_fina_battle as fina
        import _ffr_fina_cinematic as movie
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            setting=root/testing.CONFIG;setting.parent.mkdir(parents=True)
            unit={'id':13503,'ffbe':{'id':fina.SPRITE,'source':'CUSTOM'}}
            runtime=root/'build/crystal-fina-battle/runtime.json';runtime.parent.mkdir(parents=True)
            runtime.write_text(json.dumps({'schema':1,'id':13503}))
            for value in (False,True,False):
                setting.write_text(json.dumps({'schema':1,'maxMr':False,'finaCinematic':value}))
                leader.build([unit],{'ROOT':root,'rows':lambda _:self.fail('No field cycling requires no map reads')})
                payload=json.loads((root/leader.STAGE).read_bytes())
                config=payload['files']['Scripts/config.lua']
                self.assertEqual('cinematicMovie' in config,value)
                self.assertEqual(movie.PRIVATE.replace('FFRS/Content/','/Game/') in config,value)
                self.assertIn('Battle presentation ready',payload['files']['Scripts/main.lua'])

    def field_fixture(self, mid=60):
        # Explicit synthetic FSsValue floats/cell hashes, including the native
        # unversioned nested-value header. No game assets in the fixture.
        def field(name, value): return {'Name': name, 'Value': value}
        keys = [field('0', [field('Value', [field('Type', kind)])]) for kind in ('FloatType', 'HashType')]
        attributes = [field(str(i), [field('Tag', tag), field('Key', [keys[i]])])
                      for i, tag in enumerate(('Posx', 'Cell'))]
        part = field('0', [field('Attributes', attributes)])
        animations = []; chunks = []
        for motion in ('idle', 'move', 'dash'):
            for direction in (2, 4, 6, 8):
                animations.append(field(str(len(animations)), [field('AnimationName', f'{motion}{direction}'),
                                  field('Settings', {'fps': 30, 'frames': 24}), field('PartAnimes', [part])]))
                chunks.append(struct.pack('<f', direction) + struct.pack('<i', 2) + struct.pack('<ii', 0, 0)
                              + b'\x80\x09\x0e\x03' + struct.pack('<f', 0) + struct.pack('<ii', 1, 0)
                              + b'\x80\x09\x0e\x01' + struct.pack('<i', 6) + b'cell0\x00')
        cell = field('0', [field('CellName', 'cell0'), field('Size', [field('Size', {'X': 64, 'Y': 64})])])
        view = {'NameMap': ['mapId', 'name', f'pc{mid:04d}', f'/Game/Chara/Field_Unit/pc{mid:04d}/pc{mid:04d}'],
                'NamesReferencedFromExportDataCount': 1,
                'Exports': [{'Extras': base64.b64encode(b''.join(chunks)).decode(), 'Data': [
                    field('AnimeList', [field('0', [field('AnimeList', animations)])]),
                    field('CellmapList', [field('0', [field('Cells', [cell])])])]}]}
        return view, chunks, animations

    def test_field_aliases_keep_native_animation_data_and_include_complete_keyframe_tails(self):
        view, chunks, animations = self.field_fixture()
        built = leader.field_aliases(view, 60)
        clips = built['Exports'][0]['Data'][0]['Value'][0]['Value'][0]['Value']
        self.assertEqual(clips[:12], animations)
        by_name = {c['Value'][0]['Value']: c for c in clips}
        refs = []
        payloads = leader.animation_payloads(clips, built['Exports'][0]['Extras'], built['NameMap'], refs)
        by_payload = dict(zip(by_name, payloads))
        self.assertEqual(payloads[:12], chunks)
        for motion in ('idle', 'move', 'dash', 'fieldidle'):
            for destination, source in ((1, 2), (3, 2), (7, 8), (9, 8)):
                source_motion = 'idle' if motion == 'fieldidle' else motion
                dst = f'{motion}{destination}'; src = f'{source_motion}{source}'
                self.assertEqual(by_name[dst]['Value'][1:], by_name[src]['Value'][1:])
                self.assertEqual(by_payload[dst], by_payload[src])
        self.assertEqual(len(clips), 32)
        self.assertTrue(all(r == [(0.0, 'cell0')] for r in refs))
        self.assertEqual(built['NamesReferencedFromExportDataCount'], len(built['NameMap']))
        self.assertIn('fieldidle9', built['NameMap']); self.assertIn(leader.DFINA, built['NameMap'])
        self.assertEqual(leader.field_aliases(built, 60), built)
        self.assertEqual(view['NamesReferencedFromExportDataCount'], 1)

    def test_npc_walking_clips_supply_player_move_dash_and_field_idle_without_empty_poses(self):
        view,chunks,animations=self.field_fixture(470)
        view=json.loads(json.dumps(view).replace('pc0470','npc0470'))
        clips=view['Exports'][0]['Data'][0]['Value'][0]['Value'][0]['Value'];del clips[8:]
        for clip in clips[4:]:clip['Value'][0]['Value']=clip['Value'][0]['Value'].replace('move','walk')
        view['Exports'][0]['Extras']=base64.b64encode(b''.join(chunks[:8])).decode()
        built=leader.field_aliases(view,470,target_package='/Game/Chara/StudioOverworld/party1001/npc0470',
            source_package='/Game/Chara/Field_Unit/npc0470/npc0470',walk_run_fallback=True)
        clips=built['Exports'][0]['Data'][0]['Value'][0]['Value'][0]['Value']
        names=[a['Value'][0]['Value'] for a in clips]
        payload=leader.animation_payloads(clips,built['Exports'][0]['Extras'],built['NameMap'])
        self.assertEqual(payload[:8],chunks[:8])
        by=dict(zip(names,payload))
        for motion in ('idle','move','dash','fieldidle'):
            for d in leader.DIRECTIONS:self.assertIn(f'{motion}{d}',by)
        self.assertEqual(by['move9'],by['walk8']);self.assertEqual(by['dash9'],by['walk8'])

    def test_existing_empty_diagonal_cells_fall_back_but_real_diagonal_pose_is_preserved(self):
        view, chunks, animations = self.field_fixture(20)
        for destination, source in (('idle1', animations[0]), ('move1', animations[4])):
            clip = copy.deepcopy(source); clip['Name'] = str(len(animations)); clip['Value'][0]['Value'] = destination
            animations.append(clip)
        valid = copy.deepcopy(animations[-2])
        blank = chunks[4].replace(b'cell0', b'blank')
        cells = view['Exports'][0]['Data'][1]['Value'][0]['Value'][0]['Value']
        cells.append({'Name': '1', 'Value': [{'Name': 'CellName', 'Value': 'blank'}, {'Name': 'Size', 'Value': []}]})
        view['Exports'][0]['Extras'] = base64.b64encode(b''.join(chunks + [chunks[0], blank])).decode()
        built = leader.field_aliases(view, 20)
        clips = built['Exports'][0]['Data'][0]['Value'][0]['Value'][0]['Value']
        by_name = {c['Value'][0]['Value']: c for c in clips}
        self.assertEqual(by_name['idle1'], valid)
        self.assertEqual(by_name['move1']['Value'][1:], by_name['move2']['Value'][1:])
        refs = []; payloads = leader.animation_payloads(clips, built['Exports'][0]['Extras'], built['NameMap'], refs)
        self.assertTrue(all(r == [(0.0, 'cell0')] for r in refs))
        self.assertEqual(payloads[13], chunks[4])
        self.assertIn(leader.package(20), built['NameMap'])
        self.assertEqual(animations[13]['Value'][0]['Value'], 'move1')
        self.assertIn(blank, base64.b64decode(view['Exports'][0]['Extras']))

    def test_no_visible_cardinal_donor_fails_before_building(self):
        view, _, _ = self.field_fixture()
        view['Exports'][0]['Data'][1]['Value'][0]['Value'][0]['Value'][0]['Value'][1]['Value'] = []
        with self.assertRaisesRegex(ValueError, 'no usable sprite cells'): leader.field_aliases(view, 60)

    def test_missing_alias_keyframe_tail_is_rejected_even_when_reflected_data_is_valid(self):
        view, _, _ = self.field_fixture(); built = leader.field_aliases(view, 60)
        # Reproduce the released regression: append reflected animations but
        # leave the original opaque keyframe tail untouched.
        built['Exports'][0]['Extras'] = view['Exports'][0]['Extras']
        with self.assertRaisesRegex(ValueError, 'animation payload'): leader.field_aliases(built, 60)

    def test_changed_or_truncated_native_payload_fails_before_building(self):
        view, chunks, animations = self.field_fixture()
        for raw in (b''.join(chunks)[:-1], b''.join(chunks) + b'\0',
                    b''.join(chunks).replace(b'\x80\x09\x0e', b'\x80\x09\x0f')):
            with self.subTest(raw=raw[:20]), self.assertRaisesRegex(ValueError, 'animation payload'):
                leader.animation_payloads(animations, base64.b64encode(raw).decode(), view['NameMap'])

    def test_bank_keeps_every_story_slot_identity_and_separate_overworld_choices(self):
        originals = map_rows(); before = copy.deepcopy(originals)
        rain = unit(); rain['overworld'] = choice()
        rows = lambda _: copy.deepcopy(originals)
        changes, config = leader.bank([rain], rows)
        for edit in changes:
            name = edit['row']; assets = edit['set']['animationAssetList']
            self.assertEqual(assets[:2], originals[name]['animationAssetList'])
            self.assertEqual(len(assets), 10)
            self.assertEqual(config['actors'][str(originals[name]['ID'])]['1002'], 3)
            self.assertIn('StudioOverworld/party1001', assets[2]['Ss6Project'])
            self.assertEqual(assets[7]['Ss6Project'], leader.DFINA)
            expected = dict(originals['ラスウェル']['animationAssetList'][0], Ss6Project=leader.package(20))
            self.assertEqual(assets[3], expected)
            self.assertEqual(config['defaults'][str(originals[name]['ID'])],2 if name==rain['jp'] else 0)
        self.assertEqual(originals, before)
        originals['フィーナ']['ID'] = 999
        with self.assertRaisesRegex(ValueError, 'assets changed'): leader.bank([], rows)

    def test_optional_setting_preserves_cave_and_party_combined_verification(self):
        from test_crystal_cave import cave_game, enabled
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); originals, _, fina = cave_game(); originals[leader.TABLE].update(map_rows())
            enabled(root)
            path = root / testing.CONFIG; value = json.loads(path.read_bytes()); value['fieldLeader'] = True
            path.write_text(json.dumps(value))
            rain = unit(); rain['overworld'] = choice()
            rows = lambda rel: copy.deepcopy(originals[rel])
            ops = testing.verification_operations(root, [fina, rain], rows)
            built = copy.deepcopy(originals[leader.TABLE])
            for edit in ops[leader.TABLE]['set']: built[edit['row']] = testing.apply_fields(built[edit['row']], edit['set'])
            for edit in ops[leader.TABLE]['add']: built[edit['row']] = testing.apply_fields(originals[leader.TABLE][edit['cloneFrom']], edit['set'])
            testing.check_rows(originals[leader.TABLE], built, ops[leader.TABLE])
            expected = testing.expected_edits(root, [fina, rain], rows)
            self.assertEqual(testing.apply_fields(originals[leader.TABLE]['レイン'], expected[(leader.TABLE, 'レイン')]), built['レイン'])
            self.assertEqual(len(built['レイン']['animationAssetList']), 10)

    def test_install_uses_built_payload_preserves_loader_and_rolls_back_owned_files(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / 'engine'; game = Path(directory) / 'game'
            binary = game / 'FFRS/Binaries/Win64'; (binary / 'ue4ss').mkdir(parents=True)
            (binary / 'dwmapi.dll').write_bytes(b'loader proxy')
            (binary / 'ue4ss/UE4SS.dll').write_bytes(b'loader')
            other = binary / 'ue4ss/Mods/Keybinds/Scripts/main.lua'; other.parent.mkdir(parents=True); other.write_text('existing helper')
            stage = root / leader.STAGE; stage.parent.mkdir(parents=True)
            payload = {'schema': 1, 'files': {'enabled.txt': '', 'Scripts/main.lua': 'first', 'Scripts/config.lua': 'config'}}
            stage.write_text(json.dumps(payload))
            leader.deploy(leader.install_plan(root, game), root / 'backups/first')
            main = game / leader.REL / 'Scripts/main.lua'
            self.assertEqual(main.read_text(), 'first'); self.assertEqual(other.read_text(), 'existing helper')
            payload['files']['Scripts/main.lua'] = 'second'; stage.write_text(json.dumps(payload))
            leader.deploy(leader.install_plan(root, game), root / 'backups/second')
            self.assertFalse((root / 'backups/second/field-leader.json').exists())
            self.assertTrue((root / 'field-leader-backups/second.json').exists())
            self.assertEqual(main.read_text(), 'second')
            leader.deploy(leader.restore_plan(root, game, 'second'))
            self.assertEqual(main.read_text(), 'first')
            main.write_text('user edit')
            with self.assertRaisesRegex(RuntimeError, 'Preserving'): leader.install_plan(root, game)
            self.assertEqual(main.read_text(), 'user edit')
            main.write_text('first')
            leader.deploy(leader.restore_plan(root, game))
            self.assertFalse(main.exists()); self.assertFalse((game / leader.REL / 'enabled.txt').exists())
            self.assertEqual(other.read_text(), 'existing helper')
            self.assertEqual((binary / 'dwmapi.dll').read_bytes(), b'loader proxy')

    def test_missing_loader_skips_runtime_without_blocking_asset_install(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / 'engine'; game = Path(directory) / 'game'
            payload = {'schema': 1, 'files': {'enabled.txt': '', 'Scripts/main.lua': 'code', 'Scripts/config.lua': 'config'}}
            plan = leader.install_plan(root, game, payload)
            self.assertTrue(plan['runtimeSkipped'])
            messages = []
            leader.deploy(plan, log=messages.append)
            self.assertIn('custom esper mastery', messages[0])
            self.assertFalse((game / leader.REL / 'enabled.txt').exists())
            # Disabling on a clean game needs no loader and never installs one.
            leader.deploy(leader.install_plan(root, game, {'schema': 1, 'files': {}}))
            self.assertFalse((game / 'FFRS/Binaries/Win64/ue4ss/UE4SS.dll').exists())

    def test_failed_deployment_restores_original_owned_payload(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / 'engine'; game = Path(directory) / 'game'
            binary = game / 'FFRS/Binaries/Win64/ue4ss'; binary.mkdir(parents=True)
            (binary / 'UE4SS.dll').write_bytes(b'loader'); (binary.parent / 'dwmapi.dll').write_bytes(b'proxy')
            payload = {'schema': 1, 'files': {'enabled.txt': '', 'Scripts/main.lua': 'code', 'Scripts/config.lua': 'config'}}
            leader.deploy(leader.install_plan(root, game, payload))
            before = (root / leader.STATE).read_bytes()
            plan = leader.install_plan(root, game, {'schema': 1, 'files': {}})
            atomic = leader.atomic
            def failure(path, data):
                if path == plan['state'] and data != before: raise OSError('disk full fixture')
                atomic(path, data)
            with mock.patch.object(leader, 'atomic', side_effect=failure):
                with self.assertRaisesRegex(OSError, 'disk full'): leader.deploy(plan)
            self.assertEqual((root / leader.STATE).read_bytes(), before)
            self.assertEqual((game / leader.REL / 'Scripts/main.lua').read_text(), 'code')
            self.assertTrue((game / leader.REL / 'enabled.txt').is_file())

    def test_lua_controller_cycles_active_party_and_guards_story_menu_battle_vehicle(self):
        from lupa.lua54 import LuaRuntime
        lua = LuaRuntime()
        fixture = (ROOT / 'scripts/fixtures/field_leader_runtime.lua').read_text()
        lua.execute(fixture)
        lua.execute((ROOT / 'assets/existing_visions/payload/field_leader.lua').read_text())
        lua.execute('run_tests()')

    def test_saved_walking_choice_stages_story_guards_without_enabling_cycling(self):
        for native in (False,True):
            with self.subTest(native=native),tempfile.TemporaryDirectory() as directory:
                root=Path(directory);rain=unit();rain.pop('ffbe')
                rain['overworld']={'version':1,'model':'native_party_1006'} if native else choice()
                rows=lambda _:map_rows()
                config=__import__('_ffr_overworld').runtime_config([rain],rows)
                self.assertEqual(config,{'schema':1,'cycling':0,'actors':{'10':{'1001':2}},'defaults':{'10':2}})
                # Staging the controller never regenerates an animation project.
                leader.build([rain],{'ROOT':root,'rows':rows})
                payload=json.loads((root/leader.STAGE).read_bytes())
                self.assertIn('["cycling"]=0',payload['files']['Scripts/config.lua'])
                self.assertIn('native characters return during events',payload['files']['Scripts/main.lua'])
                leader.build([],{'ROOT':root,'rows':lambda _:self.fail('Removed choice must not read tables')})
                self.assertEqual(json.loads((root/leader.STAGE).read_bytes())['files'],{})

    def test_lua_saved_choice_covers_field_idle_and_yields_for_entire_cutscene(self):
        from lupa.lua54 import LuaRuntime
        lua=LuaRuntime()
        lua.execute((ROOT/'scripts/fixtures/field_leader_runtime.lua').read_text())
        lua.execute('package.preload.config = function() return {schema=1,cycling=0, '
                    'actors={["10"]={["1001"]=5},["60"]={["1006"]=4}},defaults={["10"]=5,["60"]=4}} end')
        lua.execute((ROOT/'assets/existing_visions/payload/field_leader.lua').read_text())
        lua.execute('run_saved_choice_tests()')

    def walking_runtime(self,before=''):
        from lupa.lua54 import LuaRuntime
        lua=LuaRuntime()
        lua.execute((ROOT/'scripts/fixtures/field_leader_runtime.lua').read_text())
        lua.execute('package.preload.config = function() return {schema=1,cycling=0, '
                    'actors={["10"]={["1001"]=5},["60"]={["1006"]=4}},defaults={["10"]=5,["60"]=4}} end')
        if before:lua.execute(before)
        lua.execute((ROOT/'assets/existing_visions/payload/field_leader.lua').read_text())
        return lua

    def test_persistent_game_thread_loop_retains_callbacks_through_collection_and_scene_changes(self):
        lua=self.walking_runtime('''
            local weak=setmetatable({},{__mode='v'})
            function LoopInGameThreadWithDelay(ms,fn)
                assert(ms==150);weak[1]=fn
                tick=function() assert(weak[1],'Lost native walking callback');return weak[1]() end
            end
            function LoopAsync() error('Native loop needs no async bridge') end
            function ExecuteInGameThread() error('Already on the game thread') end
        ''')
        lua.execute("collectgarbage('collect'); run_saved_choice_tests(); "
                    "for _=1,30 do collectgarbage('collect');assert(tick()==false) end")

    def test_async_loop_and_scene_hooks_remain_reachable_when_the_loader_only_keeps_weak_references(self):
        lua=self.walking_runtime('''
            local weak=setmetatable({},{__mode='v'})
            function LoopAsync(ms,fn)
                assert(ms==150);weak[1]=fn
                tick=function() assert(weak[1],'Lost async walking callback');return weak[1]() end
            end
            function RegisterHook(path,pre,post) hooks[path]=setmetatable({pre,post},{__mode='v'}) end
        ''')
        lua.execute("collectgarbage('collect');run_saved_choice_tests()")

    def test_failed_native_loop_registration_uses_the_recoverable_bridge(self):
        lua=self.walking_runtime("function LoopInGameThreadWithDelay() error('unavailable fixture') end")
        lua.execute('run_saved_choice_tests()')

    def test_failed_queue_does_not_disable_saved_walking_for_the_session(self):
        lua=self.walking_runtime()
        lua.execute('''
            local original=ExecuteInGameThread
            ExecuteInGameThread=function() error('queue failure fixture') end
            assert(tick()==false and actor.m_AnimationAssetIndex==0)
            ExecuteInGameThread=original
            assert(tick()==false and actor.m_AnimationAssetIndex==5)
        ''')

    def test_lost_callback_retries_and_late_callbacks_cannot_release_new_requests_or_override_a_scene(self):
        lua=self.walking_runtime()
        lua.execute('''
            local original=ExecuteInGameThread
            local waiting={}
            ExecuteInGameThread=function(fn) waiting[#waiting+1]=fn end
            tick();assert(#waiting==1)
            collectgarbage('collect')
            for _=1,19 do tick() end
            assert(#waiting==1,'Avoid flooding a busy game thread')
            tick();assert(#waiting==2)
            waiting[1]();assert(actor.m_AnimationAssetIndex==0)
            tick();assert(#waiting==2,'Late callback must not release the new request')
            event=true;waiting[2]();assert(actor.m_AnimationAssetIndex==0,'Fresh scene guards run at execution')
            event=false;ExecuteInGameThread=original
            tick();assert(actor.m_AnimationAssetIndex==5)
        ''')

    def test_transient_title_or_actor_lookup_error_retries_without_losing_scene_guards(self):
        lua=self.walking_runtime()
        lua.execute('''
            local original=actor.GetMapUnitId
            actor.GetMapUnitId=function() error('actor transition fixture') end
            assert(tick()==false and actor.m_AnimationAssetIndex==0)
            actor.GetMapUnitId=original
            assert(tick()==false and actor.m_AnimationAssetIndex==5)
            event=true;tick();assert(actor.m_AnimationAssetIndex==0)
            event=false;tick();assert(actor.m_AnimationAssetIndex==5)
        ''')

    def test_missing_controller_hook_disables_cycling_without_appearance_writes(self):
        from lupa.lua54 import LuaRuntime
        lua = LuaRuntime()
        lua.execute((ROOT / 'scripts/fixtures/field_leader_runtime.lua').read_text())
        lua.execute('local original = StaticFindObject; StaticFindObject = function(path) '
                    'if path:find(":InputL1", 1, true) then return {IsValid = function() return false end} end '
                    'return original(path) end')
        lua.execute((ROOT / 'assets/existing_visions/payload/field_leader.lua').read_text())
        lua.execute('assert(actor.m_AnimationAssetIndex == 0); assert(keys[Key.F6] == nil); '
                    'assert(tick == nil); assert(messages[1]:find("Cycling disabled", 1, true))')


if __name__ == '__main__': unittest.main()
