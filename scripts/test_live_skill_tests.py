"""Live test evidence is scoped to exact demo skill records."""
import copy
import json
import unittest
from test_existing_visions import ROOT, module
library=module('live_library',ROOT/'assets/existing_visions/payload/_ffr_library.py')


class LiveSkillTests(unittest.TestCase):
    def test_only_the_five_successes_get_live_verification_and_cling_retains_failed_result(self):
        report=json.loads((ROOT/'assets/existing_visions/payload/ability_live_tests.json').read_bytes())
        original={'skills':[{'id':s['id'],**s['expected']} for s in report['skills']]};before=copy.deepcopy(original)
        result=library.live_tests(original)
        verified=[s['id'] for s in result['skills'] if s['studioLiveTest']['result']=='visible_animation']
        self.assertEqual(set(verified),{500120,500580,500440,500140,500510})
        self.assertEqual(result['skills'][-1]['studioLiveTest']['result'],'damage_only_no_animation')
        self.assertEqual(original,before)
        self.assertFalse(any(library.verified_skill(s) for s in result['skills']))

    def test_changed_or_repurposed_game_record_drops_stale_verification(self):
        report=json.loads((ROOT/'assets/existing_visions/payload/ability_live_tests.json').read_bytes());entry={'id':500120,**report['skills'][0]['expected']}
        for key,value in [('name','Different skill'),('seq',[]),('seqPath','/Game/Changed'),('hits',9)]:
            changed={**entry,key:value,'studioLiveTest':{'schema':1,'result':'visible_animation'}}
            result=library.live_tests({'skills':[changed]})['skills'][0]
            self.assertNotIn('studioLiveTest',result)


if __name__=='__main__':unittest.main()
