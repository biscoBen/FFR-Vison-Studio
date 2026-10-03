"""Mode persistence, production hooks, raw builds and future native timelines."""
import ast
import copy
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock
from test_existing_visions import ROOT, installer
from test_animation_and_library import motion, library
import _ffr_ability_modes as modes


class AbilityModeTests(unittest.TestCase):
    def write(self, root, show, changes):
        path = Path(root) / modes.CONFIG
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({'schema': 1, 'showUnverified': show, 'useChanges': changes}))

    def test_defaults_and_both_flags_are_required_with_strict_validation(self):
        with tempfile.TemporaryDirectory() as root:
            self.assertEqual(modes.settings(root), {'schema': 1, 'showUnverified': False, 'useChanges': False})
            for show in (False, True):
                for changes in (False, True):
                    self.write(root, show, changes)
                    self.assertEqual(modes.enabled(root), show and changes)
            for invalid in ({}, {'schema': True, 'showUnverified': True, 'useChanges': False},
                            {'schema': 1, 'showUnverified': 1, 'useChanges': False}):
                with self.assertRaises(ValueError): modes.validate(invalid)

    def test_original_modes_do_not_read_animation_assets_or_mutate_jobs_and_clear_stale_trials(self):
        unit = {'id': 13500, 'awakening': [[['ActiveSkill', 400260], ['ActiveSkill', 400300]]]}
        for show, changes in ((False, False), (False, True), (True, False)):
            with self.subTest(show=show, changes=changes), tempfile.TemporaryDirectory() as root, mock.patch.dict(
                    sys.modules, {'_ffr_animation_repair': motion}):
                self.write(root, show, changes)
                trial = Path(root) / 'build/barrage-trial.json'; trial.parent.mkdir()
                trial.write_text('{"owners":{"13500":{"old":true}}}')
                report = trial.with_name('animation-repair-report.json'); report.write_text('{"skills":[{"status":"effect_reuse"}]}')
                tables = {'existing': {'unchanged': True}}; clones = [{'custom': True}]; jobs = [{'kind': 'user_LB'}]
                before = copy.deepcopy((tables, clones, jobs, unit))
                rows = mock.Mock(side_effect=AssertionError('Original modes must not prepare donor effects'))
                extract = mock.Mock(side_effect=AssertionError('Original modes must not extract timelines'))
                self.assertEqual(modes.prepare_barrage_trial([unit], root, rows)['owners'], {})
                self.assertEqual(modes.prepare_sequences(tables, clones, jobs, [unit], root, rows, extract), [])
                self.assertEqual((tables, clones, jobs, unit), before)
                self.assertEqual(json.loads(report.read_text())['mode'], 'original_game')

    def test_enhanced_mode_reuses_native_timelines_added_by_a_later_game(self):
        unit = {'id': 13500, 'awakening': [[['ActiveSkill', 250020]]]}
        game = {'Skill/DT_SkillData': {'future skill': {'ID': 250020}},
                'Asset/Skill/DT_SkillAsset': {'future binding': {'ID': 250021}},
                'Asset/Skill/CDT_SkillAsset_Demo': {'future binding': {'ID': 250021}}}
        with tempfile.TemporaryDirectory() as root, mock.patch.dict(sys.modules, {'_ffr_animation_repair': motion}):
            self.write(root, True, True)
            rows = lambda rel: copy.deepcopy(game[rel])
            tables = {}; clones = []; jobs = []
            self.assertEqual(modes.prepare_sequences(tables, clones, jobs, [unit], root, rows,
                             mock.Mock(side_effect=AssertionError('Existing timelines must win'))), [])
            self.assertEqual((tables, clones, jobs), ({}, [], []))
            report = json.loads((Path(root) / 'build/animation-repair-report.json').read_text())
            self.assertEqual(report['skills'][0]['status'], 'existing_sequence')

    def test_review_is_complete_and_cannot_hide_a_repurposed_skill_or_true_summon(self):
        review = json.loads((ROOT / 'assets/existing_visions/payload/ability_hiding_review.json').read_text())
        ids = [r['id'] for r in review['skills']]
        self.assertEqual(len(ids), 304); self.assertEqual(len(set(ids)), 304)
        self.assertFalse(set(ids) & set(range(430980, 431061, 10)))
        self.assertNotIn(431120, ids)
        first = review['skills'][0]
        with tempfile.TemporaryDirectory() as root:
            self.assertEqual(modes.catalog_controls({'skills': [{'id': first['id'], 'name': 'Different future skill'}]}, root)['reviewedHiddenSkills'], [])
            self.assertEqual(modes.catalog_controls({'skills': [first]}, root)['reviewedHiddenSkills'], [first['id']])

    def test_api_restart_persists_mode_and_build_guard_preserves_existing_files(self):
        routes = {}
        class App:
            def get(self, route):
                def decorator(func): routes[('GET', route)] = func; return func
                return decorator
            def put(self, route):
                def decorator(func): routes[('PUT', route)] = func; return func
                return decorator
        class HTTPException(Exception):
            def __init__(self, status, detail): super().__init__(detail)
        with tempfile.TemporaryDirectory() as root, mock.patch.dict(sys.modules, {'fastapi': SimpleNamespace(HTTPException=HTTPException)}):
            roster = Path(root) / 'mods/EstherTsukiko/units.json'; roster.parent.mkdir(parents=True); roster.write_text('[{"keep":true}]')
            testing = roster.with_name('testing.json'); testing.write_text('{"schema":1,"maxMr":true}')
            state = {'running': False}; modes.register(App(), {'ROOT': root, 'state': state})
            put = routes[('PUT', '/api/abilities/settings')]
            settings = {'schema': 1, 'showUnverified': True, 'useChanges': False}
            self.assertEqual(put(settings), settings)
            modes.register(App(), {'ROOT': root, 'state': state})
            self.assertEqual(routes[('GET', '/api/abilities/settings')](), settings)
            state['running'] = True
            with self.assertRaisesRegex(HTTPException, 'build to finish'):
                routes[('PUT', '/api/abilities/settings')]({**settings, 'useChanges': True})
            self.assertEqual(modes.settings(root), settings)
            self.assertEqual(roster.read_text(), '[{"keep":true}]')
            self.assertEqual(testing.read_text(), '{"schema":1,"maxMr":true}')

    def test_installed_builder_uses_gated_modes_and_catalog_settings_are_not_cached(self):
        source = (ROOT / 'scripts/fixtures/crystal_fina/make_vision_mod.py').read_bytes()
        from test_existing_visions import fina_installer
        patched = installer.hook_builder(fina_installer.hook_builder(source))
        calls = {ast.unparse(n.func) for n in ast.walk(ast.parse(patched)) if isinstance(n, ast.Call)}
        self.assertIn('_ffr_ability_modes.prepare_sequences', calls)
        self.assertIn('_ffr_ability_modes.prepare_barrage_trial', calls)
        with tempfile.TemporaryDirectory() as root, mock.patch.dict(sys.modules, {'_ffr_animation_repair': motion}):
            cat = {'skills': [], 'passives': [], 'visions': []}
            fake = SimpleNamespace(load=lambda: cat)
            with mock.patch.object(library, 'analyze', return_value={'schema': 1, 'available': False}):
                library.install(fake, root)
                self.assertFalse(fake.load()['abilityModes']['showUnverified'])
                self.write(root, True, True)
                self.assertTrue(fake.load()['abilityModes']['showUnverified'])
                self.assertNotIn('abilityModes', cat)
