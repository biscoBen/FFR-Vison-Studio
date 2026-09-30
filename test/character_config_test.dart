import 'dart:convert';
import 'dart:io';

import 'package:ffr_vision_studio/design/theme.dart';
import 'package:ffr_vision_studio/design/widgets.dart';
import 'package:ffr_vision_studio/screens/character_config_buttons.dart';
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
    for (var i = 0; i < 100; i++) {
      await tester.runAsync(() async {
        await Future<void>.delayed(const Duration(milliseconds: 5));
      });
      await tester.pump(const Duration(milliseconds: 5));
      if (find.byType(AlertDialog).evaluate().isNotEmpty &&
          find.text('Loading character config…').evaluate().isEmpty) {
        break;
      }
    }
    await tester.pumpAndSettle();
  }

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
    expect(temporary.listSync().whereType<File>().any((f) => f.path.endsWith('.tmp')), isFalse);
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
