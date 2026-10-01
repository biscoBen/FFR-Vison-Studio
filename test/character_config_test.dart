import 'dart:convert';
import 'dart:io';

import 'package:ffr_vision_studio/design/theme.dart';
import 'package:ffr_vision_studio/design/widgets.dart';
import 'package:ffr_vision_studio/screens/character_config_buttons.dart';
import 'package:ffr_vision_studio/screens/unit_anim_pane.dart';
import 'package:ffr_vision_studio/design/anim_viewer.dart';
import 'package:ffr_vision_studio/services/api.dart';
import 'package:ffr_vision_studio/services/bundled_features.dart';
import 'package:ffr_vision_studio/services/character_config.dart';
import 'package:ffr_vision_studio/services/paths.dart';
import 'package:ffr_vision_studio/state/app_state.dart';
import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:path/path.dart' as p;
import 'package:provider/provider.dart';

Map<String, dynamic> profile() =>
    json.decode(File('assets/crystal_fina/profile.json').readAsStringSync())
        as Map<String, dynamic>;
dynamic clone(dynamic value) => json.decode(json.encode(value));

class ConfigApi extends Api {
  ConfigApi(this.roster) : super('http://unused');
  List<dynamic> roster;
  int saves = 0;
  bool fail = false;
  Future<void> Function()? beforeSave;
  AppPaths? paths;
  final prepared = <String>{};
  final preparations = <String>[];
  bool failPreparation = false;
  @override
  Future<List<String>> anims(String form) async =>
      prepared.contains(form) ? ['idle', 'atk'] : [];
  @override
  Future<Map<String, dynamic>> prepareAssets(String ffbeId, String form) async {
    preparations.add('$ffbeId:$form');
    if (failPreparation) {
      throw ApiException('HTTP 429: the host is busy', statusCode: 429);
    }
    final directory = Directory(p.join(paths!.engineSprites, form))
      ..createSync(recursive: true);
    for (final name in [
      'unit_anime_$form.png',
      'unit_cgg_$form.csv',
      'unit_idle_cgs_$form.csv',
    ]) {
      final file = File(p.join(directory.path, name));
      if (!file.existsSync()) file.writeAsStringSync('cached $name');
    }
    return {'job': form};
  }

  @override
  Future<Map<String, dynamic>> assetProgress(String job) async {
    prepared.add(job);
    return {'state': 'done'};
  }

  @override
  Future<List<dynamic>> spec() async => clone(roster) as List;
  @override
  Future<void> saveSpec(List<dynamic> units) async {
    saves++;
    if (fail) {
      throw StateError('Disk full');
    }
    await beforeSave?.call();
    roster = clone(units) as List;
  }

  @override
  Future<void> deleteUnit(String key) async =>
      roster.removeWhere((u) => u['key'] == key);
}

class ConfigFilePicker extends FilePicker {
  String? savePath, loadPath;
  String? defaultName, initial;
  @override
  Future<String?> saveFile({
    String? dialogTitle,
    String? fileName,
    String? initialDirectory,
    FileType type = FileType.any,
    List<String>? allowedExtensions,
    Uint8List? bytes,
    bool lockParentWindow = false,
  }) async {
    defaultName = fileName;
    initial = initialDirectory;
    return savePath;
  }

