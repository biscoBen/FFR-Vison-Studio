import 'dart:convert';
import 'dart:io';

import 'package:ffr_vision_studio/design/theme.dart';
import 'package:ffr_vision_studio/screens/steps/mr_step.dart';
import 'package:ffr_vision_studio/services/character_config.dart';
import 'package:ffr_vision_studio/services/paths.dart';
import 'package:ffr_vision_studio/state/app_state.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:provider/provider.dart';

import 'catalog_visibility_test.dart' show CatalogState;
import 'character_config_test.dart' show ConfigApi;

Map<String, dynamic> fina() =>
    json.decode(File('assets/crystal_fina/profile.json').readAsStringSync())
        as Map<String, dynamic>;
dynamic copy(dynamic value) => json.decode(json.encode(value));

void main() {
  setUpAll(() async {
    await (FontLoader(
      'Barlow',
    )..addFont(rootBundle.load('assets/fonts/Barlow-Regular.ttf'))).load();
    await (FontLoader('BarlowCondensed')
          ..addFont(rootBundle.load('assets/fonts/BarlowCondensed-Bold.ttf')))
        .load();
  });

  Future<void> show(
    WidgetTester tester,
    Map<String, dynamic> unit, {
    AppState? state,
  }) async {
    tester.view.physicalSize = const Size(1320, 860);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);
    final app = state ?? CatalogState();
    if (state == null) {
      addTearDown(app.dispose);
    }
    await tester.pumpWidget(
      ChangeNotifierProvider<AppState>.value(
        value: app,
        child: MaterialApp(
          theme: Guide.theme(),
          home: Scaffold(
            body: StatefulBuilder(
              builder: (_, redraw) => MrStep(
                unit: unit,
                set: (patch) {
                  redraw(() => unit.addAll(patch));
                  if (state != null) {
                    state.update({...unit});
                  }
                },
              ),
            ),
          ),
        ),
      ),
    );
    await tester.pumpAndSettle();
  }

  Future<void> selectRank(WidgetTester tester, int rank) async {
    await tester.tap(find.byKey(const ValueKey('mr-target')));
    await tester.pumpAndSettle();
    await tester.tap(find.text('MR $rank').last);
    await tester.pumpAndSettle();
  }

  testWidgets(
    'Tronn displays native MR 0–9, exact shared passives and permanent stats',
    (tester) async {
      final unit = fina();
      unit['en'] = 'Tronn';
      unit['awakening'] = [
        [
          ['ActiveSkill', 220010],
        ],
        [],
        [],
        [],
      ];
      unit['synchro'] = [
        [],
        [
          ['PassiveSkill', 1281, -1],
        ],
        [
          ['BaseParameter', 9, 5],
        ],
        [
          ['PassiveSkill', 1280, -1],
        ],
        [
          ['BaseParameter', 11, 8],
        ],
        [
          ['ActiveSkill', 400630, -1],
        ],
        [
          ['BaseParameter', 2, 20],
        ],
        [
          ['PassiveSkill', 1279, -1],
        ],
        [
          ['BaseParameter', 7, 15],
        ],
        [
          ['PassiveSkill', 1045, -1],
          ['BaseParameter', 11, 8],
          ['MasterSkill', unit['master']['id']],
        ],
      ];
      unit['native'] = {
        'synchroCaps': List.filled(10, 5),
        'baseline': {
          'en': 'Tronn',
          'awakening': copy(unit['awakening']),
          'synchro': copy(unit['synchro']),
        },
      };
      final original = copy(unit);
      final app = CatalogState();
      addTearDown(app.dispose);
      app.catalog = {
        'skills': [
          {
            'id': 400630,
            'name': 'Focus Magic',
            'attr': 'Ability',
            'hasUnit': 'All',
            'seq': [1],
          },
        ],
        'passives': [
          {'id': 1281, 'name': 'Restore MP on Stagger', 'equipCost': 20},
          {'id': 1280, 'name': 'Fill LB on Stagger', 'equipCost': 20},
          {'id': 1279, 'name': 'Stagger Power +20%', 'equipCost': 40},
          {'id': 1045, 'name': 'Half MP Cost', 'equipCost': 50},
        ],
      };
      await show(tester, unit, state: app);
      expect(find.text('MR 0'), findsWidgets);
      expect(find.text('MR 10'), findsNothing);
      expect(
        find.text('Restore MP on Stagger — Source: Tronn; MR=1'),
        findsWidgets,
      );
      expect(
        find.descendant(
          of: find.byKey(const ValueKey('mr-grant-1-0')),
          matching: find.text('Equip cost: 20'),
        ),
        findsOneWidget,
      );
      expect(
        find.descendant(
          of: find.byKey(const ValueKey('mr-grant-2-0')),
          matching: find.text('Permanent'),
        ),
        findsOneWidget,
      );
      final scroll = find
          .descendant(
            of: find.byKey(const ValueKey('mr-ranks')),
            matching: find.byType(Scrollable),
          )
          .first;
      await tester.scrollUntilVisible(
        find.byKey(const ValueKey('mr-rank-7')),
        200,
        scrollable: scroll,
      );
      expect(
        find.text('Stagger Power +20% — Source: Tronn; MR=7'),
        findsWidgets,
      );
      await tester.scrollUntilVisible(
        find.byKey(const ValueKey('mr-rank-9')),
        200,
        scrollable: scroll,
      );
      expect(find.text('MR 9'), findsOneWidget);
      expect(unit, original);
      expect(tester.takeException(), isNull);
    },
  );

  testWidgets(
    'original visions use their actual rank count and reward capacities',
    (tester) async {
      final unit = fina();
      unit['synchro'] = <dynamic>[<dynamic>[]];
      unit['native'] = {
        'synchroCaps': [1],
      };
      await show(tester, unit);
      await tester.tap(find.byTooltip('Add HP to MR 0'));
      await tester.pumpAndSettle();
      expect(unit['synchro'], hasLength(1));
      expect(unit['synchro'][0], hasLength(1));
      await tester.tap(find.byTooltip('Add HP to MR 0'));
      await tester.pumpAndSettle();
      expect(unit['synchro'][0], hasLength(1));
      expect(find.textContaining('already has 1 rewards'), findsOneWidget);
    },
  );

  testWidgets(
    'opening MR preserves the full profile and displays inherited rewards',
    (tester) async {
      final unit = fina();
      final original = copy(unit);
      await show(tester, unit);
      expect(unit, original);
      expect(
        find.textContaining('Unlock points stay unchanged'),
        findsOneWidget,
      );
      expect(find.text('AP'), findsOneWidget);
      await tester.scrollUntilVisible(
        find.byKey(const ValueKey('mr-rank-9')),
        200,
        scrollable: find
            .descendant(
              of: find.byKey(const ValueKey('mr-ranks')),
              matching: find.byType(Scrollable),
            )
            .first,
      );
      expect(find.byKey(const ValueKey('mr-rank-9')), findsOneWidget);
      expect(tester.takeException(), isNull);
    },
  );

  testWidgets(
    'stat rewards can be added, edited, moved and removed without changing the kit',
    (tester) async {
      final unit = fina();
      final original = copy(unit);
      await show(tester, unit);
      await selectRank(tester, 1);
      await tester.enterText(find.byKey(const ValueKey('mr-stat-1')), '123');
      await tester.tap(find.byTooltip('Add HP to MR 1'));
      await tester.pumpAndSettle();
      expect(unit['synchro'][1], [
        ['BaseParameter', 1, 50],
        ['BaseParameter', 1, 123],
      ]);
      var reward = find.byKey(const ValueKey('mr-grant-1-0'));
      await tester.enterText(
        find.descendant(of: reward, matching: find.byType(TextFormField)),
        '99',
      );
      await tester.testTextInput.receiveAction(TextInputAction.done);
      await tester.pumpAndSettle();
      expect(unit['synchro'][1][0], ['BaseParameter', 1, 99]);
      await tester.tap(
        find.descendant(of: reward, matching: find.byTooltip('Move reward')),
      );
      await tester.pumpAndSettle();
      await tester.tap(find.text('MR 2').last);
      await tester.pumpAndSettle();
      expect(unit['synchro'][1], [
        ['BaseParameter', 1, 123],
      ]);
      expect(unit['synchro'][2], [
        ['BaseParameter', 5, 5],
        ['BaseParameter', 1, 99],
      ]);
      reward = find.byKey(const ValueKey('mr-grant-1-0'));
      await tester.tap(
        find.descendant(of: reward, matching: find.byTooltip('Remove reward')),
      );
      await tester.pumpAndSettle();
      expect(unit['synchro'][1], isEmpty);
      original['synchro'] = unit['synchro'];
      expect(unit, original);
      expect(tester.takeException(), isNull);
    },
  );

  testWidgets(
    'catalog passives, abilities and custom moves are granted at the selected MR',
    (tester) async {
      final unit = fina();
      unit['skills']['485300'] = {
        'from': 400030,
        'jp': 'Fixture',
        'en': 'Custom fixture move',
        'desc': 'Custom fixture description',
      };
      await show(tester, unit);
      await selectRank(tester, 2);
      final search = find.widgetWithText(TextField, 'Search MR rewards');
      for (final choice in [
        ('English', 'PassiveSkill', 1000),
        ('No sequence', 'ActiveSkill', 400010),
        ('Custom fixture', 'ActiveSkill', 485300),
      ]) {
        await tester.enterText(search, choice.$1);
        await tester.pumpAndSettle();
        if (choice.$1 == 'English') {
          expect(
            find.text('English passive — Source: Terra; MR=5'),
            findsOneWidget,
          );
        }
        if (choice.$1 == 'No sequence') {
          expect(
            find.text('No sequence (Unverified) — Source: Archwitch Fina'),
            findsOneWidget,
          );
        }
        await tester.tap(find.byTooltip('Add to MR 2'));
        await tester.pumpAndSettle();
        expect(unit['synchro'][2], contains(equals([choice.$2, choice.$3])));
        expect(find.byTooltip('Already granted at MR 2'), findsOneWidget);
      }
      expect(tester.takeException(), isNull);
    },
  );

  testWidgets(
    'five-slot cap prevents rewards being silently truncated by the engine',
    (tester) async {
      final unit = fina();
      unit['synchro'][0] = [
        for (var i = 0; i < 5; i++) ['BaseParameter', 1, i + 1],
      ];
      await show(tester, unit);
      await tester.tap(find.byTooltip('Add MP to MR 0'));
      await tester.pump();
      expect(unit['synchro'][0], hasLength(5));
      expect(
        find.text('MR 0 already has 5 rewards. Remove or move one first.'),
        findsOneWidget,
      );
      expect(tester.takeException(), isNull);
    },
  );

  testWidgets(
    'MR changes autosave and round-trip through single and bulk character configs',
    (tester) async {
      final unit = fina();
      final unrelated = copy(unit)
        ..['key'] = 'other'
        ..['en'] = 'Other';
      final temporary = Directory.systemTemp.createTempSync('mr-config-');
      final api = ConfigApi([copy(unit), copy(unrelated)]);
      final app =
          AppState(
              hostBase: 'http://unused',
              appPaths: AppPaths.at(temporary.path),
            )
            ..api = api
            ..units = copy(api.roster) as List
            ..catalog = CatalogState().catalog;
      addTearDown(() {
        app.dispose();
        temporary.deleteSync(recursive: true);
      });
      await show(tester, unit, state: app);
      await tester.tap(find.byTooltip('Add HP to MR 0'));
      await tester.pump();
      await tester.runAsync(app.save);
      await tester.pump(const Duration(milliseconds: 800));
      expect(api.roster[0]['synchro'][0], [
        ['BaseParameter', 1, 50],
      ]);
      expect(api.roster[1], unrelated);
      final single = CharacterConfig.decode(CharacterConfig.encode(unit));
      expect(single, unit);
      final all = CharacterConfig.decodeAll(CharacterConfig.encodeAll([unit]));
      expect(all.single, unit);
    },
  );
}
