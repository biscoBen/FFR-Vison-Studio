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
      expect(state['version'], '1.2.0');
      for (final name in [
        '_ffr_existingvisions.py',
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
    },
    skip: !Platform.isWindows || fixture == null,
    timeout: const Timeout(Duration(minutes: 3)),
  );
}
