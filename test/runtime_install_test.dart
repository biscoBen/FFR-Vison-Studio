import 'dart:convert';
import 'dart:io';

import 'package:ffr_vision_studio/screens/runtime_install_dialog.dart';
import 'package:ffr_vision_studio/services/api.dart';
import 'package:ffr_vision_studio/services/paths.dart';
import 'package:ffr_vision_studio/state/app_state.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';

void main() {
  for (final action in ['Install UE4SS', 'Continue without it', 'Cancel']) {
    testWidgets('missing runtime offers $action before installation', (tester) async {
      final requests = <http.Request>[];
      bool? result;
      final client = MockClient((request) async {
        requests.add(request);
        return http.Response(jsonEncode(request.method == 'GET'
            ? {'required': true, 'ready': false, 'game': r'D:\Steam\Resonance'} : {'ok': true}), 200);
      });
      await http.runWithClient(() async {
        await tester.pumpWidget(MaterialApp(home: Builder(builder: (context) => Scaffold(body: TextButton(
          onPressed: () async => result = await confirmRuntimeInstall(context, Api('http://studio'), lastBuild: true),
          child: const Text('Install last'),
        )))));
        await tester.tap(find.text('Install last')); await tester.pumpAndSettle();
        expect(requests.single.url.queryParameters['lastBuild'], 'true');
        expect(find.textContaining('Eiko'), findsOneWidget);
        await tester.tap(find.text(action).last); await tester.pumpAndSettle();
      }, () => client);
      expect(result, action != 'Cancel');
      expect(requests.length, action == 'Cancel' ? 1 : 2);
      if (action != 'Cancel') {
        expect(requests.last.url.path, '/api/runtime/choice');
        expect(jsonDecode(requests.last.body), {'game': r'D:\Steam\Resonance', 'choice': action == 'Install UE4SS' ? 'install' : 'skip'});
      }
    });
  }

  for (final status in [
    {'required': false, 'ready': false},
    {'required': true, 'ready': true},
  ]) {
    testWidgets('no prompt for runtime status $status', (tester) async {
      bool? result;
      final client = MockClient((request) async {
        expect(request.method, 'GET');
        return http.Response(jsonEncode(status), 200);
      });
      await http.runWithClient(() async {
        await tester.pumpWidget(MaterialApp(home: Builder(builder: (context) => Scaffold(body: TextButton(
          onPressed: () async => result = await confirmRuntimeInstall(context, Api('http://studio')),
          child: const Text('Install'),
        )))));
        await tester.tap(find.text('Install')); await tester.pumpAndSettle();
        expect(find.byType(AlertDialog), findsNothing);
        expect(result, true);
      }, () => client);
    });
  }

  testWidgets('cancelling runtime preflight starts neither a build nor last-build install', (tester) async {
    final directory = Directory.systemTemp.createTempSync('studio-runtime-');
    final app = AppState(hostBase: 'http://studio', appPaths: AppPaths.at(directory.path));
    app.api = Api('http://studio');
    addTearDown(() { app.dispose(); directory.deleteSync(recursive: true); });
    final requests = <String>[];
    final client = MockClient((request) async {
      requests.add(request.url.path);
      return http.Response('{}', 200);
    });
    await http.runWithClient(() async {
      await app.startBuild(install: true, prepareRuntime: () async => false);
      await app.installLast(prepareRuntime: () async => false);
    }, () => client);
    expect(requests, isNot(contains('/api/build')));
    expect(requests, isNot(contains('/api/install')));
    expect(app.building, false);
  });
}
