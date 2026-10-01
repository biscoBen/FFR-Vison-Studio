import 'package:ffr_vision_studio/design/description_tooltip.dart';
import 'package:ffr_vision_studio/design/theme.dart';
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
  for (final step in ['abilities', 'passives', 'MR']) {
    testWidgets(
      '$step shows complete variant descriptions on library and learned-row hover',
      (tester) async {
        tester.view.physicalSize = const Size(1500, 1100);
        tester.view.devicePixelRatio = 1;
        addTearDown(tester.view.resetPhysicalSize);
        addTearDown(tester.view.resetDevicePixelRatio);
        final catalog = variantCatalog();
        final original =
            'A long original description ${List.filled(15, 'that must remain fully readable').join(' ')}. END OF DESCRIPTION';
        for (final kind in ['skills', 'passives']) {
          for (final row in catalog[kind]) {
            row['desc'] = original;
          }
        }
        final app = CatalogState()..catalog = catalog;
        addTearDown(app.dispose);
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
        void update(Map<String, dynamic> patch) => unit.addAll(patch);
        final page = switch (step) {
          'abilities' => AbilitiesStep(unit: unit, set: update),
          'passives' => BonusesStep(unit: unit, set: update),
          _ => MrStep(unit: unit, set: update),
        };
        await tester.pumpWidget(
          ChangeNotifierProvider<AppState>.value(
            value: app,
            child: MaterialApp(
              theme: Guide.theme(),
              home: Scaffold(body: page),
            ),
          ),
        );
        await tester.pumpAndSettle();
        final title = step == 'passives' ? 'Grit' : 'Fire';
        final difference = step == 'passives'
            ? 'Equipment cost: 20'
            : 'Power: 17';
        final previews = find.byWidgetPredicate(
          (widget) =>
              widget is DescriptionTooltip &&
              widget.title == title &&
              widget.description.contains(difference),
        );
        expect(previews, findsNWidgets(2));
        final mouse = await tester.createGesture(kind: PointerDeviceKind.mouse);
        await mouse.addPointer(location: Offset.zero);
        addTearDown(mouse.removePointer);
        for (final preview in [previews.first, previews.last]) {
          final widget = tester.widget<DescriptionTooltip>(preview);
          expect(widget.description, contains(original));
          await mouse.moveTo(tester.getCenter(preview));
          await tester.pump(const Duration(milliseconds: 400));
          await tester.pumpAndSettle();
          expect(
            find.text(
              '${widget.title}\n\n${widget.description}',
              findRichText: true,
            ),
            findsWidgets,
          );
          await mouse.moveTo(Offset.zero);
          await tester.pumpAndSettle();
        }
        expect(tester.takeException(), isNull);
      },
    );
  }
  testWidgets(
    'very long descriptions remain readable by scrolling the hover popup',
    (tester) async {
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
              child: DescriptionTooltip(
                description: description,
                child: const Text('Hover for details'),
              ),
            ),
          ),
        ),
      );
      final mouse = await tester.createGesture(kind: PointerDeviceKind.mouse);
      await mouse.addPointer(location: Offset.zero);
      addTearDown(mouse.removePointer);
      await mouse.moveTo(tester.getCenter(find.text('Hover for details')));
      await tester.pump(const Duration(milliseconds: 400));
      await tester.pumpAndSettle();
      expect(find.text(description), findsOneWidget);
      final scroll = find.byType(SingleChildScrollView);
      final bounds = tester.getRect(scroll);
      expect(bounds.height, lessThanOrEqualTo(420));
      expect(bounds.top, greaterThanOrEqualTo(0));
      expect(bounds.bottom, lessThanOrEqualTo(700));
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
            find.descendant(of: scroll, matching: find.byType(Scrollable)),
          )
          .position;
      expect(position.pixels, greaterThan(0));
      position.jumpTo(position.maxScrollExtent);
      await tester.pumpAndSettle();
      expect(find.text(description), findsOneWidget);
      expect(tester.takeException(), isNull);
    },
  );
}