  @override
  Future<FilePickerResult?> pickFiles({
    String? dialogTitle,
    String? initialDirectory,
    FileType type = FileType.any,
    List<String>? allowedExtensions,
    Function(FilePickerStatus)? onFileLoading,
    bool allowCompression = false,
    int compressionQuality = 0,
    bool allowMultiple = false,
    bool withData = false,
    bool withReadStream = false,
    bool lockParentWindow = false,
    bool readSequential = false,
  }) async => loadPath == null
      ? null
      : FilePickerResult([
          PlatformFile(name: p.basename(loadPath!), path: loadPath, size: 0),
        ]);
}

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  setUpAll(() async {
    await (FontLoader('Barlow')
          ..addFont(rootBundle.load('assets/fonts/Barlow-Regular.ttf'))
          ..addFont(rootBundle.load('assets/fonts/Barlow-SemiBold.ttf')))
        .load();
  });
  late Directory temporary;
  late AppState app;
  late ConfigApi api;
  late ConfigFilePicker picker;
  late Map<String, dynamic> saved;
  setUp(() {
    temporary = Directory.systemTemp.createTempSync('character-config-');
    saved = profile();
    saved['stats']['MaxHitPoint'] = 777;
    saved['advancedUnknown'] = {
      'futureField': [false, null, 1.5],
    };
    saved['awakening'][0].add(['ActiveSkill', 485300]);
    saved['ffbeMap']['skills']['custom'] = 485300;
    api = ConfigApi([clone(saved)]);
    app =
        AppState(
            hostBase: 'http://unused',
            appPaths: AppPaths.at(temporary.path),
            bundledFeatures: BundledFeatures(
              readAsset: (path) async => File(path).readAsBytesSync(),
            ),
          )
          ..api = api
          ..units = clone(api.roster) as List
          ..selectedKey = saved['key'] as String;
    api.paths = app.paths;
    picker = ConfigFilePicker();
    FilePicker.platform = picker;
  });
  tearDown(() {
    app.dispose();
    temporary.deleteSync(recursive: true);
  });

  Map<String, dynamic> other() {
    final unit = CharacterConfig.restore(saved, [saved]);
    unit['key'] = 'another';
    unit['jp'] = 'Another';
    unit['en'] = 'Another';
    unit['ffbe']['base'] = 'different';
    unit['ffbe']['id'] = 'different';
    return unit;
  }

  Map<String, dynamic> hostedCharacter() {
    final unit = CharacterConfig.copy(saved)..remove('bundledPreset');
    unit['key'] = 'hosted_character';
    unit['ffbe'] = {
      'id': '102',
      'base': '10',
      'source': 'JP',
      'dir': 'units/ffbe/hosted_character/sprites/102',
    };
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
      ],
    };
    return unit;
  }

  test('saved hosted config restores missing artwork and preview data without searching first', () async {
    final unit = hostedCharacter();
    final snapshot = CharacterConfig.decode(CharacterConfig.encode(unit));
    api.roster = [];
    app.units = [];
    expect(await app.animsFor('102'), isEmpty);
    final restored = await app.loadCharacterConfig(
      snapshot,
      expectedTargetKey: null,
    );
    expect(restored, unit);
    expect(api.preparations, ['10:102']);
    expect(await app.characterAnims(restored), ['idle', 'atk']);
    expect(
      File(
        p.join(
          app.paths.engineDir,
          unit['ffbe']['dir'],
          'unit_idle_cgs_102.csv',
        ),
      ).readAsStringSync(),
      'cached unit_idle_cgs_102.csv',
    );
    expect(api.roster.single, unit);
  });

  test('remove and restore retains edited artwork and the chosen appearance across reopening Studio', () async {
    final unit = hostedCharacter();
    api.roster = [unit];
    app.units = [unit];
    final art = File(
      p.join(app.paths.engineDir, unit['ffbe']['dir'], 'unit_anime_102.png'),
    );
    art.parent.createSync(recursive: true);
    art.writeAsStringSync('my edited artwork');
    File(p.join(art.parent.path, 'unit_cgg_102.csv'))
        .writeAsStringSync('my motion layout');
    final snapshot = await app.snapshotCharacter(unit['key']);
    await app.removeUnit(unit['key']);
    final restored = await app.loadCharacterConfig(
      CharacterConfig.decode(CharacterConfig.encode(snapshot)),
      expectedTargetKey: null,
    );
    expect(art.readAsStringSync(), 'my edited artwork');
    expect(
      File(p.join(art.parent.path, 'unit_cgg_102.csv')).readAsStringSync(),
      'my motion layout',
    );
    final reopened = AppState(hostBase: 'http://unused', appPaths: app.paths)
      ..api = api;
    addTearDown(reopened.dispose);
    expect(await reopened.characterAnims(restored), ['idle', 'atk']);
    expect(api.preparations, ['10:102']);
    expect(restored['ffbe'], unit['ffbe']);
  });

  test('reopening repairs missing sprite sheets even when animation names are cached', () async {
    final unit = hostedCharacter();
    api.roster = [];
    app.units = [];
    await app.loadCharacterConfig(unit, expectedTargetKey: null);
    expect(await app.characterAnims(unit), ['idle', 'atk']);
    Directory(p.join(app.paths.engineSprites, '102'))
        .deleteSync(recursive: true);
    expect(await app.characterAnims(unit), ['idle', 'atk']);
    expect(api.preparations, ['10:102', '10:102']);
    expect(
      File(p.join(app.paths.engineSprites, '102', 'unit_anime_102.png'))
          .existsSync(),
      isTrue,
    );
    expect(api.roster.single, unit);
  });

  test('a shifted saved appearance restores only its selected and base-form artwork', () async {
    final unit = hostedCharacter();
    unit['ffbe'].addAll({
      'baseForm': '101',
      'baseDir': 'units/ffbe/hosted_character/sprites/101',
      'shift': 'brave',
    });
    api.roster = [];
    app.units = [];
    await app.loadCharacterConfig(unit, expectedTargetKey: null);
    expect(api.preparations, ['10:102', '10:101']);
    expect(
      File(
        p.join(
          app.paths.engineDir,
          unit['ffbe']['baseDir'],
          'unit_anime_101.png',
        ),
      ).existsSync(),
      isTrue,
    );
    expect(api.roster.single, unit);
    final unsafe = CharacterConfig.copy(unit)
      ..['ffbe']['baseDir'] = 'units/../../outside';
    expect(() => CharacterConfig.encode(unsafe), throwsFormatException);
  });

  test('load all prepares only the saved characters and keeps their complete configs', () async {
    final first = hostedCharacter();
    final second = CharacterConfig.restore(first, [first])
      ..['key'] = 'second_hosted';
    second['ffbe'] = {
      'id': '201',
      'base': '20',
      'source': 'GL',
      'dir': 'units/ffbe/second_hosted/sprites/201',
    };
    final configs = CharacterConfig.decodeAll(
      CharacterConfig.encodeAll([first, second]),
    );
    api.roster = [];
    app.units = [];
    final restored = await app.loadAllCharacterConfigs(
      configs,
      expectedTargetKeys: [null, null],
    );
    expect(api.preparations, ['10:102', '20:201']);
    expect(restored, configs);
    expect(api.roster, configs);
  });

  test(
    'a failed config sprite preparation keeps the roster and can be retried',
    () async {
      final unit = hostedCharacter();
      final before = clone(api.roster);
      api.failPreparation = true;
      await expectLater(
        app.loadCharacterConfig(unit, expectedTargetKey: null),
        throwsA(predicate((e) => e.toString().contains('HTTP 429'))),
      );
      expect(api.roster, before);
      expect(api.saves, 0);
      api.failPreparation = false;
      await app.loadCharacterConfig(unit, expectedTargetKey: null);
      expect(await app.characterAnims(unit), ['idle', 'atk']);
      expect(api.preparations, ['10:102', '10:102']);
    },
  );

  testWidgets(
    'a loaded character still displays motions after leaving and reopening its page',
    (tester) async {
      final unit = hostedCharacter();
      api.roster = [];
      app.units = [];
      await tester.runAsync(
        () => app.loadCharacterConfig(unit, expectedTargetKey: null),
      );
      Future<void> open() async {
        await tester.pumpWidget(
          ChangeNotifierProvider<AppState>.value(
            value: app,
            child: MaterialApp(
              home: Scaffold(body: UnitAnimPane(unit: unit)),
            ),
          ),
        );
        await tester.pumpAndSettle();
        final viewer = tester.widget<AnimViewer>(find.byType(AnimViewer));
        expect(viewer.anims, ['idle', 'atk']);
        expect(viewer.loading, isFalse);
        expect(viewer.url('idle'), endsWith('/102/idle.webp'));
      }

      await open();
      await tester.pumpWidget(const SizedBox.shrink());
      await open();
      expect(api.preparations, ['10:102']);
      expect(tester.takeException(), isNull);
    },
  );

  test('save and load preserve every setting, including custom Resonance and future fields', () {
    final restored = CharacterConfig.decode(CharacterConfig.encode(saved));
    expect(restored, saved);
    expect(restored['lb_custom']['en'], 'Crystal Restoration');
    restored['stats']['MaxHitPoint'] = 100;
    expect(saved['stats']['MaxHitPoint'], 777);
  });

  test('malformed, unsupported and incomplete files are rejected', () {
    for (final contents in [
      'not json',
      '[]',
      '{}',
      json.encode({
        'format': CharacterConfig.format,
        'version': 2,
        'unit': saved,
      }),
      json.encode({
        'format': CharacterConfig.format,
        'version': 1,
        'unit': {'key': 'missing'},
      }),
    ]) {
      expect(() => CharacterConfig.decode(contents), throwsFormatException);
    }
    for (final path in [
      '../outside',
      '/units/custom',
      'units/../outside',
      r'C:\outside',
    ]) {
      final broken = CharacterConfig.copy(saved)..['ffbe']['dir'] = path;
      expect(() => CharacterConfig.encode(broken), throwsFormatException);
    }
  });

  test('restoring an available ID changes no settings or references', () {
    expect(CharacterConfig.restore(saved, [other()]), saved);
  });

  test('vision, command, master, custom skill and Resonance ID collisions are remapped', () {
    for (final field in ['id', 'command', 'master', 'skills', 'resonance']) {
      final occupied = other();
      switch (field) {
        case 'id':
          occupied['id'] = saved['id'];
        case 'command':
          occupied['command']['id'] = saved['command']['id'];
        case 'master':
          occupied['master']['id'] = saved['master']['id'];
        case 'skills':
          occupied['skills']['485300'] = clone(saved['skills']['485300']);
          occupied['skills']['485300']['jp'] = 'Other move';
        case 'resonance':
          occupied['skills']['${CharacterConfig.resonanceId(saved['id'] as int)}'] =
              clone(saved['skills']['485300']);
          occupied['skills']['${CharacterConfig.resonanceId(saved['id'] as int)}']['jp'] =
              'Other move';
      }
      final before = clone(occupied);
      final loaded = CharacterConfig.restore(saved, [occupied]);
      final id = loaded['id'] as int;
      expect(id, isNot(saved['id']), reason: field);
      expect(loaded['awakening'][0].last, [
        'ActiveSkill',
        CharacterConfig.skillBase(id),
      ]);
      expect(loaded['synchro'].last.last, ['MasterSkill', id * 100]);
      expect(
        loaded['ffbeMap']['skills']['custom'],
        CharacterConfig.skillBase(id),
      );
      expect(loaded['skills'].values.single, saved['skills'].values.single);
      for (final setting in [
        'lb',
        'lb_custom',
        'stats',
        'elemRes',
        'ffbe',
        'advancedUnknown',
      ]) {
        expect(loaded[setting], saved[setting], reason: '$field / $setting');
      }
      expect(occupied, before);
    }
  });

  test(
    're-added character keeps its current ID while recovering the saved setup',
    () {
      final readded = CharacterConfig.restore(saved, [saved])
        ..['key'] = 'fina_readded';
      expect(CharacterConfig.target(saved, [readded]), same(readded));
      final loaded = CharacterConfig.restore(saved, [
        readded,
      ], replacing: readded);
      expect(loaded['key'], 'fina_readded');
      expect(loaded['id'], readded['id']);
      expect(loaded['stats'], saved['stats']);
      expect(loaded['lb_custom'], saved['lb_custom']);
    },
  );

  test('unrelated key collisions use a new key and multiple matching characters are rejected', () {
    final unrelated = other()..['key'] = saved['key'];
    expect(CharacterConfig.target(saved, [unrelated]), isNull);
    expect(
      CharacterConfig.restore(saved, [unrelated])['key'],
      '${saved['key']}_2',
    );
    final a = CharacterConfig.copy(saved)..['key'] = 'a';
    final b = CharacterConfig.copy(saved)..['key'] = 'b';
    expect(() => CharacterConfig.target(saved, [a, b]), throwsStateError);
  });

  test(
    'conflicting table row names are unique without changing displayed names',
    () {
      final duplicate = other()..['jp'] = saved['jp'];
      duplicate['skills'].values.single['jp'] =
          saved['skills'].values.single['jp'];
      duplicate['lb_custom']['jp'] = saved['lb_custom']['jp'];
      final result = CharacterConfig.restore(saved, [duplicate]);
      expect(result['jp'], '${saved['jp']}_2');
      expect(
        result['skills'].values.single['jp'],
        '${saved['skills'].values.single['jp']}_2',
      );
      expect(result['lb_custom']['jp'], '${saved['lb_custom']['jp']}_2');
      expect(result['en'], saved['en']);
      expect(result['lb_custom']['en'], 'Crystal Restoration');
    },
  );

  test('snapshot includes edits waiting for autosave', () async {
    final edited = CharacterConfig.copy(saved)..['stats']['Attack'] = 123;
    app.update(edited);
    expect(
      (await app.snapshotCharacter(saved['key'] as String))['stats']['Attack'],
      123,
    );
    expect(api.roster.single['stats']['Attack'], 123);
    expect(app.dirty, isFalse);
  });

  test('remove then load restores exact full config and preserves unrelated roster entries', () async {
    final unrelated = other();
    api.roster.add(unrelated);
    app.units = clone(api.roster) as List;
    final snapshot = await app.snapshotCharacter(saved['key'] as String);
    expect(await app.removeUnit(saved['key'] as String), isTrue);
    final result = await app.loadCharacterConfig(
      snapshot,
      expectedTargetKey: null,
    );
    expect(result, saved);
    expect(api.roster, [unrelated, saved]);
    final backup = Directory(app.paths.configBackups)
        .listSync()
        .whereType<File>()
        .single;
    expect(json.decode(backup.readAsStringSync()), [unrelated]);
    expect(app.selected, saved);
  });

  test(
    'replacement backs up current edits and keeps roster ordering',
    () async {
      api.roster = [other(), clone(saved)];
      app.units = clone(api.roster) as List;
      app.update(CharacterConfig.copy(saved)..['stats']['Attack'] = 222);
      await app.loadCharacterConfig(
        saved,
        expectedTargetKey: saved['key'] as String,
      );
      expect(api.roster.last, saved);
      expect(
        json
            .decode(
              Directory(app.paths.configBackups)
                  .listSync()
                  .whereType<File>()
                  .single
                  .readAsStringSync(),
            )
            .last['stats']['Attack'],
        222,
      );
    },
  );

  test(
    'unrelated edits made during loading are saved without undoing the restore',
    () async {
      final unrelated = other();
      api.roster = [unrelated];
      app.units = clone(api.roster) as List;
      var changed = false;
      api.beforeSave = () async {
        if (!changed) {
          changed = true;
          app.update(
            CharacterConfig.copy(unrelated)..['stats']['Attack'] = 999,
          );
        }
      };
      await app.loadCharacterConfig(saved, expectedTargetKey: null);
      expect(api.roster.last, saved);
      expect(api.roster.first['stats']['Attack'], 999);
      expect(app.dirty, isFalse);
    },
  );

  test('engine failure, a running build or changed target cannot replace the roster', () async {
    final before = clone(api.roster);
    app.buildState = {'running': true};
    await expectLater(
      app.loadCharacterConfig(saved, expectedTargetKey: saved['key'] as String),
      throwsStateError,
    );
    app.buildState = null;
    await expectLater(
      app.loadCharacterConfig(saved, expectedTargetKey: null),
      throwsStateError,
    );
    api.fail = true;
    await expectLater(
      app.loadCharacterConfig(saved, expectedTargetKey: saved['key'] as String),
      throwsStateError,
    );
    expect(api.roster, before);
    expect(app.units, before);
    expect(
      Directory(app.paths.configBackups).listSync().whereType<File>(),
      hasLength(1),
    );
  });

  test('missing unbundled artwork does not add an unusable vision', () async {
    final unavailable = other();
    await expectLater(
      app.loadCharacterConfig(unavailable, expectedTargetKey: null),
      throwsA(predicate((e) => e.toString().contains('artwork'))),
    );
    expect(api.saves, 0);
  });

  Future<void> buttons(
    WidgetTester tester, {
    bool followSelection = false,
    bool includeAll = false,
  }) async {
    await tester.pumpWidget(
      ChangeNotifierProvider<AppState>.value(
        value: app,
        child: MaterialApp(
          theme: Guide.theme(),
          home: Scaffold(
            body: Consumer<AppState>(
              builder: (_, state, _) => Align(
                alignment: Alignment.bottomLeft,
                child: SizedBox(
                  width: 300,
                  child: CharacterConfigButtons(
                    key: followSelection ? ValueKey(state.selectedKey) : null,
                    includeAll: includeAll,
                  ),
                ),
              ),
            ),
          ),
        ),
      ),
    );
    await tester.pump();
  }

  Future<void> completeIo(WidgetTester tester) async {
    // Real file I/O completes outside the widget test's fake clock.
    final deadline = DateTime.now().add(const Duration(seconds: 15));
    var completed = false;
    while (DateTime.now().isBefore(deadline)) {
      await tester.runAsync(() async {
        await Future<void>.delayed(const Duration(milliseconds: 20));
      });
      await tester.pump(const Duration(milliseconds: 20));
      final loading =
          find.text('Loading character config…').evaluate().isNotEmpty ||
          find.text('Loading all character configs…').evaluate().isNotEmpty;
      final footerLoad = find.descendant(
        of: find.byType(CharacterConfigButtons),
        matching: find.widgetWithText(GuideButton, 'Load character config'),
      );
      final idle =
          footerLoad.evaluate().isNotEmpty &&
          tester.widget<GuideButton>(footerLoad).onPressed != null;
      if (!loading &&
          (find.byType(AlertDialog).evaluate().isNotEmpty || idle)) {
        completed = true;
        break;
      }
    }
    expect(
      completed,
      isTrue,
      reason:
          'The config file operation must finish before settling its dialog.',
    );
    await tester.pumpAndSettle();
  }

  void cacheArtwork(Map<String, dynamic> unit) {
    final directory = Directory(
      p.join(app.paths.engineDir, unit['ffbe']['dir'] as String),
    )..createSync(recursive: true);
    for (final name in [
      'unit_anime_${unit['ffbe']['id']}.png',
      'unit_cgg_${unit['ffbe']['id']}.csv',
    ]) {
      File(p.join(directory.path, name))
          .writeAsStringSync('mock cached artwork');
    }
  }

  test('all-character file round trips every unit and rejects invalid or duplicate entries', () {
    final all = [saved, other()];
    expect(CharacterConfig.decodeAll(CharacterConfig.encodeAll(all)), all);
    for (final units in [
      [],
      [saved, saved],
      [
        saved,
        {'key': 'incomplete'},
      ],
    ]) {
      expect(() => CharacterConfig.encodeAll(units), throwsFormatException);
    }
    expect(
      () => CharacterConfig.decodeAll(CharacterConfig.encode(saved)),
      throwsFormatException,
    );
    expect(
      () => CharacterConfig.decode(CharacterConfig.encodeAll(all)),
      throwsFormatException,
    );
  });

  test('batch allocation reserves later original IDs and keeps references between saved units', () {
    final second = other();
    saved['awakening'][0].add([
      'ActiveSkill',
      CharacterConfig.skillBase(second['id'] as int),
    ]);
    saved['ffbeMap']['skills']['otherMove'] = CharacterConfig.skillBase(
      second['id'] as int,
    );
    second['synchro'][0].add(['MasterSkill', saved['master']['id']]);
    // A re-added Fina has the ID previously belonging to the second saved unit.
    final currentFina = CharacterConfig.restore(saved, [saved]);
    final targets = CharacterConfig.targets([saved, second], [currentFina]);
    final loaded = CharacterConfig.restoreAll(
      [saved, second],
      [currentFina],
      targets,
    );
    expect(loaded[0]['id'], currentFina['id']);
    expect(loaded[1]['id'], isNot(second['id']));
    expect(
      loaded[0]['awakening'][0].where(
        (g) =>
            g[0] == 'ActiveSkill' &&
            g[1] == CharacterConfig.skillBase(loaded[0]['id'] as int),
      ),
      isNotEmpty,
    );
    expect(loaded[0]['awakening'][0].last, [
      'ActiveSkill',
      CharacterConfig.skillBase(loaded[1]['id'] as int),
    ]);
    expect(
      loaded[0]['ffbeMap']['skills']['otherMove'],
      CharacterConfig.skillBase(loaded[1]['id'] as int),
    );
    expect(loaded[1]['synchro'][0].last, [
      'MasterSkill',
      loaded[0]['master']['id'],
    ]);
    expect(loaded[0]['lb_custom'], saved['lb_custom']);
  });

  test(
    'an earlier ID collision does not consume a later saved unit original ID',
    () {
      final second = other();
      final occupied = CharacterConfig.copy(saved)
        ..['key'] = 'occupied'
        ..['ffbe']['base'] = 'unrelated';
      final loaded = CharacterConfig.restoreAll([saved, second], [occupied], [
        null,
        null,
      ]);
      expect(loaded[0]['id'], 13505);
      expect(loaded[1]['id'], second['id']);
    },
  );

  test('exact duplicate-character entries are reserved before a renamed copy is matched', () {
    final secondCopy = CharacterConfig.restore(saved, [saved])
      ..['key'] = 'second_copy';
    final renamedFirst = CharacterConfig.copy(saved)..['key'] = 'renamed_first';
    final targets = CharacterConfig.targets(
      [saved, secondCopy],
      [secondCopy, renamedFirst],
    );
    expect(targets.map((u) => u!['key']), ['renamed_first', 'second_copy']);
    expect(CharacterConfig.restoreAll([saved, secondCopy], [], [null, null]), [
      saved,
      secondCopy,
    ]);
  });

  test('all snapshots include pending edits; bulk restore writes once and preserves additional units', () async {
    final second = other();
    cacheArtwork(second);
    api.roster = [clone(saved), clone(second)];
    app.units = clone(api.roster) as List;
    app.update(CharacterConfig.copy(second)..['stats']['Attack'] = 123);
    final snapshot = await app.snapshotCharacters();
    expect(snapshot[1]['stats']['Attack'], 123);
    final extra = CharacterConfig.restore(second, snapshot)
      ..['key'] = 'extra'
      ..['ffbe']['base'] = 'extra';
    api.roster = [extra, clone(second)];
    app.units = clone(api.roster) as List;
    final countBefore = api.saves;
    await app.loadAllCharacterConfigs(
      snapshot,
      expectedTargetKeys: [null, second['key'] as String],
    );
    expect(api.saves, countBefore + 1);
    expect(api.roster, [extra, snapshot[1], snapshot[0]]);
    expect(app.selectedKey, isNull);
    expect(
      json.decode(
        Directory(app.paths.configBackups)
            .listSync()
            .whereType<File>()
            .single
            .readAsStringSync(),
      ),
      [extra, second],
    );
  });

  test('a bad later entry, missing artwork or changed target cannot partially restore a batch', () async {
    final second = other();
    final before = clone(api.roster);
    await expectLater(
      app.loadAllCharacterConfigs(
        [saved, second],
        expectedTargetKeys: [saved['key'] as String, null],
      ),
      throwsA(predicate((e) => e.toString().contains('artwork'))),
    );
    cacheArtwork(second);
    await expectLater(
      app.loadAllCharacterConfigs(
        [
          saved,
          {'key': 'invalid'},
        ],
        expectedTargetKeys: [null, null],
      ),
      throwsFormatException,
    );
    await expectLater(
      app.loadAllCharacterConfigs(
        [saved, second],
        expectedTargetKeys: [null, null],
      ),
      throwsStateError,
    );
    expect(api.saves, 0);
    expect(api.roster, before);
  });

  test(
    'bulk engine failure leaves the roster unchanged and retains its backup',
    () async {
      final second = other();
      cacheArtwork(second);
      api.fail = true;
      final before = clone(api.roster);
      await expectLater(
        app.loadAllCharacterConfigs(
          [saved, second],
          expectedTargetKeys: [saved['key'] as String, null],
        ),
        throwsStateError,
      );
      expect(api.roster, before);
      expect(app.units, before);
      expect(Directory(app.paths.configBackups).listSync(), hasLength(1));
    },
  );

  test(
    'edits to additional units during a bulk request survive the restore',
    () async {
      final second = other();
      cacheArtwork(second);
      final extra = CharacterConfig.restore(second, [saved, second])
        ..['key'] = 'extra'
        ..['ffbe']['base'] = 'extra';
      api.roster = [extra];
      app.units = clone(api.roster) as List;
      var changed = false;
      api.beforeSave = () async {
        if (!changed) {
          changed = true;
          app.update(CharacterConfig.copy(extra)..['stats']['Attack'] = 999);
        }
      };
      await app.loadAllCharacterConfigs(
        [saved, second],
        expectedTargetKeys: [null, null],
      );
      expect(api.roster.first['stats']['Attack'], 999);
      expect(api.roster.skip(1), [saved, second]);
      expect(app.dirty, isFalse);
    },
  );

  testWidgets('bulk buttons appear only on the main-page footer', (
    tester,
  ) async {
    await buttons(tester);
    expect(find.text('Save all character configs'), findsNothing);
    expect(find.text('Load all character configs'), findsNothing);
    await buttons(tester, includeAll: true);
    expect(find.text('Save all character configs'), findsOneWidget);
    expect(find.text('Load all character configs'), findsOneWidget);
  });

  testWidgets(
    'Save all writes one file and Load all restores every setup with confirmation',
    (tester) async {
      final second = other();
      cacheArtwork(second);
      api.roster.add(second);
      app.units = clone(api.roster) as List;
      app.selectedKey = null;
      picker.savePath = p.join(temporary.path, 'all.visions.json');
      picker.loadPath = picker.savePath;
      await buttons(tester, includeAll: true);
      await tester.tap(find.text('Save all character configs'));
      await completeIo(tester);
      expect(
        CharacterConfig.decodeAll(File(picker.savePath!).readAsStringSync()),
        [saved, second],
      );
      expect(picker.defaultName, 'All Characters.visions.json');
      await tester.tap(find.text('OK'));
      await tester.pumpAndSettle();
      api.roster = [];
      app.units = [];
      app.select(null);
      await tester.pump();
      await tester.tap(find.text('Load all character configs'));
      await completeIo(tester);
      expect(find.text('Load all character configs?'), findsOneWidget);
      expect(find.textContaining('Restores 2 missing units'), findsOneWidget);
      await tester.tap(
        find.widgetWithText(GuideButton, 'Load all character configs').last,
      );
      await completeIo(tester);
      expect(find.text('All character configs loaded'), findsOneWidget);
      expect(api.roster, [saved, second]);
      expect(app.selectedKey, isNull);
      expect(tester.takeException(), isNull);
    },
  );

  testWidgets(
    'empty roster disables Save all and cancelled bulk load changes nothing',
    (tester) async {
      picker.loadPath = p.join(temporary.path, 'all.visions.json');
      File(picker.loadPath!)
          .writeAsStringSync(CharacterConfig.encodeAll([saved]));
      api.roster = [];
      app.units = [];
      app.selectedKey = null;
      await buttons(tester, includeAll: true);
      expect(
        tester
            .widget<GuideButton>(
              find.widgetWithText(GuideButton, 'Save all character configs'),
            )
            .onPressed,
        isNull,
      );
      await tester.tap(find.text('Load all character configs'));
      await completeIo(tester);
      await tester.tap(find.text('Cancel'));
      await tester.pumpAndSettle();
      expect(api.saves, 0);
      expect(api.roster, isEmpty);
    },
  );

  testWidgets('bottom-left Save writes a reusable file with every field', (
    tester,
  ) async {
    picker.savePath = p.join(temporary.path, 'saved.vision.json');
    File(picker.savePath!).writeAsStringSync('an older save to replace');
    await buttons(tester);
    await tester.tap(find.text('Save character config'));
    await completeIo(tester);
    expect(
      CharacterConfig.decode(File(picker.savePath!).readAsStringSync()),
      saved,
    );
    expect(picker.defaultName, 'Crystal Fina.vision.json');
    expect(picker.initial, app.paths.characterConfigs);
    expect(
      temporary.listSync().whereType<File>().any(
        (f) => f.path.endsWith('.tmp'),
      ),
      isFalse,
    );
    expect(find.text('Character config saved'), findsOneWidget);
  });

  testWidgets(
    'Save is disabled without selection; Load restores from an empty roster and closes progress',
    (tester) async {
      picker.loadPath = p.join(temporary.path, 'saved.vision.json');
      File(picker.loadPath!).writeAsStringSync(CharacterConfig.encode(saved));
      api.roster = [];
      app.units = [];
      app.selectedKey = null;
      await buttons(tester, followSelection: true);
      final save = tester.widget<GuideButton>(
        find.widgetWithText(GuideButton, 'Save character config'),
      );
      expect(save.onPressed, isNull);
      await tester.tap(find.text('Load character config'));
      await completeIo(tester);
      expect(find.text('Restore Crystal Fina?'), findsOneWidget);
      await tester.tap(
        find.widgetWithText(GuideButton, 'Load character config').last,
      );
      await completeIo(tester);
      expect(api.roster, [saved]);
      expect(find.text('Loading character config…'), findsNothing);
      expect(find.text('Character config loaded'), findsOneWidget);
      expect(tester.takeException(), isNull);
    },
  );

  testWidgets('cancelling replacement preserves the current setup', (
    tester,
  ) async {
    picker.loadPath = p.join(temporary.path, 'saved.vision.json');
    File(picker.loadPath!).writeAsStringSync(CharacterConfig.encode(saved));
    await buttons(tester);
    await tester.tap(find.text('Load character config'));
    await completeIo(tester);
    expect(find.text('Load config for Crystal Fina?'), findsOneWidget);
    await tester.tap(find.text('Cancel'));
    await tester.pumpAndSettle();
    expect(api.saves, 0);
    expect(api.roster, [saved]);
  });

  testWidgets(
    'bad files show an error and native dialog cancellation is harmless',
    (tester) async {
      await buttons(tester);
      await tester.tap(find.text('Save character config'));
      await completeIo(tester);
      await tester.tap(find.text('Load character config'));
      await completeIo(tester);
      expect(find.byType(AlertDialog), findsNothing);
      picker.loadPath = p.join(temporary.path, 'invalid.json');
      File(picker.loadPath!).writeAsStringSync('[]');
      await tester.tap(find.text('Load character config'));
      await completeIo(tester);
      expect(find.text('Could not load character config'), findsOneWidget);
      expect(api.saves, 0);
      expect(api.roster, [saved]);
    },
  );
}
