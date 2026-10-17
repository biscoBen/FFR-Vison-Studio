"""Shared-table verification must retain imported visions and enforce testing edits."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from test_native_testing import testing


def mixed_build():
    original = {
        'Rain': {'ID':1001,'Name':'Rain','Category':'Playable','Attack':20,'passiveSkillList':[7]},
        'Lasswell': {'ID':1002,'Name':'Lasswell','Category':'Playable','Attack':25,'passiveSkillList':[8]},
        'Tina': {'ID':13103,'Name':'Tina','Category':'Vision','Attack':30,'passiveSkillList':[16],
                 'ElementResistanceList':{'Fire':'None','Ice':'None'}},
        'Native vision': {'ID':13027,'Name':'Native vision','Category':'Vision','Attack':40,'passiveSkillList':[17]},
    }
    testing_ops = {'asset':'FFRS/Content/Datatable/Unit/DT_UnitParameter','add':[], 'set':[
        {'row':'Rain','set':{'passiveSkillList':[7,29660]}},
        {'row':'Lasswell','set':{'passiveSkillList':[8,29660]}}]}
    plan = copy.deepcopy(testing_ops)
    plan['set'].insert(0, {'row':'Native vision','set':{'Attack':47}})
    built = copy.deepcopy(original)
    built['Rain']['passiveSkillList'] = [7,29660]
    built['Lasswell']['passiveSkillList'] = [8,29660]
    built['Native vision']['Attack'] = 47
    for name, identity in (('Crystal Fina 2',13503),('Agrias',13504),('21O',13505)):
        changes = {'ID':identity,'Name':name,'Attack':35,'ElementResistanceList':{}}
        if identity == 13503: changes['ElementResistanceList'] = {'Ice':'Halved'}
        plan['add'].append({'row':name,'cloneFrom':'Tina','set':changes})
        built[name] = dict(copy.deepcopy(original['Tina']), ID=identity, Name=name, Attack=35)
        if identity == 13503: built[name]['ElementResistanceList']['Ice'] = 'Halved'
    return original, built, testing_ops, plan


class TestingVerificationTests(unittest.TestCase):
    def test_imports_and_native_edits_pass_with_survival_without_ignoring_new_rows(self):
        original, built, operation, plan = mixed_build()
        # This reproduces the old verifier's refusal of the user's added units.
        with self.assertRaisesRegex(ValueError, 'extra: 21O, Agrias, Crystal Fina 2'):
            testing.check_rows(original, built, operation)
        testing.check_rows(original, built, operation, plan)
        self.assertEqual(len(built), len(original)+3)
        self.assertEqual(built['Crystal Fina 2']['ElementResistanceList'], {'Fire':'None','Ice':'Halved'})
        self.assertEqual(built['Agrias']['ElementResistanceList'], {'Fire':'None','Ice':'None'})

    def test_bad_testing_data_fails_even_when_the_build_recipe_contains_the_same_error(self):
        original, built, operation, plan = mixed_build()
        built['Rain']['passiveSkillList'] = [7]
        plan['set'][1]['set']['passiveSkillList'] = [7]
        with self.assertRaisesRegex(ValueError, 'changed: Rain'):
            testing.check_rows(original, built, operation, plan)

    def test_missing_extra_and_changed_import_or_original_rows_still_fail(self):
        original, correct, operation, plan = mixed_build()
        for problem in ('missing-original','missing-import','extra','changed-original','changed-import'):
            built = copy.deepcopy(correct)
            if problem == 'missing-original': del built['Tina']
            elif problem == 'missing-import': del built['Agrias']
            elif problem == 'extra': built['Unplanned vision'] = copy.deepcopy(built['Agrias'])
            elif problem == 'changed-original': built['Tina']['Attack'] = 999
            else: built['Agrias']['Attack'] = 999
            with self.subTest(problem=problem), self.assertRaises(ValueError):
                testing.check_rows(original, built, operation, plan)

    def test_partial_map_struct_array_and_indexed_edits_match_native_writer_semantics(self):
        original = {'stats':{'Attack':10,'Defence':20}, 'elements':{'Fire':'None','Ice':'None'},
            'bundles':[{'id':1,'target':'Self','params':[1,2]}, {'id':2,'target':'Enemy','params':[3,4]}]}
        built = testing.apply_fields(original, {'stats':{'Attack':15},'elements':{},
            'bundles':[{'id':8}, {'id':9,'params':[5,6]}], 'bundles[1].params[0]':7})
        self.assertEqual(built, {'stats':{'Attack':15,'Defence':20},'elements':{'Fire':'None','Ice':'None'},
            'bundles':[{'id':8,'target':'Self','params':[1,2]}, {'id':9,'target':'Self','params':[7,6]}]})
        self.assertEqual(original['stats']['Attack'],10)

    def test_verify_reads_the_complete_recipe_and_keeps_the_recomputed_testing_operations(self):
        original, built, operation, plan = mixed_build()
        rel = 'Unit/DT_UnitParameter'
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            roster = root/'mods/EstherTsukiko/units.json'; roster.parent.mkdir(parents=True)
            roster.write_text(json.dumps([{'id':13503},{'id':13504},{'id':13505}]))
            source = root/'extracted/rows'/(rel+'.json'); source.parent.mkdir(parents=True)
            source.write_text(json.dumps({'rows':original}))
            recipe = root/'build/visions_mod/patch.json'; recipe.parent.mkdir(parents=True)
            recipe.write_text(json.dumps({'tables':[plan]}))
            def convert(args, **kwargs):
                Path(args[3]).write_text(json.dumps({'rows':built}))
            with mock.patch.object(testing, 'verification_operations', return_value={rel:operation}), \
                    mock.patch.object(testing.subprocess,'run',side_effect=convert) as writer:
                testing.verify(root,['native-reader'],'mapping.usmap')
                self.assertEqual(writer.call_count,1)
                built['Rain']['passiveSkillList'] = [7]
                with self.assertRaisesRegex(ValueError, 'Unit/DT_UnitParameter:.*changed: Rain'):
                    testing.verify(root,['native-reader'],'mapping.usmap')

    def test_missing_or_duplicate_recipe_entries_fail_and_disabled_testing_needs_no_recipe(self):
        _, _, operation, plan = mixed_build()
        rel = 'Unit/DT_UnitParameter'
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            roster = root/'mods/EstherTsukiko/units.json'; roster.parent.mkdir(parents=True)
            roster.write_text('[]')
            with mock.patch.object(testing,'verification_operations',return_value={rel:operation}), \
                    mock.patch.object(testing.subprocess,'run') as writer:
                with self.assertRaisesRegex(ValueError,'complete build recipe is unavailable'):
                    testing.verify(root,['native-reader'],'mapping.usmap')
                recipe = root/'build/visions_mod/patch.json'; recipe.parent.mkdir(parents=True)
                for tables in ([], [plan,plan]):
                    recipe.write_text(json.dumps({'tables':tables}))
                    with self.assertRaisesRegex(ValueError,'one testing table: Unit/DT_UnitParameter'):
                        testing.verify(root,['native-reader'],'mapping.usmap')
                writer.assert_not_called()
            recipe.unlink()
            with mock.patch.object(testing,'verification_operations',return_value={}):
                testing.verify(root,['native-reader'],'mapping.usmap')


if __name__ == '__main__': unittest.main()
