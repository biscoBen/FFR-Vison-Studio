"""Switch existing preset donors without reverting their mechanics or saved kits."""
import ast
import copy
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock

from test_existing_visions import ROOT, installer, fina_installer
from test_animation_and_library import motion, library
import _ffr_ability_modes as modes
import _ffr_sephira as pack


def write(root, enabled):
    path = Path(root) / pack.CONFIG
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({'schema': 1, 'useBorrowedSkillVisuals': enabled}))


def presets():
    catalog = json.loads((ROOT / 'assets/sephira_visions/catalog.json').read_bytes())
    result = []
    for p in catalog['presets']:
        u = copy.deepcopy(p['profile'])
        u[pack.FIELD] = {'version': 1, 'preset': p['id'], 'enabled': True}
        result.append(u)
    return result


class SephiraVisualTests(unittest.TestCase):
    def test_default_preserves_demo_visuals_and_settings_are_strict(self):
        with tempfile.TemporaryDirectory() as root:
            self.assertTrue(pack.settings(root)['useBorrowedSkillVisuals'])
            roster = presets()
            self.assertEqual(pack.visual_units(roster, root), roster)
            for invalid in ({}, {'schema': True, 'useBorrowedSkillVisuals': True},
                            {'schema': 1, 'useBorrowedSkillVisuals': 0},
                            {'schema': 1, 'useBorrowedSkillVisuals': True, 'extra': False}):
                with self.assertRaises(ValueError): pack.validate_settings(invalid)

    def test_all_216_substitutions_round_trip_without_changes_to_combat_grants_or_lbs(self):
        roster = presets(); before = copy.deepcopy(roster)
        policy = json.loads((ROOT / 'assets/existing_visions/payload/sephira_visuals.json').read_bytes())
        expected = {u[pack.FIELD]['preset']: {str(s['from']): s['visuals'] for s in u['skills'].values()
                    if s.get('visuals', s['from']) != s['from']} for u in roster}
        self.assertEqual(policy, {'schema': 1, 'presets': expected})
        with tempfile.TemporaryDirectory() as root:
            write(root, False)
            built = pack.visual_units(roster, root); count = 0
            for original, unit in zip(roster, built):
                for sid, s in unit['skills'].items():
                    source = original['skills'][sid]
                    if source.get('visuals', source['from']) == source['from']:
                        self.assertEqual(s, source)
                    else:
                        self.assertEqual(s['visuals'], s['from'])
                        self.assertTrue(s.pop('_sephiraSourceVisuals'))
                        s['visuals'] = source['visuals']; count += 1
                self.assertEqual(unit, original)
            self.assertEqual(count, 216)
            self.assertEqual(roster, before)
            write(root, True)
            self.assertEqual(pack.visual_units(roster, root), before)

    def test_allocated_ids_old_recipes_and_user_edits_are_preserved(self):
        unit = presets()[0]; source = next(s for s in unit['skills'].values() if s['visuals'] != s['from'])
        unit['skills'] = {900000: copy.deepcopy(source), '900010': {**source, 'visuals': 210010},
                          '900020': {**source, 'clone_sequence': True},
                          '900030': {'from': 400010, 'en': 'User copy', 'set': {'Cost': 2}},
                          '900040': {**source, 'tint': 0}, '900050': {**source, 'motion': 'attack_B'}}
        unit['sephiraRecipe'] = 2
        untagged = copy.deepcopy(unit); untagged.pop(pack.FIELD)
        before = copy.deepcopy([unit, untagged])
        with tempfile.TemporaryDirectory() as root:
            write(root, False); built = pack.visual_units([unit, untagged], root)
            self.assertEqual(built[0]['skills'][900000]['visuals'], source['from'])
            for sid in ('900010', '900020', '900030', '900040', '900050'):
                self.assertEqual(built[0]['skills'][sid], unit['skills'][sid])
            self.assertEqual(built[1], untagged)
            self.assertEqual([unit, untagged], before)

    def test_server_restart_atomic_failure_and_build_guard_preserve_other_settings(self):
        routes = {}
        class App:
            def get(self, route):
                def decorator(f): routes[('GET', route)] = f; return f
                return decorator
            def put(self, route):
                def decorator(f): routes[('PUT', route)] = f; return f
                return decorator
        class HTTPException(Exception):
            def __init__(self, status, detail): super().__init__(detail)
        with tempfile.TemporaryDirectory() as root, mock.patch.dict(sys.modules, {'fastapi': SimpleNamespace(HTTPException=HTTPException)}):
            other = Path(root) / 'mods/EstherTsukiko'; other.mkdir(parents=True)
            unchanged = {'units.json': '[{"keep":true}]', 'ability-modes.json': '{"schema":1,"showUnverified":true,"useChanges":true}',
                         'testing.json': '{"schema":1,"maxMr":true}'}
            for name, raw in unchanged.items(): (other / name).write_text(raw)
            state = {'running': False}; pack.register(App(), {'ROOT': root, 'state': state})
            get = routes[('GET', '/api/sephira/settings')]; put = routes[('PUT', '/api/sephira/settings')]
            off = {'schema': 1, 'useBorrowedSkillVisuals': False}
            self.assertTrue(get()['useBorrowedSkillVisuals']); self.assertEqual(put(off), off)
            pack.register(App(), {'ROOT': root, 'state': state})
            self.assertEqual(routes[('GET', '/api/sephira/settings')](), off)
            with mock.patch.object(pack.os, 'replace', side_effect=OSError('disk full')):
                with self.assertRaisesRegex(HTTPException, 'disk full'): put({**off, 'useBorrowedSkillVisuals': True})
            self.assertEqual(get(), off)
            self.assertFalse(list(other.glob('sephira-settings-*')))
            state['running'] = True
            with self.assertRaisesRegex(HTTPException, 'build to finish'): put({**off, 'useBorrowedSkillVisuals': True})
            self.assertEqual(get(), off)
            for name, raw in unchanged.items(): self.assertEqual((other / name).read_text(), raw)

    def test_original_mode_restores_native_shared_sequence_pointers_and_retains_user_pointers(self):
        unit = presets()[1]
        sid, recipe = next((sid, s) for sid, s in unit['skills'].items() if s['from'] == 500230)
        self.assertEqual(recipe['set']['playSequencerId'], -1)
        source = {'ID': 500230, 'playSequencerId': 225042, 'sequencerIdWhenTargetFriendlies': 225041}
        rows = lambda rel: {'Absolute Zero': source}
        before = copy.deepcopy(unit)
        with tempfile.TemporaryDirectory() as root:
            write(root, False)
            result = pack.visual_units([unit], root, rows)[0]
            changed = result['skills'][sid]
            self.assertEqual(changed['set']['playSequencerId'], 225042)
            self.assertEqual(changed['set']['sequencerIdWhenTargetFriendlies'], 225041)
            combat = {k: v for k, v in changed['set'].items() if k not in source}
            self.assertEqual(combat, {k: v for k, v in recipe['set'].items() if k not in source})
            self.assertEqual(unit, before)
            edited = copy.deepcopy(unit); edited['skills'][sid]['set']['playSequencerId'] = 210011
            self.assertEqual(pack.visual_units([edited], root, rows)[0]['skills'][sid]['set']['playSequencerId'], 210011)
            write(root, True)
            self.assertEqual(pack.visual_units([unit], root, rows), [before])

    def test_library_repairs_cannot_replace_missing_original_visuals_in_any_mode(self):
        unit = presets()[0]
        sid, recipe = next((int(sid), s) for sid, s in unit['skills'].items() if s['visuals'] != s['from'])
        unit['skills'] = {str(sid): recipe}; unit['awakening'] = [[['ActiveSkill', sid]]]; unit['synchro'] = []
        for show in (False, True):
            for changes in (False, True):
                with self.subTest(show=show, changes=changes), tempfile.TemporaryDirectory() as root:
                    write(root, False)
                    (Path(root) / modes.CONFIG).write_text(json.dumps({'schema': 1, 'showUnverified': show, 'useChanges': changes}))
                    built = pack.visual_units([unit], root); tables = {}; clones = [{'user': True}]; jobs = [{'user': True}]
                    rows = lambda rel: {}
                    extract = mock.Mock(side_effect=AssertionError('Must not prepare a substitute'))
                    native = SimpleNamespace(visual_policy={}, reuse=mock.Mock(side_effect=AssertionError('Must not borrow a donor')))
                    with mock.patch.dict(sys.modules, {'_ffr_animation_repair': motion}), mock.patch.object(
                            motion, 'NativeAnimations', return_value=native):
                        self.assertEqual(modes.prepare_sequences(tables, clones, jobs, built, root, rows, extract, native_support=object()), [])
                    self.assertEqual((tables, clones, jobs), ({}, [{'user': True}], [{'user': True}]))
                    if show and changes:
                        report = json.loads((Path(root) / 'build/animation-repair-report.json').read_text())
                        self.assertEqual(report['skills'], [{'id': sid, 'status': 'original_source_visuals', 'source': recipe['from']}])

    def test_installed_skill_builder_uses_future_source_timeline_and_original_combat_copy(self):
        patched = installer.hook_builder(fina_installer.hook_builder(
            (ROOT / 'scripts/fixtures/crystal_fina/make_vision_mod.py').read_bytes()))
        tree = ast.parse(patched)
        main = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'main')
        choices = [n for n in main.body if isinstance(n, ast.Assign) and ast.unparse(n.targets[0]) == 'UNITS']
        self.assertIn('_ffr_sephira.visual_units', ast.unparse(choices[0]))
        function = next(n for n in main.body if isinstance(n, ast.FunctionDef) and n.name == '_native_skills')
        # Execute the real hooked custom-skill block with future source bindings.
        body = [n for n in function.body if not isinstance(n, ast.Nonlocal)]
        stop = next(i for i, n in enumerate(body) if isinstance(n, ast.Assign) and ast.unparse(n.targets[0]) == 'missing')
        block = ast.Module(body=body[:stop], type_ignores=[])
        unit = presets()[0]; sid, recipe = next((int(sid), s) for sid, s in unit['skills'].items() if s['visuals'] != s['from'])
        unit['skills'] = {sid: recipe}; unit.pop('lb_custom')
        game = {'Skill/DT_SkillData': {'source': {'ID': recipe['from'], 'Cost': 999}, 'donor': {'ID': recipe['visuals'], 'Cost': 888}},
                'Battle/Sequencer/DT_BtlHitEffectData': {'source hit': {'ID': recipe['from']}, 'donor hit': {'ID': recipe['visuals']}}}
        for rel in ('Asset/Skill/DT_SkillAsset', 'Asset/Skill/CDT_SkillAsset_Demo'):
            game[rel] = {f'{name} {off}': {'ID': id + off, 'LevelSequence': f'/Game/{name}/{off}'}
                         for name, id in [('source', recipe['from']), ('donor', recipe['visuals'])] for off in (0, 1, 2)}
        with tempfile.TemporaryDirectory() as root:
            for enabled in (True, False, True):
                write(root, enabled); u = pack.visual_units([unit], root)[0]; tables = {}
                env = {'u': u, 'vid': u['id'], 'rows': lambda rel: copy.deepcopy(game[rel]),
                       'tbl': lambda rel: tables.setdefault(rel, {'add': [], 'set': []}), 'text': lambda s: s,
                       'unique_skill_base': lambda vid: sid - 1,
                       'ffbe_resonance': SimpleNamespace(uses_ffbe=lambda u, s: False)}
                exec(compile(block, 'installed_sephira_skill_builder', 'exec'), env)
                self.assertEqual(tables['Skill/DT_SkillData']['add'][0]['cloneFrom'], 'source')
                self.assertEqual(tables['Skill/DT_SkillData']['add'][0]['set']['Cost'], recipe['set']['Cost'])
                donor = 'donor' if enabled else 'source'
                for rel in ('Asset/Skill/DT_SkillAsset', 'Asset/Skill/CDT_SkillAsset_Demo'):
                    self.assertEqual([r['cloneFrom'] for r in tables[rel]['add']], [f'{donor} {off}' for off in (0, 1, 2)])
                    self.assertEqual([r['set']['ID'] for r in tables[rel]['add']], [sid + off for off in (0, 1, 2)])
                self.assertEqual(tables['Battle/Sequencer/DT_BtlHitEffectData']['add'][0]['cloneFrom'], f'{donor} hit')
                with mock.patch.dict(sys.modules, {'_ffr_animation_repair': motion}):
                    self.assertEqual(motion.prepare_sequences(tables, [], [], [u], root, lambda rel: copy.deepcopy(game.get(rel, {})),
                                     mock.Mock(side_effect=AssertionError('Future source sequence must take priority'))), [])

    def test_catalog_reload_reads_current_setting_without_mutating_cached_catalog(self):
        with tempfile.TemporaryDirectory() as root, mock.patch.dict(sys.modules, {'_ffr_animation_repair': motion}):
            catalog = {'skills': [], 'passives': [], 'visions': []}; fake = SimpleNamespace(load=lambda: catalog)
            with mock.patch.object(library, 'analyze', return_value={'schema': 1, 'available': False}):
                library.install(fake, root)
                self.assertTrue(fake.load()['sephiraSettings']['useBorrowedSkillVisuals'])
                write(root, False)
                self.assertFalse(fake.load()['sephiraSettings']['useBorrowedSkillVisuals'])
                self.assertNotIn('sephiraSettings', catalog)
