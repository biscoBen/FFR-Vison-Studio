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
      expect(state['version'], '1.2.1');
      for (final name in [
        '_ffr_existingvisions.py',
        '_ffr_party.py',
        '_ffr_party_voices.py',
        'party_voice_cues.json',
        '_ffr_overworld.py',
        '_ffr_field_leader.py',
        'field_leader.lua',
        'vagrant_knight_rain_field.png',
        'overworld_catalog.json',
        'overworld_assets.zip',
        '_ffr_testing.py',
        '_ffr_crystal_cave.py',
        '_ffr_ability_modes.py',
        'ability_hiding_review.json',
        '_ffr_animation_repair.py',
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
import _ffr_party, _ffr_party_voices, _ffr_overworld
from PIL import Image
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
    timeout: const Timeout(Duration(minutes: 3)),
  );
}
