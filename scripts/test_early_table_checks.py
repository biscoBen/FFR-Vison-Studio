"""Saved shop modes and failure ordering before expensive sprite generation."""
import ast
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

from test_existing_visions import ROOT, installer, fina_installer
sys.path.insert(0, str(ROOT/'assets/existing_visions/payload'))
from test_sephira_reward_sources import inputs, settings
import _ffr_crystal_cave as caves
import _ffr_sephira as pack
import _ffr_shrine_challenges as challenges
import _ffr_testing as testing


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding='utf-8')


def apply(original, operation):
    result = copy.deepcopy(original)
    for edit in operation['add']:
        result[edit['row']] = testing.apply_fields(result[edit['cloneFrom']], edit['set'])
    for edit in operation['set']:
        result[edit['row']] = testing.apply_fields(result[edit['row']], edit['set'])
    return result


class EarlyTableChecks(unittest.TestCase):
    def test_early_check_defers_only_later_presentation_edits(self):
        import _ffr_fina_boss as fina
        rel = 'Battle/Unit/DT_BtlUnitDesignParameter'
        operation = {'asset': 'FFRS/Content/Datatable/'+rel, 'add': [{
            'row': 'private', 'cloneFrom': 'native', 'set': {'ID': 2}}], 'set': []}
        independent = dict(operation, add=[])
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            save(root/'build/visions_mod/patch.json', {'tables': [operation]})
            original = {'native': {'ID': 1, 'Scale': 1.0}}
            save(root/'extracted/rows'/(rel+'.json'), {'rows': original})
            save(root/'mods/EstherTsukiko/units.json', [])
            built = apply(original, operation)
            def finalize(name, rows, units, folder):
                rows['private']['Scale'] = 2.0
                return rows
            with mock.patch.object(testing, 'verification_operations', return_value={rel: independent}), \
                    mock.patch.object(fina, 'final_rows', side_effect=finalize) as finishing, \
                    mock.patch.object(testing.subprocess, 'run', side_effect=lambda command, **k: save(Path(command[3]), {'rows': built})):
                testing.verify_table_recipe(root, ['tool'], 'mapping')
                finishing.assert_not_called()
                with self.assertRaisesRegex(ValueError, rel+':'):
                    testing.verify(root, ['tool'], 'mapping')
                built['private']['Scale'] = 2.0
                testing.verify(root, ['tool'], 'mapping')

    def test_shop_verifier_covers_override_normal_folka_and_unrelated_stock(self):
        _, native, units = inputs()
        units[0]['sephiraVision']['enabled'] = False
        saved = copy.deepcopy(units)
        rel = 'Shop/DT_ShopList'
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            save(root/'mods/EstherTsukiko/units.json', units)
            for name, rows in native.items(): save(root/'extracted/rows'/(name+'.json'), {'rows': rows})
            for shop in (False, True):
                for borrowed in (False, True):
                    with self.subTest(shop=shop, borrowed=borrowed):
                        settings(root, shop=shop, borrowed=borrowed)
                        chosen = pack.visual_units(pack.active_units(units), root, native.__getitem__)
                        operations = caves.prepare_shops({}, chosen, native.__getitem__)
                        challenges.prepare_shop(lambda r: operations.setdefault(r, {
                            'asset': 'FFRS/Content/Datatable/'+r, 'add': [], 'set': []}), native.__getitem__, chosen)
                        built = apply(native[rel], operations[rel])
                        def readback(command, **kwargs): save(Path(command[3]), {'rows': built})
                        with mock.patch.object(caves.subprocess, 'run', side_effect=readback):
                            caves.verify_shops(root, ['tool'], 'mapping')
                            first = next(iter(built))
                            built[first]['ItemList'][0]['PriceRatio'] += 1
                            with self.assertRaisesRegex(ValueError, 'Shop/DT_ShopList.*changed:'):
                                caves.verify_shops(root, ['tool'], 'mapping')
            self.assertEqual(json.loads((root/'mods/EstherTsukiko/units.json').read_bytes()), saved)

    def test_disabled_override_cannot_leave_extra_shop_entries_behind(self):
        _, native, units = inputs()
        rel = 'Shop/DT_ShopList'
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); settings(root, shop=False)
            save(root/'mods/EstherTsukiko/units.json', [])
            save(root/'extracted/rows'/(rel+'.json'), {'rows': native[rel]})
            asset = root/'build/visions_mod/assets/FFRS/Content/Datatable'/(rel+'.uasset')
            asset.parent.mkdir(parents=True); asset.touch()
            extra = caves.prepare_shops({}, [dict(units[0], studioAcquisition={
                'version': 1, 'location': 'mitra_shop', 'random': False, 'hideSpoilers': True})], native.__getitem__)[rel]
            built = apply(native[rel], extra)
            with mock.patch.object(caves.subprocess, 'run', side_effect=lambda command, **k: save(Path(command[3]), {'rows': built})):
                with self.assertRaisesRegex(ValueError, 'Shop/DT_ShopList.*changed:'):
                    caves.verify_shops(root, ['tool'], 'mapping')

    def test_early_readback_stops_before_effects_sprites_and_pack(self):
        source = (ROOT/'scripts/fixtures/crystal_fina/make_vision_mod.py').read_bytes()
        tree = ast.parse(installer.hook_builder(fina_installer.hook_builder(source)))
        main = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'main')
        check = next(i for i, n in enumerate(main.body) if '_ffr_testing.verify_table_recipe(' in ast.unparse(n))
        sequence = next(i for i, n in enumerate(main.body) if isinstance(n, ast.For) and ast.unparse(n.iter) == 'authored_sequences')
        sprites = next(i for i, n in enumerate(main.body) if isinstance(n, ast.Assign) and ast.unparse(n.targets[0]) == 'todo')
        self.assertLess(check, sequence); self.assertLess(sequence, sprites)
        voice_check = next(i for i, n in enumerate(main.body)
                           if '_ffr_party.verify_voice_parameters(' in ast.unparse(n))
        self.assertLess(check, voice_check); self.assertLess(voice_check, sequence)
        continuation = mock.Mock()
        block = ast.Module(body=main.body[check-1:check+1] + ast.parse('continuation()').body, type_ignores=[])
        rel = 'Skill/DT_SkillData'; asset = 'FFRS/Content/Datatable/'+rel
        original = {'donor': {'ID': 1, 'value': 0, 'unrelated': ['kept']}}
        operation = {'asset': asset, 'add': [
            {'row': 'copy', 'cloneFrom': 'donor', 'set': {'ID': 2, 'value': 7}},
            {'row': 'next', 'cloneFrom': 'copy', 'set': {'ID': 3}}], 'set': []}
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            save(root/'build/visions_mod/patch.json', {'tables': [operation]})
            save(root/'mods/EstherTsukiko/units.json', [])
            save(root/'extracted/rows'/(rel+'.json'), {'rows': original})
            built = apply(original, operation); built['donor']['value'] = '-0'
            environment = {'_ffr_testing': testing, 'ROOT': root, 'FFRDT': ['tool'], 'USMAP': 'mapping',
                           'stage': mock.Mock(), 'continuation': continuation}
            with mock.patch.object(testing, 'verification_operations', return_value={rel: dict(operation, add=[])}), \
                    mock.patch.object(testing.subprocess, 'run', side_effect=lambda command, **k: save(Path(command[3]), {'rows': built})):
                exec(compile(block, 'installed-builder', 'exec'), environment)
                continuation.assert_called_once()
                continuation.reset_mock()
                for corrupt in ('unrelated', 'missing', 'extra'):
                    with self.subTest(corrupt=corrupt):
                        failed = copy.deepcopy(built)
                        if corrupt == 'unrelated': failed['donor']['unrelated'] = []
                        elif corrupt == 'missing': failed.pop('copy')
                        else: failed['surprise'] = {'ID': 999}
                        with mock.patch.object(testing.subprocess, 'run', side_effect=lambda command, **k: save(Path(command[3]), {'rows': failed})):
                            with self.assertRaisesRegex(ValueError, 'Skill/DT_SkillData:'):
                                exec(compile(block, 'installed-builder', 'exec'), environment)
                        continuation.assert_not_called()


if __name__ == '__main__': unittest.main()
