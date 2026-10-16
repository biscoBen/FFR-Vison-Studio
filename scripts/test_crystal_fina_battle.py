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


class FinaBattleTests(unittest.TestCase):
    def test_glow_pulses_use_native_lifecycle_and_leave_gameplay_events_untouched(self):
        unit = dict(UNIT, lb_custom={'resonance': True})
        lb_id = lambda _: 444040
        asset = 'FFRS/Content/Sequencer/Battle/Skill/444040/444041/SEQ_Battle_444041_Master'
        events = [{'time': 12000, 'set': {'EventType': 'UnitPlayAnimByName', 'Unit_PlayAnimByName_AnimationName': 'LB1'}},
                  {'time': 65600, 'set': {'EventType': 'OtherReaction', 'Other_Reaction_Id': 444040}}]
        job = {'asset': asset, 'plan': {'duration': 220000, 'events': events}}
        before = copy.deepcopy(job); built = battle.prepare_job(job, [unit], lb_id)
        self.assertEqual(job, before)
        self.assertTrue(all(e in built['plan']['events'] for e in events))
        spawns = [e for e in built['plan']['events'] if e['set']['EventType'] == 'EffectSpawnNiagaraAtRandom']
        self.assertEqual([e['time'] for e in spawns], [12000 + 122 * 400, 12000 + 296 * 400])
        self.assertTrue(all(e['set']['Effect_NiagaraData']['PartName'] == 'NULL_Aura' for e in spawns))
        self.assertTrue(all(e['set']['Effect_NiagaraData']['bPlayVisionUnit'] for e in spawns))
        self.assertEqual(sum(e['set']['EventType'] == 'EffectDestroyNiagaraToNiagaraID' for e in built['plan']['events']), 2)
        self.assertEqual(sum(e['set']['EventType'] == 'EffectDiactivateNiagaraToNiagaraID' for e in built['plan']['events']), 2)
        self.assertIs(battle.prepare_job(dict(job, asset='AnotherSkill'), [unit], lb_id)['plan'], job['plan'])
        self.assertIs(battle.prepare_job(job, [], lb_id), job)

    def test_native_glow_readback_allows_omitted_false_but_rejects_missing_attachment(self):
        expected = {'NiagaraID': 'Glow', 'PartName': 'NULL_Aura', 'bDisableFollowing': False,
                    'bPlayOwnerUnit': False, 'bPlayVisionUnit': True}
        edits = [{'export': '9', 'set': {'EventType': 'EffectSpawnNiagaraAtRandom', 'Effect_NiagaraData': expected}}]
        actual = {'9': {'Effect_NiagaraData': {k: v for k, v in expected.items() if v is not False}}}
        battle.verify_glow_events(edits, actual)
        actual['9']['Effect_NiagaraData'].pop('PartName')
        with self.assertRaisesRegex(ValueError, 'PartName'): battle.verify_glow_events(edits, actual)

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

    def test_effect_table_has_only_casing_and_no_idle_aura_without_changing_native_effects(self):
        bundle = {'Name': '0', 'Value': [soft('niagaraAsset', '/Game/OriginalEffect'), p('attachPartsName', 'root'),
            p('offsetLocation', []), p('additionalRotation', [p('additionalRotation', {'Pitch': 0, 'Yaw': 180, 'Roll': 0})])]}
        source = table([{'Name': 'Donor', 'Value': [p('ID', 400), p('effectBundleList', [bundle])]}])
        before = copy.deepcopy(source); result = battle.effect_table(source, UNIT)
        self.assertEqual(source, before); self.assertEqual(battle.table_rows(result)[0], battle.table_rows(source)[0])
        effects = battle.cave.property_data(battle.table_rows(result)[1], 'effectBundleList')['Value']
        self.assertEqual([battle.cave.property_data(e, 'attachPartsName')['Value'] for e in effects], ['NULL_Crystal'])
        with self.assertRaises(ValueError): battle.effect_table(result, UNIT)

    def test_motion_spec_completes_cast_and_restores_crystal_after_half_the_seated_hold(self):
        from PIL import Image
        names = [('openarmidle2', 49), ('openarmopeneye2', 65), ('curlup2', 73), ('magicattack6', 91), ('down6', 49)]
        clips = {name: {'fps': 60, 'frameCount': count, 'parts': {'part_0': {'Cell': [[0, {'mapId': 0, 'name': name}]]}}}
                 for name, count in names}
        def vec(name, x, y): return p(name, [p(name, {'X': x, 'Y': y})])
        cells = [{'Value': [p('CellName', name), vec('Pos', i * 10, 0), vec('Size', 8, 8), vec('Pivot', 0, 0)]}
                 for i, (name, _) in enumerate(names)]
        view = {'Exports': [{'Data': [p('AnimeList', []), p('CellmapList', [{'Value': [p('Cells', cells)]}])]}]}
        original = {'animations': [{'name': name, 'frameCount': count} for name, count in [('idle', 49), ('attack_A', 117), ('magic_attack', 80), ('LB1', 400), ('Setup', 1)]]}
        before = copy.deepcopy(original)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'seat.png'; sheet = Image.new('RGBA', (1800, 1820)); sheet.paste((255, 0, 0, 255), (1122, 1497, 1158, 1534)); sheet.save(path)
            with patch.object(motion, 'decode', return_value=clips), patch.object(motion, 'extract_atlas', return_value=Image.new('RGBA', (256, 512))):
                atlas, spec = motion.battle_spec(view, {}, path, original)
        self.assertEqual(original, before); self.assertEqual(atlas.getpixel((0, 330)), (255, 0, 0, 255))
        clips = {a['name']: a for a in spec['animations']}
        self.assertEqual(clips['attack_A']['frameCount'], 60); self.assertEqual(clips['magic_attack']['frameCount'], 60)
        self.assertEqual(clips['idle']['frameCount'], 6000)
        self.assertAlmostEqual(clips['idle']['parts']['NULL_Crystal']['Roty'][-1][1], 359.94)
        self.assertEqual(clips['LB1']['parts']['NULL_Crystal']['Posy'][1:], [[134, -10000.0], [308, 183.5 / 2.7]])
        self.assertIn([183, 'original_jacket_free_seated'], clips['LB1']['parts']['part_0']['Cell'])
        self.assertEqual(clips['LB1']['parts']['part_0']['Cell'][-1][1], 'openarmidle2')
        self.assertIn([183, 0.0], clips['LB1']['parts']['part_0']['Posy'])
        self.assertEqual(clips['LB1']['parts']['part_0']['Posy'][-1], [308, 22.0 + motion.BODY_FLOAT])
        self.assertIn([183, 14.5], clips['LB1']['parts']['NULL_Aura']['Posy'])
        model = spec['model']['parts']
        self.assertEqual({p['name'] for p in model}, set(clips['idle']['parts']))
        self.assertTrue(all(p['parent'] == ( -1 if p['name'] == 'root' else 0) for p in model))


if __name__ == '__main__': unittest.main()
