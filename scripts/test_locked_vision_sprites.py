"""Exercise locked/unlocked menu rendering through the installed converter CLI."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
PAYLOAD = ROOT / 'assets/existing_visions/payload'
ENGINE_SHA = '1c6e4d4b348b048404b6578bf10010c4caa873a5599d9dcbb9f64b00d299c41d'


def pixels(image):
    raw = image.tobytes()
    return zip(raw[0::4], raw[1::4], raw[2::4], raw[3::4])


class LockedVisionSpritesTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.tools = self.root / 'engine/tools'
        self.frames = self.tools / 'ffbe2ss6'
        self.frames.mkdir(parents=True)
        for name in ('ffbe_frames.py', 'build_sprites.py'):
            shutil.copyfile(ROOT / 'scripts/fixtures/engine_motion' / name, self.frames / name)
        for name in ('_ffr_build_sprites.py', '_ffr_animation_repair.py', '_ffr_ability_modes.py'):
            shutil.copyfile(PAYLOAD / name, self.tools / name)
        self.sprites = self.root / 'sprites'
        self.sprites.mkdir()
        self.write_sprites()

    def write_sprites(self, size=3):
        sheet = Image.new('RGBA', (size * 4, size))
        colors = [(250, 80, 20, 255), (30, 240, 60, 255),
                  (60, 50, 230, 255), (250, 220, 100, 255)]
        for i, color in enumerate(colors):
            sheet.paste(color, (i * size, 0, (i + 1) * size, size))
            sheet.putpixel((i * size, 0), (*color[:3], 0))
            sheet.putpixel((i * size + 1, 0), (*color[:3], 83))
        sheet.save(self.sprites / 'unit_anime_1.png')
        (self.sprites / 'unit_cgg_1.csv').write_text(''.join(
            f'0,1,{i - 2},{2 - i},0,0,100,0,{i * size},0,{size},{size},0\n'
            for i in range(4)))
        for name, content in {'idle': '0,0,0,7\n', 'standby': '1,-2,4,3\n2,5,-3,5\n',
                              'win': '3,1,0,9\n', 'atk': '3,0,0,2\n'}.items():
            (self.sprites / f'unit_{name}_cgs_1.csv').write_text(content)

    def convert(self, folder, *, reference=False, flags=()):
        script = self.frames / 'build_sprites.py' if reference else self.tools / '_ffr_build_sprites.py'
        output = self.root / folder
        run = subprocess.run([sys.executable, str(script), str(self.sprites), '1', '13529',
                              str(output), *flags], capture_output=True, text=True)
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        return output

    def read_menu(self, output):
        spec = json.loads((output / 'menu/spec.json').read_bytes())
        with Image.open(output / 'menu/atlas.png') as image:
            atlas = image.convert('RGBA')
        cells = {}
        for cell in spec['cells']:
            x, y = cell['pos']; width, height = cell['size']
            cells[cell['name']] = atlas.crop((int(x), int(y), int(x + width), int(y + height)))
        self.assertEqual(spec['pixelSize'], list(atlas.size))
        self.assertEqual((output / 'menu/tex.bgra').read_bytes(), atlas.tobytes('raw', 'BGRA'))
        return spec, atlas, cells

    def assert_locked_only(self, before, after):
        original, _, old_cells = self.read_menu(before)
        spec, atlas, cells = self.read_menu(after)
        old_clips = {clip['name']: clip for clip in original['animations']}
        clips = {clip['name']: clip for clip in spec['animations']}
        self.assertEqual(set(clips), set(old_clips))
        for name, clip in clips.items():
            if name != 'Lock':
                self.assertEqual(clip, old_clips[name], name)
        # Every old cell keeps its pixels, dimensions and pivot despite packing.
        by_name = {cell['name']: cell for cell in spec['cells']}
        for cell in original['cells']:
            other = by_name[cell['name']]
            self.assertEqual({k: v for k, v in cell.items() if k != 'pos'},
                             {k: v for k, v in other.items() if k != 'pos'})
            self.assertEqual(cells[cell['name']].tobytes(), old_cells[cell['name']].tobytes())
        locked = clips['Lock']; old_locked = old_clips['Lock']
        self.assertEqual({k: v for k, v in locked.items() if k != 'parts'},
                         {k: v for k, v in old_locked.items() if k != 'parts'})
        used = set()
        for part, attributes in locked['parts'].items():
            self.assertEqual({k: v for k, v in attributes.items() if k != 'Cell'},
                             {k: v for k, v in old_locked['parts'][part].items() if k != 'Cell'})
            for (time, name), (old_time, old_name) in zip(
                    attributes.get('Cell', []), old_locked['parts'][part].get('Cell', []), strict=True):
                self.assertEqual(time, old_time)
                self.assertNotEqual(name, old_name)
                used.add(name)
                image = cells[name]; source = old_cells[old_name]
                self.assertEqual(image.size, source.size)
                self.assertEqual(by_name[name]['pivot'], by_name[old_name]['pivot'])
                self.assertEqual(image.getchannel('A').tobytes(), source.getchannel('A').tobytes())
                self.assertTrue(any(r != g or g != b for r, g, b, a in pixels(source) if a))
                self.assertTrue(all(r == g == b and r <= 102 for r, g, b, a in pixels(image) if a))
                self.assertTrue(any(r > 0 for r, g, b, a in pixels(image) if a))
        self.assertEqual(set(cells) - set(old_cells), used)
        for cell in spec['cells']:
            x, y = cell['pos']; width, height = cell['size']
            self.assertLessEqual(x + width, atlas.width)
            self.assertLessEqual(y + height, atlas.height)

    def test_locked_frames_are_dark_grey_with_original_alpha_pose_and_timing(self):
        source = {p.name: p.read_bytes() for p in self.sprites.iterdir()}
        before = self.convert('before', reference=True)
        after = self.convert('after')
        self.assert_locked_only(before, after)
        self.assertEqual(source, {p.name: p.read_bytes() for p in self.sprites.iterdir()})
        # The battle Lock pose has a separate purpose and must remain in color.
        for path in (before / 'battle').iterdir():
            self.assertEqual(path.read_bytes(), (after / 'battle' / path.name).read_bytes(), path.name)

    def test_menu_only_grows_atlas_and_updates_spec_and_bgra_without_touching_battle(self):
        self.write_sprites(size=250)
        before = self.convert('large-before', reference=True, flags=('--menu-only',))
        after = self.convert('large-after', flags=('--menu-only',))
        self.assert_locked_only(before, after)
        original = json.loads((before / 'menu/spec.json').read_bytes())
        spec = json.loads((after / 'menu/spec.json').read_bytes())
        self.assertGreater(spec['pixelSize'][1], original['pixelSize'][1])
        self.assertFalse((after / 'battle').exists())

    def test_battle_only_leaves_existing_menu_files_untouched(self):
        output = self.convert('only')
        menu = {p.name: p.read_bytes() for p in (output / 'menu').iterdir()}
        self.convert('only', flags=('--battle-only',))
        self.assertEqual(menu, {p.name: p.read_bytes() for p in (output / 'menu').iterdir()})

    def test_missing_standby_uses_the_visions_own_idle_for_the_locked_pose(self):
        (self.sprites / 'unit_standby_cgs_1.csv').unlink()
        before = self.convert('idle-before', reference=True, flags=('--menu-only',))
        after = self.convert('idle-after', flags=('--menu-only',))
        self.assert_locked_only(before, after)

    def test_repeated_lock_frames_share_one_grey_cell_without_changing_delays(self):
        (self.sprites / 'unit_standby_cgs_1.csv').write_text(
            '1,-2,4,3\n1,-2,4,7\n2,5,-3,5\n')
        before = self.convert('repeated-before', reference=True, flags=('--menu-only',))
        after = self.convert('repeated-after', flags=('--menu-only',))
        self.assert_locked_only(before, after)
        old_spec = json.loads((before / 'menu/spec.json').read_bytes())
        spec = json.loads((after / 'menu/spec.json').read_bytes())
        self.assertEqual(len(spec['cells']) - len(old_spec['cells']), 2)

    @unittest.skipUnless(os.name == 'nt' and os.environ.get('GITHUB_ACTIONS') == 'true',
                         'Requires Windows CI and its checksum-verified engine cache.')
    def test_same_locked_behavior_with_the_actual_checksum_pinned_engine_converter(self):
        archive = Path(os.environ['RUNNER_TEMP']) / 'ffr-studio-engine-cache' / (ENGINE_SHA + '.zip')
        with archive.open('rb') as stream:
            self.assertEqual(hashlib.file_digest(stream, 'sha256').hexdigest(), ENGINE_SHA)
        with zipfile.ZipFile(archive) as bundle:
            for name in ('ffbe_frames.py', 'build_sprites.py'):
                (self.frames / name).write_bytes(bundle.read('tools/ffbe2ss6/' + name))
        self.assert_locked_only(self.convert('actual-before', reference=True), self.convert('actual-after'))


if __name__ == '__main__':
    unittest.main()
