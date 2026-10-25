"""MR coverage must not silently include awakening grants or edited copies."""
import copy
import json
from pathlib import Path
import unittest
from audit_sephira_mr import audit,describe

ROOT=Path(__file__).resolve().parents[1]


class MrCoverageTests(unittest.TestCase):
    def test_tracked_report_matches_current_presets_and_original_mr_grants(self):
        catalog=json.loads((ROOT/'assets/sephira_visions/catalog.json').read_bytes())
        source=json.loads((ROOT/'assets/sephira_visions/native_coverage.json').read_bytes())
        actual=audit(catalog,source)
        self.assertEqual(actual,json.loads((ROOT/'docs/SEPHIRA_MR_COVERAGE.json').read_bytes()))
        self.assertEqual(describe(actual),(ROOT/'docs/SEPHIRA_MR_COVERAGE.md').read_text())
        self.assertEqual(actual['summary']['originalRewards'],75)
        self.assertEqual(len(actual['spiritWrappers']),15)

    def test_an_awakening_grant_or_private_copy_does_not_count_as_the_original_mr(self):
        source={'excludedVisions':[{'name':'Original','masterRewards':[100]}],'entries':[
            {'kind':'ActiveSkill','id':42,'name':'Original skill',
             'nativeGrants':[{'vision':'Original','track':'synchro','rank':5}]}]}
        unit={'awakening':[[['ActiveSkill',42,-1]]],'synchro':[[]],'skills':{}}
        catalog={'presets':[{'id':'new','name':'New','profile':unit}]}
        before=copy.deepcopy(catalog)
        self.assertEqual(audit(catalog,source)['rewards'][0]['status'],'awakening_only')
        self.assertEqual(catalog,before)
        unit['synchro'][0].append(['ActiveSkill',420,-1]);unit['skills']['420']={'from':42,'set':{'magnification':999}}
        self.assertEqual(audit(catalog,source)['rewards'][0]['status'],'mr_copy_needs_review')
        unit['synchro'][0].append(['ActiveSkill',42,-1])
        self.assertEqual(audit(catalog,source)['rewards'][0]['status'],'covered_mr')


if __name__=='__main__':unittest.main()
