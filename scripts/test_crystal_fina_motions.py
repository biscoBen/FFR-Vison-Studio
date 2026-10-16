"""Checks for the native SsValue payload decoder and non-installing motion draft."""
import base64
import copy
import math
import struct
import unittest
from unittest.mock import patch

from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "assets/existing_visions/payload"))
import _ffr_fina_motion as motions


def p(name, value): return {'Name': name, 'Value': value}


def native_fixture():
    def key(kind):
        return {'Value': [p('Time', 0), p('IpType', 'None'), p('Value', [p('Type', kind)])]}
    clip = {'Value': [p('AnimationName', 'openarmidle2'), p('Settings', [p('Fps', 60), p('FrameCount', 49)]),
        p('PartAnimes', [{'Value': [p('PartName', 'part_0'), p('Attributes', [
            {'Value': [p('Tag', 'Posx'), p('Key', [key('FloatType')])]},
            {'Value': [p('Tag', 'Cell'), p('Key', [key('HashType')])]}])]}])]}
    # The actual native format: scalar, two-entry map, typed mapId/name values.
    payload = bytes.fromhex('0000e84102000000000000000000000080090e0300000000010000000000000080090e01080000006e70635f305f3000')
    return {'NameMap': ['mapId', 'name'], 'Exports': [{'Data': [p('AnimeList', [{'Value': [p('AnimeList', [clip])]}])],
            'Extras': base64.b64encode(payload).decode()}]}


class FinaMotionTests(unittest.TestCase):
    def test_native_custom_values_are_read_from_the_payload_without_mutating_the_source(self):
        source = native_fixture(); before = copy.deepcopy(source)
        result = motions.decode(source)['openarmidle2']
        self.assertEqual(result['frameCount'], 49)
        self.assertEqual(result['parts']['part_0']['Posx'], [[0, 29.0]])
        self.assertEqual(result['parts']['part_0']['Cell'], [[0, {'mapId': 0, 'name': 'npc_0_0'}]])
        self.assertEqual(source, before)

    def test_truncated_extra_and_unknown_cell_headers_fail_instead_of_guessing(self):
        for edit in ('truncated', 'extra', 'unknown', 'name_index', 'nonfinite'):
            source = native_fixture(); raw = bytearray(base64.b64decode(source['Exports'][0]['Extras']))
            if edit == 'truncated': raw.pop()
            if edit == 'extra': raw.append(0)
            if edit == 'unknown': raw[16] = 0
            if edit == 'name_index': struct.pack_into('<i', raw, 8, 99)
            if edit == 'nonfinite': struct.pack_into('<f', raw, 0, math.nan)
            source['Exports'][0]['Extras'] = base64.b64encode(raw).decode()
            with self.subTest(edit=edit), self.assertRaises(ValueError): motions.decode(source)

    def test_attack_has_no_ground_pose_and_resonance_finishes_in_authorized_original_pose(self):
        clips = {}
        names = [('openarmidle2', 49), ('openarmopeneye2', 65), ('curlup2', 73), ('magicattack6', 91), ('down6', 49)]
        for name, count in names:
            clips[name] = {'fps': 60, 'frameCount': count,
                'parts': {'part_0': {'Cell': [[0, {'mapId': 0, 'name': name}]]}}}
        with patch.object(motions, 'decode', return_value=clips): result = motions.draft({})
        self.assertEqual([key[1] for key in result['attack']['parts']['part_0']['Cell']],
                         ['openarmopeneye2', 'curlup2', 'magicattack6'])
        self.assertEqual(result['attack']['frameCount'], 229)
        seat = result['resonance']['parts']['part_0']['Cell'][-1]
        self.assertEqual(seat, [183, 'original_jacket_free_seated'])
        self.assertEqual(result['resonance']['parts']['part_0']['Posy'][-1], [183, 0.0])
        self.assertEqual(result['presentationEvents'][1], {'frame': 134, 'event': 'hide_casing_and_fall'})
        self.assertIn('not implemented', result['status'])


if __name__ == '__main__': unittest.main()
