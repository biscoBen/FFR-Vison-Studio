import 'dart:async';
import 'dart:io';

import 'package:ffr_vision_studio/design/anim_viewer.dart';
import 'package:ffr_vision_studio/design/theme.dart';
import 'package:ffr_vision_studio/screens/add_unit_dialog.dart';
import 'package:ffr_vision_studio/services/api.dart';
import 'package:ffr_vision_studio/services/paths.dart';
import 'package:ffr_vision_studio/services/overworld_appearance.dart';
import 'package:ffr_vision_studio/screens/overworld_anim_pane.dart';
import 'package:ffr_vision_studio/state/app_state.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:provider/provider.dart';

class PreviewApi extends Api {
  PreviewApi() : super('http://unused');
  final prepared = <String>{};
  final requested = <String>[];
  final polls = <String, int>{};
  final blocked = <String, Completer<Map<String, dynamic>>>{};
  List<dynamic> listedUnits = [];
  bool legacy = false;
  bool fail = false;
  @override
  Future<List<dynamic>> ffbeUnits() async => listedUnits;
  @override
  Future<Map<String, dynamic>> prepareAssets(String ffbeId, String form) async {
    if (legacy) { throw ApiException('old engine', statusCode: 404); }
    requested.add(form);
    return {'job': form};
  }
  @override
  Future<Map<String, dynamic>> assetProgress(String job) async {
    if (blocked.containsKey(job)) { return blocked[job]!.future; }
    if (fail) { return {'state': 'failed', 'error': 'Checksum mismatch'}; }
    polls[job] = (polls[job] ?? 0) + 1;
    if (polls[job] == 1) { return {'state': 'running', 'stage': 'Downloading unit data'}; }
    prepared.add(job);
    return {'state': 'done', 'stage': 'Ready'};
  }
  @override
  Future<Map<String, dynamic>> ffbeUnit(String id) async => {
    'id': id, 'name': id == '10' ? 'Preview Unit' : 'Other Unit',
    'maxForm': id == '10' ? '102' : '201',
    'forms': {for (final form in id == '10' ? ['101', '102'] : ['201']) form: {
      'rarity': form == '101' ? '5' : '7',
      'sprites': prepared.contains(form) ? ['idle', 'atk'] : <String>[],
    }},
  };
  @override
  Future<List<String>> anims(String form) async => prepared.contains(form) ? ['idle', 'atk'] : [];
  @override
  Future<List<dynamic>> spec() async => [];
  @override
  Future<Map<String, dynamic>> addUnit(String ffbeId, {String? form, String? name}) async =>
      throw StateError('Previewing must never add a unit.');
}

class PreviewState extends AppState {
  PreviewState(AppPaths paths) : super(hostBase: 'http://unused', appPaths: paths);
  final legacyDownloads = <String>[];
  Map<String, dynamic>? fieldChoice;
  int? fieldPartyId;
  @override
  Future<JsonMap> editPartyCharacter(int id, {JsonMap? appearance, JsonMap? overworld, int? battleVoice, bool clearVoice = false, bool clearBattle = false, bool clearOverworld = false}) async {
    if (appearance != null || battleVoice != null || clearVoice || clearBattle || clearOverworld) { throw StateError('This test only changes overworld appearance.'); }
    fieldPartyId = id; fieldChoice = overworld;
    return {'id': id, 'overworld': overworld};
  }
  @override
  Future<void> ensureSprites(String form, {void Function(String)? onStep}) async {
    legacyDownloads.add(form);
  }
}

