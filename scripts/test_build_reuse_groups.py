"""Small setting edits must not recook unrelated native packages."""
import copy
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'assets/existing_visions/payload'))
import _ffr_build_cache as reuse
import _ffr_incremental as incremental
import _ffr_game_tables as tables


class GroupReuseTests(unittest.TestCase):
    def test_setting_edit_batches_only_changed_assets_and_rebuilds_corrupt_entries(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); legacy = root / 'legacy'; out = root / 'out'
            legacy.mkdir(); calls = []
            for name in ('Shop', 'Skills', 'Icon'):
                (legacy / (name + '.uasset')).write_bytes(name.encode())
                (legacy / (name + '.uexp')).write_bytes(b'original exports')
            plan = {'legacyRoot': str(legacy), 'outRoot': str(out), 'tables': [
                {'asset': name, 'add': [], 'set': [{'row': 'A', 'set': {'value': 1}}]}
                for name in ('Shop', 'Skills')], 'clones': [{'from': 'Icon', 'to': 'PrivateIcon', 'rename': []}]}
            recipe = root / 'patch.json'
            def tool(cmd):
                p = json.loads(Path(cmd[2]).read_bytes()); calls.append(p)
                for kind in ('tables', 'objects', 'clones'):
                    for op in p.get(kind, []):
                        name = op['to'] if kind == 'clones' else op['asset']
                        dest = out / (name + '.uasset'); dest.parent.mkdir(exist_ok=True)
                        dest.write_bytes(json.dumps(op, sort_keys=True).encode())
                        dest.with_suffix('.uexp').write_bytes(b'exports')
            def build():
                recipe.write_text(json.dumps(plan)); c = reuse.Cache(root, {'game': 'one'}, ['native'])
                env = {}
                with mock.patch.object(reuse, '_active', c): incremental.install(env)
                c.run(['native', 'patch', str(recipe)], tool)
                return c
            build(); self.assertEqual(len(calls), 1)
            expected = {p.name: p.read_bytes() for p in out.iterdir()}
            shutil.rmtree(out); build(); self.assertEqual(len(calls), 1)
            self.assertEqual(expected, {p.name: p.read_bytes() for p in out.iterdir()})
            plan['tables'][0]['set'][0]['set']['value'] = 2
            shutil.rmtree(out); build()
            self.assertEqual(len(calls), 2)
            self.assertEqual([p['asset'] for p in calls[-1]['tables']], ['Shop'])
            self.assertNotIn('clones', calls[-1])
            self.assertEqual((out / 'Skills.uasset').read_bytes(), expected['Skills.uasset'])
            # Changed native inputs invalidate their own package as well.
            (legacy / 'Skills.uexp').write_bytes(b'updated game')
            shutil.rmtree(out); build()
            self.assertEqual([p['asset'] for p in calls[-1]['tables']], ['Skills'])
            # A missing sidecar must be regenerated, never restored partially.
            for p in (root / 'build/reuse').rglob('manifest.json'):
                meta = json.loads(p.read_bytes())
                if any(r['suffix'] == '.uexp' for r in meta['files']):
                    (p.parent / '1.bin').write_bytes(b'corrupt')
            shutil.rmtree(out); build()
            self.assertEqual(len(calls), 4)
            self.assertTrue((out / 'PrivateIcon.uexp').is_file())

    def test_in_place_and_unknown_recipes_keep_the_existing_native_path(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); c = reuse.Cache(root, {}, ['native'])
            path = root / 'patch.json'
            for plan in ({'legacyRoot': str(root), 'outRoot': str(root), 'tables': []},
                         {'legacyRoot': str(root), 'outRoot': str(root/'out'), 'frames': []}):
                path.write_text(json.dumps(plan))
                self.assertIsNone(incremental._groups(c, ['native', 'patch', str(path)]))


class SnapshotTests(unittest.TestCase):
    def test_each_cli_invocation_starts_a_new_snapshot(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); values = {'A': {'ID': 1}}
            first = tables.snapshot(root, lambda rel: copy.deepcopy(values))
            self.assertEqual(first('Skill/Example')['A']['ID'], 1)
            values['A']['ID'] = 2
            second = tables.snapshot(root, first)
            self.assertEqual(second('Skill/Example')['A']['ID'], 2)
            self.assertEqual(first('Skill/Example')['A']['ID'], 1)
            tables._snapshots.pop(str(root.resolve()))

    def test_decode_once_nested_mutation_rejected_and_copied_rows_remain_editable(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); calls = []
            original = {'A': {'ID': 1, 'stats': {'HP': 10}, 'skills': [1, {'ID': 2}]}}
            def read(rel): calls.append(rel); return copy.deepcopy(original)
            rows = tables.BuildTables(root, read)
            first = rows('Skill/Example')
            self.assertIs(rows('Skill/Example'), first)
            self.assertEqual(calls, ['Skill/Example'])
            for mutation in (lambda: first['A']['stats'].__setitem__('HP', 20),
                             lambda: first['A']['skills'].append(3),
                             lambda: first['A']['skills'][1].update(ID=4)):
                with self.assertRaises(TypeError): mutation()
            edited = copy.deepcopy(first['A']); edited['stats']['HP'] = 50; edited['skills'].append(4)
            self.assertEqual(first, original)
            self.assertEqual(json.loads(json.dumps(first)), original)

    def test_default_editor_reader_sees_updated_files_without_cli_snapshot(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); path = root / 'extracted/rows/Skill/Example.json'
            path.parent.mkdir(parents=True)
            path.write_text(json.dumps({'rows': {'A': {'ID': 1}}}))
            reader = tables.reader(root)
            self.assertEqual(reader('Skill/Example')['A']['ID'], 1)
            path.write_text(json.dumps({'rows': {'A': {'ID': 2}}}))
            self.assertEqual(reader('Skill/Example')['A']['ID'], 2)


if __name__ == '__main__': unittest.main()
