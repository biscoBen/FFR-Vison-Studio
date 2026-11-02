import 'dart:io';
import 'dart:ui' show ImageByteFormat;

import 'package:ffr_vision_studio/design/theme.dart';
import 'package:ffr_vision_studio/main.dart' show Shell;
import 'package:ffr_vision_studio/screens/tablet_shards_screen.dart';
import 'package:ffr_vision_studio/services/paths.dart';
import 'package:ffr_vision_studio/services/tablet_shards.dart';
import 'package:ffr_vision_studio/state/app_state.dart';
import 'package:flutter/material.dart';
import 'package:flutter/rendering.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:provider/provider.dart';

void main() {
  final sample = TabletSave({
    2040: {9},
    3211: {3},
  });
  final files = [
    TabletSaveFile('/saves/account/GameSaveData0.sav', DateTime(2026, 11, 2)),
  ];
  setUpAll(() async {
    await TabletShard.bundled();
    await (FontLoader(
      'Barlow',
    )..addFont(rootBundle.load('assets/fonts/Barlow-Regular.ttf'))).load();
    await (FontLoader('BarlowCondensed')
          ..addFont(rootBundle.load('assets/fonts/BarlowCondensed-Bold.ttf')))
        .load();
  });

  Future<void> frame(
    WidgetTester tester,
    Widget child, {
    Size size = const Size(960, 600),
  }) async {
    tester.view.physicalSize = size;
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);
    await tester.pumpWidget(
      MaterialApp(
        theme: Guide.theme(),
        home: Scaffold(
          body: RepaintBoundary(
            key: const Key('preview'),
            child: Material(color: Guide.paper, child: child),
          ),
        ),
      ),
    );
    await tester.runAsync(
      () => Future<void>.delayed(const Duration(milliseconds: 10)),
    );
    await tester.pumpAndSettle();
  }

  testWidgets(
    'shows only missing actors and hides unvisited parts of the same location',
    (tester) async {
      await frame(
        tester,
        TabletShardsScreen(
          findSaves: (_) async => files,
          loadSave: (_) async => sample,
        ),
      );
      expect(find.text('2 / 99 collected'), findsOneWidget);
      expect(find.text('#4'), findsOneWidget);
      expect(find.text('#3'), findsNothing);
      expect(find.text('#75'), findsOneWidget);
      expect(find.text('#68'), findsNothing);
      expect(find.text('#70'), findsNothing);
      expect(tester.takeException(), isNull);
      final preview = Platform.environment['FFR_SHARD_PREVIEW'];
      if (preview != null) {
        final boundary = tester.firstRenderObject<RenderRepaintBoundary>(
          find.byKey(const Key('preview')),
        );
        await tester.runAsync(() async {
          final image = await boundary.toImage();
          final data = await image.toByteData(format: ImageByteFormat.png);
          await File(preview).writeAsBytes(data!.buffer.asUint8List());
          image.dispose();
        });
      }
      await tester.tap(find.byKey(const Key('shards-show-unvisited')));
      await tester.pumpAndSettle();
      await tester.scrollUntilVisible(
        find.text('#68'),
        300,
        scrollable: find.byType(Scrollable).last,
      );
      await tester.pumpAndSettle();
      expect(find.text('#68'), findsOneWidget);
      expect(tester.takeException(), isNull);
    },
  );

  testWidgets(
    'refresh updates the selected slot and a failed read clears stale results',
    (tester) async {
      var reads = 0;
      await frame(
        tester,
        TabletShardsScreen(
          findSaves: (_) async => files,
          loadSave: (_) async {
            reads++;
            if (reads == 1) {
              return sample;
            }
            throw const TabletSaveException('Synthetic unsupported save');
          },
        ),
      );
      expect(find.text('2 / 99 collected'), findsOneWidget);
      await tester.tap(find.text('Refresh'));
      await tester.pumpAndSettle();
      expect(reads, 2);
      expect(find.text('2 / 99 collected'), findsNothing);
      expect(find.text('Synthetic unsupported save'), findsOneWidget);
      expect(tester.takeException(), isNull);
    },
  );

  testWidgets('manual selection works with no discovered saves', (
    tester,
  ) async {
    await frame(
      tester,
      TabletShardsScreen(
        findSaves: (_) async => [],
        pickSave: () async => '/copied/GameSaveData2.sav',
        loadSave: (_) async => sample,
      ),
    );
    expect(find.textContaining('No save slots found.'), findsOneWidget);
    await tester.tap(find.text('Choose save'));
    await tester.pumpAndSettle();
    expect(find.text('2 / 99 collected'), findsOneWidget);
    expect(find.textContaining('GameSaveData2.sav'), findsOneWidget);
    expect(tester.takeException(), isNull);
  });

  testWidgets(
    'Studio exposes the tab and returns to existing vision controls',
    (tester) async {
      final root = Directory.systemTemp.createTempSync('shard-shell-');
      final app = AppState(
        hostBase: 'https://unused.invalid/',
        appPaths: AppPaths.at(root.path),
      )..phase = Phase.ready;
      addTearDown(app.dispose);
      addTearDown(() => root.deleteSync(recursive: true));
      await frame(
        tester,
        ChangeNotifierProvider.value(value: app, child: const Shell()),
        size: const Size(1320, 860),
      );
      expect(find.byKey(const Key('added-visions')), findsOneWidget);
      await tester.tap(find.text('2  TABLET SHARDS'));
      await tester.pump();
      await tester.runAsync(
        () => Future<void>.delayed(const Duration(milliseconds: 10)),
      );
      await tester.pumpAndSettle();
      expect(find.text('Choose save'), findsOneWidget);
      await tester.tap(find.text('1  VISIONS'));
      await tester.pumpAndSettle();
      expect(find.byKey(const Key('added-visions')), findsOneWidget);
      expect(app.units, isEmpty);
      expect(tester.takeException(), isNull);
    },
  );
}
