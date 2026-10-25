"""Directional field sprites and independent party appearance contracts."""
import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from types import SimpleNamespace
from unittest import mock
import io

from test_existing_visions import ROOT, party
from test_party_characters import unit, battle_rows

field = sys.modules['_ffr_overworld']


def choice(): return {'version': 1, 'model': field.MODEL}


def map_rows():
    rows = {}
    for id, jp, _, _ in party.CHARACTERS:
        mid = (id-1000)*10; path = f'/Game/Chara/Field_Unit/pc{mid:04d}/pc{mid:04d}'
        rows[jp] = {'ID': mid, 'Name': jp, 'Footstep': 'Native', 'animationAssetList': [
            {'Ss6Project': path, 'Material': 'native field shader', 'textureBaseColor': path+'_tex',
             'textureNormal': path+'_normal', 'textureMetallicRoughness': path+'_mreo', 'isVisionCharacter': False},
            {'Ss6Project': path+'_scene'}]}
    path='/Game/Chara/Field_Unit/npc0470/npc0470'
    charlotte=copy.deepcopy(rows['レイン'])
    charlotte.update(ID=470,Name='シャルロット')
    charlotte['animationAssetList']=[dict(charlotte['animationAssetList'][0],Ss6Project=path,
        textureBaseColor=path+'_tex',textureNormal=path+'_normal',textureMetallicRoughness=path+'_mreo'),
        {'Ss6Project':path+'_00'},{'Ss6Project':path+'_01'},{'Ss6Project':'native Charlotte vision'}]
    rows['シャルロット']=charlotte
    return rows


