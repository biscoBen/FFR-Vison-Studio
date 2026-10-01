import 'dart:io';

import 'package:ffr_vision_studio/design/theme.dart';
import 'package:ffr_vision_studio/design/widgets.dart';
import 'package:ffr_vision_studio/screens/home_screen.dart';
import 'package:ffr_vision_studio/screens/unit_screen.dart';
import 'package:ffr_vision_studio/services/bundled_features.dart';
import 'package:ffr_vision_studio/services/character_config.dart';
import 'package:ffr_vision_studio/services/paths.dart';
import 'package:ffr_vision_studio/state/app_state.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:provider/provider.dart';

import 'character_config_test.dart' show ConfigApi, profile, clone;

Map<String, dynamic> originalFixture() {
  final u = profile()
    ..remove('ffbe')
    ..remove('lb_custom')
    ..remove('custom');
  u.addAll({
    'key': 'native_13110',
    'id': 13110,
    'donor': 13110,
    'en': 'Cloud',
    'jp': 'Cloud',
    'lb': 440110,
    'command': {'id': 202, 'en': 'Cloud skills', 'desc': ''},
    'master': {'id': 500, 'en': 'Spirit of Cloud', 'desc': ''},
    'awakening': [
      [
        ['ActiveSkill', 446000],
      ],
      [],
      [],
      [],
    ],
    'synchro': [for (var i = 0; i < 10; i++) <dynamic>[]],
    'skills': <String, dynamic>{},
  });
  u['native'] = {
    'version': 1,
    'id': 13110,
    'baseline': clone(u),
    'synchroCaps': List.filled(10, 5),
  };
  return u;
}

class NativeApi extends ConfigApi {
  NativeApi(super.roster);
  @override
  Future<Map<String, dynamic>> nativeVision(int id) async => originalFixture();
  @override
  Future<List<dynamic>> nativeVisions() async => [originalFixture()];
  @override
  Future<List<dynamic>> ffbeUnits() async => [];
  @override
  Future<List<String>> anims(String form) async => [];
}

