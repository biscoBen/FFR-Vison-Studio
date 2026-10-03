import 'dart:async';
import 'dart:convert';
import 'dart:io';

import 'package:ffr_vision_studio/design/theme.dart';
import 'package:ffr_vision_studio/screens/add_unit_dialog.dart';
import 'package:ffr_vision_studio/services/api.dart';
import 'package:ffr_vision_studio/services/bundled_features.dart';
import 'package:ffr_vision_studio/services/crystal_fina.dart';
import 'package:ffr_vision_studio/services/paths.dart';
import 'package:ffr_vision_studio/state/app_state.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:path/path.dart' as p;
import 'package:provider/provider.dart';

dynamic clone(dynamic value) => json.decode(json.encode(value));
Map<String, dynamic> suppliedProfile() => json.decode(File('${CrystalFina.assetRoot}/profile.json').readAsStringSync()) as Map<String, dynamic>;
Future<Uint8List> diskAsset(String path) => File(path).readAsBytes();

// File installation is tested separately; keep the picker in Flutter's test zone.
class PickerFeatures extends BundledFeatures {
  PickerFeatures() : super(readAsset: (path) async => File(path).readAsBytesSync());
  @override
  Future<void> ensureUnitAssets(AppPaths paths) async {}
}

class RosterApi extends Api {
  RosterApi(this.roster) : super('http://unused');
  List<dynamic> roster;
  final calls = <String>[];
  bool cave = false;
  Future<void> Function(List<dynamic>)? beforeSave;
  @override
  Future<List<dynamic>> spec() async => clone(roster) as List;
  @override
  Future<void> saveSpec(List<dynamic> units) async {
    calls.add('save');
    await beforeSave?.call(units);
    roster = clone(units) as List;
  }
  @override
  Future<void> build({required bool install}) async { calls.add('build'); }
  @override
  Future<void> saveCrystalCave(bool value) async { calls.add('cave:$value'); cave = value; }
  @override
  Future<void> deleteUnit(String key) async { calls.add('delete'); roster.removeWhere((u) => u['key'] == key); }
  @override
  Future<List<dynamic>> ffbeUnits() async => throw StateError('host unavailable');
  @override
  Future<Map<String, dynamic>> ffbeUnit(String id) async => throw StateError('Bundled Fina must not use the hosted template.');
}

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  late Directory temporary;
  late AppPaths paths;
  setUp(() {
    temporary = Directory.systemTemp.createTempSync('crystal-fina-');
    paths = AppPaths.at(temporary.path);
  });
  tearDown(() => temporary.deleteSync(recursive: true));

  test('the supplied preset is preserved in full and is independently editable', () {
    final source = suppliedProfile();
    final result = CrystalFina.instantiate(source, []);
    expect(result.remove('bundledPreset'), CrystalFina.presetId);
    expect(result, source);
    result['stats']['MaxHitPoint'] = 999;
    expect(source['stats']['MaxHitPoint'], 600);
    expect(result['lb_custom']['en'], 'Crystal Restoration');
    expect(result['awakening'].map((tier) => tier.length).toList(), [7, 8, 7, 7]);
  });

  test('each allocated namespace avoids collisions without changing borrowed references', () {
    for (final occupied in <Map<String, dynamic>>[
      {'id': 13503}, {'command': {'id': 323}}, {'master': {'id': 1350300}},
      {'skills': {'485300': {}}}, {'skills': {'444040': {}}},
    ]) {
      final source = suppliedProfile();
      final roster = [{'key': 'other', ...occupied}];
      final before = clone(roster);
      final result = CrystalFina.instantiate(source, roster);
      expect(result['id'], isNot(13503));
      final id = result['id'] as int;
      expect(result['sort'], id + 70);
      expect(result['command']['id'], 320 + id - 13500);
      expect(result['master']['id'], id * 100);
      expect(result['synchro'].last.last, ['MasterSkill', id * 100]);
      expect(result['skills'].values.single, source['skills']['485300']);
      for (final field in ['awakening', 'lb', 'lb_custom', 'stats', 'elemRes', 'ffbe', 'custom', 'donor']) {
        expect(result[field], source[field], reason: 'Preserve borrowed references and settings: $field');
      }
      expect(roster, before);
    }
  });

  test('owned granted skills and map references follow remapping; borrowed grants do not', () {
    final source = suppliedProfile();
    source['awakening'][0].add(['ActiveSkill', 485300]);
    source['ffbeMap']['skills']['owned'] = 485300;
    source['ffbeMap']['skills']['borrowed'] = 445020;
    final result = CrystalFina.instantiate(source, [{'id': 13503}, {'id': 13514}]);
    expect(result['id'], 13515);
    expect(result['awakening'][0].last, ['ActiveSkill', 486500]);
    expect(result['ffbeMap']['skills'], {'owned': 486500, 'borrowed': 445020});
  });

  test('an already imported or bundled Fina cannot be duplicated', () {
    for (final identity in [
      {'key': 'crystal_fina_2'}, {'bundledPreset': CrystalFina.presetId},
      {'ffbe': {'base': CrystalFina.spriteId}}, {'ffbe': {'id': CrystalFina.spriteId}},
    ]) {
      expect(() => CrystalFina.instantiate(suppliedProfile(), [identity]), throwsStateError);
    }
  });

  test('verified artwork is installed, missing files repaired, and user edits preserved', () async {
    final features = BundledFeatures(readAsset: diskAsset);
    await features.ensureUnitAssets(paths);
    final relative = 'units/custom/crystal_fina_2/sprites/${CrystalFina.spriteId}/unit_anime_${CrystalFina.spriteId}.png';
    final artwork = File(p.join(paths.engineDir, relative));
    expect(artwork.readAsBytesSync(), File('${CrystalFina.assetRoot}/$relative').readAsBytesSync());
    artwork.writeAsStringSync('user artwork');
    final detail = File(p.join(paths.engineDir, 'units/custom/crystal_fina_2/detail.json'))..deleteSync();
    final roster = File(p.join(paths.engineDir, 'mods/EstherTsukiko/units.json'));
    roster.parent.createSync(recursive: true);
    roster.writeAsStringSync('existing user roster');
    await features.ensureUnitAssets(paths);
    expect(artwork.readAsStringSync(), 'user artwork');
    expect(detail.existsSync(), isTrue);
    expect(roster.readAsStringSync(), 'existing user roster');
    expect((await features.detail())['ffrStats'], suppliedProfile()['stats']);
  });

  test('a corrupt bundle is rejected before runtime files are written', () async {
    final features = BundledFeatures(readAsset: (path) async => path.endsWith('/profile.json')
      ? Uint8List.fromList(utf8.encode('{}')) : diskAsset(path));
    await expectLater(features.ensureUnitAssets(paths), throwsStateError);
    expect(Directory(paths.engineDir).existsSync(), isFalse);
  });

  test('startup and subsequent starts use the engine runtime with verified staged payload', () async {
    var starts = 0;
    final features = BundledFeatures(readAsset: diskAsset, runProcess: (exe, args, directory) async {
      starts++;
      expect(exe, paths.engineExe);
      expect(args.first, '--run');
      final existing = args[1].endsWith('install_existing_visions.py');
      final action = args.last;
      expect(args.sublist(2), ['--engine', paths.engineDir, '--action', action]);
      expect(action, existing && starts % 3 == 1 ? 'Restore' : 'Apply');
      expect(directory, paths.engineDir);
      expect(File(args[1]).existsSync(), isTrue);
      expect(File(p.join(p.dirname(args[1]), 'payload/manifest.json')).existsSync(), isTrue);
      return ProcessResult(1, 0, json.encode({'status': action == 'Restore' ? 'restored' : 'active', 'patchVersion': existing ? '1.2.1' : '1.1.1'}), '');
    });
    await features.prepareEngine(paths, engineRunning: false);
    await features.prepareEngine(paths, engineRunning: false);
    expect(starts, 6);
    await expectLater(features.prepareEngine(paths, engineRunning: true), throwsStateError);
    expect(starts, 6);
  });

  test('installer failure is visible and does not report engine readiness', () async {
    final features = BundledFeatures(readAsset: diskAsset, runProcess: (exe, args, directory) async => ProcessResult(1, 1, '', 'unsupported upstream layout'));
    await expectLater(features.prepareEngine(paths, engineRunning: false), throwsA(predicate((e) => e.toString().contains('unsupported upstream layout'))));
  });

  test('an outdated existing vision installer response cannot report readiness', () async {
    final features = BundledFeatures(readAsset: diskAsset, runProcess: (exe, args, directory) async =>
        ProcessResult(1, 0, json.encode({'status': args.last == 'Restore' ? 'restored' : 'active', 'patchVersion': '1.1.0'}), ''));
    await expectLater(features.prepareEngine(paths, engineRunning: false),
        throwsA(predicate((e) => e.toString().contains('did not confirm existing vision support'))));
  });

  test('fresh portable setup keeps verified installer payloads below Windows MAX_PATH', () async {
    paths = AppPaths.at(p.join(temporary.path, 'Windows Downloads ').padRight(120, 'x'));
    var calls = 0;
    final features = BundledFeatures(readAsset: diskAsset, runProcess: (exe, args, directory) async {
      calls++;
      final installer = File(args[1]);
      final existing = installer.path.endsWith('install_existing_visions.py');
      final payload = Directory(p.join(installer.parent.path, 'payload'));
      final manifest = json.decode(File(p.join(payload.path, 'manifest.json')).readAsStringSync()) as Map;
      for (final relative in (manifest['files'] as Map).keys.cast<String>()) {
        final staged = File(p.joinAll([payload.path, ...relative.split('/')]));
        expect(staged.path.length, lessThan(260), reason: 'The frozen engine must be able to open $relative.');
        final source = existing ? 'assets/existing_visions/payload/$relative' : '${CrystalFina.assetRoot}/engine/payload/$relative';
        expect(staged.readAsBytesSync(), File(source).readAsBytesSync());
      }
      return ProcessResult(1, 0, json.encode({'status': args.last == 'Restore' ? 'restored' : 'active', 'patchVersion': existing ? '1.2.1' : '1.1.1'}), '');
    });
    await features.prepareEngine(paths, engineRunning: false);
    final material = Directory(p.join(paths.root, 'bundled')).listSync(recursive: true).whereType<File>().singleWhere((file) => file.path.endsWith('M_CrystalFina_AlphaTest_13503.uasset'));
    material.deleteSync();
    await features.prepareEngine(paths, engineRunning: false);
    expect(material.existsSync(), isTrue);
    expect(calls, 6);
  });

  test('adding Fina flushes edits and preserves the current remote roster', () async {
    final other = {'key': 'other', 'id': 13503, 'en': 'My edited unit', 'stats': {'Attack': 88}};
    final api = RosterApi([other, {'key': 'remote', 'id': 13514, 'custom': {'keep': true}}]);
    final app = AppState(hostBase: 'http://unused', appPaths: paths, bundledFeatures: BundledFeatures(readAsset: diskAsset))..api = api..units = clone(api.roster) as List;
    addTearDown(app.dispose);
    app.update({...other, 'stats': {'Attack': 99}});
    final added = await app.addBundledUnit();
    expect(added['id'], 13515);
    expect(api.roster[0]['stats']['Attack'], 99);
    expect(api.roster[1], {'key': 'remote', 'id': 13514, 'custom': {'keep': true}});
    expect(api.roster.last, added);
    expect(app.dirty, isFalse);
    await expectLater(app.addBundledUnit(), throwsStateError);
    expect(api.roster.length, 3);
  });

  test('cave activation uses the allocated Fina and preserves edits when enabled again', () async {
    final other = {'key': 'other', 'id': 13503, 'stats': {'Attack': 88}};
    final api = RosterApi([other]);
    final app = AppState(hostBase: 'http://unused', appPaths: paths,
        bundledFeatures: BundledFeatures(readAsset: diskAsset))..api = api..units = clone(api.roster) as List;
    addTearDown(app.dispose);
    app.update({...other, 'stats': {'Attack': 99}});
    await app.setCrystalCave(true);
    expect(api.cave, isTrue); expect(app.crystalCave, isTrue);
    expect(api.roster.first['stats']['Attack'], 99);
    final fina = api.roster.last as Map<String, dynamic>;
    expect(fina['id'], 13504);
    fina['stats']['MaxHitPoint'] = 987;
    await app.setCrystalCave(true);
    expect(api.roster.length, 2);
    expect(api.roster.last['stats']['MaxHitPoint'], 987);
    expect(await app.removeUnit(fina['key'] as String), isFalse);
    expect(api.calls, isNot(contains('delete')));
    await app.setCrystalCave(false);
    expect(api.cave, isFalse); expect(app.crystalCave, isFalse);
    expect(await app.removeUnit(fina['key'] as String), isTrue);
  });

  test('edits made while the add save is in flight survive its response', () async {
    final other = {'key': 'other', 'id': 13500, 'en': 'Old'};
    final api = RosterApi([other]);
    final app = AppState(hostBase: 'http://unused', appPaths: paths, bundledFeatures: BundledFeatures(readAsset: diskAsset))..api = api..units = clone(api.roster) as List;
    addTearDown(app.dispose);
    final entered = Completer<void>(), release = Completer<void>();
    api.beforeSave = (_) async { if (!entered.isCompleted) { entered.complete(); await release.future; } };
    final adding = app.addBundledUnit();
    await entered.future;
    app.update({...other, 'en': 'New during save'});
    release.complete();
    await adding;
    expect(api.roster.first['en'], 'New during save');
    expect(api.roster.length, 2);
    expect(app.units, api.roster);
    expect(app.dirty, isFalse);
  });

  test('a failed save prevents adding Fina and retains unsaved user edits', () async {
    final other = {'key': 'other', 'id': 13500, 'en': 'Old'};
    final api = RosterApi([other])..beforeSave = (_) async => throw StateError('disk full');
    final app = AppState(hostBase: 'http://unused', appPaths: paths, bundledFeatures: BundledFeatures(readAsset: diskAsset))..api = api..units = clone(api.roster) as List;
    addTearDown(app.dispose);
    app.update({...other, 'en': 'Keep this edit'});
    await expectLater(app.addBundledUnit(), throwsStateError);
    expect(app.dirty, isTrue);
    expect(app.units.first['en'], 'Keep this edit');
    expect(api.roster.length, 1);
  });

  test('a build waits for current roster edits to finish saving', () async {
    final api = RosterApi([{'key': 'other', 'id': 13500, 'en': 'Old'}]);
    final app = AppState(hostBase: 'http://unused', appPaths: paths)..api = api..units = clone(api.roster) as List;
    addTearDown(app.dispose);
    app.update({'key': 'other', 'id': 13500, 'en': 'Updated'});
    await app.startBuild(install: false);
    expect(api.calls, ['save', 'build']);
    expect(api.roster.first['en'], 'Updated');
  });

  testWidgets('normal Add unit offers Fina offline, uses her profile, and disables an imported duplicate', (tester) async {
    tester.view.physicalSize = const Size(1300, 1000);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);
    final api = RosterApi([]);
    final app = AppState(hostBase: 'http://unused', appPaths: paths, bundledFeatures: PickerFeatures())..api = api;
    addTearDown(app.dispose);
    await tester.pumpWidget(ChangeNotifierProvider<AppState>.value(value: app,
      child: MaterialApp(theme: Guide.theme(), home: const Scaffold(body: AddUnitDialog()))));
    await tester.pumpAndSettle();
    expect(find.text('Crystal Fina'), findsOneWidget);
    await tester.tap(find.text('Crystal Fina'));
    await tester.pumpAndSettle();
    expect(find.text('600'), findsOneWidget);
    expect(find.textContaining('including Crystal Restoration'), findsOneWidget);
    expect(tester.widgetList<TextField>(find.byType(TextField)).any((f) => f.readOnly && f.controller?.text == 'Crystal Fina'), isTrue);
    app.units = [suppliedProfile()];
    app.select(null);
    await tester.pumpAndSettle();
    expect(find.text('ALREADY IN MOD'), findsOneWidget);
    expect(tester.takeException(), isNull);
  });
}
