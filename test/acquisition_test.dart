import 'dart:math';
import 'dart:io';

import 'package:ffr_vision_studio/screens/steps/acquisition_step.dart';
import 'package:ffr_vision_studio/screens/cave_terrain_preview.dart';
import 'package:ffr_vision_studio/screens/unit_screen.dart';
import 'package:ffr_vision_studio/design/theme.dart';
import 'package:ffr_vision_studio/services/acquisition.dart';
import 'package:ffr_vision_studio/services/cave_terrain.dart';
import 'package:ffr_vision_studio/services/acquisition_locations.dart';
import 'package:ffr_vision_studio/services/acquisition_map_data.dart';
import 'package:ffr_vision_studio/services/character_config.dart';
import 'package:ffr_vision_studio/services/paths.dart';
import 'package:ffr_vision_studio/state/app_state.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter/gestures.dart';
import 'package:ffr_vision_studio/screens/acquisition_map.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:provider/provider.dart';

import 'character_config_test.dart' show profile, ConfigApi;

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  setUpAll(() async {
    await AcquisitionMapData.bundled;
    await CaveTerrain.bundled;
    await PlacementScene.bundled;
    await AcquisitionCatalog.bundled;
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
      await CaveTerrain.bundled;
      const viewport = Size(800, 480);
      final tile = map.captures.first;
      final rect = map.captureRect(tile, viewport);
      const expected = {
        'earth_shrine': Offset(594, 177),
        'crystal_cave': Offset(649, 228),
        'mitra_shop': Offset(677, 342),
      };
      expect(tile.size, const Size(9000, 9000));
      // Reported coastal placement stays on the native image, at (794, 300),
      // rather than the old horizontally stretched image's ocean pixel (875).
      final coast = map.toViewport(
        AcquisitionMapData.project(16964.99, 22678.74),
        viewport,
      );
      expect(
        (coast.dx - rect.left) / rect.width * 1024,
        closeTo(794.02553, .0001),
      );
      for (final site in Acquisition.sites) {
        final projected = AcquisitionMapData.project(
          site.worldX!,
          site.worldY!,
        );
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
    AcquisitionLocations? locations,
  }) async {
    final changes = <Map<String, dynamic>>[];
    final pool = locations ?? AcquisitionLocations();
    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: AcquisitionStep(
            unit: unit ?? {'key': 'one'},
            set: changes.add,
            locations: pool,
            removeCave: pool.remove,
          ),
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
      final changes = await mount(
        tester,
        unit: {
          'key': 'one',
          Acquisition.field: const Acquisition(location: 'mitra_shop').toJson(),
        },
      );
      expect(changes, hasLength(1));
      final saved = changes.single[Acquisition.field] as Map;
      expect(find.byKey(const ValueKey('acquisition-marker')), findsNothing);
      expect(find.byKey(const ValueKey('acquisition-shop-list')), findsNothing);
      expect(find.byKey(const ValueKey('acquisition-cave-list')), findsNothing);
      await tester.tap(find.byKey(const ValueKey('acquisition-hide')));
      await tester.pump();
      expect(find.byKey(const ValueKey('acquisition-marker')), findsOneWidget);
      for (final kind in ['shop', 'cave']) {
        final tile = tester.widget<CheckboxListTile>(
          find.byKey(ValueKey('acquisition-kind-$kind')),
        );
        expect(tile.onChanged, isNull);
        expect(tile.value, (saved['cave'] == null ? 'shop' : 'cave') == kind);
        expect(
          tester
              .widget<DropdownButton<String>>(
                find.byKey(ValueKey('acquisition-$kind-list')),
              )
              .onChanged,
          isNull,
        );
      }
      await tester.tap(find.byKey(const ValueKey('acquisition-random')));
      await tester.pump();
      final rerolled = changes.last[Acquisition.field] as Map;
      expect(rerolled['location'], isNot(saved['location']));
      expect(rerolled['random'], isFalse);
      final vendor = AcquisitionCatalog.cached!.vendors.first;
      tester
          .widget<DropdownButton<String>>(
            find.byKey(const ValueKey('acquisition-shop-list')),
          )
          .onChanged!(vendor.id);
      await tester.pump();
      expect((changes.last[Acquisition.field] as Map)['location'], vendor.id);
      await tester.tap(find.byKey(const ValueKey('acquisition-hide')));
      await tester.pump();
      expect(find.byKey(const ValueKey('acquisition-marker')), findsNothing);
      expect(find.byKey(const ValueKey('acquisition-shop-list')), findsNothing);
      expect((changes.last[Acquisition.field] as Map)['location'], vendor.id);
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
    expect(changes, hasLength(1));
    expect(
      (changes.single[Acquisition.field] as Map)['location'],
      'crystal_cave',
    );
    expect(
      tester
          .widget<CheckboxListTile>(
            find.byKey(const ValueKey('acquisition-kind-cave')),
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
    expect(changes, hasLength(1));
    expect(
      (changes.single[Acquisition.field] as Map)['location'],
      'crystal_cave',
    );
    expect(
      tester
          .widget<CheckboxListTile>(
            find.byKey(const ValueKey('acquisition-kind-cave')),
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
    'right-click after zoom and pan saves the clicked coordinates and chosen entrance; cancel preserves the pool',
    (tester) async {
      final locations = AcquisitionLocations();
      addTearDown(locations.dispose);
      final changes = await mount(
        tester,
        locations: locations,
        unit: {
          'key': 'one',
          Acquisition.field: const Acquisition(
            location: 'mitra_shop',
            random: false,
            hideSpoilers: false,
          ).toJson(),
        },
      );
      tester
          .widget<Slider>(find.byKey(const ValueKey('acquisition-zoom')))
          .onChanged!(3);
      await tester.pumpAndSettle();
      await tester.drag(
        find.byKey(const ValueKey('acquisition-map')),
        const Offset(40, 20),
      );
      await tester.pumpAndSettle();
      final box = tester.getRect(
        find.byKey(const ValueKey('acquisition-map-context')),
      );
      final point = box.center + const Offset(12, 20);
      final viewer = tester.widget<InteractiveViewer>(
        find.byKey(const ValueKey('acquisition-map')),
      );
      final native = AcquisitionMapData.cached!.fromViewport(
        viewer.transformationController!.toScene(point - box.topLeft),
        box.size,
      );
      Future<void> open() async {
        final click = await tester.startGesture(
          point,
          kind: PointerDeviceKind.mouse,
          buttons: kSecondaryMouseButton,
        );
        await click.up();
        await tester.pumpAndSettle();
        await tester.tap(find.text('Add cave here'));
        await tester.pumpAndSettle();
      }

      await open();
      expect(
        find.byKey(const ValueKey('cave-entrance-desert_sinkhole')),
        findsOneWidget,
      );
      await tester.tap(find.text('Cancel'));
      await tester.pumpAndSettle();
      expect(locations.caves, hasLength(1));
      await open();
      await tester.enterText(
        find.byKey(const ValueKey('cave-name')),
        'Chosen test cave',
      );
      await tester.tap(find.byKey(const ValueKey('cave-entrance-shrine')));
      await tester.tap(find.byKey(const ValueKey('cave-add')));
      await tester.pumpAndSettle();
      expect(locations.caves, hasLength(2));
      final added = locations.caves.last;
      expect(added.name, 'Chosen test cave');
      expect(added.entrance, 'shrine');
      expect(added.worldX, closeTo(-native.dy, .0001));
      expect(added.worldY, closeTo(native.dx, .0001));
      expect((changes.last[Acquisition.field] as Map)['location'], added.id);
      final model = tester.widget<AcquisitionMap>(find.byType(AcquisitionMap));
      expect(model.site!.id, added.id);
      await tester.tap(find.byKey(const ValueKey('acquisition-hide')));
      await tester.pumpAndSettle();
      expect(
        tester.widget<AcquisitionMap>(find.byType(AcquisitionMap)).caves,
        isEmpty,
      );
      expect(find.byKey(const ValueKey('acquisition-marker')), findsNothing);
    },
  );

  testWidgets(
    'right-click removes a visible selected cave after zoom/pan; cancel and hidden markers preserve it',
    (tester) async {
      final locations = AcquisitionLocations();
      addTearDown(locations.dispose);
      const cave = CaveLocation(
        id: 'cave_remove',
        name: 'Remove test',
        entrance: 'shrine',
        worldX: 17000,
        worldY: 21000,
      );
      await locations.add(cave);
      const neighbor = CaveLocation(
        id: 'cave_neighbor',
        name: 'Other overlapping cave',
        entrance: 'rock_cave',
        worldX: 17000,
        worldY: 21000,
      );
      await locations.add(neighbor);
      await mount(
        tester,
        locations: locations,
        unit: {
          'key': 'one',
          Acquisition.field: Acquisition(
            location: cave.id,
            random: false,
            hideSpoilers: false,
            cave: cave.toJson(),
          ).toJson(),
        },
      );
      tester
          .widget<Slider>(find.byKey(const ValueKey('acquisition-zoom')))
          .onChanged!(4);
      await tester.pumpAndSettle();
      await tester.drag(
        find.byKey(const ValueKey('acquisition-map')),
        const Offset(20, 15),
      );
      await tester.pumpAndSettle();
      Future<void> menu(Offset point) async {
        final click = await tester.startGesture(
          point,
          kind: PointerDeviceKind.mouse,
          buttons: kSecondaryMouseButton,
        );
        await click.up();
        await tester.pumpAndSettle();
      }

      await menu(
        tester.getCenter(find.byKey(const ValueKey('acquisition-marker'))),
      );
      expect(find.text('Remove cave: Remove test'), findsOneWidget);
      await tester.tapAt(const Offset(3, 3));
      await tester.pumpAndSettle();
      expect(locations.cave(cave.id), isNotNull);
      await menu(
        tester.getCenter(
          find.byKey(const ValueKey('acquisition-cave-cave_neighbor')),
        ),
      );
      expect(find.text('Remove cave: Other overlapping cave'), findsOneWidget);
      expect(find.text('Remove cave: Remove test'), findsOneWidget);
      await tester.tap(find.text('Remove cave: Other overlapping cave'));
      await tester.pumpAndSettle();
      expect(locations.cave(neighbor.id), isNull);
      expect(locations.cave(cave.id), isNotNull);
      await tester.tap(find.byKey(const ValueKey('acquisition-hide')));
      await tester.pumpAndSettle();
      await menu(
        tester.getCenter(find.byKey(const ValueKey('acquisition-map-context'))),
      );
      expect(find.textContaining('Remove cave:'), findsNothing);
      await tester.tapAt(const Offset(3, 3));
      await tester.pumpAndSettle();
      await tester.tap(find.byKey(const ValueKey('acquisition-hide')));
      await tester.pumpAndSettle();
      await menu(
        tester.getCenter(find.byKey(const ValueKey('acquisition-marker'))),
      );
      await tester.tap(find.text('Remove cave: Remove test'));
      await tester.pumpAndSettle();
      expect(locations.cave(cave.id), isNull);
      expect(
        tester
            .widget<DropdownButton<String>>(
              find.byKey(const ValueKey('acquisition-shop-list')),
            )
            .value,
        AcquisitionCatalog.cached!.mitraShop,
      );
      expect(tester.takeException(), isNull);
    },
  );

  testWidgets(
    'selecting a custom cave centers its pin; vendors without native coordinates do not get a false pin',
    (tester) async {
      final locations = AcquisitionLocations();
      addTearDown(locations.dispose);
      const cave = CaveLocation(
        id: 'cave_far',
        name: 'Far cave',
        entrance: 'rock_cave',
        worldX: 1000,
        worldY: -5000,
      );
      await locations.add(cave);
      await mount(
        tester,
        locations: locations,
        unit: {
          'key': 'one',
          Acquisition.field: const Acquisition(
            location: 'mitra_shop',
            random: false,
            hideSpoilers: false,
          ).toJson(),
        },
      );
      tester
          .widget<DropdownButton<String>>(
            find.byKey(const ValueKey('acquisition-cave-list')),
          )
          .onChanged!(cave.id);
      await tester.pumpAndSettle();
      final box = tester.getSize(
        find.byKey(const ValueKey('acquisition-map-context')),
      );
      final viewer = tester.widget<InteractiveViewer>(
        find.byKey(const ValueKey('acquisition-map')),
      );
      final center = AcquisitionMapData.cached!.fromViewport(
        viewer.transformationController!.toScene(box.center(Offset.zero)),
        box,
      );
      expect(center.dx, closeTo(cave.worldY, .0001));
      expect(center.dy, closeTo(-cave.worldX, .0001));
      tester
          .widget<DropdownButton<String>>(
            find.byKey(const ValueKey('acquisition-shop-list')),
          )
          .onChanged!('shop_0');
      await tester.pumpAndSettle();
      expect(find.byKey(const ValueKey('acquisition-marker')), findsNothing);
      expect(
        find.text(
          'This vendor has no mapped overworld location in the supplied game data.',
        ),
        findsOneWidget,
      );
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
