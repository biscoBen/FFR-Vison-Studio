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
    temporary = Directory.systemTemp.createTempSync('sprite-startup-');
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

  test('startup prepares every hosted look without selecting or adding a character', () async {
    expect(await app.animsFor('101'), isEmpty);
    final roster = json.encode(app.units);
    await app.prepareStartupSprites();
    expect(downloads, ['101', '102', '201']);
    expect(api.requests, ['10:101', '10:102', '20:201']);
    expect(await app.animsFor('101'), ['idle', 'atk']);
    expect(json.encode(app.units), roster);
    expect(app.dirty, isFalse);
    expect(app.spriteWarning, isNull);
    expect(app.bootSteps.last.state, 'done');
    expect(app.bootSteps.last.detail, '3/3 forms ready');
  });

  test('subsequent launches use complete local packs without downloads or preparation jobs', () async {
    await app.prepareStartupSprites();
    downloads.clear();
    api.requests.clear();
    // A new AppState exercises persistent files, rather than an in-memory flag.
    final next = AppState(hostBase: app.hostBase, appPaths: paths)
      ..api = api
      ..hostIndex = app.hostIndex;
    addTearDown(next.dispose);
    await next.prepareStartupSprites();
    expect(downloads, isEmpty);
    expect(api.requests, isEmpty);
    expect(next.spriteWarning, isNull);
  });

  test('missing animations are restored from the verified ZIP despite .complete; artwork is retained', () async {
    await app.prepareStartupSprites();
    downloads.clear();
    api.requests.clear();
    sprite('101', 'unit_idle_cgs_101.csv').deleteSync();
    sprite('101', 'unit_anime_101.png').writeAsStringSync('my edited artwork');
    expect(sprite('101', '.complete').existsSync(), isTrue);
    await app.prepareStartupSprites();
    expect(downloads, isEmpty);
    expect(api.requests, ['10:101']);
    expect(
      sprite('101', 'unit_idle_cgs_101.csv').readAsStringSync(),
      'fixture unit_idle_cgs_101.csv',
    );
    expect(
      sprite('101', 'unit_anime_101.png').readAsStringSync(),
      'my edited artwork',
    );
  });

  test('a missing sheet and missing ZIP trigger just the affected form download on the next launch', () async {
    await app.prepareStartupSprites();
    downloads.clear();
    api.requests.clear();
    sprite('102', 'unit_anime_102.png').deleteSync();
    File(p.join(paths.downloads, '102.zip')).deleteSync();
    await app.prepareStartupSprites();
    expect(downloads, ['102']);
    expect(api.requests, ['10:102']);
    expect(sprite('102', 'unit_anime_102.png').existsSync(), isTrue);
  });

  test('an orphan completion marker never hides a missing pack', () async {
    final marker = sprite('101', '.complete');
    marker.parent.createSync(recursive: true);
    marker.writeAsStringSync('old interrupted download');
    await app.prepareStartupSprites();
    expect(downloads, contains('101'));
    expect(sprite('101', 'unit_icon_101.png').existsSync(), isTrue);
  });

  test('a failed form is reported without blocking other forms and retried on the next launch', () async {
    unavailable.add('101');
    await app.prepareStartupSprites();
    expect(api.requests, ['10:102', '20:201']);
    expect(app.spriteWarning, contains('1 character form'));
    expect(app.spriteWarning, contains('HTTP 403'));
    expect(app.bootSteps.last.state, 'done');
    expect(sprite('101', '.studio-preview-ready').existsSync(), isFalse);
    expect(
      File(p.join(app.logsDir, 'sprite-startup.log')).readAsStringSync(),
      contains('HTTP 403'),
    );
    unavailable.clear();
    downloads.clear();
    api.requests.clear();
    await app.prepareStartupSprites();
    expect(downloads, ['101']);
    expect(api.requests, ['10:101']);
    expect(app.spriteWarning, isNull);
  });

  test('failed unit-data preparation retries even when the sprite files were downloaded', () async {
    api.failures.add('102');
    await app.prepareStartupSprites();
    expect(app.spriteWarning, contains('Unit data unavailable'));
    expect(sprite('102', '.studio-preview-ready').existsSync(), isFalse);
    downloads.clear();
    api.requests.clear();
    api.failures.clear();
    await app.prepareStartupSprites();
    expect(downloads, isEmpty);
    expect(api.requests, ['10:102']);
    expect(app.spriteWarning, isNull);
  });

  test('checksum mismatch leaves no trusted inventory and retries the download next launch', () async {
    final correct = archives['101']!;
    archives['101'] = utf8.encode('damaged download');
    await app.prepareStartupSprites();
    expect(app.spriteWarning, contains('checksum mismatch'));
    expect(sprite('101', '.studio-sprites.json').existsSync(), isFalse);
    archives['101'] = correct;
    downloads.clear();
    api.requests.clear();
    await app.prepareStartupSprites();
    expect(downloads, ['101']);
    expect(api.requests, ['10:101']);
    expect(app.spriteWarning, isNull);
  });

  test('a failed index refresh is retried even when every sprite is already cached', () async {
    api.failRebuild = true;
    await app.prepareStartupSprites();
    expect(app.spriteWarning, contains('Character index unavailable'));
    expect(app.bootSteps.last.detail, '0/3 forms ready; 3 retry next start');
    expect(sprite('101', '.studio-preview-ready').existsSync(), isFalse);
    api.failRebuild = false;
    downloads.clear();
    api.requests.clear();
    await app.prepareStartupSprites();
    expect(downloads, isEmpty);
    expect(api.rebuilds, 2);
    expect(api.requests, ['10:101', '10:102', '20:201']);
    expect(app.spriteWarning, isNull);
  });

  test('an unavailable sprite host stops repeated failures and retries all remaining forms later', () async {
    for (final form in ['301', '401']) {
      archives[form] = spriteZip(form);
      (app.hostIndex!['units'] as List).add({
        'id': form,
        'packs': [form],
      });
      (app.hostIndex!['forms'] as Map)[form] = {
        'url': '${app.hostBase}/$form.zip',
        'sha256': sha256.convert(archives[form]!).toString(),
      };
    }
    unavailable.addAll(archives.keys);
    await app.prepareStartupSprites();
    expect(downloads, ['101', '102', '201']);
    expect(app.spriteWarning, contains('5 character forms'));
    unavailable.clear();
    downloads.clear();
    await app.prepareStartupSprites();
    expect(downloads, ['101', '102', '201', '301', '401']);
    expect(app.bootSteps.last.detail, '5/5 forms ready');
    expect(app.spriteWarning, isNull);
  });

  test('offline launch retains cached packs and defers missing files without network requests', () async {
    await app.prepareStartupSprites();
    downloads.clear();
    api.requests.clear();
    sprite('201', 'unit_icon_201.png').deleteSync();
    app.banner = 'Could not reach the download host. Running the installed version; updates are checked next start.';
    await app.prepareStartupSprites();
    expect(downloads, isEmpty);
    expect(api.requests, isEmpty);
    expect(app.bootSteps.last.detail, '2/3 forms ready; 1 retry next start');
    expect(sprite('101', 'unit_anime_101.png').existsSync(), isTrue);
    expect(app.banner, contains('Running the installed version'));
    expect(app.spriteWarning, contains('download host is unreachable'));
  });

  test('old engines still receive the sprite packs without unsupported preparation jobs', () async {
    api.legacy = true;
    await app.prepareStartupSprites();
    expect(downloads, ['101', '102', '201']);
    expect(api.rebuilds, 1);
    expect(app.spriteWarning, isNull);
  });

  test('an unavailable character index does not prevent startup or erase installed sprites', () async {
    app.hostIndex = null;
    await app.prepareStartupSprites();
    expect(app.bootSteps.last.state, 'done');
    expect(app.spriteWarning, contains('retry next start'));
    expect(downloads, isEmpty);
  });

  test('first-run game setup finishes deferred unit preparation before opening the roster', () async {
    api.needsGameData = true;
    app.phase = Phase.setup;
    await app.prepareStartupSprites();
    expect(app.spriteWarning, contains('Prepare the game data first'));
    downloads.clear();
    await app.runSetup('fixture game');
    expect(downloads, isEmpty);
    expect(api.prepared, {'101', '102', '201'});
    expect(app.spriteWarning, isNull);
    expect(app.phase, Phase.ready);
    expect(app.setupProgress!.state, 'done');
  });
}
