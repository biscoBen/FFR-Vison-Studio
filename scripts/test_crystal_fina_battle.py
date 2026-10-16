"""Vision isolation and native Fina battle presentation contracts."""
import copy
from pathlib import Path
import sys
import struct
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'assets/existing_visions/payload'))
import _ffr_fina_battle as battle
import _ffr_fina_motion as motion


def p(name, value): return {'Name': name, 'Value': value, 'IsZero': False}
def soft(name, path): return p(name, {'AssetPath': {'PackageName': path, 'AssetName': Path(path).name}, 'SubPathString': None})
def table(rows): return {'NameMap': [], 'Exports': [{'Table': {'Data': rows}}]}
UNIT = {'id': 13503, 'jp': 'FixtureFina', 'donor': 13108, 'ffbe': {'id': battle.SPRITE, 'source': 'CUSTOM'}}


# Closed cube in native mesh coordinates; precomputed edges use the same ray
# contract as the original crystal. Its center is the body/socket origin.
def cube_triangles():
    vertices = [(x, y, z) for x in (-700, 700) for y in (-700, 700) for z in (-700, 700)]
    indices = [(0,1,3),(0,3,2),(4,6,7),(4,7,5),(0,4,5),(0,5,1),
               (2,3,7),(2,7,6),(0,2,6),(0,6,4),(1,5,7),(1,7,3)]
    return [[*vertices[a], *[vertices[b][i]-vertices[a][i] for i in range(3)],
                           *[vertices[c][i]-vertices[a][i] for i in range(3)]] for a,b,c in indices]


