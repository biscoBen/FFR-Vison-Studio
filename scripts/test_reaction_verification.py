"""Post-build regressions for existing Zidane reaction rows with borrowed effects."""
import ast
import contextlib
import copy
import glob
import io
import json
import os
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock

from test_existing_visions import ROOT, native, animation, installer


class ReactionVerificationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.root = Path(self.temp.name)
        self.rel = 'Battle/Sequencer/DT_BtlHitEffectData'
        self.targets = {446800: 'ジタン_フリーエナジー', 446820: 'ジタン_ミールツイスター'}
        self.sources = {446800: (220130, 'Water'), 446820: (220170, 'Aero')}
        self.units = [{'id': 13505, 'awakening': [[['ActiveSkill', sid] for sid in self.targets]], 'skills': {}}]
        self.game = {self.rel: {}, 'Skill/DT_SkillData': {}, 'Skill/DT_SkillEffectData': {},
                     'Asset/Skill/DT_SkillAsset': {}, 'Asset/Skill/CDT_SkillAsset_Demo': {},
                     'UI/Skill/DT_CommandSkillIcon': {}, 'UI/Skill/CDT_SkillIcon': {}}
        skills = []
        for sid, name in self.targets.items():
            donor, donor_name = self.sources[sid]; element = 'Water' if sid == 446800 else 'Wind'
            self.game[self.rel][name] = {'ID': sid, 'NormalEffectID': -1, 'CriticalEffectID': -1,
                                        'PlayShakeID': 0, 'MechanicsEffectID': 999, 'Untouched': [1, 2]}
            self.game[self.rel][donor_name] = {'ID': donor, 'NormalEffectID': donor + 1,
                'CriticalEffectID': donor + 2, 'PlayShakeID': 1, 'MechanicsEffectID': 123}
            skills += [{'id': sid, 'name': name, 'attr': 'Ability', 'seq': [], 'hits': 1,
                        'dmgType': 'Magic', 'element': element, 'mag': 25},
                       {'id': donor, 'name': donor_name, 'attr': 'Magic', 'hasUnit': 'All', 'seq': [1]}]
        self.catalog = {'skills': skills}
        self.save(self.root / 'data/ffr_catalog.json', self.catalog)
        policy = animation.effect_policy(self.catalog)['skills']
        self.report = {'schema': 1, 'skills': [{'id': sid, 'status': 'effect_reuse',
            **policy[str(sid)], 'reactionRow': self.sources[sid][1]} for sid in self.targets]}
        self.report_path = self.root / 'build/animation-repair-report.json'
        self.save(self.report_path, self.report); self.save_units()
        for rel, values in self.game.items(): self.save(self.root / 'extracted/rows' / (rel + '.json'), {'rows': values})
        reader = animation.NativeAnimations(lambda rel: self.game[rel], self.root, None, {})
        tables = {}
        for sid in self.targets:
            reader.bind_reaction_visuals(sid, {'reactionRow': self.sources[sid][1]}, tables)
        self.built = copy.deepcopy(self.game[self.rel])
        for edit in tables[self.rel]['set']: self.built[edit['row']].update(edit['set'])
        self.base = self.root / 'build/visions_mod/assets/FFRS/Content/Datatable'
        package = self.base / (self.rel + '.uasset'); package.parent.mkdir(parents=True)
        package.write_bytes(b'Explicit synthetic table presence; serializer returns test rows')
        source = installer.hook_verifier((ROOT / 'scripts/fixtures/existing_visions/verify_mod.py').read_bytes())
        functions = [n for n in ast.parse(source).body if isinstance(n, ast.FunctionDef)]
        def convert(args, **kwargs):
            self.save(Path(args[3]), {'rows': self.built})
            return SimpleNamespace(returncode=0, stderr='')
        self.env = {'ROOT': str(self.root), 'BASE': str(self.base), 'TMP': str(self.root / 'verify'),
            'os': os, 'json': json, 'sys': sys, 'glob': glob, 'subprocess': SimpleNamespace(run=convert),
            'UNUSED_ICON_TAGS': [13104], 'ffrenv': SimpleNamespace(FFRDT=['synthetic serializer'])}
        exec(compile(ast.Module(body=functions, type_ignores=[]), 'reaction_verifier_fixture', 'exec'), self.env)

    def tearDown(self): self.temp.cleanup()

    def save(self, path, value):
        path.parent.mkdir(parents=True, exist_ok=True); path.write_text(json.dumps(value), encoding='utf-8')

    def save_units(self): self.save(self.root / 'mods/EstherTsukiko/units.json', self.units)

    def verify(self):
        output = io.StringIO()
        with mock.patch.dict('sys.modules', {'_ffr_existingvisions': native, '_ffr_animation_repair': animation}), \
                contextlib.redirect_stdout(output), self.assertRaises(SystemExit) as result:
            self.env['main']()
        return result.exception.code, output.getvalue()

    def test_the_normal_verifier_accepts_both_exact_planned_cosmetic_changes(self):
        self.report_path.unlink()
        code, output = self.verify(); self.assertEqual(code, 1)
        self.assertIn('UNEXPECTED: ジタン_フリーエナジー, ジタン_ミールツイスター', output)
        self.save(self.report_path, self.report)
        code, output = self.verify(); self.assertEqual(code, 0)
        self.assertIn('OK: no pre-existing row changed unexpectedly', output)
        for sid, key in self.targets.items():
            self.assertEqual(self.built[key]['ID'], sid)
            self.assertEqual(self.built[key]['MechanicsEffectID'], 999)

    def test_unrelated_fields_wrong_cosmetic_values_and_missing_rows_still_fail(self):
        original = copy.deepcopy(self.built); key = self.targets[446800]
        for field, value in [('ID', 999), ('MechanicsEffectID', 123), ('NormalEffectID', 777), ('Untouched', [])]:
            with self.subTest(field=field):
                self.built = copy.deepcopy(original); self.built[key][field] = value
                self.assertEqual(self.verify()[0], 1)
        self.built = copy.deepcopy(original); self.built.pop(key)
        self.assertEqual(self.verify()[0], 1)

    def test_stale_incompatible_and_custom_reports_cannot_allow_changed_rows(self):
        for change in ('unselected', 'custom', 'wrong_donor', 'wrong_row', 'existing_sequence'):
            with self.subTest(change=change):
                units = copy.deepcopy(self.units); report = copy.deepcopy(self.report)
                if change == 'unselected': units[0]['awakening'] = []
                elif change == 'custom': units[0]['skills'] = {'446800': {'from': 446800}}
                elif change == 'wrong_donor': report['skills'][0]['donor'] = 999
                elif change == 'wrong_row': report['skills'][0]['reactionRow'] = 'Aero'
                else:
                    self.save(self.root / 'extracted/rows/Asset/Skill/DT_SkillAsset.json', {'rows': {'original': {'ID': 446801}}})
                self.save(self.root / 'mods/EstherTsukiko/units.json', units); self.save(self.report_path, report)
                self.assertEqual(self.verify()[0], 1)

    def test_report_cannot_authorize_shared_original_vision_reaction_edits(self):
        self.save(self.root / 'extracted/rows/Item/Vision/DT_VisionAwakeningMasteryData.json', {'rows': {
            'Original vision': {'ID': 13118, 'detailData': [
                {'parameterType': 'ActiveSkill', 'params': [sid, -1]} for sid in self.targets]}}})
        code, output = self.verify()
        self.assertEqual(code, 1); self.assertIn('UNEXPECTED', output)


if __name__ == '__main__': unittest.main()
