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

    def test_all_regions_production_parent_and_cooked_composite_change_only_movement_flag(self):
        original=copy.deepcopy(self.tables);result=self.prepare()
        self.assertEqual(set(result),set(self.tables))
        for rel,plan in result.items():
            self.assertFalse(plan['add'])
            for change in plan['set']:
                self.assertTrue(original[rel][change['row']]['doMovementEncount'])
                self.assertEqual(change['set'],{'doMovementEncount':False})
            self.assertNotIn('town',{change['row'] for change in plan['set']})
        self.assertEqual(self.tables,original)

    def test_disabling_produces_no_encounter_edits_and_legacy_default_is_off(self):
        (self.root/testing.CONFIG).write_text(json.dumps({'schema':1,'maxMr':False}))
        self.assertFalse(testing.settings(self.root)['noEncounters'])
        self.assertEqual(self.prepare(),{})
        with self.assertRaises(ValueError):testing.validate_settings({'schema':1,'maxMr':False,'noEncounters':1})

    def test_missing_or_unrecognized_native_schema_fails_before_patching(self):
        self.tables['Map/MapData/DT_MapData_05Old']['dungeon'].pop('doMovementEncount')
        with self.assertRaisesRegex(ValueError,'movement-encounter flag'):self.prepare()
        (self.root/'extracted/utoc_filelist.tsv').write_text('unrelated.uasset')
        with self.assertRaisesRegex(ValueError,'No native map tables'):testing.encounter_tables(self.root)

    def test_paired_parents_are_prepared_even_if_only_shared_legacy_file_exists(self):
        rel='Map/MapData/DT_MapData_00Com';prod=rel+'_Prod'
        listing=self.root/'extracted/utoc_filelist.tsv';listing.write_text('\n'.join(native.PREFIX+r+'.uasset' for r in (rel,prod)))
        path=self.root/'extracted/legacy'/native.PREFIX/(rel+'.uasset');path.parent.mkdir(parents=True);path.write_bytes(b'fixture')
        calls=[]
        def extract(folder):
            calls.append(folder);target=self.root/'extracted/legacy/FFRS/Content'/(folder+'.uasset')
            target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(b'fixture')
        with mock.patch('_ffr_fina_cinematic.ensure_assets'):
            testing.ensure_assets(self.root,extract)
        self.assertEqual(calls,['Datatable/'+prod]);self.assertEqual(testing.encounter_tables(self.root),[rel])


if __name__=='__main__':unittest.main()