class OverworldTests(unittest.TestCase):
    def test_charlotte_uses_the_native_npc_project_and_preserves_her_original_story_and_vision_slots(self):
        source=map_rows();before=copy.deepcopy(source)
        for uid,*_ in party.CHARACTERS:
            rain=unit(uid);rain.pop('ffbe');rain['overworld']={'version':1,'model':'native_charlotte'}
            party.validate(rain);ops={};field.prepare(ops,[rain],lambda _:source)
            built=copy.deepcopy(source);edit,=ops[field.TABLE]['set'];built[rain['jp']].update(edit['set'])
            field.check_rows(source,built,[rain])
            self.assertEqual(built['シャルロット'],before['シャルロット'])
            self.assertEqual(built[rain['jp']]['animationAssetList'][:-1],source[rain['jp']]['animationAssetList'])
            appended=built[rain['jp']]['animationAssetList'][-1]
            self.assertEqual(appended['Ss6Project'],f'/Game/Chara/StudioOverworld/party{uid}/npc0470')
            for key in ('textureBaseColor','textureNormal','textureMetallicRoughness'):
                self.assertEqual(appended[key],source['シャルロット']['animationAssetList'][0][key])
        self.assertEqual(source,before)

    def test_charlotte_generation_clones_native_npc_animation_without_texture_conversion(self):
        from test_field_leader import FieldLeaderTests
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);rain=unit();rain.pop('ffbe');rain['overworld']={'version':1,'model':'native_charlotte'}
            source=root/'legacy/FFRS/Content/Chara/Field_Unit/npc0470/npc0470.uasset';source.parent.mkdir(parents=True)
            source.write_bytes(b'original project');source.with_suffix('.uexp').write_bytes(b'original payload')
            original=FieldLeaderTests().field_fixture(470)[0]
            original=json.loads(json.dumps(original).replace('pc0470','npc0470'));calls=[]
            def run(cmd):
                calls.append(cmd)
                if cmd[1]=='tojson':Path(cmd[3]).write_text(json.dumps(original))
                elif cmd[1]=='fromjson':
                    target=Path(cmd[3]);target.write_bytes(Path(cmd[2]).read_bytes());target.with_suffix('.uexp').write_bytes(b'payload')
                else:self.fail('A native NPC must not convert textures or use FFBE packs')
            field.generate(rain,{'ROOT':root,'LEGACY':root/'legacy','OUT':root/'out','FFRDT':['tool'],'USMAP':'fixture','run':run})
            target=root/'out/FFRS/Content/Chara/StudioOverworld/party1001/npc0470.uasset'
            view=json.loads(target.read_bytes())
            self.assertIn(field.package(rain),view['NameMap'])
            self.assertNotIn(field.native_package(field.CHARLOTTE),view['NameMap'])
            self.assertEqual([c[1] for c in calls],['tojson','fromjson'])

    def test_native_party_choices_keep_source_textures_story_slots_and_battle_identity(self):
        original=map_rows();before=copy.deepcopy(original)
        for donor,source_jp,*_ in party.CHARACTERS:
            rain=unit();rain['overworld']={'version':1,'model':f'native_party_{donor}'}
            snapshot=copy.deepcopy(rain);party.validate(rain)
            operations={};field.prepare(operations,[rain],lambda _:original)
            edit,=operations[field.TABLE]['set'];built=copy.deepcopy(original)
            built[rain['jp']].update(edit['set'])
            field.check_rows(original,built,[rain])
            self.assertEqual(len(edit['set']),1)
            self.assertEqual(built[rain['jp']]['animationAssetList'][:-1],original[rain['jp']]['animationAssetList'])
            for texture in ('textureBaseColor','textureNormal','textureMetallicRoughness'):
                self.assertEqual(built[rain['jp']]['animationAssetList'][-1][texture],original[source_jp]['animationAssetList'][0][texture])
            self.assertIn('/StudioOverworld/party1001/',built[rain['jp']]['animationAssetList'][-1]['Ss6Project'])
            self.assertEqual(rain,snapshot)
        self.assertEqual(original,before)
        with self.assertRaises(ValueError):field.validate({'version':1,'model':'native_party_9999'})
        broken=copy.deepcopy(original);broken['魔人フィーナ']['animationAssetList'][0]['textureBaseColor']='unexpected'
        with self.assertRaisesRegex(ValueError,'selected original'):
            field.prepare({},[dict(unit(),overworld={'version':1,'model':'native_party_1006'})],lambda _:broken)

    def test_native_generation_keeps_drawable_native_clips_and_reuses_the_project_on_warm_builds(self):
        from test_field_leader import FieldLeaderTests
        import _ffr_build_cache as cache
        import _ffr_field_leader as leader
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);rain=unit();rain['overworld']={'version':1,'model':'native_party_1006'}
            source=root/'legacy/FFRS/Content/Chara/Field_Unit/pc0060/pc0060.uasset';source.parent.mkdir(parents=True)
            source.write_bytes(b'original project');source.with_suffix('.uexp').write_bytes(b'original payload')
            original=FieldLeaderTests().field_fixture(60)[0];calls=[]
            def run(cmd):
                calls.append(cmd)
                if cmd[1]=='tojson':Path(cmd[3]).write_text(json.dumps(original))
                elif cmd[1]=='fromjson':
                    target=Path(cmd[3]);target.write_bytes(Path(cmd[2]).read_bytes());target.with_suffix('.uexp').write_bytes(b'native copied payload')
                else:self.fail('Native field choice must not convert sprites/textures or download artwork')
            env={'ROOT':root,'LEGACY':root/'legacy','OUT':root/'out','FFRDT':['tool'],'USMAP':'fixture','run':run}
            reuse=cache.Cache(root,{'nativeField':1})
            with mock.patch.object(cache,'_active',reuse):
                field.generate(rain,env)
                target=root/'out/FFRS/Content/Chara/StudioOverworld/party1001/pc0060.uasset'
                output=target.read_bytes();built=json.loads(output)
                self.assertIn(field.package(rain),built['NameMap'])
                self.assertNotIn('fieldidle9', [v for v in built['NameMap'] if v.startswith('/Game/')])
                self.assertEqual(leader.field_aliases(built,60,target_package=field.package(rain)),built)
                target.unlink();target.with_suffix('.uexp').unlink()
                field.generate(rain,env)
                self.assertEqual(target.read_bytes(),output)
                self.assertEqual(len(calls),2)
                self.assertEqual(reuse.stats['party-native-field']['reused'],1)

    def test_every_catalog_loop_has_character_pixels_and_no_inserted_standing_pose(self):
        from PIL import Image
        from build_overworld_catalog import audit, cell, has_character
        models = field.catalog()['models']
        self.assertEqual(len(models), 9)
        self.assertEqual(sum(x['directions'] == 8 for x in models.values()), 4)
        for key, entry in models.items():
            with self.subTest(model=key):
                choice = {'version': 1, 'model': key}; field.validate(choice)
                image = Image.open(io.BytesIO(field.asset_bytes(entry, 'sheet'))).convert('RGBA')
                self.assertEqual(list(image.size), entry['size'])
                self.assertIsNotNone(Image.open(io.BytesIO(field.asset_bytes(entry, 'icon'))).getbbox())
                audited, _ = audit(image)
                self.assertEqual(audited['directions'], entry['directions'])
                self.assertEqual(audited['motions'], entry['motions'])
                animations = {a['name']: a for a in field.spec('pc0020', choice)['animations']}
                self.assertEqual(len(animations), 52)
                for direction, _ in field.DIRECTIONS:
                    for motion in ('idle', 'move', 'dash'):
                        frames = entry['motions'][f'{motion}{direction}']
                        self.assertTrue(all(has_character(cell(image, r, c)) for r, c in frames))
                        self.assertEqual(animations[f'fieldidle{direction}']['parts'], animations[f'idle{direction}']['parts'])
                        if motion == 'idle': continue
                        self.assertTrue(all(c > 0 for _, c in frames))
                        self.assertGreaterEqual(len({cell(image, r, c).tobytes() for r, c in frames}), 2)
                        for row, col in frames:
                            idle_row = row % 8
                            rests = {cell(image, idle_row, c).tobytes() for c in range(7)
                                     if has_character(cell(image, idle_row, c))}
                            self.assertNotIn(cell(image, row, col).tobytes(), rests)
                if entry['directions'] == 4:
                    self.assertEqual(entry['motions']['dash1'], entry['motions']['dash2'])
                    self.assertEqual(entry['motions']['dash7'], entry['motions']['dash8'])

    def test_shadow_slots_and_mid_loop_standing_frames_are_not_treated_as_movement(self):
        from PIL import Image, ImageDraw
        from build_overworld_catalog import audit, has_character
        shadow = Image.new('RGBA', (64, 64)); ImageDraw.Draw(shadow).ellipse((14, 50, 50, 57), fill=(20, 20, 20, 190))
        self.assertIsNotNone(shadow.getbbox()); self.assertFalse(has_character(shadow))
        sheet = Image.new('RGBA', (448, 1536))
        for row in range(24):
            for col in range(7): sheet.paste(shadow, (col * 64, row * 64))
        for row in range(4):
            idle = Image.new('RGBA', (64, 64)); ImageDraw.Draw(idle).rectangle((22, 12, 40, 54), fill='red')
            for offset in (0, 8, 16): sheet.paste(idle, (0, (row + offset) * 64))
            for offset in (8, 16):
                for col in range(1, 7):
                    pose = idle.copy(); ImageDraw.Draw(pose).rectangle((col + 5, 30, col + 12, 40), fill='yellow')
                    sheet.paste(pose, (col * 64, (row + offset) * 64))
                sheet.paste(idle, (3 * 64, (row + offset) * 64))
        value, removed = audit(sheet)
        self.assertEqual(value['directions'], 4)
        self.assertEqual(removed['move2'], [0, 3])
        self.assertEqual(value['motions']['move2'], [[16, c] for c in (1, 2, 4, 5, 6)])

    def test_corrupt_field_archive_is_rejected_before_generation(self):
        entry = field.model()
        with mock.patch.object(field.Path, 'read_bytes', return_value=b'corrupt archive'):
            with self.assertRaisesRegex(ValueError, 'checksum'): field.asset_bytes(entry, 'sheet')

    def test_install_verifiers_share_cave_and_field_expectations_and_reject_corruption(self):
        from test_crystal_cave import cave_game, enabled, testing, cave
        for cave_on, field_on in ((True, True), (False, True), (True, False)):
            with self.subTest(cave=cave_on, field=field_on), tempfile.TemporaryDirectory() as directory:
                root = Path(directory); originals, _, fina = cave_game()
                originals[field.TABLE].update(map_rows())
                rain = unit(); rain.pop('ffbe')
                if field_on: rain['overworld'] = choice()
                units = [fina, rain]
                config = root/'mods/EstherTsukiko'; config.mkdir(parents=True)
                (config/'units.json').write_text(json.dumps(units))
                if cave_on: enabled(root)
                rows = lambda rel: copy.deepcopy(originals[rel])
                operations = testing.prepare({}, units, root, rows)
                field.prepare(operations, [rain], rows)
                recipe = root/'build/visions_mod/patch.json'; recipe.parent.mkdir(parents=True, exist_ok=True)
                recipe.write_text(json.dumps({'tables':list(operations.values())}))
                built = copy.deepcopy(originals)
                for rel, operation in operations.items():
                    for e in operation['set']:
                        built[rel][e['row']] = testing.apply_fields(built[rel][e['row']], e['set'])
                    for e in operation['add']:
                        built[rel][e['row']] = testing.apply_fields(originals[rel][e['cloneFrom']], e['set'])
                for rel, value in originals.items():
                    path = root/'extracted/rows'/(rel+'.json'); path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_text(json.dumps({'rows': value}))
                if field_on:
                    base = root/'build/visions_mod/assets/FFRS/Content'/field.package(rain).removeprefix('/Game/')
                    base.parent.mkdir(parents=True)
                    for suffix in ('', '_tex', '_normal', '_mreo'):
                        for extension in ('.uasset', '.uexp'):
                            base.with_name(base.name+suffix).with_suffix(extension).write_bytes(b'explicit file fixture')
                def decode(args, **_):
                    asset, target = args[2:4]
                    asset = asset.replace('\\', '/')
                    rel = asset.split('FFRS/Content/Datatable/')[1].removesuffix('.uasset')
                    source = built if '/build/visions_mod/' in asset else originals
                    Path(target).write_text(json.dumps({'rows': source[rel]}))
                windows_readback = root/'windows-path-readback.json'
                asset = root/'build/visions_mod/assets/FFRS/Content/Datatable'/(field.TABLE+'.uasset')
                decode(['fixture-tool', 'rows', str(asset).replace('/', '\\'), str(windows_readback)])
                self.assertEqual(json.loads(windows_readback.read_text())['rows'], built[field.TABLE])
                with mock.patch('subprocess.run', side_effect=decode):
                    testing.verify(root, ['fixture-tool'], 'fixture.usmap')
                    party.verify(root, ['fixture-tool'], 'fixture.usmap')
                    if cave_on and field_on:
                        correct = copy.deepcopy(built[field.TABLE])
                        changes = (
                            lambda value: value[rain['jp']].update(Footstep='Wrong'),
                            lambda value: value.pop(cave.NAME),
                            lambda value: value[cave.NAME]['animationAssetList'][0].update(Ss6Project='Wrong'),
                            lambda value: value.update(Unexpected={'ID': 99999}),
                        )
                        for change in changes:
                            built[field.TABLE] = copy.deepcopy(correct); change(built[field.TABLE])
                            with self.assertRaises(ValueError): testing.verify(root, ['fixture-tool'], 'fixture.usmap')
                            with self.assertRaises(ValueError): party.verify(root, ['fixture-tool'], 'fixture.usmap')

    def test_field_choice_is_sparse_independent_and_rejects_unsupported_sheets(self):
        u = unit(); u['overworld'] = choice(); before = copy.deepcopy(u)
        self.assertEqual(party.validate(u), before)
        original = dict(u); original.pop('ffbe'); self.assertEqual(party.validate(original), original)
        for value in (None, {'version': True, 'model': field.MODEL}, {'version': 2, 'model': field.MODEL},
                      {'version': 1, 'model': 'a2'}, dict(choice(), path='../other.png')):
            with self.subTest(value=value), self.assertRaises(ValueError):
                party.validate(dict(u, overworld=value))

    def test_all_eight_field_rows_keep_special_scene_clips_battle_choices_and_unselected_rows(self):
        originals = map_rows(); battle = battle_rows(); source = {field.TABLE: originals, party.TABLE: battle}
        for id, jp, _, _ in party.CHARACTERS:
            u = unit(id); u['overworld'] = choice(); before = copy.deepcopy(u)
            operations = {}; party.prepare(operations, [u], lambda rel: copy.deepcopy(source[rel]))
            self.assertEqual(set(operations), {field.TABLE, party.TABLE})
            field_op = operations[field.TABLE]['set'][0]
            self.assertEqual(field_op['row'], jp); self.assertEqual(len(field_op['set']), 1)
            built = copy.deepcopy(originals)
            built[jp].update(field_op['set'])
            field.check_rows(originals, built, [u])
            self.assertEqual(built[jp]['animationAssetList'][:-1], originals[jp]['animationAssetList'])
            self.assertEqual(built[jp]['animationAssetList'][0]['Material'], 'native field shader')
            changed = copy.deepcopy(built); changed[jp]['Name'] = 'Vagrant Rain'
            with self.assertRaises(ValueError): field.check_rows(originals, changed, [u])
            changed = copy.deepcopy(built); changed[jp]['animationAssetList'][1]['Ss6Project'] = 'other scene'
            with self.assertRaises(ValueError): field.check_rows(originals, changed, [u])
            self.assertEqual(u, before)
            only_field = dict(u); only_field.pop('ffbe'); operations = {}
            party.prepare(operations, [only_field], lambda rel: copy.deepcopy(source[rel]))
            self.assertEqual(set(operations), {field.TABLE})
        operations = {}; field.prepare(operations, [unit()], lambda _: self.fail('disabled field choice read a table'))
        self.assertFalse(operations)
        with self.assertRaises(ValueError): field.prepare({}, [dict(unit(), overworld=choice())], lambda _: {})

    def test_bundled_sheet_and_keypad_motion_cells_cover_every_direction(self):
        from PIL import Image
        sheet = ROOT/'assets/existing_visions/payload'/field.SHEET
        data = sheet.read_bytes()
        self.assertEqual(hashlib.sha256(data).hexdigest(), field.SHEET_SHA256)
        self.assertEqual(hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest(),
                         'ec345dbeb6a3f68d53aa24a107b8b53e78abfb51')
        with Image.open(sheet) as image:
            self.assertEqual(image.size, (448, 1536))
            # This is an actual rest cell, rather than an additional step.
            for row in range(8):
                idle = image.crop((0, row*64, 64, (row+1)*64)).tobytes()
                for offset in (8, 16):
                    self.assertEqual(idle, image.crop((0, (row+offset)*64, 64, (row+offset+1)*64)).tobytes())
        spec = field.spec('pc0010'); cells = {c['name'] for c in spec['cells']}
        animations = {a['name']:a for a in spec['animations']}
        self.assertEqual(len(animations),len(spec['animations']))
        for direction, _ in field.DIRECTIONS:
            self.assertEqual(animations[f'fieldidle{direction}']['parts'], animations[f'idle{direction}']['parts'])
        self.assertEqual({d for d,_ in field.DIRECTIONS}, {1,2,3,4,6,7,8,9})
        self.assertEqual(animations['idle8']['parts']['part_0']['Cell'], [[0,'field_1_0']])
        self.assertEqual(animations['idle2']['parts']['part_0']['Cell'], [[0,'field_0_0']])
        # Visual review of the bundled sheet: row 3 faces east, row 5 southeast.
        for motion, offset in (('idle', 0), ('move', 16), ('dash', 8)):
            first = 0 if motion == 'idle' else 1
            self.assertEqual(animations[f'{motion}6']['parts']['part_0']['Cell'][0], [0, f'field_{3+offset}_{first}'])
            self.assertEqual(animations[f'{motion}3']['parts']['part_0']['Cell'][0], [0, f'field_{5+offset}_{first}'])
            self.assertEqual(animations[f'{motion}7']['parts']['part_0']['Cell'][0], [0, f'field_{6+offset}_{first}'])
            self.assertEqual(animations[f'{motion}9']['parts']['part_0']['Cell'][0], [0, f'field_{7+offset}_{first}'])
        for d,row in field.DIRECTIONS:
            for motion,offset,delay in (('idle',0,1),('move',16,8),('dash',8,5)):
                animation = animations[f'{motion}{d}']; keys = animation['parts']['part_0']['Cell']
                columns = (0,) if motion == 'idle' else range(1, 7)
                self.assertEqual(keys, [[i*delay, f'field_{row+offset}_{col}'] for i, col in enumerate(columns)])
                self.assertTrue(all(c in cells for _,c in keys))
                self.assertEqual(animation['frameCount'], len(columns)*delay)
                self.assertEqual(animation['parts']['part_0']['Posx'], [[0,0.0]])

    def test_generator_writes_private_field_assets_and_correct_texture_payload_sizes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); u = unit(); u['overworld'] = choice(); calls = []
            templates = root/'legacy/FFRS/Content/Chara/summon/summon13110'; templates.mkdir(parents=True)
            for suffix in ('','_tex','_normal','_mreo'):
                for extension in ('.uasset','.uexp'): (templates/('summon13110'+suffix+extension)).write_bytes(b'explicit fixture')
            env = {'ROOT':str(root),'LEGACY':str(root/'legacy'),'OUT':str(root/'out'),
                   'FFRDT':['tool'],'USMAP':'fixture.usmap','run':calls.append,
                   'ffrenv':SimpleNamespace(py=lambda *args:list(args))}
            field.generate(u,env)
            self.assertEqual(len(calls),4)
            self.assertTrue(all('StudioOverworld/party1001' in str(c) for c in calls))
            self.assertTrue(all('/StudioParty/' not in str(c) and '/Chara/Field_Unit/' not in str(c) for c in calls))
            work = root/'build/overworld/party_1001'
            self.assertEqual((work/'tex.bgra').stat().st_size,448*1536*4)
            self.assertEqual((work/'normal.bc5').stat().st_size,448*1536)
            self.assertEqual((work/'mreo.bgra').stat().st_size,448*1536*4)
            self.assertEqual(json.loads((work/'spec.json').read_text())['animePackName'],'pc0010')


if __name__ == '__main__': unittest.main()
