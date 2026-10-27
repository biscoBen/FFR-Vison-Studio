"""All managed kits retain mechanics while shipped technical text is shortened."""
import copy
import json
from pathlib import Path
import unittest

from sephira_descriptions import revise
from test_sephira_challenges import fixture

ROOT=Path(__file__).resolve().parents[1]


class DescriptionTests(unittest.TestCase):
    def test_all_ability_and_resonance_text_is_concise_with_native_style(self):
        catalog=json.loads((ROOT/'assets/sephira_visions/catalog.json').read_bytes())
        count=0
        for preset in catalog['presets']:
            unit=preset['profile'];lb=unit['lb_custom']['desc']
            self.assertTrue(lb)
            self.assertNotRegex(lb,r'Native|mechanics|sprite animation|FFBE|Sephira')
            for recipe in unit['skills'].values():
                text=recipe.get('desc','')
                self.assertNotRegex(text,r'; MP |accuracy|stagger |power [0-9]|\[TEMP\]|friendlies|Source:')
                self.assertLess(len(text),220)
                self.assertTrue(text)
            count+=len(preset['descriptionUpdate']['skills'])
        self.assertEqual(count,313)
        aria=next(p['profile'] for p in catalog['presets'] if p['id']=='aria')
        rejuvenate=next(r for r in aria['skills'].values() if r['en']=='Rejuvenate')
        self.assertEqual(rejuvenate['desc'],'Restore 20% of own max HP.')
        self.assertEqual(aria['lb_custom']['desc'],'Heal all allies and cast Regen on them. Heal effect can exceed max HP.')

    def test_native_text_rebuild_changes_only_descriptions(self):
        catalog=json.loads((ROOT/'assets/sephira_visions/catalog.json').read_bytes())
        baseline=copy.deepcopy(catalog)
        for preset in baseline['presets']:
            audit=preset.pop('descriptionUpdate')
            for edit in audit['skills']:
                recipe,=[r for r in preset['profile']['skills'].values()
                         if r['from']==edit['from'] and r['en']==edit['name']]
                recipe['desc']=edit['before']
            if 'resonance' in audit: preset['profile']['lb_custom']['desc']=audit['resonance']['before']
        rows=fixture();english=json.loads((ROOT/'scripts/fixtures/sephira_challenges/native-resonance-text.json').read_bytes())
        revise(baseline,lambda rel:{**rows[rel],**english['nativeRows']},english)
        self.assertEqual(baseline,catalog)
        self.assertEqual(revise(copy.deepcopy(baseline),lambda rel:{**rows[rel],**english['nativeRows']},english),catalog)


if __name__=='__main__':unittest.main()
