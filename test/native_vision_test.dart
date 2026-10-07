import 'dart:io';
import 'dart:ui' show PointerDeviceKind;

import 'package:ffr_vision_studio/design/theme.dart';
import 'package:ffr_vision_studio/design/widgets.dart';
import 'package:ffr_vision_studio/screens/home_screen.dart';
import 'package:ffr_vision_studio/screens/unit_screen.dart';
import 'package:ffr_vision_studio/services/bundled_features.dart';
import 'package:ffr_vision_studio/services/character_config.dart';
import 'package:ffr_vision_studio/services/paths.dart';
import 'package:ffr_vision_studio/state/app_state.dart';
import 'package:flutter/material.dart';
import 'package:flutter/gestures.dart' show kSecondaryMouseButton;
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:provider/provider.dart';

import 'character_config_test.dart' show ConfigApi, profile, clone;

Map<String, dynamic> originalFixture({int id = 13110, String name = 'Cloud'}) {
  final u = profile()
    ..remove('ffbe')
    ..remove('lb_custom')
    ..remove('custom');
  u.addAll({
    'key': 'native_$id',
    'id': id,
    'donor': id,
    'en': name,
    'jp': name,
    'lb': id == 13024 ? 414090 : 440110,
    'command': {
      'id': id == 13024 ? 200 : 202,
      'en': '$name skills',
      'desc': '',
    },
    'master': {
      'id': id == 13024 ? 1302400 : 500,
      'en': 'Spirit of $name',
      'desc': '',
    },
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
    'id': id,
    'baseline': clone(u),
    'synchroCaps': List.filled(10, 5),
  };
  return u;
}

class NativeApi extends ConfigApi {
  NativeApi(super.roster);
  bool maxMr = false;
  bool practiceBattle = false;
  @override
  Future<Map<String, dynamic>> saveAbilityModes({required bool showUnverified, required bool useChanges}) async =>
      {'schema': 1, 'showUnverified': showUnverified, 'useChanges': useChanges};
  bool borrowedVisuals = true;
  bool failVisualSettings = false;
  @override
  Future<Map<String, dynamic>> saveSephiraVisualSettings({required bool useBorrowedSkillVisuals}) async {
    if (failVisualSettings) throw StateError('Settings write failed.');
    borrowedVisuals = useBorrowedSkillVisuals;
    return {'schema': 1, 'useBorrowedSkillVisuals': borrowedVisuals};
  }
  @override
  Future<bool> testingMaxMr() async => maxMr;
  @override
  Future<void> saveTestingMaxMr(bool value) async { maxMr = value; }
  @override
  Future<bool> testingPracticeBattle() async => practiceBattle;
  @override
  Future<void> saveTestingPracticeBattle(bool value) async { practiceBattle = value; }
  @override
  Future<bool> fieldLeader() async => fieldLeaderValue;
  bool fieldLeaderValue = false;
  @override
  Future<void> saveFieldLeader(bool value) async { fieldLeaderValue = value; }
  @override
  Future<Map<String, dynamic>> nativeVision(int id) async =>
      originalFixture(id: id, name: id == 13024 ? 'Tronn' : 'Cloud');
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

  test('lower-ID original can change models, edit MR and round-trip single and bulk configs', () async {
    final added = clone(api.roster.first);
    final native = await app.editNativeVision(13024, appearance: profile());
    expect(native['id'], 13024);
    expect(native['donor'], 13024);
    expect(native['lb'], 414090);
    native['synchro'][0].add(['PassiveSkill', 1234, 8]);
    app.update(native);
    await app.save();
    final single = CharacterConfig.decode(CharacterConfig.encode(native));
    expect(single, native);
    final all = CharacterConfig.decodeAll(
      CharacterConfig.encodeAll([added, native]),
    );
    expect(
      CharacterConfig.restoreAll(
        all,
        api.roster,
        api.roster.cast<Map<String, dynamic>?>(),
      ),
      [added, native],
    );
    expect(api.roster.first, added);
    app.useOriginalModel(native);
    await app.save();
    expect(api.roster.last['id'], 13024);
    expect(api.roster.last['ffbe'], isNull);
    expect(api.roster.last['synchro'][0], [
      ['PassiveSkill', 1234, 8],
    ]);
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

  Future<void> rightClickVision(WidgetTester tester, String name) async {
    final card = find.descendant(of: find.byKey(const Key('added-visions')), matching: find.text(name.toUpperCase()));
    await tester.tap(card, kind: PointerDeviceKind.mouse, buttons: kSecondaryMouseButton);
    if (app.building) { await tester.pump(const Duration(milliseconds: 300)); }
    else { await tester.pumpAndSettle(); }
    expect(find.text('Remove vision'), findsOneWidget);
    expect(app.selectedKey, isNull);
  }

  testWidgets('added vision context menu confirms removal and supports cancelling', (tester) async {
    await show(tester);
    final before = clone(api.roster);
    final name = api.roster.first['en'] as String;
    await rightClickVision(tester, name);
    await tester.tap(find.text('Remove vision'));
    await tester.pumpAndSettle();
    expect(find.text('Remove $name from the mod?'), findsOneWidget);
    await tester.tap(find.text('Keep'));
    await tester.pumpAndSettle();
    expect(api.roster, before);
    await rightClickVision(tester, name);
    await tester.tap(find.text('Remove vision'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Remove'));
    await wait(tester, () => app.units.isEmpty);
    expect(api.roster, isEmpty);
    expect(app.nativeVisions, [originalFixture()]);
  });

  testWidgets('removing an acquired original returns it to Defaults', (tester) async {
    api.roster.add(originalFixture()..['testAcquire'] = true);
    app.units = clone(api.roster) as List;
    await show(tester);
    await rightClickVision(tester, 'Cloud');
    await tester.tap(find.text('Remove vision'));
    await tester.pumpAndSettle();
    expect(find.text('Revert Cloud to original?'), findsOneWidget);
    await tester.tap(find.text('Revert to original'));
    await wait(tester, () => !app.units.any((u) => u['native'] != null));
    expect(api.roster, hasLength(1));
    expect(find.descendant(of: find.byKey(const Key('default-visions')), matching: find.text('CLOUD')), findsOneWidget);
  });

  testWidgets('context removal is disabled during builds and preserves cave-required Fina', (tester) async {
    await show(tester);
    app.buildState = {'running': true};
    app.notifyListeners();
    await tester.pump();
    await rightClickVision(tester, api.roster.first['en'] as String);
    expect(tester.widget<PopupMenuItem<String>>(find.byType(PopupMenuItem<String>)).enabled, isFalse);
    await tester.sendKeyEvent(LogicalKeyboardKey.escape);
    await tester.pump(const Duration(milliseconds: 300));
    app.buildState = null;
    app.crystalCave = true;
    String? removalNotice;
    app.addListener(() { removalNotice ??= app.notice; });
    app.notifyListeners();
    await tester.pumpAndSettle();
    await rightClickVision(tester, api.roster.first['en'] as String);
    await tester.tap(find.text('Remove vision'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Remove'));
    await wait(tester, () => removalNotice != null);
    expect(app.units, hasLength(1));
    expect(api.roster, hasLength(1));
    expect(removalNotice, contains('Turn off Crystal Fina cave'));
    await tester.pump(const Duration(seconds: 6));
  });

  testWidgets('dragging original visions enables acquisition and dragging back keeps edits', (tester) async {
    await show(tester);
    final before = clone(api.roster.first);
    final source = find.byKey(const ValueKey('drag-native-13110'));
    final top = find.byKey(const Key('added-visions'));
    await tester.dragFrom(tester.getCenter(source), tester.getCenter(top) - tester.getCenter(source));
    await wait(tester, () => app.units.any((u) => u['testAcquire'] == true));
    expect(app.selectedKey, isNull);
    expect(api.roster.first, before);
    final original = api.roster.last;
    expect(original['id'], 13110);
    expect(original['donor'], 13110);
    expect(original['native']['baseline'], originalFixture()['native']['baseline']);
    expect(find.descendant(of: top, matching: find.text('CLOUD')), findsOneWidget);
    final saved = CharacterConfig.decode(CharacterConfig.encode(original as JsonMap));
    expect(saved['testAcquire'], isTrue);
    final edited = CharacterConfig.copy(original)..['stats']['Attack'] = 999;
    app.update(edited);
    final defaults = find.byKey(const Key('default-visions'));
    await tester.dragFrom(tester.getCenter(source), tester.getCenter(defaults) - tester.getCenter(source));
    await wait(tester, () => app.units.last['testAcquire'] == null);
    expect(api.roster, hasLength(2));
    expect(api.roster.last['stats']['Attack'], 999);
    expect(find.descendant(of: defaults, matching: find.text('CLOUD')), findsOneWidget);
  });

  test('acquisition is idempotent, preserves pending edits and is blocked during builds', () async {
    final edited = CharacterConfig.copy(app.units.first as JsonMap)..['stats']['Attack'] = 222;
    app.update(edited);
    await app.editNativeVision(13110, testAcquire: true, selectEditor: false);
    await app.editNativeVision(13110, testAcquire: true, selectEditor: false);
    expect(api.roster, hasLength(2));
    expect(api.roster.first['stats']['Attack'], 222);
    app.buildState = {'running': true};
    await expectLater(app.editNativeVision(13110, testAcquire: false), throwsStateError);
    await expectLater(app.setTestingMaxMr(true), throwsStateError);
    await expectLater(app.setTestingPracticeBattle(true), throwsStateError);
    expect(api.roster.last['testAcquire'], isTrue);
  });

  testWidgets('MR testing persists both toggle states without changing the roster', (tester) async {
    final before = clone(api.roster);
    await show(tester);
    final control = find.byKey(const Key('testing-max-mr'));
    await tester.ensureVisible(control);
    await tester.tap(control);
    await wait(tester, () => app.testingMaxMr);
    expect(api.maxMr, isTrue);
    expect(api.roster, before);
    await tester.tap(control);
    await wait(tester, () => !app.testingMaxMr);
    expect(api.maxMr, isFalse);
    final invalid = profile()..['testAcquire'] = true;
    expect(() => CharacterConfig.validate(invalid), throwsFormatException);
  });

  testWidgets('ability controls preserve roster and remembered repairs while disabled', (tester) async {
    final before = clone(api.roster);
    await show(tester);
    final toggle = find.byKey(const Key('show-unverified-skills'));
    final checkbox = find.byKey(const Key('use-ability-changes'));
    await tester.ensureVisible(toggle);
    expect(tester.widget<CheckboxListTile>(checkbox).onChanged, isNull);
    await tester.tap(toggle);
    await wait(tester, () => app.showUnverifiedSkills);
    expect(app.useAbilityChanges, isFalse);
    await tester.tap(checkbox);
    await wait(tester, () => app.useAbilityChanges);
    await tester.tap(toggle);
    await wait(tester, () => !app.showUnverifiedSkills);
    expect(app.useAbilityChanges, isTrue);
    expect(tester.widget<CheckboxListTile>(checkbox).onChanged, isNull);
    expect(app.catalog!['abilityModes'], {'schema': 1, 'showUnverified': false, 'useChanges': true});
    expect(api.roster, before);
    app.buildState = {'running': true};
    app.notifyListeners();
    await tester.pump();
    expect(tester.widget<SwitchListTile>(toggle).onChanged, isNull);
  });

  testWidgets('shop battle works without a roster and preserves MR testing', (tester) async {
    api.roster.clear(); app.units.clear();
    await show(tester);
    final buildButton = find.ancestor(of: find.text('Build without installing'), matching: find.byType(GuideButton));
    expect(tester.widget<GuideButton>(buildButton).onPressed, isNull);
    final control = find.byKey(const Key('testing-practice-battle'));
    await tester.ensureVisible(control);
    await tester.tap(control);
    await wait(tester, () => app.testingPracticeBattle);
    expect(api.practiceBattle, isTrue);
    expect(tester.widget<GuideButton>(buildButton).onPressed, isNotNull);
    expect(api.roster, isEmpty);
    await app.setTestingMaxMr(true);
    await tester.tap(control);
    await wait(tester, () => !app.testingPracticeBattle);
    expect(api.practiceBattle, isFalse);
    expect(api.maxMr, isTrue);
  });

  testWidgets('Sephira visuals switch independently without resetting saved kits', (tester) async {
    final before = clone(api.roster);
    await show(tester);
    final control = find.byKey(const Key('sephira-borrowed-skill-visuals'));
    await tester.ensureVisible(control);
    expect(app.useSephiraBorrowedVisuals, isTrue);
    expect(app.showUnverifiedSkills, isFalse);
    expect(app.useAbilityChanges, isFalse);
    expect(tester.widget<SwitchListTile>(control).onChanged, isNotNull);
    await tester.tap(control);
    await wait(tester, () => !app.useSephiraBorrowedVisuals);
    expect(api.borrowedVisuals, isFalse);
    expect(api.roster, before);
    expect(app.units, before);
    expect(app.showUnverifiedSkills, isFalse);
    expect(app.useAbilityChanges, isFalse);
    await app.setAbilityModes(showUnverified: true, useChanges: true);
    expect(app.useSephiraBorrowedVisuals, isFalse);
    await tester.tap(control);
    await wait(tester, () => app.useSephiraBorrowedVisuals);
    expect(api.borrowedVisuals, isTrue);
    expect(app.useAbilityChanges, isTrue);
    expect(api.roster, before);
    app.buildState = {'running': true}; app.notifyListeners();
    await tester.pump();
    expect(tester.widget<SwitchListTile>(control).onChanged, isNull);
    await expectLater(app.setSephiraBorrowedVisuals(false), throwsStateError);
    expect(api.borrowedVisuals, isTrue);
  });

  test('Sephira visuals preserve the current selection after a failed settings save', () async {
    api.failVisualSettings = true;
    final before = clone(api.roster);
    await expectLater(app.setSephiraBorrowedVisuals(false), throwsStateError);
    expect(app.useSephiraBorrowedVisuals, isTrue);
    expect(api.roster, before);
  });

  testWidgets('controller cycling toggle persists with an empty roster and retains other settings', (tester) async {
    api.roster.clear(); app.units.clear();
    await show(tester);
    final control = find.byKey(const Key('field-leader-cycle'));
    await tester.ensureVisible(control);
    await tester.tap(control);
    await wait(tester, () => app.fieldLeader);
    expect(api.fieldLeaderValue, isTrue);
    expect(api.roster, isEmpty);
    final buildButton = find.ancestor(of: find.text('Build without installing'), matching: find.byType(GuideButton));
    expect(tester.widget<GuideButton>(buildButton).onPressed, isNotNull);
    await app.setTestingMaxMr(true);
    await tester.tap(control);
    await wait(tester, () => !app.fieldLeader);
    expect(api.fieldLeaderValue, isFalse);
    expect(api.maxMr, isTrue);
    app.buildState = {'running': true};
    await expectLater(app.setFieldLeader(true), throwsStateError);
  });

  testWidgets(
    'reverting from the home popup restores the original and preserves other roster edits',
    (tester) async {
      final cloud = (await tester.runAsync(
        () => app.editNativeVision(13110, appearance: profile()),
      ))!;
      cloud['stats']['Attack'] = 999;
      cloud['awakening'][0].add(['ActiveSkill', 485300]);
      cloud['synchro'][0].add(['PassiveSkill', 1234, 8]);
      cloud['lb'] = 485300;
      app.update(cloud);

      final tronn = (await tester.runAsync(() => app.editNativeVision(13024)))!;
      tronn['stats']['Attack'] = 222;
      tronn['synchro'][0].add(['PassiveSkill', 1234, 3]);
      app.update(tronn);
      final added = CharacterConfig.copy(app.units.first as JsonMap)
        ..['stats']['Attack'] = 333;
      app.update(added);
      app.select(null);
      final remaining = clone(
        app.units.where((u) => u['key'] != cloud['key']).toList(),
      );

      await show(tester);
      await tester.tap(find.text('CLOUD'));
      await tester.pumpAndSettle();
      await tester.tap(find.widgetWithText(GuideButton, 'Revert to original'));
      await tester.pumpAndSettle();
      expect(find.text('Revert Cloud to original?'), findsOneWidget);
      expect(
        find.textContaining(
          'The next build/install applies the original vision',
        ),
        findsOneWidget,
      );
      await tester.tap(find.widgetWithText(GuideButton, 'Revert to original'));
      await wait(
        tester,
        () => app.units.every((u) => u['key'] != cloud['key']),
      );
      expect(app.units, remaining);
      expect(api.roster, remaining);
      expect(find.text('CLOUD'), findsOneWidget);
      expect(find.text('Game vision · defaults'), findsOneWidget);

      await tester.tap(find.text('CLOUD'));
      await tester.pumpAndSettle();
      expect(
        tester
            .widget<GuideButton>(
              find.widgetWithText(GuideButton, 'Revert to original'),
            )
            .onPressed,
        isNull,
      );
      await tester.tap(find.widgetWithText(GuideButton, 'Edit vision'));
      await wait(tester, () => app.selected != null);
      expect(app.selected, originalFixture());
      expect(api.roster, [...remaining, originalFixture()]);
      expect(tester.takeException(), isNull);
    },
  );

  testWidgets('cancelling a revert keeps the model and all vision edits', (
    tester,
  ) async {
    final cloud = (await tester.runAsync(
      () => app.editNativeVision(13110, appearance: profile()),
    ))!;
    cloud['stats']['Attack'] = 999;
    cloud['synchro'][0].add(['PassiveSkill', 1234, 8]);
    app.update(cloud);
    await tester.runAsync(app.save);
    app.select(null);
    final before = clone(app.units);
    final saves = api.saves;

    await show(tester);
    await tester.tap(find.text('CLOUD'));
    await tester.pumpAndSettle();
    await tester.tap(find.widgetWithText(GuideButton, 'Revert to original'));
    await tester.pumpAndSettle();
    await tester.tap(find.widgetWithText(GuideButton, 'Keep'));
    await tester.pumpAndSettle();

    expect(app.units, before);
    expect(api.roster, before);
    expect(api.saves, saves);
    expect(find.text('CLOUD'), findsOneWidget);
    expect(find.text('Game vision · your edits'), findsOneWidget);
    expect(tester.takeException(), isNull);
  });

  testWidgets('the last reverted vision can still be rebuilt and installed', (
    tester,
  ) async {
    api.roster = [];
    app.units = [];
    app.modInstalled = true;
    final cloud = (await tester.runAsync(() => app.editNativeVision(13110)))!;
    cloud['stats']['Attack'] = 999;
    app.update(cloud);
    app.select(null);

    await show(tester);
    await tester.tap(find.text('CLOUD'));
    await tester.pumpAndSettle();
    await tester.tap(find.widgetWithText(GuideButton, 'Revert to original'));
    await tester.pumpAndSettle();
    await tester.tap(find.widgetWithText(GuideButton, 'Revert to original'));
    await wait(tester, () => app.units.isEmpty);

    expect(api.roster, isEmpty);
    expect(find.text('CLOUD'), findsOneWidget);
    expect(
      tester
          .widget<GoButton>(
            find.widgetWithText(GoButton, 'INSTALL INTO THE GAME'),
          )
          .onPressed,
      isNotNull,
    );
    expect(
      tester
          .widget<GuideButton>(
            find.widgetWithText(GuideButton, 'Build without installing'),
          )
          .onPressed,
      isNotNull,
    );
    expect(tester.takeException(), isNull);
  });

  testWidgets('revert is disabled for untouched visions and during a build', (
    tester,
  ) async {
    await show(tester);
    await tester.tap(find.text('CLOUD'));
    await tester.pumpAndSettle();
    final revert = find.widgetWithText(GuideButton, 'Revert to original');
    expect(tester.widget<GuideButton>(revert).onPressed, isNull);
    await tester.tap(revert);
    await tester.pumpAndSettle();
    expect(api.roster, [profile()]);
    expect(api.saves, 0);
    await tester.tap(find.widgetWithText(GuideButton, 'Cancel'));
    await tester.pumpAndSettle();

    await tester.runAsync(() => app.editNativeVision(13110));
    app.buildState = {'running': true};
    app.select(null);
    await tester.pump();
    final before = clone(api.roster);
    final saves = api.saves;
    await tester.tap(find.text('CLOUD'));
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 300));
    expect(tester.widget<GuideButton>(revert).onPressed, isNull);
    await tester.tap(revert);
    await tester.pump(const Duration(milliseconds: 300));
    expect(app.units, before);
    expect(api.roster, before);
    expect(api.saves, saves);
    expect(tester.takeException(), isNull);
  });

  testWidgets(
    'opening screen lists untouched game visions; viewing Resonance never creates a custom LB',
    (tester) async {
      await show(tester);
      expect(find.text('CLOUD'), findsOneWidget);
      expect(find.text('ADDED VISIONS'), findsOneWidget);
      expect(find.text('DEFAULT VISIONS'), findsOneWidget);
      expect(
        find.descendant(
          of: find.byKey(const Key('default-visions')),
          matching: find.text('CLOUD'),
        ),
        findsOneWidget,
      );
      expect(
        find.descendant(
          of: find.byKey(const Key('added-visions')),
          matching: find.text('CLOUD'),
        ),
        findsNothing,
      );
      expect(api.roster, hasLength(1));
      await tester.tap(find.text('CLOUD'));
      await tester.pumpAndSettle();
      await tester.tap(find.widgetWithText(GuideButton, 'Edit vision'));
      await wait(tester, () => app.selected != null);
      expect(find.text('Change model'), findsOneWidget);
      await tester.tap(find.text('4  RESONANCE'));
      await tester.pumpAndSettle();
      expect(find.text('Climhazzard'), findsOneWidget);
      expect(
        find.text('Climhazzard (Unverified) — Source: Cloud'),
        findsOneWidget,
      );
      expect(app.selected!['lb_custom'], isNull);
      expect(api.roster.last, originalFixture());
      expect(tester.takeException(), isNull);
    },
  );

  testWidgets(
    'lower-ID original appears on the opening screen and can be edited',
    (tester) async {
      app.nativeVisions = [originalFixture(id: 13024, name: 'Tronn')];
      await show(tester);
      expect(find.text('TRONN'), findsOneWidget);
      await tester.tap(find.text('TRONN'));
      await tester.pumpAndSettle();
      await tester.tap(find.widgetWithText(GuideButton, 'Edit vision'));
      await wait(tester, () => app.selected != null);
      expect(app.selected!['id'], 13024);
      expect(find.text('Change model'), findsOneWidget);
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
