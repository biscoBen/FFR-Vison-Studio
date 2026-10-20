import 'dart:convert';
import 'dart:io';

import 'package:ffr_vision_studio/design/theme.dart';
import 'package:ffr_vision_studio/screens/deck_sync_panel.dart';
import 'package:ffr_vision_studio/services/api.dart';
import 'package:ffr_vision_studio/services/paths.dart';
import 'package:ffr_vision_studio/state/app_state.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:provider/provider.dart';

void main() {
  test('sync settings API sends token only to local setup and has no default destination', () async {
    final requests = <http.Request>[];
    final client = MockClient((request) async {
      requests.add(request);
      return http.Response(jsonEncode({'enabled': true, 'repository': 'tester/private-mods', 'hasToken': true}), 200);
    });
    await http.runWithClient(() async {
      final api = Api('http://127.0.0.1:8765');
      await api.configureDeckSync(enabled: true, repository: 'tester/private-mods', token: 'synthetic token');
      await api.configureDeckSync(enabled: false, repository: 'tester/private-mods');
      await api.publishDeckMod();
      await api.forgetDeckToken();
    }, () => client);
    expect(jsonDecode(requests[0].body), {'enabled': true, 'repository': 'tester/private-mods', 'token': 'synthetic token'});
    expect(jsonDecode(requests[1].body), {'enabled': false, 'repository': 'tester/private-mods'});
    expect(requests[2].url.path, '/api/deck/publish');
    expect(requests[2].body, '{}');
    expect(requests[3].method, 'DELETE');
  });

  testWidgets('fresh sync is off and publish stays disabled until personal setup', (tester) async {
    final directory = Directory.systemTemp.createTempSync('deck-sync-widget-');
    addTearDown(() => directory.deleteSync(recursive: true));
    final app = AppState(hostBase: 'http://unused', appPaths: AppPaths.at(directory.path));
    addTearDown(app.dispose);
    expect(app.deckSync['enabled'], false);
    expect(app.deckSync['repository'], '');
    await tester.pumpWidget(ChangeNotifierProvider.value(value: app, child: MaterialApp(
      theme: Guide.theme(), home: const Scaffold(body: SingleChildScrollView(child: DeckSyncPanel(canBuild: true))),
    )));
    expect(find.text('STEAM DECK SNAPSHOTS'), findsOneWidget);
    await tester.tap(find.byKey(const Key('deck-private-advanced')));
    await tester.pumpAndSettle();
    expect(tester.widget<SwitchListTile>(find.byKey(const Key('deck-sync-enabled'))).value, false);
    await tester.tap(find.byKey(const Key('deck-sync-publish')));
    expect(app.buildState, isNull);
    expect(app.deckWorking, false);
  });

  testWidgets('only the explicit publish button uploads after a successful build', (tester) async {
    for (final scenario in [(publish: false, result: 'ok'), (publish: true, result: 'failed'), (publish: true, result: 'ok')]) {
      final directory = Directory.systemTemp.createTempSync('deck-sync-build-');
      final app = AppState(hostBase: 'http://unused', appPaths: AppPaths.at(directory.path));
      app.api = Api('http://127.0.0.1:8765');
      app.deckSync = {'enabled': true, 'repository': 'tester/private-mods', 'hasToken': true};
      var uploads = 0;
      final client = MockClient((request) async {
        if (request.url.path == '/api/deck/publish') { uploads++; }
        final data = switch (request.url.path) {
          '/api/build/log' => {'running': false, 'result': scenario.result},
          '/api/deck/status' => {'running': true, 'enabled': true, 'hasToken': true},
          _ => {'ok': true},
        };
        return http.Response(jsonEncode(data), 200);
      });
      try {
        await http.runWithClient(() async {
          await app.startBuild(install: false, publishToDeck: scenario.publish);
          await tester.pump(const Duration(milliseconds: 1300));
          await tester.pump();
          expect(uploads, scenario.publish && scenario.result == 'ok' ? 1 : 0);
        }, () => client);
      } finally { app.dispose(); directory.deleteSync(recursive: true); }
    }
  });

  testWidgets('setup masks the token and never prepopulates an account destination', (tester) async {
    final directory = Directory.systemTemp.createTempSync('deck-sync-dialog-');
    addTearDown(() => directory.deleteSync(recursive: true));
    final app = AppState(hostBase: 'http://unused', appPaths: AppPaths.at(directory.path));
    addTearDown(app.dispose);
    await tester.pumpWidget(MaterialApp(home: Builder(builder: (context) => Scaffold(body:
      TextButton(onPressed: () => showDeckSyncSetup(context, app), child: const Text('Setup'))))));
    await tester.tap(find.text('Setup'));
    await tester.pumpAndSettle();
    final repo = tester.widget<TextField>(find.byKey(const Key('deck-sync-repository')));
    final token = tester.widget<TextField>(find.byKey(const Key('deck-sync-token')));
    expect(repo.controller!.text, '');
    expect(token.obscureText, true);
    expect(token.controller!.text, '');
    expect(find.text('Create my private repository'), findsOneWidget);
    expect(find.text('Open GitHub token settings'), findsOneWidget);
    await tester.tap(find.text('Cancel'));
    await tester.pumpAndSettle();
  });
}
