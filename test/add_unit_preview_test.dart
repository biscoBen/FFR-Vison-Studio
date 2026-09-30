import 'dart:async';
import 'dart:io';

import 'package:ffr_vision_studio/design/anim_viewer.dart';
import 'package:ffr_vision_studio/design/theme.dart';
import 'package:ffr_vision_studio/screens/add_unit_dialog.dart';
import 'package:ffr_vision_studio/services/api.dart';
import 'package:ffr_vision_studio/services/paths.dart';
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
  bool legacy = false;
  bool fail = false;
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

  Future<void> picker(WidgetTester tester) async {
    tester.view.physicalSize = const Size(1300, 1000);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);
    await tester.pumpWidget(ChangeNotifierProvider<AppState>.value(value: app,
      child: MaterialApp(theme: Guide.theme(), home: const Scaffold(body: AddUnitDialog()))));
    await tester.pumpAndSettle();
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
