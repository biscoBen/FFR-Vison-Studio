import 'dart:convert';

import 'package:ffr_vision_studio/design/description_details.dart';
import 'package:ffr_vision_studio/design/theme.dart';
import 'package:ffr_vision_studio/design/widgets.dart';
import 'package:ffr_vision_studio/screens/steps/abilities_step.dart';
import 'package:ffr_vision_studio/screens/steps/bonuses_step.dart';
import 'package:ffr_vision_studio/screens/steps/mr_step.dart';
import 'package:ffr_vision_studio/state/app_state.dart';
import 'package:flutter/gestures.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:provider/provider.dart';

import 'catalog_descriptions_test.dart' show variantCatalog;
import 'catalog_visibility_test.dart' show CatalogState;

void main() {
  setUpAll(() async {
    await (FontLoader(
      'Barlow',
    )..addFont(rootBundle.load('assets/fonts/Barlow-Regular.ttf'))).load();
    await (FontLoader('BarlowCondensed')
          ..addFont(rootBundle.load('assets/fonts/BarlowCondensed-Bold.ttf')))
        .load();
  });

  Future<void> showPage(
    WidgetTester tester,
    String step,
    Map<String, dynamic> unit,
    Map<String, dynamic> catalog,
  ) async {
    tester.view.physicalSize = const Size(1500, 1100);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);
    final app = CatalogState()..catalog = catalog;
    addTearDown(app.dispose);
    await tester.pumpWidget(
      ChangeNotifierProvider<AppState>.value(
        value: app,
        child: MaterialApp(
          theme: Guide.theme(),
          home: Scaffold(
            body: StatefulBuilder(
              builder: (_, setState) {
                void update(Map<String, dynamic> patch) =>
                    setState(() => unit.addAll(patch));
                return switch (step) {
                  'abilities' => AbilitiesStep(unit: unit, set: update),
                  'passives' => BonusesStep(unit: unit, set: update),
                  _ => MrStep(unit: unit, set: update),
                };
              },
            ),
          ),
        ),
      ),
    );
    await tester.pumpAndSettle();
  }

  Finder preview(String step) => find.byWidgetPredicate(
    (widget) =>
        widget is DescriptionDetails &&
        widget.title == (step == 'passives' ? 'Grit' : 'Fire') &&
        widget.description.contains(
          step == 'passives' ? 'Equipment cost: 20' : 'Power: 17',
        ),
  );

  for (final step in ['abilities', 'passives', 'MR']) {
    testWidgets(
      '$step opens complete library and learned descriptions on click without hover or roster changes',
      (tester) async {
        final catalog = variantCatalog();
        final original =
            'A long original description ${List.filled(15, 'that must remain fully readable').join(' ')}. END OF DESCRIPTION';
        for (final kind in ['skills', 'passives']) {
          for (final row in catalog[kind]) {
            row['desc'] = original;
          }
        }
        final unit = <String, dynamic>{
          'id': 13500,
          'awakening': [
            [
              ['ActiveSkill', 400010],
              ['PassiveSkill', 1001],
            ],
            [],
            [],
            [],
          ],
          'synchro': [
            [
              ['ActiveSkill', 400010],
              ['PassiveSkill', 1001],
            ],
          ],
        };
        final before = jsonEncode(unit);
        await showPage(tester, step, unit, catalog);
        final previews = preview(step);
        expect(previews, findsNWidgets(2));
        final mouse = await tester.createGesture(kind: PointerDeviceKind.mouse);
        await mouse.addPointer(location: Offset.zero);
        addTearDown(mouse.removePointer);
        for (final row in [previews.first, previews.last]) {
          final widget = tester.widget<DescriptionDetails>(row);
          expect(widget.description, contains(original));
          final center = tester.getCenter(row);
          await mouse.moveTo(center);
          await tester.pump(const Duration(seconds: 1));
          await tester.pumpAndSettle();
          expect(find.byType(AlertDialog), findsNothing);
          await mouse.down(center);
          await mouse.moveTo(center + const Offset(0.25, 0.25));
          await mouse.up();
          await tester.pumpAndSettle();
          final dialog = find.byType(AlertDialog);
          expect(dialog, findsOneWidget);
          expect(
            find.descendant(of: dialog, matching: find.text(widget.title)),
            findsOneWidget,
          );
          final text = tester.widget<SelectableText>(
            find.descendant(of: dialog, matching: find.byType(SelectableText)),
          );
          expect(text.data, widget.description);
          await tester.tap(find.widgetWithText(GuideButton, 'Close'));
          await tester.pumpAndSettle();
          expect(find.byType(AlertDialog), findsNothing);
          expect(jsonEncode(unit), before);
          await mouse.moveTo(Offset.zero);
        }
        expect(tester.takeException(), isNull);
      },
    );
  }

  for (final step in ['abilities', 'passives']) {
    testWidgets('$step opens unused entries on click and equips them on drag', (
      tester,
    ) async {
      final unit = <String, dynamic>{
        'id': 13500,
        'awakening': [[], [], [], []],
      };
      await showPage(tester, step, unit, variantCatalog());
      final row = preview(step);
      expect(row, findsOneWidget);
      final start = tester.getCenter(row);
      final target = tester.getCenter(find.text('TIER 2'));
      final mouse = await tester.createGesture(kind: PointerDeviceKind.mouse);
      await mouse.down(start);
      await mouse.up();
      await tester.pumpAndSettle();
      expect(find.byType(AlertDialog), findsOneWidget);
      expect(unit['awakening'], [[], [], [], []]);
      await tester.tap(find.widgetWithText(GuideButton, 'Close'));
      await tester.pumpAndSettle();
      await mouse.down(start);
      await mouse.moveTo(start + const Offset(24, 0));
      await tester.pump();
      expect(find.byType(AlertDialog), findsNothing);
      await mouse.moveTo(target);
      await tester.pump();
      await mouse.up();
      await tester.pumpAndSettle();
      await mouse.removePointer();
      expect(find.byType(AlertDialog), findsNothing);
      expect(unit['awakening'][0], isEmpty);
      expect(unit['awakening'][1], [
        step == 'passives' ? ['PassiveSkill', 1001] : ['ActiveSkill', 400010],
      ]);
      expect(tester.takeException(), isNull);
    });
  }

  testWidgets('very long clicked descriptions remain readable by scrolling', (
    tester,
  ) async {
    tester.view.physicalSize = const Size(1000, 700);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);
    final description = List.generate(
      100,
      (i) => 'Description line $i, including all of its details.',
    ).join('\n');
    await tester.pumpWidget(
      MaterialApp(
        theme: Guide.theme(),
        home: Scaffold(
          body: Center(
            child: DescriptionDetails(
              description: description,
              child: const Text('Click for details'),
            ),
          ),
        ),
      ),
    );
    await tester.tap(find.text('Click for details'));
    await tester.pumpAndSettle();
    final dialog = find.byType(AlertDialog);
    expect(find.text('Full description'), findsOneWidget);
    final scroll = find.descendant(
      of: dialog,
      matching: find.byType(SingleChildScrollView),
    );
    final bounds = tester.getRect(scroll);
    expect(bounds.height, lessThanOrEqualTo(420));
    expect(bounds.top, greaterThanOrEqualTo(0));
    expect(bounds.bottom, lessThanOrEqualTo(700));
    final mouse = await tester.createGesture(kind: PointerDeviceKind.mouse);
    await mouse.addPointer(location: Offset.zero);
    addTearDown(mouse.removePointer);
    await mouse.moveTo(bounds.center);
    await tester.sendEventToBinding(
      PointerScrollEvent(
        position: bounds.center,
        scrollDelta: const Offset(0, 400),
      ),
    );
    await tester.pumpAndSettle();
    final position = tester
        .state<ScrollableState>(
          find.descendant(of: scroll, matching: find.byType(Scrollable)).first,
        )
        .position;
    expect(position.pixels, greaterThan(0));
    position.jumpTo(position.maxScrollExtent);
    await tester.pumpAndSettle();
    expect(
      tester.widget<SelectableText>(find.byType(SelectableText)).data,
      description,
    );
    await tester.tap(find.widgetWithText(GuideButton, 'Close'));
    await tester.pumpAndSettle();
    expect(find.byType(AlertDialog), findsNothing);
    expect(tester.takeException(), isNull);
  });
}
