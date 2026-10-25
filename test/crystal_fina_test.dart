import 'dart:async';
import 'dart:convert';
import 'dart:io';

import 'package:ffr_vision_studio/design/theme.dart';
import 'package:ffr_vision_studio/design/widgets.dart';
import 'package:ffr_vision_studio/services/sephira_visions.dart';
import 'package:ffr_vision_studio/screens/add_unit_dialog.dart';
import 'package:ffr_vision_studio/screens/home_screen.dart';
import 'package:ffr_vision_studio/services/api.dart';
import 'package:ffr_vision_studio/services/bundled_features.dart';
import 'package:ffr_vision_studio/services/character_config.dart';
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
Map<String, dynamic> legacyProfile() => json.decode(File('scripts/fixtures/crystal_fina_legacy_profile.json').readAsStringSync()) as Map<String, dynamic>;
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
  bool caveTest = false;
  bool failCaveSettings = false;
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
  Future<void> saveCrystalCave(bool value) async {
    calls.add('cave:$value');
    if (failCaveSettings) throw StateError('settings write failed');
    cave = value; if (value) caveTest = false;
  }
  @override
  Future<void> saveCrystalCaveTest(bool value) async {
    calls.add('cave-test:$value');
    if (failCaveSettings) throw StateError('settings write failed');
    caveTest = value; if (value) cave = false;
  }
  @override
  Future<void> deleteUnit(String key) async { calls.add('delete'); roster.removeWhere((u) => u['key'] == key); }
  @override
  Future<List<dynamic>> ffbeUnits() async => throw StateError('host unavailable');
  @override
  Future<Map<String, dynamic>> ffbeUnit(String id) async {
    if (id == '50') return {'name': 'A2', 'forms': {'51': {'rarity': 5, 'sprites': []}}};
    throw StateError('Bundled Fina must not use the hosted template.');
  }
}

class PickerApp extends AppState {
  PickerApp(AppPaths paths) : super(hostBase: 'http://unused', appPaths: paths, bundledFeatures: PickerFeatures());
  @override
  Future<void> prepareUnitPreview(String ffbeId, String form, {void Function(String)? onStep}) async {}
}

