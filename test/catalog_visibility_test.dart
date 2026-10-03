import 'dart:convert';

import 'package:ffr_vision_studio/design/theme.dart';
import 'package:ffr_vision_studio/screens/steps/abilities_step.dart';
import 'package:ffr_vision_studio/screens/steps/bonuses_step.dart';
import 'package:ffr_vision_studio/screens/steps/tiers.dart';
import 'package:ffr_vision_studio/screens/steps/mr_step.dart';
import 'package:ffr_vision_studio/screens/steps/native_resonance_step.dart';
import 'package:ffr_vision_studio/design/description_details.dart';

import 'catalog_compact_summaries_test.dart' show compactExamples;

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
    'abilityModes': {'schema': 1, 'showUnverified': true, 'useChanges': true},
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
    Map<String, dynamic> unit, {
    CatalogState? state,
  }) async {
    tester.view.physicalSize = const Size(1500, 1100);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);
    final app = state ?? CatalogState();
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
    'ordinary unverified abilities remain grantable while Resonances stay out of the library',
    (tester) async {
      final unit = <String, dynamic>{};
      await showStep(
        tester,
        (unit, set) => AbilitiesStep(unit: unit, set: set),
        unit,
      );
      for (final title in [
        'No sequence (Unverified) — Source: Archwitch Fina',
        'Unit-specific (Unverified) — Source: Archwitch Fina',
        'High ID (Unverified)',
      ]) {
        expect(find.text(title), findsOneWidget);
      }
      expect(
        find.text('Limit burst (Unverified) — Source: Warrior of Light'),
        findsNothing,
      );
      expect(find.text('Regular ability'), findsOneWidget);
      expect(find.text('Regular ability (Unverified)'), findsNothing);
      await tester.enterText(find.byType(TextField), 'High ID');
      await tester.pumpAndSettle();
      expect(
        find.text('No sequence (Unverified) — Source: Archwitch Fina'),
        findsNothing,
      );
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

  testWidgets(
    'untranslated passives are hidden in selection but existing grants survive',
    (tester) async {
      final unit = <String, dynamic>{
        'awakening': [
          [],
          [
            ['PassiveSkill', 1001],
          ],
          [],
          [],
        ],
      };
      final before = jsonEncode(unit);
      await showStep(
        tester,
        (unit, set) => BonusesStep(unit: unit, set: set),
        unit,
      );
      expect(find.text('English passive — Source: Terra; MR=5'), findsOneWidget);
      expect(find.text('攻撃力アップ (Unverified)'), findsOneWidget);
      expect(
        find.ancestor(
          of: find.text('攻撃力アップ (Unverified)'),
          matching: find.byType(LibraryRow),
        ),
        findsNothing,
      );
      await tester.enterText(
        find.widgetWithText(TextField, 'Search passives'),
        '攻撃',
      );
      await tester.pumpAndSettle();
      expect(find.byType(LibraryRow), findsNothing);
      expect(jsonEncode(unit), before);
      expect(tester.takeException(), isNull);
    },
  );

  testWidgets(
    'Curaga picker keeps different combat variants and labels assigned unverified moves',
    (tester) async {
      final app = CatalogState();
      app.catalog = {
        'abilityModes': {'schema': 1, 'showUnverified': true, 'useChanges': true},
        'skills': [
          for (final (id, target, power, damage, side, sequence) in [
            (210030, 'Single', 1500, 'Magic', 'Friendlies', [1, 2]),
            (215020, 'Group', 1500, 'Magic', 'Friendlies', [1, 2]),
            (240030, 'Single', 1500, 'Magic', 'Friendlies', <int>[]),
            (245020, 'Group', 600, 'Magic', 'Friendlies', <int>[]),
            (506110, 'Group', 600, 'None', 'Enemies', <int>[]),
          ])
            {
              'id': id,
              'name': 'Curaga',
              'target': target,
              'mag': power,
              'dmgType': damage,
              'relation': side,
              'seq': sequence,
              'attr': 'Magic',
              'hasUnit': 'All',
            },
          {
            'id': 440280,
            'name': 'Aetherial Wind',
            'attr': 'FinishBlow',
            'seq': <int>[],
            'hasUnit': 'All',
          },
        ],
        'visions': [
          {'id': 13127, 'name': 'Y’shtola', 'finishBlow': 440280},
        ],
        'effects': [],
        'icons': [],
        'passives': [],
        'duplicatePolicy': {
          'schema': 2,
          'ownersComplete': true,
          'available': true,
          'groups': {},
          'protected': {
            'skills': [240030],
          },
          'verifiedMatches': {
            'skills': {
              '240030': [210030],
            },
          },
        },
      };
      await showStep(
        tester,
        (unit, set) => AbilitiesStep(unit: unit, set: set),
        {},
        state: app,
      );
      expect(find.text('Curaga — Source: Ayaka; awakening=3'), findsOneWidget);
      expect(find.text('Curaga — Source: Leah'), findsOneWidget);
      expect(
        find.text('Curaga (Unverified) — Source: Aether’s Guardian'),
        findsOneWidget,
      );
      expect(
        find.text('Curaga (Unverified) — Source: Gilgamesh'),
        findsOneWidget,
      );
      expect(find.text('Curaga (Unverified) — Source: Ayaka'), findsNothing);
      expect(
        find.text('Aetherial Wind (Unverified) — Source: Y’shtola'),
        findsNothing,
      );
      expect(find.textContaining('voice Label'), findsNothing);
      expect(tester.takeException(), isNull);
    },
  );
  testWidgets(
    'compact ability rows wrap every stat and retain full click details at minimum width',
    (tester) async {
      final app = CatalogState()
        ..catalog = {...compactExamples(), 'icons': [], 'passives': [],
          'abilityModes': {'schema': 1, 'showUnverified': true, 'useChanges': true}};
      await showStep(
        tester,
        (unit, set) => AbilitiesStep(unit: unit, set: set),
        {},
        state: app,
      );
      tester.view.physicalSize = const Size(960, 1100);
      await tester.pumpAndSettle();
      expect(find.text('Deal dark-type magic damage.'), findsOneWidget);
      const stats =
          'Type=Magic; All Targets; Accuracy=500; Break=12; Power=36; MP=0; Hits=3; Crit Chance=0';
      final text = tester.widget<Text>(find.text(stats));
      expect(text.maxLines, isNull);
      expect(find.textContaining('Hit damage shares:'), findsNothing);
      final preview = tester.widget<DescriptionDetails>(
        find.byWidgetPredicate(
          (w) => w is DescriptionDetails && w.title == 'Execution (Unverified) — Source: Dark Bahamut',
        ),
      );
      expect(preview.description, contains('Hit damage shares: 0.2, 0.3, 0.5'));
      expect(preview.description, contains('Critical chance: 0'));
      expect(tester.takeException(), isNull);
    },
  );

  testWidgets('MR hides restricted choices while preserving existing rewards', (
    tester,
  ) async {
    final app = CatalogState();
    app.catalog!['skills'] = <Map<String, dynamic>>[
      for (final row in app.catalog!['skills'])
        Map<String, dynamic>.from(row as Map),
      {'id': 501000, 'name': 'Attack', 'attr': 'Fight'},
      {'id': 501010, 'name': '針千本', 'attr': 'Ability'},
    ];
    final unit = <String, dynamic>{
      'synchro': [
        [
          ['ActiveSkill', 440010],
          ['ActiveSkill', 501000],
          ['ActiveSkill', 501010],
          ['PassiveSkill', 1001],
        ],
      ],
    };
    final before = jsonEncode(unit);
    await showStep(
      tester,
      (unit, set) => MrStep(unit: unit, set: set),
      unit,
      state: app,
    );
    for (final title in [
      'Limit burst (Unverified) — Source: Warrior of Light',
      'Attack (Unverified) — Source: A-Type Magitek Armor+',
      '針千本 (Unverified) — Source: Black Shark',
      '攻撃力アップ (Unverified)',
    ]) {
      expect(
        find.text(title),
        findsOneWidget,
      ); // Existing reward, not a picker entry.
    }
    expect(jsonEncode(unit), before);
    expect(tester.takeException(), isNull);
  });

  testWidgets(
    'all 26 default Resonances remain available in the Resonance selector',
    (tester) async {
      final app = CatalogState();
      app.catalog = {
        'skills': [
          for (var i = 0; i < 26; i++)
            {
              'id': 440000 + i,
              'name': 'Resonance $i',
              'attr': 'FinishBlow',
              'seq': [1],
            },
        ],
        'visions': [
          for (var i = 0; i < 26; i++)
            {'name': 'Vision $i', 'finishBlow': 440000 + i},
        ],
      };
      final unit = <String, dynamic>{'lb': 440000};
      await showStep(
        tester,
        (unit, set) => NativeResonanceStep(unit: unit, set: set),
        unit,
        state: app,
      );
      final picker = tester.widget<DropdownButton<num>>(
        find.byType(DropdownButton<num>),
      );
      expect(picker.items!.length, 26);
      expect(picker.items!.map((item) => item.value).toSet(), {
        for (var i = 0; i < 26; i++) 440000 + i,
      });
      expect(unit['lb'], 440000);
      expect(tester.takeException(), isNull);
    },
  );
}
