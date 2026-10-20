import 'dart:convert';
import 'dart:io';
import 'package:ffr_vision_studio/services/api.dart';
import 'package:ffr_vision_studio/services/paths.dart';
import 'package:ffr_vision_studio/state/app_state.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  test('snapshot/preset revision reloads saved settings and preserves dirty edits on conflict', () async {
    final directory = Directory.systemTemp.createTempSync('launch-restore-');
    final app = AppState(hostBase: 'http://unused', appPaths: AppPaths.at(directory.path));
    addTearDown(() { app.dispose(); directory.deleteSync(recursive: true); });
    app.api = Api('http://127.0.0.1:8765');
    var revision = 'initial';
    final units = [{'id':13500,'key':'restored','en':'Restored unit'}];
    final client = MockClient((request) async {
      final data = switch (request.url.path) {
        '/api/status' => {'launchRevision':revision},
        '/api/spec' => units,
        '/api/ffr/catalog' => {'skills': [], 'abilityModes': {'useChanges': false}},
        '/api/native/catalog' || '/api/party/catalog' => [],
        '/api/testing' => {'schema':1,'maxMr':false},
        _ => {},
      };
      return http.Response(jsonEncode(data),200);
    });
    await http.runWithClient(() async {
      await app.refreshStatus();
      expect(app.api!.launchRevision,'initial');
      revision='restored';
      await app.refreshStatus();
      expect(app.units.single['key'],'restored');
      expect(app.api!.launchRevision,'restored');
      // A restarted engine creates a fresh API object for the same setup.
      app.api=Api('http://127.0.0.1:8765');
      await app.refreshStatus();
      expect(app.api!.launchRevision,'restored');
      app.dirty=true;
      app.units=[{'id':13501,'key':'unsaved','en':'Unsaved unit'}];
      revision='newer-restore';
      await app.refreshStatus();
      expect(app.snapshotConflict,true);
      expect(app.units.single['key'],'unsaved');
      expect(app.api!.launchRevision,'restored');
      await app.reloadRestoredSetup();
      expect(app.snapshotConflict,false);
      expect(app.units.single['key'],'restored');
      expect(app.api!.launchRevision,'newer-restore');
      final backup=Directory(app.paths.configBackups).listSync().whereType<File>().single;
      expect(jsonDecode(backup.readAsStringSync()).single['key'],'unsaved');
    },()=>client);
  });

  test('roster saves carry the loaded launch revision for stale-restore protection', () async {
    final client=MockClient((request) async {
      expect(request.headers['X-Launch-Revision'],'loaded-before-restore');
      expect(jsonDecode(request.body),[]);
      return http.Response('{"detail":"Saved setup changed"}',409);
    });
    await http.runWithClient(() async {
      final api=Api('http://studio')..launchRevision='loaded-before-restore';
      await expectLater(api.saveSpec([]),throwsA(isA<ApiException>()));
    },()=>client);
  });
}