class FinaBattleTests(unittest.TestCase):
    def test_native_glow_clone_keeps_opaque_export_data_and_rejects_loss(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / 'Source.uasset'; source.write_bytes(b'header')
            source.with_suffix('.uexp').write_bytes(b'native parameter names, offsets, curves and VM')
            target = Path(tmp) / 'private/Glow.uasset'
            def clone(command):
                self.assertEqual(command[0], 'clone-package')
                target.write_bytes(b'private header')
                target.with_suffix('.uexp').write_bytes(source.with_suffix('.uexp').read_bytes())
            battle.clone_glow(source, target, UNIT, [], 'mapping', clone)
            def lossy(command):
                clone(command); target.with_suffix('.uexp').write_bytes(b'JSON dropped native metadata')
            with self.assertRaisesRegex(ValueError, 'export data changed'):
                battle.clone_glow(source, target, UNIT, [], 'mapping', lossy)

    def test_native_image_mirroring_requires_supported_tag_and_boolean_fallback(self):
        key = p('0', [p('Time', 0), p('Value', [p('Bool_temp', True)])])
        attr = p('0', [p('Tag', 'Imgfliph'), p('Key', [key])])
        part = p('0', [p('PartName', 'part_0'), p('Attributes', [attr])])
        clip = p('0', [p('AnimationName', 'attack_A'), p('PartAnimes', [part])])
        view = {'Exports': [{'Data': [p('AnimeList', [p('0', [p('AnimeList', [clip])])])]}]}
        spec = {'animations': [{'name': 'attack_A', 'parts': {'part_0': {'Imgfliph': [[0, 1.0]]}}}]}
        with patch.object(motion, 'decode', return_value={'attack_A': {'parts': {'part_0': {'Imgfliph': [[0, 1.0]]}}}}):
            motion.verify_image_mirroring(view, spec)
            key['Value'][1]['Value'][0]['Value'] = False
            with self.assertRaisesRegex(ValueError, 'bool cache'): motion.verify_image_mirroring(view, spec)

    def runtime(self):
        from lupa.lua54 import LuaRuntime
        import _ffr_field_leader as leader
        lua = LuaRuntime()
        config = battle.runtime_config(UNIT, {'X': -.29, 'Y': -2.08, 'Z': 1233}, cube_triangles())
        lua.execute('package.preload.config = function() return ' + leader.lua({'schema': 1, 'actors': {}, 'fina': config}) + ' end')
        root = Path(__file__).resolve().parent.parent
        lua.execute((root / 'scripts/fixtures/fina_battle_runtime.lua').read_text())
        lua.execute((root / 'assets/existing_visions/payload/fina_battle.lua').read_text())
        return lua

    def test_runtime_uses_direct_components_and_preserves_native_attack_playback(self):
        lua = self.runtime()
        lua.execute('run_fina_tests()')

    def test_runtime_reads_game_parameter_names_instead_of_assuming_upstream_spelling(self):
        for fields in (('OutAnimPackName', 'OutAnimationName'), ('AnimationPack', 'Animation'),
                       ('Second', 'First')):
            with self.subTest(fields=fields):
                lua = self.runtime()
                lua.globals().sprite.outputFields = lua.table_from(fields)
                lua.execute('run_fina_tests()')

    def test_transient_missing_animation_outputs_keep_crystal_and_retry_without_aborting(self):
        lua = self.runtime()
        lua.execute('sprite.namesUnavailable=true; tick(); assert(#meshes==1 and meshes[1].visible); '
                    'assert(not meshes[1].invalid); sprite.namesUnavailable=false; run_fina_tests()')

    def test_no_glow_is_created_while_seated_or_reforming(self):
        lua = self.runtime()
        lua.execute("""
            tick(); sprite.playing='lb1_before'; tick()
            sprite.playing='LB1'; sprite.frame=164; tick(); assert(glows[1].invalid)
            for _, frame in ipairs({183,210,246,258,282,431,0}) do
                sprite.frame=frame; tick(); assert(#glows==1)
            end
            sprite.playing='Idle'; tick(); sprite.playing='lb1_before'; tick()
            assert(#glows==2 and glows[2].activationAlpha==1)
        """)

    def test_runtime_config_uses_the_current_private_assets_and_shortened_hold(self):
        cfg = battle.runtime_config(UNIT, {'X': 1, 'Y': 2, 'Z': 3}, cube_triangles())
        self.assertEqual(cfg['id'], UNIT['id'])
        self.assertIn('/13503/', cfg['mesh'])
        self.assertNotIn('cast', cfg)
        self.assertNotIn('castFrames', cfg)
        self.assertEqual(cfg['glowAlpha'], 2.0)
        self.assertEqual(cfg['glassFallbackBias'], 12.0)
        self.assertEqual(cfg['bodyRefraction'], .2)
        self.assertEqual(cfg['flashes'], [(0, 0, 134, 164)])
        self.assertEqual(cfg['reform'] - motion.SEAT, 75)
        job = {'asset': 'unchanged'}
        self.assertIs(battle.prepare_job(job, [UNIT], lambda _: 1), job)

    def test_body_ray_measures_rotated_scaled_mesh_and_applies_reduced_warp(self):
        lua = self.runtime()
        # Uniform and nonuniform scales; translated camera/mesh and the actual
        # mesh rotation must not be mistaken for component depth scale alone.
        for scale in (.002, .138, .42, 20):
            with self.subTest(scale=scale):
                lua.execute(f'sprite.parentScale={{X={scale}/.12,Y=2,Z=3}}; camera.location={{X=100000,Y=0,Z=0}}; time=0; tick()')
                bias = lua.globals().materials[1]['RefractionDepthBias']
                depth = scale * 700
                strength = depth / max(1, min(bias*.5, 50)) - bias
                self.assertAlmostEqual(strength, .2)
        lua.execute('sprite.parentScale={X=1,Y=1,Z=1}; time=12.5; tick()')  # 45 degree turn.
        bias = lua.globals().materials[1]['RefractionDepthBias']
        self.assertAlmostEqual(84 * 2**.5 / (bias*.5)-bias, .2, delta=.0001)
        lua.execute('assert(#materials==1 and materials[1].source.path==require("config").fina.material)')
        self.assertTrue(any('Glass ray depth=' in line for line in lua.globals().messages.values()))

    def test_overlapping_shells_use_front_surface_nearest_camera(self):
        import _ffr_field_leader as leader
        outer = cube_triangles()
        inner = [[value*.5 for value in tri] for tri in outer]
        lua = self.runtime()
        lua.execute('require("config").fina.glassTriangles='+leader.lua(inner+outer))
        lua.execute('tick()')
        bias = lua.globals().materials[1]['RefractionDepthBias']
        self.assertAlmostEqual(84/(bias*.5)-bias, .2)

    def test_deeper_lower_body_drives_attenuation_rather_than_center_only(self):
        import _ffr_field_leader as leader
        # Shear the native cube so its lower bulb is deeper than its midpoint.
        triangles = cube_triangles()
        for t in triangles:
            t[0] -= .25*t[2]; t[3] -= .25*t[5]; t[6] -= .25*t[8]
        lua = self.runtime()
        lua.execute('require("config").fina.glassTriangles='+leader.lua(triangles))
        lua.execute('camera.location={X=100000,Y=0,Z=0}; tick()')
        bias = lua.globals().materials[1]['RefractionDepthBias']
        self.assertLess(84/(bias*.5)-bias, .2)
        self.assertAlmostEqual(100.875/(bias*.5)-bias, .2, delta=.01)

    def test_missing_camera_keeps_casing_and_accepted_fallback_then_recovers(self):
        lua = self.runtime()
        lua.execute('camera.invalid=true; tick(); assert(meshes[1].visible and not meshes[1].invalid); '
                    'assert(materials[1].RefractionDepthBias==12); camera.invalid=false; tick(); '
                    'assert(materials[1].RefractionDepthBias~=12)')

    def test_skill_motion_duration_uses_release_window_without_imported_csv(self):
        import _ffr_animation_repair as repair
        self.assertEqual(repair.motion_seconds(UNIT, '/no-source-needed', True), .5)
        self.assertEqual(repair.motion_seconds(UNIT, '/no-source-needed', False), .5)

    def test_model_readback_rejects_orphan_attachments_and_inherited_body_offsets(self):
        parts = [{'name': 'root', 'parent': -1, 'type': 'Null'},
                 {'name': 'part_0', 'parent': 0, 'type': 'Normal'},
                 {'name': 'NULL_Crystal', 'parent': 0, 'type': 'Null'}]
        native = [{'Value': [p('PartName', x['name']), p('ParentIndex', x['parent']),
                            p('Type', x['type']), p('ArrayIndex', i)]} for i, x in enumerate(parts)]
        model = [p('PartList', native), p('MeshList', []), p('BoneList', [])]
        view = {'Exports': [{'Data': [p('AnimeList', [{'Value': [p('Model', model)]}])]}]}
        motion.verify_model(view, {'model': {'parts': parts}})
        native[1]['Value'][1]['Value'] = 2
        with self.assertRaisesRegex(ValueError, 'model parts/parents'): motion.verify_model(view, {'model': {'parts': parts}})
        native[1]['Value'][1]['Value'] = 0; native.pop()
        with self.assertRaisesRegex(ValueError, 'model parts/parents'): motion.verify_model(view, {'model': {'parts': parts}})

    def test_nonpositive_scale_fields_are_explicitly_written_only_on_the_current_fina(self):
        fallback = struct.unpack('<f', struct.pack('<f', 2.7))[0]
        for sprite, effect, expected in [(0, 0, (fallback, 1.0)), (2.5, 0, (2.5, 1.0)),
                                         ('+0', 1.4, (fallback, 1.4)), (-1, -1, (fallback, 1.0)), (3.0, 2.0, (3.0, 2.0))]:
            row = {'Name': UNIT['jp'], 'Value': [p('ID', UNIT['id']), p('Scale', sprite),
                p('attachEffectSacle', effect), p('attackOffsetLocation', {'keep': 42})]}
            other = {'Name': 'Donor', 'Value': [p('ID', 13108), p('Scale', 0), p('attachEffectSacle', 0)]}
            source = table([row, other]); before = copy.deepcopy(source)
            with self.subTest(sprite=sprite, effect=effect):
                built, scales = battle.design_table(source, UNIT)
                self.assertEqual(scales, expected); self.assertEqual(source, before)
                rows = battle.table_rows(built); self.assertEqual(rows[1], other)
                self.assertEqual(rows[0]['Value'][3], row['Value'][3])
                self.assertEqual(tuple(battle.cave.property_data(rows[0], name)['Value'] for name in ('Scale', 'attachEffectSacle')), expected)

    def test_invalid_scale_data_and_ambiguous_owners_still_fail(self):
        for value in (float('nan'), float('inf'), True, 'garbage'):
            row = {'Name': UNIT['jp'], 'Value': [p('ID', UNIT['id']), p('Scale', value), p('attachEffectSacle', 1)]}
            with self.subTest(value=value), self.assertRaises(ValueError): battle.design_table(table([row]), UNIT)
        with self.assertRaises(ValueError): battle.design_table(table([]), UNIT)

    def test_only_selected_custom_fina_is_replaced(self):
        self.assertIsNone(battle.selected([{'id': 13108}]))
        self.assertEqual(battle.selected([UNIT]), UNIT)
        for units in ([UNIT, UNIT], [dict(UNIT, id=-1)], [dict(UNIT, ffbe=dict(UNIT['ffbe'], source='GLOBAL'))]):
            with self.assertRaises(ValueError): battle.selected(units)

    def test_fresh_battle_table_keeps_all_other_units_and_nonappearance_fields(self):
        animation = {'Value': [soft('Ss6Project', '/Game/Chara/summon/summon13503/summon13503'),
            *[soft(n, '/original/' + n) for n in ('Material', 'textureBaseColor', 'textureNormal', 'textureMetallicRoughness')],
            p('isVisionCharacter', True)]}
        fina = {'Name': UNIT['jp'], 'Value': [p('ID', 13503), p('animationAssetList', [animation]), p('soundData', {'keep': True})]}
        other = {'Name': 'Other', 'Value': [p('ID', 13108), p('animationAssetList', []), p('soundData', {'different': True})]}
        source = table([fina, other]); before = copy.deepcopy(source)
        built = battle.battle_table(source, UNIT); rows = battle.table_rows(built)
        self.assertEqual(source, before); self.assertEqual(rows[1], other)
        self.assertEqual(rows[0]['Value'][2], fina['Value'][2])
        values = {q['Name']: q['Value'] for q in battle.cave.property_data(rows[0], 'animationAssetList')['Value'][0]['Value']}
        self.assertFalse(values['isVisionCharacter'])
        self.assertIn('/StudioCrystalFinaBattle/13503/', values['Ss6Project']['AssetPath']['PackageName'])
        self.assertTrue(values['Material']['AssetPath']['PackageName'].endswith('/M_Ss_Component_PBRBattle'))
        changed = copy.deepcopy(source); changed['Exports'][0]['Table']['Data'][0]['Name'] = 'WrongOwner'
        with self.assertRaises(ValueError): battle.battle_table(changed, UNIT)

    def test_motion_spec_completes_cast_and_restores_crystal_after_exact_seated_hold(self):
        from PIL import Image
        names = [('openarmidle2', 49), ('openarmopeneye2', 65), ('curlup2', 73), ('magicattack6', 91), ('down6', 49)]
        clips = {name: {'fps': 60, 'frameCount': count, 'parts': {'part_0': {'Cell': [[0, {'mapId': 0, 'name': name}]]}}}
                 for name, count in names}
        clips['magicattack6']['parts']['part_0']['Cell'] += [
            [66, {'mapId': 0, 'name': 'shot_start'}], [74, {'mapId': 0, 'name': 'shot_end'}]]
        def vec(name, x, y): return p(name, [p(name, {'X': x, 'Y': y})])
        cell_names = [name for name, _ in names] + ['shot_start', 'shot_end']
        cells = [{'Value': [p('CellName', name), vec('Pos', i * 10, 0), vec('Size', 8, 8), vec('Pivot', 0, 0)]}
                 for i, name in enumerate(cell_names)]
        view = {'Exports': [{'Data': [p('AnimeList', []), p('CellmapList', [{'Value': [p('Cells', cells)]}])]}]}
        original = {'animations': [{'name': name, 'frameCount': count} for name, count in [('idle', 49), ('command', 30), ('magic_idle', 30), ('LB1_before', 60), ('attack_A', 117), ('magic_attack', 80), ('LB1', 400), ('Setup', 1)]]}
        before = copy.deepcopy(original)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'seat.png'; sheet = Image.new('RGBA', (1800, 1820)); sheet.paste((255, 0, 0, 255), (1122, 1497, 1158, 1534)); sheet.save(path)
            with patch.object(motion, 'decode', return_value=clips), patch.object(motion, 'extract_atlas', return_value=Image.new('RGBA', (256, 512))):
                atlas, spec = motion.battle_spec(view, {}, path, original)
        self.assertEqual(original, before); self.assertEqual(atlas.getpixel((0, 330)), (255, 0, 0, 255))
        clips = {a['name']: a for a in spec['animations']}
        # Native release begins with the hands-forward shot; preparation has
        # already shown eyes/turn/charge. No full cast survives into recovery.
        for name in ('attack_A', 'magic_attack'):
            self.assertEqual(clips[name]['frameCount'], 30)
            self.assertEqual(clips[name]['parts']['part_0']['Cell'][0], [0, 'shot_start'])
            self.assertEqual(clips[name]['parts']['part_0']['Cell'][-1][1], 'shot_end')
        for name in ('command', 'magic_idle'):
            self.assertEqual(clips[name]['frameCount'], 30)
            self.assertEqual([value for _, value in clips[name]['parts']['part_0']['Cell']],
                             ['openarmopeneye2', 'curlup2', 'magicattack6'])
        self.assertEqual(clips['Studio_FinaCast']['frameCount'], 60)
        self.assertIn([30, 'shot_start'], clips['Studio_FinaCast']['parts']['part_0']['Cell'])
        self.assertEqual(clips['LB1_before']['parts']['NULL_Aura']['Posy'], [[0, 183.5 / 2.7]])
        self.assertEqual(clips['Studio_FinaCast']['parts']['part_0']['Imgfliph'], [[0, 1.0]])
        self.assertEqual(clips['LB1']['parts']['part_0']['Imgfliph'], [[0, 1.0], [258, 0.0]])
        self.assertTrue(all('Fliph' not in clip['parts']['part_0'] for clip in clips.values()))
        self.assertEqual(clips['idle']['frameCount'], 6000)
        self.assertAlmostEqual(clips['idle']['parts']['NULL_Crystal']['Roty'][-1][1], 359.94)
        self.assertEqual(clips['LB1']['parts']['NULL_Crystal']['Posy'][1:], [[134, -10000.0], [258, 183.5 / 2.7]])
        self.assertIn([183, 'original_jacket_free_seated'], clips['LB1']['parts']['part_0']['Cell'])
        self.assertEqual(clips['LB1']['parts']['part_0']['Cell'][-1][1], 'openarmidle2')
        self.assertIn([183, 0.0], clips['LB1']['parts']['part_0']['Posy'])
        self.assertEqual(clips['LB1']['parts']['part_0']['Posy'][-1], [258, 22.0 + motion.BODY_FLOAT])
        self.assertIn([183, 14.5], clips['LB1']['parts']['NULL_Aura']['Posy'])
        model = spec['model']['parts']
        self.assertEqual({p['name'] for p in model}, set(clips['idle']['parts']))
        self.assertTrue(all(p['parent'] == ( -1 if p['name'] == 'root' else 0) for p in model))


if __name__ == '__main__': unittest.main()