Map<String, dynamic> disabledFina() => suppliedProfile()..['key'] = 'sephira_crystal_fina_saved'..[SephiraVisions.field] = {
  'version': 1, 'preset': 'crystal_fina', 'enabled': false,
};

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
    expect(result['awakening'].map((tier) => tier.length).toList(), [7, 6, 5, 3]);
    expect(result['synchro'][3].single[0], 'PassiveSkill');
    expect(result['synchro'][7].single[0], 'PassiveSkill');
    expect((result['awakening'] as List).expand((t) => t as List).any((g) => g[0]=='ActiveSkill' && result['skills'][g[1].toString()]?['from']==506110),isTrue);
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
      expect(result['synchro'].last.last, ['MasterSkill', id * 100, -1]);
      final base = 445000 + (id - 13100) * 100;
      expect(result['skills'][base.toString()], source['skills']['485300']);
      expect(result['skills']['${base + 18}']['set']['belongCommandList'], [result['command']['id']]);
      for (final field in ['lb', 'lb_custom', 'stats', 'elemRes', 'ffbe', 'custom', 'donor']) {
        expect(result[field], source[field], reason: 'Preserve borrowed references and settings: $field');
      }
      expect(roster, before);
    }
  });

  test('known old Fina rewards repair once without resetting identity, artwork or kit edits', () {
    for (final tagged in [false, true]) {
      final unit = CrystalFina.instantiate(legacyProfile(), [{'id':13503}, {'id':13514}]);
      if (tagged) unit[SephiraVisions.field] = {'version':1, 'preset':'crystal_fina', 'enabled':false};
      unit['stats']['Mind'] = 83;
      unit['custom'] = {'artwork':'my artwork'};
      unit['studioAcquisition'] = {'version':1, 'random':false, 'hideSpoilers':false, 'location':'mitra_shop'};
      (unit['skills'] as Map).values.first['set']['Cost'] = 19;
      final before = clone(unit);
      expect(CrystalFina.needsRewardRepair(unit), isTrue);
      final fixed = CrystalFina.repairRewards(unit, suppliedProfile());
      expect(unit, before);
      for (final field in ['id','key','command','master','ffbe','lb','lb_custom','stats','custom','studioAcquisition',SephiraVisions.field]) {
        expect(fixed[field], unit[field], reason:field);
      }
      for (final entry in (unit['skills'] as Map).entries) { expect(fixed['skills'][entry.key], entry.value); }
      expect(fixed['synchro'][3].single, ['PassiveSkill',1551,-1]);
      expect(fixed['synchro'][7].single, ['PassiveSkill',1552,-1]);
      final learned = (fixed['skills'] as Map).entries.singleWhere((e) => e.value['from']==506110).key;
      expect(fixed['skills'][learned.toString()]['from'],506110);
      expect(fixed['skills'][learned.toString()]['set']['belongCommandList'], [unit['command']['id']]);
      expect(fixed['synchro'][9].last, ['MasterSkill',unit['master']['id'],-1]);
      expect((fixed['awakening'] as List).expand((t) => t as List).where((g) => g[0]=='PassiveSkill' && g[1]==1456),hasLength(1));
      expect(CrystalFina.needsRewardRepair(fixed),isFalse);
      expect(identical(CrystalFina.repairRewards(fixed,suppliedProfile()),fixed),isTrue);
    }
  });

  test('reward repair allocates around custom skills and preserves edited reward layouts', () {
    final unit = legacyProfile();
    unit['skills']['485318'] = clone(unit['skills']['485300']);
    final repaired = CrystalFina.repairRewards(unit,suppliedProfile());
    expect(repaired['skills']['485318'], unit['skills']['485318']);
    expect((repaired['skills'] as Map).entries.singleWhere((e) => e.value['from']==506110).key,isNot('485318'));
    unit['synchro'][3] = [['ActiveSkill',210010]];
    expect(CrystalFina.needsRewardRepair(unit),isFalse);
    expect(identical(CrystalFina.repairRewards(unit,suppliedProfile()),unit),isTrue);
    for (final field in ['native','party']) {
      final original = legacyProfile()..[field] = {'id':1};
      expect(CrystalFina.needsRewardRepair(original),isFalse);
    }
  });

  test('build backs up and repairs the old standalone rewards before the engine reads them', () async {
    final api = RosterApi([legacyProfile()]);
    final app = PickerApp(paths)..api=api..units=clone(api.roster) as List;
    addTearDown(app.dispose);
    await app.startBuild(install:true);
    expect(api.calls, ['save','build']);
    expect(api.roster.single['synchro'][3].single, ['PassiveSkill',1551,-1]);
    final backup = Directory(paths.configBackups).listSync().whereType<File>().single;
    expect(CharacterConfig.decodeAll(backup.readAsStringSync()).single['synchro'], legacyProfile()['synchro']);
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
      if (existing) {
        for (final resource in ['_ffr_build_icons.py', 'ability_live_tests.json', 'CaveHcaV3.cs', 'cave_hca_v3.ps1']) {
          expect(File(p.join(p.dirname(args[1]), 'payload', resource)).readAsBytesSync(),
            File('assets/existing_visions/payload/$resource').readAsBytesSync());
        }
      }
      return ProcessResult(1, 0, json.encode({'status': action == 'Restore' ? 'restored' : 'active', 'patchVersion': existing ? '1.2.90' : '1.1.1'}), '');
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
      return ProcessResult(1, 0, json.encode({'status': args.last == 'Restore' ? 'restored' : 'active', 'patchVersion': existing ? '1.2.90' : '1.1.1'}), '');
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

  test('retired cave switches migrate to a normal assignment and preserve roster edits', () async {
    for (final testMode in [false, true]) {
      final other = {'key': 'other', 'id': 13503, 'stats': {'Attack': 88}};
      final fina = CrystalFina.instantiate(suppliedProfile(), [other]);
      fina['stats']['MaxHitPoint'] = 987;
      final api = RosterApi([other, fina])..cave = !testMode..caveTest = testMode;
      final app = PickerApp(paths)..api = api..units = clone(api.roster) as List
        ..crystalCave = !testMode..crystalCaveTest = testMode;
      addTearDown(app.dispose);
      app.update({...other, 'stats': {'Attack': 99}});
      await app.migrateCrystalCaveOptions();
      expect(api.roster, hasLength(2));
      expect(api.roster.first['stats']['Attack'], 99);
      expect(api.roster.last['stats']['MaxHitPoint'], 987);
      expect(api.roster.last['id'], 13504);
      final acquisition = api.roster.last['studioAcquisition'] as Map;
      expect(acquisition['location'], 'crystal_cave');
      expect(acquisition['random'], isFalse);
      expect(acquisition['cave']['worldX'], 17600);
      expect(app.crystalCave || app.crystalCaveTest || api.cave || api.caveTest, isFalse);
      final calls = api.calls.length;
      await app.migrateCrystalCaveOptions();
      expect(api.calls.length, calls);
      expect(await app.removeUnit(fina['key'] as String), isTrue);
      expect(api.roster, hasLength(1));
    }
  });

  testWidgets('home removes all standalone Fina cave and diagnostic controls', (tester) async {
    final api = RosterApi([]);
    final app = AppState(hostBase: 'http://unused', appPaths: paths,
        bundledFeatures: BundledFeatures(readAsset: diskAsset))..api = api..crystalCaveTest = true;
    addTearDown(app.dispose);
    tester.view.physicalSize = const Size(1920, 1080);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);
    await tester.pumpWidget(ChangeNotifierProvider<AppState>.value(value: app,
      child: MaterialApp(theme: Guide.theme(), home: const Scaffold(body: HomeScreen()))));
    expect(find.byKey(const Key('crystal-fina-cave')), findsNothing);
    expect(find.byKey(const Key('crystal-fina-cave-test')), findsNothing);
    expect(find.byKey(const Key('crystal-fina-solid-check')), findsNothing);
    expect(find.byKey(const Key('crystal-fina-rotate')), findsNothing);
    expect(find.byKey(const Key('field-leader-cycle')), findsOneWidget);
    expect(find.byKey(const Key('testing-practice-battle')), findsOneWidget);
    expect(find.text('Crystal Fina cave'), findsNothing);
    expect(find.text('Crystal Fina Test'), findsNothing);
    expect(api.roster, isEmpty);
  });

  test('migration preserves explicit cave or shop choices and disabled collection membership', () async {
    for (final choice in ['shop_2001', 'cave_custom']) {
      final fina = disabledFina();
      fina['studioAcquisition'] = choice == 'shop_2001'
          ? {'version': 2, 'random': false, 'hideSpoilers': false, 'location': choice, 'cave': null}
          : {'version': 2, 'random': true, 'hideSpoilers': true, 'location': choice,
              'cave': {'version': 2, 'id': choice, 'name': 'My cave', 'entrance': 'shrine',
                'worldX': 17000.0, 'worldY': 21000.0, 'worldZ': 80.0, 'yaw': -90.0, 'scale': .75}};
      final before = clone(fina);
      final api = RosterApi([fina])..caveTest = true;
      final app = PickerApp(paths)..api = api..units = clone(api.roster) as List..crystalCaveTest = true;
      addTearDown(app.dispose);
      await app.migrateCrystalCaveOptions();
      expect(api.roster.single, before);
      expect(app.hasCrystalFina, isFalse);
      expect(api.caveTest, isFalse);
      expect(api.calls, ['cave-test:false']);
    }
  });

  test('failed migration retains the old switch and prevents a build until saved', () async {
    final fina = suppliedProfile();
    final api = RosterApi([fina])..caveTest = true;
    final app = PickerApp(paths)..api = api..units = clone(api.roster) as List..crystalCaveTest = true;
    addTearDown(app.dispose);
    api.beforeSave = (_) async => throw StateError('disk full');
    await expectLater(app.migrateCrystalCaveOptions(), throwsStateError);
    expect(api.roster.single['studioAcquisition'], isNull);
    expect(api.caveTest, isTrue);
    await app.startBuild(install: false);
    expect(api.calls, isNot(contains('build')));
    api.beforeSave = null;
    await app.startBuild(install: false);
    expect(api.roster.single['studioAcquisition']['location'], 'crystal_cave');
    expect(api.caveTest, isFalse);
    expect(api.calls.last, 'build');
  });

  test('retiring a saved switch never recreates a removed Fina', () async {
    final api = RosterApi([])..cave = true;
    final app = PickerApp(paths)..api = api..crystalCave = true;
    addTearDown(app.dispose);
    await app.migrateCrystalCaveOptions();
    expect(api.roster, isEmpty);
    expect(api.cave, isFalse);
    expect(api.calls, ['cave:false']);
  });

  test('a settings failure after migration saves the cave safely and can retry', () async {
    final api = RosterApi([suppliedProfile()])..caveTest = true..failCaveSettings = true;
    final app = PickerApp(paths)..api = api..units = clone(api.roster) as List..crystalCaveTest = true;
    addTearDown(app.dispose);
    await expectLater(app.migrateCrystalCaveOptions(), throwsStateError);
    final saved = clone(api.roster);
    expect(api.roster.single['studioAcquisition']['location'], 'crystal_cave');
    expect(api.caveTest && app.crystalCaveTest, isTrue);
    api.failCaveSettings = false;
    await app.migrateCrystalCaveOptions();
    expect(api.roster, saved);
    expect(api.caveTest || app.crystalCaveTest, isFalse);
  });

  test('Add moves disabled Crystal Fina to Added Visions with her identity and edits', () async {
    final original = disabledFina();
    original['stats']['Mind'] = 77;
    original['studioAcquisition'] = {'version': 1, 'random': false, 'hideSpoilers': false, 'location': 'mitra_shop'};
    final before = clone(original);
    final api = RosterApi([original]);
    final app = PickerApp(paths)..api = api..units = clone(api.roster) as List..sephiraInitialized = true;
    app.sephiraPresets = [{'id': 'crystal_fina', 'name': 'Crystal Fina', 'theme': 'Healing', 'profile': suppliedProfile()}];
    addTearDown(app.dispose);
    expect(app.hasCrystalFina, isFalse);
    final added = await app.addBundledUnit();
    expect(app.hasCrystalFina, isTrue);
    expect(app.sephiraEnabled, isFalse);
    expect(app.sephiraUnits, isEmpty);
    expect(api.roster, hasLength(1));
    expect(SephiraVisions.member(added), isFalse);
    expect(added, (clone(before) as Map)..remove(SephiraVisions.field));
    expect(original, before, reason: 'Do not mutate the saved source during preparation');
    await app.setSephiraEnabled(true);
    await app.setSephiraEnabled(false);
    expect(api.roster, hasLength(1));
    expect(app.hasCrystalFina, isTrue);
    expect(app.includedUnitCount, 1);
    await expectLater(app.addBundledUnit(), throwsStateError);
  });

  test('enabling the cave activates disabled saved Fina without duplicating her', () async {
    final api = RosterApi([disabledFina()]);
    final app = PickerApp(paths)..api = api..units = clone(api.roster) as List;
    addTearDown(app.dispose);
    await app.setCrystalCaveTest(true);
    expect(app.crystalCaveTest, isTrue);
    expect(app.hasCrystalFina, isTrue);
    expect(app.sephiraEnabled, isFalse);
    expect(api.roster, hasLength(1));
    expect(SephiraVisions.member(api.roster.single as Map), isFalse);
  });

  test('failed standalone promotion leaves the disabled saved entry intact', () async {
    final api = RosterApi([disabledFina()]);
    final before = clone(api.roster);
    final app = PickerApp(paths)..api = api..units = clone(api.roster) as List;
    addTearDown(app.dispose);
    api.beforeSave = (_) async => throw StateError('disk full');
    await expectLater(app.addBundledUnit(), throwsStateError);
    expect(app.units, before);
    expect(api.roster, before);
    expect(app.hasCrystalFina, isFalse);
  });

  test('standalone promotion preserves edits made during save and stays included', () async {
    final api = RosterApi([disabledFina()]);
    final app = PickerApp(paths)..api = api..units = clone(api.roster) as List;
    addTearDown(app.dispose);
    var edited = false;
    api.beforeSave = (_) async {
      if (edited) return;
      edited = true;
      final unit = clone(app.units.single) as Map<String, dynamic>;
      unit['stats']['Mind'] = 81;
      app.update(unit);
    };
    final added = await app.addBundledUnit();
    expect(added['stats']['Mind'], 81);
    expect(api.roster.single['stats']['Mind'], 81);
    expect(SephiraVisions.member(api.roster.single as Map), isFalse);
    expect(app.hasCrystalFina, isTrue);
    expect(app.dirty, isFalse);
  });

  test('Add checks the current saved roster before creating a second Fina', () async {
    final api = RosterApi([suppliedProfile()]);
    final app = PickerApp(paths)..api = api;
    addTearDown(app.dispose);
    await expectLater(app.addBundledUnit(), throwsStateError);
    expect(api.roster, hasLength(1));
    expect(api.calls, isEmpty);
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
  });  testWidgets('disabled collection Fina is available in Add and active Fina is blocked', (tester) async {
    tester.view.physicalSize = const Size(1300, 1000);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);
    final saved = disabledFina()..['stats']['Mind'] = 77;
    final api = RosterApi([saved]);
    final app = PickerApp(paths)..api = api..units = clone(api.roster) as List;
    addTearDown(app.dispose);
    await tester.pumpWidget(ChangeNotifierProvider<AppState>.value(value: app,
      child: MaterialApp(theme: Guide.theme(), home: const Scaffold(body: AddUnitDialog()))));
    await tester.pumpAndSettle();
    expect(find.text('IN MOD'), findsNothing);
    await tester.tap(find.text('Crystal Fina'));
    await tester.pumpAndSettle();
    expect(find.text('77'), findsOneWidget, reason: 'Show the saved kit that Add will preserve');
    expect(tester.widget<GoButton>(find.byType(GoButton)).label, 'Add unit');
    expect(tester.widget<GoButton>(find.byType(GoButton)).onPressed, isNotNull);
    app.units = [suppliedProfile()]; app.select(null);
    await tester.pumpAndSettle();
    expect(find.text('IN MOD'), findsOneWidget);
    expect(tester.widget<GoButton>(find.byType(GoButton)).label, 'Already in mod');
    expect(tester.widget<GoButton>(find.byType(GoButton)).onPressed, isNull);
  });

  testWidgets('A2 badge follows included entries and Add another makes duplicates explicit', (tester) async {
    tester.view.physicalSize = const Size(1300, 1000);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);
    final api = RosterApi([]);
    final app = PickerApp(paths)..api = api..hostIndex = {'units': [
      {'id': '50', 'name': 'A2', 'packs': ['51'], 'hasSprites': true},
    ]}..units = [
      {'ffbe': {'base': '50'}, SephiraVisions.field: {'version': 1, 'preset': 'a2', 'enabled': false}},
    ];
    addTearDown(app.dispose);
    await tester.pumpWidget(ChangeNotifierProvider<AppState>.value(value: app,
      child: MaterialApp(theme: Guide.theme(), home: const Scaffold(body: AddUnitDialog()))));
    await tester.pumpAndSettle();
    expect(find.text('IN MOD'), findsNothing);
    await tester.tap(find.text('A2'));
    await tester.pumpAndSettle();
    expect(tester.widget<GoButton>(find.byType(GoButton)).label, 'Add unit');
    expect(tester.widget<GoButton>(find.byType(GoButton)).onPressed, isNotNull);
    app.units = [{'ffbe': {'base': '50'}}]; app.select(null);
    await tester.pumpAndSettle();
    expect(find.text('IN MOD'), findsOneWidget);
    expect(tester.widget<GoButton>(find.byType(GoButton)).label, 'Add another');
    expect(tester.widget<GoButton>(find.byType(GoButton)).onPressed, isNotNull);
    expect(tester.takeException(), isNull);
  });

}
