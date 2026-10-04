import 'dart:math';
import 'dart:io';

import 'package:ffr_vision_studio/screens/steps/acquisition_step.dart';
import 'package:ffr_vision_studio/screens/unit_screen.dart';
import 'package:ffr_vision_studio/design/theme.dart';
import 'package:ffr_vision_studio/services/acquisition.dart';
import 'package:ffr_vision_studio/services/acquisition_map_data.dart';
import 'package:ffr_vision_studio/services/character_config.dart';
import 'package:ffr_vision_studio/services/paths.dart';
import 'package:ffr_vision_studio/state/app_state.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:provider/provider.dart';

import 'character_config_test.dart' show profile, ConfigApi;

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  setUpAll(() async {
    await AcquisitionMapData.bundled;
    await (FontLoader(
      'Barlow',
    )..addFont(rootBundle.load('assets/fonts/Barlow-Regular.ttf'))).load();
    await (FontLoader('BarlowCondensed')
          ..addFont(rootBundle.load('assets/fonts/BarlowCondensed-Bold.ttf')))
        .load();
  });

  test(
    'native capture and marker projection agree for the three demo sites',
    () async {
      final map = await AcquisitionMapData.bundled;
      const viewport = Size(800, 480);
      final tile = map.captures.first;
      final rect = map.captureRect(tile, viewport);
      const expected = {
        'earth_shrine': Offset(617, 177),
        'crystal_cave': Offset(688, 228),
        'mitra_shop': Offset(725, 342),
      };
      for (final site in Acquisition.sites) {
        final projected = AcquisitionMapData.project(site.worldX, site.worldY);
        final point = map.toViewport(projected, viewport);
        expect(rect.contains(point), isTrue);
        expect(
          (point.dx - rect.left) / rect.width * 1024,
          closeTo(expected[site.id]!.dx, 1),
        );
        expect(
          (point.dy - rect.top) / rect.height * 1024,
          closeTo(expected[site.id]!.dy, 1),
        );
        expect(
          (map.fromViewport(point, viewport) - projected).distance,
          lessThan(.0001),
        );
      }
    },
  );
  test(
    'defaults hide the random selection; both Random transitions reroll',
    () {
      var value = Acquisition.initial(rng: Random(1));
      expect(value.random, isTrue);
      expect(value.hideSpoilers, isTrue);
      for (final random in [false, true, false, true]) {
        final previous = value.location;
        value = value.reroll(random, rng: Random(2));
        expect(value.random, random);
        expect(value.location, isNot(previous));
        expect(value.hideSpoilers, isTrue);
      }
    },
  );

  test('preferences survive single/bulk config save and slot restoration', () {
    final unit = profile();
    final settings = const Acquisition(
      location: 'earth_shrine',
      random: false,
      hideSpoilers: false,
    ).toJson();
    unit[Acquisition.field] = settings;
    expect(
      CharacterConfig.decode(CharacterConfig.encode(unit))[Acquisition.field],
      settings,
    );
    final restored = CharacterConfig.decodeAll(
      CharacterConfig.encodeAll([unit]),
    );
    expect(
      CharacterConfig.restore(restored.single, [profile()])[Acquisition.field],
      settings,
    );
    for (final value in [
      {...settings, 'location': 'unknown'},
      {...settings, 'random': 'false'},
      {...settings, 'hideSpoilers': null},
      {...settings, 'version': 2},
    ]) {
      expect(
        () => CharacterConfig.encode({...unit, Acquisition.field: value}),
        throwsFormatException,
      );
    }
    expect(() => CharacterConfig.encode(profile()), returnsNormally);
  });

  Future<List<Map<String, dynamic>>> mount(
    WidgetTester tester, {
    Map<String, dynamic>? unit,
  }) async {
    final changes = <Map<String, dynamic>>[];
    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: AcquisitionStep(unit: unit ?? {'key': 'one'}, set: changes.add),
        ),
      ),
    );
    await tester.runAsync(() async {
      await Future<void>.delayed(Duration.zero);
    });
    await tester.pumpAndSettle();
    return changes;
  }

  testWidgets(
    'spoilers hide choices and marker; revealing shows checked disabled choice',
    (tester) async {
      final changes = await mount(tester);
      expect(changes, hasLength(1));
      final saved = changes.single[Acquisition.field] as Map;
      expect(find.byKey(const ValueKey('acquisition-marker')), findsNothing);
      for (final site in Acquisition.sites) {
        expect(
          find.byKey(ValueKey('acquisition-site-${site.id}')),
          findsNothing,
        );
      }
      await tester.tap(find.byKey(const ValueKey('acquisition-hide')));
      await tester.pump();
      expect(find.byKey(const ValueKey('acquisition-marker')), findsOneWidget);
      for (final site in Acquisition.sites) {
        final tile = tester.widget<CheckboxListTile>(
          find.byKey(ValueKey('acquisition-site-${site.id}')),
        );
        expect(tile.onChanged, isNull);
        expect(tile.value, site.id == saved['location']);
      }
      await tester.tap(find.byKey(const ValueKey('acquisition-random')));
      await tester.pump();
      final rerolled = changes.last[Acquisition.field] as Map;
      expect(rerolled['location'], isNot(saved['location']));
      expect(rerolled['random'], isFalse);
      await tester.tap(
        find.byKey(const ValueKey('acquisition-site-mitra_shop')),
      );
      await tester.pump();
      expect(
        (changes.last[Acquisition.field] as Map)['location'],
        'mitra_shop',
      );
      await tester.tap(find.byKey(const ValueKey('acquisition-hide')));
      await tester.pump();
      expect(find.byKey(const ValueKey('acquisition-marker')), findsNothing);
      expect(
        find.byKey(const ValueKey('acquisition-site-mitra_shop')),
        findsNothing,
      );
      expect(
        (changes.last[Acquisition.field] as Map)['location'],
        'mitra_shop',
      );
    },
  );

  testWidgets('restoring and moving between visions preserves each selection', (
    tester,
  ) async {
    final saved = const Acquisition(
      location: 'earth_shrine',
      random: false,
      hideSpoilers: false,
    ).toJson();
    var changes = await mount(
      tester,
      unit: {'key': 'one', Acquisition.field: saved},
    );
    expect(changes, isEmpty);
    expect(
      tester
          .widget<CheckboxListTile>(
            find.byKey(const ValueKey('acquisition-site-earth_shrine')),
          )
          .value,
      isTrue,
    );
    changes = await mount(tester, unit: {'key': 'two'});
    expect(changes, hasLength(1));
    expect(find.byKey(const ValueKey('acquisition-marker')), findsNothing);
    changes = await mount(
      tester,
      unit: {'key': 'one', Acquisition.field: saved},
    );
    expect(changes, isEmpty);
    expect(
      tester
          .widget<CheckboxListTile>(
            find.byKey(const ValueKey('acquisition-site-earth_shrine')),
          )
          .value,
      isTrue,
    );
  });

  testWidgets(
    'map zoom slider, mouse dragging and reset use the same transform',
    (tester) async {
      await mount(
        tester,
        unit: {
          'key': 'one',
          Acquisition.field: const Acquisition(
            location: 'earth_shrine',
            hideSpoilers: false,
          ).toJson(),
        },
      );
      final viewer = tester.widget<InteractiveViewer>(
        find.byKey(const ValueKey('acquisition-map')),
      );
      tester
          .widget<Slider>(find.byKey(const ValueKey('acquisition-zoom')))
          .onChanged!(2);
      await tester.pump();
      final controller = viewer.transformationController!;
      expect(controller.value.getMaxScaleOnAxis(), 2);
      expect(
        tester.getSize(find.byKey(const ValueKey('acquisition-marker'))).width,
        32,
      );
      final before = controller.value.clone();
      await tester.drag(
        find.byKey(const ValueKey('acquisition-map')),
        const Offset(60, 40),
      );
      await tester.pump();
      expect(controller.value, isNot(before));
      expect(
        tester
            .widget<Slider>(find.byKey(const ValueKey('acquisition-zoom')))
            .value,
        2,
      );
      await tester.tap(find.text('Full map'));
      await tester.pump();
      expect(controller.value.isIdentity(), isTrue);
      expect(
        tester
            .widget<Slider>(find.byKey(const ValueKey('acquisition-zoom')))
            .value,
        1,
      );
      expect(tester.takeException(), isNull);
    },
  );

  testWidgets(
    'the added-vision tab stays accessible at minimum width and saves through AppState',
    (tester) async {
      tester.view.physicalSize = const Size(960, 600);
      tester.view.devicePixelRatio = 1;
      addTearDown(tester.view.resetPhysicalSize);
      addTearDown(tester.view.resetDevicePixelRatio);
      final dir = Directory.systemTemp.createTempSync('acquisition-editor-');
      final unit = profile();
      final api = ConfigApi([unit]);
      final app =
          AppState(hostBase: 'http://unused', appPaths: AppPaths.at(dir.path))
            ..api = api
            ..units = [unit]
            ..selectedKey = unit['key'] as String
            ..catalog = {'skills': [], 'passives': [], 'icons': []};
      addTearDown(() {
        app.dispose();
        dir.deleteSync(recursive: true);
      });
      await tester.pumpWidget(
        ChangeNotifierProvider.value(
          value: app,
          child: MaterialApp(
            theme: Guide.theme(),
            home: const Scaffold(body: UnitScreen()),
          ),
        ),
      );
      await tester.pumpAndSettle();
      await tester.ensureVisible(find.text('6  ACQUISITION'));
      await tester.tap(find.text('6  ACQUISITION'));
      await tester.pump();
      await tester.runAsync(() async {
        await Future<void>.delayed(Duration.zero);
      });
      await tester.pumpAndSettle();
      expect(find.byKey(const ValueKey('acquisition-hide')), findsOneWidget);
      await tester.tap(find.byKey(const ValueKey('acquisition-hide')));
      await tester.pump();
      await app.save();
      final preferences = api.roster.single[Acquisition.field] as Map;
      expect(preferences['hideSpoilers'], isFalse);
      expect(preferences['random'], isTrue);
      expect(
        CharacterConfig.decode(
          CharacterConfig.encode(api.roster.single),
        )[Acquisition.field],
        preferences,
      );
      expect(tester.takeException(), isNull);
      await app.shutdown();
    },
  );
}
