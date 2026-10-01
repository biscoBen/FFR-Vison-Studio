"""Source labels must follow actual unit references, never name guesses."""
import copy
import json
from pathlib import Path
import tempfile
import unittest

from test_animation_and_library import library


class SourceLabelsTests(unittest.TestCase):
    def fixture(self, root):
        tables = {
            'Skill/DT_SkillData': {
                'needles': {'ID': 10, 'belongCommandList': [99], 'skillIdAfterModeChange': 20},
                'twin': {'ID': 20, 'skillIdAfterModeChange': 10},
                'level': {'ID': 30}, 'ai': {'ID': 40}, 'not_a_skill_reference': {'ID': 50},
                'default': {'ID': 60, 'belongCommandList': [88]},
                'unknown_source': {'ID': 70, 'belongCommandList': [77]},
            },
            'Skill/DT_PassiveSkillData': {'guard': {'ID': 100}},
            'Skill/DT_SkillEffectData': {},
            'Skill/DT_CommandSkillData': {
                'cactuar': {'ID': 99, 'unitIdToUseSkill': 900},
                'leah': {'ID': 88, 'unitIdToUseSkill': 13045},
                'missing_name': {'ID': 77, 'unitIdToUseSkill': 901},
            },
            'Unit/DT_UnitParameter': {
                'cactuar': {'ID': 900, 'Name': {'table': '/Game/Text/ST_UnitName.ST_UnitName', 'key': 'UnitName900'}, 'LevelParamId': 1, 'passiveSkillList': [100]},
                'leah': {'ID': 13045, 'Name': 'Leah'},
                'unknown': {'ID': 901, 'Name': '未翻訳'},
            },
            'Unit/LevelParameter/DT_UnitLevelParameterList': {'level': {'ID': 1, 'DataTable': '/Game/Datatable/Unit/LevelParameter/enemy/Cactuar.Cactuar'}},
            'Unit/LevelParameter/enemy/Cactuar': {'level1': {'AddSkills': [30]}},
            'Unit/AI/DT_BtlUnitAIParameter': {
                'cactuar': {'UnitId': 900, 'actions': [{'skillId': 40, 'accuracy': 50}], 'someOtherId': 50},
                'unknown': {'UnitId': 999, 'skillId': 50},
                'index_collision': {'ID': 900, 'skillId': 50},
            },
        }
        for rel, data in tables.items():
            path = root / 'extracted/rows' / (rel + '.json')
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps({'rows': data}))
        path = root / 'extracted/locres_en.json'
        path.write_text(json.dumps({'ST_UnitName': {'UnitName900': 'Cactuar'}}))
        cat = {'skills': [{'id': sid, 'name': f'Skill {sid}'} for sid in (10, 20, 30, 40, 50, 60, 70)],
               'passives': [{'id': 100, 'name': 'Guard'}], 'visions': [{'id': 13045, 'name': 'Leah'}]}
        return tables, cat

    def test_commands_levels_ai_passives_and_target_twins_confirm_sources_without_integer_collisions(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); tables, cat = self.fixture(root)
            before = copy.deepcopy([tables, cat])
            result = library.analyze(cat, root)
            self.assertEqual(result['sources']['skills'], {str(sid): ['Cactuar'] for sid in (10, 20, 30, 40)})
            self.assertEqual(result['sources']['passives'], {'100': ['Cactuar']})
            self.assertEqual(result['owners']['skills']['60'], ['Leah'])
            self.assertEqual([tables, cat], before)

    def test_optional_missing_sources_do_not_break_core_library_or_guess_from_names(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); tables, cat = self.fixture(root)
            (root / 'extracted/rows/Unit/DT_UnitParameter.json').unlink()
            cat['skills'][0]['name'] = 'Cactuar needles'
            self.assertEqual(library.analyze(cat, root)['sources'], {'skills': {}, 'passives': {}})

    def test_canonical_english_names_work_without_ftext_namespace_and_untranslated_names_stay_unlabelled(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); tables, cat = self.fixture(root)
            tables['Unit/DT_UnitParameter']['cactuar']['Name'] = {'table': 'Missing', 'key': 'Missing'}
            path = root / 'extracted/rows/Unit/DT_UnitParameter.json'
            path.write_text(json.dumps({'rows': tables['Unit/DT_UnitParameter']}))
            result = library.analyze(cat, root)
            self.assertEqual(result['sources']['skills']['10'], ['Cactuar'])
            self.assertNotIn('70', result['sources']['skills'])
