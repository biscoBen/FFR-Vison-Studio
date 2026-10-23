"""Read-only movie collector: binary extraction and bounded, scoped diagnostics."""
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

ROOT = Path(__file__).resolve().parents[1]
FOLDER = ROOT / 'scripts/reference/crystal-fina-battle'
HELPER = FOLDER / 'Collect Fina Movie Diagnostics.ps1'
PWSH = shutil.which('pwsh')
REPAK = os.environ.get('FFR_TEST_REPAK') or shutil.which('repak')
NAMES = ['Collect Fina Movie Diagnostics.cmd', HELPER.name, 'Movie Diagnostics README.txt']
PLAYER_NAMES = ['Collect Fina Movie Player.cmd', HELPER.name, 'Movie Player README.txt']


class MovieDownloadTests(unittest.TestCase):
    def test_standalone_download_contains_exact_reviewed_sources(self):
        with zipfile.ZipFile(FOLDER / 'Crystal-Fina-Movie-Diagnostics.zip') as z:
            self.assertEqual(z.namelist(), NAMES)
            self.assertIsNone(z.testzip())
            for name in NAMES:
                self.assertEqual(z.read(name).decode('utf-8').replace('\r\n', '\n'),
                                 (FOLDER / name).read_text())

    def test_player_download_contains_exact_reviewed_sources(self):
        with zipfile.ZipFile(FOLDER / 'Crystal-Fina-Movie-Player-Reference.zip') as z:
            self.assertEqual(z.namelist(), PLAYER_NAMES)
            self.assertIsNone(z.testzip())
            for name in PLAYER_NAMES:
                self.assertEqual(z.read(name).decode('utf-8').replace('\r\n', '\n'),
                                 (FOLDER / name).read_text())


