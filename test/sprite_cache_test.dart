import 'dart:convert';
import 'dart:io';

import 'package:archive/archive.dart';
import 'package:crypto/crypto.dart';
import 'package:ffr_vision_studio/services/api.dart';
import 'package:ffr_vision_studio/services/paths.dart';
import 'package:ffr_vision_studio/state/app_state.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:path/path.dart' as p;

class SpriteApi extends Api {
  SpriteApi(this.paths) : super('http://unused');
  final AppPaths paths;
  final requests = <String>[];
  final prepared = <String>{};
  final failures = <String>{};
  var legacy = false;
  var failRebuild = false;
  var needsGameData = false;
  var rebuilds = 0;

  @override
  Future<void> rebuildFfbeIndex() async {
    rebuilds++;
    if (failRebuild) {
      throw ApiException('Character index unavailable');
    }
  }

  @override
  Future<JsonMap> prepareAssets(String ffbeId, String form) async {
    if (needsGameData) {
      throw ApiException('Prepare the game data first', statusCode: 422);
    }
    if (legacy) {
      throw ApiException('Old engine', statusCode: 404);
    }
    requests.add('$ffbeId:$form');
    expect(
      File(p.join(paths.engineSprites, form, 'unit_anime_$form.png'))
          .existsSync(),
      isTrue,
    );
    expect(
      File(p.join(paths.engineSprites, form, 'unit_cgg_$form.csv'))
          .existsSync(),
      isTrue,
    );
    return {'job': form};
  }

  @override
  Future<JsonMap> assetProgress(String job) async {
    if (failures.contains(job)) {
      return {'state': 'failed', 'error': 'Unit data unavailable'};
    }
    prepared.add(job);
    return {'state': 'done'};
  }

  @override
  Future<List<String>> anims(String form) async =>
      prepared.contains(form) ? ['idle', 'atk'] : [];
  @override
  Future<void> setup(String game) async {
    needsGameData = false;
  }

  @override
  Future<JsonMap> setupLog() async => {
    'running': false,
    'result': 'ok',
    'log': <String>[],
  };
  @override
  Future<JsonMap> catalog() async => {};
  @override
  Future<List<dynamic>> spec() async => [];
  @override
  Future<List<dynamic>> nativeVisions() async => [];
  @override
  Future<JsonMap> status() async => {'setupNeeded': false};
  @override
  Future<void> saveSpec(List<dynamic> units) async =>
      throw StateError('Startup must not save the roster.');
  @override
  Future<JsonMap> addUnit(String ffbeId, {String? form, String? name}) async =>
      throw StateError('Startup must not add a unit.');
}

