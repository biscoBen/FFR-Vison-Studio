import 'dart:convert';
import 'dart:io';
import 'dart:typed_data';

import 'package:crypto/crypto.dart';
import 'package:ffr_vision_studio/services/ffbe_animation_library.dart';
import 'package:ffr_vision_studio/services/paths.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:path/path.dart' as p;

void main() {
  late Directory temporary;
  late AppPaths paths;
  late Map<String, Uint8List> assets;
  late List<String> reads;
  final pack = Uint8List.fromList(utf8.encode('verified source pack'));
  const service = FfbeAnimationLibrary.assetRoot;

  setUp(() {
    temporary = Directory.systemTemp.createTempSync('ffbe-library-');
    paths = AppPaths.at(temporary.path);
    reads = [];
    assets = {
      '$service/library-01.zip': pack,
      '$service/manifest.json': Uint8List.fromList(
        utf8.encode(
          json.encode({
            'schema': 1,
            'revision': FfbeAnimationLibrary.revision,
            'packs': [
              {
                'name': 'library-01.zip',
                'bytes': pack.length,
                'sha256': sha256.convert(pack).toString(),
              },
            ],
          }),
        ),
      ),
    };
    addTearDown(() => temporary.deleteSync(recursive: true));
  });

  Future<Uint8List> read(String name) async {
    reads.add(name);
    return assets[name]!;
  }

  File installed(String name) => File(
    p.join(
      paths.engineDir,
      'library',
      'ffbe',
      FfbeAnimationLibrary.revision,
      name,
    ),
  );

  test(
    'stages verified packs offline, reuses them and preserves the roster',
    () async {
      final roster = File(
        p.join(paths.engineDir, 'mods', 'EstherTsukiko', 'units.json'),
      );
      roster.parent.createSync(recursive: true);
      roster.writeAsStringSync('private edited roster');
      final library = FfbeAnimationLibrary();
      await library.prepare(paths, readAsset: read);
      expect(installed('library-01.zip').readAsBytesSync(), pack);
      expect(
        File(p.join(paths.engineDir, 'library', 'ffbe', 'manifest.json'))
            .existsSync(),
        isTrue,
      );
      reads.clear();
      await library.prepare(paths, readAsset: read);
      expect(reads, ['$service/manifest.json']);
      installed('library-01.zip').writeAsBytesSync(List.filled(pack.length, 0));
      await library.prepare(paths, readAsset: read);
      expect(installed('library-01.zip').readAsBytesSync(), pack);
      expect(roster.readAsStringSync(), 'private edited roster');
    },
  );

  test('rejects corrupt assets without publishing a manifest', () async {
    assets['$service/library-01.zip'] = Uint8List.fromList([1, 2, 3]);
    await expectLater(
      FfbeAnimationLibrary().prepare(paths, readAsset: read),
      throwsStateError,
    );
    expect(installed('library-01.zip').existsSync(), isFalse);
    expect(
      File(p.join(paths.engineDir, 'library', 'ffbe', 'manifest.json'))
          .existsSync(),
      isFalse,
    );
  });

  test(
    'rejects unexpected pack paths before reading or writing packs',
    () async {
      final manifest =
          json.decode(utf8.decode(assets['$service/manifest.json']!)) as Map;
      manifest['packs'][0]['name'] = '../../units.json';
      assets['$service/manifest.json'] = Uint8List.fromList(
        utf8.encode(json.encode(manifest)),
      );
      await expectLater(
        FfbeAnimationLibrary().prepare(paths, readAsset: read),
        throwsStateError,
      );
      expect(reads, ['$service/manifest.json']);
    },
  );
}
