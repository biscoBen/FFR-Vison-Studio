import 'dart:convert';
import 'dart:io';

import 'package:ffr_vision_studio/services/bundled_features.dart';
import 'package:ffr_vision_studio/services/paths.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:path/path.dart' as p;

void main() {
  final fixture = Platform.environment['FFR_STUDIO_ENGINE_FIXTURE'];
  test(
    'fresh Windows engine installs all bundled features in a long portable path',
    () async {
      final temporary = Directory.systemTemp.createTempSync('ffr-boot-');
      addTearDown(() => temporary.deleteSync(recursive: true));
      final paths = AppPaths.at(
        p.join(temporary.path, 'Windows Downloads ').padRight(120, 'x'),
      );
      final source = Directory(fixture!);
      for (final file in source.listSync(recursive: true).whereType<File>()) {
        final destination = File(
          p.join(paths.engineDir, p.relative(file.path, from: source.path)),
        );
        destination.parent.createSync(recursive: true);
        file.copySync(destination.path);
      }
      final features = BundledFeatures(
        readAsset: (path) => File(path).readAsBytes(),
      );
      final roster = File(
        p.join(paths.engineDir, 'mods', 'EstherTsukiko', 'units.json'),
      );
      expect(roster.existsSync(), isFalse);
      await features.prepareEngine(paths, engineRunning: false);
      expect(roster.existsSync(), isFalse);
      // A valid edited vision fixture checks that a subsequent start preserves
      // saved user configuration without requiring an installed game.
      final savedVision = json.decode(
        File('assets/crystal_fina/profile.json').readAsStringSync(),
      ) as Map;
      savedVision['stats']['Attack'] = 789;
      roster.parent.createSync(recursive: true);
      roster.writeAsStringSync(json.encode([savedVision]));
      final before = roster.readAsBytesSync();
      final material = File(
        p.join(
          paths.engineDir,
          '.ffr-crystalfina/material/FFRS/Content/BP/Map/Unit/Material/'
          'M_CrystalFina_AlphaTest_13503.uasset',
        ),
      );
      expect(
        material.readAsBytesSync(),
        File(
          'assets/crystal_fina/engine/payload/material/FFRS/Content/BP/Map/'
          'Unit/Material/M_CrystalFina_AlphaTest_13503.uasset',
        ).readAsBytesSync(),
      );
      material.deleteSync();
      await features.prepareEngine(paths, engineRunning: false);
      expect(material.existsSync(), isTrue);
      expect(roster.readAsBytesSync(), before);
      final state = json.decode(
        File(p.join(paths.engineDir, '.ffr-existing-visions/state.json'))
            .readAsStringSync(),
      ) as Map;
      expect(state['version'], '1.2.87');
      for (final name in [
        '_ffr_existingvisions.py',
        '_ffr_build_progress.py',
        '_ffr_build_cache.py',
        '_ffr_ffbe_library.py',
        '_ffr_ffbe_download.py',
        'ffbe_library_manifest.json',
        'ffbe_library_browser.zip',
        '_ffr_ffbe_renderer.py',
        '_ffr_ffbe_texture.py',
        '_ffr_ffbe_placement.py',
        '_ffr_ffbe_uv.py',
        'ffbe_library.html',
        '_ffr_ffbe_needles.py',
        'ffbe_needles.zip',
        '_ffr_fina_cinematic.py',
        '_ffr_fina_cave_music.py',
        '_ffr_movie_audio.py',
        '_ffr_cave_music_preview.py',
        'cave_music_preview.zip',
        'fina_cinematic.zip',
        '_ffr_deck_sync.py',
        '_ffr_party.py',
        '_ffr_party_voices.py',
        '_ffr_native_voices.py',
        'native_voice_codec.ps1',
        'party_voice_cues.json',
        '_ffr_overworld.py',
        '_ffr_field_leader.py',
        'field_leader.lua',
        'vagrant_knight_rain_field.png',
        'overworld_catalog.json',
        'overworld_assets.zip',
        '_ffr_testing.py',
        '_ffr_crystal_cave.py',
        '_ffr_fina_battle.py',
        'fina_battle.lua',
        '_ffr_fina_preview.py',
        'fina_battle_preview.zip',
        '_ffr_fina_motion.py',
        '_ffr_ability_modes.py',
        'ability_hiding_review.json',
        '_ffr_animation_repair.py',
        '_ffr_native_skills.py',
        'native_skill_repairs.json',
        '_ffr_build_icons.py',
        'ability_live_tests.json',
        '_ffr_build_sprites.py',
        '_ffr_library.py',
        'ffbe_animation_index.json',
        'ffbe_barrage_index.json',
      ]) {
        expect(
          File(p.join(paths.engineDir, 'tools', name)).readAsBytesSync(),
          File('assets/existing_visions/payload/$name').readAsBytesSync(),
        );
      }
      final fieldCheck = File(
        p.join(paths.engineDir, 'check_overworld_startup.py'),
      );
      fieldCheck.writeAsStringSync('''
import sys, io
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / 'tools'))
import _ffr_party, _ffr_party_voices, _ffr_native_voices, _ffr_overworld, _ffr_deck_sync
from fastapi import FastAPI
root = Path(__file__).parent
assert _ffr_deck_sync.settings(root)['enabled'] is False
vault = _ffr_deck_sync.CredentialStore(root)
try:
    vault.put('tester/frozen-fixture', 'github_pat_' + 'A' * 25)
    assert vault.get('tester/frozen-fixture') == 'github_pat_' + 'A' * 25
finally:
    vault.delete('tester/frozen-fixture')
assert vault.get('tester/frozen-fixture') is None
app = FastAPI()
_ffr_deck_sync.register(app, {'ROOT': str(root)})
status = next(r for r in app.routes if r.path == '/api/deck/status').endpoint()
assert status['enabled'] is False and status['repository'] == '' and status['hasToken'] is False
from PIL import Image
import _ffr_fina_preview
import struct, _ffr_cave_music_preview, _ffr_movie_audio
# These helpers run inside the real frozen engine, which does not bundle wave
# or developer-only WannaCRI. Exercise real PCM trimming and CRI metadata.
pcm = bytes(48000 * 4 * 8)
fmt = struct.pack('<HHIIHH',1,2,48000,192000,4,16)
wav = b'RIFF'+struct.pack('<I',36+len(pcm))+b'WAVEfmt '+struct.pack('<I',16)+fmt+b'data'+struct.pack('<I',len(pcm))+pcm
short = _ffr_cave_music_preview.trim_wave(wav)
assert len(short)==44+307200*4
metadata = _ffr_movie_audio._write_utf('frozen',[('samples',5)],[{'samples':307200}])
assert _ffr_movie_audio._read_utf(metadata)[2]==[{'samples':307200}]
preview_app = FastAPI()
_ffr_fina_preview.register(preview_app, {'ROOT': str(root)})
native_route = next(r for r in preview_app.routes if r.path == '/api/ffbe/anim/99887755552703/{anim}.webp')
native_preview = native_route.endpoint('idle')
assert native_preview.headers['x-fina-presentation'] == 'native-fina-10'
assert native_preview.headers['cache-control'] == 'no-store'
with Image.open(io.BytesIO(native_preview.body)) as image:
    assert image.size == (280, 360) and image.n_frames > 2
    image.seek(0)
    image.load()
_ffr_party.validate({'key':'party_1001', 'id':1001, 'jp':'レイン', 'en':'Rain',
    'party':{'version':1, 'id':1001}, 'overworld':{'version':1, 'model':'vagrant_knight_rain'}})
assert 'idle9' in [a['name'] for a in _ffr_overworld.spec('pc0010')['animations']]
with Image.open(Path(_ffr_overworld.__file__).with_name(_ffr_overworld.SHEET)) as image:
    assert image.size == (448,1536)
assert len(_ffr_overworld.catalog()['models']) == 9
for speaker, _, _, _ in _ffr_party.CHARACTERS:
    cues = _ffr_party_voices.profile(speaker)
    assert cues['attack']['name'] == 'VO_BTL_ATK_01_' + _ffr_party.voice_label(speaker)
    assert all(cues[phase]['duration'] > 0 for phase in ('opening', 'release', 'finish'))
for model, entry in _ffr_overworld.catalog()['models'].items():
    choice = {'version':1, 'model':model}
    _ffr_overworld.validate(choice)
    assert len(_ffr_overworld.spec('pc0010', choice)['animations']) == 52
    with Image.open(io.BytesIO(_ffr_overworld.asset_bytes(entry, 'sheet'))) as image:
        assert list(image.size) == entry['size']
    with Image.open(io.BytesIO(_ffr_overworld.asset_bytes(entry, 'icon'))) as image:
        assert image.width > 0
import gzip, json
import _ffr_ffbe_library, _ffr_ffbe_download
assert not (root/'library/ffbe/manifest.json').exists()
requests=[]
class LocalResponse:
    status=200
    headers={}
    def __init__(self,path):self.stream=path.open('rb')
    def __enter__(self):return self
    def __exit__(self,*args):self.stream.close()
    def read(self,n):return self.stream.read(n)
pack_source=Path(${json.encode(Directory('assets/ffbe_library').absolute.path)})
def offline_transport(request,**kwargs):
    requests.append(request.full_url)
    return LocalResponse(pack_source/request.full_url.rsplit('/',1)[1])
installation=_ffr_ffbe_download.Installation(root,opener=offline_transport)
assert installation.status()['ready'] is False and requests == []
installation.start()
installation.thread.join(120)
assert installation.status()['ready'],installation.status()
assert len(requests)==56
library_app = FastAPI()
_ffr_ffbe_library.register(library_app, {'ROOT': str(root)})
route = {r.path:r.endpoint for r in library_app.routes if hasattr(r, 'endpoint')}
summary = route['/api/ffbe-library/catalog'](q='1,000 Needles')
assert summary['summary']['skills'] == 65428 and summary['total'] > 0
assert all('sourceLabel' in r for r in summary['items'])
owners = route['/api/ffbe-library/sources']()['items']
assert any(s['key']=='character:Agrias' for s in owners)
agrias = route['/api/ffbe-library/catalog'](source='character:Agrias',animated=False)
assert agrias['total'] > 0 and all(r['sourceLabel']=='Agrias' for r in agrias['items'])
own = agrias['items'][0]
assert route['/api/ffbe-library/entry/{kind}/{identity}'](own['kind'],own['id'],source='character:Agrias')['entry']['sourceLabel']=='Agrias'
library = _ffr_ffbe_library.Library(root)
effect = json.loads(gzip.decompress(library.simulation('1002460')))
assert effect['warnings'] == [] and len(effect['textures']) == 3
assert any(len({tuple(p['pos']) for p in frame}) >= 4 for frame in effect['frames'])
sprite = next(e for e in library.document('effects.json').values() if e['type'] == '1' and all('raw/' + n in library.files for n in e['file'].split(':')))
assert library.sprite_simulation(sprite)['frames']
audio = library.document('audio.json')
wave = next(iter(audio['waves'].values()))
assert route['/api/ffbe-library/file/{name:path}']('audio/' + wave['file']).body[:4] == b'fLaC'
movies = library.document('movies.json')
assert len(movies) == 90
movie = next(iter(movies.values()))
assert route['/api/ffbe-library/file/{name:path}']('movies/' + movie['file']).body[:4] == bytes.fromhex('1a45dfa3')
print('FFBE library, source particles, sound and cinematic ready')
print('Overworld module and field sheet ready')
''');
      final fieldResult = await Process.run(paths.engineExe, [
        '--run',
        fieldCheck.path,
      ], workingDirectory: paths.engineDir);
      expect(
        fieldResult.exitCode,
        0,
        reason: '${fieldResult.stdout}\n${fieldResult.stderr}',
      );
      expect(
        fieldResult.stdout.toString(),
        contains('Overworld module and field sheet ready'),
      );
    },
    skip: !Platform.isWindows || fixture == null,
    timeout: const Timeout(Duration(minutes: 6)),
  );
}
