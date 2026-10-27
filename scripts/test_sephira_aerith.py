"""Original 5-star Aerith replacement: save compatibility, kit and clean audio."""
import copy
import json
from pathlib import Path
import unittest
import tempfile

from test_existing_visions import ROOT
import _ffr_sephira as sephira
import _ffr_sephira_lb_audio as audio
from sephira_aerith import revise, FORM, PACK_SHA256


def before():
    unit = json.loads((ROOT/'scripts/fixtures/elephim_before_aerith.json').read_bytes())
    unit['sephiraVision'] = {'version': 1, 'preset': 'elephim', 'enabled': True}
    return unit


class AerithTests(unittest.TestCase):
    def test_preset_retains_complete_regular_kit_and_permanent_save_identity(self):
        catalog = json.loads((ROOT/'assets/sephira_visions/catalog.json').read_bytes())
        preset = next(p for p in catalog['presets'] if p['id'] == 'elephim')
        unit = preset['profile']; old = before(); old.pop('sephiraVision')
        changed = {'en','desc','ffbe','lb','lb_custom','command','master','sephiraAppearanceRevision'}
        for key in old.keys()-changed: self.assertEqual(unit[key], old[key], key)
        self.assertEqual(unit['id'], 13523)
        self.assertEqual(unit['command']['id'], old['command']['id'])
        self.assertEqual(unit['master']['id'], old['master']['id'])
        self.assertEqual((preset['name'], preset['form']['label']), ('Aerith','5'))
        self.assertEqual(preset['form']['sha256'], PACK_SHA256)
        self.assertEqual(unit['ffbe']['id'], FORM)
        self.assertEqual((unit['lb'],unit['lb_custom']['from']), (412510,412510))
        self.assertEqual(unit['lb_custom']['set'], {})  # Retain the native heal/cleanse budget.
        self.assertEqual(unit['lb_custom']['ffbe_lb_id'], FORM)
        self.assertIn('Restore HP',unit['lb_custom']['desc'])
        self.assertNotIn('70%',unit['lb_custom']['desc'])
        snapshot = copy.deepcopy(catalog); revise(catalog)
        self.assertEqual(catalog, snapshot)

    def test_legacy_migration_preserves_edits_grants_acquisition_and_cross_references(self):
        unit = before(); unit['stats']['Mind'] = 777; unit['price'] = 1
        unit['studioAcquisition'] = {'version':1,'location':'mitra_shop','random':False,'hideSpoilers':False}
        next(iter(unit['skills'].values()))['set']['Cost'] = 17
        snapshot = copy.deepcopy(unit)
        result = sephira.repair_appearance(unit)
        self.assertEqual(unit, snapshot)
        changed = {'en','desc','ffbe','lb','lb_custom','command','master','sephiraAppearanceRevision'}
        for key in unit.keys()-changed: self.assertEqual(result[key],unit[key],key)
        self.assertEqual(result['master']['id'],unit['master']['id'])
        self.assertEqual(result['command']['id'],unit['command']['id'])
        self.assertEqual(result['en'],'Aerith')
        self.assertEqual(result['master']['en'],'Spirit of Aerith')
        self.assertEqual(result['lb_custom']['en'],'Great Gospel')
        with tempfile.TemporaryDirectory() as root:
            self.assertEqual(sephira.visual_units([unit],root),[result])
        self.assertIs(sephira.repair_appearance(result),result)
        result['ffbe']['id']='207000407';result['lb_custom']['audio']='none'
        self.assertIs(sephira.repair_appearance(result),result)

    def test_disabled_unrelated_and_deliberately_replaced_models_are_not_forced(self):
        unit = before(); unit['sephiraVision']['enabled'] = False
        self.assertEqual(sephira.active_units([unit]),[])
        for field,value in [('ffbe',{'id':'another-model'}),('native',{'id':13024}),
                            ('party',{'id':1001}),('sephiraVision',{'preset':'fran','enabled':True,'version':1})]:
            changed = copy.deepcopy(unit);changed[field] = value
            self.assertIs(sephira.repair_appearance(changed),changed)

    def test_great_gospel_uses_original_cues_and_supported_clean_recordings(self):
        metadata,files=audio.payload();profile=metadata['profiles']['elephim']
        self.assertEqual((profile['form'],profile['sourceName']),(FORM,'Great Gospel'))
        self.assertEqual([(s['frame'],s['cueId']) for s in profile['sounds']],[(0,794),(30,793)])
        bank=json.loads(files['audio/SE.json'])
        for cue in (793,794):
            records=[r for r in bank['recordings'] if r['sourceCueId']==cue]
            self.assertEqual(len(records),1)
            sample=files['audio/samples/'+bank['waves'][str(records[0]['sourceWaveId'])]['sha256']+'.hca']
            self.assertEqual(sample[:6],b'HCA\0\x02\0')
            self.assertEqual(sample[34],sample[35]);self.assertEqual(sample[40:46],b'ciph\0\0')
        unit=sephira.repair_appearance(before())
        self.assertIsNotNone(audio.selected(unit,unit['lb_custom']))


if __name__ == '__main__': unittest.main()
