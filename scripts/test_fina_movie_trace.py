"""Read-only movie observer, owned installer and exact standalone download."""
import ctypes
import ctypes.util
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
FOLDER = ROOT / 'scripts/reference/crystal-fina-battle'
NAMES = ['Install Movie Trace.cmd', 'Collect Movie Trace.cmd', 'Disable Movie Trace.cmd',
         'Movie Playback Trace.ps1', 'movie_trace.lua', 'Collect Fina Movie Diagnostics.ps1', 'Movie Trace README.txt']
PWSH = shutil.which('pwsh')


class TraceDownloadTests(unittest.TestCase):
    def test_download_has_exact_sources(self):
        with zipfile.ZipFile(FOLDER / 'Crystal-Fina-Movie-Trace.zip') as z:
            self.assertEqual(z.namelist(), NAMES)
            self.assertIsNone(z.testzip())
            for name in NAMES:
                self.assertEqual(z.read(name).decode().replace('\r\n', '\n'), (FOLDER/name).read_text())


@unittest.skipUnless(PWSH, 'PowerShell required')
class TraceInstallerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.game = Path(self.temp.name) / "Game & user's folder"
        self.mods = self.game/'FFRS/Binaries/Win64/ue4ss/Mods'
        self.mods.mkdir(parents=True)
        self.foreign = self.mods/'OtherMod'; self.foreign.mkdir()
        (self.foreign/'enabled.txt').write_bytes(b'unchanged')
        self.trace = self.mods/'FFRStudioMovieTrace'
        self.env = dict(os.environ, XDG_CACHE_HOME=str(Path(self.temp.name)/'cache'),
                        XDG_CONFIG_HOME=str(Path(self.temp.name)/'config'),
                        XDG_DATA_HOME=str(Path(self.temp.name)/'data'))

    def run_action(self, action, success=True):
        r = subprocess.run([PWSH, '-NoLogo', '-NoProfile', '-File', str(FOLDER/'Movie Playback Trace.ps1'),
                            '-Action', action, '-GamePath', str(self.game), '-NoPrompt'],
                           capture_output=True, text=True, timeout=15, env=self.env)
        self.assertEqual(r.returncode, 0 if success else 1, r.stdout+r.stderr)

    def test_install_and_disable_touch_only_the_owned_trace(self):
        self.run_action('Install')
        self.assertEqual((self.trace/'Scripts/main.lua').read_bytes(), (FOLDER/'movie_trace.lua').read_bytes())
        self.assertTrue((self.trace/'enabled.txt').is_file())
        self.run_action('Disable')
        self.assertFalse((self.trace/'enabled.txt').exists())
        self.assertEqual((self.foreign/'enabled.txt').read_bytes(), b'unchanged')
        self.run_action('Install')
        self.assertTrue((self.trace/'enabled.txt').is_file())

    def test_unknown_same_named_folder_is_never_overwritten_or_disabled(self):
        self.trace.mkdir(); (self.trace/'enabled.txt').write_bytes(b'foreign')
        for action in ('Install', 'Disable'):
            self.run_action(action, success=False)
            self.assertEqual((self.trace/'enabled.txt').read_bytes(), b'foreign')
            self.assertEqual(list(self.trace.iterdir()), [self.trace/'enabled.txt'])


@unittest.skipUnless(ctypes.util.find_library('lua5.4'), 'Lua 5.4 shared library required')
class TraceRuntimeTests(unittest.TestCase):
    def test_observes_progress_and_display_without_writing_native_state(self):
        lib = ctypes.CDLL(ctypes.util.find_library('lua5.4'))
        lib.luaL_newstate.restype = ctypes.c_void_p
        lib.luaL_openlibs.argtypes = [ctypes.c_void_p]
        lib.luaL_loadstring.argtypes = [ctypes.c_void_p, ctypes.c_char_p]
        lib.lua_pcallk.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_int, ctypes.c_int,
                                 ctypes.c_ssize_t, ctypes.c_void_p]
        lib.lua_tolstring.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.POINTER(ctypes.c_size_t)]
        lib.lua_tolstring.restype = ctypes.c_char_p
        lib.lua_close.argtypes = [ctypes.c_void_p]
        state = lib.luaL_newstate(); self.addCleanup(lambda: lib.lua_close(state)); lib.luaL_openlibs(state)
        def execute(source):
            status = lib.luaL_loadstring(state, source.encode())
            if status == 0: status = lib.lua_pcallk(state, 0, 0, 0, 0, None)
            if status: self.fail(lib.lua_tolstring(state, -1, None).decode())
        execute('''
            messages={}; inThread=false; statusReads=0; frame=30
            function print(s) messages[#messages+1]=s end
            function object(label, fields)
                fields=fields or {}
                fields.IsValid=function() assert(inThread); return true end
                fields.GetFullName=function() assert(inThread); return label end
                return setmetatable({}, {__index=fields,__newindex=function() error('Native state write') end})
            end
            movie=object('PlatformManaMovie CrystalFina_Test')
            component=object('ManaComponent Runtime', {Movie=movie,AlphaTrack=0,
                GetFrameNumber=function() assert(inThread); return frame end})
            player=object('ManaPlayer MP_BtlManaPlayer', {ManaComponent=component,ManaMovie=movie,
                GetStatus=function() assert(inThread); statusReads=statusReads+1; return 5 end})
            empty=object('ManaPlayer Uninitialized', {GetStatus=function() error('Unsafe uninitialized getter') end})
            managerFields={bUseMovie=true}
            manager=object('CPP_UI_BtlCinematicManager Runtime',managerFields)
            function FindAllOf(class)
                assert(inThread)
                if class=='ManaPlayer' then return {player,empty} end
                if class=='CPP_UI_BtlCinematicManager' then return {manager} end
                if class=='BP_BtlSequencerMovieActor_C' then return {object('MovieActor Runtime')} end
                error('Unexpected class')
            end
            function LoopInGameThreadWithDelay(delay,fn) assert(delay==250); tick=fn end
            function ExecuteInGameThread(fn) inThread=true; fn(); inThread=false end
            Key={F8=119}
            function RegisterKeyBind(key,fn) assert(key==119); bookmark=fn end
            function run() inThread=true; assert(tick()==false); inThread=false end
        ''')
        execute((FOLDER/'movie_trace.lua').read_text())
        execute('''
            run(); assert(statusReads==1)
            local first=#messages; run(); assert(#messages==first)
            assert(not table.concat(messages):find('Unsafe uninitialized'))
            assert(table.concat(messages):find('bUseMovie=true'))
            assert(table.concat(messages):find('movieActors=1'))
            assert(table.concat(messages):find('frameBucket=2'))
            frame=45; run(); assert(table.concat(messages):find('frameBucket=3'))
            managerFields.bUseMovie=false; run(); assert(table.concat(messages):find('bUseMovie=false'))
            bookmark(); assert(table.concat(messages):find('F8 bookmark'))
            for i=1,1600 do bookmark() end
            assert(#messages==1500)
        ''')