void main() {
  late Directory temporary;
  late PreviewState app;
  late PreviewApi api;
  setUp(() {
    temporary = Directory.systemTemp.createTempSync('unit-preview-');
    api = PreviewApi();
    app = PreviewState(AppPaths.at(temporary.path))..api = api;
    app.hostIndex = {'units': [
      {'id': '10', 'name': 'Preview Unit', 'packs': ['101', '102'], 'hasSprites': true},
      {'id': '20', 'name': 'Other Unit', 'packs': ['201'], 'hasSprites': true},
    ]};
  });
  tearDown(() { app.dispose(); temporary.deleteSync(recursive: true); });

  Future<void> picker(WidgetTester tester, {AddUnitDialog dialog = const AddUnitDialog()}) async {
    tester.view.physicalSize = const Size(1300, 1000);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);
    await tester.pumpWidget(ChangeNotifierProvider<AppState>.value(value: app,
      child: MaterialApp(theme: Guide.theme(), home: Scaffold(body: dialog))));
    await tester.pumpAndSettle();
  }

  testWidgets('overworld picker labels genuine models, uses normal images and applies without downloads', (tester) async {
    await picker(tester, dialog: const AddUnitDialog(replaceOverworldId: 1001));
    expect(find.text('Vagrant Knight Rain'), findsOneWidget);
    expect(find.text('Preview Unit'), findsNothing);
    expect(find.text('Other Unit'), findsNothing);
    expect(find.text('Crystal Fina'), findsNothing);
    expect(find.text('4-way'), findsWidgets);
    expect(find.text('8-way'), findsWidgets);
    expect(find.byIcon(Icons.directions_walk), findsNothing);
    expect(OverworldAppearance.entries.length, 9);
    await tester.tap(find.text('Vagrant Knight Rain'));
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 100));
    expect(find.byType(OverworldAnimPane), findsOneWidget);
    expect(find.text('South'), findsOneWidget);
    await tester.runAsync(() => Future<void>.delayed(const Duration(milliseconds: 30)));
    await tester.pump();
    for (final direction in [('East', 19), ('Southeast', 21)]) {
      await tester.tap(find.byType(DropdownButton<int>));
      await tester.pump(const Duration(milliseconds: 300));
      await tester.tap(find.text(direction.$1).last);
      await tester.pump(const Duration(milliseconds: 300));
      final paint = find.descendant(of: find.byType(OverworldAnimPane), matching: find.byType(CustomPaint));
      final dynamic painter = tester.widget<CustomPaint>(paint).painter;
      expect(painter.row, direction.$2);
    }
    await tester.tap(find.text('USE THIS MODEL'));
    await tester.pump();
    expect(app.fieldPartyId, 1001);
    expect(app.fieldChoice, OverworldAppearance.profile);
    expect(api.requested, isEmpty);
    expect(app.legacyDownloads, isEmpty);
    await tester.pumpWidget(const SizedBox());
    await tester.pumpAndSettle();
    expect(tester.takeException(), isNull);
  });

  testWidgets('four-way field choice previews its own cardinal frames and persists the selected model', (tester) async {
    await picker(tester, dialog: const AddUnitDialog(replaceOverworldId: 1002));
    await tester.tap(find.text('Lasswell'));
    await tester.pump();
    await tester.runAsync(() async {
      await OverworldAppearance.assetBytes('lasswell', 'icon');
      await Future<void>.delayed(const Duration(milliseconds: 50));
    });
    await tester.pump(const Duration(milliseconds: 100));
    final dropdown = tester.widget<DropdownButton<int>>(find.byType(DropdownButton<int>));
    expect(dropdown.items!.map((item) => item.value), [2, 8, 4, 6]);
    expect(find.byType(Image), findsWidgets);
    expect(tester.widgetList<Image>(find.byType(Image)).every((image) => image.image is MemoryImage), isTrue);
    await tester.tap(find.byType(DropdownButton<String>));
    await tester.pump(const Duration(milliseconds: 300));
    await tester.tap(find.text('Run').last);
    await tester.pump(const Duration(milliseconds: 300));
    final paint = find.descendant(of: find.byType(OverworldAnimPane), matching: find.byType(CustomPaint));
    final dynamic painter = tester.widget<CustomPaint>(paint).painter;
    expect(painter.row, 8);
    expect(painter.frame, inInclusiveRange(1, 6));
    await tester.tap(find.text('USE THIS MODEL'));
    await tester.pump();
    expect(app.fieldPartyId, 1002);
    expect(app.fieldChoice, {'version': 1, 'model': 'lasswell'});
    expect(api.requested, isEmpty);
    expect(app.legacyDownloads, isEmpty);
    await tester.pumpWidget(const SizedBox());
    await tester.pumpAndSettle();
    expect(tester.takeException(), isNull);
  });

  for (final scenario in [
    (name: 'add', dialog: const AddUnitDialog(), hosted: true),
    (name: 'vision replacement', dialog: const AddUnitDialog(replaceVisionId: 13024), hosted: true),
    (name: 'party replacement', dialog: const AddUnitDialog(replacePartyId: 1001), hosted: true),
    (name: 'engine catalog fallback', dialog: const AddUnitDialog(), hosted: false),
  ]) {
    testWidgets('${scenario.name} browses the full roster and uncapped search results', (tester) async {
      final roster = <Map<String, dynamic>>[
        for (var i = 0; i < 240; i++)
          {'id': '${1000 + i}', 'name': 'Catalog unit ${i.toString().padLeft(3, '0')}',
            'packs': ['${1000 + i}'], 'hasSprites': true},
        {'id': '20', 'name': 'Zidane', 'packs': ['201'], 'hasSprites': true},
      ];
      if (scenario.hosted) {
        app.hostIndex = {'units': roster};
      } else {
        app.hostIndex = null;
        api.listedUnits = roster;
      }
      await picker(tester, dialog: scenario.dialog);
      final scrollable = find.descendant(of: find.byType(ListView), matching: find.byType(Scrollable));
      // Browsing must reach a name beyond the former first-200/C cutoff.
      await tester.scrollUntilVisible(find.text('Zidane'), 500, scrollable: scrollable, maxScrolls: 50);
      expect(find.text('Zidane'), findsOneWidget);
      expect(api.requested, isEmpty);
      await tester.tap(find.text('Zidane'));
      await tester.pumpAndSettle();
      expect(find.text('OTHER UNIT'), findsOneWidget);
      expect(api.requested, ['201']);
      expect(app.units, isEmpty);
      // A broad search must also let us reach its final match after row 200.
      await tester.enterText(find.byType(TextField).first, 'Catalog unit');
      await tester.pumpAndSettle();
      await tester.scrollUntilVisible(find.text('Catalog unit 239'), 500, scrollable: scrollable, maxScrolls: 50);
      expect(find.text('Catalog unit 239'), findsOneWidget);
      expect(tester.takeException(), isNull);
    });
  }

  testWidgets('a never-added unit gets its complete pack and animations on the first selection', (tester) async {
    await picker(tester);
    expect((await api.ffbeUnit('10'))['forms']['102']['sprites'], isEmpty);
    await tester.tap(find.text('Preview Unit'));
    await tester.pumpAndSettle();
    expect(api.requested, ['102']);
    expect(app.legacyDownloads, isEmpty);
    final viewer = tester.widget<AnimViewer>(find.byType(AnimViewer));
    expect(viewer.anims, ['idle', 'atk']);
    expect(viewer.loading, isFalse);
    expect(viewer.url('idle'), endsWith('/102/idle.webp'));
    expect(app.units, isEmpty);
    expect(tester.takeException(), isNull);
  });

  testWidgets('switching looks prepares the new pack before refreshing its animation list', (tester) async {
    await picker(tester);
    await tester.tap(find.text('Preview Unit'));
    await tester.pumpAndSettle();
    tester.widget<DropdownButtonFormField<String>>(find.byType(DropdownButtonFormField<String>)).onChanged!('101');
    await tester.pumpAndSettle();
    expect(api.requested, ['102', '101']);
    final viewer = tester.widget<AnimViewer>(find.byType(AnimViewer));
    expect(viewer.anims, ['idle', 'atk']);
    expect(viewer.url('idle'), endsWith('/101/idle.webp'));
    expect(app.units, isEmpty);
    expect(tester.takeException(), isNull);
  });

  testWidgets('changing units during preparation ignores the earlier result', (tester) async {
    final first = Completer<Map<String, dynamic>>();
    api.blocked['102'] = first;
    await picker(tester);
    await tester.tap(find.text('Preview Unit'));
    await tester.pump();
    await tester.tap(find.text('Other Unit'));
    await tester.pumpAndSettle();
    first.complete({'state': 'done'});
    await tester.pumpAndSettle();
    final viewer = tester.widget<AnimViewer>(find.byType(AnimViewer));
    expect(viewer.url('idle'), endsWith('/201/idle.webp'));
    expect(viewer.anims, ['idle', 'atk']);
    expect(tester.takeException(), isNull);
  });

  testWidgets('closing the picker during preparation does not update a disposed widget', (tester) async {
    final pending = Completer<Map<String, dynamic>>();
    api.blocked['102'] = pending;
    await picker(tester);
    await tester.tap(find.text('Preview Unit'));
    await tester.pump();
    await tester.pumpWidget(const SizedBox.shrink());
    pending.complete({'state': 'done'});
    await tester.pumpAndSettle();
    expect(tester.takeException(), isNull);
    expect(app.units, isEmpty);
  });

  test('preparation failure is reported without adding or saving a unit', () async {
    api.fail = true;
    await expectLater(app.prepareUnitPreview('10', '102'), throwsA(predicate((e) => e.toString().contains('Checksum mismatch'))));
    expect(app.units, isEmpty);
  });

  test('older engines keep the supported sprite download path', () async {
    api.legacy = true;
    await app.prepareUnitPreview('10', '102');
    expect(app.legacyDownloads, ['102']);
  });

  test('complete preparation invalidates a cached empty animation list', () async {
    expect(await app.animsFor('102'), isEmpty);
    await app.prepareUnitPreview('10', '102');
    expect(await app.animsFor('102'), ['idle', 'atk']);
  });
}
