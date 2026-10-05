import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:ffr_vision_studio/screens/cave_placement_dialog.dart';
import 'package:ffr_vision_studio/screens/cave_terrain_preview.dart';
import 'package:ffr_vision_studio/services/acquisition_locations.dart';
import 'package:ffr_vision_studio/services/acquisition.dart';
import 'package:ffr_vision_studio/services/cave_terrain.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  setUpAll(() async {
    await CaveTerrain.bundled;
    await PlacementScene.bundled;
    await AcquisitionCatalog.bundled;
  });
  test('native placement scenery loads paint and directional-independent tree textures', () {
    final scene = PlacementScene.cached!;
    expect(scene.terrainImages, hasLength(74));
    expect(scene.foliage.length, greaterThan(2500));
    expect(scene.images, isNotEmpty);
    expect(
      scene.props.any((p) => p['name'].toString().contains('forest_col')),
      isFalse,
    );
  });
  test('native height interpolation matches decoded game terrain and rejects unknown regions', () async {
    final terrain = await CaveTerrain.bundled;
    expect(terrain.patches, hasLength(74));
    expect(terrain.height(17600, 21400), closeTo(85.103125, 1e-6));
    expect(terrain.height(0, 0), isNull);
    final p = terrain.patches.first;
    expect(
      p.sample(p.x + p.dx * .5, p.y + p.dy * .5),
      closeTo((p.at(0, 0) + p.at(1, 0) + p.at(0, 1) + p.at(1, 1)) / 4, 1e-8),
    );
  });
  testWidgets(
    'entrance selection is accessible before terrain on a short window',
    (tester) async {
      tester.view.physicalSize = const Size(800, 500);
      tester.view.devicePixelRatio = 1;
      addTearDown(tester.view.resetPhysicalSize);
      addTearDown(tester.view.resetDevicePixelRatio);
      final pool = AcquisitionLocations();
      addTearDown(pool.dispose);
      final before = pool.caves.map((c) => c.toJson()).toList();
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: Builder(
              builder: (context) => TextButton(
                onPressed: () => showCavePlacement(
                  context,
                  pool,
                  AcquisitionCatalog.cached!,
                  const Offset(17600, 21400),
                ),
                child: const Text('Open'),
              ),
            ),
          ),
        ),
      );
      await tester.tap(find.text('Open'));
      await tester.pumpAndSettle();
      expect(find.text('Choose cave entrance'), findsOneWidget);
      expect(find.byType(CaveTerrainPreview), findsNothing);
      for (final entrance in AcquisitionCatalog.cached!.entrances) {
        final tile = find.byKey(ValueKey('cave-entrance-${entrance.id}'));
        await tester.ensureVisible(tile);
        await tester.tap(tile);
        await tester.pump();
        expect(
          find.descendant(of: tile, matching: find.byIcon(Icons.check)),
          findsOneWidget,
        );
        expect(tester.takeException(), isNull);
      }
      await tester.tap(find.text('Cancel'));
      await tester.pumpAndSettle();
      expect(pool.caves.map((c) => c.toJson()).toList(), before);
    },
  );
  testWidgets(
    '3D dragging, height and size persist; cancelling an edit leaves the saved cave intact',
    (tester) async {
      tester.view.physicalSize = const Size(1200, 1000);
      tester.view.devicePixelRatio = 1;
      addTearDown(tester.view.resetPhysicalSize);
      addTearDown(tester.view.resetDevicePixelRatio);
      final pool = AcquisitionLocations();
      addTearDown(pool.dispose);
      CaveLocation? result;
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: Builder(
              builder: (context) => TextButton(
                onPressed: () async {
                  result = await showCavePlacement(
                    context,
                    pool,
                    AcquisitionCatalog.cached!,
                    const Offset(17600, 21400),
                  );
                },
                child: const Text('Open'),
              ),
            ),
          ),
        ),
      );
      await tester.tap(find.text('Open'));
      await tester.pumpAndSettle();
      expect(find.byType(CaveTerrainPreview), findsNothing);
      expect(
        tester
            .widget<TextButton>(
              find.byKey(const ValueKey('cave-entrance-next')),
            )
            .onPressed,
        isNull,
      );
      await tester.tap(find.byKey(const ValueKey('cave-entrance-shrine')));
      await tester.pump();
      await tester.tap(find.byKey(const ValueKey('cave-entrance-next')));
      await tester.pumpAndSettle();
      expect(find.text('Size 75%'), findsOneWidget);
      final beforeX =
          (tester
                  .widget<TextField>(find.byKey(const ValueKey('cave-x')))
                  .controller!)
              .text;
      await tester.timedDrag(
        find.byKey(const ValueKey('cave-terrain-drag')),
        const Offset(60, -40),
        const Duration(milliseconds: 400),
      );
      await tester.pump();
      expect(
        tester
            .widget<TextField>(find.byKey(const ValueKey('cave-x')))
            .controller!
            .text,
        isNot(beforeX),
      );
      await tester.enterText(find.byKey(const ValueKey('cave-z')), '12.5');
      await tester.tap(find.byKey(const ValueKey('cave-add')));
      await tester.pumpAndSettle();
      expect(result, isNotNull);
      expect(result!.entrance, 'shrine');
      expect(result!.worldZ, 12.5);
      expect(result!.scale, .75);
      expect(Acquisition.validCave(result!.toJson()), isTrue);
      expect(pool.cave(result!.id)!.toJson(), result!.toJson());
      final original = result!;
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: Builder(
              builder: (context) => TextButton(
                onPressed: () => showCavePlacement(
                  context,
                  pool,
                  AcquisitionCatalog.cached!,
                  Offset(original.worldX, original.worldY),
                  existing: original,
                  save: pool.update,
                ),
                child: const Text('Edit'),
              ),
            ),
          ),
        ),
      );
      await tester.tap(find.text('Edit'));
      await tester.pumpAndSettle();
      await tester.tap(find.byKey(const ValueKey('cave-change-entrance')));
      await tester.pumpAndSettle();
      await tester.tap(find.byKey(const ValueKey('cave-entrance-rock_cave')));
      await tester.pump();
      await tester.tap(find.byKey(const ValueKey('cave-entrance-next')));
      await tester.pumpAndSettle();
      await tester.enterText(find.byKey(const ValueKey('cave-z')), '-100');
      await tester.tap(find.text('Cancel'));
      await tester.pumpAndSettle();
      expect(pool.cave(original.id)!.toJson(), original.toJson());
    },
  );
}
