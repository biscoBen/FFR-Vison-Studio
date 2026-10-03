"""Directional field sprites and independent party appearance contracts."""
import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from types import SimpleNamespace

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
    return rows


class OverworldTests(unittest.TestCase):
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
            self.assertEqual(field_op['row'], jp); self.assertEqual(len(field_op['set']), 4)
            built = copy.deepcopy(originals)
            for key, value in field_op['set'].items(): built[jp]['animationAssetList'][0][key.split('.')[-1]] = value
            field.check_rows(originals, built, [u])
            self.assertEqual(built[jp]['animationAssetList'][1:], originals[jp]['animationAssetList'][1:])
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
        with Image.open(sheet) as image: self.assertEqual(image.size, (448, 1536))
        spec = field.spec('pc0010'); cells = {c['name'] for c in spec['cells']}
        animations = {a['name']:a for a in spec['animations']}
        self.assertEqual(len(animations),len(spec['animations']))
        self.assertEqual({d for d,_ in field.DIRECTIONS}, {1,2,3,4,6,7,8,9})
        self.assertEqual(animations['idle8']['parts']['part_0']['Cell'], [[0,'field_1_0']])
        self.assertEqual(animations['idle2']['parts']['part_0']['Cell'], [[0,'field_0_0']])
        for d,row in field.DIRECTIONS:
            for motion,offset,delay in (('idle',0,1),('move',16,8),('dash',8,5)):
                animation = animations[f'{motion}{d}']; keys = animation['parts']['part_0']['Cell']
                self.assertEqual(keys[0], [0,f'field_{row+offset}_0'])
                self.assertTrue(all(c in cells for _,c in keys))
                self.assertEqual(animation['frameCount'], (1 if motion=='idle' else 7)*delay)
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