@unittest.skipUnless(PWSH and REPAK, 'PowerShell and repak required; set FFR_TEST_REPAK if needed.')
class MovieCollectorTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.game = self.root / "Game & user's folder"
        self.engine = self.root / "Studio & user's folder/engine"
        (self.game / 'FFRS/Binaries/Win64').mkdir(parents=True)
        self.write(self.engine / 'tools/make_vision_mod.py', b'# fixture')
        self.write(self.engine / 'config.json', json.dumps({'gameRoot': str(self.game), 'secret': 'private'}).encode())
        tool = self.engine / 'tools/repak/repak.exe'
        tool.parent.mkdir(parents=True)
        shutil.copy2(REPAK, tool)
        self.output = self.root / 'results'
        self.env = dict(os.environ, USERPROFILE=str(self.root), LOCALAPPDATA=str(self.root / 'Local'),
                        XDG_CACHE_HOME=str(self.root / 'cache'), XDG_CONFIG_HOME=str(self.root / 'config'),
                        XDG_DATA_HOME=str(self.root / 'data'))
        self.private = 'FFRS/Content/Movies/Studio/CrystalFina_Test'
        self.native = 'FFRS/Content/Movies/Skill/MV_Skill440110'
        self.master = 'FFRS/Content/Sequencer/Battle/Skill/444030/444031/SEQ_Battle_444031_Master'

    def write(self, path, data):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return path

    def pack(self, label, destination, entry, data):
        stage = self.root / label
        self.write(stage / entry, data)
        destination.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run([REPAK, 'pack', '--version', 'V11', '--mount-point', '../../../',
                        str(stage), str(destination)], check=True, capture_output=True)

    def run_helper(self, *, success=True, player=False):
        p = subprocess.run([PWSH, '-NoLogo', '-NoProfile', '-File', str(HELPER),
                            '-EnginePath', str(self.engine), '-GamePath', str(self.game),
                            '-OutputRoot', str(self.output), '-NoPrompt',
                            *(['-PlayerReference'] if player else [])],
                           env=self.env, text=True, capture_output=True, timeout=60)
        self.assertEqual(p.returncode, 0 if success else 1, p.stdout + p.stderr)
        return p

    def digest(self, folder):
        return {str(p.relative_to(folder)): hashlib.sha256(p.read_bytes()).hexdigest()
                for p in folder.rglob('*') if p.is_file()}

    def archive(self):
        path, = self.output.glob('*.zip')
        return zipfile.ZipFile(path)

    def test_extracts_exact_binary_prefixes_and_leaves_game_and_studio_untouched(self):
        paks = self.game / 'FFRS/Content/Paks'
        fina = b'CRID' + bytes(range(256)) * 9
        native = b'CRID' + bytes(range(256)) * 10000
        self.pack('fina-stage', paks / '~mods/zzz_EstherTsukiko_P.pak', self.private + '.usm', fina)
        self.pack('native-stage', paks / 'FFRS-Windows.pak', self.native + '_vp9.usm', native)
        self.write(self.engine / 'build/fina-cinematic/timeline.json', json.dumps({'asset': self.master}).encode())
        self.write(self.engine / ('build/visions_mod/assets/' + self.master + '.uasset'), b'master')
        self.write(self.engine / ('build/visions_mod/assets/' + self.private + '_vp9.uasset'), b'private descriptor')
        self.write(self.engine / ('extracted/legacy/' + self.native + '_vp9.uasset'), b'native descriptor')
        self.write(self.game / 'FFRS/Saved/SaveGames/private.sav', b'private save')
        self.write(self.game / 'FFRS/Saved/Logs/FFRS.log', b'LogMana: failed movie fixture')
        self.write(self.engine / 'tools/fina_cinematic.zip', b'')
        with zipfile.ZipFile(self.engine / 'tools/fina_cinematic.zip', 'w') as z:
            z.writestr('manifest.json', '{}'); z.writestr('spec.json', '{}')
            z.writestr('unrelated-private.txt', 'private')
        self.write(self.game / 'FFRS/Saved/Config/Windows/GameUserSettings.ini',
                   b'bPlayCG=True\nAccountToken=private\n')
        before = (self.digest(self.game), self.digest(self.engine))
        self.run_helper()
        self.assertEqual(before, (self.digest(self.game), self.digest(self.engine)))
        with self.archive() as z:
            self.assertEqual(z.read('movies/installed-fina.usm-prefix'), fina)
            self.assertEqual(z.read('movies/original-cloud.usm-prefix'), native[:2*1024*1024])
            report = json.loads(z.read('report.json').decode('utf-8-sig'))
            self.assertEqual(report['errors'], [])
            self.assertEqual([s['prefixOnly'] for s in report['samples']], [False, True])
            self.assertIn('engine/build/visions_mod/assets/' + self.master + '.uasset', z.namelist())
            self.assertIn('engine/build/visions_mod/assets/' + self.private + '_vp9.uasset', z.namelist())
            self.assertIn('engine/extracted/legacy/' + self.native + '_vp9.uasset', z.namelist())
            self.assertIn(b'bPlayCG=True', z.read('report.json'))
            self.assertNotIn(b'AccountToken', z.read('report.json'))
            self.assertFalse(any(n.endswith(('.pak', '.ucas', '.utoc', '.sav', 'config.json', 'unrelated-private.txt')) for n in z.namelist()))

    def test_missing_movies_return_a_report_and_untrusted_timeline_is_not_followed(self):
        self.write(self.engine / 'build/fina-cinematic/timeline.json',
                   b'{"asset":"../../private/credentials"}')
        self.run_helper()
        with self.archive() as z:
            r = json.loads(z.read('report.json').decode('utf-8-sig'))
            self.assertEqual(len(r['errors']), 3)
            self.assertEqual(r['samples'], [])
            self.assertFalse(any(n.startswith('movies/') for n in z.namelist()))

    def test_reads_loose_original_and_exports_decoder_options_without_game_key_or_other_config(self):
        native = b'CRID' + bytes(range(256)) * 10000
        self.write(self.game / (self.native + '_vp9.usm'), native)
        settings = (b'[/Script/CriWareRuntime.CriWarePluginSettings]\r\n'
                    b'DecryptKey=4141414141414141\r\nbEnableManaDecryption=True\r\n'
                    b'NumManaDecoders=6\r\nManaVideoKey=do-not-export\r\n'
                    b'[Other]\r\nAccountToken=do-not-export\r\n')
        paks = self.game / 'FFRS/Content/Paks'
        self.pack('profile-stage', paks / 'FFRS-Windows.pak', 'FFRS/Config/DefaultEngine.ini', settings)
        self.write(self.engine / 'extracted/pak/FFRS/Config/DefaultEngine.ini',
                   settings.replace(b'bEnableManaDecryption=True', b'bEnableManaDecryption=False'))
        before = (self.digest(self.game), self.digest(self.engine))
        self.run_helper()
        self.assertEqual(before, (self.digest(self.game), self.digest(self.engine)))
        with self.archive() as z:
            self.assertEqual(z.read('movies/original-cloud.usm-prefix'), native[:2*1024*1024])
            raw = z.read('report.json')
            r = json.loads(raw.decode('utf-8-sig'))
            self.assertEqual(r['schema'], 2)
            self.assertEqual([p['options']['bEnableManaDecryption'] for p in r['movieProfiles']], ['True', 'False'])
            self.assertTrue(all(p['keyConfigured'] for p in r['movieProfiles']))
            self.assertTrue(all(p['options']['NumManaDecoders'] == '6' for p in r['movieProfiles']))
            self.assertEqual(len(r['nativeMovieAttempts']), 1)
            self.assertNotIn(b'4141414141414141', raw)
            self.assertNotIn(b'ManaVideoKey', raw)
            self.assertNotIn(b'do-not-export', raw)
            self.assertFalse(any(n.endswith('.ini') for n in z.namelist()))

    def test_collects_corrected_streams_movie_entry(self):
        movie = b'CRID' + bytes(range(256)) * 10
        entry = 'FFRS/Content/Streams/Movies/Studio/CrystalFina_Test.usm'
        self.pack('corrected-stage', self.game / 'FFRS/Content/Paks/~mods/zzz_EstherTsukiko_P.pak', entry, movie)
        self.run_helper()
        with self.archive() as z:
            self.assertEqual(z.read('movies/installed-fina.usm-prefix'), movie)
            report = json.loads(z.read('report.json').decode('utf-8-sig'))
            self.assertEqual(report['samples'][0]['entry'], entry)
            self.assertEqual(len(report['errors']), 1)  # Native sample intentionally absent.

    @unittest.skipIf(sys.platform == 'win32', 'POSIX executable fixture; real Windows retoc remains a live check.')
    def test_player_reference_extracts_only_scoped_assets_and_leaves_installations_untouched(self):
        stems = ['Movies/Sequencer/' + n for n in (
            'BP_BtlSequencerMovieActor', 'MP_BtlManaPlayer',
            'MSB_BtlSequencer_Texture', 'MSB_BtlSequencer_Texture_Mat')]
        stems += ['Sequencer/Battle/Skill/440110/440111/SEQ_Battle_440111_Master',
                  'Sequencer/Battle/Skill/440110/440111/Track/SEQ_Battle_440111_Cut_000']
        fixture = self.root / 'native-fixture'
        for stem in stems:
            self.write(fixture / ('FFRS/Content/' + stem + '.uasset'), stem.encode())
        self.write(fixture / 'FFRS/Content/Unrelated/private.uasset', b'private')
        self.write(self.engine / 'extracted/Mappings.usmap', b'mappings fixture')
        tool = self.engine / 'tools/retoc/retoc.exe'
        self.write(tool, (f'#!{sys.executable}\n'
            'import pathlib, shutil, sys\n'
            'a=sys.argv[1:]\n'
            'assert a[:3]==["to-legacy","--no-shaders","--filter"]\n'
            'assert a[3] in ("Movies/Sequencer/","Sequencer/Battle/Skill/440110/440111/")\n'
            'assert pathlib.Path(a[4]).name=="Paks"\n'
            f'source=pathlib.Path({str(fixture)!r})\n'
            'for p in (source/"FFRS/Content"/a[3]).rglob("*"):\n'
            ' if p.is_file():\n'
            '  out=pathlib.Path(a[5])/p.relative_to(source)\n'
            '  out.parent.mkdir(parents=True,exist_ok=True)\n'
            '  shutil.copyfile(p,out)\n'
            'print("info: : Extracted assets (0 failed)")\n').encode())
        tool.chmod(0o755)
        before = self.digest(self.game), self.digest(self.engine)
        self.run_helper(player=True)
        self.assertEqual(before, (self.digest(self.game), self.digest(self.engine)))
        with self.archive() as z:
            report = json.loads(z.read('report.json').decode('utf-8-sig'))
            self.assertEqual(report['purpose'], 'native-movie-player')
            self.assertEqual(report['errors'], [])
            self.assertEqual(len(report['extraction']), 2)
            self.assertTrue(all(x['timeoutSeconds'] == 60 for x in report['extraction']))
            self.assertEqual(len(report['files']), len(stems))
            self.assertEqual(z.read('native/Mappings.usmap'), b'mappings fixture')
            for stem in stems:
                self.assertEqual(z.read('native/legacy/FFRS/Content/' + stem + '.uasset'), stem.encode())
            self.assertFalse(any('private' in n or n.endswith(('.usm', '.sav', '.pak', '.ini')) for n in z.namelist()))

    @unittest.skipIf(sys.platform == 'win32', 'POSIX executable fixture; real Windows retoc remains a live check.')
    def test_player_reference_reports_failed_assets_even_when_reader_exits_zero(self):
        tool = self.engine / 'tools/retoc/retoc.exe'
        self.write(tool, (f'#!{sys.executable}\nprint("info: : Extracted 0 (3 failed)")\n').encode())
        tool.chmod(0o755)
        self.run_helper(player=True)
        with self.archive() as z:
            report = json.loads(z.read('report.json').decode('utf-8-sig'))
            self.assertEqual(len(report['errors']), 8)  # Two failed filters and six absent required assets.
            self.assertEqual(report['files'], [])
            self.assertTrue(all(x['exitCode'] == 0 for x in report['extraction']))

    def test_rejects_output_in_game_or_engine_before_writing(self):
        for folder in (self.game, self.engine):
            self.output = folder / 'do-not-create'
            self.run_helper(success=False)
            self.assertFalse(self.output.exists())


if __name__ == '__main__':
    unittest.main()
