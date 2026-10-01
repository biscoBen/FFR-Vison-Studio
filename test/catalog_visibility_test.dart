import 'package:ffr_vision_studio/design/theme.dart';
import 'package:ffr_vision_studio/screens/steps/abilities_step.dart';
import 'package:ffr_vision_studio/screens/steps/bonuses_step.dart';
import 'package:ffr_vision_studio/screens/steps/tiers.dart';
import 'package:ffr_vision_studio/state/app_state.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:provider/provider.dart';

class CatalogState extends ChangeNotifier implements AppState {
  @override
  List<dynamic> units = [];
  @override
  JsonMap? catalog = {
    'skills': [
      {
        'id': 400030,
        'name': 'Regular ability',
        'seq': [1],
        'hasUnit': 'All',
        'attr': 'Ability',
      },
      {
        'id': 400010,
        'name': 'No sequence',
        'seq': [],
        'hasUnit': 'All',
        'attr': 'Ability',
      },
      {
        'id': 400020,
        'name': 'Unit-specific',
        'seq': [1],
        'hasUnit': 'Cloud',
        'attr': 'Ability',
      },
      {
        'id': 440010,
        'name': 'Limit burst',
        'seq': [1],
        'hasUnit': 'All',
        'attr': 'FinishBlow',
      },
      {
        'id': 460000,
        'name': 'High ID',
        'seq': [1],
        'hasUnit': 'All',
        'attr': 'Ability',
      },
    ],
    'passives': [
      {'id': 1000, 'name': 'English passive', 'desc': 'A translated passive.'},
      {'id': 1001, 'name': '攻撃力アップ', 'desc': 'A Japanese passive.'},
    ],
    'icons': [],
  };

  @override
  dynamic noSuchMethod(Invocation invocation) => super.noSuchMethod(invocation);
}

void main() {
  setUpAll(() async {
    final text = FontLoader('Barlow')
      ..addFont(rootBundle.load('assets/fonts/Barlow-Regular.ttf'));
    final headings = FontLoader('BarlowCondensed')
      ..addFont(rootBundle.load('assets/fonts/BarlowCondensed-Bold.ttf'));
    await text.load();
    await headings.load();
  });
  Future<void> showStep(
    WidgetTester tester,
    Widget Function(Map<String, dynamic>, ValueChanged<Map<String, dynamic>>)
    step,
    Map<String, dynamic> unit,
  ) async {
    tester.view.physicalSize = const Size(1500, 1100);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);
    final app = CatalogState();
    addTearDown(app.dispose);
    await tester.pumpWidget(
      ChangeNotifierProvider<AppState>.value(
        value: app,
        child: MaterialApp(
          theme: Guide.theme(),
          home: Scaffold(
            body: StatefulBuilder(
              builder: (context, setState) =>
                  step(unit, (patch) => setState(() => unit.addAll(patch))),
            ),
          ),
        ),
      ),
    );
    await tester.pumpAndSettle();
  }

  testWidgets(
    'all previously excluded ability types can be searched and granted',
    (tester) async {
      final unit = <String, dynamic>{};
      await showStep(
        tester,
        (unit, set) => AbilitiesStep(unit: unit, set: set),
        unit,
      );
      for (final name in [
        'No sequence',
        'Unit-specific',
        'Limit burst',
        'High ID',
      ]) {
        expect(find.text('$name (Unverified)'), findsOneWidget);
      }
      expect(find.text('Regular ability'), findsOneWidget);
      expect(find.text('Regular ability (Unverified)'), findsNothing);
      await tester.enterText(find.byType(TextField), 'High ID');
      await tester.pumpAndSettle();
      expect(find.text('No sequence (Unverified)'), findsNothing);
      final row = find.ancestor(
        of: find.text('High ID (Unverified)'),
        matching: find.byType(LibraryRow),
      );
      await tester.tap(
        find.descendant(of: row, matching: find.byType(TierMenu)),
      );
      await tester.pumpAndSettle();
      await tester.tap(find.text('Tier 1'));
      await tester.pumpAndSettle();
      expect((unit['awakening'] as List).first, [
        ['ActiveSkill', 460000],
      ]);
      expect(find.text('learned'), findsOneWidget);
      expect(find.text('High ID (Unverified)'), findsNWidgets(2));
      expect(tester.takeException(), isNull);
    },
  );

  testWidgets('Japanese passives can be searched and granted', (tester) async {
    final unit = <String, dynamic>{};
    await showStep(
      tester,
      (unit, set) => BonusesStep(unit: unit, set: set),
      unit,
    );
    expect(find.text('English passive'), findsOneWidget);
    expect(find.text('English passive (Unverified)'), findsNothing);
    expect(find.text('攻撃力アップ (Unverified)'), findsOneWidget);
    await tester.enterText(
      find.widgetWithText(TextField, 'Search passives'),
      '攻撃',
    );
    await tester.pumpAndSettle();
    expect(find.text('English passive'), findsNothing);
    final row = find.ancestor(
      of: find.text('攻撃力アップ (Unverified)'),
      matching: find.byType(LibraryRow),
    );
    await tester.tap(find.descendant(of: row, matching: find.byType(TierMenu)));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Tier 2'));
    await tester.pumpAndSettle();
    expect((unit['awakening'] as List)[1], [
      ['PassiveSkill', 1001],
    ]);
    expect(find.text('granted'), findsOneWidget);
    expect(find.text('攻撃力アップ (Unverified)'), findsNWidgets(2));
    expect(tester.takeException(), isNull);
  });
}