void main() {
  late Directory temporary;
  late HttpServer server;
  late AppPaths paths;
  late AppState app;
  late SpriteApi api;
  late Map<String, List<int>> archives;
  late List<String> downloads;
  late Set<String> unavailable;

  List<int> spriteZip(String form) {
    final archive = Archive();
    for (final name in [
      'unit_anime_$form.png',
      'unit_cgg_$form.csv',
      'unit_icon_$form.png',
      'unit_idle_cgs_$form.csv',
      'unit_atk_cgs_$form.csv',
    ]) {
      final bytes = utf8.encode('fixture $name');
      archive.addFile(ArchiveFile(name, bytes.length, bytes));
    }
    archive.addFile(ArchiveFile('optional-empty.txt', 0, <int>[]));
    return ZipEncoder().encode(archive);
  }

  File sprite(String form, String name) =>
      File(p.join(paths.engineSprites, form, name));

  setUp(() async {
    temporary = Directory.systemTemp.createTempSync('sprite-cache-');
    paths = AppPaths.at(temporary.path);
    downloads = [];
    unavailable = {};
    archives = {
      for (final form in ['101', '102', '201']) form: spriteZip(form),
    };
    server = await HttpServer.bind(InternetAddress.loopbackIPv4, 0);
    server.listen((request) async {
      final form = p.basenameWithoutExtension(request.uri.path);
      downloads.add(form);
      if (unavailable.contains(form)) {
        request.response.statusCode = HttpStatus.forbidden;
      } else {
        request.response.add(archives[form]!);
      }
      await request.response.close();
    });
    api = SpriteApi(paths);
    app = AppState(hostBase: 'http://127.0.0.1:${server.port}', appPaths: paths)
      ..api = api;
    app.hostIndex = {
      'units': [
        {
          'id': '10',
          'packs': ['101', '102'],
        },
        {
          'id': '20',
          'packs': ['201'],
        },
        {
          'id': 'duplicate',
          'packs': ['101'],
        },
        {'id': 'no-pack', 'packs': []},
      ],
      'forms': {
        for (final entry in archives.entries)
          entry.key: {
            'url': '${app.hostBase}/${entry.key}.zip',
            'sha256': sha256.convert(entry.value).toString(),
          },
      },
    };
    app.units = [
      {
        'key': 'saved-unit',
        'en': 'Keep my edits',
        'stats': {'Attack': 999},
      },
    ];
  });
  tearDown(() async {
    app.dispose();
    await server.close(force: true);
    temporary.deleteSync(recursive: true);
  });

  test('game setup leaves every hosted sprite pack on demand', () async {
    app.phase = Phase.setup;
    api.needsGameData = true;
    await app.runSetup('fixture game');
    expect(app.phase, Phase.ready);
    expect(downloads, isEmpty);
    expect(api.requests, isEmpty);
    expect(
      app.bootSteps.map((s) => s.label),
      isNot(contains('Download missing character sprites')),
    );
  });

  test('only the requested form is downloaded and indexed', () async {
    await app.ensureSprites('101');
    await app.prepareUnitPreview('10', '101');
    expect(downloads, ['101']);
    expect(api.requests, ['10:101']);
    expect(await app.animsFor('101'), ['idle', 'atk']);
    expect(sprite('102', 'unit_anime_102.png').existsSync(), isFalse);
  });

  test('complete packs are reused across Studio instances', () async {
    await app.ensureSprites('101');
    downloads.clear();
    final next = AppState(hostBase: app.hostBase, appPaths: paths)
      ..api = api
      ..hostIndex = app.hostIndex;
    addTearDown(next.dispose);
    await next.ensureSprites('101');
    expect(downloads, isEmpty);
    expect(api.rebuilds, 1);
  });

  test(
    'missing motion files reuse the verified ZIP and retain edited artwork',
    () async {
      await app.ensureSprites('101');
      downloads.clear();
      sprite('101', 'unit_idle_cgs_101.csv').deleteSync();
      sprite(
        '101',
        'unit_anime_101.png',
      ).writeAsStringSync('my edited artwork');
      await app.ensureSprites('101');
      expect(downloads, isEmpty);
      expect(
        sprite('101', 'unit_idle_cgs_101.csv').readAsStringSync(),
        'fixture unit_idle_cgs_101.csv',
      );
      expect(
        sprite('101', 'unit_anime_101.png').readAsStringSync(),
        'my edited artwork',
      );
    },
  );

  test(
    'an orphan completion marker does not hide a missing requested pack',
    () async {
      final marker = sprite('101', '.complete');
      marker.parent.createSync(recursive: true);
      marker.writeAsStringSync('interrupted');
      await app.ensureSprites('101');
      expect(downloads, ['101']);
      expect(sprite('101', 'unit_icon_101.png').existsSync(), isTrue);
    },
  );

  test(
    'a deleted sheet and ZIP download just the requested form again',
    () async {
      await app.ensureSprites('102');
      downloads.clear();
      sprite('102', 'unit_anime_102.png').deleteSync();
      File(p.join(paths.downloads, '102.zip')).deleteSync();
      await app.ensureSprites('102');
      expect(downloads, ['102']);
      expect(sprite('102', 'unit_anime_102.png').existsSync(), isTrue);
    },
  );

  test(
    'checksum failures do not become trusted packs and retry on demand',
    () async {
      final correct = archives['101']!;
      archives['101'] = utf8.encode('damaged download');
      await expectLater(
        app.ensureSprites('101'),
        throwsA(predicate((e) => e.toString().contains('checksum mismatch'))),
      );
      expect(sprite('101', '.studio-sprites.json').existsSync(), isFalse);
      archives['101'] = correct;
      downloads.clear();
      await app.ensureSprites('101');
      expect(downloads, ['101']);
    },
  );

  test('failed index refresh retries the cached requested pack without another download', () async {
    api.failRebuild = true;
    await expectLater(app.ensureSprites('101'), throwsA(isA<ApiException>()));
    expect(sprite('101', '.studio-preview-ready').existsSync(), isFalse);
    api.failRebuild = false;
    downloads.clear();
    await app.ensureSprites('101');
    expect(downloads, isEmpty);
    expect(api.rebuilds, 2);
  });

  test('legacy engines keep on-demand cached sprite preparation', () async {
    api.legacy = true;
    await app.prepareUnitPreview('10', '101');
    expect(downloads, ['101']);
    expect(api.rebuilds, 1);
    expect(sprite('102', 'unit_anime_102.png').existsSync(), isFalse);
  });
}