void main() {
  setUpAll(() async {
    await (FontLoader(
      'Barlow',
    )..addFont(rootBundle.load('assets/fonts/Barlow-Regular.ttf'))).load();
    await (FontLoader('BarlowCondensed')
          ..addFont(rootBundle.load('assets/fonts/BarlowCondensed-Bold.ttf')))
        .load();
  });
  late Directory dir;
  late NativeApi api;
  late AppState app;
  setUp(() {
    dir = Directory.systemTemp.createTempSync('native-vision-');
    api = NativeApi([profile()]);
    app =
        AppState(
            hostBase: 'http://unused',
            appPaths: AppPaths.at(dir.path),
            bundledFeatures: BundledFeatures(
              readAsset: (path) async => File(path).readAsBytesSync(),
            ),
          )
          ..api = api
          ..units = clone(api.roster) as List
          ..nativeVisions = [originalFixture()]
          ..catalog = {
            'skills': [
              {
                'id': 440110,
                'name': 'Climhazzard',
                'desc': 'Original Resonance',
                'attr': 'FinishBlow',
              },
              {
                'id': 446000,
                'name': 'Braver',
                'attr': 'Ability',
                'seq': [1],
                'hasUnit': 'All',
              },
            ],
            'passives': [],
            'icons': [],
          };
  });
  tearDown(() {
    app.dispose();
    dir.deleteSync(recursive: true);
  });

  test(
    'opening an original keeps its game ID and all current added-unit edits',
    () async {
      final edited = CharacterConfig.copy(app.units.first as JsonMap)
        ..['stats']['Attack'] = 123;
      app.update(edited);
      final native = await app.editNativeVision(13110);
      expect(native, originalFixture());
      expect(api.roster.first, edited);
      expect(api.roster, hasLength(2));
      expect(app.selectedKey, 'native_13110');
      await app.editNativeVision(13110);
      expect(api.roster, hasLength(2));
    },
  );

  test('Fina model replacement preserves every original kit field and existing Fina', () async {
    final before = clone(api.roster);
    final native = await app.editNativeVision(13110, appearance: profile());
    final expected = originalFixture()
      ..['ffbe'] = profile()['ffbe']
      ..['menuScale'] = profile()['menuScale'] ?? 2.52;
    if (profile()['icon'] != null) {
      expected['icon'] = profile()['icon'];
    }
    expect(native, expected);
    expect(api.roster.first, before.first);
    expect(native['lb'], 440110);
    expect(native['lb_custom'], isNull);
    expect(app.hasCrystalFina, isTrue);
    app.useOriginalModel(native);
    await app.save();
    expect(api.roster.last, originalFixture());
  });

  test('incomplete original snapshots and changed native identities are rejected before loading', () {
    final incomplete = originalFixture();
    (incomplete['native']['baseline'] as Map).remove('stats');
    expect(() => CharacterConfig.validate(incomplete), throwsFormatException);
    final moved = originalFixture();
    moved['command']['id'] = 999;
    expect(() => CharacterConfig.validate(moved), throwsFormatException);
    final missingCaps = originalFixture();
    missingCaps['native']['synchroCaps'] = [5];
    expect(() => CharacterConfig.validate(missingCaps), throwsFormatException);
  });

  test('original configs match by game identity across model changes and never reassign native IDs', () {
    final old = originalFixture();
    final changed = CharacterConfig.copy(old)..['ffbe'] = profile()['ffbe'];
    expect(CharacterConfig.sameCharacter(old, changed), isTrue);
    expect(CharacterConfig.sameCharacter(changed, profile()), isFalse);
    final saved = CharacterConfig.decode(CharacterConfig.encode(old));
    expect(saved, old);
    expect(
      CharacterConfig.restore(saved, [profile(), changed], replacing: changed),
      old,
    );
    expect(
      CharacterConfig.decodeAll(CharacterConfig.encodeAll([profile(), old])),
      [profile(), old],
    );
    expect(
      CharacterConfig.restoreAll([profile(), old], [profile(), changed], [
        profile(),
        changed,
      ]),
      [profile(), old],
    );
    expect(() => CharacterConfig.restore(old, [old]), throwsStateError);
  });

  test('restoring an original config works without FFBE artwork and leaves added units intact', () async {
    final native = originalFixture();
    native['stats']['Attack'] = 155;
    await app.loadCharacterConfig(native, expectedTargetKey: null);
    expect(api.roster, [profile(), native]);
    expect(api.roster.last['id'], 13110);
    app.units = [native];
    expect(app.hasCrystalFina, isFalse);
  });

  Future<void> show(WidgetTester tester) async {
    tester.view.physicalSize = const Size(1320, 860);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);
    await tester.pumpWidget(
      ChangeNotifierProvider<AppState>.value(
        value: app,
        child: MaterialApp(
          theme: Guide.theme(),
          home: Scaffold(
            body: Consumer<AppState>(
              builder: (_, state, _) => state.selected == null
                  ? const HomeScreen()
                  : const UnitScreen(),
            ),
          ),
        ),
      ),
    );
    await tester.pumpAndSettle();
  }

  Future<void> wait(WidgetTester tester, bool Function() ready) async {
    final deadline = DateTime.now().add(const Duration(seconds: 15));
    while (!ready() && DateTime.now().isBefore(deadline)) {
      await tester.runAsync(
        () => Future<void>.delayed(const Duration(milliseconds: 10)),
      );
      await tester.pump(const Duration(milliseconds: 20));
    }
    expect(ready(), isTrue);
    await tester.pumpAndSettle();
  }

  testWidgets(
    'opening screen lists untouched game visions; viewing Resonance never creates a custom LB',
    (tester) async {
      await show(tester);
      expect(find.text('CLOUD'), findsOneWidget);
      expect(api.roster, hasLength(1));
      await tester.tap(find.text('CLOUD'));
      await tester.pumpAndSettle();
      await tester.tap(find.widgetWithText(GuideButton, 'Edit vision'));
      await wait(tester, () => app.selected != null);
      expect(find.text('Change model'), findsOneWidget);
      await tester.tap(find.text('4  RESONANCE'));
      await tester.pumpAndSettle();
      expect(find.text('Climhazzard'), findsOneWidget);
      expect(find.text('Climhazzard (Unverified)'), findsOneWidget);
      expect(app.selected!['lb_custom'], isNull);
      expect(api.roster.last, originalFixture());
      expect(tester.takeException(), isNull);
    },
  );

  testWidgets(
    'the normal model picker can use Fina without adding or replacing her kit',
    (tester) async {
      await show(tester);
      await tester.tap(find.text('CLOUD'));
      await tester.pumpAndSettle();
      await tester.tap(find.widgetWithText(GuideButton, 'Change model'));
      await tester.pumpAndSettle();
      expect(find.text('CHOOSE A REPLACEMENT MODEL'), findsOneWidget);
      await tester.tap(find.text('Crystal Fina'));
      await wait(
        tester,
        () => find.text('REPLACEMENT MODEL').evaluate().isNotEmpty,
      );
      await tester.tap(find.text('USE THIS MODEL'));
      await wait(tester, () => app.selected != null);
      expect(api.roster, hasLength(2));
      expect(api.roster.first, profile());
      expect(app.selected!['en'], 'Cloud');
      expect(app.selected!['lb'], 440110);
      expect(app.selected!['ffbe']['id'], profile()['ffbe']['id']);
      expect(find.text('Use original model'), findsOneWidget);
      expect(tester.takeException(), isNull);
    },
  );
}
